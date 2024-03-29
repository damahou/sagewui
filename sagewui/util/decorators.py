from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import wraps
from threading import Lock

from flask import url_for
from flask import request
from flask import session
from flask import redirect
from flask import g
from flask_babel import gettext

from .. import config as CFG
from .templates import message as message_template

_ = gettext

global_lock = Lock()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            # XXX: Do we have to specify this for the publised
            # worksheets here?
            if request.path.startswith('/home/_sage_/'):
                g.username = CFG.UN_GUEST
                return f(*args, **kwds)
            else:
                return redirect(url_for('base.index', next=request.url))
        else:
            g.username = session['username']
        return f(*args, **kwds)
    return wrapper


def admin_required(f):
    @login_required
    @wraps(f)
    def wrapper(*args, **kwds):
        if not g.notebook.user_manager[g.username].is_admin:
            return message_template(
                _("You do not have permission to access this location"),
                cont=url_for('base.index'),
                username=g.username)
        return f(*args, **kwds)

    return wrapper


def guest_or_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            g.username = CFG.UN_GUEST
        else:
            g.username = session['username']
        return f(*args, **kwds)
    return wrapper


def with_lock(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        with global_lock:
            return f(*args, **kwds)
    return wrapper
