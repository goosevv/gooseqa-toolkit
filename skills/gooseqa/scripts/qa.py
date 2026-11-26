"""GooseQA Toolkit: local evidence-first QA workspace. Python standard library only."""
import argparse, contextlib, datetime as dt, json, os, pathlib, re, sys, tempfile, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from urllib.request import build_opener, ProxyHandler
import hashlib, subprocess, webbrowser, shutil

VERSION = "0.2.0"

ROOT = pathlib.Path(__file__).resolve().parent
DATA = pathlib.Path(os.environ.get('GOOSEQA_DATA', pathlib.Path.cwd() / '.gooseqa')).resolve()
STAGES = ['Discovery','Risk analysis','Test design','Automation plan','Implementation','Execution','Review','CI & reporting']
MODES = ['LEARN','PAIR','AUTO']
KINDS = ['UI','API','Unit','Integration','Visual','Desktop','Game','AI']
RESULTS = ['PASS','FAIL','BLOCKED','SKIPPED']

def now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
def uid(): return uuid.uuid4().hex[:12]
def clean(v, label, limit=3000, required=True):
    if not isinstance(v,str) or len(v)>limit or (required and not v.strip()): raise ValueError(f'{label}: expected text (1–{limit} characters)' if required else f'{label}: expected text (max {limit})')
    return v.strip()
def choice(v, options, label):
    if v not in options: raise ValueError(f'{label}: choose {", ".join(options)}')
    return v

def empty(): return {'version':1,'projects':[]}
def read():
    path=DATA/'state.json'
    if not path.exists(): return empty()
    obj=json.loads(path.read_text(encoding='utf-8'))
    if obj.get('version')!=1 or not isinstance(obj.get('projects'),list): raise ValueError('Unsupported state format')
    return obj

@contextlib.contextmanager
def lock(timeout=4):
    DATA.mkdir(parents=True,exist_ok=True)
    p=DATA/'state.lock'; until=time.monotonic()+timeout
    while True:
        try: fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY); break
        except FileExistsError:
            if time.monotonic()>until: raise ValueError('State is locked; close other writers. If no writer is active, remove state.lock manually.')
            time.sleep(.05)
    try: os.write(fd,str(os.getpid()).encode()); yield
    finally: os.close(fd); p.unlink(missing_ok=True)

def save(s):
    fd,tmp=tempfile.mkstemp(dir=DATA,prefix='state-',suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(s,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,DATA/'state.json')
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def project(s,pid):
    for p in s['projects']:
        if p['id']==pid: return p
    raise ValueError('Project not found')
def item(rows,id):
    for x in rows:
        if x['id']==id: return x
    raise ValueError('Item not found')
def gates(p):
    cases=p['cases']; critical=[c for c in cases if c['priority']=='P0']; latest={r['case_id']:r for r in p['runs']}
    return [bool(p['notes'].get('0')),bool(p['risks']),bool(cases) and all(c['expected'] for c in cases) and all(any(c['risk_id']==r['id'] and c['priority']=='P0' for c in cases) for r in p['risks'] if r['priority']=='P0'),bool(p['notes'].get('3')),bool(cases) and all(c['automation_ref'] for c in critical) and any(c['automation_ref'] for c in cases),bool(critical) and all(c['id'] in latest and latest[c['id']]['result']=='PASS' and latest[c['id']]['evidence'] for c in critical),bool(p['notes'].get('6')) and not any(b['status']=='OPEN' and b['severity']=='P0' for b in p['bugs']),bool(p['notes'].get('7'))]

def mutate(s,action,d):
    if not isinstance(d,dict): raise ValueError('Payload must be an object')
    if action=='project':
        p={'id':uid(),'name':clean(d.get('name'),'name',100),'repo':clean(d.get('repo',''),'repo',500,False),'mode':choice(d.get('mode','LEARN'),MODES,'mode'),'stage':0,'notes':{},'risks':[],'cases':[],'runs':[],'bugs':[],'tasks':[],'demo':False,'created':now()}; s['projects'].append(p); return p
    p=project(s,d.get('project_id')); row={'id':uid(),'created':now()}
    if action=='mode': p['mode']=choice(d.get('mode'),MODES,'mode')
    elif action=='note':
        stage=d.get('stage');
        if type(stage) is not int or not 0<=stage<len(STAGES): raise ValueError('Invalid stage')
        p['notes'][str(stage)]=clean(d.get('text'),'note',12000,False)
    elif action=='advance':
        i=p['stage']; blocked=[STAGES[j] for j in range(min(i+1,8)) if not gates(p)[j]]
        if i>=8: raise ValueError('Workflow already complete')
        if blocked: raise ValueError('Missing gate(s): '+', '.join(blocked))
        p['stage']+=1
    elif action=='risk':
        row.update(title=clean(d.get('title'),'title',200),priority=choice(d.get('priority'),['P0','P1','P2'],'priority'),reason=clean(d.get('reason'),'reason'));p['risks'].append(row);return row
    elif action=='case':
        risk=d.get('risk_id','');
        if risk: item(p['risks'],risk)
        row.update(title=clean(d.get('title'),'title',200),kind=choice(d.get('kind'),KINDS,'kind'),priority=choice(d.get('priority'),['P0','P1','P2'],'priority'),risk_id=risk,steps=clean(d.get('steps'),'steps'),expected=clean(d.get('expected'),'expected'),automation_ref=clean(d.get('automation_ref',''),'automation_ref',500,False));p['cases'].append(row);return row
    elif action=='automate':
        c=item(p['cases'],d.get('case_id'));c['automation_ref']=clean(d.get('automation_ref'),'automation_ref',500,False);return c
    elif action=='run':
        c=item(p['cases'],d.get('case_id')); result=choice(d.get('result'),RESULTS,'result'); ev=clean(d.get('evidence',''),'evidence',3000,result in ['PASS','FAIL']);
        row.update(case_id=c['id'],result=result,evidence=ev,command=clean(d.get('command',''),'command',1000,False),source=choice(d.get('source','manual'),['manual','agent','ci'],'source'));p['runs'].append(row);return row
    elif action=='bug':
        case=d.get('case_id','');
        if case:item(p['cases'],case)
        row.update(title=clean(d.get('title'),'title',200),severity=choice(d.get('severity'),['P0','P1','P2'],'severity'),case_id=case,details=clean(d.get('details'),'details'),status='OPEN');p['bugs'].append(row);return row
    elif action=='bug-status': item(p['bugs'],d.get('id'))['status']=choice(d.get('status'),['OPEN','CLOSED'],'status')
    elif action=='task': row.update(title=clean(d.get('title'),'title',200),details=clean(d.get('details',''),'details',3000,False),done=False);p['tasks'].append(row);return row
    elif action=='task-status':
        if type(d.get('done')) is not bool: raise ValueError('done must be boolean')
        item(p['tasks'],d.get('id'))['done']=d['done']
    else: raise ValueError('Unknown action')
    return p

def apply(action,d):
    with lock():
        s=read();r=mutate(s,action,d);save(s);return r

def snapshot():
    s=read()
    for p in s['projects']:p['gates']=gates(p)
    return s

def report(p):
    out=[f'# {p["name"]} — QA report',f'Mode: {p["mode"]} | Project ID: {p["id"]}', 'DEMO / synthetic data' if p['demo'] else 'Recorded evidence is user/agent supplied; not independently verified.', '', '## Workflow']
    out += [f'- [{"x" if v else " "}] {name}' for name,v in zip(STAGES,gates(p))]
    for k,v in p['notes'].items(): out += [f'### {STAGES[int(k)]}',v]
    for key,title in [('risks','Risks'),('cases','Test cases'),('runs','Recorded runs'),('bugs','Defects'),('tasks','Learning tasks')]:
        out += ['',f'## {title}']
        for x in p[key]:out += ['','### '+x.get('title',x.get('result',x['id']))]+[f'- {k}: {v}' for k,v in x.items() if k!='title']
    return '\n'.join(out)+'\n'

def demo():
    with lock():
        s=read();p=mutate(s,'project',{'name':'Bug Report Builder · DEMO','repo':'Synthetic example — not a real run','mode':'LEARN'});p['demo']=True;id=p['id'];p['notes']['0']='Example: local form, draft persistence, report generation. This is illustrative, not an audit.'
        r=mutate(s,'risk',{'project_id':id,'title':'Draft lost on reload','priority':'P0','reason':'QA report data loss'});mutate(s,'case',{'project_id':id,'risk_id':r['id'],'title':'Draft persists on reload','priority':'P0','kind':'UI','steps':'Fill title; reload','expected':'Title remains unchanged'});mutate(s,'task',{'project_id':id,'title':'Write first Playwright assertion','details':'Use toHaveValue; explain why it detects regression.'});p['stage']=1;save(s);return p

class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,ctype='application/json; charset=utf-8'):
        b=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");self.end_headers();self.wfile.write(b)
    def valid_host(self):return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.valid_host():return self.send(403,{'error':'Local host only'})
        path=urlparse(self.path).path
        try:
            if path=='/api/health':return self.send(200,{'app':'gooseqa','version':VERSION,'workspace':workspace_id()})
            if path=='/api/state':return self.send(200,snapshot())
            if path.startswith('/api/report/'):
                p=project(read(),path.split('/')[-1]);return self.send(200,report(p).encode(),'text/plain; charset=utf-8')
            files={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}
            if path in files:
                f,t=files[path];return self.send(200,(ROOT/'static'/f).read_bytes(),t+'; charset=utf-8')
            self.send(404,{'error':'Not found'})
        except (ValueError,KeyError,OSError) as e:self.send(400,{'error':str(e)})
    def do_POST(self):
        if not self.valid_host() or self.headers.get('Origin') not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:return self.send(403,{'error':'Local same-origin requests only'})
        try:
            if not self.path.startswith('/api/action/'):return self.send(404,{'error':'Not found'})
            if self.headers.get_content_type()!='application/json':raise ValueError('Expected JSON')
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=100000:raise ValueError('Invalid payload size')
            d=json.loads(self.rfile.read(n));self.send(200,apply(self.path.split('/')[-1],d))
        except (ValueError,KeyError,TypeError,OSError) as e:self.send(400,{'error':str(e)})

def workspace_id():
    return hashlib.sha256(os.path.normcase(str(DATA.resolve())).encode()).hexdigest()

def ensure_project(mode=None):
    repo=str(pathlib.Path.cwd().resolve())
    with lock():
        s=read()
        matches=[p for p in s['projects'] if not p['demo'] and os.path.normcase(p['repo'])==os.path.normcase(repo)]
        if not matches:
            matches=[p for p in s['projects'] if not p['demo'] and p['name']==pathlib.Path(repo).name and not p['repo']]
        if len(matches)>1: raise ValueError('Multiple matching projects; resolve duplicates in the workspace first.')
        if matches:
            p=matches[0]
            if not p['repo']:p['repo']=repo
            if mode: p['mode']=choice(mode,MODES,'mode')
            created=False
        else:
            p=mutate(s,'project',{'name':pathlib.Path(repo).name or repo,'repo':repo,'mode':mode or 'LEARN'})
            created=True
        save(s)
        return p,created

def probe(port):
    try:
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{port}/api/health',timeout=.35) as r:
            return json.load(r)
    except (OSError,ValueError):return None

_children=[]

def launch_dashboard(port=8766):
    # Serialize launch requests for the same workspace; the health endpoint never takes this lock.
    if not 1024<=port<=65516: raise ValueError('Port must be between 1024 and 65516')
    import socket
    with lock(timeout=20):
        for candidate in range(port,port+20):
            health=probe(candidate)
            if health=={'app':'gooseqa','version':VERSION,'workspace':workspace_id()}:
                return candidate,False,None
        for candidate in range(port,port+20):
            with socket.socket() as sock:
                try:sock.bind(('127.0.0.1',candidate))
                except OSError:continue
            env=dict(os.environ,GOOSEQA_DATA=str(DATA))
            flags={'creationflags':subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
            with (DATA/'dashboard.log').open('ab') as log:
                child=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve()),'serve','--port',str(candidate)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,env=env,close_fds=True,**flags)
            until=time.monotonic()+5
            while time.monotonic()<until:
                if child.poll() is not None:break
                if probe(candidate)=={'app':'gooseqa','version':VERSION,'workspace':workspace_id()}:
                    _children.append(child)
                    return candidate,True,child.pid
                time.sleep(.08)
            if child.poll() is None:
                child.terminate()
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:child.kill();child.wait()
        raise ValueError('Could not launch dashboard; see .gooseqa/dashboard.log or run serve manually')


def start(mode=None,port=8766,open_browser=True):
    p,created=ensure_project(mode)
    actual_port,launched,pid=launch_dashboard(port)
    url=f'http://127.0.0.1:{actual_port}/?project={p["id"]}'
    opened=False
    if open_browser:
        try:opened=bool(webbrowser.open(url,new=2))
        except (OSError,webbrowser.Error):pass
    return {'project_id':p['id'],'project':p['name'],'mode':p['mode'],'stage':p['stage'],'next_stage':STAGES[p['stage']] if p['stage']<len(STAGES) else 'Complete','created':created,'dashboard_url':url,'server_started':launched,'server_pid':pid,'browser_open_requested':opened,'tools':{name:bool(shutil.which(name)) for name in ['git','node','npm','python','python3','pytest']},'note':'Browser opening is best effort; use dashboard_url manually if needed. Agent performs QA steps.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('serve');p.add_argument('--port',type=int,default=8766)
    for cmd in ['start','dashboard']:
        p=sub.add_parser(cmd);p.add_argument('--port',type=int,default=8766);p.add_argument('--no-browser',action='store_true')
        if cmd=='start':p.add_argument('mode',nargs='?',choices=MODES)
    sub.add_parser('list');sub.add_parser('demo');p=sub.add_parser('report');p.add_argument('project_id');p=sub.add_parser('apply',help='Apply a validated action from JSON file or stdin (-)');p.add_argument('action');p.add_argument('file');p=sub.add_parser('install-skill');p.add_argument('target',choices=['codex','claude','both']);p.add_argument('--project',default='.');p.add_argument('--global',dest='global_scope',action='store_true')
    a=parser.parse_args()
    try:
        if a.cmd=='serve':
            server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);print(f'GooseQA: http://127.0.0.1:{server.server_port}',flush=True)
            try:server.serve_forever()
            except KeyboardInterrupt:pass
            finally:server.server_close()
        elif a.cmd=='start':print(json.dumps(start(a.mode,a.port,not a.no_browser),ensure_ascii=False,indent=2))
        elif a.cmd=='dashboard':print(json.dumps(start(None,a.port,not a.no_browser),ensure_ascii=False,indent=2))
        elif a.cmd=='list':print(json.dumps(snapshot(),ensure_ascii=False,indent=2))
        elif a.cmd=='demo':print(demo()['id'])
        elif a.cmd=='report':print(report(project(read(),a.project_id)))
        elif a.cmd=='apply':print(json.dumps(apply(a.action,json.load(sys.stdin) if a.file=='-' else json.loads(pathlib.Path(a.file).read_text(encoding='utf-8-sig'))),ensure_ascii=False,indent=2))
        elif a.cmd=='install-skill':
            import shutil
            roots=[(pathlib.Path.home() if a.global_scope else pathlib.Path(a.project).resolve())/('.agents' if target=='codex' else '.claude')/'skills'/'gooseqa' for target in (['codex','claude'] if a.target=='both' else [a.target])]
            for dest in roots:
                if dest.exists():raise ValueError(f'Already exists, refusing overwrite: {dest}')
            for dest in roots:
                shutil.copytree(ROOT/'skills'/'gooseqa',dest);print(dest)
    except (ValueError,OSError,KeyError,TypeError) as e:print(f'Error: {e}',file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
