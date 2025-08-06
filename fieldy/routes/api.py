import json

from flask import Blueprint, render_template, request, Response, redirect, url_for, flash, send_file, abort, jsonify, \
    make_response
from flask_login import login_required, current_user

from fieldy.database import db
from fieldy.extensions import csrf  # db,
# from fieldy.forms import TaskForm
from fieldy.models import User, Project

from datetime import datetime

from sqlalchemy import and_, func, extract, inspect
from sqlalchemy.orm import joinedload
import requests
import os
import logging


bp = Blueprint('api_v0', __name__)
csrf.exempt(bp)


@bp.route('/')
def index():
    return jsonify('Hello, world!')

@bp.get('/projects')
def get_projects():
    projects = Project.query.all()
    return jsonify(projects)

@bp.post('/projects')
def post_project():
    attrs = ['name', 'pos1', 'pos2', 'pos3', 'tileset', 'paths']
    data = {attr: request.json.get(attr) for attr in attrs}

    # Convert pos1 to JSON string, if it exists
    if data['pos1']:
        data['pos1'] = json.dumps(data['pos1'])

    # Create a new Project instance with the data
    new = Project(**data)

    # Add the new project to the database session
    db.session.add(new)

    db.session.commit()
    # Return a success response
    return jsonify({'status': 'ok', 'id': new.id}), 201  # 201 Created


@bp.get('/projects/<int:project_id>')
def get_project(project_id):
    project = Project.query.get(project_id)
    for column in project.__table__.columns:
        if column.info.get('json'):
            setattr(project, column.name, json.loads(
                getattr(project, column.name) or '{}'
            ))
    return jsonify(project)

@bp.put('/projects/<int:project_id>')
def update_project(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'status': 'no'})

    attrs = ['name', 'pos1', 'pos2', 'pos3', 'tileset', 'paths', 'model']
    for attr in attrs:
        if value := request.json.get(attr):
            if attr in ('pos1', 'pos2', 'pos3', 'paths', 'model'):
                value = json.dumps(value)
            setattr(project, attr, value)

    project.updatedAt = datetime.now()
    db.session.commit()
    return jsonify({'status': 'ok'})

@bp.get('/projects/<int:project_id>/paths')
def get_project_paths(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'status': 'no'})

    paths = json.dumps(project.paths)
    project.updatedAt = datetime.now()
    db.session.commit()
    return jsonify({'status': 'ok'})

@bp.get('/search/address')
def search_address():
    res = requests.get('https://dapi.kakao.com/v2/local/search/address.json', {
        'analyze_type': 'similar',
        'query': request.args.get('query'),
        'size': 10
    }, headers={"Authorization": "KakaoAK 10b38351b91b00d67c2067c1f29ddd50"})
    return res.json()
