"""Manage execution and outputs of cucumber at a controler node"""
import os
import re
import stat
import paramiko


class Cucumber:
    """The Cucumber class manages execution and outputs of cucumber at a controler node
    Keyword arguments:
    conn_data - dictionary for paramiko.client.SSHClient
                (http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient)
    Load_system_host_keys - Boolean to define whetever the system host keys should be used
                            or not
    MissingHostKeyPolicy - AutoAddPolicy or RejectPolicy strings
                           (http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient)
    """

    def __init__(self, conn_data, load_system_host_keys=True, MissingHostKeyPolicy=None):
        self.conn_data = conn_data
        self.ssh_client = paramiko.SSHClient()
        if MissingHostKeyPolicy == "RejectPolicy":
            MissingHostKeyPolicy = paramiko.RejectPolicy()
        else:
            MissingHostKeyPolicy = paramiko.AutoAddPolicy()
        self.ssh_client.set_missing_host_key_policy(MissingHostKeyPolicy)
        if load_system_host_keys:
            self.ssh_client.load_system_host_keys()
        self.ssh_client.connect(**conn_data)

    def run_command(self, command, env_vars=None, output_file=False):
        """Run a command and get print stdout and stderr (merged) to stdout and optionally a file

        Keyword arguments:
        command - A string with the command to execute
        env_vars - A dictionary with the environment variables to be added
        output_file - The path for a file to store stdout and stderr
        """
        tran = self.ssh_client.get_transport()
        chan = tran.open_session()
        # Merge stdout and stderr in order
        chan.get_pty()
        chan.update_environment(env_vars)
        chan_stream = chan.makefile()
        print("try to understand 1")
        chan.exec_command(command)
        print("try to understand 2")
        if output_file:
            o_file = open(output_file, 'a')
        for line in chan_stream:
            print(line.strip())
            if output_file:
                o_file.write(line)
        if output_file:
            o_file.close()
        print("try to understand 3")
        return chan.recv_exit_status()

    def copy_atime_mtime(self, remote_path, local_path):
        """Copy atime and mtime from a remote path to a local path

        Keyword arguments:
        remote_path: A string with the remote path
        local_path: A string with the local path
        """
        # This is required because paramiko does not provide any parameter
        # to preserve modification times, access times, and modes as -p
        # on scp
        sftp_client = self.ssh_client.open_sftp()
        atime = sftp_client.stat(remote_path).st_atime
        mtime = sftp_client.stat(remote_path).st_mtime
        os.utime(local_path, (atime, mtime))

    def get(self, remotepath, localpath):
        """Get a file from the controller

        Keyword arguments:
        remotepath - A string with the full remote path. The filename part can be a REGEX
        localpath - A string with the local path to the folder where data is to be copied
        """
        copied_files = []
        sftp_client = self.ssh_client.open_sftp()
        path = remotepath.rsplit('/', 1)[0]
        filename = remotepath.rsplit('/', 1)[1]
        files = sftp_client.listdir(path)
        for fname in files:
            if re.match("^%s$" % filename, fname):
                copied_files.append(path + '/' + fname)
                sftp_client.get(path + '/' + fname, localpath + '/' + fname)
                self.copy_atime_mtime(path + '/' + fname, localpath + '/' + fname)
        if not copied_files:
            raise FileNotFoundError
        return(copied_files)

    def put_file(self, localpath, remotepath):
        """Put a file in the controller

        Keyword arguments:
        localpath - A string with the local path to a file to be copied to the controler
        remotepath - A string with the full remote path
        """
        sftp_client = self.ssh_client.open_sftp()
        sftp_client.put(localpath, remotepath)

    # Credit goes to https://stackoverflow.com/a/50130813
    def get_recursive(self, remotedir, localdir, sftp_client=None):
        """Get a directory (recursively) from the controller)

        Keyword arguments:
        remotedir - A string with the path for the remote dir to be copied
        localdir - A string with the path for the local dir, including
                   the directory to be copied
        """
        sftp_client = self.ssh_client.open_sftp()
        if not os.path.isdir(localdir):
            os.mkdir(localdir)
        for entry in sftp_client.listdir_attr(remotedir):
            remotepath = remotedir + "/" + entry.filename
            localpath = os.path.join(localdir, entry.filename)
            mode = entry.st_mode
            if stat.S_ISDIR(mode):
                try:
                    os.mkdir(localpath)
                    self.copy_atime_mtime(remotepath, localpath)
                except OSError:
                    pass
                self.get_recursive(remotepath, localpath, sftp_client)
            elif stat.S_ISREG(mode):
                sftp_client.get(remotepath, localpath)
                self.copy_atime_mtime(remotepath, localpath)

    def close(self):
        """Close the SSH connection to the controller"""
        self.ssh_client.close()
