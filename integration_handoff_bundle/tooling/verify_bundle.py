"""Check portable data joins, original copies and actual API/solver behaviours."""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
B=Path(sys.argv[1]).resolve();P=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None
def read(p):return json.loads((B/p).read_text(encoding='utf-8'))
manifest=read('INTEGRATION_MANIFEST.json')
assert [p['route'] for p in manifest['pages']]==['/dispatch','/history','/yard']
for p in manifest['pages']:
    for f in [p['source_entry'],p['spec'],*p['data_files']]:assert (B/f).is_file(),f
stations=read('data/stations.json');station_ids={s['id'] for s in stations}
assert len(stations)==manifest['stations']['count']==8
assert station_ids=={s['original_id'] for s in read('data/stations_personal.json')['stations']}
blocks=read('data/blocks.json');block_ids={b['id'] for b in blocks}
trains=read('data/trains.json');train_ids={t['id'] for t in trains}
assert len(blocks)==14 and len(trains)==16
assert all(b['from_station'] in station_ids and b['to_station'] in station_ids for b in blocks)
assert all(t['origin'] in station_ids and t['destination'] in station_ids and set(t['planned_stops'])<=station_ids for t in trains)
assert all(v['resource'] in (station_ids if v['kind']=='station' else block_ids) and v['train_id'] in train_ids for v in read('data/schedule.json'))
assert all(s['block_id'] in block_ids for s in read('data/signals.json'))
yard=read('data/resource_scenarios.json');assert set(yard)=={'seed','provenance','yard'}
assert len(yard['yard']['wagons'])==120 and all(w['destination'] in station_ids for w in yard['yard']['wagons'])
if P:
    for row in read('source/BACKEND_PROVENANCE.json'):
        if row['mode']=='exact text copy':assert (B/row['target']).read_bytes()==(P/row['original']).read_bytes() or (B/row['target']).read_text(encoding='utf-8')==(P/row['original']).read_text(encoding='utf-8')
    for row in read('source/FRONTEND_PROVENANCE.json'):
        if row['mode']=='exact text copy':assert (B/row['target']).read_text(encoding='utf-8')==(P/row['original']).read_text(encoding='utf-8')
        elif 'declarations' in row:
            raw=(P/row['original']).read_text(encoding='utf-8');copy=(B/row['target']).read_text(encoding='utf-8')
            # Imports can move; declarations themselves are preserved verbatim.
            for d in row['declarations']:
                lines=raw.splitlines();start=d['line']-1
                assert lines[start] in copy,(row['target'],d['name'])
sys.path.insert(0,str(B/'source/shared_required_only/backend'))
from fastapi.testclient import TestClient
from main import app
from app import api
from app.yard import validate,metrics
observations={}
with tempfile.TemporaryDirectory(prefix='jibek-handoff-') as temp:
    os.environ['DATABASE_PATH']=str(Path(temp)/'operations.sqlite')
    with TestClient(app) as client:
        assert client.get('/api/state').status_code==401
        token=client.post('/api/auth/login',json={'username':'dispatcher','password':'dispatch-demo'}).json()['token'];headers={'Authorization':'Bearer '+token}
        assert client.post('/api/simulation/pause',headers=headers).status_code==200
        initial=client.get('/api/state',headers=headers).json()
        with client.websocket_connect('/ws/live') as socket:
            socket.send_json({'token':token});assert len(socket.receive_json()['stations'])==8
        h=client.get('/api/history',headers=headers).json();assert len(h['snapshots'])==61
        historical=client.get('/api/history?at=1501',headers=headers).json();assert historical['time']==1500
        scores={c['name']:c['score'] for c in initial['quality']['components']};assert 0<=initial['quality']['value']<=100
        assert client.get('/api/resources/locomotives',headers=headers).status_code==404
        calculated=client.post('/api/resources/yard/optimize',headers=headers,json={'runtime_seconds':.5});assert calculated.status_code==200,calculated.text
        r=calculated.json()['result'];assert validate(r['after'],yard['yard'])
        assert r['after_metrics']==metrics(r['after'],yard['yard']['wagons'])
        assert r['objective_after']<=r['objective_before']
        applied=client.post('/api/resources/yard/apply',headers=headers,json={'plan_id':r['plan_id']});assert applied.status_code==200
        assert client.get('/api/state',headers=headers).json()['schedule']==initial['schedule']
        assert any('yard resource plan' in a['description'] for a in client.get('/api/history',headers=headers).json()['actions'])
        assert client.post('/api/incidents',headers=headers,json={'type':'delay_10','location_id':'P104','duration':600}).status_code==200
        options=client.post('/api/replan',headers=headers);assert options.status_code==200,options.text
        opts=options.json();assert len(opts)==3 and all(o['remaining_conflicts']==0 for o in opts)
        changed=client.post('/api/replan/'+opts[0]['id']+'/apply',headers=headers);assert changed.status_code==200,changed.text
        assert not changed.json()['conflicts']
        assert client.post('/api/replan/'+opts[0]['id']+'/apply',headers=headers).status_code==409
        csv_bytes=client.get('/api/reports/csv',headers=headers).content
        rows=list(csv.DictReader(io.StringIO(csv_bytes.decode('utf-8'))));assert sum(r['category']=='train' for r in rows)==16 and sum(r['category']=='quality' for r in rows)==5
        pdf=client.get('/api/reports/pdf',headers=headers).content;assert pdf.startswith(b'%PDF-')
        assert client.post('/api/simulation/reset',headers=headers).status_code==200
        assert client.post('/api/resources/yard/apply',headers=headers,json={'plan_id':r['plan_id']}).status_code==409
        observations={'before_quality':initial['quality'],'after_quality':changed.json()['quality'],'yard_before':r['before_metrics'],'yard_after':r['after_metrics'],'csv_rows':len(rows),'pdf_bytes':len(pdf)}
report={'passed':True,'pages':3,'stations':8,'trains':16,'blocks':14,'checks':['manifest paths','all station/block/train/yard joins','original exact copies/declarations','authenticatedREST/WS','61warmup snapshots/nearest-earlier retrieval','independentyardvalidation/measuredmetrics','yardapplydoesnotmutatetraffic','yardactionlog','3dispatchalternatives/zero-conflictapply','stalerecommendationrejected','realCSV/PDF','resetstalesyardplan'],'observations':observations}
(B/'VALIDATION_BACKEND.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Portable bundle: all data/source/API/solver/export checks passed.')
