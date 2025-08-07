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
        try:
            key = int(key)
            match = {'que': 'Queue', 'com': 'Combi', 'nor': 'Normal', 'cou': 'Count', 'func': 'Func'}
            elem_type = match[val['type']]
            
            # 안전한 키 접근 - desc 키가 없거나 비어있는 경우 기본값 사용
            description = val.get('desc', f'Element_{key}')
            if not description or description == '':
                description = f'Element_{key}'
            
            print(f"🔧 Creating {elem_type} {key} with desc: '{description}'")
            
            if elem_type == 'Combi':
                pre = val.get('pre', [])
                fol = val.get('fol', [])
                duration = val.get('duration', 1)
                element = c2.Combi(description, _make_list(pre), _make_list(fol), duration)
                
            elif elem_type == 'Normal':
                fol = val.get('fol', [])
                duration = val.get('duration', 1)
                element = c2.Normal(description, _make_list(fol), duration)
                
            elif elem_type == 'Queue':
                length = val.get('length', 0)
                start = val.get('start', False)
                element = c2.Queue(description, length, _check_bool(start))
                
            elif elem_type == 'Count':
                fol = val.get('fol', [])
                quantity = val.get('quantity', 1)
                element = c2.Count(description, _make_list(fol), quantity)
                
            elif elem_type == 'Func':
                fol = val.get('fol', [])
                con = val.get('con', 1)
                element = c2.Func(description, _make_list(fol), con)
                
            else:
                print(f"⚠️ Unknown element type: {elem_type}")
                element = c2.Queue(f"Unknown_{key}", 1)

            command[key] = element
            print(f"✅ Created {elem_type} {key} successfully")
            
        except KeyError as e:
            print(f"❌ Missing key {e} in element {key}: {val}")
            # 기본 Queue 엘리먼트로 대체
            command[key] = c2.Queue(f"Default_{key}", 1)
            
        except Exception as e:
            print(f"❌ Error creating element {key}: {e}")
            print(f"   Element data: {val}")
            # 기본 Queue 엘리먼트로 대체
            command[key] = c2.Queue(f"Error_{key}", 1)

    print(f"🎯 Total elements created: {len(command)}")
    return command
