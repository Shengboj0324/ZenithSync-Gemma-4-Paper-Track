from types import SimpleNamespace
import unittest

from zenithsync.container_cleanup import cleanup_owned_container


class CleanupTests(unittest.TestCase):
    def manager(self, *, stop_fails=False, query_fails=False, present=False):
        def stop(cid):
            if stop_fails:
                raise RuntimeError('service unavailable')
        def listing(**kwargs):
            self.assertEqual(kwargs, {'all': True, 'filters': {'id': 'owned'}})
            if query_fails:
                raise ConnectionError('cannot verify')
            return [object()] if present else []
        return SimpleNamespace(stop=stop, client=SimpleNamespace(containers=SimpleNamespace(list=listing)))

    def test_stop_failure_with_remaining_container_is_not_success(self):
        result = cleanup_owned_container(self.manager(stop_fails=True, present=True), 'owned')
        self.assertFalse(result['removed'])
        self.assertEqual(result['errors'][0]['operation'], 'stop')

    def test_unavailable_observation_is_unknown_not_removed(self):
        result = cleanup_owned_container(self.manager(query_fails=True), 'owned')
        self.assertIsNone(result['removed'])

    def test_authoritative_absence_after_stop_error_is_recorded(self):
        result = cleanup_owned_container(self.manager(stop_fails=True), 'owned')
        self.assertTrue(result['removed'])
        self.assertEqual(len(result['errors']), 1)


if __name__ == '__main__':
    unittest.main()
