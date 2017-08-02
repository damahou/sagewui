#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mimetypes
import time

from flask import Blueprint
from flask import url_for
from flask import request
from flask import session
from flask import redirect
from flask import g
from flask import make_response
from flask import current_app
from flask_babel import gettext

from ..config import UAT_USER
from ..config import UN_ADMIN
from ..config import UN_GUEST
from ..util.templates import DynamicJs

from ..util.auth import challenge
from ..util.decorators import login_required
from ..util.decorators import guest_or_login_required
from ..util.decorators import with_lock
from ..util.templates import render_template
from ..util.text import is_valid_email
from ..util.text import is_valid_username
from ..util.text import trunc_invalid_username_chars
from .worksheet import url_for_worksheet

base = Blueprint('base', __name__)
# Globals
mimetypes.add_type('text/plain', '.jmol')

#############
# Main Page #
#############


@base.route('/')
def index():
    if 'username' in session:
        # If there is a next request use that.  See issue #76
        if 'next' in request.args:
            response = redirect(request.values.get('next', ''))
            return response
        response = redirect(
            url_for('worksheet_listing.home', username=session['username']))
        if 'remember' in request.args:
            response.set_cookie('nb_session_%s' % g.notebook.port,
                                expires=(time.time() + 60 * 60 * 24 * 14))
        else:
            response.set_cookie('nb_session_%s' % g.notebook.port)
        response.set_cookie('cookie_test_%s' % g.notebook.port, expires=1)
        return response

    if (current_app.startup_token is not None and
            'startup_token' in request.args):
        if request.args['startup_token'] == current_app.startup_token:
            g.username = session['username'] = UN_ADMIN
            session.modified = True
            current_app.startup_token = None
            return redirect(url_for('base.index'))

    return redirect(url_for('authentication.login'))

######################
# Dynamic Javascript #
######################

dynamic_javascript = DynamicJs()


@base.route('/javascript/dynamic/notebook_dynamic.js')
def dynamic_js():
    data, datahash = dynamic_javascript.javascript
    return render_js(data, datahash)


@base.route('/javascript/dynamic/localization.js')
def localization_js():
    data, datahash = dynamic_javascript.localization
    return render_js(data, datahash)


@base.route('/javascript/dynamic/mathjax_sage.js')
def mathjax_js():
    data, datahash = dynamic_javascript.mathjax
    return render_js(data, datahash)


@base.route('/javascript/dynamic/keyboard/<browser_os>')
def keyboard_js(browser_os):
    data, datahash = dynamic_javascript.keyboard(browser_os)
    return render_js(data, datahash)


def render_js(data, datahash):
    if request.environ.get('HTTP_IF_NONE_MATCH', None) == datahash:
        response = make_response('', 304)
    else:
        response = make_response(data)
        response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
        response.headers['Etag'] = datahash
    return response

###########
# History #
###########


@base.route('/history')
@login_required
def history():
    return render_template(
        'html/history.html', username=g.username,
        text=g.notebook.user_history_text(g.username), actions=False)


@base.route('/live_history')
@login_required
def live_history():
    W = g.notebook.create_wst_from_history(
        gettext('Log'), g.username, 100)
    return redirect(url_for_worksheet(W))
