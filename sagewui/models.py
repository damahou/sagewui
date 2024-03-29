from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object


import copy
import time

from flask_babel import gettext
from flask_babel import lazy_gettext

from . import config as CFG
from .util import import_from
from .util import N_
from .util import set_default

_ = lazy_gettext

app_defaults = {
    'word_wrap_cols': 72,
    'max_history_length': 250,

    'idle_timeout': 0,        # timeout in seconds for worksheets
    'doc_timeout': 600,         # timeout in seconds for live docs
    'idle_check_interval': 360,

    'save_interval': 360,        # seconds

    'doc_pool_size': 128,

    'pub_interact': False,

    'server_pool': [],

    'system': 'sage',

    'pretty_print': False,

    'ulimit': '',

    'notification_recipients': None,

    'email': False,

    'accounts': False,

    'challenge': False,
    'challenge_type': 'simple',
    'recaptcha_public_key': '',
    'recaptcha_private_key': '',
    'default_language': 'en_US',
    'theme': 'Default',
    'model_version': 0,

    'auth_ldap': False,
    'ldap_uri': 'ldap://example.net:389/',
    'ldap_basedn': 'ou=users,dc=example,dc=net',
    'ldap_binddn': 'cn=manager,dc=example,dc=net',
    'ldap_bindpw': 'secret',
    'ldap_gssapi': False,
    'ldap_username_attrib': 'cn',
    'ldap_timeout': 5,
    }

app_gui_hints = {
    'max_history_length': {
        CFG.DESC: _('Maximum history length'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'idle_timeout': {
        CFG.POS: 1,
        CFG.DESC: _('Idle timeout for normal worksheets (seconds)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'doc_timeout': {
        CFG.POS: 3,
        CFG.DESC: _('Idle timeout for live documentation (seconds)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'idle_check_interval': {
        CFG.DESC: _('Idle check interval (seconds)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'save_interval': {
        CFG.DESC: _('Save interval (seconds)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'doc_pool_size': {
        CFG.DESC: _('Doc worksheet pool size'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'pub_interact': {
        CFG.DESC: _(
            'Enable published interacts (EXPERIMENTAL; USE AT YOUR OWN RISK)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_BOOL,
    },
    'server_pool': {
        CFG.DESC: _('Worksheet process users (comma-separated list)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_LIST,
    },
    'system': {
        CFG.DESC: _('Default system'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_STRING,
    },
    'ulimit': {
        CFG.DESC: _('Worksheet process limits'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_STRING,
    },
    'model_version': {
        CFG.DESC: _('Model Version'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_INFO,
    },
    'notification_recipients': {
        CFG.DESC: _('Send notification e-mails to (comma-separated list)'),
        CFG.GROUP: CFG.G_SERVER,
        CFG.TYPE: CFG.T_LIST,
    },
    'word_wrap_cols': {
        CFG.DESC: _('Number of word-wrap columns'),
        CFG.GROUP: CFG.G_APPEARANCE,
        CFG.TYPE: CFG.T_INTEGER,
    },
    'pretty_print': {
        CFG.DESC: _('Pretty print (typeset) output'),
        CFG.GROUP: CFG.G_APPEARANCE,
        CFG.TYPE: CFG.T_BOOL,
    },
    'default_language': {
        CFG.DESC: _('Default Language'),
        CFG.GROUP: CFG.G_APPEARANCE,
        CFG.TYPE: CFG.T_CHOICE,
        CFG.CHOICES: CFG.TRANSLATIONS,
    },
    'theme': {
        CFG.DESC: _('Theme'),
        CFG.GROUP: CFG.G_APPEARANCE,
        CFG.TYPE: CFG.T_CHOICE,
        CFG.CHOICES: CFG.THEMES,
    },

    'accounts': {
        CFG.POS: 2,
        CFG.DESC: _('Enable user registration'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_BOOL,
    },
    'email': {
        CFG.POS: 3,
        CFG.DESC: _('Require e-mail for account registration'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_BOOL,
    },
    'challenge': {
        CFG.POS: 4,
        CFG.DESC: _('Use a challenge for account registration'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_BOOL,
    },
    'challenge_type': {
        CFG.POS: 4,
        CFG.DESC: _('Type of challenge'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_CHOICE,
        CFG.CHOICES: [N_('simple'), N_('recaptcha')],
    },
    'recaptcha_public_key': {
        CFG.DESC: _('reCAPTCHA public key'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_STRING,
    },
    'recaptcha_private_key': {
        CFG.DESC: _('reCAPTCHA private key'),
        CFG.GROUP: CFG.G_AUTH,
        CFG.TYPE: CFG.T_STRING,
    },

    'auth_ldap': {
        CFG.POS: 1,
        CFG.DESC: _('Enable LDAP Authentication'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_BOOL,
    },
    'ldap_uri': {
        CFG.POS: 2,
        CFG.DESC: _('LDAP URI'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_STRING,
    },
    'ldap_binddn': {
        CFG.POS: 3,
        CFG.DESC: _('Bind DN'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_STRING,
    },
    'ldap_bindpw': {
        CFG.POS: 4,
        CFG.DESC: _('Bind Password'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_STRING,
    },
    'ldap_gssapi': {
        CFG.POS: 5,
        CFG.DESC: _('Use GSSAPI instead of Bind DN/Password'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_BOOL,
    },
    'ldap_basedn': {
        CFG.POS: 6,
        CFG.DESC: _('Base DN'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_STRING,
    },
    'ldap_username_attrib': {
        CFG.POS: 7,
        CFG.DESC: _('Username Attribute (i.e. cn, uid or userPrincipalName)'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_STRING,
    },
    'ldap_timeout': {
        CFG.POS: 8,
        CFG.DESC: _('Query timeout (seconds)'),
        CFG.GROUP: CFG.G_LDAP,
        CFG.TYPE: CFG.T_INTEGER,
    },
}

user_defaults = {
    'max_history_length': 1000,
    'default_system': 'sage',
    'autosave_interval': 60 * 60,
    'default_pretty_print': False,
    'next_worksheet_id_number': -1,  # not yet initialized
    'language': 'default',
    }

user_gui_hints = {
    'language': {
        CFG.DESC: lazy_gettext('Language'),
        CFG.GROUP: lazy_gettext('Appearance'),
        CFG.TYPE: CFG.T_CHOICE,
        CFG.CHOICES: ['default'] + CFG.TRANSLATIONS,
        },
    }


class Configuration(object):
    @classmethod
    def from_basic(cls, basic):
        c = cls()
        c.confs = copy.copy(basic)
        return c

    def __init__(self):
        self.confs = {}

    def __repr__(self):
        return 'Configuration: %s' % self.confs

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.confs == other.confs

    def __ne__(self, other):
        return not self.__eq__(other)

    def basic(self):
        return self.confs

    def defaults(self):
        raise NotImplementedError

    def defaults_descriptions(self):
        raise NotImplementedError

    def __getitem__(self, key):
        try:
            return self.confs[key]
        except KeyError:
            if key in self.defaults():
                A = self.defaults()[key]
                self.confs[key] = A
                return A
            else:
                raise KeyError("No key '%s' and no default for this key" % key)

    def __setitem__(self, key, value):
        self.confs[key] = value

    def html_conf_form(self, action):
        D = self.defaults()
        C = self.confs
        K = list(set(list(C.keys()) + list(D.keys())))
        K.sort()
        options = ''
        for key in K:
            options += ('<tr><td>%s</td><td><input type="text" name="%s" '
                        'value="%s"></td></tr>\n' % (
                            key, key, self[key]))
        s = """
        <form method="post" action="%s" enctype="multipart/form-data">
        <input type="submit" value="Submit">
        <table border=0 cellpadding=5 cellspacing=2>
            %s
        </table>
        </form>
        """ % (action, options)
        return s

    def update_from_form(self, form):
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        keys = list(set(list(C.keys()) + list(D.keys())))

        updated = {}
        for key in keys:
            try:
                typ = DS[key][CFG.TYPE]
            except KeyError:
                # We skip this setting.  Perhaps defaults_descriptions
                # is not in sync with defaults, someone has tampered
                # with the request arguments, etc.
                continue
            val = form.get(key, '')

            if typ == CFG.T_BOOL:
                if val:
                    val = True
                else:
                    val = False

            elif typ == CFG.T_INTEGER:
                try:
                    val = int(val)
                except ValueError:
                    val = self[key]

            elif typ == CFG.T_REAL:
                try:
                    val = float(val)
                except ValueError:
                    val = self[key]

            elif typ == CFG.T_LIST:
                val = val.strip()
                if val == '' or val == 'None':
                    val = None
                else:
                    val = val.split(',')

            if typ != CFG.T_INFO and self[key] != val:
                self[key] = val
                updated[key] = ('updated', gettext('Updated'))

        return updated

    def html_table(self, updated=None):
        if updated is None:
            updated = {}

        # check if LDAP can be used
        ldap_version = import_from('ldap', '__version__')

        # For now, we assume there's a description for each setting.
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        K = set(list(C.keys()) + list(D.keys()))

        G = {}
        # Make groups
        for key in K:
            try:
                gp = DS[key][CFG.GROUP]
                # don't display LDAP settings if the check above failed
                if gp == CFG.G_LDAP and ldap_version is None:
                    continue
                DS[key][CFG.DESC]
                DS[key][CFG.TYPE]
            except KeyError:
                # We skip this setting.  It's obsolete and/or
                # defaults_descriptions is not up to date.  See
                # *_conf.py for details.
                continue
            try:
                G[gp].append(key)
            except KeyError:
                G[gp] = [key]

        s = ''
        color_picker = 0
        special_init = ''
        for group in G:
            s += ('<div class="section">\n  <h2>%s</h2>\n  <table>\n' %
                  lazy_gettext(group))

            opts = G[group]

            opts.sort(key=lambda x: (DS[x].get(CFG.POS, CFG.POS_DEFAULT), x))
            for o in opts:
                s += ('    <tr>\n      <td>%s</td>\n      <td>\n' %
                      lazy_gettext(DS[o][CFG.DESC]))
                input_type = 'text'
                input_value = self[o]

                extra = ''
                if DS[o][CFG.TYPE] == CFG.T_BOOL:
                    input_type = 'checkbox'
                    if input_value:
                        extra = 'checked="checked"'

                if DS[o][CFG.TYPE] == CFG.T_LIST:
                    if input_value is not None:
                        input_value = ','.join(input_value)

                if DS[o][CFG.TYPE] == CFG.T_CHOICE:
                    s += '        <select name="%s" id="%s">\n' % (o, o)
                    for c in DS[o][CFG.CHOICES]:
                        selected = ''
                        if c == input_value:
                            selected = ' selected="selected"'
                        s += ('          <option value="%s"%s>%s</option>\n' %
                              (c, selected, lazy_gettext(c)))
                    s += '        </select>\n'

                elif DS[o][CFG.TYPE] == CFG.T_INFO:
                    s += '        <span>%s</span>' % input_value

                else:
                    s += ('        <input type="%s" name="%s" id="%s" '
                          'value="%s" %s>\n' % (
                              input_type, o, o, input_value, extra))

                    if DS[o][CFG.TYPE] == CFG.T_COLOR:
                        s += ('        <div id="picker_%s"></div>\n' %
                              color_picker)
                        special_init += (
                            '    $("#picker_%s").farbtastic("#%s");\n' % (
                                color_picker, o))
                        color_picker += 1

                s += ('      </td>\n      <td class="%s">%s</td>\n'
                      '    </tr>\n' % updated.get(o, ('', '')))

            s += '  </table>\n</div>\n'

        s += ('<script type="text/javascript">\n'
              '$(document).ready(function() {\n' + special_init +
              '});\n</script>')

        lines = s.split('\n')
        lines = ['  ' + x for x in lines]

        return '\n'.join(lines)


class ServerConfiguration(Configuration):
    def defaults(self):
        return app_defaults

    def defaults_descriptions(self):
        return app_gui_hints


class UserConfiguration(Configuration):
    def defaults(self):
        return user_defaults

    def defaults_descriptions(self):
        return user_gui_hints


class User(object):
    account_types = (CFG.UAT_ADMIN, CFG.UAT_USER, CFG.UAT_GUEST)

    def __init__(self,
                 username, password='', email='',
                 account_type=CFG.UAT_ADMIN, external_auth=None,

                 email_confirmed=False,
                 is_suspended=False,
                 viewable_worksheets=None,
                 conf=None,
                 temporary_password='',  # TODO: Remove. Useless.
                 # TODO: There are a spurious User__username field in the
                 # cpickled users this **kwargs get rid of this and other
                 # spurious fields. This must be removed when the pickled
                 # users integrity is checked in a more apropriate way.
                 **kwargs
                 ):
        self.username = username
        self.password = password
        self.email = email
        self.email_confirmed = email_confirmed  # Boolean
        self.__account_type = account_type  # property unused?
        self.external_auth = external_auth
        self.temporary_password = temporary_password  # unused
        self.is_suspended = is_suspended
        self.viewable_worksheets = set_default(viewable_worksheets, set())
        self.conf = set_default(conf, UserConfiguration())

    @property
    def account_type(self):
        """
        EXAMPLES::

            sage: from sagenb.notebook.user import User
            sage: User('A', account_type=CFG.UAT_ADMIN).account_type
            'admin'
            sage: User('B', account_type=CFG.UAT_USER).account_type
            'user'
            sage: User('C', account_type=CFG.UAT_GUEST).account_type
            'guest'
        """
        return self.__account_type

    @account_type.setter
    def account_type(self, account_type):
        if self.username == CFG.UN_ADMIN:
            account_type = CFG.UAT_ADMIN
        elif account_type not in self.account_types:
            raise ValueError(
                'account type must be one{}, {}, or {}'.format(
                    *self.account_types))
        self.__account_type = account_type


class Worksheet(object):
    def __init__(self,
                 owner, id_number, name='', system='sage',

                 pretty_print=False, live_3D=False, auto_publish=False,
                 last_change=None, saved_by_info=None, tags=None,
                 collaborators=None,
                 published_id_number=None, worksheet_that_was_published=None,
                 ratings=None,
                 # TODO: There are a spurious User__username field in the
                 # cpickled users this **kwargs get rid of this and other
                 # spurious fields. This must be removed when the pickled
                 # users integrity is checked in a more apropriate way.
                 **kwargs
                 ):
        self.owner = owner
        self.id_number = id_number
        self.name = name
        self.system = system
        self.pretty_print = pretty_print
        self.live_3D = live_3D
        self.auto_publish = auto_publish
        self.last_change = set_default(last_change, (owner, time.time()))
        self.saved_by_info = set_default(saved_by_info, dict())
        self.tags = set_default(tags, dict())
        self.collaborators = set_default(collaborators, list())
        self.published_id_number = published_id_number
        self.worksheet_that_was_published = set_default(
            worksheet_that_was_published, (owner, id_number))
        self.ratings = set_default(ratings, list())
