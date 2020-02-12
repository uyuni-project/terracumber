"""Run and manage terraform"""
from json import load
from os import environ, path, symlink, unlink
from re import match
from shutil import copy
from subprocess import CalledProcessError, Popen, PIPE, STDOUT


class Terraformer:
    """The Terraformer class runs terraform to create and manage environments

    Keyword arguments:
    terraform_path - String with a path where the terraform code is
    maintf - String with the path where the main.tf file is
    backend - suma backend to be used
    variables - Dictionary with variables to be replaced at the main.tf
    output_file - String with the path to a file to store console output to the specified file
                  (False to avoid it)
    """

    def __init__(self, terraform_path, maintf, backend, variables=None, output_file=False):
        self.terraform_path = terraform_path
        self.maintf = maintf
        self.variables = variables
        self.output_file = output_file
        copy(maintf, terraform_path + '/main.tf')
        # Only if we are using a folder with folder structure used by sumaform
        if path.exists('%s/backend_modules/%s' % (terraform_path, backend)):
            if path.exists('%s/modules/backend' % terraform_path):
                unlink('%s/modules/backend' % terraform_path)
            symlink('%s/backend_modules/%s' %(terraform_path, backend),
            '%s/modules/backend' % terraform_path)


    def init(self):
        """Run terraform init"""
        return self.__run_command(["terraform", "init"])

    def taint(self, what):
        """Taint resources according to a retex
 
        Keywords arguments:
        what - A regex expression
        """
        resources = self.__get_resources(what)
        for resource in resources:
            print(resource)
            self.__run_command(["terraform", "taint", "%s" % resource])

    def apply(self):
        """Run terraform apply"""
        return self.__run_command(["terraform", "apply", "-auto-approve"])

    def destroy(self):
        """Run terraform destroy"""
        self.__run_command(["terraform", "destroy", "-auto-approve"])

    def get_hostname(self, resource):
        """Get a hostname for an instance from the tfstate file"""
        with open(self.terraform_path + '/terraform.tfstate', 'r') as tf_state:
            j = load(tf_state)
            # This seems to be sumaform specific. I wonder if there is
            # a way of making this generic :-(
            value = j['outputs']['configuration']['value']
            if resource in value.keys():
                if 'hostnames' in value[resource].keys():
                    return value[resource]['hostnames'][0]
                if 'hostname' in value[resource].keys():
                    return value[resource]['hostname']
        return None

    def __get_resources(self, what=None):
        """Get a list of all resources from the tfstate file, or only
           some type of resources is used
        """
        if not path.isfile(self.terraform_path + '/terraform.tfstate'):
            return[]
        # We should use the terraform.tf state file for this, but then we
        # would need a way more complicated code, as you can't get the
        # addresses from the file without transformations depending
        # on the resource type.
        all_resources = self.__run_command(["terraform", "state", "list"], True)
        if not what:
            return all_resources
        filtered_resources = []
        for resource in all_resources:
            if match(what, resource):
                filtered_resources.append(resource)
        return filtered_resources

    def __run_command(self, command, get_output=False):
        """Run an arbitary command locally. Optionally, store the output to a file.
           This is fact a wrapper for __run_command_iterator()
        """
        if get_output:
            output = []
        if self.output_file:
            output_file = open(self.output_file, 'a')
        try:
            for stdout_line in self.__run_command_iterator(command):
                if get_output:
                    output.append(stdout_line.rstrip())
                    continue
                if self.output_file:
                    output_file.write(stdout_line)
                print(stdout_line, end='')
            if get_output:
                return output
            return 0
        except CalledProcessError as error:
            return error.returncode
        finally:
            if self.output_file:
                output_file.close()

    def __run_command_iterator(self, command):
        """Run an arbitary command locally, merge stderr to stdout and work as an interator """
        process = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=self.terraform_path,
                        universal_newlines=True, env={**environ, **self.variables})
        for stdout_line in iter(process.stdout.readline, ""):
            yield stdout_line
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise CalledProcessError(return_code, command)
