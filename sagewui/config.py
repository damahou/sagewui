from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
from babel import Locale
from babel.core import UnknownLocaleError
from pkg_resources import resource_filename

from appdirs import user_data_dir
from flask_babel import lazy_gettext
from pexpect.exceptions import ExceptionPexpect

from .sage_server.workers import sage
from .util import sage_browser

# Global variables across the application
# TODO: remove this. Previously in notebook.misc
APP_NAME = 'sagewui'
notebook = None

try:
    sage_conf = sage()
except ExceptionPexpect:
    raise OSError('Install sage and ensure that "sage" is in system PATH')

sage_conf.execute('\n'.join((
    'from sage.env import SAGE_ENV',
    'from sage.misc.latex_macros import sage_mathjax_macros',
    '[',
    '    SAGE_ENV,',
    '    sage_mathjax_macros(),',
    '    {',
    '         "UPDATE_PREFIX": _interact_.INTERACT_UPDATE_PREFIX,',
    '         "RESTART": _interact_.INTERACT_RESTART,',
    '         "START": _interact_.INTERACT_START,',
    '         "TEXT": _interact_.INTERACT_TEXT,',
    '         "HTML": _interact_.INTERACT_HTML,',
    '         "END": _interact_.INTERACT_END,',
    '         },',
    ' ]',
    )))
while True:
    sconf = sage_conf.output_status()
    if sconf.done:
        break
sage_conf.quit()

exec('sage_conf = ' + sconf.output.strip())
SAGE_ENV, mathjax_macros, INTERACT_CONF = sage_conf
SAGE_VERSION = SAGE_ENV['SAGE_VERSION']

# sage paths
BROWSER_PATH = sage_browser(SAGE_ENV['SAGE_ROOT'])

# sagewui paths
# TODO: This must be in sync with flask app base path. Should be removed from
# here
APP_PATH = resource_filename(__name__, '')
BASE_PATH = user_data_dir(APP_NAME)
DB_PATH = os.path.join(BASE_PATH, 'db')
SSL_PATH = os.path.join(BASE_PATH, 'ssl')
PID_PATH = os.path.join(BASE_PATH, 'run')
HOME_PATH = BASE_PATH
PID_FILE_TEMPLATE = 'sagewui-{}.pid'

# paths for static urls
DOC_PATH = os.path.join(SAGE_ENV['SAGE_DOC'], 'output', 'html', 'en')
SRC_PATH = os.path.join(SAGE_ENV['SAGE_SRC'], 'sage')
JMOL_PATH = os.path.join(SAGE_ENV['SAGE_SHARE'], 'jmol')
JSMOL_PATH = os.path.join(SAGE_ENV['SAGE_SHARE'], 'jsmol')
J2S_PATH = os.path.join(JSMOL_PATH, 'j2s')

# DB
DEFAULT_NB_NAME = 'default'

# Interact markers
INTERACT_UPDATE_PREFIX = INTERACT_CONF['UPDATE_PREFIX']
INTERACT_RESTART = INTERACT_CONF['RESTART']
INTERACT_START = INTERACT_CONF['START']
INTERACT_TEXT = INTERACT_CONF['TEXT']
INTERACT_HTML = INTERACT_CONF['HTML']
INTERACT_END = INTERACT_CONF['END']

# Gui config
CHOICES = 'choices'
DESC = 'desc'
GROUP = 'group'
POS = 'pos'
TYPE = 'type'

T_BOOL = 0
T_CHOICE = 2
T_COLOR = 4
T_INFO = 7
T_INTEGER = 1
T_LIST = 6
T_REAL = 3
T_STRING = 5

G_APPEARANCE = lazy_gettext('Appearance')
G_AUTH = lazy_gettext('Authentication')
G_LDAP = lazy_gettext('LDAP')
G_SERVER = lazy_gettext('Server')

POS_DEFAULT = 100

# Users Globals
SALT = 'aa'
# User Account Types
UAT_ADMIN = 'admin'
UAT_USER = 'user'
UAT_GUEST = 'guest'
# User Names
UN_ADMIN = 'admin'  # User name for default admin user
UN_GUEST = 'guest'
UN_PUB = 'pub'  # User name for published worksheets
UN_SAGE = '_sage_'  # User name for doc browser worksheets
UN_SYSTEM = (UN_GUEST, UN_SAGE, UN_PUB)

# Default worksheet tags
# Integers that define which folder this worksheet is in relative to a given
# user.
WS_ARCHIVED = 0
WS_ACTIVE = 1
WS_TRASH = 2

# Notebook globals
# [(string: name, bool: optional)]
SYSTEMS = (('sage', False),
           ('gap', False),
           ('gp', False),
           ('html', False),
           ('latex', False),
           ('maxima', False),
           ('python', False),
           ('r', False),
           ('sh', False),
           ('singular', False),
           ('axiom', True),
           ('fricas', True),
           ('kash', True),
           ('macaulay2', True),
           ('magma', True),
           ('maple', True,),
           ('mathematica', True),
           ('matlab', True),
           ('mupad', True),
           ('octave', True),
           ('scilab', True))


# Cell output control
# Maximum number of characters allowed in output.  This is needed
# avoid overloading web browser.  For example, it should be possible
# to gracefully survive:
#    while True:
#       print("hello world")
# On the other hand, we don't want to loose the output of big matrices
# and numbers, so don't make this too small.
MAX_OUTPUT = 32000
MAX_OUTPUT_LINES = 120
# Used to detect and format tracebacks.
# See :func:`.util.text.format_exception`.
TRACEBACK = 'Traceback (most recent call last):'

# Worksheet control
# Constants that control the behavior of the worksheet.
INITIAL_NUM_CELLS = 1  # number of empty cells in new worksheets
WARN_THRESHOLD = 100   # The number of seconds, so if there was no
# activity on this worksheet for this many
# seconds, then editing is considered safe.
# Used when multiple people are editing the
# same worksheet.

# themes
THEME_PATHS = [
    tp for tp in (os.path.join(d, 'themes') for d in [APP_PATH, BASE_PATH])
    if os.path.isdir(tp)]
# TODO: Only needed by sagenb.notebook.server_conf
THEMES = []
for path in THEME_PATHS:
    THEMES.extend([
        theme for theme in os.listdir(path)
        if os.path.isdir(os.path.join(path, theme))])
THEMES.sort()
DEFAULT_THEME = 'Default'
# TODO: dangerous. flask_babel translations path is not configurable.
# This must be in sync with the hardcoded babel translation path. This
# should be removed when sagenb.notebook.server_conf, sagenb.notebook.user_conf
# be refactored.

# translations
TRANSLATIONS_PATH = os.path.join(APP_PATH, 'translations')
# TODO: Only needed by sagenb.notebook.server_conf, sagenb.notebook.user_conf
TRANSLATIONS = []
for name in (l for l in os.listdir(TRANSLATIONS_PATH) if l != 'en_US'):
    try:
        Locale.parse(name)
    except UnknownLocaleError:
        pass
    else:
        TRANSLATIONS.append(name)
TRANSLATIONS.sort()
TRANSLATIONS.insert(0, 'en_US')
# For pybabel
lazy_gettext('January')
lazy_gettext('February')
lazy_gettext('March')
lazy_gettext('April')
lazy_gettext('May')
lazy_gettext('June')
lazy_gettext('July')
lazy_gettext('August')
lazy_gettext('September')
lazy_gettext('October')
lazy_gettext('November')
lazy_gettext('December')

# GUI settings
MATHJAX = True
JEDITABLE_TINYMCE = True

# password
min_password_length = 6
