import './build-demo.mjs';
import {build} from 'esbuild';
import fs from 'node:fs';
import path from 'node:path';
await build({entryPoints:['web/report.js'],outfile:'web/vendor/report.bundle.js',bundle:true,format:'esm',minify:true});
await build({entryPoints:['web/extension/host.tsx'],outfile:'web/vendor/extension.bundle.js',bundle:true,format:'esm',minify:true,jsx:'automatic'});
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.ttf':'font/ttf','.png':'image/png','.json':'application/json'};const assets={};function walk(dir){for(const name of fs.readdirSync(dir)){const p=path.join(dir,name);if(fs.statSync(p).isDirectory())walk(p);else assets['/'+path.relative('web',p).split(path.sep).join('/')]={type:types[path.extname(p)]||'application/octet-stream',body:fs.readFileSync(p).toString('base64')};}}walk('web');fs.writeFileSync('server/assets.generated.json',JSON.stringify(assets));fs.rmSync('dist',{recursive:true,force:true});await build({entryPoints:['server/index.js'],outfile:'dist/server/index.js',bundle:true,format:'esm',platform:'browser',target:'es2022',minify:true});fs.mkdirSync('dist/.openai',{recursive:true});fs.copyFileSync('.openai/hosting.json','dist/.openai/hosting.json');

