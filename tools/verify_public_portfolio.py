"""Reproduce public source tests only. No private repository or credentials required."""
import json,os,pathlib,re,subprocess,sys
root=pathlib.Path(os.environ.get('GITHUB_WORKSPACE','.')).resolve();out=root/'public-evidence';out.mkdir(exist_ok=True)
repos={
 'sage-situated-companion':('96553e30eb4dab43902e23545e950824fee268f6',[]),
 'CERL-Preemptive':('55d70f149a0a63cd7d05bea5f85d7de04342ee1b',[]),
 'Commons-Unified-Protocol':('f07ecada3c3cfb771c7f88f2095b21e95242d07a',[]),
 'aurora-sovereign-core':('c588811e72140501732b0161076adff830b8d586',[]),
 'commons-sentience-sandbox':('c3a96e6376dfed8827793b5f5f1b46fa16b69422',['tests/test_commons_governance.py','tests/test_challenge_lab_scenario.py','tests/test_validation_scenarios.py','tests/test_civic_continuum_demo.py']),
 'maya-node':('a2d24f8689a274444431967cd01a924f272bc61d',['tests/integration/test_real_file_gate.py']),
}
env=os.environ.copy();env.pop('OPENAI_API_KEY',None);results=[]
for name,(sha,paths) in repos.items():
 dest=root/'public-sources'/name;dest.mkdir(parents=True,exist_ok=True)
 commands=[['git','init',str(dest)],['git','-C',str(dest),'fetch','--depth=1','https://github.com/mommommy1960-lang/'+name+'.git',sha],['git','-C',str(dest),'checkout','--detach','FETCH_HEAD']]
 try:
  for command in commands:subprocess.run(command,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
  command=[sys.executable,'-m','pytest','-q',*paths,'--junitxml='+str(out/(name+'.xml'))]
  r=subprocess.run(command,cwd=dest,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);output=r.stdout;passed=r.returncode==0
 except Exception as e:output=str(e);passed=False
 (out/(name+'.log')).write_text(output)
 m=re.search(r'\b(\d+) passed\b',output);count=int(m.group(1)) if m else None
 results.append({'repository':name,'commit':sha,'passed':passed,'tests':count});print(name+': '+('PASS' if passed else 'FAIL')+(' · '+str(count)+' tests' if count else ''),flush=True)
 if not passed:print(output[-8000:],flush=True)
report={'publicSourcesOnly':True,'allPassed':all(x['passed'] for x in results),'testsExcludingSubtests':sum(x['tests'] or 0 for x in results),'suites':results,'boundary':'Public pinned-source tests only. Excludes private web/workbench code, live AI, payments, hardware and independent customer acceptance.'}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
summary='# Public portfolio verification\n\n| Repository | Result | Tests |\n|---|---|---:|\n'+''.join('| '+x['repository']+' | '+('PASS' if x['passed'] else 'FAIL')+' | '+str(x['tests'])+' |\n' for x in results)+'\n'+report['boundary']+'\n'
(out/'summary.md').write_text(summary)
if os.environ.get('GITHUB_STEP_SUMMARY'):
 with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
sys.exit(0 if report['allPassed'] else 1)
