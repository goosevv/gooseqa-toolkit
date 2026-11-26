import json, os, pathlib, sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import model_router as r

class RouterTest(unittest.TestCase):
    def host(self):
        return dict(provider='generic',delegation=True,model_selection=True,max_agents=1,
                    current_model='root',current_classes=['BALANCED'],current_effort='medium',
                    models=[dict(id='fast',classes=['FAST'],efforts=['low']),
                            dict(id='reason',classes=['BALANCED','REASONING'],efforts=['medium'])])
    def test_default(self):
        p=r.plan({},self.host())
        self.assertEqual(p['max_concurrent_subagents'],1)
        self.assertEqual(p['roles']['explorer']['model'],'fast')
        self.assertEqual(p['roles']['test_runner']['execution'],'cli')
        self.assertEqual(p['roles']['visual_analyst']['execution'],'blocked')
        self.assertEqual(p['status'],'planned_not_executed')
    def test_unknown_host(self):
        p=r.plan({}, {})
        self.assertEqual(p['max_concurrent_subagents'],0)
        self.assertEqual(p['roles']['orchestrator']['execution'],'current')
        self.assertIsNone(p['roles']['orchestrator']['model'])
    def test_eco(self):
        p=r.plan(dict(profile='ECO'),self.host())
        self.assertFalse(any(x['execution']=='delegate' for x in p['roles'].values()))
    def test_strict_manual(self):
        p=r.plan(dict(routing='manual',allow_fallback=False,models={'explorer':'missing'}),self.host())
        self.assertEqual(p['roles']['explorer']['execution'],'blocked')
    def test_original_non_codex(self):
        self.assertEqual(r.plan(dict(routing='original'),self.host())['roles']['orchestrator']['execution'],'blocked')
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GOOSEQA_CONFIG':str(pathlib.Path(d)/'settings.json')}):
            self.assertEqual(r.load()['profile'],'BALANCED')
            r.save(dict(profile='ECO'))
            self.assertEqual(r.load()['profile'],'ECO')
            with self.assertRaises(ValueError):r.save(dict(max_agents=99))
            self.assertEqual(r.load()['profile'],'ECO')
    def test_invalid_inventory(self):
        with self.assertRaises(ValueError):r.plan({},dict(models=[dict(id='x',classes=['UNKNOWN'])]))
