"""Review coverage is structural evidence, never semantic certification."""
from copy import deepcopy
import unittest
from zenithsync.training_corpus import validate_task_alignment


class TaskAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.records = [{'task_id': 'issue-1', 'repository_group': 'owner/repo'},
                        {'task_id': 'issue-2', 'repository_group': 'owner/other'}]
        self.reviews = [{**r, 'decision': 'accepted', 'rationale': 'Synthetic fixture.'}
                        for r in self.records]

    def documents(self, reviews):
        return [{'schema_version': 1, 'task_reviews': reviews}]

    def test_exact_coverage_allows_multiple_traces_and_sharded_reviews(self):
        documents = self.documents(self.reviews[:1]) + self.documents(self.reviews[1:])
        validate_task_alignment(documents, self.records + [self.records[0]])

    def test_missing_duplicate_and_foreign_reviews_fail(self):
        variants = [(self.reviews[:1], 'incomplete'),
                    (self.reviews + [self.reviews[0]], 'Duplicate')]
        for field in ('task_id', 'repository_group'):
            altered = deepcopy(self.reviews);altered[0][field] = 'foreign'
            variants.append((altered, 'foreign'))
        for reviews, error in variants:
            with self.subTest(error=error, reviews=reviews):
                with self.assertRaisesRegex(ValueError, error):
                    validate_task_alignment(self.documents(reviews), self.records)

    def test_unresolved_rejected_empty_and_malformed_reviews_fail(self):
        for decision in ('rejected', 'unresolved', True):
            altered = deepcopy(self.reviews);altered[0]['decision'] = decision
            with self.assertRaises(ValueError):
                validate_task_alignment(self.documents(altered), self.records)
        for document in ({}, {'schema_version': True, 'task_reviews': self.reviews},
                         {'schema_version': 1, 'task_reviews': []}):
            with self.assertRaises(ValueError):
                validate_task_alignment([document], self.records)
        altered = deepcopy(self.reviews);altered[0]['rationale'] = ' '
        with self.assertRaises(ValueError):
            validate_task_alignment(self.documents(altered), self.records)

    def test_hash_valid_receipt_with_wrong_repository_denies_training(self):
        from zenithsync.training_corpus import GATES, corpus_content_identity
        from tests.test_training_corpus import CorpusTests
        fixture = CorpusTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.manifest['status'] = 'admitted'
        evidence = fixture.alignment_evidence()
        evidence['task_reviews'][0]['repository_group'] = 'wrong/repository'
        fixture.write('evidence.json', evidence)
        for gate in GATES:
            fixture.write(gate+'.json', {'gate': gate, 'status': 'passed',
                'corpus_content_sha256': corpus_content_identity(fixture.manifest),
                'evidence': [fixture.ref('evidence.json')]})
            fixture.manifest['admission'][gate] = fixture.ref(gate+'.json')
        with self.assertRaisesRegex(ValueError, 'foreign'):
            fixture.load(purpose='training')
