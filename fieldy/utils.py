from datetime import datetime, timedelta, timezone
try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin

from flask import request, redirect, url_for, current_app

import requests
from phpserialize import unserialize

import json, uuid

# from flask_login import current_user  # LocalProxy

import numpy as np

def make_path(paths, start, duration):
    paths = np.array([path[0] for path in paths])
    distances = np.linalg.norm(paths[1:] - paths[:-1], axis=1)
    total_length = np.sum(distances)

    times = np.zeros_like(distances)
    if total_length != 0:
        times = distances / total_length * duration
    times = np.concatenate(([0], times))

    times_cumulative = np.cumsum(times)
    formatted_times = [(start + timedelta(seconds=t)).strftime('%Y-%m-%dT%H:%M:%S%z') for t in times_cumulative]

    positions = []
    for formatted_time, pos in zip(formatted_times, paths):
        positions.extend([formatted_time] + list(pos))

    return positions

'''
def _compute_distance(pos1, pos2):
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


def make_path(paths, start, duration):
    distances = [_compute_distance(paths[i][0], paths[i - 1][0]) for i in range(1, len(paths))]
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
'''

KST = timezone(timedelta(hours=+9))

tz_db = {
    'Asia/Seoul': +9,
    'America/Chicago': -6,
    'Etc/UTC': 0,
    'Pacific/Guam': +10,
    'Pacific/Auckland': +12,
}


def tzinfo(hour):
    return timezone(timedelta(hours=hour))


# TODO: parameter들 확인해주기!
def str_to_date(date: str, hour=0, minute=0, tz: timezone = KST):
    return datetime.strptime(f"{date} {hour}:{minute:02}", '%Y-%m-%d %H:%M').replace(tzinfo=tz)


def get_sms_remaining() -> int:
    """
    남은 문자 개수

    :return:
    """
    response = requests.post('http://sms.phps.kr/lib/send.sms',
                             data={'adminuser': 'appletekbiz', 'authkey': 'P!SHOV8X#A', 'type': 'view'},
                             headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': ''},
                             # verify=True
                             )
    return int(unserialize(response.content)[b'curcount'])


def send_sms(phone: str, msg: str) -> bool:
    """

    :param phone:
    :param msg:
    :return:
    """
    msg = msg.encode('euc-kr')
    response = requests.post('http://sms.phps.kr/lib/send.sms',
                             data={'adminuser': 'appletekbiz', 'authkey': 'P!SHOV8X#A', 'phone': phone, 'name': '', 'name2': '',
                                    'rphone': '010-2103-8000', 'msg': '', 'sms': msg, 'date': '0', 'ip': '20.214.252.181'},
                             headers={'Accept': '', 'User-Agent': 'PHP Script'}
                             )
    return unserialize(response.content)[b'status'].decode() == 'success'


def _is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default='panel.index', **kwargs):
    # TODO: Not working correctly
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if _is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


def is_active(*endpoints):
    return 'secondary' if request.url_rule.endpoint in endpoints else 'white'


# timestamp_to_datetime = lambda x: datetime.fromtimestamp(int(request.form.get(x))) if request.form.get(x) else None

