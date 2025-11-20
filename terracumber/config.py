"""Manage HCL files as configuration files"""
import hcl2


def read_config(path):
    """Return a dictionary with all the variables from a HCL file"""
    config = {}
    with open(path, 'r') as cfg:
        hcl_file = hcl2.load(cfg)
        if not 'variable' in hcl_file.keys():
            return config
        for key, value in hcl_file['variable'].items():
            try:
                config[key] = value['default']
            except KeyError:
                pass
    return config
