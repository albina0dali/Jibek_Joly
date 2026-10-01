import fs from 'node:fs';
import {makeWorld,step} from '../web/corridor-engine.js';
const world=makeWorld({auto:true});while(!world.done&&world.time<240)step(world,.5);world.demo=true;fs.writeFileSync('web/demo-trip.json',JSON.stringify(world));console.log('Demo trip:',world.timeline.length,'frames;',world.time.toFixed(1),'minutes; complete:',world.done);
