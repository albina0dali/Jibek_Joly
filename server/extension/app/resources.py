"""Yard-only adapter extracted from original ResourcePlanning lifecycle."""
import copy
import json
import threading
from pathlib import Path
from . import yard

class ResourcePlanning:
    def __init__(self,sim):
        self.sim=sim
        self.lock=threading.RLock()
        self.dataset=json.loads((Path(__file__).resolve().parents[3] / 'data' / 'extensions' / 'operations'/'resource_scenarios.json').read_text(encoding='utf-8'))
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
