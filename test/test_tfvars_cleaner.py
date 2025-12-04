import unittest
from unittest.mock import patch, mock_open, MagicMock
from terracumber import tfvars_cleaner

class TestTfvarsCleaner(unittest.TestCase):

    def test_to_hcl_simple_types(self):
        """Test basic HCL conversion for strings, bools, and nulls."""
        self.assertEqual(tfvars_cleaner.to_hcl("value"), '"value"')
        self.assertEqual(tfvars_cleaner.to_hcl(True), 'true')
        self.assertEqual(tfvars_cleaner.to_hcl(False), 'false')
        self.assertEqual(tfvars_cleaner.to_hcl(None), 'null')
        self.assertEqual(tfvars_cleaner.to_hcl(123), '123')

    def test_to_hcl_lists(self):
        """Test HCL conversion for lists."""
        data = ["a", "b", 1]
        expected = '["a", "b", "1"]' # integers in lists are converted to strings in the current implementation for safety/consistency if mixed
        # Actually, looking at your implementation: items = [to_hcl(item, 0) for item in obj]
        # to_hcl(1) -> '1'. So result is ["a", "b", 1] effectively (unquoted if raw int).

        # Let's test based on exact string output of your function
        self.assertEqual(tfvars_cleaner.to_hcl(["a", "b"]), '["a", "b"]')

    def test_to_hcl_dictionaries(self):
        """Test HCL conversion for dictionaries (nested blocks)."""
        data = {
            "key1": "value1",
            "key2": {
                "nested": "value2"
            }
        }
        # Note: formatting depends on the indentation logic in to_hcl
        expected = 'key1 = "value1"\nkey2 = {\n  nested = "value2"\n}'
        self.assertEqual(tfvars_cleaner.to_hcl(data).strip(), expected.strip())

    def test_get_default_keep_list_delete_all_false(self):
        """Test default retention when delete_all is False (keep infrastructure)."""
        env_config = {
            "controller": {},
            "server": {},
            "proxy": {},
            "sles15_minion": {},
            "ubuntu_client": {}
        }

        # Should exclude 'minion' and 'client' keywords
        expected = {'controller', 'server', 'proxy'}
        result = tfvars_cleaner.get_default_keep_list(env_config, delete_all=False)
        self.assertEqual(result, expected)

    def test_get_default_keep_list_delete_all_true(self):
        """Test default retention when delete_all is True (keep only core)."""
        env_config = {
            "controller": {},
            "server": {},
            "proxy": {}, # Should be removed
            "monitoring_server": {}, # Should be removed
            "sles15_minion": {}, # Should be removed
            "sles15_buildhost": {} # Should be removed
        }

        # Should exclude proxies, monitoring, buildhosts, terminals, minions, clients
        expected = {'controller', 'server'}
        result = tfvars_cleaner.get_default_keep_list(env_config, delete_all=True)
        self.assertEqual(result, expected)

    @patch('terracumber.tfvars_cleaner.hcl2.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('terracumber.tfvars_cleaner.logger')
    def test_clean_tfvars(self, mock_logger, mock_file, mock_hcl_load):
        """Test the full clean_tfvars process."""

        # Mock input data found in the tfvars file
        input_data = {
            'ENVIRONMENT_CONFIGURATION': {
                'controller': {'mac': 'aa:bb:cc'},
                'sles15_minion': {'mac': '11:22:33'},
                'rocky_minion': {'mac': '44:55:66'}
            },
            'BASE_CONFIGURATIONS': {
                'base_core': {}
            }
        }
        mock_hcl_load.return_value = input_data

        # We want to explicitly keep 'rocky_minion', but 'sles15_minion' should go.
        # 'controller' should be kept by default.
        explicit_keep = ['rocky_minion']

        # Run the cleaner
        tfvars_cleaner.clean_tfvars('dummy.tfvars', explicit_keep, delete_all=False)

        # Check what was written to the file
        # We expect a write call containing the processed HCL string
        handle = mock_file()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        # Assertions
        self.assertIn('controller = {', written_content)
        self.assertIn('rocky_minion = {', written_content)
        self.assertNotIn('sles15_minion = {', written_content)

        # BASE_CONFIGURATIONS should be preserved intact
        self.assertIn('BASE_CONFIGURATIONS', written_content)

if __name__ == '__main__':
    unittest.main()
