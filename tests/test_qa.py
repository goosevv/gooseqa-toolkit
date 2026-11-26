import tempfile, unittest, pathlib, sys, json, subprocess, threading, urllib.request, urllib.error
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import qa
class QA(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=qa.DATA;qa.DATA=pathlib.Path(self.tmp.name)/'state';self.p=qa.apply('project',{'name':'test','mode':'LEARN'});self.pid=self.p['id']
    def tearDown(self):qa.DATA=self.old;self.tmp.cleanup()
    def add(self,a,**kw):return qa.apply(a,{'project_id':self.pid,**kw})
    def risk(self):return self.add('risk',title='data loss',priority='P0',reason='critical')
    def case(self,r):return self.add('case',title='persist',kind='UI',priority='P0',risk_id=r['id'],steps='reload',expected='same data')
    def test_persistence(self):self.assertEqual(qa.read()['projects'][0]['id'],self.pid)
    def test_gate_blocks(self):
        with self.assertRaises(ValueError):self.add('advance')
        self.add('note',stage=0,text='audited');self.add('advance');self.assertEqual(qa.read()['projects'][0]['stage'],1)
    def test_run_evidence(self):
        c=self.case(self.risk())
        with self.assertRaises(ValueError):self.add('run',case_id=c['id'],result='PASS',evidence='')
        self.add('run',case_id=c['id'],result='PASS',evidence='test passed: named test');self.assertTrue(qa.snapshot()['projects'][0]['gates'][5]);self.add('run',case_id=c['id'],result='FAIL',evidence='assertion');self.assertFalse(qa.snapshot()['projects'][0]['gates'][5])
    def test_risk_coverage(self):
        self.case(self.risk());self.add('risk',title='second risk',priority='P0',reason='critical');self.assertFalse(qa.snapshot()['projects'][0]['gates'][2])
    def test_invalid_link(self):
        with self.assertRaises(ValueError):self.add('case',title='bad',kind='UI',priority='P0',risk_id='unknown',steps='x',expected='y')
    def test_bug_review_gate(self):
        b=self.add('bug',title='defect',severity='P0',details='unexpected');self.add('note',stage=6,text='review');self.assertFalse(qa.snapshot()['projects'][0]['gates'][6]);self.add('bug-status',id=b['id'],status='CLOSED');self.assertTrue(qa.snapshot()['projects'][0]['gates'][6])
    def test_demo(self):self.assertTrue(qa.demo()['demo']);self.assertIn('DEMO',qa.report(qa.read()['projects'][-1]))
    def test_learning(self):
        t=self.add('task',title='first task');self.add('task-status',id=t['id'],done=True);self.assertTrue(qa.read()['projects'][0]['tasks'][0]['done'])
    def test_install(self):
        root=pathlib.Path(__file__).resolve().parents[1];dest=pathlib.Path(self.tmp.name)/'repo';dest.mkdir();cmd=[sys.executable,str(root/'qa.py'),'install-skill','both','--project',str(dest)];subprocess.run(cmd,check=True,capture_output=True)
        for name in ['.agents','.claude']:
            s=dest/name/'skills/gooseqa';self.assertTrue((s/'SKILL.md').exists());self.assertTrue((s/'scripts/static/app.js').exists());subprocess.run([sys.executable,str(s/'scripts/qa.py'),'list'],cwd=dest,check=True,capture_output=True)
        self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
    def test_start_resume_preserves_progress_and_mode(self):
        p,new=qa.ensure_project('PAIR');self.assertTrue(new)
        qa.apply('note',{'project_id':p['id'],'stage':0,'text':'existing evidence'})
        qa.apply('advance',{'project_id':p['id']})
        q,new=qa.ensure_project();self.assertFalse(new);self.assertEqual(q['id'],p['id']);self.assertEqual(q['mode'],'PAIR');self.assertEqual(q['stage'],1)
        q,new=qa.ensure_project('AUTO');self.assertFalse(new);self.assertEqual(q['mode'],'AUTO');self.assertEqual(q['notes']['0'],'existing evidence')
    def test_start_detached_reuse_and_busy_port(self):
        import socket, os, signal
        with socket.socket() as busy:
            busy.bind(('127.0.0.1',0));busy.listen();port=busy.getsockname()[1]
            # Avoid waiting for HTTP response on the intentionally occupied port.
            first=qa.start('PAIR',port,False)
            try:
                self.assertTrue(first['server_started']);self.assertFalse(first['browser_open_requested']);self.assertNotIn(f':{port}/',first['dashboard_url'])
                second=qa.start(None,port,False);self.assertFalse(second['server_started']);self.assertEqual(first['dashboard_url'],second['dashboard_url']);self.assertEqual(first['project_id'],second['project_id']);self.assertEqual(second['mode'],'PAIR')
                with urllib.request.urlopen(first['dashboard_url']) as r:self.assertEqual(r.status,200)
                with urllib.request.urlopen(first['dashboard_url'].split('/?')[0]+'/api/state') as r:self.assertTrue(any(p['id']==first['project_id'] for p in json.load(r)['projects']))
            finally:
                for child in qa._children[:]:
                    if child.pid==first['server_pid']:child.terminate();child.wait(timeout=5);qa._children.remove(child)
    def test_browser_open_and_fallback(self):
        from unittest.mock import patch
        with patch.object(qa,'launch_dashboard',return_value=(8766,False,None)),patch.object(qa.webbrowser,'open',return_value=True) as browser:
            r=qa.start('LEARN');browser.assert_called_once_with(r['dashboard_url'],new=2);self.assertTrue(r['browser_open_requested'])
        with patch.object(qa,'launch_dashboard',return_value=(8766,False,None)),patch.object(qa.webbrowser,'open',return_value=False):
            r=qa.start();self.assertFalse(r['browser_open_requested']);self.assertTrue(r['dashboard_url'].startswith('http://127.0.0.1:'))
    def test_http(self):
        server=qa.ThreadingHTTPServer(('127.0.0.1',0),qa.Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start();base=f'http://127.0.0.1:{server.server_port}'
        try:
            for path in ['/','/app.js','/style.css','/api/state','/api/report/'+self.pid]:
                with urllib.request.urlopen(base+path) as r:self.assertEqual(r.status,200);self.assertTrue(r.read())
            with urllib.request.urlopen(base+'/gooseqa-logo.png') as r:
                self.assertEqual(r.status,200)
                self.assertEqual(r.headers.get_content_type(),'image/png')
                self.assertTrue(r.read().startswith(b'\x89PNG\r\n\x1a\n'))
            body=json.dumps({'project_id':self.pid,'mode':'PAIR'}).encode();req=urllib.request.Request(base+'/api/action/mode',data=body,headers={'Content-Type':'application/json','Origin':base});self.assertEqual(urllib.request.urlopen(req).status,200)
            req=urllib.request.Request(base+'/api/action/mode',data=body,headers={'Content-Type':'application/json','Origin':'https://evil.example'});self.assertRaises(urllib.error.HTTPError,urllib.request.urlopen,req)
        finally:server.shutdown();server.server_close();t.join()
