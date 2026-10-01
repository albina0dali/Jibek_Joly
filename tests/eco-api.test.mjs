import test from 'node:test';
import assert from 'node:assert/strict';
import {adviceFromSnapshot} from '../server/eco-api.js';
const snapshot={train_id:'SIM-FRT-208',distance_km:7,current_speed_kmh:80,speed_limit_kmh:80,now_min:0,signal_open_min:10,mass_tons:3500};
test('Worker Eco endpoint uses the same smooth snapshot calculation as the UI',()=>{
 const result=adviceFromSnapshot(snapshot);
 assert.equal(result.train_id,snapshot.train_id);
 assert.equal(result.recommended_speed_kmh,42);
 assert.ok(result.cruise_speed_kmh<42);
 assert.equal(result.recommended_speed_profile[0].speed_kmh,80);
 assert.equal(result.recommended_speed_profile.at(-1).distance_km,7);
 assert.ok(result.energy_proxy_units<result.baseline_energy_proxy_units);
});
test('Worker rejects malformed, non-SIM and non-finite inputs without inventing advice',()=>{
 for(const row of [null,[],{...snapshot,train_id:'FRT-208'},{...snapshot,distance_km:-1},{...snapshot,distance_km:Infinity},{...snapshot,now_min:'0'}])assert.throws(()=>adviceFromSnapshot(row),e=>e.status===422);
 assert.equal(adviceFromSnapshot({...snapshot,signal_open_min:null}).status,'UNKNOWN');
 assert.equal(adviceFromSnapshot({...snapshot,signal_open_min:1}).status,'UNREACHABLE');
});
