"""Manage HCL files as configuration files"""
import hcl2

def read_config(path):
    """Return a dictionary with all the variables from a HCL file"""
    config = {}
    with open(path, 'r') as cfg:
        hcl_data = hcl2.load(cfg)
        if 'variable' not in hcl_data.keys():
            return config
        for var_block in hcl_data['variable']:
            for var_name, var_attributes in var_block.items():
                try:
                    # Directly access the 'default' key in the attributes dictionary
                    value = var_attributes['default']
                    if value is None:
                        config[var_name] = 'null'
                    else:
                        config[var_name] = value
                except KeyError:
                    # Pass if 'default' is not defined (e.g., for SCC_USER)
                    pass
    return config
