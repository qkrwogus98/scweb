
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv



db = SQLAlchemy(engine_options={
    # 'connect_args': {"options": "-c timezone=Asia/Seoul"}
})


class SequelizeBase:
    __table_args__ = {'extend_existing': True}

    # Front
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Rear
    createdAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, index=True, default=datetime.utcnow)


def initialize_db_tables(app):
    with app.app_context():
        db.create_all()
