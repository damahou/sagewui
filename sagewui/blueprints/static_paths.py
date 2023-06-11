# (c) 2015 J Miguel Farto, jmfarto@gmail.com
r'''
Aditional static paths
'''

import os
from pathlib import Path

from flask import Blueprint
from flask import current_app as app
from flask.helpers import send_from_directory

from .. import config as CFG
from ..util.templates import send_static_file

static_paths = Blueprint('static_paths', __name__)


def send_from_path(basepathname, filepath):
    return send_static_file(Path(basepathname) / filepath)


@static_paths.route('/css/<path:filename>')
def css(filename):
    # send_static file secures filename
    return app.send_static_file(os.path.join('sage', 'css', filename))


@static_paths.route('/images/<path:filename>')
@static_paths.route('/favicon.ico', defaults={'filename': 'favicon.ico'})
def images(filename):
    # send_static file secures filename
    return app.send_static_file(os.path.join('sage', 'images', filename))


@static_paths.route('/ext/<path:filename>')
def ext_static_file(filename):
    return send_from_path('ext', filename)


@static_paths.route('/sage/<path:filename>')
def sage_static_file(filename):
    return send_from_path('sage', filename)


@static_paths.route('/sage3d/<path:filename>')
def sage3d_static_file(filename):
    return send_from_path('sage3d', filename)


@static_paths.route('/java/jmol/<path:filename>')
def jmol(filename):
    return send_from_directory(CFG.JMOL_PATH, filename)


@static_paths.route('/jsmol/<path:filename>')
def jsmol(filename):
    if CFG.JSMOL_PATH:
        return send_from_directory(CFG.JSMOL_PATH, filename)
    else:
        return send_from_path('ext/jsmol', filename)


@static_paths.route('/j2s/<path:filename>')
def j2s(filename):
    if CFG.J2S_PATH:
        return send_from_directory(CFG.J2S_PATH, filename)
    else:
        return send_from_path('ext/jsmol/j2s', filename)


@static_paths.route('/threejs/<path:filename>')
def threejs(filename):
    return send_from_directory(CFG.THREEJS_PATH, filename)
