"""Run and manage terraform"""
import fileinput
from json import load, JSONDecodeError
from os import environ, path, symlink, unlink
from re import match, subn
from shutil import copy
from subprocess import CalledProcessError, Popen, PIPE, STDOUT
from .tf_module_cleaner import remove_unselected_tf_resources

# Fallback to allow running python3 -m unittest
try:
    from utils import merge_two_dicts
except ImportError:
    from .utils import merge_two_dicts


class Terraformer:
    """The Terraformer class runs terraform to create and manage environments

    Keyword arguments:
    terraform_path - String with a path where the terraform code is
    maintf - String with the path where the main.tf file is
    backend - suma backend to be used
    variables - Dictionary with variables to be replaced at the main.tf
    output_file - String with the path to a file to store console output to the specified file
                  (False to avoid it)
    terraform_bin - path to terraform bin
    """

    def __init__(self, terraform_path, maintf, backend, variables={}, output_file=False, terraform_bin='/usr/bin/terraform', variables_description_file="", tfvars_files=[]):
        self.terraform_path = terraform_path
        self.maintf = maintf
        self.variables = variables or {}
        self.output_file = output_file
        self.terraform_bin = terraform_bin
        self.variables_description_file = variables_description_file
        self.tfvars_files = tfvars_files
        self.backend = backend
        self.is_prepared = False  # Flag to check if the environment is prepared

    def prepare_environment(self):
        """Prepare the terraform environment by copying files and setting up symlinks."""
        if not self.is_prepared:
            copy(self.maintf, self.terraform_path + '/main.tf')
            if path.isfile(self.variables_description_file):
                copy(self.variables_description_file, self.terraform_path + '/variables.tf')
            for tfvars_file in self.tfvars_files:
                copy(tfvars_file, self.terraform_path)
                self.tfvars_files.append(path.basename(tfvars_file))

            # Only if we are using a folder with folder structure used by sumaform
            if path.exists('%s/backend_modules/%s' % (path.abspath(self.terraform_path), self.backend)):
                if path.islink('%s/modules/backend' % self.terraform_path):
                    unlink('%s/modules/backend' % self.terraform_path)
                symlink('%s/backend_modules/%s' % (path.abspath(self.terraform_path), self.backend),
                        '%s/modules/backend' % self.terraform_path)

            self.is_prepared = True  # Mark as prepared

    def inject_repos(self, custom_repositories_json):
        """Set additional repositories into the main.tf, so they are injected by sumaform

        Returns:
            0 if no error
            1 if the json is not well-formed
            2 if the main.tf has an incorrect number of placeholders
        """
        self.prepare_environment()  # Ensure environment is prepared
        if custom_repositories_json:
            try:
                repos = load(custom_repositories_json)
            except JSONDecodeError:
                return 1
            for node in repos.keys():
                if node == 'server' or node == 'proxy':
                    node_mu_repos = repos.get(node, None)
                    replacement_list = ["additional_repos = {"]
                    for name, url in node_mu_repos.items():
                        replacement_list.append(f'\n    "{name}" = "{url}"')
                    replacement_list.append("\n}")
                    replacement = ''.join(replacement_list)
                    placeholder = f'//{node}_additional_repos'
                    n_replaced = 0
                    for line in fileinput.input(f"{self.terraform_path}/main.tf", inplace=True):
                        (new_line, n) = subn(placeholder, replacement, line)
                        print(new_line, end='')
                        n_replaced += n
                    if n_replaced > 1:
                        return 2
                    elif n_replaced == 0:
                        return 3
        return 0

    def init(self):
        self.prepare_environment()  # Ensure environment is prepared
        """Run terraform init"""
        return self.__run_command([self.terraform_bin, "init"])

    def taint(self, what):
        self.prepare_environment()  # Ensure environment is prepared
        """Taint resources according to a regex

        Keywords arguments:
        what - A regex expression
        """
        resources = self.__get_resources(what)
        for resource in resources:
            print(resource)
            self.__run_command([self.terraform_bin, "taint", "%s" % resource])

    def apply(self, parallelism=10, use_tf_resource_cleaner=False, tf_resources_to_keep=[], tf_resources_to_delete=[]):
        """Run terraform apply after removing unselected resources from the main.tf.

        parallelism - Define the number of parallel resource operations. Defaults to 10 as specified by terraform.
        use_tf_resource_cleaner - Option to enable or disable the resource cleaner mechanism
        tf_resources_to_keep - List of minions to keep. If not minions are declared, all minions are going to be removed.
        tf_resources_to_delete - Active action to delete proxy, monitoring-server or retail ( build and terminal minions)
        """
        self.prepare_environment()  # Ensure environment is prepared
        if use_tf_resource_cleaner:
            remove_unselected_tf_resources(f"{self.terraform_path}/main.tf", tf_resources_to_keep, tf_resources_to_delete)

        command_arguments = [self.terraform_bin, "apply", "-auto-approve", f"-parallelism={parallelism}"]
        for file in self.tfvars_files:
            command_arguments.append(f"-var-file={file}")
        return self.__run_command(command_arguments)

    def destroy(self):
        """Run terraform destroy"""
        command_arguments = [self.terraform_bin, "destroy", "-auto-approve"]
        for file in self.tfvars_files:
            command_arguments.append("-var-file=%s" % file)
        self.__run_command(command_arguments)

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

    def get_single_node_ipaddr(self):
        """Get the hostname for a single node from tfstate file"""
        with open(self.terraform_path + '/terraform.tfstate', 'r') as tf_state:
            j = load(tf_state)
            # This seems to be sumaform specific. I wonder if there is
            # a way of making this generic :-(
            value = j['outputs']['configuration']['value']
            if 'ipaddrs' in value.keys():
                return value['ipaddrs'][0][0]
        return None

    def __get_resources(self, what=None):
        """Get a list of all resources from the tfstate file, or only
           some type of resources is used
        """
        if not path.isfile(self.terraform_path + '/terraform.tfstate'):
            return []
        # We should use the terraform.tf state file for this, but then we
        # would need a way more complicated code, as you can't get the
        # addresses from the file without transformations depending
        # on the resource type.
        all_resources = self.__run_command(
            [self.terraform_bin, "state", "list"], True)
        if not what:
            return all_resources
        filtered_resources = []
        for resource in all_resources:
            if match(what, resource):
                filtered_resources.append(resource)
        return filtered_resources

    def __run_command(self, command, get_output=False):
        """Run an arbitary command locally. Optionally, store the output to a file. """
        if get_output:
            output = []
            output_file = None
        else:
            output_file = open(self.output_file, 'a')
        try:
            process = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=self.terraform_path,
                            universal_newlines=True, env=merge_two_dicts(environ, self.variables))
            for stdout_line in self.__run_command_iterator(process):
                if get_output:
                    output.append(stdout_line.rstrip())
                    continue
                if output_file:
                    output_file.write(stdout_line)
                    print(stdout_line, end='')
            process.stdout.close()
            return_code = process.wait()
            if return_code:
                raise CalledProcessError(return_code, command)
            if get_output:
                return output
            return 0
        except CalledProcessError as error:
            return error.returncode
        finally:
            if output_file:
                output_file.close()

    def __run_command_iterator(self, process):
        """ Return data from running an arbitary command locally, merge stderr to stdout and work as an interator """
        for stdout_line in iter(process.stdout.readline, ""):
            yield stdout_line
