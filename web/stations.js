import registry from './station-registry.json' with {type:'json'};
export const stationRegistry=registry;
export function stationDisplayName(source,id){return registry.find(s=>s.source_ids[source]===String(id))?.display_name||String(id);}
export function extensionSecondsToDisplayTime(seconds){
 if(!Number.isFinite(seconds))return '—';
 const total=8*3600+Math.floor(seconds),hours=Math.floor(total/3600),minutes=Math.floor((total%3600+3600)%3600/60),rest=(total%60+60)%60;
 return `${String(hours).padStart(2,'0')}:${String(minutes).padStart(2,'0')}:${String(rest).padStart(2,'0')}`;
}
