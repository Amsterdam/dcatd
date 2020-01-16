def dictionary_vary(a: dict, b: dict, exclude: dict, parent_key: str = None) -> bool:
    '''
    Are two dictionaries different. Compare recursively
    Ignore keys in exclude, context dependen on parent key.
    Compare date values only till 8 characters or on date and not time
    '''
    parent_exclude = exclude.get(parent_key, set())

    if set(a.keys()) - parent_exclude != set(b.keys()) - parent_exclude:
        return True

    for key, value in a.items():
        if key not in parent_exclude:
            if isinstance(value, dict):
                if not isinstance(b[key], dict) or dictionary_vary(value, b[key], exclude, key):
                    return True
            elif isinstance(value, list):
                if not isinstance(b[key], list) or len(value) != len(b[key]):
                    return True
                for i in range(len(value)):
                    if isinstance(value[i], dict):
                        if not isinstance(b[key][i], dict) or dictionary_vary(value[i], b[key][i], exclude, key):
                            return True
                    else:  # We do not have lists of lists
                        if value[i] != b[key][i]:
                            return True
            elif key in ('modified', 'modification_date', 'issued', 'dct:issued'):
                if value[:8] != b[key][:8]:
                    return True
            else:
                if value != b[key]:
                    return True

    return False
