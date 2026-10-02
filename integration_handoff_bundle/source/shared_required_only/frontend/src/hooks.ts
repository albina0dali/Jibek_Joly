import {useEffect,useState,useRef} from 'react';
import type {Session,Snapshot} from './types';
import {request} from './services';

export function useLive(session:Session|null){
 const [state,setState]=useState<Snapshot|null>(null),[connection,setConnection]=useState('CONNECTING'),[latency,setLatency]=useState(0);
 const firstFrame=useRef(0);
 useEffect(()=>{
  if(!session){setState(null);return;}
  let disposed=false,attempt=0,ws:WebSocket,timer:ReturnType<typeof setTimeout>,lastReceived=Date.now();
  request<Snapshot>('/api/state',session).then(s=>{if(!disposed)setState(s)}).catch(()=>setConnection('OFFLINE'));
  const connect=()=>{
   if(disposed)return;
   ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/live`);
   ws.onopen=()=>{ws.send(JSON.stringify({token:session.token}));firstFrame.current=performance.now()};
   ws.onmessage=event=>{lastReceived=Date.now();const started=performance.now();const snapshot=JSON.parse(event.data) as Snapshot;setState(snapshot);setConnection('LIVE');attempt=0;requestAnimationFrame(()=>{if(!disposed)setLatency(Math.round(performance.now()-started))})};
   ws.onerror=()=>ws.close();
   ws.onclose=()=>{if(disposed)return;attempt++;setConnection(!navigator.onLine||attempt>4?'OFFLINE':'RECONNECTING');timer=setTimeout(connect,Math.min(15000,500*2**attempt));};
  };
  const offline=()=>{setConnection('OFFLINE');ws?.close()};
  const online=()=>{clearTimeout(timer);attempt=0;lastReceived=Date.now();if(ws){ws.onclose=null;ws.close()}setConnection('RECONNECTING');connect()};
  window.addEventListener('offline',offline);
  window.addEventListener('online',online);
  const watchdog=setInterval(()=>{if(ws?.readyState===WebSocket.OPEN&&Date.now()-lastReceived>4000)ws.close()},1000);
  connect();
  return()=>{disposed=true;clearTimeout(timer);clearInterval(watchdog);window.removeEventListener('offline',offline);window.removeEventListener('online',online);ws?.close()};
 },[session]);
 return {state,setState,connection,latency};
}
