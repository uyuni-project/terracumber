import hcl

def read_config(path):
    config = {}
    with open(path, 'r') as f:
        for k,v in hcl.load(f)['variable'].items():
            try:
                config[k] = v['default']
            except KeyError:
                pass
    return(config)
