import os
import paramiko
import stat

class Cucumber:
    ''' The Cucumber runs a cucumber testsuite on a controller node

    :param conn_data: dictionary for paramiko.client.SSHClient (http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient)
    :param load_system_host_keys: True or False
    :param MissingHostKeyPolicy: AutoAddPolicy or RejectPolicy strings (http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient)
    '''
    def __init__(self, conn_data, load_system_host_keys = True, MissingHostKeyPolicy=None):
        self.conn_data = conn_data
        self.ssh_client = paramiko.SSHClient()
        if MissingHostKeyPolicy == "RejectPolicy":
            MissingHostKeyPolicy = paramiko.RejectPolicy()
        else:
            MissingHostKeyPolicy = paramiko.AutoAddPolicy()
        self.ssh_client.set_missing_host_key_policy(MissingHostKeyPolicy)
        if load_system_host_keys:
            ssh_client.load_system_host_keys()
        self.ssh_client.connect(**conn_data)


    def run_command(self, command, env_vars = {}, output_file = False):
        ''' Run a command and get stdout and stderr merged

        :param command: The command to execute
        :param env_vars: A dictionary with the environment variables to be added
        :param output_file: If specified, writes the outputs to the specified path
        '''
        tran = self.ssh_client.get_transport()
        chan = tran.open_session()
        # Merge stdout and stderr in order
        chan.get_pty()
        chan.update_environment(env_vars)
        c = chan.makefile()
        chan.exec_command(command)
        if output_file:
            f = open(output_file, 'a')
        for line in c:
            print(line.strip())
            if output_file:
                f.write(line)
        if output_file:
            f.close()
        return(chan.recv_exit_status())


    def get(self, remotepath, localpath):
        ''' Get a file or folder from the controller
        :param remotepath: A remote path
        :param localpath: A local path
        '''
        sftp_client = self.ssh_client.open_sftp()
        sftp_client.get(remotepath, localpath)


    # Credit goes to https://stackoverflow.com/a/50130813
    def get_recursive(self, remotedir, localdir, sftp_client = None):
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
                except OSError:
                    pass
                self.get_recursive(remotepath, localpath, sftp_client)
            elif stat.S_ISREG(mode):
                sftp_client.get(remotepath, localpath)


    def close(self):
        ''' Close the SSH connection to the controller '''
        self.ssh_client.close()
        
