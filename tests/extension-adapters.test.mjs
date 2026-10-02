import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {stationRegistry,stationDisplayName,extensionSecondsToDisplayTime} from '../web/stations.js';
import {makeWorld} from '../web/corridor-engine.js';
import {quality} from '../web/quality.js';
import {movementQuality} from '../web/quality.js';
import {calculateMovementIndex} from '../web/movement-index.js';
import {extensionProxy} from '../server/extension-proxy.js';

test('Canonical registry has nine team stations and an ordered shared eight-station subset',()=>{
 assert.equal(stationRegistry.length,9);
 assert.equal(new Set(stationRegistry.map(s=>s.id)).size,9);
 assert.equal(stationRegistry.filter(s=>s.status==='team-only').length,1);
 assert.equal(stationRegistry.filter(s=>s.status==='shared').length,8);
 assert(stationRegistry.every(s=>s.coordinates===null));
 assert.equal(stationDisplayName('team',6),'Шу');
 assert.equal(stationDisplayName('extension','team-station-7'),'Алматы-1');
 assert.equal(stationRegistry.find(s=>s.source_ids.extension==='team-station-8').corridor_distance_km,164);
});
test('Time adapter uses seconds after 08:00, with hours, minutes and seconds',()=>{
 assert.equal(extensionSecondsToDisplayTime(0),'08:00:00');
 assert.equal(extensionSecondsToDisplayTime(6120),'09:42:00');
 assert.equal(extensionSecondsToDisplayTime(2401),'08:40:01');
 assert.equal(extensionSecondsToDisplayTime(NaN),'—');
});
test('Shared movement model uses common vectors, live inputs and fixed weights',()=>{
 for(const v of JSON.parse(fs.readFileSync('tests/movement-index-vectors.json','utf8')))assert.equal(calculateMovementIndex(v.input).index,v.expected);
 const w=makeWorld({mode:'wave',events:false});
 const healthy=movementQuality(w);assert(healthy.index>=88&&healthy.index<=93);
 w.trains.forEach(t=>t.delay=10);
 assert(movementQuality(w).index<healthy.index);
 assert.deepEqual(healthy.weights,[30,20,20,20,10]);
});
test('Rebased data joins canonical stations without losing entity counts or chainage',()=>{
 const read=name=>JSON.parse(fs.readFileSync(`data/extensions/operations/${name}.json`,'utf8'));
 const stations=read('stations'),ids=new Set(stations.map(s=>s.id));
 assert.deepEqual(stations.map(s=>s.id),stationRegistry.filter(s=>s.status==='shared').map(s=>s.id));
 assert.deepEqual(stations.map(s=>s.distance_km),[0,18,43,61,89,112,138,164]);
 for(const t of read('trains'))assert(ids.has(t.origin)&&ids.has(t.destination)&&t.planned_stops.every(id=>ids.has(id)));
 for(const b of read('blocks'))assert(ids.has(b.from_station)&&ids.has(b.to_station));
 for(const t of read('timetable'))assert(ids.has(t.station_id));
 for(const v of read('schedule').filter(v=>v.kind==='station'))assert(ids.has(v.resource));
 const yard=read('resource_scenarios').yard;assert.equal(yard.station_id,'team-station-7');assert.equal(yard.wagons.length,120);assert.equal(yard.tracks.length,4);assert.equal(yard.shunters.length,2);assert(yard.wagons.every(w=>ids.has(w.destination)));
 assert.equal(read('trains').length,16);
});
test('Three unique extension routes coexist with all original core routes',()=>{
 const app=fs.readFileSync('web/app.js','utf8');
 const nav=app.slice(app.indexOf('const navs='),app.indexOf('function route'));
 for(const route of ['movement-plan','history-reports','wagons-consists'])assert.equal((nav.match(new RegExp("\\['"+route+"','",'g'))||[]).length,1);
 for(const route of ['map','plan','ato','history','system','dashboard','game','scenario','causes','about'])assert(app.includes("['"+route+"','"));
 const w=makeWorld({mode:'wave',events:false});assert.equal(w.trains.length,6);assert.equal(quality(w).index,100);
});
test('Extension proxy checks identity, origin, allowlist and unavailable service',async()=>{
 const url='https://example.test/api/extension/session';
 assert.equal((await extensionProxy(new Request(url,{method:'POST'}),{})).status,401);
 assert.equal((await extensionProxy(new Request(url,{method:'POST',headers:{'oai-authenticated-user-id':'u',origin:'https://evil.test'}}),{})).status,403);
 assert.equal((await extensionProxy(new Request(url,{method:'POST',headers:{'oai-authenticated-user-id':'u',origin:'https://example.test'}}),{})).status,503);
 const req=new Request('https://example.test/api/extension/settings',{headers:{'oai-authenticated-user-id':'u'}});
 assert.equal((await extensionProxy(req,{EXTENSION_URL:'https://solver.test'})).status,404);
});
test('Proxy bootstrap forwards service credentials without modifying core dataset',async()=>{
 const response=await extensionProxy(new Request('https://team.test/api/extension/session',{method:'POST',headers:{'oai-authenticated-user-id':'u',origin:'https://team.test'}}),{EXTENSION_URL:'https://solver.test',EXTENSION_DISPATCH_PASSWORD:'test-only',EXTENSION_SERVICE:{async fetch(request){assert.equal(request.url,'https://solver.test/api/auth/login');assert.deepEqual(await request.json(),{username:'dispatcher',password:'test-only'});return Response.json({token:'synthetic-test'})}}});
 assert.equal(response.status,200);assert.equal((await response.json()).token,'synthetic-test');
});
