import unittest
from scripts.audit_repository_lineage import project_repository


class RepositoryLineageTests(unittest.TestCase):
    def test_nonfork_root_is_own_numeric_identity(self):
        r=project_repository({'id':1,'full_name':'Owner/Repo','fork':False})
        self.assertEqual(r['network_root'],{'id':1,'full_name':'Owner/Repo'})

    def test_fork_uses_declared_network_root_not_immediate_parent(self):
        r=project_repository({'id':3,'full_name':'c/repo','fork':True,
            'parent':{'id':2,'full_name':'b/repo'},'source':{'id':1,'full_name':'a/repo'}})
        self.assertEqual(r['network_root']['id'],1)
        self.assertEqual(r['parent']['id'],2)

    def test_incomplete_or_malformed_metadata_rejects(self):
        cases=[{'id':True,'full_name':'a/b','fork':False},
               {'id':1,'full_name':'../b','fork':False},
               {'id':1,'full_name':'a/b','fork':True}]
        for obj in cases:
            with self.subTest(obj=obj):
                with self.assertRaises((ValueError,KeyError)):project_repository(obj)


if __name__=='__main__':unittest.main()
