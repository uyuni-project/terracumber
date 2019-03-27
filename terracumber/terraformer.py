from json import load
from os import environ, path
from shutil import copy
from subprocess import CalledProcessError, Popen, PIPE, STDOUT

class Terraformer:
    ''' The Terraformer class runs terraform to create enviroments

    :param terraform_path: Path where the terraform code is
    :param maintf: Path where the main.tf file is
    :param workdir: Path where the work directory for terraform is located
    :param variables: Dictionary with variables to be replaced at the main.tf
    :param init: True if you want to run terraform init
    :param destroy: True if you want to complete destroy the environment
    :param taint: Array with elements to be tained (for example ['domain', 'main_disk'] (should be used with destroy = False)
    :param output_file: Store console output to the specified file (False to avoid it)
    '''
    def __init__(self, terraform_path, maintf, variables = None, init = True, destroy = True, taint = None, output_file = False):
        self.terraform_path = terraform_path
        self.maintf = maintf
        self.variables = variables
        self.init = init
        self.destroy = destroy
        self.taint = taint
        self.output_file = output_file
        copy(maintf, terraform_path + '/main.tf')
        if init:
            self.__run_command(["terraform", "init"])
        if taint:
            resources = self.__get_resources(taint)
            for resource in resources:
                split = [value for value in resource.split('.') if value != 'module']
                module = '.'.join(split[0:-2])
                element = '.'.join(split[-2:])
                self.__run_command(["terraform", "taint", "-module=%s" % module, "%s" % element])
        if destroy:
            self.__run_command(["terraform", "destroy", "-auto-approve"])


    def apply(self):
        return(self.__run_command(["terraform", "apply", "-auto-approve"]))


    def get_hostname(self, resource):
        with open(self.terraform_path + '/terraform.tfstate', 'r') as f:
            j = load(f)
            for module in j['modules']:
                if '.'.join(module['path']) == resource:
                    return(module['outputs']['configuration']['value']['hostname'])


    def __get_resources(self, what = None):
        if not path.isfile(self.terraform_path + '/terraform.tfstate'):
            return([])
        all_resources = self.__run_command(["terraform", "state", "list"], True)
        if not what:
            return(all_resources)
        filtered_resources = []
        for resource in all_resources:
            if resource.split('.')[-1] in what:
                filtered_resources.append(resource)
        return(filtered_resources)


    def __run_command(self, command, get_output = False):
        if get_output:
            output = []
        if self.output_file:
            f = open(self.output_file, 'a')
        try:
            for stdout_line in self.__run_command_iterator(command):
                if get_output:
                    output.append(stdout_line.rstrip())
                    continue
                if self.output_file:
                    f.write(stdout_line)
                print(stdout_line, end='')
            if get_output:
                return(output)
            return(0)
        except CalledProcessError as e:
            return(e.returncode)
        finally:
            if self.output_file:
                f.close()


    def __run_command_iterator(self, command):
        process = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=self.terraform_path, universal_newlines=True, env={**environ, **self.variables})
        for stdout_line in iter(process.stdout.readline, ""):
            yield stdout_line
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            raise CalledProcessError(return_code, command)
