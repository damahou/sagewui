# -*- coding: utf-8 -*
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str

import os

from flask import Flask
from flask import g
from flask import url_for
from flask_autoindex import AutoIndex
from flask_babel import Babel
from flask_babel import gettext
from flask_themes2 import Themes
from flask_themes2 import theme_paths_loader

from . import config as CFG
from .util.decorators import guest_or_login_required
from .util.templates import css_escape
from .util.templates import convert_time_to_string
from .util.templates import DynamicJs
from .util.templates import prettify_time_ago
from .util.templates import number_of_rows
from .util.templates import message as message_template
from .util.templates import render_template
from .util.templates import join_max

from .blueprints.admin import admin
from .blueprints.authentication import authentication
from .blueprints.base import base
from .blueprints.doc import doc
from .blueprints.static_paths import static_paths
from .blueprints.worksheet_listing import worksheet_listing
from .blueprints.worksheet import worksheet


def create_app(notebook, startup_token=None, debug=False):
    """
    This is the main method to create a running notebook. This is
    called from the process spawned in run.py
    """
    # Create app
    app = Flask(__name__)
    app.startup_token = startup_token

    app.config.update({
        'SESSION_COOKIE_HTTPONLY': False,
        'PROPAGATE_EXCEPTIONS': debug,
        'DEBUG': debug,
        'SECRET_KEY': os.urandom(24),
        })

    dynamic_javascript = DynamicJs(debug=debug)

    @app.before_request
    def set_notebook_object():
        g.notebook = notebook
        g.dynamic_javascript = dynamic_javascript

    # Handles all uncaught exceptions if not debug activated
    @app.errorhandler(500)
    def log_exception(error):
        return message_template(
            gettext('''500: Internal server error.'''),
            username=getattr(g, 'username', CFG.UAT_GUEST)), 500

    # Template globals
    app.add_template_global(url_for)
    # Template filters
    app.add_template_filter(css_escape)
    app.add_template_filter(number_of_rows)
    app.add_template_filter(convert_time_to_string)
    app.add_template_filter(prettify_time_ago)
    app.add_template_filter(join_max)
    app.add_template_filter(max)
    app.add_template_filter(lambda x: repr(str(x)), name='repr_str')

    # Default template context
    @app.context_processor
    def default_template_context():
        return {'sitename': gettext('Sage Notebook'),
                'sage_version': CFG.SAGE_VERSION,
                'MATHJAX': CFG.MATHJAX,
                'JEDITABLE_TINYMCE': CFG.JEDITABLE_TINYMCE,
                'conf': notebook.conf}

    # Register the Blueprints
    app.register_blueprint(admin)
    app.register_blueprint(authentication)
    app.register_blueprint(base)
    app.register_blueprint(doc, url_prefix='/doc')
    app.register_blueprint(static_paths)
    app.register_blueprint(worksheet)
    app.register_blueprint(worksheet_listing)

    # # Extensions
    # Babel
    babel = Babel(app, default_locale='en_US')

    # Check if saved default language exists. If not fallback to default
    @app.before_first_request
    def check_default_lang():
        def_lang = notebook.conf['default_language']
        trans_ids = [str(trans) for trans in babel.list_translations()]
        if def_lang not in trans_ids:
            notebook.conf['default_language'] = None

    # register callback function for locale selection
    # this function must be modified to add per user language support
    @babel.localeselector
    def get_locale():
        return g.notebook.conf['default_language']

    # Themes
    app.config['THEME_PATHS'] = CFG.THEME_PATHS
    app.config['DEFAULT_THEME'] = CFG.DEFAULT_THEME
    Themes(app, app_identifier='sagewui', loaders=[theme_paths_loader])
    name = notebook.conf['theme']
    if name not in app.theme_manager.themes:
        notebook.conf['theme'] = app.config['DEFAULT_THEME']

    # autoindex v0.3 doesnt seem to work with modules
    # routing with app directly does the trick
    # TODO: Check to see if autoindex 0.4 works with modules
    idx = AutoIndex(app, browse_root=CFG.SRC_PATH, add_url_rules=False)

    @app.route('/src/')
    @app.route('/src/<path:path>')
    @guest_or_login_required
    def autoindex(path='.'):
        filename = os.path.join(CFG.SRC_PATH, path)
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                src = f.read().decode('utf-8', 'ignore')
            if (os.path.splitext(filename)[1] in
                    ['.py', '.c', '.cc', '.h', '.hh', '.pyx', '.pxd']):
                return render_template(
                    'html/source_code.html',
                    src_filename=path, src=src, username=g.username)
            return src
        return idx.render_autoindex(path)

    return app
