"""Synthetic JSON payloads test accounting independently of Torch deserialization."""
import copy
from pathlib import Path
import tempfile
import unittest
from zenithsync.artifacts import canonical_json, file_record, load_json
from zenithsync.training_schedule import make_schedule, iter_updates, initial_cursor
from zenithsync.session_report import validate_session_report


class SessionReportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.schedule = make_schedule([{'example_id':'fixture','input_tokens':3,'supervised_tokens':1}],
            corpus_content_sha256='a'*64,seed=1,target_supervised_tokens=3,max_epochs=3,
            max_update_supervised_tokens=1)
        self.start = initial_cursor(self.schedule)
        self.bindings = {'synthetic_fixture':True}
        self.records = []
        for update in iter_updates(self.schedule):
            path = self.root/f"update-{update['step']:08d}.pt"
            payload = {'bindings':self.bindings,'cursor':update['next_cursor'],
                       'optimizer':{'completed_steps':update['step']}}
            path.write_bytes(canonical_json(payload))
            self.records.append({'path':str(path),'identity':file_record(path),
                'cursor':update['next_cursor'],'metrics':{'supervised_tokens':1,
                'microbatch_supervised_tokens':[1],'token_mean_loss':1.2,'microbatches':1}})
        self.report = {'status':'schedule_complete','cursor':self.records[-1]['cursor'],
            'checkpoints':self.records,'checkpoint_bytes':sum(r['identity']['size_bytes'] for r in self.records),
            'elapsed_seconds':1.0}

    def validate(self, report=None, **kwargs):
        options = dict(schedule=self.schedule,start_cursor=self.start,bindings=self.bindings,
            checkpoint_root=self.root,max_updates=4,max_seconds=60,max_checkpoint_bytes=10000,
            max_session_checkpoint_bytes=100000,load_payload=lambda path,identity:load_json(path))
        options.update(kwargs)
        return validate_session_report(self.report if report is None else report,**options)

    def test_complete_and_resumed_reports(self):
        self.assertEqual(self.validate()['verified_updates'],3)
        report = copy.deepcopy(self.report)
        report['checkpoints'] = report['checkpoints'][1:]
        report['checkpoint_bytes'] = sum(r['identity']['size_bytes'] for r in report['checkpoints'])
        self.assertEqual(self.validate(report,start_cursor=self.records[0]['cursor'])['verified_updates'],2)

    def test_false_stop_reasons_and_accounting_rejected(self):
        changes = [lambda r:r.update(status='wall_budget'),
                   lambda r:r.update(checkpoint_bytes=r['checkpoint_bytes']+1),
                   lambda r:r['checkpoints'][0]['metrics'].update(supervised_tokens=True),
                   lambda r:r['checkpoints'][0]['metrics'].update(token_mean_loss=float('nan')),
                   lambda r:r['checkpoints'][0]['cursor'].update(completed_updates=True),
                   lambda r:r['checkpoints'].reverse()]
        for change in changes:
            report = copy.deepcopy(self.report);change(report)
            with self.assertRaises(ValueError):self.validate(report)

    def test_payload_cursor_and_bindings_must_agree(self):
        for key in ('bindings','cursor'):
            def altered(path,identity):
                payload = load_json(path);payload[key] = {};return payload
            with self.assertRaisesRegex(ValueError,'payload differs'):
                self.validate(load_payload=altered)

    def test_path_escape_and_file_change_rejected(self):
        report = copy.deepcopy(self.report);report['checkpoints'][0]['path'] = str(self.root/'wrong.pt')
        with self.assertRaisesRegex(ValueError,'path differs'):self.validate(report)
        Path(self.records[0]['path']).write_text('changed')
        with self.assertRaisesRegex(ValueError,'identity or size'):self.validate()

    def test_update_budget_requires_exact_count(self):
        report = copy.deepcopy(self.report)
        report['checkpoints'] = report['checkpoints'][:1]
        report.update(status='update_budget',cursor=report['checkpoints'][0]['cursor'],
                      checkpoint_bytes=report['checkpoints'][0]['identity']['size_bytes'])
        self.assertEqual(self.validate(report,max_updates=1)['verified_updates'],1)
        with self.assertRaisesRegex(ValueError,'stop reason'):self.validate(report,max_updates=2)


if __name__ == '__main__':unittest.main()
