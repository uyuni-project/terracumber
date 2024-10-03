"""Manage HCL files as configuration files"""
import hcl2

def read_config(path):
    """Return a dictionary with all the variables from a HCL file"""
    config = {}
    with open(path, 'r') as cfg:
        hcl_file = hcl2.load(cfg)

        # Debugging the structure of hcl_file
        print(hcl_file)  # Print to check the structure

        if 'variable' not in hcl_file:
            return config

        # Ensure 'variable' is a dictionary before accessing its items
        if isinstance(hcl_file['variable'], dict):
            for key, value in hcl_file['variable'].items():
                try:
                    config[key] = value['default']
                except KeyError:
                    pass
        else:
            print("Unexpected format for 'variable':", type(hcl_file['variable']))

    return config

