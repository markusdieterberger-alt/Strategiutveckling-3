#!/usr/bin/env python3
"""Collect local checks. Does not compile Pine, run CT, or inspect any account."""
import csv, hashlib, io, json, platform, re, unittest
from datetime import datetime, timezone
from pathlib import Path
import test_qa

ROOT=Path(__file__).resolve().parent

def collect():
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_qa)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (ROOT/'local_test_output.txt').write_text(stream.getvalue())
    summary={'scope':'LOCAL SOURCE AND SYNTHETIC TESTS ONLY; NOT PINE COMPILATION OR CT REPLAY',
             'utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
             'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skipped':len(result.skipped),'native_forward_trades':0,'native_observation_seconds':0}
    budget={}
    for p in (ROOT/'pine').glob('*.pine'):
        s=p.read_text();budget[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'plot_count_static_estimate':len(re.findall(r'^plot\(',s,re.M))+1,
            'request_security_calls':s.count('request.security('),'request_footprint_calls':s.count('request.footprint('),
            'native_compiled_tokens':'UNKNOWN','native_execution_time':'UNKNOWN'}
    summary['source_budget']=budget
    (ROOT/'local_test_results.json').write_text(json.dumps(summary,indent=2)+'\n')
    source=(ROOT/'reference/EAA_CT_SCALPER_STRATEGY_V1.pine').read_text()
    inputs=[];lines=source.splitlines()
    for i,line in enumerate(lines):
        if '= input.' in line or '=input.' in line:
            decl=line; j=i+1
            while decl.count('(')>decl.count(')') and j<len(lines):decl+='\n'+lines[j];j+=1
            inputs.append({'source_line':i+1,'declaration':decl,'native_server_value':'UNKNOWN',
                           'v2_status':'REMOVED_COUNTERFACTUAL_STRESS_LEDGER' if 'eaaStressSlip' in line else 'PRESERVED'})
    config={'scope':'SOURCE DEFAULTS ONLY, NOT EFFECTIVE SERVER SETTINGS',
            'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'strategy_declaration':source[source.index('strategy('):source.index('\n\n',source.index('strategy('))],
            'source_inputs':inputs,'v2_added_inputs':{'v2PineLogs':False,'v2DiagAlerts':False,'v2TraceAllBars':False},
            'diagnostic_added_input':{'v2ConfirmedHtf':False},'v2_fixed_confirmed_htf':True,
            'required_native_manifest_fields':['source export/hash','alert creation UTC','alert name','ticker prefix','data delay and entitlement','standard candles','timeframe','chart timezone','session','roll/backadjustment','loaded history range','test start/end','all inputs','all Strategy Properties','commission','slippage','margin','capital','sizing','Bar Magnifier','limit verification','calculation/fill options']}
    (ROOT/'LOCKED_INPUTS.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    manifest=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS.txt':
            manifest.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix())
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(manifest)+'\n')
    print(json.dumps(summary,indent=2))
    if not result.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':collect()
