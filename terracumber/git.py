"""Manage a git repository"""
import os
import os.path
import pygit2


class Git:
    """The Git class manages a git repository

    Keyword arguments:
    url: The URL for the Git repository
    ref: The Git reference to be used
    folder: The folder where the Git repository will be cloned to
    auth: Either a dictionary with three keys (private, public, passphrase) to access local SSH Keys
          or a dictionary with two keys (user, password) to user user/password authentication
    auto: If True, clone the repository inmediatly, or do a forced checkout if directory
          already exists

    If neither ssh_key or user_password are provided, the class will try to use a Key pair from
    a SSH agent
    """
    def __init__(self, url, ref, folder, auth=None, auto=False):
        self.url = url
        self.ref = ref
        self.folder = folder
        if 'user' in auth:
            credentials = pygit2.credentials.UserPass(auth['user'],
                                                      auth['password'])
        elif 'private' in auth:
            credentials = pygit2.credentials.Keypair('git',
                                                     auth['private'],
                                                     auth['public'],
                                                     auth['passphrase'])
        else:
            credentials = pygit2.KeypairFromAgent('git')
        if not auto:
            return
        if os.path.isdir(self.folder):
            self.checkout()
        else:
            self.clone()

    def clone(self):
        """ Clone a repository to the specified folder """
        repo = pygit2.clone_repository(self.url, self.folder)
        repo.checkout(self.ref)

    def checkout(self):
        """ Checkout changes ignoring any local changes """
        repo = pygit2.Repository(pygit2.discover_repository(self.folder))
        repo.remotes['origin'].fetch()
        remote_ref = self.ref.replace('refs/heads', 'refs/remotes/origin')
        remote_id = repo.lookup_reference(remote_ref).target
        local_id = repo.lookup_reference(self.ref)
        local_id.set_target(remote_id)
        repo.reset(local_id.target, pygit2.GIT_RESET_HARD)
