
import os
from babel import Locale
from babel.core import UnknownLocaleError
from pkg_resources import resource_filename

from appdirs import user_data_dir
from flask_babel import lazy_gettext
from pexpect.exceptions import ExceptionPexpect

from sagewui_kernels.sage.workers import sage
from .util import sage_browser

app_name = 'sagewui'

# sagewui default paths
APP_PATH = resource_filename(__name__, '')
HOME_PATH = user_data_dir(app_name)
DB_DIR = 'db'
SSL_DIR = 'ssl'
PID_DIR = 'run'
PID_FILE_TEMPLATE = 'sagewui-{}.pid'

# DB
DEFAULT_NB_NAME = 'default'

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
def update_themes(default_theme='Default'):
    global THEME_PATHS
    global THEMES
    global DEFAULT_THEME
    THEME_PATHS = [
        tp for tp in (os.path.join(d, 'themes') for d in [APP_PATH, HOME_PATH])
        if os.path.isdir(tp)]
    THEMES = [theme for path in THEME_PATHS for theme in os.listdir(path)
              if os.path.isdir(os.path.join(path, theme))]
    THEMES.sort()
    DEFAULT_THEME = 'Default'


update_themes()

# translations
TRANSLATIONS_PATH = os.path.join(APP_PATH, 'translations')
TRANSLATIONS = []
for name in (lan for lan in os.listdir(TRANSLATIONS_PATH) if lan != 'en_US'):
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
MIN_PASSWORD_LENGTH = 6


# Global variables across the application
# TODO: remove this. Previously in notebook.misc
notebook = None

# sage runtime configuration
SAGE = None
SAGE_PATH = None
SAGE_VERSION = None
BROWSER_PATH = None
DOC_PATH = None
SRC_PATH = None
JMOL_PATH = None
JSMOL_PATH = None
J2S_PATH = None
THREEJS_PATH = None
INTERACT_UPDATE_PREFIX = None
INTERACT_RESTART = None
INTERACT_START = None
INTERACT_TEXT = None
INTERACT_HTML = None
INTERACT_END = None
MATHJAX_MACROS = None


def add_sage_conf(sage_path='sage'):
    global SAGE_PATH
    global SAGE_VERSION
    global BROWSER_PATH
    global DOC_PATH
    global SRC_PATH
    global JMOL_PATH
    global JSMOL_PATH
    global J2S_PATH
    global THREEJS_PATH
    global INTERACT_UPDATE_PREFIX
    global INTERACT_RESTART
    global INTERACT_START
    global INTERACT_TEXT
    global INTERACT_HTML
    global INTERACT_END
    global MATHJAX_MACROS

    SAGE_PATH = sage_path

    try:
        sage_conf = sage(sage=SAGE_PATH)
    except ExceptionPexpect:
        raise OSError(
            'Install sage and ensure that "{}" is in system PATH'.format(
                SAGE_PATH))

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

    sage_conf = eval(sconf.output.strip())
    sage_env, MATHJAX_MACROS, interact_conf = sage_conf

    if isinstance(MATHJAX_MACROS, dict):
        MATHJAX_MACROS = ['{}: {!r}'.format(k, v).replace("'", '"')
                          for k, v in MATHJAX_MACROS.items()]
    SAGE_VERSION = sage_env['SAGE_VERSION']

    # sage paths
    BROWSER_PATH = sage_browser(sage_env['SAGE_ROOT'])

    # paths for static urls
    DOC_PATH = os.path.join(sage_env['SAGE_DOC'], 'html', 'en')
    SRC_PATH = os.path.join(sage_env['SAGE_SRC'], 'sage')
    JMOL_PATH = os.path.join(sage_env['SAGE_SHARE'], 'jmol')
    JSMOL_PATH = os.path.join(sage_env['SAGE_SHARE'], 'jsmol')
    J2S_PATH = os.path.join(JSMOL_PATH, 'j2s')
    THREEJS_PATH = os.path.join(sage_env['SAGE_SHARE'], 'threejs')

    # Interact markers
    INTERACT_UPDATE_PREFIX = interact_conf['UPDATE_PREFIX']
    INTERACT_RESTART = interact_conf['RESTART']
    INTERACT_START = interact_conf['START']
    INTERACT_TEXT = interact_conf['TEXT']
    INTERACT_HTML = interact_conf['HTML']
    INTERACT_END = interact_conf['END']
