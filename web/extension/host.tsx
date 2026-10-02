import {createRoot,Root} from 'react-dom/client';
import {useEffect,useState} from 'react';
import {Dispatch} from './Dispatch';
import {History} from './History';
import {YardBrain} from './YardBrain';
import {TrainDrawer,Panel} from './shared/components';
import {setLanguage,t,useLanguage} from './shared/i18n';
import {clock,request} from './shared/services';
import type {Session,Snapshot} from './shared/types';

let root:Root|null=null;
export function unmountExtension(){root?.unmount();root=null;}
export function mountExtension(element:HTMLElement,page:string,language:number){
 setLanguage(language?'kk':'ru');
 root=createRoot(element);root.render(<Extension page={page}/>);
}
function Extension({page}:{page:string}){
 useLanguage();
 const [session,setSession]=useState<Session|null>(null),[state,setState]=useState<Snapshot|null>(null),[error,setError]=useState(''),[message,setMessage]=useState(''),[selected,setSelected]=useState<string|null>(null),[retry,setRetry]=useState(0),[busy,setBusy]=useState(false),[lastUpdate,setLastUpdate]=useState<number|null>(null);
 useEffect(()=>{const header=document.getElementById('connection-state');if(header){header.textContent=error?t('Reconnecting'):state?'Python · LIVE':t('Connecting');header.title=lastUpdate?`${t('Last update')}: ${new Date(lastUpdate).toLocaleTimeString('en-GB')} · ${t('Polling every second')}`:t('Waiting for data')}},[state,lastUpdate,error]);
 useEffect(()=>{const header=document.getElementById('header-clock');if(header&&state)header.textContent=clock(state.time);const revision=document.getElementById('run-id');if(revision&&state){revision.textContent=`r${state.revision}`;revision.title='Python schedule revision'}},[state?.time,state?.revision]);
 useEffect(()=>{
  let active=true,timer:ReturnType<typeof setTimeout>;
  async function connect(){
   try{
    const s=await request<Session>('/api/session',null,'POST');if(!active)return;setSession(s);
    async function poll(){try{const next=await request<Snapshot>('/api/state',s);if(active){setState(next);setLastUpdate(Date.now());setError('')}}catch(e){if(active)setError(String(e))}finally{if(active)timer=setTimeout(poll,1000)}}
    await poll();
   }catch(e){if(active){setError(String(e));timer=setTimeout(connect,2000)}}
  }
  void connect();return()=>{active=false;clearTimeout(timer)};
 },[retry]);
 async function act(path:string,body?:unknown){
  if(!session)return false;setBusy(true);
  try{const result=await request<Snapshot>(path,session,'POST',body);setState(result&&'trains' in result?result:await request<Snapshot>('/api/state',session));return true}catch(e){setMessage(String(e));return false}finally{setBusy(false)}
 }
 const props=state&&session?{state:{...state,replanning:state.replanning||busy},session,act,select:setSelected,notify:setMessage}:null;
 return <div className="extension-pages">
  {state&&<div className="operational-kpis">
   <div className="stat"><div className="label">{t('Quality Index')}</div><div className={`value ${state.quality.value>=80?'good':state.quality.value>=60?'warn':'bad'}`}>{state.quality.value.toFixed(1)}<small>/100</small></div></div>
   <div className="stat"><div className="label">{t('Active trains')}</div><div className="value">{state.trains.filter(tr=>tr.status!=='completed').length}</div></div>
   <div className="stat"><div className="label">{t('Active incidents')}</div><div className="value">{state.incidents.filter(i=>i.status==='active').length}</div></div>
   <div className="stat"><div className="label">{t('Average delay')}</div><div className="value">{(state.trains.reduce((s,tr)=>s+tr.delay_seconds,0)/Math.max(1,state.trains.length)/60).toFixed(1)}<small>{t('min')}</small></div></div>
   <div className="stat"><div className="label">{t('Conflicts')}</div><div className="value">{state.conflicts.length}</div></div>
   <span className={`kpi-state ${state.quality.value>=80?'good':state.quality.value>=60?'warn':'bad'}`} title={`revision ${state.revision}`}>{state.quality.value>=80?'NORMAL':state.quality.value>=60?'ATTENTION':'CRITICAL'}</span>
  </div>}
  {error&&<div className="info" role="alert" title={error}>{t("Service temporarily unavailable")} · {t("Last received state")} <button onClick={()=>{setError('');setRetry(n=>n+1)}}>{t('Retry')}</button></div>}
  {state&&<div className="transport"><span className="demo">SIMULATED · seed 42</span><span title={t("Python traffic model · 8 stations · 16 trains")}>Көкшетау — Алматы-2 · 164 {t("km")} · {t("Synthetic operational corridor distance")}</span><strong>{clock(state.time)}</strong><span title="I = Σ(score × weight / 100)">{t('Quality Index')} · {state.quality.value.toFixed(1)} / 100</span><button disabled={busy} onClick={()=>void act(`/api/simulation/${state.paused?'resume':'pause'}`)}>{t(state.paused?'Resume':'Pause')}</button><select aria-label={t('Simulation speed')} value={state.speed} onChange={e=>void act(`/api/simulation/${e.target.value}`)}>{[1,2,5].map(n=><option key={n} value={n}>{n}×</option>)}</select></div>}
  {!props&&!error&&<div className="info">{t('Loading railway state')}</div>}
  {state&&page==='movement-plan'&&<div className="dispatch-filters"><button disabled={busy||state.replanning} onClick={()=>void act('/api/incidents',{type:'delay_10',location_id:'F103',duration:600})}>{t('Demo incident: F103 +10 min')}</button><button disabled={busy||state.replanning} onClick={()=>void act('/api/simulation/reset').then(ok=>ok&&act('/api/simulation/pause'))}>{t('Reset demo')}</button><span className="meta">{t('Preview is read-only. Apply changes the simulated schedule.')}</span></div>}
  {props&&(page==='movement-plan'?<Dispatch {...props}/>:page==='history-reports'?<><div className="info">{t('Exports always use current live traffic, including during replay. Yard inventory is not exported.')}</div><History {...props}/></>:<YardBrain {...props}/>)}
  {state&&page==='movement-plan'&&<Panel title={t('Movement Index breakdown')} subtitle={t('Weights 30/20/20/20/10 · energy is an advisory proxy')}><div className="table-wrap"><table><thead><tr><th>{t('Factor')}</th><th>{t('Score')}</th><th>{t('Weight')}</th><th>{t('Contribution')}</th><th>{t('Reason')}</th></tr></thead><tbody>{state.quality.components.map(c=><tr key={c.name}><td>{t(`index.${c.name}`)}</td><td>{c.score}</td><td>{c.weight}%</td><td>{c.contribution}</td><td>{t(c.reason)}</td></tr>)}</tbody></table></div><p className="padded meta">I = Σ(score × weight / 100); {t('Energy factor: 70 + 0.05 × advisory savings %. All factors are clamped to 0–100.')}</p></Panel>}
  {selected&&state&&state.trains.find(tr=>tr.id===selected)&&<TrainDrawer state={state} train={state.trains.find(tr=>tr.id===selected)!} onClose={()=>setSelected(null)}/>}
  {message&&<div className="toast" role="status" onClick={()=>setMessage('')}>{message}</div>}
 </div>;
}
