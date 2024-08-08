import os
import shutil
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
Extracts the default modules that should not be removed.

maintf_content - Content of the main.tf file
"""
def get_default_modules(maintf_content):
    module_names = re.findall(r'module\s+"([^"]+)"', maintf_content)
    filtered_module_names = [name for name in module_names if 'minion' not in name and 'client' not in name]
    logger.info(f"Default modules are {filtered_module_names}")
    return filtered_module_names

"""
Checks if a configuration line in the controller module references is a minion that should be kept.

line - A configuration line from the controller
minions_list - List of minions to keep
"""
def contains_minion(line, minions_list):
    return any(minion in line for minion in minions_list)

"""
Filters configuration lines in the controller module to retain only the configurations
for the minions that should be kept. Also ensures that the output module is not deleted
(identified by having 'configuration' in the title). Removes workaround lines for clarity.

maintf_content - Content of the main.tf file
minions_list - List of minions to keep
"""
def filter_module_references(maintf_content, minions_list):
    lines = terraform_content.split('\n')
    filtered_lines = [
        line for line in lines
        if (
            ('configuration' not in line or contains_minion(line, minions_list)) and
            'WORKAROUND' not in line
        ) or 'output' in line
    ]
    return '\n'.join(filtered_lines)

"""
Removes minion modules that are not in the list of minions to keep.

maintf_file - Path to the main.tf file
minions_list - List of minions to keep
"""
def remove_unused_minion(maintf_file, minion_list):
    with open(maintf_file, 'r') as file:
        data = file.read()

    modules = data.split("module ")

    minion_list.extend(get_default_modules(data))

    for module in modules[1:]:
        module_name = module.split('"')[1]
        if module_name not in minion_list and 'base' not in module_name:
            logger.info(f"Removing minion {module_name} from main.tf")
            data = data.replace("module " + module, '')
        elif module_name == 'controller':
            data = data.replace(module, filter_module_references(module, minion_list))

    cleaned_content = re.sub(r'\n{3,}', '\n\n', data)
    with open(terraform_file, 'w') as file:
        file.write(cleaned_content)
        logger.info(f"Unused modules removed from {terraform_file}.")
