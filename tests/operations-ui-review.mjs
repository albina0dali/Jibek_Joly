import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const browser=await chromium.launch({headless:true});
const results=[];fs.mkdirSync('.jol-local/ui-review/after',{recursive:true});
try{
 const page=await browser.newPage({viewport:{width:1366,height:768}});
 await page.goto('http://localhost:8787/#map');
 await expect(page.locator('.nav-group')).toHaveCount(4);
 await expect(page.locator('nav a')).toHaveCount(13);
 await expect(page.locator('nav a[href="#ato"]')).toHaveText('Автоведение');
 await page.locator('#wave-mode').selectOption('crowded');
 const baseline=Number(await page.locator('#operational-kpis .value').first().innerText().then(s=>s.split('/')[0]));
 await page.locator('[data-act="incident"]').click();
 await expect(page.locator('.live-incident')).toBeVisible();
 await expect(page.locator('.live-incident')).toContainText(/резерв/);
 await page.locator('#speed').selectOption('8');
 await page.locator('#play-button').click();
 await expect.poll(async()=>Number(await page.locator('#operational-kpis .value').first().innerText().then(s=>s.split('/')[0])),{timeout:20000}).toBeLessThan(baseline);
 await page.locator('#play-button').click();
 const incident=Number(await page.locator('#operational-kpis .value').first().innerText().then(s=>s.split('/')[0]));
 assert(incident<baseline,`Core incident should reduce index: ${baseline} -> ${incident}`);
 await page.locator('[data-act="map-view"][data-view="2d"]').click();
 await page.screenshot({path:'.jol-local/ui-review/after/map-incident-2d-1366.png'});
 results.push({coreIncident:{baseline,incident},scope:'Core; independent of Python incident'});
 await page.goto('http://localhost:8787/#scenario');
 await page.locator('[data-act="seek"][data-time="35"]').click();
 await page.screenshot({path:'.jol-local/ui-review/after/scenario-impact-1366.png'});
 await page.goto('http://localhost:8787/#ato');
 await expect(page.locator('main h1')).toHaveText('Автоведение');
 await expect(page.locator('.page-heading')).toContainText('Рекомендуемый профиль скорости');
 await page.goto('http://localhost:8787/#movement-plan');
 await expect(page.locator('#connection-state')).toHaveText('Python · LIVE');
 await expect(page.locator('#connection-state')).toHaveAttribute('title',/Последнее обновление/);
 await page.route('**/api/extension/state',route=>route.abort());
 await expect(page.locator('#connection-state')).toHaveText('Переподключение',{timeout:10000});
 await expect(page.locator('[role="alert"]')).toContainText('Сервис временно недоступен');
 await page.unroute('**/api/extension/state');
 await expect(page.locator('#connection-state')).toHaveText('Python · LIVE',{timeout:10000});
 results.push({reconnect:'PASS: state fetch interruption, stale state alert, automatic recovery'});
 for(const light of [false,true])for(const kk of [false,true]){
  await page.evaluate(({light,kk})=>{localStorage.setItem('jol-theme',light?'light':'dark');localStorage.setItem('jol-lang',kk?'1':'0')},{light,kk});
  for(const route of ['map','scenario','movement-plan','wagons-consists']){
   await page.goto(`http://localhost:8787/#${route}`);await page.reload();
   await page.waitForSelector('main h1');await page.waitForTimeout(800);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await page.screenshot({path:`.jol-local/ui-review/after/${route}-1366-${kk?'kk':'ru'}-${light?'light':'dark'}.png`});
  }
 }
 results.push({screenshots:16,locales:['ru','kk'],themes:['light','dark'],viewport:'1366x768',overflow:'PASS'});
 await page.evaluate(()=>localStorage.setItem('jol-lang','0'));
 await page.goto('http://localhost:8787/#ato');await page.reload();
 await page.locator('[data-adv="trip-demo"]').click();
 await expect(page.locator('#connection-state')).toHaveText('Готовая демонстрационная поездка');
 await page.goto('http://localhost:8787/#system');
 await page.route('**/api/stream',route=>route.abort());
 await page.locator('[data-adv="connect"]').click();
 await expect(page.locator('#connection-state')).toHaveText('Переподключение',{timeout:10000});
 await page.unroute('**/api/stream');
 await expect(page.locator('#connection-state')).toHaveText('SSE · LIVE',{timeout:15000});
 assert((await page.request.get('http://localhost:8787/api/health')).ok());
 results.push({sse:'PASS: interrupted stream, reconnect state, telemetry recovery',workerHealth:'200'});
 fs.writeFileSync('.jol-local/ui-review/ui-checks.json',JSON.stringify(results,null,2));
 console.log(JSON.stringify(results));
}finally{await browser.close()}
