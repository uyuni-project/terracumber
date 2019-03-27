# Credit goes to https://stackoverflow.com/a/26853961
# We use this solution to keep compatible with python < 3.5
def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z
