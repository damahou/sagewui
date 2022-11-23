# -*- coding: utf-8 -*
"""
The Sage Notebook

AUTHORS:

  - William Stein
"""

#############################################################################
#
#       Copyright (C) 2006-2009 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#
#############################################################################
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import object
from builtins import open

import logging
import os
import re
import shutil
import traceback
import sys

from docutils.core import publish_parts

from sagewui_kernels.sage.workers import sage
from .. import config as CFG
from ..storage import FilesystemDatastore
from ..util import cached_property
from ..util import make_path_relative
from ..util import makedirs
from ..util import set_restrictive_permissions
from ..util import sort_worksheet_list
from ..util import walltime
from ..util.decorators import global_lock
from ..util.docHTMLProcessor import docutilsHTMLProcessor
from ..util.docHTMLProcessor import SphinxHTMLProcessor
from ..util.notification import logger
from ..util.notification import TwistedEmailHandler
from ..util.text import extract_title
from ..util.text import extract_text

from ..models import ServerConfiguration
from ..controllers import UserManager
from .worksheet import update_worksheets


class WorksheetDict(dict):
    wst_name_re = re.compile(r'^([^/]+)/(\d+)$')

    def __init__(self, storage, *args, **kwds):
        self._storage = storage
        dict.__init__(self, *args, **kwds)

    def __missing__(self, item):
        m = self.wst_name_re.match(item)
        if m is None:
            raise KeyError(item)
        username, id = m.groups()
        id = int(id)

        try:
            worksheet = self._storage.load_worksheet(username, id)
        except ValueError:
            raise KeyError(item)

        self[item] = worksheet
        return worksheet


# Old stuff
# Notebook autosave.
# Save if make a change to notebook and at least some seconds have elapsed
# since last save.

class NotebookUpdater(object):

    def __init__(self, notebook):
        self.notebook = notebook
        self.save_interval = notebook.conf['save_interval']
        self.idle_interval = notebook.conf['idle_check_interval']
        self.last_save_time = walltime()
        self.last_idle_time = walltime()

    def save_check(self):
        t = walltime()
        if t > self.last_save_time + self.save_interval:
            with global_lock:
                # if someone got the lock before we did, they might have saved,
                # so we check against the last_save_time again we don't put the
                # global_lock around the outer loop since we don't need it
                # unless we are actually thinking about saving.
                if t > self.last_save_time + self.save_interval:
                    self.notebook.save()
                    self.last_save_time = t

    def idle_check(self):
        t = walltime()
        if t > self.last_idle_time + self.idle_interval:
            with global_lock:
                # if someone got the lock before we did, they might have
                # already idled, so we check against the last_idle_time again
                # we don't put the global_lock around the outer loop since we
                # don't need it unless we are actually thinking about quitting
                # worksheets
                if t > self.last_idle_time + self.idle_interval:
                    self.notebook.update_worksheet_processes()
                    self.notebook.quit_idle_worksheet_processes()
                    self.last_idle_time = t

    def update(self):
        self.save_check()
        self.idle_check()


class Notebook(object):
    HISTORY_MAX_OUTPUT = 92 * 5
    HISTORY_NCOLS = 90

    def __init__(self, dir, user_manager=None):
        self.systems = CFG.SYSTEMS
        # TODO: This come from notebook.misc. Must be a conf parameter
        self.DIR = None

        dir = dir.rstrip(os.sep)

        self.dir = dir

        S = FilesystemDatastore(dir)
        self._storage = S

        # Now set the configuration, loaded from the datastore.
        try:
            self.conf = S.load_server_conf()
        except IOError:
            C = ServerConfiguration()
            # if we are newly creating a notebook, then we want to
            # have a default model version of 1, currently
            # we can't just set the default value in server_conf.py
            # to 1 since it would then be 1 for notebooks without the
            # model_version property
            # TODO: distinguish between a new server config default values
            #  and default values for missing properties
            C['model_version'] = 1
            self.conf = C

        self.user_manager = UserManager(
            auth_ldap=self.conf['auth_ldap'],
            ldap_uri=self.conf['ldap_uri'],
            ldap_basedn=self.conf['ldap_basedn'],
            ldap_binddn=self.conf['ldap_binddn'],
            ldap_bindpw=self.conf['ldap_bindpw'],
            ldap_gssapi=self.conf['ldap_gssapi'],
            ldap_username_attrib=self.conf['ldap_username_attrib'],
            ldap_timeout=self.conf['ldap_timeout'],
            ) if user_manager is None else user_manager

        # Set up email notification logger
        logger.addHandler(TwistedEmailHandler(self.conf, logging.ERROR))
        # also log to stderr
        logger.addHandler(logging.StreamHandler())

        # Set the list of users
        try:
            S.load_users(self.user_manager)
        except IOError:
            pass

        # Set the list of worksheets
        W = WorksheetDict(S)
        self.__worksheets = W

        # Store / Refresh public worksheets
        for id_number in os.listdir(self._storage._abspath(
                S._user_path(CFG.UN_PUB))):
            if id_number.isdigit():
                a = "pub/" + str(id_number)
                if a not in W:
                    try:
                        W[a] = self._storage.load_worksheet(
                            CFG.UN_PUB, int(id_number))
                    except Exception:
                        print("Warning: problem loading %s/%s: %s" % (
                            CFG.UN_PUB, int(id_number),
                            traceback.format_exc()))

        # Old stuff
        self.updater = NotebookUpdater(self)

    # Repair broken notebooks. This is for migrations from official notebooks

    def repair(self):
        # mynb: repair notebooks with old unpublish method with missing
        # published worksheets
        for wst in self.all_wsts:
            if wst.published_id_number is not None:
                try:
                    self.filename_wst(wst.published_filename)
                except KeyError:
                    wst.published_id_number = None
                    wst.save()

    # App controller

    def delete(self):
        """
        Delete all files related to this notebook.

        This is used for doctesting mainly. This command is obviously
        *VERY* dangerous to use on a notebook you actually care about.
        You could easily lose all data.

        EXAMPLES::

            sage: tmp = tmp_dir()
            sage: nb = sagenb.notebook.notebook.Notebook(tmp)
            sage: sorted(os.listdir(tmp))
            ['home']
            sage: nb.delete()

        Now the directory is gone.::

            sage: os.listdir(tmp)
            Traceback (most recent call last):
            ...
            OSError: [Errno 2] No such file or directory: '...
        """
        # TODO: Not used. Only in docs.
        self._storage.delete()

    def save(self):
        """
        Save this notebook server to disk.
        """
        S = self._storage
        S.save_users(self.user_manager)
        S.save_server_conf(self.conf)
        # Save the non-doc-browser worksheets.
        for n, W in self.__worksheets.items():
            if not n.startswith('doc_browser'):
                S.save_worksheet(W)
        if hasattr(self, '_user_history'):
            for username, H in self._user_history.items():
                S.save_user_history(username, H)

    def logout(self, username):
        r"""
        Do not do anything on logout (so far).

        In particular, do **NOT** stop all ``username``'s worksheets!
        """
        pass

    def upgrade_model(self):
        """
        Upgrade the model, if needed.

        - Version 0 (or non-existent model version, which defaults to 0):
          Original flask notebook
        - Version 1: shared worksheet data cached in the User object
        """
        model_version = self.conf['model_version']
        if model_version is None or model_version < 1:
            print("Upgrading model version to version 1")
            # this uses code from all_wsts()
            user_manager = self.user_manager
            num_users = 0
            for username in self.user_manager:
                num_users += 1
                if num_users % 1000 == 0:
                    print('Upgraded %d users' % num_users)
                if username in (CFG.UN_SAGE, CFG.UN_PUB):
                    continue
                try:
                    for w in self.user_wsts(username):
                        owner = w.owner
                        id_number = w.id_number
                        collaborators = w.collaborators
                        for u in collaborators:
                            try:
                                user_manager[u].viewable_worksheets.add(
                                    (owner, id_number))
                            except KeyError:
                                # user doesn't exist
                                pass
                except (UnicodeEncodeError, OSError):
                    # Catch UnicodeEncodeError because sometimes a username has
                    # a non-ascii character Catch OSError since sometimes when
                    # moving user directories (which happens automatically when
                    # getting user's worksheets), OSError: [Errno 39] Directory
                    # not empty is thrown (we should be using shutil.move
                    # instead, probably) users with these problems won't have
                    # their sharing cached, but they will probably have
                    # problems logging in anyway, so they probably won't notice
                    # not having shared worksheets
                    print('Error on username %s' % username.encode('utf8'),
                          file=sys.stderr)
                    print(traceback.format_exc(), sys.stderr)
            print('Done upgrading to model version 1')
            self.conf['model_version'] = 1

    # App controller. The notebook history.

    def user_history(self, username):
        if not hasattr(self, '_user_history'):
            self._user_history = {}
        if username in self._user_history:
            return self._user_history[username]
        history = []
        for hunk in self._storage.load_user_history(username):
            hunk = hunk
            history.append(hunk)
        self._user_history[username] = history
        return history

    def user_history_text(self, username, maxlen=None):
        history = self.user_history(username)
        if maxlen:
            history = history[-maxlen:]
        return '\n\n'.join([hunk.strip() for hunk in history])

    def add_to_user_history(self, entry, username):
        history = self.user_history(username)
        history.append(entry)
        maxlen = self.user_manager[username]['max_history_length']
        while len(history) > maxlen:
            del history[0]

    # User query

    def readonly_user(self, username):
        """
        Returns True if the user is supposed to only be a read-only user.
        """
        return self._storage.readonly_user(username)

    # Worksheet query

    def _with_running_worksheets(self, worksheets):
        """
        if a worksheet has already been loaded in self.__worksheets, return
        that instead since worksheets that are already running should be
        noted as such.
        """
        return [self.__worksheets.get(w.filename, w) for w in worksheets]

    @property
    def _pub_wsts(self):
        path = self._storage._abspath(self._storage._user_path(CFG.UN_PUB))
        v = []
        a = ""
        for id_number in (idn for idn in os.listdir(path) if idn.isdigit()):
            a = '/'.join((CFG.UN_PUB, id_number))
            if a not in self.__worksheets:
                try:
                    self.__worksheets[a] = self._storage.load_worksheet(
                        "pub", int(id_number))
                except Exception:
                    print('Warning: problem loading {}: {}'.format(
                        a, traceback.format_exc()))
                    continue

            v.append(self.__worksheets[a])
        return v

    def _user_viewable_wsts(self, username):
        r"""
        Returns all worksheets viewable by `username`.
        For `admin`, only the worksheets owned by him are returned.
        """
        # Should return worksheets from self.__worksheets if possible
        worksheets = self.user_wsts(username)
        user_vw = self.user_manager[username].viewable_worksheets
        viewable_worksheets = (
            self._storage.load_worksheet(owner, id) for owner, id in user_vw)
        # we double-check that we can actually view these worksheets
        # just in case someone forgets to update the map
        worksheets.extend(
            w for w in viewable_worksheets if w.viewable_by(username))
        return self._with_running_worksheets(worksheets)

    def user_wsts(self, username):
        r"""
        Returns all worksheets owned by `username`
        """
        if username == CFG.UN_PUB:
            return self._pub_wsts

        worksheets = self._storage.worksheets(username)
        return self._with_running_worksheets(worksheets)

    def user_viewable_wsts(self, username):
        if self.user_manager[username].is_admin:
            return self.all_wsts
        return self._user_viewable_wsts(username)

    def user_active_wsts(self, username):
        return [wst for wst in self.user_viewable_wsts(username)
                if wst.is_active(username)]

    def user_trashed_wsts(self, username):
        return [wst for wst in self.user_viewable_wsts(username)
                if wst.is_trashed(username)]

    def user_archived_wsts(self, username):
        return [wst for wst in self.user_viewable_wsts(username)
                if wst.is_archived(username)]

    def user_selected_wsts(self, user, typ="active", sort='last_edited',
                           reverse=False, search=None):
        if user == CFG.UN_PUB:
            W = self.user_wsts(CFG.UN_PUB)
        elif typ == "trash":
            W = self.user_trashed_wsts(user)
        elif typ == "active":
            W = self.user_active_wsts(user)
        else:  # typ must be archived
            W = self.user_archived_wsts(user)

        if search:
            W = [x for x in W if x.satisfies_search(search)]
        sort_worksheet_list(W, sort, reverse)  # changed W in place
        return W

    def filename_wst(self, filename):
        """
        Get the worksheet with the given filename.  If there is no
        such worksheet, raise a ``KeyError``.

        INPUT:

        - ``filename`` - a string

        OUTPUT:

        - a Worksheet instance
        """
        try:
            return self.__worksheets[filename]
        except KeyError:
            raise KeyError("No worksheet with filename '%s'" % filename)

    def id_wst(self, own_id):
        return self.filename_wst('{}/{}'.format(*own_id))

    def came_from_wst(self, wst):
        """
        Return a fresh copy of the worksheet that was published
        to get wst, if wst was
        published. Otherwise just return wst.

        OUTPUT: Worksheet

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: nb.came_from_wst(P) is W
            True
            sage: S = nb.publish_wst(W, 'admin')
            sage: nb.came_from_wst(P) is S
            False
            sage: nb.came_from_wst(P) is W
            True
        """
        # things can go wrong (especially with old migrated Sage notebook
        # servers!), but we don't want such problems to crash the notebook
        # server.
        try:
            return self.id_wst(wst.worksheet_that_was_published)
        except Exception:
            return wst

    @property
    def all_wsts(self):
        """
        We should only call this if the user is admin!
        """
        return [w for username in self.user_manager
                if username not in (CFG.UN_SAGE, CFG.UN_PUB)
                for w in self.user_wsts(username)]

    # Worksheet controller

    def new_id_number(self, username):
        """
        Find the next worksheet id for the given user.
        """
        u = self.user_manager[username]
        id_number = u['next_worksheet_id_number']
        if id_number == -1:  # need to initialize
            id_numbers = [w.id_number for w in self.user_wsts(username)]
            id_numbers.append(-1)
            id_number = max(id_numbers) + 1
        u['next_worksheet_id_number'] = id_number + 1
        return id_number

    def initialize_wst(self, src, W):
        r"""
        Initialize a new worksheet from a source worksheet.

        INPUT:

        - ``src`` - a Worksheet instance; the source

        - ``W`` - a new Worksheet instance; the target
        """
    # TODO: move to storage backend
        shutil.rmtree(W.cells_directory, ignore_errors=True)
        shutil.rmtree(W.data_directory, ignore_errors=True)
        shutil.rmtree(W.snapshot_directory, ignore_errors=True)
        shutil.copytree(src.cells_directory, W.cells_directory)
        shutil.copytree(src.data_directory, W.data_directory)
        makedirs(W.snapshot_directory)
        set_restrictive_permissions(W.snapshot_directory)

        W.edit_save(src.body)
        W.save()

    def worksheet(self, username, id_number=None, **kwargs):
        """
        Create a new worksheet with given id_number belonging to the
        user with given username, or return an already existing
        worksheet.  If id_number is None, creates a new worksheet
        using the next available new id_number for the given user.

        INPUT:

            - ``username`` -- string

            - ``id_number`` - nonnegative integer or None (default)
        """
        S = self._storage
        if id_number is None:
            id_number = self.new_id_number(username)
        try:
            W = S.load_worksheet(username, id_number)
        except ValueError:
            W = S.create_worksheet(username, id_number, **kwargs)
        self.__worksheets[W.filename] = W
        return W

    @cached_property()
    def scratch_wst(self):
        return self.create_wst('scratch', CFG.UN_SAGE)

    def create_wst(self, worksheet_name, username):
        if username != CFG.UN_PUB and self.user_manager[username].is_guest:
            raise ValueError("guests cannot create new worksheets")

        W = self.worksheet(username)

        W.system = self.user_manager[username]['default_system']
        W.name = worksheet_name
        self.save_worksheet(W)
        self.__worksheets[W.filename] = W

        return W

    def create_wst_from_history(self, name, username, maxlen=None):
        W = self.create_wst(name, username)
        W.edit_save(
            'Log Worksheet\n' + self.user_history_text(username, maxlen=None))
        return W

    def copy_wst(self, ws, owner):
        W = self.create_wst('default', owner)
        self.initialize_wst(ws, W)
        name = "Copy of %s" % ws.name
        W.name = name
        return W

    def delete_wst(self, filename):
        """
        Delete the given worksheet and remove its name from the worksheet
        list.  Raise a KeyError, if it is missing.

        INPUT:

        - ``filename`` - a string
        """
        try:
            W = self.__worksheets[filename]
        except KeyError:
            raise KeyError("Attempt to delete missing worksheet '%s'" %
                           filename)

        W.quit()
        shutil.rmtree(W.directory, ignore_errors=False)

    def empty_trash(self, username):
        """
        Empty the trash for the given user.

        INPUT:

        -  ``username`` - a string

        This empties the trash for the given user and cleans up all files
        associated with the worksheets that are in the trash.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Sage', owner='sage')
            sage: W._notebook = nb
            sage: W.move_to_trash('sage')
            sage: nb.empty_trash('sage')
        """
        X = self.user_viewable_wsts(username)
        for W in (ws for ws in X if ws.is_trashed(username)):
            W.delete_user(username)
            if W.owner is None:
                self.delete_wst(W.filename)

    def export_wst(self, worksheet_filename, output_filename, title=None):
        """
        Export a worksheet, creating a sws file on the file system.

        INPUT:

            -  ``worksheet_filename`` - a string e.g., 'username/id_number'

            -  ``output_filename`` - a string, e.g., 'worksheet.sws'

            - ``title`` - title to use for the exported worksheet (if
               None, just use current title)
        """
        S = self._storage
        W = self.filename_wst(worksheet_filename)
        S.save_worksheet(W)
        username = W.owner
        id_number = W.id_number
        S.export_worksheet(username, id_number, output_filename, title=title)

    def import_wst(self, filename, owner):
        r"""
        Import a worksheet with the given ``filename`` and set its
        ``owner``.  If the file extension is not recognized, raise a
        ValueError.

        INPUT:

        -  ``filename`` - a string

        -  ``owner`` - a string

        OUTPUT:

        -  ``worksheet`` - a newly created Worksheet instance

        EXAMPLES:

        We create a notebook and import a plain text worksheet
        into it.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('foo\n{{{\n2+3\n}}}')
            sage: W = nb.import_wst(name, 'admin')

        W is our newly-created worksheet, with the 2+3 cell in it::

            sage: W.name
            'foo'
            sage: W.cells
            [TextCell 0: foo, Cell 1: in=2+3, out=]
        """
        if not os.path.exists(filename):
            raise ValueError("no file %s" % filename)

        # Figure out the file extension
        ext = os.path.splitext(filename)[1]
        if ext.lower() == '.txt':
            # A plain text file with {{{'s that defines a worksheet
            # (no graphics).
            W = self._import_wst_txt(filename, owner)
        elif ext.lower() == '.sws':
            # An sws file (really a tar.bz2) which defines a worksheet with
            # graphics, etc.
            W = self._import_wst_sws(filename, owner)
        elif ext.lower() == '.html':
            # An html file, which should contain the static version of
            # a sage help page, as generated by Sphinx
            with open(filename) as f:
                html = f.read()

            cell_pattern = r"""{{{id=.*?///.*?}}}"""
            docutils_pattern = (r'<meta name="generator" content="Docutils '
                                r'\S+: http://docutils\.sourceforge\.net/" />')

            if re.search(cell_pattern, html, re.DOTALL) is not None:
                W = self._import_wst_txt(filename, owner)
            elif re.search(docutils_pattern, html) is not None:
                W = self._import_wst_docutils_html(filename, owner)
            else:
                # Sphinx web page or unrecognized html file.
                # We do the default behavior, i.e. we import as if it was
                # generated by Sphinx web page
                W = self._import_wst_html(filename, owner)
        elif ext.lower() == '.rst':
            # A ReStructuredText file
            W = self._import_wst_rst(filename, owner)
        else:
            # We only support txt, sws, html and rst files
            raise ValueError("unknown extension '%s'" % ext)
        self.__worksheets[W.filename] = W
        return W

    def _import_wst_txt(self, filename, owner):
        r"""
        Import a plain text file as a new worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .txt

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

        We write a plain text worksheet to a file and import it
        using this function.::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('foo\n{{{\na = 10\n}}}')
            sage: W = nb._import_wst_txt(name, 'admin'); W
            admin/0: [TextCell 0: foo, Cell 1: in=a = 10, out=]
        """
        with open(filename) as f:
            worksheet_txt = f.read()
        wst_name, _ = extract_text(worksheet_txt)
        worksheet = self.create_wst(wst_name, owner)
        worksheet.edit_save(worksheet_txt)
        return worksheet

    def _import_wst_sws(self, filename, username):
        r"""
        Import an sws format worksheet into this notebook as a new
        worksheet.

        INPUT:

        - ``filename`` - a string; a filename that ends in .sws;
           internally it must be a tar'd bz2'd file.

        - ``username`` - a string

        OUTPUT:

        - a new Worksheet instance

        EXAMPLES:

        We create a notebook, then make a worksheet from a plain text
        file first.::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('{{{id=0\n2+3\n}}}')
            sage: W = nb.import_wst(name, 'admin')
            sage: W.filename
            'admin/0'
            sage: sorted([w.filename for w in nb.all_wsts])
            ['admin/0']

        We then export the worksheet to an sws file.::

            sage: sws = os.path.join(tmp_dir(), 'tmp.sws')
            sage: nb.export_wst(W.filename, sws)

        Now we import the sws.::

            sage: W = nb._import_wst_sws(sws, 'admin')
            sage: nb._Notebook__worksheets[W.filename] = W

        Yes, it's there now (as a new worksheet)::

            sage: sorted([w.filename for w in nb.get_all_worksheets()])
            ['admin/0', 'admin/1']
        """
        id_number = self.new_id_number(username)
        worksheet = self._storage.import_worksheet(
            username, id_number, filename)

        return worksheet

    def _import_wst_html(self, filename, owner):
        r"""
        Import a static html help page generated by Sphinx as a new
        worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .html

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

        We write a plain text worksheet to a file and import it
        using this function.::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: name = tmp_filename() + '.html'
            sage: fd = open(name,'w')
            sage: fd.write(''.join([
            ....: '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional',
            ....: '//EN"\n',
            ....: '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"'
            ....: '>',
            ....: '\n',
            ....: '\n',
            ....: '<html xmlns="http://www.w3.org/1999/xhtml">\n',
            ....: '  <head>\n',
            ....: '   <title>Test notebook &mdash; test</title>\n',
            ....: ' </head>\n',
            ....: '  <body>\n',
            ....: '   <div class="document">\n',
            ....: '      <div class="documentwrapper">\n',
            ....: '        <div class="bodywrapper">\n',
            ....: '          <div class="body">\n',
            ....: '<p>Here are some computations:</p>\n',
            ....: '\n',
            ....: '<div class="highlight-python"><div class="highlight"><pre>'
            ....: '\n',
            ....: '<span class="gp">sage',
            ....: ': </span><span class="mi">1</span><span class="o">+</span>',
            ....: '<span class="mi">1</span>\n',
            ....: '<span class="go">2</span>\n',
            ....: '</pre></div></div>\n',
            ....: '\n',
            ....: '</div></div></div></div>\n',
            ....: '</body></html>']))
            sage: fd.close()
            sage: W = nb._import_wst_html(name, 'admin')
            sage: W.name
            'Test notebook -- test'
            sage: W.owner
            'admin'
            sage: W.cells
            [TextCell 1: <div class="document">
                  <div class="documentwrapper">
                    <div class="bodywrapper">
                      <div class="body">
            <p>Here are some computations:</p>
            <BLANKLINE>
            <div class="highlight-python">, Cell 0: in=1+1, out=
            2, TextCell 2: </div>
            <BLANKLINE>
            </div></div></div></div>]
            sage: cell = W.cells[1]
            sage: cell.input
            '1+1'
            sage: cell.output_text()
            '<pre class="shrunk">2</pre>'
        """
        # Inspired from sagenb.notebook.twist.WorksheetFile.render
        doc_page_html = open(filename).read()
        # FIXME: does SphinxHTMLProcessor raise an appropriate message
        # if the html file does not contain a Sphinx HTML page?
        doc_page = SphinxHTMLProcessor().process_doc_html(doc_page_html)

        title = extract_title(doc_page_html).replace('&mdash;', '--')

        worksheet = self.create_wst(title, owner)
        worksheet.edit_save(doc_page)

        # FIXME: An extra compute cell is always added to the end.
        # Pop it off.
        cells = worksheet.cells
        cells.pop()

        return worksheet

    def _import_wst_rst(self, filename, owner):
        r"""
        Import a ReStructuredText file as a new worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .rst

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

            sage: sprompt = 'sage' + ':'
            sage: rst = '\n'.join(['=============',
            ....:       'Test Notebook',
            ....:       '=============',
            ....:       '',
            ....:       'Let\'s do some computations::',
            ....:       '',
            ....:       '    %s 2+2' % sprompt,
            ....:       '    4',
            ....:       '',
            ....:       '::',
            ....:       '',
            ....:       '    %s x^2' % sprompt,
            ....:       '    x^2'])
            sage: name = tmp_filename() + '.rst'
            sage: fd = open(name,'w')
            sage: fd.write(rst)
            sage: fd.close()
            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb._import_wst_rst(name, 'admin')
            sage: W.name
            'Test Notebook'
            sage: W.owner
            'admin'
            sage: W.cells
            [TextCell 2: <h1 class="title">Test Notebook</h1>
            <BLANKLINE>
            <p>Let's do some computations:</p>, Cell 0: in=2+2, out=
            4, Cell 1: in=x^2, out=
            x^2]
            sage: cell = W.cells[1]
            sage: cell.input
            '2+2'
            sage: cell.output_text()
            '<pre class="shrunk">4</pre>'

        """
        rst = open(filename).read()

        # docutils removes the backslashes if they are not escaped This is
        # not practical because backslashes are almost never escaped in
        # Sage docstrings written in ReST.  So if the user wants the
        # backslashes to be escaped automatically, he adds the comment
        # ".. escape-backslashes" in the input file
        if re.search(
                r'^\.\.[ \t]+escape-backslashes', rst,
                re.MULTILINE) is not None:
            rst = rst.replace('\\', '\\\\')

        # Do the translation rst -> html (using docutils)
        D = publish_parts(rst, writer_name='html')
        title = D['title']
        html = D['whole']

        # Do the translation html -> txt
        translator = docutilsHTMLProcessor()
        worksheet_txt = translator.process_doc_html(html)

        # Create worksheet
        worksheet = self.create_wst(title, owner)
        worksheet.edit_save(worksheet_txt)

        return worksheet

    def _import_wst_docutils_html(self, filename, owner):
        r"""
        Import a static html help page generated by docutils as a new
        worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .html

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

            sage: sprompt = 'sage' + ':'
            sage: rst = '\n'.join(['=============',
            ....:       'Test Notebook',
            ....:       '=============',
            ....:       '',
            ....:       'Let\'s do some computations::',
            ....:       '',
            ....:       '    %s 2+2' % sprompt,
            ....:       '    4',
            ....:       '',
            ....:       '::',
            ....:       '',
            ....:       '    %s x^2' % sprompt,
            ....:       '    x^2'])
            sage: from docutils.core import publish_string
            sage: html = publish_string(rst, writer_name='html')
            sage: name = tmp_filename() + '.html'
            sage: fd = open(name,'w')
            sage: fd.write(html)
            sage: fd.close()
            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir()
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb._import_wst_docutils_html(name, 'admin')
            sage: W.name
            'Test Notebook'
            sage: W.owner
            'admin'
            sage: W.cells
            [TextCell 2: <h1 class="title">Test Notebook</h1>
            <BLANKLINE>
            <p>Let's do some computations:</p>, Cell 0: in=2+2, out=
            4, Cell 1: in=x^2, out=
            x^2]
            sage: cell = W.cells[1]
            sage: cell.input
            '2+2'
            sage: cell.output_text()
            '<pre class="shrunk">4</pre>'

        """
        html = open(filename).read()

        # Do the translation html -> txt
        translator = docutilsHTMLProcessor()
        worksheet_txt = translator.process_doc_html(html)

        # Extract title
        title, _ = extract_text(worksheet_txt)
        if title.startswith('<h1 class="title">'):
            title = title[18:]
        if title.endswith('</h1>'):
            title = title[:-5]

        # Create worksheet
        worksheet = self.create_wst(title, owner)
        worksheet.edit_save(worksheet_txt)

        return worksheet

    def publish_wst(self, worksheet, username):
        r"""
        Publish a user's worksheet.  This creates a new worksheet in
        the 'pub' directory with the same contents as ``worksheet``.

        INPUT:

        - ``worksheet`` - an instance of Worksheet

        - ``username`` - a string

        OUTPUT:

        - a new or existing published instance of Worksheet

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir()
            sage: nb.user_manager.add_user('Mark','password','',force=True)
            sage: W = nb.create_wst('First steps', owner='Mark')
            sage: nb.user_manager.create_default_users('password')
            sage: nb.publish_wst(nb.filename_wst(
                'Mark/0'), 'Mark')
            pub/0: [Cell 1: in=, out=]
        """
        W = None

        # Reuse an existing published version
        for X in self.user_wsts(CFG.UN_PUB):
            if self.came_from_wst(X) == worksheet:
                W = X

        # Or create a new one.
        if W is None:
            W = self.create_wst(worksheet.name, CFG.UN_PUB)

        # Copy cells, output, data, etc.
        self.initialize_wst(worksheet, W)

        # Update metadata.
        W.worksheet_that_was_published = worksheet
        W.move_to_archive(username)
        worksheet.published_id_number = W.id_number
        W.record_edit(username)
        W.name = worksheet.name
        self.__worksheets[W.filename] = W
        W.save()
        return W

    def unpublish_wst(self, worksheet):
        self.delete_wst(worksheet.published_filename)
        worksheet.published_id_number = None

    def save_worksheet(self, W, conf_only=False):
        self._storage.save_worksheet(W, conf_only=conf_only)

    def delete_doc_browser_worksheets(self):
        """Not used"""
        for w in self.user_wsts(CFG.UN_SAGE):
            if w.name.startswith('doc_browser'):
                self.delete_wst(w.filename)

    # Information about the pool of worksheet compute servers

    def server_pool(self):
        return self.conf['server_pool']

    def set_server_pool(self, servers):
        self.conf['server_pool'] = servers

    def get_ulimit(self):
        try:
            return self.__ulimit
        except AttributeError:
            self.__ulimit = ''
            return ''

    def set_ulimit(self, ulimit):
        self.__ulimit = ulimit

    def new_worksheet_process(self, init_code=None):
        """
        Return a new worksheet process object with parameters determined by
        configuration of this notebook server.
        """
        ulimit = self.get_ulimit()
        # We have to parse the ulimit format to our ProcessLimits.
        # The typical format is.
        # '-u 400 -v 1024 -t 3600'
        #    -u --> max_processes
        #    -v --> max_vmem in Mib (a minimum of 1024 is needed)
        #    -t -- > max_cputime in seconds

        tbl = {'v': None, 'u': None, 't': None}
        for x in ulimit.split('-'):
            for k in tbl:
                if x.startswith(k):
                    tbl[k] = int(x.split()[1].strip())
        if tbl['v'] is not None:
            tbl['v'] = (1024 if tbl['v'] < 1024 else tbl['v'])*1024*1024
        return sage(
            sage=CFG.SAGE_PATH,
            server_pool=self.server_pool(),
            max_vmem=tbl['v'],
            max_cputime=tbl['t'],
            max_processes=tbl['u'],
            init_code='\n'.join((init_code, "DIR = '{}'".format(self.DIR))))

    # Computing control

    def quit(self):
        for W in tuple(self.__worksheets.values()):
            W.quit()

    def update_worksheet_processes(self):
        update_worksheets()

    def quit_idle_worksheet_processes(self):
        timeout = self.conf['idle_timeout']
        doc_timeout = self.conf['doc_timeout']

        for W in self.__worksheets.values():
            if W.compute_process_has_been_started():
                if W.docbrowser:
                    W.quit_if_idle(doc_timeout)
                else:
                    W.quit_if_idle(timeout)

    def quit_worksheet(self, W):
        try:
            del self.__worksheets[W.filename]
        except KeyError:
            pass


def load_notebook(dir, interface=None, port=None, secure=None,
                  user_manager=None):
    """
    Load and return a notebook from a given directory.  Create a new
    one in that directory, if one isn't already there.

    INPUT:

    -  ``dir`` - a string that defines a directory name

    -  ``interface`` - the address of the interface the server listens at

    -  ``port`` - the port the server listens on

    -  ``secure`` - whether the notebook is secure

    OUTPUT:

    - a Notebook instance
    """
    dir = make_path_relative(dir)
    nb = Notebook(dir)
    nb.interface = interface
    nb.port = port
    nb.secure = secure

    # Install this copy of the notebook in config as *the*
    # global notebook object used for computations.  This is
    # mainly to avoid circular references, etc.  This also means
    # only one notebook can actually be used at any point.
    # TODO: remove this. Previously in notebook.misc
    CFG.notebook = nb

    return nb
