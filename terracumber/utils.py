"""Common tools"""

def merge_two_dicts(dict_x, dict_y):
    """Merge two dictionaries
    Credit goes to https://stackoverflow.com/a/26853961
    We use this solution to keep compatibility with python < 3.5
    """
    dict_z = dict_x.copy()   # start with dict_x's keys and values
    dict_z.update(dict_y)    # modifies dict_z with dict_y's keys and values & returns None
    return dict_z
