// Extract only required declarations; preserve their bodies verbatim.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const project=path.resolve(process.argv[2]);
const bundle=path.resolve(process.argv[3]);
const require=createRequire(path.join(project,'frontend/package.json'));
const ts=require('typescript');
const provenance=[];
const read=file=>fs.readFileSync(path.join(project,file),'utf8');
const write=(file,s)=>{fs.mkdirSync(path.dirname(path.join(bundle,file)),{recursive:true});fs.writeFileSync(path.join(bundle,file),s)};
function extract(original,names,target,replacements={}){
 const raw=read(original),ast=ts.createSourceFile(original,raw,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
 const declarations=ast.statements.filter(n=>names.includes(n.name?.text)||ts.isVariableStatement(n)&&n.declarationList.declarations.some(d=>names.includes(d.name.text)));
 if(declarations.length!==names.length)throw Error('Missing declaration in '+original);
 const identifiers=new Set();for(const n of declarations){const visit=x=>{if(ts.isIdentifier(x))identifiers.add(x.text);ts.forEachChild(x,visit)};visit(n)}
 const imports=ast.statements.filter(ts.isImportDeclaration).map(n=>{
  const c=n.importClause;if(!c)return n.getText(ast);
  if(c.namedBindings&&ts.isNamedImports(c.namedBindings)){
   const elements=c.namedBindings.elements.filter(e=>identifiers.has(e.name.text));
   if(!elements.length&&!c.name)return '';
   const spec=replacements[n.moduleSpecifier.text]||n.moduleSpecifier.text;
   return `import ${c.isTypeOnly?'type ':''}${c.name?c.name.text+', ':''}{${elements.map(e=>e.getText(ast)).join(',')}} from '${spec}';`;
  }return n.getText(ast);
 }).filter(Boolean);
 const content=imports.join('\n')+'\n\n'+declarations.map(n=>n.getText(ast)).join('\n\n')+'\n';write(target,content);
 provenance.push({original,target,mode:'AST declaration extraction; original bodies preserved',declarations:declarations.map(n=>({name:n.name?.text||n.declarationList.declarations[0].name.text,line:ast.getLineAndCharacterOfPosition(n.getStart(ast)).line+1}))});
}
const shared='../shared_required_only/frontend/src/';
const pageImports={'./i18n':shared+'i18n','./types':shared+'types','./components':shared+'components','./services':shared+'services'};
extract('frontend/src/pages.tsx',['Dispatch'],'source/movement_plan/Dispatch.tsx',pageImports);
extract('frontend/src/pages.tsx',['History'],'source/history_reports/History.tsx',pageImports);
for(const file of ['source/movement_plan/Dispatch.tsx','source/history_reports/History.tsx'])write(file,fs.readFileSync(path.join(bundle,file),'utf8')+`\nimport type {PageProps} from '${shared}page-contract';\nimport {PageTitle} from '${shared}PageTitle';\n`);
extract('frontend/src/pages.tsx',['PageTitle'],'source/shared_required_only/frontend/src/PageTitle.tsx');
extract('frontend/src/pages.tsx',['PageProps'],'source/shared_required_only/frontend/src/page-contract.ts');
extract('frontend/src/components.tsx',['trainColor','Badge','Panel','Network','Diagram','TrainDrawer'],'source/shared_required_only/frontend/src/components.tsx');
extract('frontend/src/types.ts',['Station','Block','Conflict','Incident','Train','Visit','Quality','Option','Snapshot','Session'],'source/shared_required_only/frontend/src/types.ts');
extract('frontend/src/resource-types.ts',['Wagon','YardTrain','YardData','YardMetrics','OptimizationResult','ResourceState','YardState'],'source/wagons_consists/resource-types.ts');
extract('frontend/src/resource-pages.tsx',['useResource','Provenance','CalculateButton','CompareMetric','YardBrain','YardSchematic'],'source/wagons_consists/YardBrain.tsx',{
 './pages':shared+'page-contract','./components':shared+'components','./services':shared+'services','./i18n':shared+'i18n','./resource-types':'./resource-types'});
let yard=fs.readFileSync(path.join(bundle,'source/wagons_consists/YardBrain.tsx'),'utf8');
yard=yard.replace(`import {PageTitle} from '${shared}page-contract';`,`import {PageTitle} from '${shared}PageTitle';`);write('source/wagons_consists/YardBrain.tsx',yard);
let main=read('frontend/src/main.tsx');
main=main.replace(/import \{Overview[^\n]+\n/,'').replace(/import \{YardBrain[^\n]+\n/,'').replace("import type {PageProps} from './pages';","import type {PageProps} from './page-contract';\nimport {Dispatch} from '../../../movement_plan/Dispatch';\nimport {History} from '../../../history_reports/History';\nimport {YardBrain} from '../../../wagons_consists/YardBrain';");
main=main.replace(/const navigation=\[[^\n]+/,'const navigation=[{path:\'/dispatch\',label:"Dispatch Plan",icon:ChartNoAxesCombined},{path:\'/history\',label:"History & Reports",icon:HistoryIcon},{path:\'/yard\',label:"Yard Brain",icon:Layers}];');
main=main.replace(/<Route path="(?:\/|\/traffic|\/incidents|\/advisory|\/analytics|\/locomotives|\/maintenance|\/settings)" element=\{<[^>]+>\}\/?>/g,'');
main=main.replace('<Navigate to="/" replace/>','<Navigate to="/dispatch" replace/>');
const ast=ts.createSourceFile('main.tsx',main,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
const used=new Set();for(const n of ast.statements.filter(n=>!ts.isImportDeclaration(n))){const visit=x=>{if(ts.isIdentifier(x))used.add(x.text);ts.forEachChild(x,visit)};visit(n)}
for(const n of [...ast.statements].reverse())if(ts.isImportDeclaration(n)&&n.moduleSpecifier.text==='lucide-react'){
 const names=n.importClause.namedBindings.elements.filter(e=>used.has(e.name.text)).map(e=>e.getText(ast));
 main=main.slice(0,n.getStart(ast))+`import {${names.join(',')}} from 'lucide-react';`+main.slice(n.end);
}
write('source/shared_required_only/frontend/src/main.tsx',main);
provenance.push({original:'frontend/src/main.tsx',target:'source/shared_required_only/frontend/src/main.tsx',mode:'Reference host adapter: only three routes/nav links; root redirects /dispatch; unused imports removed; remaining shell unchanged'});
for(const name of ['services.ts','hooks.ts','i18n.tsx','locales/catalog.json','locales/resources.json']){write('source/shared_required_only/frontend/src/'+name,read('frontend/src/'+name));provenance.push({original:'frontend/src/'+name,target:'source/shared_required_only/frontend/src/'+name,mode:'exact text copy'})}
// Styles are reference assets, optional for team design. Remove rules exclusively
// targeting omitted pages; preserve generic rules and responsive ancestors.
const postcss=require('postcss');
for(const name of ['style.css','resource-style.css']){
 const css=postcss.parse(read('frontend/src/'+name));
 css.walkRules(rule=>{
  const omitted=/\.(?:overview-grid|operational-summary|quality-kpi|quality-track|summary-metric|attention[\w-]*|healthy-state|next-timeline|timeline-time|network-foot|incident[\w-]*|inject-form|recovery[\w-]*|advisory-summary|phases|phase|analytics[\w-]*|contribution[\w-]*|trend|factors|settings-fields|sensor[\w-]*|maintenance[\w-]*|risk-policy|intervention-timeline|fleet[\w-]*)(?![\w-])/;
  const keep=rule.selectors.filter(s=>!omitted.test(s));if(!keep.length)rule.remove();else rule.selectors=keep;
 });write('source/shared_required_only/frontend/src/'+name,css.toString());
 provenance.push({original:'frontend/src/'+name,target:'source/shared_required_only/frontend/src/'+name,mode:'Optional reference styling: selectors exclusively belonging to omitted pages removed'});
}
write('source/FRONTEND_PROVENANCE.json',JSON.stringify(provenance,null,2));
console.log('Extracted only Dispatch, History, YardBrain and required shared declarations.');
