
import datetime
import time
import re

from hashlib import sha1
from itertools import islice
from jsmin import jsmin
from pathlib import Path

from flask import g
from flask import current_app as app
from flask import send_from_directory
from flask_babel import format_datetime
from flask_babel import get_locale
from flask_babel import ngettext
from flask_themes2 import render_theme_template
from flask_themes2 import get_theme

from . import cached_property
from . import N_
from . import nN_
from .keymaps_js import get_keyboard

from .. import config as CFG
from flask import json

css_illegal_re = re.compile(r'[^-A-Za-z_0-9]')


# jinja2 filters

def css_escape(string):
    r"""
    Returns a string with all characters not legal in a css name
    replaced with hyphens (-).

    INPUT:

    - ``string`` -- the string to be escaped.

    EXAMPLES::

        sage: from sagenb.util.templates import css_escape
        sage: css_escape('abcd')
        'abcd'
        sage: css_escape('12abcd')
        '12abcd'
        sage: css_escape(r'\'"abcd\'"')
        '---abcd---'
        sage: css_escape('my-invalid/identifier')
        'my-invalid-identifier'
        sage: css_escape(r'quotes"mustbe!escaped')
        'quotes-mustbe-escaped'
    """
    return css_illegal_re.sub('-', string)


def prettify_time_ago(t):
    """
    Converts seconds to a meaningful string.

    INPUT

    - t -- time in seconds

    """
    if t < 60:
        s = int(t)
        return ngettext('%(num)d second', '%(num)d seconds', s)
    if t < 3600:
        m = int(t / 60)
        return ngettext('%(num)d minute', '%(num)d minutes', m)
    if t < 3600 * 24:
        h = int(t / 3600)
        return ngettext('%(num)d hour', '%(num)d hours', h)
    d = int(t / (3600 * 24))
    return ngettext('%(num)d day', '%(num)d days', d)


def convert_time_to_string(t):
    """
    Converts ``t`` (in Unix time) to a locale-specific string
    describing the time and date.
    """
    try:
        return format_datetime(datetime.datetime.fromtimestamp(float(t)))
    except AttributeError:  # testing as opposed to within the Flask app
        return time.strftime('%B %d, %Y %I:%M %p', time.localtime(float(t)))


def number_of_rows(txt, ncols):
    r"""
    Returns the number of rows needed to display a string, given a
    maximum number of columns per row.

    INPUT:

    - ``txt`` - a string; the text to "wrap"

    - ``ncols`` - an integer; the number of word wrap columns

    OUTPUT:

    - an integer

    EXAMPLES::

        sage: from sagenb.notebook.cell import number_of_rows
        sage: s = "asdfasdf\nasdfasdf\n"
        sage: number_of_rows(s, 8)
        2
        sage: number_of_rows(s, 5)
        4
        sage: number_of_rows(s, 4)
        4
    """
    rows = txt.splitlines()
    nrows = len(rows)
    for i in range(nrows):
        nrows += (len(rows[i]) - 1) // ncols
    return nrows


def join_max(it, maxi=None, sep=', '):
    it = list(it)
    if maxi is not None and len(it) > maxi:
        it = it[:maxi]
        it.append('...')
    return sep.join(it)


# theme template rendering

def render_template(template, **context):
    """
    For themes to work this replacement of flask.render_template must be used.

    INPUT:

    - As in flask.render_template

    OUTPUT:

    - As in flask.render_template, but if the current theme miss the template,
      the application's normal template is served.

    EXAMPLES::

        sage: from sagewui.util.templates import render_template
        sage: type(render_template)
    """
    theme = g.notebook.conf['theme']
    return render_theme_template(theme, template, **context)


# theme static files

def theme_relative_static_path(themeid):
    theme_absolute_path = Path(get_theme(themeid).static_path)
    app_absolute_path = Path(app.root_path)

    return theme_absolute_path.relative_to(app_absolute_path)


def current_theme_relative_static_path():
    return theme_relative_static_path(g.notebook.conf['theme'])


def send_static_file(path):
    """
    Replacement of flask.Flask.send_static_file( for send static files
    from current theme.

    INPUT:

    - As in flask.Flask.send_static_file

    OUTPUT:

    - As static file in current theme static folder, but if the current theme
    miss the file, the application's normal static file is served.

    EXAMPLES::

        sage: from sagewui.util.templates import send_static_file
        sage: type(send_static_file)
    """

    static_path = current_theme_relative_static_path()
    file_path = static_path / path
    if file_path.exists():
        return send_from_directory(file_path, path)
    else:
        return app.send_static_file(path)


# Message template

def message(msg, cont='/', username=None, **kwds):
    """Returns an error message to the user."""
    template_dict = {
        'msg': msg, 'cont': cont,
        'username': username,
        'sage_version': CFG.SAGE_VERSION
        }
    template_dict.update(kwds)
    return render_template('html/error_message.html', **template_dict)


# Dynamic javascript

class DynamicJs(object):
    def __init__(self, debug=False):
        self.debug = debug
        self.__localization = {}
        self.__keyboard = {}

    @property
    def localization(self):
        locale = repr(get_locale())
        if self.__localization.get(locale, None) is None:
            data = render_template('js/localization.js', N_=N_, nN_=nN_)
            self.__localization[locale] = self._prepare_data(data)
        return self.__localization[locale]

    @cached_property()
    def mathjax(self):
        data = render_template('js/mathjax_sage.js',
                               theme_mathjax_macros=CFG.MATHJAX_MACROS)
        return self._prepare_data(data)

    def keyboard(self, browser_os):
        if self.__keyboard.get(browser_os, None) is None:
            data = get_keyboard(browser_os)
            self.__keyboard[browser_os] = self._prepare_data(data)

        return self.__keyboard[browser_os]

    def _prepare_data(self, data):
        if not self.debug:
            data = jsmin(data)
        return (data, sha1(repr(data).encode('utf-8')).hexdigest())

    def clear_cache(self):
        del self.mathjax
        self.__localization = {}
        self.__keyboard = {}


# json responses

def encode_response(obj, separators=(',', ':'), **kwargs):
    """
    Encodes response data to send to a client.  The current
    implementation uses JSON.  See :mod:`json` for details.

    INPUT:

    - ``obj`` - an object comprised of basic Python types

    - ``separators`` - a string 2-tuple (default: (',', ':'));
      dictionary separators to use

    - ``kwargs`` - additional keyword arguments to pass to the
      encoding function

    OUTPUT:

    - a string

    EXAMPLES::

        sage: from sagenb.notebook.misc import encode_response
        sage: o = [int(3), float(2), {'foo': 'bar'}, None]
        sage: encode_response(o)
        '[3,2.0,{"foo":"bar"},null]'
        sage: d = {'AR': 'MA', int(11): 'foo', 'bar': float(1.0), None: 'blah'}
        sage: encode_response(d, sort_keys = True)
        '{"null":"blah","11":"foo","AR":"MA","bar":1.0}'
        sage: d['archies'] = ['an', 'mon', 'hier']
        sage: d['sub'] = {'shape': 'triangle', 'color': 'blue',
                          'sides': [int(3), int(4), int(5)]}
        sage: encode_response(d, sort_keys = True)
        '{"null":"blah","11":"foo","AR":"MA","archies":["an","mon","hier"],
        "bar":1.0,"sub":{"color":"blue","shape":"triangle","sides":[3,4,5]}}'
        sage: print(encode_response(d, separators = (', ', ': '), indent = 4))
        {
            "...": ...
        }
    """
    # TODO: Serialize class attributes, so we can do, e.g., r_dict.foo
    # = 'bar' instead of r_dict['foo'] = 'bar' below.

    # TODO: Use cjson, simplejson instead?  Serialize Sage types,
    # e.g., Integer, RealLiteral?
    return json.dumps(obj, separators=separators, **kwargs)


# completions


def completions_html(cell_id, s, cols=3):
    """
    Returns tabular HTML code for a list of introspection completions.

    INPUT:

    - ``cell_id`` - an integer or a string; the ID of the ambient cell

    - ``s`` - a string with space separated completions

    - ``cols`` max number of columns


    OUTPUT:

    - html code
    """
    if 'no completions of' in s:
        return ''

    s = s.split()
    if len(s) <= 1:
        return ''  # don't show a window, just replace it

    completions = enumerate(islice(s, i, None, cols) for i in range(cols))
    return render_template(
        'html/worksheet/completions.html',
        cell_id=cell_id,
        completions_enumerated=completions)
