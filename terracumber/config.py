import hcl2

def flatten(value):
    """Flatten complex structures into a dictionary or list."""
    if isinstance(value, dict):
        return {k: flatten(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [flatten(v) for v in value]
    return value

def read_config(path):
    """Return a dictionary with all the variables from a HCL file"""
    config = {}
    with open(path, 'r') as cfg:
        hcl_file = hcl2.load(cfg)

        # Debugging: Print to check the structure
        print(hcl_file)

        if 'variable' in hcl_file:
            variables = hcl_file['variable']

            # Handle list or dict for variables
            if isinstance(variables, dict):
                for key, value in variables.items():
                    try:
                        config[key] = flatten(value['default'])
                    except KeyError:
                        pass
            elif isinstance(variables, list):
                for variable in variables:
                    for key, value in variable.items():
                        try:
                            config[key] = flatten(value['default'])
                        except KeyError:
                            pass

    return config
