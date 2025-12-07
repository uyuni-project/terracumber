import hcl2
import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def to_hcl(obj, indent_level=0):
    """
    Recursively converts a Python object to an HCL string.
    """
    indent = "  " * indent_level
    if isinstance(obj, dict):
        lines = []
        for key, value in obj.items():
            # Recursively format the value
            formatted_value = to_hcl(value, indent_level + 1)

            # If the value is a dictionary, we format it as a block: key = { ... }
            if isinstance(value, dict):
                lines.append(f"{indent}{key} = {{\n{formatted_value}\n{indent}}}")
            else:
                lines.append(f"{indent}{key} = {formatted_value}")
        return "\n".join(lines)
    elif isinstance(obj, list):
        items = [to_hcl(item, 0) for item in obj]
        return f"[{', '.join(items)}]"
    elif isinstance(obj, str):
        safe_str = obj.replace('"', '\\"')
        return f'"{safe_str}"'
    elif isinstance(obj, bool):
        return str(obj).lower()  # True -> true
    elif obj is None:
        return "null"
    else:
        return str(obj)

def get_default_keep_list(env_config, delete_all):
    """
    Identifies resources to keep based on the delete_all flag.
    Returns a set of keys (strings) to preserve.
    """
    exclusions = ['minion', 'client']
    if delete_all:
        exclusions.extend(['terminal', 'buildhost', 'proxy', 'dhcp_dns', 'monitoring_server'])

    keep_list = set()
    for key in env_config.keys():
        # If the key does NOT contain any of the exclusion words, keep it.
        if all(exclusion not in key for exclusion in exclusions):
            keep_list.add(key)

    logger.info(f"Default resources to keep: {keep_list}")
    return keep_list

def clean_tfvars(tfvars_file, explicit_keep_list, delete_all=False):
    """
    Loads a tfvars file, removes unselected resources, and saves as .tfvars
    """
    logger.info(f"Loading {tfvars_file}...")

    with open(tfvars_file, 'r') as file:
        data = hcl2.load(file)

    if 'ENVIRONMENT_CONFIGURATION' in data:
        env_config = data['ENVIRONMENT_CONFIGURATION']
        defaults = get_default_keep_list(env_config, delete_all)
        final_keep_set = defaults.union(set(explicit_keep_list))
        logger.info(f"Final keep list: {final_keep_set}")
        cleaned_env_config = {
            k: v for k, v in env_config.items()
            if k in final_keep_set
        }
        removed = set(env_config.keys()) - set(cleaned_env_config.keys())
        for r in removed:
            logger.info(f"Removing: {r}")
        data['ENVIRONMENT_CONFIGURATION'] = cleaned_env_config
    else:
        logger.warning("No ENVIRONMENT_CONFIGURATION block found in file.")
    output_file = tfvars_file  # Overwrite original
    hcl_content = to_hcl(data)
    hcl_content = re.sub(r'}\n(\w)', r'}\n\n\1', hcl_content)

    with open(output_file, 'w') as f:
        f.write(hcl_content)
        f.write("\n") # Ensure EOF newline

    logger.info(f"Cleaned configuration saved to: {output_file}")

remove_unselected_tfvars_resources = clean_tfvars