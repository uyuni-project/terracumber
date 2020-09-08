"""Manage a git repository"""
import os
import os.path
import pygit2
import re


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
        try:
            repo.checkout('refs/heads/' + self.ref)
        except KeyError:
            # Maybe this is a tag
            repo.checkout('refs/tags/' + self.ref)

    def ref_is_tag(self):
        """ Check if the reference on the object is a tag
            This can only be checked on the local repository, so if
            you want to check tags on a new remote, make sure you use
            refresh_local_repo() first """
        repo = pygit2.Repository(pygit2.discover_repository(self.folder))
        if 'refs/tags/' + self.ref in repo.listall_references():
            return True
        return False


    def refresh_local_repo(self):
        """ Refresh a local repository, including remote change management when
            needed """
        repo = pygit2.Repository(pygit2.discover_repository(self.folder))
        # Create the current remote if we don't have it
        create_remote = True
        for remote in repo.remotes:
            if remote.url == self.url:
                remote = remote.name
                create_remote = False
                break
        if create_remote:
            remote = self.url.replace(
                '/', '-').replace('.', '-').replace(':', '-')
            repo.remotes.create(remote, self.url)
        remote_url = repo.remotes[remote].url
        # Delete tags and fetch from the remote
        print("Removing tags and fetching from %s..." % remote_url)
        for reference in repo.listall_references():
            if re.match('refs\/tags\/.+', reference):
                repo.references.delete(reference)
        # We need to force tags, as otherwise fetch() only downloads heds by default
        repo.remotes[remote].fetch(refspecs=['+refs/heads/*:refs/remotes/%s/*' % remote, '+refs/tags/*:refs/remotes/%s/*' % remote])
        return repo, remote, remote_url


    def checkout(self):
        """ Checkout changes ignoring any local changes """
        repo, remote, remote_url = self.refresh_local_repo()
        # Calculate remote reference
        if self.ref_is_tag():
            remote_ref = 'refs/tags/' + self.ref
            print("%s seems to be a tag" % self.ref)
            try:
                remote_id = repo.lookup_reference(remote_ref).target
            except KeyError:
                raise KeyError("Could not find reference %s (remote URL %s)" % (
                    remote_ref, remote_url))
        else:
            remote_ref = 'refs/remotes/' + remote + '/' + self.ref
            try:
                remote_id = repo.lookup_reference(remote_ref).target
            except KeyError:
                raise KeyError("Could not find reference %s (remote URL %s)" % (
                    remote_ref, remote_url))

        print("Checking out")
        # If the remote ref is a tag, just checkout
        if self.ref_is_tag():
            local_ref = remote_ref
            local_id = repo.lookup_reference(local_ref)
            repo.checkout(local_ref)
            return
        # Otherwise, checkout the reference, set the remote ID
        # and perform a hard reset
        try:
            local_ref = 'refs/heads/' + self.ref
            local_id = repo.lookup_reference(local_ref)
            repo.checkout(local_ref)
            local_id.set_target(remote_id)
        # The exception happens if the local_ref is not available
        except KeyError as e:
            repo.create_reference(local_ref, remote_id)
            repo.checkout(local_ref)
            local_id = repo.lookup_reference(local_ref)
        print("Performing hard reset to ignore local changes")
        repo.reset(local_id.target, pygit2.GIT_RESET_HARD)
