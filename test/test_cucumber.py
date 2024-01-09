from terracumber import cucumber
import unittest
from unittest.mock import patch


class TestCucumber(unittest.TestCase):
    def setUp(self):
        self.conn_data = {'hostname': None, 'username': 'root', 'port': 22, 'password': 'linux'}

    @patch('terracumber.cucumber.paramiko.SSHClient')
    @patch('builtins.open')
    def test_run_command(self, mock_open, mock_sshclient):
        self.cucumber = cucumber.Cucumber(self.conn_data)
        mock_sshclient.return_value.get_transport.return_value.open_session.return_value.recv_exit_status.return_value = 0
        self.assertEqual(self.cucumber.run_command('true'), 0)
        mock_sshclient.return_value.get_transport.return_value.open_session.return_value.recv_exit_status.return_value = 1
        self.assertEqual(self.cucumber.run_command('false'), 1)
        mock_sshclient.return_value.get_transport.return_value.open_session.return_value.makefile.return_value = [
            'VAR=555']
        self.cucumber.run_command('echo VAR=$VAR', {'VAR': '555'}, '/tmp/data.json')
        mock_open.assert_called_with('/tmp/data.json', 'a')
        mock_open.return_value.write.assert_called_with('VAR=555')
        mock_open.return_value.close.assert_called()

    @patch('terracumber.cucumber.paramiko.SSHClient')
    @patch('terracumber.cucumber.paramiko.sftp_attr')
    @patch('terracumber.cucumber.os.utime')
    def test_copy_atime_mtime(self, mock_utime, mock_sftp_attr, mock_sshclient):
        mock_sftp_attr.st_atime = 1
        mock_sftp_attr.st_mtime = 2
        mock_sshclient.return_value.open_sftp.return_value.stat.return_value = mock_sftp_attr
        self.cucumber = cucumber.Cucumber(self.conn_data)
        self.cucumber.copy_atime_mtime('/remote_path/file', '/local_path/file')
        mock_utime.assert_called_with('/local_path/file', (1, 2))

    @patch('terracumber.cucumber.paramiko.SSHClient')
    @patch('terracumber.cucumber.Cucumber.copy_atime_mtime')
    def test_get(self, mock_copy_atime_mtime, mock_sshclient):
        # No matches
        mock_sshclient.return_value.open_sftp.return_value.listdir.return_value = ['file']
        self.cucumber = cucumber.Cucumber(self.conn_data)
        with self.assertRaises(FileNotFoundError):
            self.cucumber.get('/remote_path/invalid', '/local_path/')
        # Get one file
        mock_sshclient.return_value.open_sftp.return_value.listdir.return_value = ['file']
        self.cucumber.get('/remote_path/file', '/local_path/')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/remote_path/file', '/local_path/file')
        # Get several files using a regex
        mock_sshclient.return_value.open_sftp.return_value.listdir.return_value = ['file', 'afile', 'aafile', 'file2']
        self.assertEqual(self.cucumber.get('/remote_path/.?file.*', '/local_path/'),
                         ['/remote_path/file', '/remote_path/afile', '/remote_path/file2'])
        # Get a whole directory
        self.assertEqual(self.cucumber.get('/remote_path/.*', '/local_path/'),
                         ['/remote_path/file', '/remote_path/afile', '/remote_path/aafile', '/remote_path/file2'])

    @patch('terracumber.cucumber.paramiko.SSHClient')
    @patch('terracumber.cucumber.Cucumber.copy_atime_mtime')
    @patch('terracumber.cucumber.os.mkdir')
    def test_get_recursive(self, mock_mkdir, mock_copy_atime_mtime, mock_sshclient):
        mock_sshclient.return_value.open_sftp.return_value.listdir.return_value = ['file', 'file2', 'folder/file3',
                                                                                   'folder/subfolder/file4']
        self.cucumber = cucumber.Cucumber(self.conn_data)
        self.cucumber.get_recursive('/remote_path/', '/local_path/')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/remote_path/file', '/local_path/file')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/remote_path/file2', '/local_path/file2')
        mock_mkdir.called_with('/local_path/folder')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/remote_path/folder/file3',
                                                                           '/local_path/folder/file3')
        mock_mkdir.called_with('/local_path/folder/subfolder')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/remote_path/folder/subfolder/file4',
                                                                           '/local_path/folder/subfolder/file4')

    @patch('terracumber.cucumber.paramiko.SSHClient')
    def test_put_file(self, mock_sshclient):
        # Put one file
        mock_sshclient.return_value.open_sftp.return_value.listdir.return_value = ['file']
        self.cucumber = cucumber.Cucumber(self.conn_data)
        self.cucumber.put_file('/local_path/file', '/remote_path/')
        mock_sshclient.return_value.open_sftp.return_value.get.called_with('/local_path/file', '/remote_path/')

    @patch('terracumber.cucumber.paramiko.SSHClient')
    def test_close(self, mock_sshclient):
        self.cucumber = cucumber.Cucumber(self.conn_data)
        self.cucumber.close()
        mock_sshclient.return_value.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
