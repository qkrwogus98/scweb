from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, send_file, abort, jsonify, \
    make_response
from flask_login import login_required, current_user
from flask_cors import CORS, cross_origin


from fieldy.database import db
from fieldy.extensions import csrf  # db,
# from fieldy.forms import TaskForm
from fieldy.models import User, Project
from fieldy.utils import make_path, redirect_back

from sqlalchemy import and_, func, extract
from sqlalchemy.orm import joinedload

import os
from dotenv import load_dotenv


bp = Blueprint('main', __name__)
CORS(bp, resources={r'*': {'origins': '*'}})

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

CS_TOKEN = os.getenv('CESIUM_TOKEN')

@bp.route('/')
def index():
    projects = Project.query.order_by(Project.id).all()
    return render_template('index.html', projects=projects)

@bp.route('/new')
def new_project():
    return render_template('new.html',cs_token=CS_TOKEN)

@bp.route('/new/<int:project_id>/delete')
def delete_project(project_id):
    # project = Project.query.get(project_id)
    flash('관리자에게 문의하시기 바랍니다.', 'danger')
    return redirect_back()

@bp.route('/realtime')
def realtime():
    return render_template('realtime.html',cs_token=CS_TOKEN)

@bp.route('/new/<int:project_id>')
def new_project2(project_id):
    return render_template('new2.html', project_id=project_id,cs_token=CS_TOKEN)

@bp.route('/new/<int:project_id>/model')
def new_project3(project_id):
    return render_template('new3.html', project_id=project_id,cs_token=CS_TOKEN)

from urllib.parse import urlencode

@bp.route('/new/<int:project_id>/test')
def new_test(project_id):
    args = request.args.to_dict()
    if args.get('dump'):
        del args['dump']
    encoded = urlencode(args)
    return render_template('test.html', project_id=project_id, encoded=encoded,cs_token=CS_TOKEN)


@bp.route('/new/<int:project_id>/simulate')
def new_simulate(project_id):
    args = request.args.to_dict()
    if args.get('dump'):
        del args['dump']
    encoded = urlencode(args)
    return render_template('simulate.html', project_id=project_id, encoded=encoded, cs_token=CS_TOKEN)

import ciclone2 as c2
from ciclone2 import *
from ciclone2.utils import make_command

@bp.route('/new/<int:project_id>/prod')
@csrf.exempt
def make_prod(project_id):
    my = c2.Model()
    my.debug = True  # set False for brief trace

    if project_id == 1:
        my.add(_make_commands({
            'soil': 20,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 5 * 60,
            'dumping': 40,
            'returning': 240,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 4 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))
    elif project_id == 8:
        my.add(_make_commands({
            'soil': 10,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 17 * 60,
            'dumping': 0.5 * 60,
            'returning': 17 * 60,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 12.5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 10 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))

    my.run()

    return jsonify({
        'productivity': [item for item in my.stats[0]['counter'] if item['id'] == 16][0]['prod_rate'] * 1000
    })


@bp.route('/new/<int:project_id>/json')
@csrf.exempt
def make_json(project_id):
    my = c2.Model()
    my.debug = True  # set False for brief trace

    if project_id == 1:
        my.add(_make_commands({
            'soil': 20,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 5 * 60,
            'dumping': 40,
            'returning': 240,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 4 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))
    elif project_id == 8:
        my.add(_make_commands({
            'soil': 10,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 17 * 60,
            'dumping': 0.5 * 60,
            'returning': 17 * 60,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 12.5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 10 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))

    my.run()
    passive_data = my.envs[0].passive

    now_queue = {}
    result = []

    for k, v in passive_data.items():
        now_queue[k] = 0

    start_time = datetime.fromisoformat('2023-10-17T10:00:00+09:00')

    data = my.envs[0].queues
    for i in range(len(data) - 1):
        start = data[i]['now']
        stop = data[i + 1]['now']
        now_queue[data[i]['id']] = data[i]['val']
        val = copy.copy(now_queue)

        result.append({
            'start': (start_time + timedelta(seconds=start)).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'stop': (start_time + timedelta(seconds=stop)).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'data': val
        })

    return jsonify({
        'queue': {
            'Dump': {'id': 3, 'length': my.command[3]._length, 'name': '트럭'},
            'Excavator': {'id': 2, 'length': my.command[2]._length, 'name': '굴착기'},
            'Dozer': {'id': 9, 'length': my.command[9]._length, 'name': '도저'},
            'Roller': {'id': 13, 'length': my.command[13]._length, 'name': '롤러'},
            '_Soil': {'id': 0, 'length': my.command[0]._length}
        },
        'productivity': [item for item in my.stats[0]['counter'] if item['id'] == 16][0]['prod_rate'] * 1000,
        'data': result
    })

def _make_commands(params):
    return {
        0: c2.Queue('Soil', params['soil']),
        1: c2.Combi('Loading', [0, 2, 3], [2, 4], params['loading']),
        2: c2.Queue('Excavator', params['num_excavator']),
        3: c2.Queue('Dump truck', params['num_dump'], start=True),
        4: c2.Normal('Hauling', 5, params['hauling']),
        5: c2.Normal('Dumping', [6, 16], params['dumping']),
        6: c2.Normal('Returning', 3, params['returning']),

        16: Count('Production of Dump', 14),
        14: c2.Func('Spread Func', 7, params['con_dozer']),
        7: c2.Queue('Spread Q', 0),
        8: c2.Combi('Spread', [7, 9], [9, 15], params['spreading']),
        9: c2.Queue('Dozer', params.get('num_dozer', 1)),

        15: c2.Func('Compact Func', 10, params['con_roller']),
        10: c2.Queue('Spreaded Soil', 0),
        11: c2.Combi('Compact', [10, 13], 12, params['compacting']),
        12: c2.Count('Production', 13),
        13: c2.Queue('Roller', params.get('num_roller', 1))
    }

@bp.route('/new/<int:project_id>/czml')
@csrf.exempt
def get_czml_just_project(project_id):
    my = c2.Model()
    my.debug = True  # set False for brief trace

    if project_id == 1:
        # comm = {
        #     1: c2.Queue('LoaderQ', request.args.get('excavator', 1, type=int)),  # length
        #     2: c2.Combi('Loading', [1, 3], [1, 4], 120),
        #     3: c2.Queue('TruckQ', request.args.get('dump', 3, type=int), start=True),
        #     4: c2.Normal('Hauling', 5, TRI(270, 300, 330)),
        #     5: c2.Normal('Dumping', 6, 40),
        #     6: c2.Count('Production', 7),
        #     7: c2.Normal('Returning', 3, 240),
        # }
        # my.until(Count6=20)

        my.add(_make_commands({
            'soil': 20,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 5 * 60,
            'dumping': 40,
            'returning': 240,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 4 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))

        ex_1 = [0.14223775818238782, -0.42239567554260354, -0.8483727819644872, 0.2856815294204244]  # 0도
        ex_2 = [-0.44034762768430025, 0.06887418502351028, 0.645137567013289, 0.6206027981393011]  # 125도
        ex_pos = [-3082438.9937163005, 4057883.95447715, 3823115.414877715]

    elif project_id == 8:
        my.add(_make_commands({
            'soil': 10,
            'loading': 2 * 60,
            'num_excavator': request.args.get('excavator', 1, type=int),
            'num_dump': request.args.get('dump', 2, type=int),
            'hauling': 17 * 60,
            'dumping': 0.5 * 60,
            'returning': 17 * 60,
            'con_dozer': request.args.get('con_dozer', 3, type=int),
            'spreading': 12.5 * 60,
            'num_dozer': request.args.get('dozer', 1, type=int),
            'con_roller': request.args.get('con_roller', 2, type=int),
            'compacting': 10 * 60,
            'num_roller': request.args.get('roller', 1, type=int)
        }))

        ex_1 = [-0.19803758320250028, -0.39435024799697266, -0.40271755133095016, 0.8019274103022308]  # -90도
        ex_2 = [-0.41889007164413744, -0.13884192180269161, 0.2823272697675524, 0.8517894935802532]  # -180도
        ex_pos = [-3020481.772925505, 4056780.4435730274, 3872883.43287323]

    my.run()

    with open(os.path.join(os.path.dirname(__file__), 'test.json')) as f:
        default = json.load(f)

    start_time = datetime.fromisoformat(default[0]['clock']['currentTime'])

    trace = my.envs[0].data

    project = Project.query.get(project_id)
    paths = json.loads(project.paths)

    entities = {}
    dozer = []
    roller = []
    roller_pos = 0

    complicated = False

    excavator = []  # orientation
    total_time = -1

    last_ex = -1

    if project_id == 8:
        path_return = paths['Truck 길 연장'][::-1] + paths['dump'][::-1] + paths['이동']
        path_haul = path_return[::-1]
    elif project_id == 1:
        path_haul = paths['haul']
        path_return = paths['return']

    for t in trace:
        if t['end'] and t['cnt'] > 10 and not t['closed']:
            num = t['cnt'] % 20
            total_time = max(total_time, t['end'])
            if num not in entities:
                entities[num] = []
            duration = t['end'] - t['start']
            if t['current_desc'] == 'Hauling':
                entities[num].append(make_path(path_haul, start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Returning':
                entities[num].append(make_path(path_return, start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Loading':
                if len(entities[num]) == 0:
                    entities[num].append([
                                             (start_time + timedelta(seconds=t['start'])).strftime('%Y-%m-%dT%H:%M:%S%z')
                                         ] + path_haul[0][0])  # cartesian3 좌표
                if last_ex != t['start']:
                    excavator.extend([t['start']] + ex_1)

                _bucket = request.args.get('bucket', 2, type=int)
                for i in range(_bucket):
                    excavator.extend([t['start'] + (i + 1) * duration / _bucket] + ex_2)
                    excavator.extend([t['start'] + (i + 1) * duration / _bucket + (10 - (_bucket - 1 - i))] + ex_1)
                last_ex = t['end']
            elif t['current_desc'] == 'Dumping':
                pass
            elif t['current_desc'] == 'Spread':
                complicated = True
                dozer.extend(make_path(paths['Dozer and Roller'], start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Compact':
                ppaath = paths['Dozer and Roller'] if roller_pos == 0 else paths['Dozer and Roller'][::-1]
                roller.extend(make_path(ppaath, start_time + timedelta(seconds=t['start']), duration))
                roller_pos ^= 1

    # 초기화
    excavator[:0] = [0.] + ex_1

    import copy

    # generator = UniqueRGBGenerator()
    generator = DistinctColorGenerator(len(entities))

    # DumpTruck
    for k, v in entities.items():
        aa = copy.deepcopy(default[1])
        aa['id'] = f'DumpTruck {k + 1}'
        aa['model']['color']['rgba'] = list(generator.generate()) + [255]
        aa['position']['cartesian'] = [item for sublist in v for item in sublist]
        default.append(aa)

    # Excavator
    aa = copy.deepcopy(default[3])
    aa['id'] = 'Excavator'
    aa['orientation']['epoch'] = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
    aa['orientation']['unitQuaternion'] = excavator
    aa['position']['cartesian'] = ex_pos
    default.append(aa)

    if complicated:
        # Dozer
        aa = copy.deepcopy(default[4])
        aa['id'] = f'Dozer'
        aa['position']['cartesian'] = dozer
        default.append(aa)

        # Roller
        aa = copy.deepcopy(default[5])
        aa['id'] = f'Roller'
        aa['position']['cartesian'] = roller
        default.append(aa)

    # Path
    for x in ('Hauling', 'Returning'):
        aa = copy.deepcopy(default[2])
        data = path_return if x == 'Returning' else path_haul
        aa['id'] = f'{x} Path'
        aa['polyline']['positions']['cartesian'] = [item for sublist in data for item in sublist[0]]
        default.append(aa)

    default[0]['clock']['interval'] = f'{start_time.strftime("%Y-%m-%dT%H:%M:%S%z")}/' \
                                      f'{(start_time + timedelta(seconds=total_time)).strftime("%Y-%m-%dT%H:%M:%S%z")}'

    default = [x for x in default if not x['id'].startswith('_')]

    return jsonify(default)


@bp.route('/new/<int:project_id>/czml2')
@csrf.exempt
def get_czml2_just_project(project_id):
    my = c2.Model()
    my.debug = True

    project = Project.query.get(project_id)
    paths = json.loads(project.paths)
    model = json.loads(project.model)

    model_data = model['model']
    model_data = {int(key): value for key, value in model_data.items()}

    my.add(make_command(model_data))
    my.run()

    with open(os.path.join(os.path.dirname(__file__), 'test.json')) as f:
        default = json.load(f)

    start_time = datetime.fromisoformat(default[0]['clock']['currentTime'])

    trace = my.envs[0].data

    entities = {}
    dozer = []
    roller = []
    roller_pos = 0

    complicated = False

    excavator = []  # orientation
    total_time = -1

    last_ex = -1

    path = dict()
    equipment_ex = None
    ex_orientation = dict()

    for elemId, elem in my.command.items():
        if elem.desc in ('Hauling', 'Returning', 'Spread', 'Compact'):
            path[elem.desc] = eval(model_data[elemId]['pathOption']) \
                if model_data[elemId].get('path') == '_option' else paths.get(model_data[elemId]['path'])

    for key, val in model_data.items():
        if val.get('equipment') == 'excavator':
            equipment_ex = val
            ex_orientation[1] = val['ex_1_orientation']
            ex_orientation[2] = val['ex_2_orientation']

    first_dozer = None
    for t in trace:
        if t['end'] and t['cnt'] > 10 and not t['closed']:
            num = t['cnt'] % 20
            total_time = max(total_time, t['end'])
            if num not in entities:
                entities[num] = []
            duration = t['end'] - t['start']
            if t['current_desc'] == 'Hauling':
                entities[num].append(make_path(path['Hauling'], start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Returning':
                entities[num].append(make_path(path['Returning'], start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Loading':
                if len(entities[num]) == 0:
                    entities[num].append([(start_time + timedelta(seconds=t['start'])).strftime('%Y-%m-%dT%H:%M:%S%z')]
                                         + path['Hauling'][0][0])  # cartesian3 좌표
                if last_ex != t['start']:
                    excavator.extend([t['start']] + ex_orientation[1])

                _bucket = int(equipment_ex.get('bucket', 2))
                for i in range(_bucket):
                    excavator.extend([t['start'] + (i + 1) * duration / _bucket] + ex_orientation[2])
                    excavator.extend([t['start'] + (i + 1) * duration / _bucket + (10 - (_bucket - 1 - i))] + ex_orientation[1])
                last_ex = t['end']
            elif t['current_desc'] == 'Dumping':
                pass
            elif t['current_desc'] == 'Spread':
                complicated = True
                dozer.extend(make_path(path['Spread'], start_time + timedelta(seconds=t['start']), duration))
                if not first_dozer:
                    first_dozer = t['start']
            elif t['current_desc'] == 'Compact':
                _path = path['Compact'] if roller_pos == 0 else path['Compact'][::-1]
                roller.extend(make_path(_path, start_time + timedelta(seconds=t['start']), duration))
                roller_pos ^= 1

    if project_id == 8 or project_id == 16 or project_id == 19:
        path['Compact'] = path['Spread']
        now = first_dozer + 3 * 60
        while now < total_time:
            _path = path['Compact'] if roller_pos == 0 else path['Compact'][::-1]
            roller.extend(make_path(_path, start_time + timedelta(seconds=now), 3 * 60))
            now += 3 * 60
            roller_pos ^= 1

    # 초기화
    excavator[:0] = [0.] + ex_orientation[1]
    if 'Spread' in path:
        dozer[:0] = [start_time.strftime('%Y-%m-%dT%H:%M:%S%z')] + path['Spread'][0][0]
    if 'Compact' in path:
        roller[:0] = [start_time.strftime('%Y-%m-%dT%H:%M:%S%z')] + path['Compact'][0][0]

    import copy

    # generator = UniqueRGBGenerator()
    generator = DistinctColorGenerator(len(entities))

    # DumpTruck
    for k, v in entities.items():
        aa = copy.deepcopy(default[1])
        aa['id'] = f'DumpTruck {k + 1}'
        aa['model']['color']['rgba'] = list(generator.generate()) + [255]
        aa['position']['cartesian'] = [item for sublist in v for item in sublist]
        default.append(aa)

    # Excavator
    aa = copy.deepcopy(default[3])
    aa['id'] = 'Excavator'
    aa['orientation']['epoch'] = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
    aa['orientation']['unitQuaternion'] = excavator
    aa['position']['cartesian'] = equipment_ex['position']
    default.append(aa)

    if complicated:
        # Dozer
        aa = copy.deepcopy(default[4])
        aa['id'] = f'Dozer'
        aa['position']['cartesian'] = dozer
        default.append(aa)

        # Roller
        aa = copy.deepcopy(default[5])
        aa['id'] = f'Roller'
        aa['position']['cartesian'] = roller
        default.append(aa)

    # Path
    for x in ('Hauling', 'Returning'):
        aa = copy.deepcopy(default[2])
        aa['id'] = f'{x} Path'
        aa['polyline']['positions']['cartesian'] = [item for sublist in path[x] for item in sublist[0]]
        default.append(aa)

    default[0]['clock']['interval'] = f'{start_time.strftime("%Y-%m-%dT%H:%M:%S%z")}/' \
                                      f'{(start_time + timedelta(seconds=total_time)).strftime("%Y-%m-%dT%H:%M:%S%z")}'

    default = [x for x in default if not x['id'].startswith('_')]

    return jsonify(default)


@bp.route('/new/<int:project_id>/json2')
@csrf.exempt
def make_json2(project_id):
    my = c2.Model()
    my.debug = True

    project = Project.query.get(project_id)
    model = json.loads(project.model)

    model_data = model['model']
    model_data = {int(key): value for key, value in model_data.items()}

    my.add(make_command(model_data))
    my.run()

    passive_data = my.envs[0].passive

    now_queue = {}
    result = []

    for k, v in passive_data.items():
        now_queue[k] = 0

    start_time = datetime.fromisoformat('2023-10-17T10:00:00+09:00')

    data = my.envs[0].queues
    for i in range(len(data) - 1):
        start = data[i]['now']
        stop = data[i + 1]['now']
        now_queue[data[i]['id']] = data[i]['val']
        val = copy.copy(now_queue)

        result.append({
            'start': (start_time + timedelta(seconds=start)).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'stop': (start_time + timedelta(seconds=stop)).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'data': val
        })

    desired_order = {
        'dump': '트럭',
        'excavator': '굴착기',
        'dozer': '도저',
        'roller': '롤러'
    }
    queue = {
        val['equipment']: {
            'id': key,
            'length': my.command[key]._length,
            'name': desired_order[val['equipment']]
        }
        for key, val in model_data.items()
        if val.get('equipment') in desired_order
    }
    queue['_soil'] = {'id': 0, 'length': my.command[0]._length}
    
    counter = [item for item in my.stats[0]['counter'] if item['desc'] == 'Production of Dump'][0]
    prod_rate = counter['prod_rate']
    productivity = float(model['etc'].get('dump_capacity', 7.89)) * prod_rate * 3600

    price_per_day = 0
    if e := queue.get('dump'):
        price_per_day += float(model['etc'].get('cost_dump', 500_000)) * e['length']
    if e := queue.get('excavator'):
        price_per_day += float(model['etc'].get('cost_excavator', 900_000)) * e['length']
    if e := queue.get('dozer'):
        price_per_day += float(model['etc'].get('cost_dozer', 300_000)) * e['length']
    if e := queue.get('roller'):
        price_per_day += float(model['etc'].get('cost_roller', 300_000)) * e['length']

    return jsonify({
        'queue': queue,
        'productivity': productivity,
        'unitCost': price_per_day / (productivity * 8),
        'avg_interarrival': counter['avg_interarrival'],
        'data': result
    })


@bp.route('/new/<int:project_id>/prod2')
@csrf.exempt
def make_prod2(project_id):
    my = c2.Model()
    my.debug = True  # set False for brief trace

    project = Project.query.get(project_id)
    model = json.loads(project.model)

    model_data = model['model']
    model_data = {int(key): value for key, value in model_data.items()}

    for el in model_data.values():
        if el.get('equipment') == 'dump':
            el['length'] = request.args.get('dump', 2, type=int)

    my.add(make_command(model_data))
    my.run()

    queue = {
        val['equipment']: {
            'id': key,
            'length': my.command[key]._length
        }
        for key, val in model_data.items()
        if val.get('equipment')
    }

    counter = [item for item in my.stats[0]['counter'] if item['desc'] == 'Production of Dump'][0]
    prod_rate = counter['prod_rate']
    productivity = float(model['etc'].get('dump_capacity', 7.89)) * prod_rate * 3600

    price_per_day = 0
    if e := queue.get('dump'):
        price_per_day += float(model['etc'].get('cost_dump', 500_000)) * e['length']
    if e := queue.get('excavator'):
        price_per_day += float(model['etc'].get('cost_excavator', 900_000)) * e['length']
    if e := queue.get('dozer'):
        price_per_day += float(model['etc'].get('cost_dozer', 300_000)) * e['length']
    if e := queue.get('roller'):
        price_per_day += float(model['etc'].get('cost_roller', 300_000)) * e['length']

    return jsonify({
        'productivity': productivity,
        'unitCost': price_per_day / (productivity * 8),
        'avg_interarrival': counter['avg_interarrival']
    })



import json
from datetime import datetime, timedelta, timezone
from pprint import pprint

from .data import hauling, hauling2, returning, returning2
from .color import UniqueRGBGenerator, DistinctColorGenerator

import numpy as np

# from ciclone import *

@bp.route('/czml_test')
@csrf.exempt
def czml():

    my = Model()

    my.debug = True  # set False for brief trace

    comm: Dict[Union[int, str], Element] = {
        1: Queue('LoaderQ', 1),  # length
        2: Combi('Load', [1, 3], [1, 4], 120),
        3: Queue('TruckQ', 5, start=True),
        4: Normal('Haul', 5, TRI(270, 300, 330)),
        5: Normal('Dump', 6, 40),
        6: Count('Production', 7),
        7: Normal('Return', 3, 240),
    }

    my.add(comm)
    # my.until(time=100)
    my.until(Count6=20)

    my.run()

    # def compute_distance(pos1, pos2):
    #     x1, y1 = latlon_to_xy(*reversed(pos1))
    #     x2, y2 = latlon_to_xy(*reversed(pos2))
    #     return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def compute_distance2(pos1, pos2):
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def make_path(paths, start, duration):
        distances = [compute_distance2(paths[i][0], paths[i - 1][0]) for i in range(1, len(paths))]
        total_length = sum(distances)
        distances.append(0)

        current_time = start
        positions = []
        polyline_positions = []
        for pos, dist in zip(paths, distances):
            formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S%z')
            positions.extend([formatted_time] + pos[0])
            polyline_positions.extend(pos[0])
            time = dist / total_length * duration
            current_time += timedelta(seconds=time)

        return positions  # , polyline_positions

    with open(os.path.join(os.path.dirname(__file__), 'test.json')) as f:
        default = json.load(f)

    start_time = datetime.fromisoformat(default[0]['clock']['currentTime'])
    current_time = start_time

    trace = my._trace

    entities = {}
    total_time = -1
    for t in trace:
        if t['type'] == 'trace' and t['start'] != -1 and t['entity'] > 10000:
            num = t['entity'] // 1000 % 10
            total_time = max(total_time, t['end'])
            if num not in entities:
                entities[num] = []
            duration = t['end'] - t['start']
            if t['current_desc'] == 'Haul':
                entities[num].append(make_path(hauling2, start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Return':
                entities[num].append(make_path(returning2, start_time + timedelta(seconds=t['start']), duration))
            elif t['current_desc'] == 'Load':
                pass
            elif t['current_desc'] == 'Dump':
                pass

    import copy

    # generator = UniqueRGBGenerator()
    generator = DistinctColorGenerator(len(entities))

    참조 = default[1]
    for k, v in entities.items():
        aa = copy.deepcopy(참조)
        aa['id'] = f'DumpTruck{k + 1}'
        aa['model']['color']['rgba'] = list(generator.generate()) + [255]
        aa['position']['cartesian'] = [item for sublist in v for item in sublist]
        default.append(aa)

    참조2 = default[2]
    for x in ('Haul', 'Return'):
        aa = copy.deepcopy(참조2)
        if x == 'Haul':
            data = hauling2
        elif x == 'Return':
            data = returning2
        aa['id'] = f'{x}Path'
        aa['polyline']['positions']['cartesian'] = [item for sublist in data for item in sublist[0]]
        default.append(aa)

    default[0]['clock']['interval'] = f'{start_time.strftime("%Y-%m-%dT%H:%M:%S%z")}/' \
                                      f'{(start_time + timedelta(seconds=total_time)).strftime("%Y-%m-%dT%H:%M:%S%z")}'

    default = [x for x in default if not x['id'].startswith('_')]

    return jsonify(default)



@bp.route('/czml2')
@csrf.exempt
def czml2():
    my = c2.Model()

    my.debug = True  # set False for brief trace

    comm = {
        0: c2.Queue('Soil', 100),
        1: c2.Combi('Loading', [0, 2, 3], [2, 4], 2 * 60),
        2: c2.Queue('Excavator', 1),
        3: c2.Queue('Dump truck', 4, start=True),
        4: c2.Normal('Hauling', 5, 17 * 60),
        5: c2.Normal('Dumping', [6, 14], 0.5 * 60),
        6: c2.Normal('Returning', 3, 17 * 60),

        14: c2.Func('Spread Func', 7, 3),
        7: c2.Queue('Spread Q', 0),
        8: c2.Combi('Spread', [7, 9], [9, 15], 12.5 * 60),
        9: c2.Queue('Dozer', 1),

        15: c2.Func('Compact Func', 10, 2),
        10: c2.Queue('Spreaded Soil', 0),
        11: c2.Combi('Compact', [10, 13], 12, 10 * 60),
        12: c2.Count('Production', 13),
        13: c2.Queue('Roller', 1)
    }

    my.add(comm)

    my.run()

    def compute_distance2(pos1, pos2):
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    def make_path(paths, start, duration):
        distances = [compute_distance2(paths[i][0], paths[i - 1][0]) for i in range(1, len(paths))]
        total_length = sum(distances)
        distances.append(0)

        current_time = start
        positions = []
        polyline_positions = []
        for pos, dist in zip(paths, distances):
            formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S%z')
            positions.extend([formatted_time] + pos[0])
            polyline_positions.extend(pos[0])
            time = dist / total_length * duration
            current_time += timedelta(seconds=time)

        return positions  # , polyline_positions

    with open(os.path.join(os.path.dirname(__file__), 'test.json')) as f:
        default = json.load(f)

    start_time = datetime.fromisoformat(default[0]['clock']['currentTime'])

    trace = my.envs[0].data
    return jsonify(trace)

    # project = Project.query.get(8)
    # paths = json.loads(project.paths)

    # entities = {}
    # dozer = []
    # roller = []
    # roller_pos = 0

    # excavator = []  # orientation
    # total_time = -1

    # ex_1 = [-0.19803758320250028, -0.39435024799697266, -0.40271755133095016, 0.8019274103022308]  # -90도
    # ex_2 = [-0.41889007164413744, -0.13884192180269161, 0.2823272697675524, 0.8517894935802532]  # -180도
    # last_ex = -1

    # path_haul = paths['Truck 길 연장'][::-1] + paths['dump'][::-1] + paths['이동']

    # for t in trace:
    #     if t['end'] and t['cnt'] > 10 and not t['closed']:
    #         num = t['cnt'] % 20
    #         total_time = max(total_time, t['end'])
    #         if num not in entities:
    #             entities[num] = []
    #         duration = t['end'] - t['start']
    #         if t['current_desc'] == 'Hauling':
    #             entities[num].append(make_path(path_haul[::-1], start_time + timedelta(seconds=t['start']), duration))
    #         elif t['current_desc'] == 'Returning':
    #             entities[num].append(make_path(path_haul, start_time + timedelta(seconds=t['start']), duration))
    #         elif t['current_desc'] == 'Loading':
    #             if len(entities[num]) == 0:
    #                 entities[num].append([
    #                                          (start_time + timedelta(seconds=t['start'])).strftime('%Y-%m-%dT%H:%M:%S%z')
    #                                      ] + path_haul[::-1][0][0])  # cartesian3 좌표
    #             if last_ex != t['start']:
    #                 excavator.extend([t['start']] + ex_1)
    #             excavator.extend([t['end']] + ex_2)
    #             excavator.extend([t['end']+5] + ex_1)
    #             last_ex = t['end']
    #         elif t['current_desc'] == 'Dumping':
    #             pass
    #         elif t['current_desc'] == 'Spread':
    #             dozer.extend(make_path(paths['Dozer and Roller'], start_time + timedelta(seconds=t['start']), duration))
    #         elif t['current_desc'] == 'Compact':
    #             ppaath = paths['Dozer and Roller'] if roller_pos == 0 else paths['Dozer and Roller'][::-1]
    #             roller.extend(make_path(ppaath, start_time + timedelta(seconds=t['start']), duration))
    #             roller_pos ^= 1


    # # 초기화
    # excavator[:0] = [0] + ex_1

    # import copy

    # # generator = UniqueRGBGenerator()
    # generator = DistinctColorGenerator(len(entities))

    # 참조 = default[1]
    # for k, v in entities.items():
    #     aa = copy.deepcopy(참조)
    #     aa['id'] = f'DumpTruck{k + 1}'
    #     aa['model']['color']['rgba'] = list(generator.generate()) + [255]
    #     aa['position']['cartesian'] = [item for sublist in v for item in sublist]
    #     default.append(aa)

    # 참조3 = default[3]
    # aa = copy.deepcopy(참조3)
    # aa['id'] = 'Excavator'
    # aa['orientation']['epoch'] = start_time.strftime("%Y-%m-%dT%H:%M:%S%z")
    # aa['orientation']['unitQuaternion'] = excavator
    # default.append(aa)

    # 참조4 = default[4]
    # aa = copy.deepcopy(참조4)
    # aa['id'] = f'Dozer'
    # aa['position']['cartesian'] = dozer
    # default.append(aa)

    # 참조5 = default[5]
    # aa = copy.deepcopy(참조5)
    # aa['id'] = f'Roller'
    # aa['position']['cartesian'] = roller
    # default.append(aa)

    # 참조2 = default[2]
    # for x in ('Haul', 'Return'):
    #     aa = copy.deepcopy(참조2)
    #     if x == 'Haul':
    #         data = path_haul[::-1]
    #     elif x == 'Return':
    #         data = path_haul
    #     aa['id'] = f'{x}Path'
    #     aa['polyline']['positions']['cartesian'] = [item for sublist in data for item in sublist[0]]
    #     default.append(aa)

    # default[0]['clock']['interval'] = f'{start_time.strftime("%Y-%m-%dT%H:%M:%S%z")}/' \
    #                                   f'{(start_time + timedelta(seconds=total_time)).strftime("%Y-%m-%dT%H:%M:%S%z")}'

    # default = [x for x in default if not x['id'].startswith('_')]

    # return jsonify(default)
