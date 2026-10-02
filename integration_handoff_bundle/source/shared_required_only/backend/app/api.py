import asyncio


from contextlib import nullcontext


import os


import secrets


import time


from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect


from fastapi.responses import Response


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


from pydantic import BaseModel, Field


from .models import IncidentInput, Settings


from .reports import csv_report, pdf_report


router=APIRouter()


security=HTTPBearer(auto_error=False)


sessions={}


sim=None


clients=set()


replan_lock=asyncio.Lock()


async def calculate_latest():
    async with replan_lock:
        while True:
            revision=sim.revision
            if sim.options and sim.options[0]['revision']==revision:
                return
            await asyncio.to_thread(sim.replan)
            if revision==sim.revision:
                return


class Login(BaseModel):
    username: str
    password: str


class ResourceCalculation(BaseModel):
    train_id: str = 'F103'
    runtime_seconds: float = Field(default=2,ge=.1,le=3)


class ResourceApply(BaseModel):
    plan_id: str
    option_id: str | None = None


def user(credentials: HTTPAuthorizationCredentials | None=Depends(security)):
    session=sessions.get(credentials.credentials if credentials else '')
    if not session or session['expires']<time.time():
        raise HTTPException(401,'Sign in with a demo account')
    return session


def admin(session=Depends(user)):
    if session['role']!='ADMIN':
        raise HTTPException(403,'Admin access required to update settings')
    return session


@router.post('/api/auth/login')
def login(payload:Login):
    accounts={'dispatcher':('DISPATCHER',os.getenv('DISPATCHER_PASSWORD','dispatch-demo')),'admin':('ADMIN',os.getenv('ADMIN_PASSWORD','admin-demo'))}
    account=accounts.get(payload.username)
    if not account or not secrets.compare_digest(payload.password,account[1]):
        raise HTTPException(401,'Invalid demo credentials')
    token=secrets.token_urlsafe(32)
    session=dict(username=payload.username,role=account[0],expires=time.time()+86400)
    sessions[token]=session
    return dict(token=token,**session)


@router.get('/api/state',dependencies=[Depends(user)])
def state():
    with sim.lock:
        return sim.snapshot()


@router.post('/api/incidents',dependencies=[Depends(user)])
async def inject(payload:IncidentInput):
    try:
        incident=sim.inject(payload)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    asyncio.create_task(calculate_latest())
    return incident


@router.post('/api/replan',dependencies=[Depends(user)])
async def replan():
    sim.options=[]
    await calculate_latest()
    if sim.optimizer_error:
        raise HTTPException(409,sim.optimizer_error)
    return sim.options


@router.post('/api/replan/{option_id}/apply',dependencies=[Depends(user)])
def apply(option_id:str):
    try:
        return sim.apply(option_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc))


@router.post('/api/simulation/{action}',dependencies=[Depends(user)])
def control(action:str):
    # Resource lifecycle and traffic reset must be atomic, using the same
    # resource-before-traffic lock order as maintenance application.
    with sim.resources.lock if action=='reset' else nullcontext(), sim.lock:
        if action=='pause':
            sim.paused=True
        elif action=='resume':
            sim.paused=False
        elif action=='reset':
            sim.reset()
            sim.resources.reset()
        elif action in ('1','2','5'):
            sim.settings.simulation_speed=int(action)
        else:
            raise HTTPException(422,'Unknown simulator action')
        return sim.snapshot()


@router.get('/api/quality',dependencies=[Depends(user)])
def get_quality():
    return state()['quality']


@router.get('/api/history',dependencies=[Depends(user)])
def history(at:int|None=None):
    with sim.lock:
        if at is not None:
            snapshot=sim.store.get(at)
            if not snapshot:
                raise HTTPException(404,'No snapshot available in this interval')
            return snapshot
        return dict(snapshots=sim.store.index(),actions=sim.store.actions())


@router.get('/api/settings',dependencies=[Depends(user)])
def settings():
    return sim.settings


@router.put('/api/settings',dependencies=[Depends(admin)])
def update_settings(payload:Settings):
    with sim.lock:
        sim.settings=payload
        sim.store.save_configuration(payload.model_dump())
        sim.revision+=1
        sim.options=[]
        sim.store.log(sim.time,'Admin updated simulator, Quality Index and optimization settings')
    return payload


@router.get('/api/reports/{format}',dependencies=[Depends(user)])
def report(format:str):
    with sim.lock:
        s=sim.snapshot()
        if format=='csv':
            return Response(csv_report(s),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=autodispatcher.csv'})
        if format=='pdf':
            return Response(pdf_report(s,sim.store.actions(),sim.store.index()),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=autodispatcher.pdf'})
    raise HTTPException(404,'Choose csv or pdf')


@router.get('/health')
def health():
    return dict(status='ok',dataset='synthetic',trains=len(sim.trains))


@router.get('/api/resources/{module}',dependencies=[Depends(user)])
def resource_snapshot(module:str):
    try:
        return sim.resources.snapshot(module)
    except ValueError as exc:
        raise HTTPException(404,str(exc))


@router.post('/api/resources/{module}/optimize',dependencies=[Depends(user)])
async def resource_optimize(module:str,payload:ResourceCalculation):
    if module not in ('yard',):
        raise HTTPException(404,'Unknown resource planning module')
    try:
        return await asyncio.to_thread(sim.resources.calculate,module,payload.train_id,payload.runtime_seconds)
    except (ValueError,AssertionError) as exc:
        raise HTTPException(409,str(exc))


@router.post('/api/resources/{module}/apply',dependencies=[Depends(user)])
def resource_apply(module:str,payload:ResourceApply):
    if module not in ('yard',):
        raise HTTPException(404,'Unknown resource planning module')
    try:
        return sim.resources.apply(module,payload.plan_id,payload.option_id)
    except (ValueError,AssertionError) as exc:
        raise HTTPException(409,str(exc))


@router.websocket('/ws/live')
async def websocket(ws:WebSocket):
    # Authenticate with the first frame so tokens never appear in URL access logs.
    await ws.accept()
    try:
        message=await asyncio.wait_for(ws.receive_json(),timeout=5)
        session=sessions.get(message.get('token',''))
        if not session or session['expires']<time.time():
            await ws.close(code=4401)
            return
        clients.add(ws)
        deadline=asyncio.get_running_loop().time()
        while True:
            with sim.lock:
                snapshot=sim.snapshot()
            await ws.send_json(snapshot)
            deadline+=1
            await asyncio.sleep(max(0,deadline-asyncio.get_running_loop().time()))
    except (WebSocketDisconnect,RuntimeError,asyncio.TimeoutError):
        pass
    finally:
        clients.discard(ws)
