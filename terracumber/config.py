"""Manage HCL files as configuration files"""
import hcl


def read_config(path):
    """Return a dictionary with all the variables from a HCL file"""
    config = {}
    with open(path, 'r') as cfg:
        for key, value in hcl.load(cfg)['variable'].items():
            try:
                config[key] = value['default']
            except KeyError:
                pass
    return config
