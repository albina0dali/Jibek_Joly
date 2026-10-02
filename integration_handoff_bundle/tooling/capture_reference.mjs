// Browser verification of original pages against an isolated copied backend.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const project=path.resolve(process.argv[2]),bundle=path.resolve(process.argv[3]);
const require=createRequire(path.join(project,'frontend/package.json'));
const {chromium}=require('@playwright/test');
const root=path.join(bundle,'reference_screenshots');fs.mkdirSync(root,{recursive:true});
const write=(file,data)=>{const p=path.join(bundle,file);fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(data,null,2))};
const backend='http://127.0.0.1:8001';
const login=await fetch(backend+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'dispatcher',password:'dispatch-demo'})}).then(r=>r.json());
async function api(url,method='GET',body){const r=await fetch(backend+url,{method,headers:{Authorization:'Bearer '+login.token,'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});if(!r.ok)throw Error(url+' '+r.status+' '+await r.text());return r.json()}
await api('/api/simulation/reset','POST');await api('/api/simulation/pause','POST');
const baseline=await api('/api/state');write('data/captured/default_state.json',baseline);
const index=await api('/api/history');write('data/captured/history_default.json',index);
const warmup=[];for(const s of index.snapshots)warmup.push(await api('/api/history?at='+s.time));write('data/captured/history_snapshots.json',warmup);
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
// HTTP and socket redirection isolate all screenshot interactions from the
// user's running main simulator. Original UI source remains unchanged.
await context.route('**/api/**',async route=>{const u=new URL(route.request().url());const response=await route.fetch({url:backend+u.pathname+u.search});await route.fulfill({response})});
await context.routeWebSocket('**/ws/live',socket=>{
 const remote=new WebSocket('ws://127.0.0.1:8001/ws/live'),queue=[];
 remote.addEventListener('open',()=>{for(const message of queue)remote.send(message)});
 socket.onMessage(message=>{if(remote.readyState===1)remote.send(message);else queue.push(message)});
 remote.addEventListener('message',event=>socket.send(event.data));
 socket.onClose(()=>remote.close());
 remote.addEventListener('close',()=>socket.close());
});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:5173/dispatch');await page.getByRole('button',{name:'English',exact:true}).click();await page.getByRole('button',{name:'Open operations'}).click();
await page.getByRole('heading',{name:'Dispatch plan',exact:true}).waitFor();
async function shot(name){await page.evaluate(()=>document.querySelector('button[aria-label="Русский"]').click());await page.screenshot({path:path.join(root,name+'.png'),fullPage:true});write('reference_screenshots/'+name+'.visible.json',{url:page.url(),language:'ru',text:await page.locator('main').innerText(),source:'Original frontend; isolated bundle backend; seed42, paused'});await page.evaluate(()=>document.querySelector('button[aria-label="English"]').click())}
await shot('movement_plan_default');
await page.getByRole('button',{name:'Zoom in',exact:true}).click();await page.getByRole('button',{name:'Pan later',exact:true}).click();await page.getByRole('combobox',{name:'Diagram time range'}).selectOption('7200');await page.getByRole('button',{name:'Freight',exact:true}).click();await shot('movement_plan_filtered_zoom');
await page.getByRole('button',{name:'All',exact:true}).click();await page.getByRole('combobox',{name:'Inspect train'}).selectOption('P104');await page.getByRole('button',{name:'Open service details'}).click();await shot('movement_plan_train_drawer');await page.getByRole('button',{name:'Close train inspector'}).click();
await api('/api/incidents','POST',{type:'delay_10',location_id:'P104',duration:600});
for(let i=0;i<80;i++){if((await api('/api/state')).options.length)break;await new Promise(r=>setTimeout(r,100))}
await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/replan')&&r.status()===200),page.getByRole('button',{name:'Generate alternatives'}).click()]);
await page.getByRole('combobox',{name:'Plan preview'}).locator('option').nth(1).waitFor({state:'attached'});
await page.getByRole('combobox',{name:'Plan preview'}).selectOption({index:1});await shot('movement_plan_recommendation_preview');
write('data/captured/dispatch_options.json',(await api('/api/state')).options);
const applyResponse=page.waitForResponse(r=>/\/api\/replan\/[^/]+\/apply$/.test(r.url()));await page.getByRole('button',{name:'Apply to simulator',exact:true}).click();const appliedResponse=await applyResponse;if(!appliedResponse.ok())throw Error('Dispatch UI apply: '+await appliedResponse.text());await page.getByRole('combobox',{name:'Plan preview'}).locator('option').nth(1).waitFor({state:'detached'});await shot('movement_plan_applied');
write('data/captured/after_dispatch_apply.json',await api('/api/state'));
await page.getByRole('link',{name:'History & Reports',exact:true}).click();await page.getByRole('heading',{name:'Operational action log'}).waitFor();await page.locator('.action-log>div').first().waitFor();await shot('history_reports_default');
await page.getByRole('button',{name:'Last 15 min',exact:true}).click();await page.locator('.history-status').waitFor();await page.waitForFunction(()=>document.querySelector('.replay-controls strong')?.textContent==='08:25:00');await shot('history_reports_replay');
await page.getByRole('button',{name:'Play replay',exact:true}).click();await page.getByRole('button',{name:'Pause replay',exact:true}).waitFor();await page.getByRole('button',{name:'Pause replay',exact:true}).click();
await page.locator('.network .train-symbol rect').first().click();await page.locator('.drawer').waitFor();await shot('history_reports_snapshot_drawer');await page.getByRole('button',{name:'Close train inspector'}).click();
for(const format of ['CSV','PDF']){const event=page.waitForEvent('download');await page.getByRole('button',{name:'Export '+format,exact:true}).click();const d=await event;const target=path.join(bundle,'data/captured/autodispatcher.'+format.toLowerCase());await d.saveAs(target);if(fs.statSync(target).size===0)throw Error('Empty export')}
await page.getByRole('button',{name:'Return to live',exact:true}).click();
await page.getByRole('link',{name:'Yard Brain',exact:true}).click();await page.getByRole('heading',{name:'Wagon inventory'}).waitFor();await shot('wagons_consists_default');
await page.getByRole('button',{name:'Optimize wagon formation'}).click();await page.getByRole('button',{name:'Apply resource plan'}).waitFor();await shot('wagons_consists_optimized');
const yard=await api('/api/resources/yard');write('data/captured/yard_optimized.json',yard);
await page.getByRole('button',{name:'Before optimization',exact:true}).click();await shot('wagons_consists_before_tab');
await page.getByRole('button',{name:'After optimization',exact:true}).click();await page.locator('.inventory-wagon').nth(14).click();
await page.getByRole('slider',{name:'Yard timeline'}).fill('7200');await shot('wagons_consists_selection_timeline');
await page.getByRole('button',{name:'Apply resource plan'}).click();await page.getByRole('button',{name:'Applied to resource simulator'}).waitFor();await shot('wagons_consists_applied');
write('data/captured/history_after_actions.json',await api('/api/history'));
write('data/captured/yard_applied.json',await api('/api/resources/yard'));
await context.close();
// Smoke-check the portable three-route frontend too, with the same API contract.
const portable=await browser.newContext({viewport:{width:1440,height:1000}}),p=await portable.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto('http://127.0.0.1:5175/dispatch');await p.getByRole('button',{name:'English',exact:true}).click();await p.getByRole('button',{name:'Open operations'}).click();
await p.getByRole('heading',{name:'Dispatch plan',exact:true}).waitFor();if(await p.locator('nav a').count()!==3)throw Error('Portable route scope mismatch');
for(const [route,heading] of [['/history','History & reports'],['/yard','Yard Brain']]){await p.goto('http://127.0.0.1:5175'+route);await p.getByRole('heading',{name:heading,exact:true}).waitFor()}
if(errors.length)throw Error(errors.join('\n'));
write('VALIDATION_BROWSER.json',{passed:true,original_frontend:'http://127.0.0.1:5173',isolated_backend:backend,portable_frontend:'http://127.0.0.1:5175',pages:['/dispatch','/history','/yard'],screenshots:fs.readdirSync(root).filter(n=>n.endsWith('.png')),browser_errors:errors,checks:['filters/range/pan/zoom','train drawer','generate/preview/apply dispatch plan','history replay/pause/return live','historical train drawer','actual CSV/PDF downloads while in replay','yard calculate/before-after/selection/time scrubber/apply','portable exactly three navigation links']});
await browser.close();console.log('Original three-page browser capture and portable frontend smoke passed.');
