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

:param maintf_content: Content of the main.tf file.
:param tf_resources_to_delete: List that can include 'proxy', 'monitoring', and 'retail' that will force to delete those modules.
:return: List of default module names to keep.
"""
def get_default_modules(maintf_content, tf_resources_to_delete):
    module_names = re.findall(r'module\s+"([^"]+)"', maintf_content)
    exclusions = ['minion', 'client']

    if tf_resources_to_delete:
        if 'retail' in tf_resources_to_delete:
            exclusions.extend(['terminal', 'buildhost'])
        if 'proxy' in tf_resources_to_delete:
            exclusions.append('proxy')
        if 'monitoring-server' in tf_resources_to_delete:
            exclusions.append('monitoring-server')

    filtered_module_names = [name for name in module_names if all(exclusion not in name for exclusion in exclusions)]

    logger.info(f"Default modules are {filtered_module_names}")
    return filtered_module_names

"""
Check for any resource in the line with exact match within '.'

line - A configuration line from the controller
tf_resources_to_keep - List of resources to keep
"""
def contains_resource_name(line, tf_resources_to_keep):
    return any(re.search(rf'\.{re.escape(resource)}\.', line) for resource in tf_resources_to_keep)

"""
Filters configuration lines in the controller module to retain only the configurations
for the resouces that should be kept. Also ensures that the output module is not deleted
(identified by having 'configuration' in the title). Removes workaround lines for clarity.

maintf_content - Content of the main.tf file
tf_resources_to_keep - List of resources to keep
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
Removes modules and controller references from resources not in the resources to keep list.
Removes comments upside modules from main.tf.

maintf_file - Path to the main.tf file
tf_resources_to_keep - List of resources to keep
tf_resources_to_delete - List of resources to remove ( can only be proxy, monitoring-server and retail)
"""
def remove_unselected_tf_resources(maintf_file, tf_resources_to_keep, tf_resources_to_delete):
    with open(maintf_file, 'r') as file:
        raw_data = file.read()
#     filtered_lines = [line for line in raw_data if not line.lstrip().startswith("//")]
    # Regex to match lines that start with "//" followed by optional spaces
    pattern = re.compile(r'^\s*//')

    # Filter out lines that match the pattern
    filtered_lines = [line for line in lines if not pattern.match(raw_data)]
#     for line in raw_data:
#         if not line.startswith("//"):
#             filtered_lines = line
#         else:
#             logger.info(f"Remove comment line : {line}")
    data = ''.join(filtered_lines)
    logger.info(f"Remove comments : {data}")
    modules = data.split("module ")

    tf_resources_to_keep.extend(get_default_modules(data, tf_resources_to_delete))
    logger.info(f"Resources to keep {tf_resources_to_keep}.")

    for module in modules[1:]:
        module_name = module.split('"')[1]
        if module_name not in tf_resources_to_keep :
            logger.info(f"Removing minion {module_name} from main.tf")
            data = data.replace("module " + module, '')
        elif module_name == 'controller':
            data = data.replace(module, filter_module_references(module, tf_resources_to_keep))
    cleaned_content = re.sub(r'\n{3,}', '\n\n', data)
    with open(maintf_file, 'w') as file:
        file.write(cleaned_content)
        logger.info(f"Unused modules removed from {maintf_file}.")
