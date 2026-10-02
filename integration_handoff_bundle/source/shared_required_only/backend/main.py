import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import api
from app.simulator import Simulator

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(name)s %(message)s')


@asynccontextmanager
async def lifespan(app):
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        logging.warning('OR-Tools unavailable; using deterministic fallback')
    api.sim=Simulator()
    from app.resources import ResourcePlanning
    api.sim.resources=ResourcePlanning(api.sim)
    async def loop():
        deadline=asyncio.get_running_loop().time()
        while True:
            deadline+=1
            await asyncio.sleep(max(0,deadline-asyncio.get_running_loop().time()))
            await asyncio.to_thread(api.sim.tick)
    task=asyncio.create_task(loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    api.sim.store.db.close()


app=FastAPI(title='Autodispatcher · synthetic railway operations',version='1.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://localhost:8080').split(','),allow_methods=['*'],allow_headers=['*'])
app.include_router(api.router)
