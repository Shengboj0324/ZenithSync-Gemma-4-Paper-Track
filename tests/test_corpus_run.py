import unittest
from zenithsync.artifacts import file_record
from zenithsync.corpus_run import preflight_corpus_run


class CorpusRunTests(unittest.TestCase):
    def setUp(self):
        from tests.test_training_corpus import CorpusTests
        from zenithsync.training_corpus import GATES, corpus_content_identity
        from zenithsync.training_schedule import make_schedule
        self.fixture = CorpusTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.manifest['status'] = 'admitted'
        f.write('fixture-evidence.json', f.alignment_evidence())
        for gate in GATES:
            f.write(gate+'.json', {'gate':gate,'status':'passed',
                'corpus_content_sha256':corpus_content_identity(f.manifest),
                'evidence':[f.ref('fixture-evidence.json')]})
            f.manifest['admission'][gate] = f.ref(gate+'.json')
        f.load(purpose='training')
        self.config = {'schema_version':1,'seed':19,'learning_rate':0.0001,
            'max_updates':1,'max_seconds':300,'max_sequence_tokens':8,
            'max_checkpoint_bytes':100000,'max_session_checkpoint_bytes':200000,
            'max_corpus_bytes':100000,'max_example_bytes':10000}
        self.schedule = make_schedule([{'example_id':'trace1','input_tokens':3,'supervised_tokens':1}],
            corpus_content_sha256=corpus_content_identity(f.manifest),seed=19,
            target_supervised_tokens=2,max_epochs=2,max_update_supervised_tokens=1)

    def run_preflight(self):
        f = self.fixture;f.write('config.json',self.config);f.write('schedule.json',self.schedule)
        return preflight_corpus_run(corpus_root=f.root,
            corpus_sha256=file_record(f.root/'corpus.json')['sha256'],
            schedule_path=f.root/'schedule.json',schedule_sha256=file_record(f.root/'schedule.json')['sha256'],
            config_path=f.root/'config.json',config_sha256=file_record(f.root/'config.json')['sha256'])

    def test_valid_exact_plan(self):
        corpus, schedule, config = self.run_preflight()
        self.assertTrue(corpus.summary['training_admitted'])
        self.assertEqual(schedule,self.schedule);self.assertEqual(config,self.config)

    def test_quarantine_denied(self):
        f = self.fixture;f.manifest['status'] = 'quarantine';f.write('corpus.json',f.manifest)
        with self.assertRaisesRegex(ValueError,'Quarantine'):self.run_preflight()

    def test_bad_config_and_capacity(self):
        for key,value in [('seed',2**32),('max_updates',True),('learning_rate',0),('max_sequence_tokens',2)]:
            with self.subTest(key=key):
                old = self.config[key];self.config[key] = value
                with self.assertRaises(ValueError):self.run_preflight()
                self.config[key] = old

    def test_schedule_content_change_rejected(self):
        self.schedule['examples'][0]['supervised_tokens'] = 2
        with self.assertRaises(ValueError):self.run_preflight()


if __name__ == '__main__':unittest.main()
