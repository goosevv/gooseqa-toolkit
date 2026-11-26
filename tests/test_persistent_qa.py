import unittest
from unittest.mock import patch
import qa

class PersistentQATests(unittest.TestCase):
    def setUp(self):
        self.state = qa.empty()
        self.p = qa.mutate(self.state, 'project', {'name':'sample','repo':'sample','mode':'AUTO'})
    def do(self, action, **fields):
        return qa.mutate(self.state, action, dict(project_id=self.p['id'], **fields))
    def add_case(self, priority):
        return self.do('case', title=priority, kind='Unit', priority=priority,
                       steps='run named case', expected='correct output', automation_ref='tests.py')
    def test_checkpoint_and_memory(self):
        self.do('checkpoint', status='working', detail='finished setup')
        self.do('memory', key='stack', text='Python', source='pyproject.toml')
        self.assertEqual(self.p['checkpoint']['detail'], 'finished setup')
        self.assertEqual(self.p['memory']['stack']['source'], 'pyproject.toml')
        self.do('note', stage=0, text='confirmed discovery')
        self.do('advance')
        self.assertEqual(self.p['checkpoint']['stage'], 1)
        self.assertEqual(self.p['checkpoint']['status'], 'pending')
    def test_impact_falls_back_and_includes_p0(self):
        a,b,c = [self.add_case(x) for x in ('P0','P1','P2')]
        self.assertEqual(qa.impact(self.p)['mode'],'FULL')
        self.p['baseline']='abc'
        self.do('impact-map', path='src/b.py', case_ids=[b['id']])
        with patch.object(qa,'changed_paths',return_value=['src/b.py']):
            result=qa.impact(self.p)
            self.assertEqual(result['mode'],'INCREMENTAL')
            self.assertEqual(set(result['case_ids']),{a['id'],b['id']})
        with patch.object(qa,'changed_paths',return_value=['src/b.py','shared.py']):
            self.assertEqual(qa.impact(self.p)['mode'],'FULL')
        with patch.object(qa,'changed_paths',return_value=None):
            self.assertEqual(qa.impact(self.p)['mode'],'FULL')
    def test_review_gate_and_stale_evidence(self):
        risk=self.do('risk',title='loss',priority='P0',reason='critical')
        c=self.do('case',title='P0',kind='Unit',priority='P0',risk_id=risk['id'],
                  steps='run',expected='output',automation_ref='test.py')
        for stage in (0,3,6):
            self.do('note',stage=stage,text='verified')
        self.do('run',case_id=c['id'],result='PASS',evidence='named case passed')
        self.p['stage']=6
        self.assertFalse(qa.gates(self.p)[6])
        fingerprint=qa.review_hash(self.p)
        self.do('review-result',verdict='ACCEPT',method='independent',
                reviewer='test reviewer',findings='assertions checked',fingerprint=fingerprint)
        self.assertTrue(qa.gates(self.p)[6])
        self.do('run',case_id=c['id'],result='FAIL',evidence='named case failed')
        self.assertFalse(qa.gates(self.p)[6])
        with self.assertRaises(ValueError):
            self.do('review-result',verdict='ACCEPT',method='independent',
                    reviewer='test reviewer',findings='old evidence',fingerprint=fingerprint)
    def test_new_cycle_preserves_history_not_pass(self):
        c=self.add_case('P0')
        self.do('run',case_id=c['id'],result='PASS',evidence='old result')
        self.do('memory',key='stack',text='Python',source='manifest')
        self.p['stage']=8
        self.do('new-cycle')
        self.assertEqual(self.p['stage'],0)
        self.assertEqual(self.p['runs'],[])
        self.assertEqual(len(self.p['history'][0]['runs']),1)
        self.assertFalse(qa.gates(self.p)[5])
        self.assertIn('stack',self.p['memory'])

if __name__ == '__main__':
    unittest.main()
