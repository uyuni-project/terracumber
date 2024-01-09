from terracumber import git
import pygit2
import unittest
from unittest.mock import patch


class TestGit(unittest.TestCase):
    def setUp(self):
        self.repo_url = 'https://github.com/uyuni-project/terracumber.git'
        self.ref = 'master'
        self.folder = '/tmp/folder'
        self.username = 'myuser'
        self.password = 'mypassword'
        self.auto = True

    def test_init_credentials_user_password(self):
        credentials = pygit2.credentials.UserPass(self.username, self.password)
        self.repo = git.Git(self.repo_url, self.ref, self.folder, {'user': self.username, 'password': self.password})
        self.assertEqual(vars(self.repo.credentials), vars(credentials))

    def test_init_credentials_private(self):
        credentials = pygit2.credentials.Keypair('git', 'mykeypath', 'mypublicpath', 'mypassphrase')
        self.repo = git.Git(self.repo_url, self.ref, self.folder,
                            {'public': 'mypublicpath', 'private': 'mykeypath', 'passphrase': 'mypassphrase'})
        self.assertEqual(vars(self.repo.credentials), vars(credentials))

    @patch('terracumber.git.os.path.isdir', return_value=False)
    @patch('terracumber.git.pygit2.Repository')
    @patch('terracumber.git.pygit2.clone_repository')
    def test_clone(self, mock_clone_repository, mock_pygit2, mock_isdir):
        self.repo = git.Git(self.repo_url, self.ref, self.folder, {'user': self.username, 'password': self.password},
                            self.auto)
        self.assertTrue(self.repo.cloning)

    @unittest.expectedFailure
    @patch('terracumber.git.pygit2.clone_repository')
    @patch('terracumber.git.pygit2.Repository')
    def test_clone_ref_is_tag(self, mock_repository, mock_clone_repository):
        mock_repository.return_value.listall_references.return_value = ['ref/heads/master', 'refs/tags/mytag']
        self.repo = git.Git(self.repo_url, 'mytag', self.folder, {'user': self.username, 'password': self.password},
                            self.auto)
        self.assertTrue(self.repo.ref_is_tag())
        self.repo = git.Git(self.repo_url, 'mybranch', self.folder, {'user': self.username, 'password': self.password},
                            self.auto)
        self.assertFalse(self.repo.ref_is_tag(), True)

    @unittest.expectedFailure
    @patch('terracumber.git.pygit2.Repository')
    @patch('terracumber.git.pygit2.Remote')
    @patch('terracumber.git.Git.checkout')
    def test_is_remote(self, mock_checkout, mock_remote, mock_repository):
        mock_remote.name = 'origin'
        mock_remote.url = 'https://github.com/uyuni-project/terracumber.git'
        mock_repository.return_value.remotes = [mock_remote]
        self.repo = git.Git(self.repo_url, 'mytag', self.folder, {'user': self.username, 'password': self.password},
                            self.auto)
        self.assertTrue(self.repo.is_remote())
        self.repo = git.Git('https://github.com/uyuni-project/terracumber2.git', 'mytag', self.folder,
                            {'user': self.username, 'password': self.password}, self.auto)
        self.assertFalse(self.repo.is_remote())

    @patch('terracumber.git.pygit2.Repository')
    def test_remove_all_tags(self, mock_repository):
        mock_repository.return_value.listall_references.return_value = ['ref/heads/master', 'refs/tags/mytag']
        self.repo = git.Git(self.repo_url, 'mytag', self.folder, {'user': self.username, 'password': self.password},
                            self.auto)
        self.assertTrue(self.repo.remove_all_tags())
        mock_repository.return_value.listall_references.return_value = ['ref/heads/master']
        self.assertFalse(self.repo.remove_all_tags())

    @unittest.expectedFailure
    @patch('terracumber.git.pygit2.Repository')
    def test_create_remote_from_url(self, mock_pygit2):
        self.repo = git.Git('https://github.com/uyuni-project/terracumber2.git', 'mytag', self.folder,
                            {'user': self.username, 'password': self.password}, self.auto)
        self.assertEqual(self.repo.create_remote_from_url(), 'https---github-com-uyuni-project-terracumber2-git')

    @patch('terracumber.git.os.path.isdir', return_value=True)
    @patch('terracumber.git.pygit2.Repository')
    @patch('terracumber.git.Git.refresh_local_repo', return_value=('https---github-com-uyuni-project-terracumber-git',
                                                       'https://github.com/uyuni-project/terracumber.git'))
    def test_refresh_local_repo(self, mock_refres_local_repo, mock_repository, mock_is_dir):
        mock_repository.return_value.listall_references.return_value = ['ref/heads/master', 'refs/tags/mytag']
        # Simulate invalid references
        mock_repository.return_value.lookup_reference.side_effect = KeyError()
        # Tag exists locally but not on the remote
        mock_repository.return_value.lookup_reference.side_effect = KeyError()
        with self.assertRaises(Exception) as e:
            self.repo = git.Git('https://github.com/uyuni-project/terracumber.git', 'mytag', self.folder,
                                {'user': self.username, 'password': self.password}, self.auto)
        self.assertEqual(str(e.exception),
                         "Could not find reference refs/tags/mytag (remote URL https://github.com/uyuni-project/terracumber.git)")
        # Branch exists locally but not on the remote
        with self.assertRaises(Exception) as e:
            self.repo = git.Git('https://github.com/uyuni-project/terracumber.git', 'master', self.folder,
                                {'user': self.username, 'password': self.password}, self.auto)
        self.assertEqual(str(e.exception),
                         "Could not find reference refs/remotes/https---github-com-uyuni-project-terracumber-git/master (remote URL https://github.com/uyuni-project/terracumber.git)")
        # Simulate valid references
        mock_repository.return_value.lookup_reference.side_effect = None
        # Tag exists locally and on the remote
        self.repo = git.Git('https://github.com/uyuni-project/terracumber.git', 'mytag', self.folder,
                            {'user': self.username, 'password': self.password}, self.auto)
        self.assertFalse(self.repo.reset_hard)
        # Branch exists locally and on the remote
        self.repo = git.Git('https://github.com/uyuni-project/terracumber.git', 'mybranch', self.folder,
                            {'user': self.username, 'password': self.password}, self.auto)
        self.assertTrue(self.repo.reset_hard)


if __name__ == '__main__':
    unittest.main()
