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
    auto: If True, clone the repository immediately, or do a forced checkout if directory
          already exists

    If neither ssh_key or user_password are provided, the class will try to use a Key pair from
    a SSH agent
    """

    def __init__(self, url, ref, folder, auth=None, auto=False):
        self.url = url
        self.ref = ref
        self.folder = folder
        self.cloning = False
        self.tag = False
        self.reset_hard = False
        self.repo = None
        if 'user' in auth:
            self.credentials = pygit2.credentials.UserPass(auth['user'],
                                                           auth['password'])
        elif 'private' in auth:
            self.credentials = pygit2.credentials.Keypair('git',
                                                          auth['private'],
                                                          auth['public'],
                                                          auth['passphrase'])
        else:
            self.credentials = pygit2.KeypairFromAgent('git')
        if not auto:
            return
        if os.path.isdir(self.folder):
            self.repo = pygit2.Repository(pygit2.discover_repository(self.folder))
            self.checkout()
        else:
            self.clone()

    def clone(self):
        """ Clone a repository to the specified folder """
        self.cloning = True
        self.repo = pygit2.clone_repository(self.url, self.folder)
        try:
            self.repo.checkout('refs/heads/' + self.ref)
        except KeyError:
            # Maybe this is a tag
            self.repo.checkout('refs/tags/' + self.ref)

    def ref_is_tag(self):
        """ Check if the reference on the object is a tag
            This can only be checked on the local repository, so if
            you want to check tags on a new remote, make sure you use
            refresh_local_repo() first """
        if 'refs/tags/' + self.ref in self.repo.listall_references():
            self.tag = True
            return True
        return False

    def is_remote(self):
        """ Check if a remote exits on a local repository """
        for remote in self.repo.remotes:
            if remote.url == self.url:
                return remote.name
        return False

    def remove_all_tags(self):
        """ Remove all tags from a local repository """
        removed = False
        for reference in self.repo.listall_references():
            if re.match('refs\/tags\/.+', reference):
                self.repo.references.delete(reference)
                removed = True
        return removed

    def create_remote_from_url(self):
        """ Create a remote from URL on a local repository """
        remote_name = self.url.replace('/', '-').replace('.', '-').replace(':', '-')
        self.repo.remotes.create(remote_name, self.url)
        return remote_name

    def refresh_local_repo(self):
        """ Refresh a local repository, including remote change management when
            needed """
        # Create the current remote if we don't have it
        remote = self.is_remote()
        if not remote:
            remote = self.create_remote_from_url()
        remote_url = self.repo.remotes[remote].url
        # Delete tags and fetch from the remote
        print("Removing tags and fetching from %s..." % remote_url)
        self.remove_all_tags()
        # We need to force tags, as otherwise fetch() only downloads
        # heads by default
        # We need to force fetching pull requests as well, so than we
        # can checkout pr/PR/head where PR is the pull request number
        self.repo.remotes[remote].fetch(refspecs=['+refs/heads/*:refs/remotes/%s/*' % remote,
                                                  '+refs/tags/*:refs/remotes/%s/*' % remote,
                                                  '+refs/pull/*:refs/remotes/%s/pr/*' % remote])
        return remote, remote_url

    def checkout(self):
        """ Checkout changes ignoring any local changes """
        remote, remote_url = self.refresh_local_repo()
        # Calculate remote reference
        if self.ref_is_tag():
            remote_ref = 'refs/tags/' + self.ref
            print("%s seems to be a tag" % self.ref)
        else:
            remote_ref = 'refs/remotes/' + remote + '/' + self.ref
        try:
            remote_id = self.repo.lookup_reference(remote_ref).target
        except KeyError:
            raise Exception("Could not find reference %s (remote URL %s)" % (
                remote_ref, remote_url)) from None
        print("Checking out")
        # If the remote ref is a tag, just checkout
        if self.ref_is_tag():
            local_ref = remote_ref
            local_id = self.repo.lookup_reference(local_ref)
            self.repo.checkout(local_ref)
            return
        # Otherwise, checkout the reference, set the remote ID
        # and perform a hard reset
        try:
            local_ref = 'refs/heads/' + self.ref
            local_id = self.repo.lookup_reference(local_ref)
            self.repo.checkout(local_ref)
            local_id.set_target(remote_id)
        # The exception happens if the local_ref is not available
        except KeyError as e:
            self.repo.create_reference(local_ref, remote_id)
            self.repo.checkout(local_ref)
            local_id = self.repo.lookup_reference(local_ref)
        print("Performing hard reset to ignore local changes")
        self.repo.reset(local_id.target, pygit2.GIT_RESET_HARD)
        self.reset_hard = True
