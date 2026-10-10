import unittest
from zenithsync.qualification_sampling import stratified_repository_batch


class QualificationSamplingTests(unittest.TestCase):
    def records(self):
        return [{'repo':'owner/repo'+str(i),'instance_id':'task'+str(i),
                 'trajectory_id':'trace'+str(i),'serialized_source_tokens':i+1}
                for i in range(40)]

    def test_order_independence_unique_repositories_and_strata(self):
        rows=self.records()
        a=stratified_repository_batch(rows,excluded_repositories=[],seed=19,per_stratum=3)
        self.assertEqual(a,stratified_repository_batch(rows[::-1],excluded_repositories=[],seed=19,per_stratum=3))
        self.assertEqual(len({r['repo'] for r in a}),12)
        for s in range(4):
            self.assertEqual(sum(r['stratum']==s for r in a),3)
            self.assertTrue(all(r['stratum_population']==10 for r in a if r['stratum']==s))

    def test_exclusion_and_shortest_trace_precede_sampling(self):
        rows=self.records()
        rows.append({**rows[0],'trajectory_id':'longer','serialized_source_tokens':999})
        chosen=stratified_repository_batch(rows,excluded_repositories=['OWNER/REPO39'],seed=19,per_stratum=1)
        self.assertNotIn('owner/repo39',{r['repo'] for r in chosen})
        self.assertNotIn('longer',{r['trajectory_id'] for r in chosen})
        self.assertEqual({r['stratum_population'] for r in chosen},{9,10})

    def test_invalid_counts_duplicates_and_undersupply_fail(self):
        rows=self.records()
        with self.assertRaises(ValueError):
            stratified_repository_batch(rows+[rows[0]],excluded_repositories=[],seed=1)
        with self.assertRaises(ValueError):
            stratified_repository_batch(rows[:3],excluded_repositories=[],seed=1)
        rows[0]['serialized_source_tokens']=True
        with self.assertRaises(ValueError):
            stratified_repository_batch(rows,excluded_repositories=[],seed=1)
