import copy
import csv
import io
import json
import sys
import base64
import re
import zlib
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'/'extension'))
from app.simulator import Simulator
from app.resources import ResourcePlanning
from app.models import IncidentInput
from app import yard
from app.quality import quality,calculate_movement_index
from app.reports import csv_report,pdf_report
from reportlab.pdfbase import pdfmetrics

def report_text(pdf):
    content=[]
    for raw in re.findall(rb'stream\r?\n(.*?)endstream',pdf,re.S):
        try: content.append(zlib.decompress(base64.a85decode(raw.strip(),adobe=True)))
        except (ValueError,zlib.error): pass
    return b'\n'.join(content).decode('latin1')

@pytest.fixture
def sim():
    s=Simulator(':memory:')
    s.paused=True
    s.resources=ResourcePlanning(s)
    yield s
    s.store.db.close()

def test_baseline_and_dynamic_quality(sim):
    state=sim.snapshot(at=2401)
    assert 88 <= state['quality']['value'] <= 93
    assert len(state['stations'])==8 and len(state['blocks'])==14 and len(state['trains'])==16
    disturbed=copy.deepcopy(state['trains'])
    for train in disturbed: train['delay_seconds']+=900
    assert quality(disturbed,[{'id':'test'}],[],sim.settings)['value']<state['quality']['value']
    assert quality(state['trains'],[],[],sim.settings)['value']==state['quality']['value']
    print('Calculated extension baseline:',state['quality']['value'])

def test_shared_movement_vectors():
    for vector in json.loads((ROOT/'tests'/'movement-index-vectors.json').read_text()):
        v=vector['input']
        _, value=calculate_movement_index(v['weightedDelaySeconds'],v['averageDelaySeconds'],v['utilization'],v['conflicts'],v['energySavingsPercent'])
        assert value==vector['expected']

def test_replan_preview_apply_and_stale_validation(sim):
    live=copy.deepcopy(sim.snapshot())
    sim.replan()
    assert len(sim.options)==3
    assert sim.snapshot()['schedule']==live['schedule']
    option=sim.options[0]
    sim.apply(option['id'])
    assert sim.revision>live['revision']
    assert sim.schedule and sim.store.actions()
    with pytest.raises(ValueError): sim.apply(option['id'])

def test_actual_incident_reduces_quality_and_replan_recovers(sim):
    normal=sim.snapshot()['quality']['value']
    sim.inject(IncidentInput(type='delay_10',location_id='F103',duration=600))
    incident=sim.snapshot()['quality']['value']
    assert incident<normal
    assert 70 <= incident <= 80
    sim.replan()
    assert sim.options
    sim.apply(max(sim.options,key=lambda o:o['quality_index'])['id'])
    recovered=sim.snapshot()['quality']['value']
    assert recovered>incident
    assert 85 <= recovered <= 92
    print('Actual incident QI:',normal,'->',incident,'->',recovered)

def test_history_readonly_and_real_reports(sim):
    before=sim.snapshot()
    replay=sim.store.get(1800)
    assert replay['time']==1800
    assert sim.snapshot()==before
    rows=list(csv.reader(io.StringIO(csv_report(before))))
    assert sum(row[0]=='train' for row in rows)==16
    assert sum(row[0]=='quality' for row in rows)==5
    assert sum(row[0]=='station' for row in rows)==8
    assert all(t['origin'].startswith('team-station-') and t['destination'].startswith('team-station-') for t in before['trains'])
    assert all(s['id'].startswith('team-station-') for s in replay['stations'])
    assert all(s['name'] in csv_report(before) for s in before['stations'])
    pdf=pdf_report(before,sim.store.actions(),sim.store.index())
    assert pdf.startswith(b'%PDF') and len(pdf)>2000
    text=report_text(pdf)
    assert 'Autodispatcher Demo Report' in text
    assert all(train['id'] in text for train in before['trains'])
    assert str(before['quality']['value']) in text
    assert all(s['id'] in text for s in before['stations'])
    assert all(ord(c) in pdfmetrics.getFont('JibekReport').face.charToGlyph for s in before['stations'] for c in s['name'])

def test_yard_apply_isolation_and_constraints(sim):
    before=sim.snapshot()
    state=sim.resources.snapshot('yard')
    assert len(state['data']['wagons'])==120
    assert len(state['data']['tracks'])==4 and len(state['data']['shunters'])==2
    assert state['baseline_metrics']['train_count']==12
    result=sim.resources.calculate('yard',runtime=.1)
    assert yard.validate(result['result']['after'],state['data'])
    assert result['result']['objective_after']<=result['result']['objective_before']
    applied=sim.resources.apply('yard',result['result']['plan_id'])
    assert applied['applied']['plan_id']==result['result']['plan_id']
    after=sim.snapshot()
    assert before['schedule']==after['schedule'] and before['trains']==after['trains']
    assert before['quality']==after['quality']
    print('Yard:',state['baseline_metrics'],'->',result['result']['after_metrics'])
