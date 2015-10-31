from __future__ import absolute_import

import os
from flask import Blueprint
from flask import url_for
from flask import request
from flask import redirect
from flask import g
from flask.ext.babel import gettext

from ..misc.misc import SAGE_VERSION
from ..notebook.misc import is_valid_password
from ..notebook.misc import is_valid_email
from ..notebook.themes import render_template

from ..util import templates
from ..util.decorators import login_required
from ..util.decorators import with_lock

_ = gettext

settings = Blueprint('settings', __name__)


@settings.route('/settings', methods=['GET', 'POST'])
@login_required
@with_lock
def settings_page():
    error = None
    redirect_to_home = None
    redirect_to_logout = None
    nu = g.notebook.user_manager().user(g.username)

    autosave = int(request.values.get('autosave', 0)) * 60
    if autosave:
        nu['autosave_interval'] = autosave
        redirect_to_home = True

    old = request.values.get('old-pass', None)
    new = request.values.get('new-pass', None)
    two = request.values.get('retype-pass', None)

    if new or two:
        if not old:
            error = _('Old password not given')
        elif not g.notebook.user_manager().check_password(g.username, old):
            error = _('Incorrect password given')
        elif not new:
            error = _('New password not given')
        elif not is_valid_password(new, g.username):
            error = _(
                'Password not acceptable. Must be 4 to 32 characters and not '
                'contain spaces or username.')
        elif not two:
            error = _('Please type in new password again.')
        elif new != two:
            error = _('The passwords you entered do not match.')

        if not error:
            # The browser may auto-fill in "old password," even
            # though the user may not want to change her password.
            g.notebook.user_manager().set_password(g.username, new)
            redirect_to_logout = True

    if g.notebook.conf()['email']:
        newemail = request.values.get('new-email', None)
        if newemail:
            if is_valid_email(newemail):
                nu.set_email(newemail)
                # nu.set_email_confirmation(False)
                redirect_to_home = True
            else:
                error = _('Invalid e-mail address.')

    if error:
        return templates.message(error, url_for('settings_page'))

    if redirect_to_logout:
        return redirect(url_for('authentication.logout'))

    if redirect_to_home:
        return redirect(url_for('worksheet_listing.home', username=g.username))

    td = {}
    td['sage_version'] = SAGE_VERSION
    td['username'] = g.username

    td['autosave_intervals'] = (
        (i, ' selected') if nu['autosave_interval'] / 60 == i else (i, '')
        for i in range(1, 10, 2))

    td['email'] = g.notebook.conf()['email']
    if td['email']:
        td['email_address'] = nu.get_email() or 'None'
        if nu.is_email_confirmed():
            td['email_confirmed'] = _('Confirmed')
        else:
            td['email_confirmed'] = _('Not confirmed')

    td['admin'] = nu.is_admin()

    return render_template(
        os.path.join('html', 'settings', 'account_settings.html'), **td)
