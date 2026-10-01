import fs from 'node:fs';
const packageData=JSON.parse(fs.readFileSync('data/eco-package.json','utf8'));
fs.writeFileSync('web/synthetic-data.js','// Generated from data/eco-package.json.\nexport const syntheticData='+JSON.stringify(packageData,null,2)+';\n');
