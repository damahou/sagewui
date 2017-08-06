# (c) 2015 J Miguel Farto, jmfarto@gmail.com
r'''
Aditional static paths
'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from flask import Blueprint
from flask import current_app as app
from flask.helpers import send_from_directory

from ..config import JMOL_PATH
from ..config import JSMOL_PATH
from ..config import J2S_PATH
from ..config import THREEJS_PATH


static_paths = Blueprint('static_paths', __name__)


@static_paths.route('/css/<path:filename>')
def css(filename):
    # send_static file secures filename
    return app.send_static_file(os.path.join('sage', 'css', filename))


@static_paths.route('/images/<path:filename>')
@static_paths.route('/favicon.ico', defaults={'filename': 'favicon.ico'})
def images(filename):
    # send_static file secures filename
    return app.send_static_file(os.path.join('sage', 'images', filename))


@static_paths.route('/javascript/<path:filename>')
@static_paths.route('/java/<path:filename>')
def static_file(filename):
    return app.send_static_file(filename)


@static_paths.route('/java/jmol/<path:filename>')
def jmol(filename):
    return send_from_directory(JMOL_PATH, filename)


@static_paths.route('/jsmol/<path:filename>')
def jsmol(filename):
    return send_from_directory(JSMOL_PATH, filename)


@static_paths.route('/j2s/<path:filename>')
def j2s(filename):
    return send_from_directory(J2S_PATH, filename)


@static_paths.route('/threejs/<path:filename>')
def threejs(filename):
    return send_from_directory(THREEJS_PATH, filename)
