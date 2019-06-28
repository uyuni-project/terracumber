"""Run and manage terraform"""
from json import load
from os import environ, path
from shutil import copy
from subprocess import CalledProcessError, Popen, PIPE, STDOUT


class Terraformer:
    """The Terraformer class runs terraform to create and manage environments

    Keyword arguments:
    terraform_path - String with a path where the terraform code is
    maintf - String with the path where the main.tf file is
    variables - Dictionary with variables to be replaced at the main.tf
    output_file - String with the path to a file to store console output to the specified file
                  (False to avoid it)
    """

    def __init__(self, terraform_path, maintf, variables=None, output_file=False):
        self.terraform_path = terraform_path
        self.maintf = maintf
        self.variables = variables
        self.output_file = output_file
        copy(maintf, terraform_path + '/main.tf')

    def init(self):
        """Run terraform init"""
        return self.__run_command(["terraform", "init"])

    def taint(self, what):
        """Taint the resources matching the given types
 
        Keywords arguments:
        what - An array with the types to be tainted, for example: ['domain', 'main_disk']
        """
        resources = self.__get_resources(what)
        for resource in resources:
            split = [value for value in resource.split('.') if value != 'module']
            module = '.'.join(split[0:-2])
            element = '.'.join(split[-2:])
            self.__run_command(["terraform", "taint", "-module=%s" % module, "%s" % element])

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
            for module in j['modules']:
                if '.'.join(module['path']) == resource:
                    return module['outputs']['configuration']['value']['hostname']
        return None

    def __get_resources(self, what=None):
        """Get a list of all resources from the tfstate file, or only
           some type of resources is used
        """
        if not path.isfile(self.terraform_path + '/terraform.tfstate'):
            return[]
        all_resources = self.__run_command(
            ["terraform", "state", "list"], True)
        if not what:
            return all_resources
        filtered_resources = []
        for resource in all_resources:
            if resource.split('.')[-1] in what:
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
