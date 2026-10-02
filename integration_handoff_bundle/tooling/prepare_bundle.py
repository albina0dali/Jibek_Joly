"""Build data inventory and a minimal standalone backend without editing origin."""
import ast
import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT=Path(sys.argv[1]).resolve()
BUNDLE=Path(sys.argv[2]).resolve()
records=[]
def write(name,value):
    p=BUNDLE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(original,target,transform=None):
    raw=(PROJECT/original).read_text(encoding='utf-8')
    write(target,transform(raw) if transform else raw)
    records.append(dict(original=original,target=target,original_sha256=hashlib.sha256((PROJECT/original).read_bytes()).hexdigest(),mode='adapted path/scope; see SOURCE_PROVENANCE.md' if transform else 'exact text copy'))
backend='source/shared_required_only/backend/'
for name in ['__init__','models','conflicts','scheduler','quality','ato','ingestion','history','reports']:
    copy(f'backend/app/{name}.py',backend+f'app/{name}.py')
copy('backend/app/simulator.py',backend+'app/simulator.py',lambda s:s.replace("DATA = Path(__file__).resolve().parents[1] / 'data'","DATA = Path(__file__).resolve().parents[4] / 'data'").replace('from data.generate_demo_data import generate','from .generate_demo_data import generate').replace('            generate()','            generate(output=DATA)'))
copy('backend/app/yard.py',backend+'app/yard.py')
copy('backend/main.py',backend+'main.py')
copy('backend/requirements.txt',backend+'requirements.txt')
copy('backend/data/generate_demo_data.py',backend+'app/generate_demo_data.py',lambda s:s.replace('output = Path(output or Path(__file__).parent)',"output = Path(output or Path(__file__).resolve().parents[4] / 'data')"))
# Generator is needed only for missing schedule recovery. Yard input is preserved
# as data, so no locomotive/maintenance generator is part of the dependency graph.
api=(PROJECT/'backend/app/api.py').read_text(encoding='utf-8')
tree=ast.parse(api)
allowed={'calculate_latest','Login','ResourceCalculation','ResourceApply','user','admin','login','state','inject','replan','apply','control','get_quality','history','settings','update_settings','report','health','resource_snapshot','resource_optimize','resource_apply','websocket'}
lines=api.splitlines(keepends=True)
parts=[]
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and node.name not in allowed:continue
    first=min([node.lineno]+[d.lineno for d in getattr(node,'decorator_list',[])])-1
    parts.append(''.join(lines[first:node.end_lineno]))
adapted='\n\n'.join(parts).replace("('yard','locomotives','maintenance')","('yard',)")
write(backend+'app/api.py',adapted)
records.append(dict(original='backend/app/api.py',target=backend+'app/api.py',mode='AST top-level extraction; only required routes + scenario/configuration support; resource endpoints limited to yard'))
write(backend+'app/resources.py','''"""Yard-only adapter extracted from original ResourcePlanning lifecycle."""
import copy
import json
import threading
from pathlib import Path
from . import yard

class ResourcePlanning:
    def __init__(self,sim):
        self.sim=sim
        self.lock=threading.RLock()
        self.dataset=json.loads((Path(__file__).resolve().parents[4]/'data'/'resource_scenarios.json').read_text(encoding='utf-8'))
        self.results={}
        self.applied={}
        self.version=0
    def snapshot(self,module):
        if module!='yard':raise ValueError('Unknown resource planning module')
        with self.lock:
            data=copy.deepcopy(self.dataset['yard'])
            initial=yard.baseline(data)
            return dict(module=module,seed=self.dataset['seed'],provenance='SIMULATED / DERIVED',data=data,baseline=initial,baseline_metrics=yard.metrics(initial,data['wagons']),result=self.results.get('yard'),applied=self.applied.get('yard'),version=self.version)
    def calculate(self,module,train_id='F103',runtime=2):
        if module!='yard':raise ValueError('Unknown resource planning module')
        with self.lock:
            version=self.version
            data=copy.deepcopy(self.dataset['yard'])
        result=yard.solve(data,runtime)
        with self.lock:
            if version!=self.version:raise ValueError('Scenario changed during calculation; solve the current scenario again')
            result['plan_id']=f'yard-{version}-{len(self.sim.store.actions())}'
            result['version']=version
            self.results['yard']=result
        with self.sim.lock:self.sim.store.log(self.sim.time,f'yard optimization computed; {result["calculation_time_ms"]:.0f} ms; synthetic resources')
        return self.snapshot(module)
    def apply(self,module,plan_id,option_id=None):
        if module!='yard':raise ValueError('Unknown resource planning module')
        with self.lock:
            result=self.results.get('yard')
            if not result or result['plan_id']!=plan_id or result['version']!=self.version:raise ValueError('Resource plan is stale; calculate again')
            yard.validate(result['after'],self.dataset['yard'])
            self.applied['yard']=dict(plan_id=plan_id,option_id=option_id,time=self.sim.time,provenance='SIMULATED / DERIVED')
        with self.sim.lock:self.sim.store.log(self.sim.time,f'Applied synthetic yard resource plan {plan_id}')
        return self.snapshot(module)
    def reset(self):
        with self.lock:
            self.version+=1
            self.results={}
            self.applied={}
''')
records.append(dict(original='backend/app/resources.py',target=backend+'app/resources.py',mode='Yard branch adapter; original yard response/validation/lifecycle retained; fleet/maintenance branches excluded'))
inventory=[]
for file in sorted((PROJECT/'backend/data').glob('*.json')):
    data=json.loads(file.read_text(encoding='utf-8'))
    item=dict(source='backend/data/'+file.name,original_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),kind=type(data).__name__,count=len(data),fields=list(data[0]) if isinstance(data,list) and data else list(data) if isinstance(data,dict) else [],included=True)
    if file.name=='resource_scenarios.json':
        item['selection']=['seed','provenance','yard'];item['excluded_sections']=['fleet','maintenance'];item['nested_counts']={k:len(data['yard'][k]) for k in ['wagons','tracks','shunters']}
        write('data/'+file.name,{k:data[k] for k in ['seed','provenance','yard']})
    else:copy('backend/data/'+file.name,'data/'+file.name)
    inventory.append(item)
stations=json.loads((PROJECT/'backend/data/stations.json').read_text(encoding='utf-8'))
rows=[]
for order,s in enumerate(sorted(stations,key=lambda s:s['distance_km']),1):
    direct=s['id'] in ('S3','S4','S5','S7','S8')
    rows.append(dict(**s,original_id=s['id'],display_name=s['name'],coordinates=None,coordinate_note='No latitude/longitude in original dataset; distance_km is corridor chainage, not coordinates',route='Arqa — Dala (fictional corridor)',order_in_corridor=order,used_in=['schedule.json','timetable.json','trains.json (origin/destination/planned_stops)','signals via blocks','history snapshot stations']+(['yard.station_id' if s['id']=='S7' else 'yard.wagons[].destination'] if direct else []),page_dependencies=['movement-plan','history-reports']+(['wagons-consists'] if direct else [])))
write('data/stations_personal.json',dict(station_count=len(rows),route='Arqa — Dala',stations=rows))
write('data/DATA_INVENTORY.json',inventory)
write('source/BACKEND_PROVENANCE.json',records)
for name in ['index.html','tsconfig.json','package-lock.json']:
    copy('frontend/'+name,'source/shared_required_only/frontend/'+name)
pkg=json.loads((PROJECT/'frontend/package.json').read_text(encoding='utf-8'));pkg['scripts']={'dev':'vite --host 127.0.0.1 --port 5175','build':'tsc -b && vite build','preview':'vite preview --host 127.0.0.1 --port 4175'}
write('source/shared_required_only/frontend/package.json',pkg)
write('source/shared_required_only/frontend/vite.config.ts',"import {defineConfig} from 'vite';\nimport react from '@vitejs/plugin-react';\nimport path from 'node:path';\nexport default defineConfig({plugins:[react()],resolve:{dedupe:['react','react-dom'],alias:Object.fromEntries(['react','react-dom','react-router-dom','lucide-react'].map(name=>[name,path.resolve('node_modules',name)]))},server:{fs:{allow:[path.resolve('..','..','..')]},proxy:{'/api':'http://127.0.0.1:8001','/ws':{target:'ws://127.0.0.1:8001',ws:true},'/health':'http://127.0.0.1:8001'}}});\n")
# TypeScript must resolve packages for page source outside frontend root.
config=json.loads((PROJECT/'frontend/tsconfig.json').read_text(encoding='utf-8'));config['compilerOptions']['baseUrl']='.';config['compilerOptions']['paths']={'react':['node_modules/@types/react'],'react/*':['node_modules/@types/react/*'],'react-router-dom':['node_modules/react-router-dom'],'lucide-react':['node_modules/lucide-react']};config['include']=['src','../../movement_plan','../../history_reports','../../wagons_consists'];write('source/shared_required_only/frontend/tsconfig.json',config)
write('assets/README.md','# Assets\n\nNo local bitmap/logo/font files are required. Charts/topology/wagons are inline SVG. Icons come from lucide-react. Optional reference CSS imports IBM Plex fonts from Google Fonts; system fallbacks work offline. The team can replace all presentation styles. reference_screenshots are validation evidence, not production assets.\n')
print('Portable backend/data prepared; station count:',len(stations))
