import os
import shutil
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
Extracts the default modules that should not be removed based on the `delete_all` flag.

:param maintf_content: Content of the main.tf file.
:param delete_all: Boolean indicating whether to delete all resources (True) or just clients (False).
:return: List of module names to keep.
"""
def get_default_modules(maintf_content, delete_all):
    module_names = re.findall(r'module\s+"([^"]+)"', maintf_content)
    exclusions = ['minion', 'client']

    if delete_all:
        exclusions.extend(['terminal', 'buildhost', 'proxy', 'dhcp_dns', 'monitoring_server'])

    filtered_module_names = [name for name in module_names if all(exclusion not in name for exclusion in exclusions)]

    logger.info(f"Default modules to keep: {filtered_module_names}")
    return filtered_module_names

"""
Check for any resource in the line with exact match within '.'.

:param line: A configuration line from the controller.
:param tf_resources_to_keep: List of resources to keep.
:return: Boolean indicating if the line contains a resource to keep.
"""
def contains_resource_name(line, tf_resources_to_keep):
    return any(re.search(rf'\.{re.escape(resource)}\.', line) for resource in tf_resources_to_keep)

"""
Filters configuration lines in the controller module to retain only the configurations
for the resources that should be kept. Also ensures that the output module is not deleted.

:param maintf_content: Content of the main.tf file.
:param tf_resources_to_keep: List of resources to keep.
:return: Filtered main.tf content.
"""
def filter_module_references(maintf_content, tf_resources_to_keep):
    lines = maintf_content.split('\n')
    filtered_lines = [
        line for line in lines
        if (
            ('configuration' not in line or contains_resource_name(line, tf_resources_to_keep)) and
            'WORKAROUND' not in line
        ) or 'output' in line
    ]
    return '\n'.join(filtered_lines)

"""
Removes modules and controller references for resources not in the resources to keep list.
Removes comments outside modules from main.tf.

:param maintf_file: Path to the main.tf file.
:param tf_resources_to_keep - List of resources to keep
:param delete_all: Boolean indicating whether to delete all resources (True) or just clients (False).
"""
def remove_unselected_tf_resources(maintf_file, tf_resources_to_keep, delete_all):
    with open(maintf_file, 'r') as file:
        raw_data = file.readlines()

    filtered_lines = [line for line in raw_data if not line.lstrip().startswith("//")]
    data = ''.join(filtered_lines)
    modules = data.split("module ")
    tf_resources_to_keep.extend(get_default_modules(data, delete_all))
    logger.info(f"Resources to keep {tf_resources_to_keep}.")

    for module in modules[1:]:
        module_name = module.split('"')[1]
        if module_name not in tf_resources_to_keep:
            logger.info(f"Removing module {module_name} from main.tf")
            data = data.replace("module " + module, '')
        elif module_name == 'controller':
            data = data.replace(module, filter_module_references(module, tf_resources_to_keep))
    cleaned_content = re.sub(r'\n{3,}', '\n\n', data)
    with open(maintf_file, 'w') as file:
        file.write(cleaned_content)
        logger.info(f"Unused modules removed from {maintf_file}.")
