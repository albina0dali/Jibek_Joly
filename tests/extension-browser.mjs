import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
const errors=[],failed=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',r=>{if(r.status()>=400)failed.push(r.url()+': '+r.status())});
fs.mkdirSync('.jol-local/review',{recursive:true});
const results=[];
const fictional=/Arqa|Sarybel|Kumyr|Terek|Bastau|Zhalyn|Aksai|Dala Terminal|Арқа|Ақcай|Ақсай|Дала терминал/i;
async function checkUnified(){const text=await page.locator('main').innerText();assert(!fictional.test(text),'Fictional station visible');assert(!/\?{3,}/.test(text),'Broken translation visible');assert.equal(await page.locator('.topbar').count(),1);assert.equal(await page.locator('.sidebar nav').count(),1)}
async function api(path,method='GET',body,token){return page.evaluate(async({path,method,body,token})=>{const r=await fetch(path,{method,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},body:body===undefined?undefined:JSON.stringify(body)});if(!r.ok)throw Error(await r.text());return r.json()},{path,method,body,token})}
try{
 await page.goto('http://localhost:8787/#map');
 await expect(page.locator('nav .active')).toHaveAttribute('href','#map');
 const coreDisplay=await page.locator('#live-stats').innerText();
 const core=await api('/api/sessions','POST',{});
 const coreBefore=await api('/api/trip?session='+core.id);
 await page.locator('nav a[href="#movement-plan"]').click();
 await expect(page.locator('.extension-pages h1')).toHaveText('План движения');
 const session=await api('/api/extension/session','POST');
 await api('/api/extension/simulation/reset','POST',undefined,session.token);
 await api('/api/extension/simulation/pause','POST',undefined,session.token);
 const normal=await api('/api/extension/state','GET',undefined,session.token);
 assert.equal(normal.stations.length,8);assert(normal.stations.every(s=>s.id.startsWith('team-station-')));
 assert(normal.quality.value>=88&&normal.quality.value<=93);
 await page.getByRole('button',{name:'Демо-сбой: F103 +10 мин',exact:true}).click();
 const before=await api('/api/extension/state','GET',undefined,session.token);
 assert(before.quality.value<normal.quality.value&&before.quality.value>=70&&before.quality.value<=80);
 await expect(page.locator('.extension-pages .page-heading button')).toBeEnabled({timeout:20000});
 await page.locator('.extension-pages .page-heading button').click();
 const preview=page.locator('.dispatch-filters select').first();
 await expect(preview.locator('option')).toHaveCount(4);
 await expect(page.locator('.extension-pages .page-heading button')).toBeEnabled({timeout:15000});
 await preview.selectOption({index:1});
 assert.deepEqual((await api('/api/extension/state','GET',undefined,session.token)).schedule,before.schedule);
 const points=await page.locator('.trajectory').first().locator('polyline').first().getAttribute('points');
 await page.getByRole('button',{name:'Увеличить',exact:true}).click();
 assert.notEqual(await page.locator('.trajectory').first().locator('polyline').first().getAttribute('points'),points);
 await page.locator('.dispatch-filters .tabs button').nth(3).click();
 assert.equal(await page.locator('.trajectory').count(),before.trains.filter(t=>t.type==='freight').length);
 await page.locator('.dispatch-filters .tabs button').first().click();
 await page.locator('.plan-layout .panel').last().locator('button.full').first().click();
 await expect(page.locator('.drawer')).toBeVisible();
 await page.locator('.drawer-head button').click();
 await page.locator('.plan-layout .callout button').click();
 await expect(preview).toHaveValue('');
 const after=await api('/api/extension/state','GET',undefined,session.token);
 assert(after.revision>before.revision);
 assert(after.quality.value>before.quality.value&&after.quality.value>=85&&after.quality.value<=93);
 await checkUnified();
 results.push(`Calculated incident/recovery: ${normal.quality.value} → ${before.quality.value} → ${after.quality.value}`);
 await page.screenshot({path:'.jol-local/review/movement-applied.png',fullPage:true});
 results.push('Movement: filters, zoom, inspector, three alternatives, preview isolation, apply revision');
 console.log(results.at(-1));

 await page.locator('nav a[href="#history-reports"]').click();
 await expect(page.locator('.extension-pages h1')).toHaveText('История и отчёты');
 await page.locator('.replay-controls .tabs button').last().click();
 await expect(page.locator('.replay-controls .badge')).toHaveClass('badge amber');
 const scrubber=page.locator('.replay-controls input');
 await scrubber.fill(String(before.time-600));await scrubber.dispatchEvent('input');
 await page.waitForTimeout(600);
 await page.locator('.network .train-symbol rect').first().click();
 await expect(page.locator('.drawer')).toBeVisible();await page.locator('.drawer-head button').click();
 assert.deepEqual((await api('/api/extension/state','GET',undefined,session.token)).schedule,after.schedule);
 for(const [i,format]of ['csv','pdf'].entries()){
  const downloaded=page.waitForEvent('download');await page.locator('.extension-pages .page-heading button').nth(i).click();
  const download=await downloaded;await download.saveAs(`.jol-local/review/report.${format}`);
  const data=fs.readFileSync(`.jol-local/review/report.${format}`);
  if(format==='pdf')assert(data.subarray(0,4).toString()==='%PDF'&&data.length>2000);
  else {assert(data.toString().includes('category,id,status_or_score'));assert.equal((data.toString().match(/^train,/gm)||[]).length,16);assert.equal((data.toString().match(/^station,/gm)||[]).length,8);assert(data.toString().includes('summary,movement-index,'+after.quality.value));assert(data.toString().includes('summary,simulation-time,'));assert(data.toString().includes('Алматы-1'));assert(!fictional.test(data.toString()))}
 }
 await page.screenshot({path:'.jol-local/review/history-replay.png',fullPage:true});
 const replayButton=page.locator('.replay-controls>button').first();await replayButton.click();await page.waitForTimeout(700);await replayButton.click();
 await page.locator('.replay-controls>button').last().click();await expect(page.locator('.replay-controls .badge')).toHaveClass('badge green');
 results.push('History: time range, scrubber, replay play/pause, snapshot drawer, return live, CSV 16 rows, PDF nonempty, live isolation');
 console.log(results.at(-1));

 await page.locator('nav a[href="#wagons-consists"]').click();
 await expect(page.locator('.extension-pages h1')).toHaveText('Вагоны и составы');
 await expect(page.locator('.inventory-wagon')).toHaveCount(120);
 await page.getByRole('searchbox',{name:'Поиск вагонов'}).fill('W120');
 await expect(page.locator('.inventory-wagon')).toHaveCount(1);
 await page.getByRole('searchbox',{name:'Поиск вагонов'}).fill('');
 await expect(page.locator('.inventory-wagon')).toHaveCount(120);
 const yardBefore=await api('/api/extension/resources/yard','GET',undefined,session.token);
 assert.equal(yardBefore.data.station_id,'team-station-7');
 await expect(page.getByText('SIMULATED YARD OPERATIONS',{exact:true})).toBeVisible();
 assert.equal(yardBefore.data.tracks.length,4);assert.equal(yardBefore.data.shunters.length,2);
 await page.locator('.extension-pages .page-heading button').click();
 await expect(page.locator('.resource-explanation button')).toBeEnabled({timeout:15000});
 await page.locator('.resource-layout .tabs button').first().click();
 await expect(page.locator('.resource-layout tbody tr')).toHaveCount(12);
 await page.locator('.resource-layout .tabs button').last().click();
 await expect(page.locator('.resource-layout tbody tr')).toHaveCount(8);
 await page.locator('.inventory-wagon').nth(40).click();
 await page.locator('.yard-scrubber input').fill('5000');
 await page.locator('.yard-scrubber input').dispatchEvent('input');
 await page.locator('.resource-explanation button').click();
 await expect(page.locator('.resource-explanation button')).toBeDisabled();
 await expect.poll(async()=>Boolean((await api('/api/extension/resources/yard','GET',undefined,session.token)).applied)).toBe(true);
 const yardAfter=await api('/api/extension/resources/yard','GET',undefined,session.token);
 assert(yardAfter.applied);assert.deepEqual((await api('/api/extension/state','GET',undefined,session.token)).schedule,after.schedule);
 await page.screenshot({path:'.jol-local/review/yard-applied.png',fullPage:true});
 results.push('Yard: 120 wagons, 4 tracks, 2 shunters, optimization 12→8, before/after, inventory selection, timeline, apply without train mutation');
 console.log(results.at(-1));

 await page.locator('nav a[href="#plan"]').click();await expect(page.locator('nav .active')).toHaveAttribute('href','#plan');
 await page.locator('nav a[href="#map"]').click();await expect(page.locator('nav .active')).toHaveAttribute('href','#map');
 assert.equal(await page.locator('#live-stats').innerText(),coreDisplay);
 assert.deepEqual((await api('/api/trip?session='+core.id)).world,coreBefore.world);
 results.push('Core isolation: same stored six-train world after all three extension pages and original plan/map navigation');
 for(const route of ['scenario','game','ato','history','system','dashboard','causes','about']){
  await page.locator(route==='scenario'?'nav a[href^="#scenario/"]':`nav a[href="#${route}"]`).click();
  await expect(page.locator('nav .active')).toHaveAttribute('href',new RegExp('^#'+route+'(?:/|$)'));
  assert(await page.locator('main h1').count()>=1);
 }
 results.push('All ten original pages load: map, scenario, game, plan, ato, history, system, dashboard, causes, about');
 for(const light of [false,true]){
  if(await page.evaluate(()=>document.body.classList.contains('light'))!==light)await page.getByRole('button',{name:'Сменить тему',exact:true}).click();
  let reference;
  for(const route of ['dashboard','map','plan','movement-plan','history-reports','wagons-consists','scenario','game','ato','history','system','causes','about']){
   await page.locator(route==='scenario'?'nav a[href^="#scenario/"]':`nav a[href="#${route}"]`).click();
   await expect(page.locator('nav .active')).toHaveAttribute('href',new RegExp('^#'+route+'(?:/|$)'));
   await expect(page.locator('main h1')).toBeVisible();
   if(['movement-plan','history-reports','wagons-consists'].includes(route))await expect(page.locator('.extension-pages .transport')).toBeVisible();
   await checkUnified();
   const tokens=await page.evaluate(()=>{const h=document.querySelector('main h1'),p=document.querySelector('main .panel'),b=document.querySelector('main button');return {bg:getComputedStyle(document.body).backgroundColor,font:getComputedStyle(h).fontFamily,headingSize:getComputedStyle(h).fontSize,panel:p&&getComputedStyle(p).backgroundColor,buttonFont:b&&getComputedStyle(b).fontFamily}});
   if(!reference)reference=tokens;
   assert.equal(tokens.bg,reference.bg);assert.equal(tokens.font,reference.font);assert.equal(tokens.headingSize,reference.headingSize);if(tokens.panel)assert.equal(tokens.panel,reference.panel);if(tokens.buttonFont)assert.equal(tokens.buttonFont,reference.font);
   if(['dashboard','map','plan','movement-plan','history-reports','wagons-consists'].includes(route))await page.screenshot({path:`.jol-local/review/unified-${route}-${light?'light':'dark'}.png`,fullPage:true});
   await page.getByRole('button',{name:'KZ',exact:true}).click();
   if(['movement-plan','history-reports','wagons-consists'].includes(route))await expect(page.locator('.extension-pages .transport')).toBeVisible();
   await checkUnified();await page.getByRole('button',{name:'RU',exact:true}).click();
  }
 }
 await expect(page.locator('nav a[href="#plan"]')).toHaveText('Диспетчерская');
 await expect(page.locator('nav a[href="#history"]')).toHaveText('Записи поездок');
 results.push('All 13 routes in RU/KK and dark/light: canonical names, identical background/font/heading/cards/buttons, clear navigation; screenshots for six review pages');
 await page.locator('nav a[href="#wagons-consists"]').click();await expect(page.locator('.inventory-wagon')).toHaveCount(120);
 await page.getByRole('button',{name:'KZ',exact:true}).click();await expect(page.locator('.extension-pages h1')).toHaveText('Вагондар мен құрамдар');
 await page.getByRole('button',{name:'RU',exact:true}).click();
 await page.getByRole('button',{name:'Сменить тему',exact:true}).click();await page.screenshot({path:'.jol-local/review/yard-light.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 for(const route of ['movement-plan','history-reports','wagons-consists']){
  await page.locator(`nav a[href="#${route}"]`).click();await expect(page.locator('.extension-pages .transport')).toBeVisible();
  await checkUnified();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
  await page.screenshot({path:`.jol-local/review/unified-${route}-mobile.png`,fullPage:true});
 }
 await page.screenshot({path:'.jol-local/review/yard-mobile.png',fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1));
 assert.equal(await page.locator('.topbar').count(),1);assert.equal(await page.locator('.sidebar nav').count(),1);
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 results.push('Single header/navigation, shared RU/KK/theme, mobile no horizontal overflow, no JS errors or failed HTTP requests');
 fs.writeFileSync('.jol-local/review/browser-results.json',JSON.stringify({results,errors,failed},null,2));
 console.log(results.join('\n'));
}catch(e){console.log('Body:',(await page.locator('body').innerText()).slice(-4000));console.log('Errors:',errors,'HTTP:',failed);await page.screenshot({path:'.jol-local/review/browser-failure.png',fullPage:true});throw e}finally{await browser.close()}
