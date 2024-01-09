from terracumber import junit
import unittest


class TestJunit(unittest.TestCase):
    def setUp(self):
        self.junit = junit.Junit('test/resources/junit/failures')

    def test_sort_test_files_by_mtime(self):
        file_list = [
            'test/resources/junit/failures/TEST-features-secondary-srv_delete_channel_from_ui.xml',
            'test/resources/junit/failures/TEST-features-secondary-srv_delete_channel_with_tool.xml',
            'test/resources/junit/failures/TEST-features-secondary-srv_power_management.xml',
            'test/resources/junit/failures/TEST-features-secondary-srv_test_maintenance_windows.xml',
            'test/resources/junit/failures/TEST-features-secondary-srv_users.xml',
            'test/resources/junit/failures/TEST-features-secondary-srv_virtual_host_manager.xml',
            'test/resources/junit/failures/TEST-features-secondary-trad_centos_client.xml']
        self.maxDiff = None
        self.assertListEqual(self.junit.sort_test_files_by_mtime(), file_list)

    def test_get_totals(self):
        totals = {'failures': 3, 'errors': 0, 'skipped': 0, 'passed': 63, 'tests': 66, 'time': 1334.586592}
        self.assertDictEqual(self.junit.get_totals(), totals)

    def test_get_failures(self):
        failure_messages = [
            "failed Schedule some actions on the CentOS 7 traditional client",
            "failed Cleanup: bootstrap a CentOS minion after traditional client tests",
            "failed Cleanup: re-subscribe the new CentOS minion to a base channel"]
        self.assertListEqual(self.junit.get_failures(), failure_messages)
        self.assertListEqual(self.junit.get_failures(number=1), failure_messages[0:1])
        self.assertListEqual(self.junit.get_failures(number=0), [])


class TestJunitSaltShaker(unittest.TestCase):
    def setUp(self):
        self.junit = junit.Junit('test/resources/junit/salt-shaker/failures')

    def test_get_failures_saltshaker(self):
        failure_messages = [
            "test.test_junit.TestJunit::test_sort_test_files_by_mtime",
            "test.test_junit.TestJunitSaltShaker::test_get_failures",
        ]
        self.assertListEqual(self.junit.get_failures_saltshaker(), failure_messages)
        self.assertListEqual(self.junit.get_failures_saltshaker(number=1), failure_messages[0:1])
        self.assertListEqual(self.junit.get_failures_saltshaker(number=0), [])


if __name__ == '__main__':
    unittest.main()
