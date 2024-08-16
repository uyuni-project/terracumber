from terracumber import terraformer
import unittest
from subprocess import CalledProcessError
from unittest.mock import patch


@patch('terracumber.terraformer.copy')
@patch('terracumber.terraformer.path')
@patch('terracumber.terraformer.symlink')
@patch('terracumber.terraformer.unlink')
class TestTerraformer(unittest.TestCase):
    def setUp(self):
        self.terraform_path = 'test/resources'
        self.maintf = 'test/resources/test.tf'
        self.backend = 'libvirt'
        self.variables = {'CUCUMBER_BRANCH': 'test'}
        self.output_file = 'test/resources/output.log'

    def test_manage_backend_symlink(self, mock_unlink, mock_symlink, mock_path, mock_copy):
        mock_path.exists.return_value = True
        mock_path.abspath.return_value = '/tmp'
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend)
        self.terraformer.prepare_environment()
        mock_unlink.assert_called_once_with('test/resources/modules/backend')
        mock_symlink.assert_called_once_with('/tmp/backend_modules/libvirt', 'test/resources/modules/backend')

    def test_get_hostname(self, mock_unlink, mock_symlink, mock_path, mock_copy):
        # Test an invalid machine
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend)
        self.assertEqual(self.terraformer.get_hostname('controller'), 'uyuni-master-ctl.mgr.suse.de')
        self.assertIsNone(self.terraformer.get_hostname('invalid'))
        # Test a valid machine
        self.terraformer = terraformer.Terraformer('/tmp', self.maintf, self.backend)
        with self.assertRaises(FileNotFoundError):
            self.assertIsNone(self.terraformer.get_hostname('controller'))

    def test_get_resources(self, mock_unlink, mock_symlink, mock_path, mock_copy):
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend)
        with patch.object(self.terraformer, '_Terraformer__run_command') as mock_run_command:
            mock_run_command.return_value = ['module.base.module.base_backend.libvirt_network.additional_network[0]',
                                             'module.base.module.base_backend.libvirt_volume.volumes["opensuse152o"]',
                                             'module.proxy.module.proxy.module.host.data.template_file.network_config',
                                             'module.proxy.module.proxy.module.host.data.template_file.user_data',
                                             'module.proxy.module.proxy.module.host.libvirt_cloudinit_disk.cloudinit_disk[0]',
                                             'module.proxy.module.proxy.module.host.libvirt_domain.domain[0]',
                                             'module.proxy.module.proxy.module.host.libvirt_volume.main_disk[0]',
                                             'module.proxy.module.proxy.module.host.null_resource.provisioning[0]',
                                             'module.server.module.server.module.host.data.template_file.network_config',
                                             'module.server.module.server.module.host.data.template_file.user_data',
                                             'module.server.module.server.module.host.libvirt_cloudinit_disk.cloudinit_disk[0]',
                                             'module.server.module.server.module.host.libvirt_domain.domain[0]',
                                             'module.server.module.server.module.host.libvirt_volume.main_disk[0]',
                                             'module.server.module.server.module.host.null_resource.provisioning[0]']
            expected_result = ['module.proxy.module.proxy.module.host.libvirt_domain.domain[0]',
                               'module.proxy.module.proxy.module.host.libvirt_volume.main_disk[0]',
                               'module.server.module.server.module.host.libvirt_domain.domain[0]',
                               'module.server.module.server.module.host.libvirt_volume.main_disk[0]']
            self.assertEqual(self.terraformer._Terraformer__get_resources('.*(domain|main_disk).*'), expected_result)
            self.assertFalse(self.terraformer._Terraformer__get_resources('.*invalid.*'))

    @patch('builtins.open')
    @patch('terracumber.terraformer.Popen')
    def test_run_command(self, mock_popen, mock_open, mock_unlink, mock_symlink, mock_path, mock_copy):
        mock_popen.return_value.wait.return_value = 0
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend, None,
                                                   self.output_file)
        with patch.object(self.terraformer, '_Terraformer__run_command_iterator') as mock_cmd_iterator:
            # Test log output
            mock_cmd_iterator.return_value = iter(["TEST"])
            self.assertEqual(self.terraformer._Terraformer__run_command('echo TEST', False), 0)
            mock_open.assert_called_once_with('test/resources/output.log', 'a')
            mock_open.return_value.write.assert_called_once_with('TEST')
            mock_open.return_value.close.assert_called_once()
            # Test return values
            mock_cmd_iterator.return_value = iter(["TEST"])
            mock_open.reset_mock()
            self.assertEqual(self.terraformer._Terraformer__run_command('echo TEST', get_output=True), ['TEST'])
            mock_open.assert_not_called()
            mock_open.return_value.write.assert_not_called()
            mock_open.return_value.close.assert_not_called()
            # Test a command failure
            mock_cmd_iterator.return_value = iter([])
            mock_open.reset_mock()
            mock_popen.return_value.wait.return_value = 1
            self.assertEqual(self.terraformer._Terraformer__run_command('false', get_output=True), 1)
            mock_open.assert_not_called()
            mock_open.return_value.write.assert_not_called()
            mock_open.return_value.close.assert_not_called()

    @patch('terracumber.terraformer.Popen')
    def test_run_command_iterator(self, mock_popen, mock_unlink, mock_symlink, mock_path, mock_copy):
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend, {}, self.output_file)
        iterator = self.terraformer._Terraformer__run_command_iterator(mock_popen)
        with self.assertRaises(StopIteration):
            mock_popen.stdout.readline.return_value = "TEST"
            self.assertEqual(next(iterator), "TEST")
            mock_popen.stdout.readline.return_value = ""
            next(iterator)

    def test_apply(self, mock_unlink, mock_symlink, mock_path, mock_copy):
        # Arrange
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend, None,
                                                   self.output_file)
        with patch.object(self.terraformer, '_Terraformer__run_command') as mock_run_command:

            # Act
            self.terraformer.apply(20)

            # Assert
            mock_run_command.assert_called_with(["/usr/bin/terraform", "apply", "-auto-approve", "-parallelism=20"])

@patch('terracumber.terraformer.copy')
@patch('terracumber.terraformer.path')
@patch('terracumber.terraformer.symlink')
@patch('terracumber.terraformer.unlink')
class TestTerraformerSaltShaker(unittest.TestCase):
    def setUp(self):
        self.terraform_path = 'test/resources/salt-shaker'
        self.maintf = 'test/resources/salt-shaker/test-salt-shaker.tf'
        self.backend = 'libvirt'

    def test_get_single_node_ipaddr(self, mock_unlink, mock_symlink, mock_path, mock_copy):
        # Test an invalid machine
        self.terraformer = terraformer.Terraformer(self.terraform_path, self.maintf, self.backend)
        self.assertEqual(self.terraformer.get_single_node_ipaddr(), '192.168.122.100')
        # Test a valid machine
        self.terraformer = terraformer.Terraformer('/tmp', self.maintf, self.backend)
        with self.assertRaises(FileNotFoundError):
            self.assertIsNone(self.terraformer.get_single_node_ipaddr())

if __name__ == '__main__':
    unittest.main()
