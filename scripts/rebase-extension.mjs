import fs from 'node:fs';
import {nodes} from '../web/corridor-engine.js';
const subset=[0,1,3,4,5,6,7,8];
const raw='integration_handoff_bundle/data';
const stations=JSON.parse(fs.readFileSync(`${raw}/stations.json`,'utf8'));
const mapping=Object.fromEntries(stations.map((s,i)=>[s.id,`team-station-${subset[i]}`]));
const names=Object.fromEntries(stations.map((s,i)=>[s.name,nodes[subset[i]].name]));
function rebase(value){
 if(Array.isArray(value))return value.map(rebase);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[mapping[k]||k,rebase(v)]));
 if(typeof value!=='string')return value;
 if(mapping[value])return mapping[value];
 for(const [old,name] of Object.entries(names))value=value.replaceAll(old,name);
 return value.replace(/Arqa\s*(?:—|â€”|-)\s*Dala/g,'Көкшетау — Алматы-2');
}
for(const file of fs.readdirSync('data/extensions/operations').filter(f=>f.endsWith('.json'))){
 const rebased=rebase(JSON.parse(fs.readFileSync(`${raw}/${file}`,'utf8')));
 if(file==='metadata.json')Object.assign(rebased,{network:'team-corridor',distance_semantics:'Synthetic operational corridor distance',corridor_distance_km:164,station_mapping:mapping});
 fs.writeFileSync(`data/extensions/operations/${file}`,JSON.stringify(rebased,null,2)+'\n');
}
const registry=nodes.map((s,i)=>{const at=subset.indexOf(i);return {id:`team-station-${i}`,display_name:s.name,aliases:[],source_ids:{team:String(i),extension:at<0?null:`team-station-${i}`},coordinates:null,model_position:{x:s.x,z:s.z},...(at<0?{}:{corridor_distance_km:stations[at].distance_km}),status:at<0?'team-only':'shared'};});
fs.writeFileSync('web/station-registry.json',JSON.stringify(registry,null,2)+'\n');
fs.mkdirSync('docs',{recursive:true});
fs.writeFileSync('docs/STATION_MAPPING.md',`# Unified demo network\n\nNine canonical team stations; the extension uses eight in corridor order. Ақкөл remains in the team model; the operational model collapses this intermediate stop to preserve both endpoints and the Алматы-1 formation hub. This is an explicit synthetic-demo rebase.\n\n| Old ID | Reference name | Canonical ID | Unified name | Synthetic km |\n|---|---|---|---|---|\n${stations.map((s,i)=>`| ${s.id} | ${s.name} | ${mapping[s.id]} | ${nodes[subset[i]].name} | ${s.distance_km} |`).join('\n')}\n\n**Synthetic operational corridor distance**: 164 km. Chainage, times, capacities and yard equipment are normalized simulation inputs, not real geography or station properties. Geographic coordinates remain null; team x/z are scene positions. Алматы-1 hosts SIMULATED YARD OPERATIONS only.\n\nRun \`node scripts/build-station-registry.mjs\` to reproduce the registry and rebased dataset from the untouched handoff. All station joins in trains, blocks, schedule, timetable and resource scenarios use canonical IDs, including API state, history, planning and reports. Train/block/signal IDs and 16 trains, 120 wagons, four tracks and two shunters are preserved. S1–S8 remain only in provenance and raw handoff.\n`);
