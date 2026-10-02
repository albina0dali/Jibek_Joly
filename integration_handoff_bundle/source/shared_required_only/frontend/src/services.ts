import {t as translate} from './i18n';
import type { Session } from './types';
export const clock=(t:number)=>`${String(8+Math.floor(t/3600)).padStart(2,'0')}:${String(Math.floor(t%3600/60)).padStart(2,'0')}:${String(Math.floor(t%60)).padStart(2,'0')}`;
export const minutes=(t:number)=>`${(t/60).toFixed(1)} ${translate('min')}`;
export const label=(s:string)=>translate(s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()));
export async function request<T>(path:string,session:Session|null,method='GET',body?:unknown):Promise<T>{
 const response=await fetch(path,{method,headers:{'Content-Type':'application/json',...(session?{Authorization:`Bearer ${session.token}`}:{})},body:body===undefined?undefined:JSON.stringify(body)});
 if(!response.ok){const data=await response.json().catch(()=>({detail:response.statusText}));throw new Error(translate(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail)));}
 return response.json() as Promise<T>;
}
export async function download(format:string,session:Session){const response=await fetch(`/api/reports/${format}`,{headers:{Authorization:`Bearer ${session.token}`}});if(!response.ok)throw new Error('Report export failed');const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=`autodispatcher.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
