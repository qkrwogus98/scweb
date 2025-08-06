from datetime import datetime, timedelta, timezone
import random

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

from dataclasses import dataclass

from fieldy.database import db, SequelizeBase


class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    # salt = db.Column(db.String)
    firstName = db.Column('first_name', db.String)
    lastName = db.Column('last_name', db.String)
    team = db.Column(db.String)
    phone = db.Column(db.String)
    token = db.Column(db.String)
    acl = db.Column(db.Integer, default=0)
    set_config = db.Column('config', db.Text)
    createdAt = db.Column(db.DateTime(True), index=True, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime(True), index=True, default=datetime.utcnow)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        _len = random.randint(20, 30)
        self.password = generate_password_hash(password, salt_length=_len)

    def validate_password(self, password):
        return check_password_hash(self.password, password)

    def init_config(self):
        self.config: dict = json.loads(self.set_config or '{}')  # noqa

    def get_timezone(self):
        hour = self.config.get('tz', +9)
        return timezone(timedelta(hours=hour))


@dataclass
class Project(db.Model):  # , SequelizeBase):
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name: str = db.Column(db.String)
    area: str = db.Column(db.String)  # 공구

    pos1: str = db.Column(db.String, info={'json': True})  # Cartesian3 + HPR
    pos2: str = db.Column(db.String, info={'json': True})  # Cartesian3 + HPR
    pos3: str = db.Column(db.String, info={'json': True})

    tileset: str = db.Column(db.String)

    paths: str = db.Column(db.Text, info={'json': True})
    model: str = db.Column(db.Text, info={'json': True})

    createdAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)


@dataclass
class Model(db.Model):  # , SequelizeBase):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    name = db.Column(db.String)

    data = db.Column(db.Text, info={'json': True})

    createdAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    project = db.relationship('Project')


@dataclass
class Simulation(db.Model):  # , SequelizeBase):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

    input = db.Column(db.Text)
    output = db.Column(db.Text)
    etc = db.Column(db.Text)

    createdAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    model = db.relationship('Model')
    project = db.relationship('Project')


class Device(db.Model, SequelizeBase):
    sessionID = db.Column(db.String(16), unique=True)
    type = db.Column(db.String)
    model = db.Column(db.String)
    name = db.Column(db.String)
    isOn = db.Column(db.Boolean)
    isRunning = db.Column(db.Boolean)
    battery = db.Column(db.Integer)


class Position(db.Model, SequelizeBase):
    sessionID = db.Column(db.String(16))
    time = db.Column(db.DateTime(True))
    timestamp = db.Column(db.Integer)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    alt = db.Column(db.Float)
    heading = db.Column(db.Float)
    horizontalAccuracy = db.Column('hz_accuracy', db.Float)
    verticalAccuracy = db.Column('vt_accuracy', db.Float)
    headingAccuracy = db.Column('hd_accuracy', db.Float)
    speed = db.Column(db.Float)
    note1 = db.Column(db.String)
    note2 = db.Column(db.String)


class Sensor(db.Model, SequelizeBase):
    sessionID = db.Column(db.String(16))
    time = db.Column(db.DateTime(True))
    timestamp = db.Column(db.Float)
    Gravity_X = db.Column(db.Float)
    Gravity_Y = db.Column(db.Float)
    Gravity_Z = db.Column(db.Float)
    LinearAcceleration_X = db.Column(db.Float)
    LinearAcceleration_Y = db.Column(db.Float)
    LinearAcceleration_Z = db.Column(db.Float)
    Gyroscope_X = db.Column(db.Float)
    Gyroscope_Y = db.Column(db.Float)
    Gyroscope_Z = db.Column(db.Float)
    Height = db.Column(db.Float)
    Magnetometer_X = db.Column(db.Float)
    Magnetometer_Y = db.Column(db.Float)
    Magnetometer_Z = db.Column(db.Float)
    Orientation_Azimuth = db.Column(db.Float)
    Orientation_Pitch = db.Column(db.Float)
    Orientation_Roll = db.Column(db.Float)
    Orientation_Yaw = db.Column(db.Float)
    Acceleration_X = db.Column(db.Float)
    Acceleration_Y = db.Column(db.Float)
    Acceleration_Z = db.Column(db.Float)
    Euler_R = db.Column(db.Float)
    Euler_P = db.Column(db.Float)
    Euler_Y = db.Column(db.Float)
    Temperature = db.Column(db.Float)


class Log(db.Model, SequelizeBase):
    __tablename__ = 'logs'

    sessionID = db.Column(db.String(16))
    time = db.Column(db.DateTime(True), default=datetime.utcnow)
    type = db.Column(db.Integer)
    msg = db.Column(db.String)


class Station(db.Model, SequelizeBase):
    name = db.Column(db.String)
    name2 = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    transX = db.Column('trans_x', db.Float)
    transZ = db.Column('trans_z', db.Float)
    nation = db.Column(db.String, default='kr')


