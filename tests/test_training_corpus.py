import hashlib
from pathlib import Path
import tempfile
import unittest
from zenithsync.artifacts import canonical_json,file_record
from zenithsync.training_corpus import GATES,load_corpus,corpus_content_identity,IndexedCorpus


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        ident={'sha256':'a'*64,'size_bytes':1}
        self.assets={k:ident for k in ['chat_template.jinja','tokenizer.json','tokenizer_config.json']}
        candidate={'schema_version':1,'input_ids':[1,2,3],'labels':[-100,-100,3],
                   'vocab_size':8,'pad_token_id':0,'history':ident,'tools':ident,'training_approved':False}
        self.write('tokens.json',candidate)
        self.audit={'token_candidate':file_record(self.root/'tokens.json'),'assets':self.assets,
                    'truncated':False,'history':ident,'tools':ident,'input_tokens':3,'supervised_tokens':1,
                    'input_sha256':self.hash(candidate['input_ids']),'labels_sha256':self.hash(candidate['labels'])}
        self.write('audit.json',self.audit)
        self.record={'example_id':'trace1','task_id':'repo-1','repository_group':'owner/repo',
                     'leakage_group':'repo-1','split':'train','tokens':self.ref('tokens.json'),'audit':self.ref('audit.json')}
        self.manifest={'schema_version':2,'status':'quarantine','tokenizer_assets':self.assets,'max_length':10,
                       'examples':[self.record],'admission':{g:None for g in GATES}}

    def alignment_evidence(self):
        return {'schema_version': 1, 'synthetic_test_only': True,
                'task_reviews': [
                    {'task_id': task, 'repository_group': repo,
                     'decision': 'accepted', 'rationale': 'Synthetic structural test only.'}
                    for task, repo in sorted({(r['task_id'], r['repository_group'])
                                              for r in self.manifest['examples']})]}

    def hash(self,value):return hashlib.sha256(canonical_json(value)).hexdigest()
    def write(self,name,value):(self.root/name).write_bytes(canonical_json(value))
    def ref(self,name):return {'path':name,'identity':file_record(self.root/name)}
    def load(self,**kwargs):
        self.write('corpus.json',self.manifest)
        return load_corpus(self.root,self.root/'corpus.json',expected_manifest_sha256=self.hash(self.manifest),**kwargs)

    def test_valid_quarantine_and_training_rejection(self):
        r=self.load();self.assertEqual(r['summary']['supervised_tokens'],1)
        self.assertFalse(r['summary']['training_admitted'])
        with self.assertRaisesRegex(ValueError,'Quarantine'):self.load(purpose='training')
        self.manifest['status']='admitted'
        with self.assertRaisesRegex(ValueError,'unresolved gate'):self.load(purpose='training')

    def test_legacy_corpus_remains_inspectable_but_cannot_train(self):
        self.manifest['schema_version']=1
        del self.manifest['admission']['task_alignment']
        self.assertFalse(self.load()['summary']['training_admitted'])
        self.manifest['status']='admitted'
        self.write('legacy-evidence.json',{'synthetic_test_only':True})
        for gate in self.manifest['admission']:
            self.write(gate+'.json',{'gate':gate,'status':'passed',
                'corpus_content_sha256':corpus_content_identity(self.manifest),
                'evidence':[self.ref('legacy-evidence.json')]})
            self.manifest['admission'][gate]=self.ref(gate+'.json')
        self.assertFalse(self.load()['summary']['training_admitted'])
        with self.assertRaisesRegex(ValueError,'Legacy corpus'):
            self.load(purpose='training')

    def test_v2_cannot_omit_alignment_gate(self):
        del self.manifest['admission']['task_alignment']
        with self.assertRaisesRegex(ValueError,'gate map'):
            self.load()

    def test_alignment_cannot_be_an_unbound_pass_claim(self):
        self.manifest['status']='admitted'
        self.write('evidence.json',{'synthetic_test_only':True})
        for gate in GATES:
            self.write(gate+'.json',{'gate':gate,'status':'passed',
                'corpus_content_sha256':corpus_content_identity(self.manifest),
                'evidence':[self.ref('evidence.json')]})
            self.manifest['admission'][gate]=self.ref(gate+'.json')
        receipt={'gate':'task_alignment','status':'passed',
                 'corpus_content_sha256':'f'*64,'evidence':[self.ref('evidence.json')]}
        self.write('task_alignment.json',receipt)
        self.manifest['admission']['task_alignment']=self.ref('task_alignment.json')
        with self.assertRaisesRegex(ValueError,'does not bind'):
            self.load(purpose='training')

    def indexed(self, **kwargs):
        return IndexedCorpus(self.root, self.root/'corpus.json',
                             expected_manifest_sha256=self.hash(self.manifest), **kwargs)

    def test_indexed_fetch_matches_materialized_and_does_not_cache_arrays(self):
        loaded=self.load()
        reader=self.indexed(purpose='inspection')
        self.assertEqual(reader.fetch('trace1'),loaded['examples'][0])
        self.assertEqual(reader.metadata(),[{'example_id':'trace1','task_id':'repo-1',
                         'split':'train','input_tokens':3,'supervised_tokens':1}])
        self.assertNotIn('input_ids',reader._records['trace1'])
        fetched=reader.fetch('trace1');fetched['input_ids'][0]=7
        metadata=reader.metadata();metadata[0]['example_id']='changed'
        summary=reader.summary;summary['manifest']['sha256']='b'*64
        self.assertEqual(reader.fetch('trace1'),loaded['examples'][0])

    def test_indexed_rejects_post_validation_token_and_manifest_mutations(self):
        self.load();reader=self.indexed(purpose='inspection')
        original=(self.root/'tokens.json').read_bytes()
        self.write('tokens.json',{})
        with self.assertRaisesRegex(ValueError,'hash mismatch'):reader.fetch('trace1')
        (self.root/'tokens.json').write_bytes(original)
        self.write('corpus.json',{})
        with self.assertRaisesRegex(ValueError,'Manifest changed'):reader.fetch('trace1')

    def test_indexed_requires_admission_and_per_example_byte_bound(self):
        self.load()
        with self.assertRaisesRegex(ValueError,'Quarantine'):self.indexed()
        with self.assertRaisesRegex(ValueError,'byte ceiling'):
            self.indexed(purpose='inspection',max_example_bytes=1)

    def test_indexed_validates_audit_before_exposing_any_example(self):
        self.audit['supervised_tokens']=2;self.write('audit.json',self.audit)
        self.record['audit']=self.ref('audit.json')
        self.write('corpus.json',self.manifest)
        with self.assertRaisesRegex(ValueError,'accounting'):
            self.indexed(purpose='inspection')

    def test_tampered_tokens_and_audit_accounting(self):
        (self.root/'tokens.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.load()
        self.record['tokens']=self.ref('tokens.json')
        with self.assertRaises(ValueError):self.load()

    def test_hash_and_byte_ceiling_and_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError,'byte ceiling'):self.load(max_total_bytes=1)
        self.manifest['examples'].append(dict(self.record))
        with self.assertRaisesRegex(ValueError,'Duplicate example'):self.load()

    def test_rejects_cross_repository_alias_paths(self):
        self.record['tokens']['path']='../tokens.json'
        with self.assertRaises(ValueError):self.load()

    def test_labels_must_match_audit(self):
        self.audit['supervised_tokens']=2;self.write('audit.json',self.audit)
        self.record['audit']=self.ref('audit.json')
        with self.assertRaisesRegex(ValueError,'accounting'):self.load()

    def test_admission_receipts_bind_exact_content(self):
        # Synthetic local receipts test structural enforcement, not real approval.
        self.manifest['status']='admitted'
        self.write('fixture-evidence.json',self.alignment_evidence())
        for gate in GATES:
            name=gate+'.json'
            self.write(name,{'gate':gate,'status':'passed',
                'corpus_content_sha256':corpus_content_identity(self.manifest),
                'evidence':[self.ref('fixture-evidence.json')]})
            self.manifest['admission'][gate]=self.ref(name)
        self.assertTrue(self.load(purpose='training')['summary']['training_admitted'])
        self.manifest['max_length']=11
        with self.assertRaisesRegex(ValueError,'does not bind'):self.load(purpose='training')

    def test_symlinked_candidate_rejected(self):
        (self.root/'link.json').symlink_to(self.root/'tokens.json')
        self.record['tokens']['path']='link.json'
        with self.assertRaisesRegex(ValueError,'Symlinked'):self.load()

    def test_canonical_repository_groups_cannot_cross_splits(self):
        from copy import deepcopy
        candidate={'schema_version':1,'input_ids':[1,2,4],'labels':[-100,-100,4],
                   'vocab_size':8,'pad_token_id':0,'history':self.audit['history'],'tools':self.audit['tools'],'training_approved':False}
        self.write('tokens2.json',candidate)
        audit=deepcopy(self.audit);audit.update(token_candidate=file_record(self.root/'tokens2.json'),
            input_sha256=self.hash(candidate['input_ids']),labels_sha256=self.hash(candidate['labels']))
        self.write('audit2.json',audit)
        self.manifest['examples'].append({**self.record,'example_id':'trace2','task_id':'repo-2',
            'repository_group':'OWNER/REPO','leakage_group':'repo-2','split':'development',
            'tokens':self.ref('tokens2.json'),'audit':self.ref('audit2.json')})
        with self.assertRaisesRegex(ValueError,'cross-split leakage'):self.load()


if __name__=='__main__':unittest.main()
