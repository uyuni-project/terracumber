import pygit2
import os.path


class Git:
    ''' The Git class manages a git repository for the terraform code

    :param url: The URL for the Git repository
    :param ref: The Git reference to be used
    :param folder: The folder where the Git repository will be cloned to
    :param ssh_key: Dictionary with three keys (private, public, passphrase) to access local SSH Keys
    :param user_password: Dictionary with two keys (user, password)

    If neither ssh_key or user_password are provided, the class will try to use a Key pair from
    a SSH agent
    '''
    def __init__(self, url, ref, folder, ssh_key = None, user_password = None):
        self.url = url
        self.ref = ref
        self.folder = folder
        if ssh_key:
            CREDENTIALS = pygit2.credentials.Keypair('git',
                                         ssh_key['private'],
                                         ssh_key['public'],
                                         ssh_key['passphrase'])
        elif user_password:
            CREDENTIALS = pygit2.credentials.UserPass(user_password['user'],
                    user_password['password'])
        else:
            CREDENTIALS = pygit2.KeypairFromAgent('git')
        if os.path.isdir(self.folder):
            repo = pygit2.Repository(pygit2.discover_repository(self.folder))
            repo.remotes['origin'].fetch()
            remote_ref = self.ref.replace('refs/heads','refs/remotes/origin')
            remote_id = repo.lookup_reference(remote_ref).target
            local_id = repo.lookup_reference(self.ref)
            local_id.set_target(remote_id)
            repo.reset(local_id.target, pygit2.GIT_RESET_HARD)
        else:
            repo = pygit2.clone_repository(self.url, self.folder)
            repo.checkout(self.ref)

