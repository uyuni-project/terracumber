import unittest
from unittest.mock import patch, mock_open
import re
from terracumber import tf_module_cleaner


class TestTerraformFunctions(unittest.TestCase):

    @patch('terracumber.tf_module_cleaner.re.findall')
    @patch('terracumber.tf_module_cleaner.logger.info')
    def test_get_default_modules(self, mock_logger, mock_findall):
        mock_findall.return_value = ['module.server', 'module.proxy', 'module.terminal']
        tf_resources_to_delete = ['retail', 'proxy']

        result = tf_module_cleaner.get_default_modules('content', tf_resources_to_delete)
        expected = ['module.server']

        self.assertEqual(result, expected)

    def test_contains_resource_name(self):
        tf_resources_to_keep = ['server', 'client']

        self.assertTrue(tf_module_cleaner.contains_resource_name('module.server.configuration', tf_resources_to_keep))
        self.assertFalse(tf_module_cleaner.contains_resource_name('module.proxy.configuration', tf_resources_to_keep))

    def test_filter_module_references(self):
        tf_resources_to_keep = ['rocky8-minion', 'server', 'proxy']
        maintf_content = """
        module "server" {
          product_version    = "4.3-released"
        }
        module "rocky8-minion" {
          product_version    = "4.3-released"
        }
        module "sles15sp5-minion" {
          product_version    = "4.3-released"
        }
        module "proxy" {
          product_version    = "4.3-released"
        }
        module "controller" {
          server_configuration = module.server.configuration
          proxy_configuration  = module.proxy.configuration
          sle15sp5_minion_configuration = module.sles15sp5-minion.configuration
          rocky8_minion_configuration    = module.rocky8-minion.configuration
          # WORKAROUND
        }
        """
        expected = """
        module "server" {
          product_version    = "4.3-released"
        }
        module "rocky8-minion" {
          product_version    = "4.3-released"
        }
        module "sles15sp5-minion" {
          product_version    = "4.3-released"
        }
        module "proxy" {
          product_version    = "4.3-released"
        }
        module "controller" {
          server_configuration = module.server.configuration
          proxy_configuration  = module.proxy.configuration
          rocky8_minion_configuration    = module.rocky8-minion.configuration
        }
        """

        result = tf_module_cleaner.filter_module_references(maintf_content, tf_resources_to_keep)
        self.assertEqual(result.strip(), expected.strip())

    @patch('terracumber.tf_module_cleaner.open', new_callable=mock_open, read_data='module "server" { } module "proxy" { } module "client" { }')
    @patch('terracumber.tf_module_cleaner.get_default_modules')
    @patch('terracumber.tf_module_cleaner.filter_module_references')
    @patch('terracumber.tf_module_cleaner.logger.info')
    def test_remove_unselected_tf_resources(self, mock_logger, mock_filter_module_references, mock_get_default_modules, mock_open):
        mock_get_default_modules.return_value = ['server']
        mock_filter_module_references.return_value = 'module "rocky8-minion" { }'

        tf_resources_to_keep = ['rocky8-minion']
        tf_resources_to_delete = ['proxy']

        tf_module_cleaner.remove_unselected_tf_resources('mockfile', tf_resources_to_keep, tf_resources_to_delete)

        handle = mock_open()
        handle.write.assert_called_once_with('module "server" { } ')

if __name__ == '__main__':
    unittest.main()
