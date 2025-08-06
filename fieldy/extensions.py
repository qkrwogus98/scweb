# from flask_moment2 import Moment
from flask_login import LoginManager
from flask_wtf import CSRFProtect

from fieldy.models import User

# moment = Moment()
login_manager = LoginManager()
csrf = CSRFProtect()

@login_manager.user_loader
def user_loader(user_id):
    # TODO: cache 하든지..?
    user = User.query.get(user_id)
    if user is None:
        return None
    user.init_config()
    return user
