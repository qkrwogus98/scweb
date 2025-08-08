import ciclone2 as c2

def _make_list(value):
    if isinstance(value, int):
        return value
    elif ',' not in value:
        return int(value)
    else:
        return [int(x) for x in value.split(",")]

def _check_bool(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.capitalize()
    else:
        return False

def make_command(model_data):
    command = dict()

    for key, val in model_data.items():
        key = int(key)
        match = {'que': 'Queue', 'com': 'Combi', 'nor': 'Normal', 'cou': 'Count', 'func': 'Func'}
        elem_type = match[val['type']]
        if elem_type == 'Combi':
            element = eval(
                f'c2.{elem_type}("{val["desc"]}", {_make_list(val["pre"])}, {_make_list(val["fol"])}, {val["duration"]})')
        elif elem_type == 'Normal':
            element = eval(f'c2.{elem_type}("{val["desc"]}", {_make_list(val["fol"])}, {val["duration"]})')
        elif elem_type == 'Queue':
            element = eval(f'c2.{elem_type}("{val["desc"]}", {val["length"]}, {_check_bool(val.get("start"))})')
        elif elem_type == 'Count':
            element = eval(f'c2.{elem_type}("{val["desc"]}", {_make_list(val["fol"])}, {val.get("quantity", 1)})')
            # _until = f'model.until(Count{key}={val["until"]})'
        elif elem_type == 'Func':
            element = eval(f'c2.{elem_type}("{val["desc"]}", {_make_list(val["fol"])}, {val["con"]})')

        command[key] = element

    return command
