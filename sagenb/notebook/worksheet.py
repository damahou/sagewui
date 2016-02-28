# -*- coding: utf-8 -*-
r"""
A Worksheet

A worksheet is embedded in a web page that is served by the Sage
server. It is a linearly-ordered collections of numbered cells,
where a cell is a single input/output block.

The worksheet module is responsible for running calculations in a
worksheet, spawning Sage processes that do all of the actual work
and are controlled via pexpect, and reporting on results of
calculations. The state of the cells in a worksheet is stored on
the file system (not in the notebook pickle sobj).

AUTHORS:

 - William Stein
"""

###########################################################################
#       Copyright (C) 2006-2009 William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
###########################################################################

# Import standard Python libraries that we will use below
from __future__ import absolute_import

import bz2
import calendar
import copy
import os
import re
import shutil
import time
from time import strftime

from flask.ext.babel import gettext

from .. import config
# Imports specifically relevant to the sage notebook
from .cell import Cell, TextCell
from ..config import INITIAL_NUM_CELLS
from ..config import WARN_THRESHOLD
from ..config import UN_PUB
from ..util import walltime
from ..util import ignore_nonexistent_files
from ..util import next_available_id
from ..util import set_restrictive_permissions
from ..util import unicode_str
from ..util.templates import format_completions_as_html
from ..util.templates import prettify_time_ago
from ..util.text import ignore_prompts_and_output
from ..util.text import extract_text_before_first_compute_cell
from ..util.text import extract_first_compute_cell
from ..util.text import split_search_string_into_keywords
from ..util.text import extract_text

_ = gettext

# Integers that define which folder this worksheet is in relative to a
# given user.
WS_ARCHIVED = 0
WS_ACTIVE = 1
WS_TRASH = 2


all_worksheet_processes = []


def update_worksheets():
    """
    Iterate through and "update" all the worksheets.  This is needed
    for things like wall timeouts.
    """
    for S in all_worksheet_processes:
        S.update()


def Worksheet_from_basic(obj, notebook_worksheet_directory):
    """
    INPUT:

        - ``obj`` -- a dictionary (a basic Python objet) from which a
                     worksheet can be reconstructed.

        - ``notebook_worksheet_directory`` - string; the directory in
           which the notebook object that contains this worksheet
           stores worksheets, i.e., nb.worksheet_directory().

    OUTPUT:

        - a worksheet

    EXAMPLES::

            sage: import sagenb.notebook.worksheet
            sage: W = sagenb.notebook.worksheet.Worksheet(
                'test', 0, tmp_dir(), system='gap', owner='sageuser',
                pretty_print=True, auto_publish=True)
            sage: _=W.new_cell_after(0); B = W.basic()
            sage: W0 = sagenb.notebook.worksheet.Worksheet_from_basic(
                B, tmp_dir())
            sage: W0.basic() == B
            True
    """
    W = Worksheet()
    W.reconstruct_from_basic(obj, notebook_worksheet_directory)
    return W


class Worksheet(object):
    _last_identifier = re.compile(r'[a-zA-Z0-9._]*$')

    def __init__(self,
                 name=None, id_number=-1,
                 notebook_worksheet_directory=None, system='sage',
                 owner=None, pretty_print=False,
                 auto_publish=False, create_directories=True, live_3D=False):
        ur"""
        Create and initialize a new worksheet.

        INPUT:

        -  ``name`` - string; the name of this worksheet

        - ``id_number`` - Integer; name of the directory in which the
           worksheet's data is stored

        -  ``notebook_worksheet_directory`` - string; the
           directory in which the notebook object that contains this worksheet
           stores worksheets, i.e., nb.worksheet_directory().

        -  ``system`` - string; 'sage', 'gp', 'singular', etc.
           - the math software system in which all code is evaluated by
           default

        -  ``owner`` - string; username of the owner of this
           worksheet

        -  ``pretty_print`` - bool (default: False); whether
           all output is pretty printed by default.

        - ``create_directories`` -- bool (default: True): if True,
          creates various files and directories where data will be
          stored.  This option is here only for the
          migrate_old_notebook method in notebook.py
        -  ``live_3D`` - bool (default: False); whether 3-D plots should
           be loaded live (interactive). Too many live plots may make a
           worksheet unresponsive because of the javascript load.

        EXAMPLES: We test the constructor via an indirect doctest::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: import sagenb.notebook.misc
            sage: sagenb.notebook.misc.notebook = nb
            sage: W = nb.create_wst(
                'Test with unicode ěščřžýáíéďĎ', 'admin')
            sage: W
            admin/0: [Cell 1: in=, out=]
        """
        # Record the basic properties of the worksheet
        self.__id_number = int(id_number)  # property readonly
        self.owner = owner
        self.name = name  # property
        self.system = system
        self.__pretty_print = pretty_print  # property
        self.live_3D = live_3D
        self.auto_publish = auto_publish
        self.last_change = (self.owner, time.time())
        self.__saved_by_info = {}  # property readonly
        self.__collaborators = []  # property
        self.__viewers = []  # property readonly
        self.published_id_number = None
        self.__worksheet_that_was_published = (self.owner,
                                               self.id_number)  # property
        self.__ratings = []  # property readonly

        # State variables
        # state sequence number, used for sync
        self.__state_number = 0  # property readonly + increase()
        # Initialize the cell id counter.
        self.__next_id = 0
        if name is None:
            # A fresh worksheet
            self.clear()
            return
        # set the directory in which the worksheet files will be stored.  We
        # also add the hash of the name, since the cleaned name loses info,
        # e.g., it could be all _'s if all characters are funny.
        self.__filename = os.path.join(owner, str(id_number))
        self.__dir = os.path.join(notebook_worksheet_directory, str(id_number))

        if create_directories:
            self.create_directories()
        self.clear()

    def increase_state_number(self):
        if not self.is_published() and not self.docbrowser:
            self.__state_number += 1

    @property
    def state_number(self):
        if self.is_published() or self.docbrowser:
            return 0
        return self.__state_number

    def create_directories(self):
        # creating directories should be a function of the storage backend, not
        # here
        if not os.path.exists(self.__dir):
            os.makedirs(self.__dir)
            set_restrictive_permissions(self.__dir, allow_execute=True)
            set_restrictive_permissions(self.snapshot_directory())
            set_restrictive_permissions(self.cells_directory())

    @property
    def id_number(self):
        """
        Return the id number of this worksheet, which is an integer.

        EXAMPLES::

            sage: from sagenb.notebook.worksheet import Worksheet
            sage: W = Worksheet('test', 2, tmp_dir(), owner='sageuser')
            sage: W.id_number
            2
            sage: type(W.id_number)
            <type 'int'>
        """
        return self.__id_number

    def basic(self):
        """
        Output a dictionary of basic Python objects that defines the
        configuration of this worksheet, except the actual cells and
        the data files in the DATA directory and images and other data
        in the individual cell directories.

        The fields of the dictionary are:
            'id_number'
                Basic identification
            'name'
                Basic identification

            'owner'
                permission: who can look at the worksheet
            'system'
                default type of computation system that evaluates cells
            'viewers'
                permission: who can look at the worksheet
            'collaborators'
                permission: who can look at the worksheet

            'published_id_number'
                publishing worksheets (am I published?); auto-publish me?
                If this worksheet is published, then the published_id_number is
                the id of the published version of this worksheet. Otherwise,
                it is None.
            'worksheet_that_was_published'
                If this is a published worksheet, then ws_pub is a 2-tuple
                ('username', id_number) of a non-published worksheet.
                Otherwise ws_pub is None.
            'auto_publish'
                Whether or not this worksheet should automatically be
                republished when changed.
            'published'
            'published_time'

            'pretty_print'
                Appearance
                default
            'live_3D'
                Whether to load 3-D live.  Should only be set to
                true by the user as worksheets with more than 1 or 2
                live (interactive) 3-D plots may bog down because of
                javascript overload.
            'ratings'
                what other users think of this worksheet
                triples
                      (username, rating, comment)
            'saved_by_info'
                #???
            'tags'
                dictionary mapping usernames to list of tags that
                reflect what the tages are for that user.  A tag can be
                an integer
                  0,1,2 (=WS_ARCHIVED,WS_ACTIVE,WS_TRASH),
                or a string (not yet supported).
                This is used for now to fill in the __user_views.
            'last_change'
                information about when this worksheet was last changed,
                and by whom
                    last_change = ('username', time.time())
            'last_change_pretty'
            'filename'
            'running'
            'attached_data_files'

        EXAMPLES::

            sage: import sagenb.notebook.worksheet
            sage: W = sagenb.notebook.worksheet.Worksheet(
                'test', 0, tmp_dir(), owner='sage')
            sage: sorted((W.basic().items()))
            [('auto_publish', False), ('collaborators', []),
             ('id_number', 0), ('last_change', ('sage', ...)),
             ('live_3D', False), ('name', u'test'), ('owner', 'sage'),
             ('pretty_print', False), ('published_id_number', None),
             ('ratings', []), ('saved_by_info', {}), ('system', None),
             ('tags', {'sage': [1]}), ('viewers', []),
             ('worksheet_that_was_published', ('sage', 0))]
        """
        d = {
            'id_number': self.id_number,
            'owner': self.owner,
            'name': self.name,
            'system': self.system,
            'pretty_print': self.pretty_print,
            'live_3D': self.live_3D,
            'auto_publish': self.auto_publish,
            'last_change': self.last_change,
            'saved_by_info': self.saved_by_info,
            'tags': self.tags(),
            'collaborators': self.collaborators,
            'viewers': self.viewers,
            'published_id_number': self.published_id_number,
            'worksheet_that_was_published':
            self.worksheet_that_was_published,
            'ratings': self.ratings,
            # New UI
            'last_change_pretty': prettify_time_ago(
                time.time() - self.last_change[1]),
            'filename': self.filename(),
            'running': self.compute_process_has_been_started(),
            'attached_data_files': self.attached_data_files(),
            'published': self.has_published_version(),
            }
        if d['published']:
            d['published_time'] = strftime(
                "%B %d, %Y %I:%M %p", self.published_version().date_edited)
        # New UI end

        return d

    def reconstruct_from_basic(self, obj, notebook_worksheet_directory=None):
        """
        Reconstruct as much of the worksheet's configuration as
        possible from the properties that happen to be set in the
        basic dictionary obj.

        INPUT:

            - ``obj`` -- a dictionary of basic Python objects

            - ``notebook_worksheet_directory`` -- must be given if
              ``id_number`` is a key of obj; otherwise not.

        EXAMPLES::

            sage: import sagenb.notebook.worksheet
            sage: W = sagenb.notebook.worksheet.Worksheet(
                'test', 0, tmp_dir(), system='gap', owner='sageuser',
                pretty_print=True, auto_publish=True)
            sage: W.new_cell_after(0)
            Cell 1: in=, out=
            sage: b = W.basic()
            sage: W0 = sagenb.notebook.worksheet.Worksheet()
            sage: W0.reconstruct_from_basic(b, tmp_dir())
            sage: W0.basic() == W.basic()
            True
        """
        try:
            del self.__cells
        except AttributeError:
            pass
        for key, value in obj.iteritems():
            if key == 'name':
                if repr(value) == '<_LazyString broken>':
                    value = ''
                self.name = value
            elif key == 'id_number':
                self.__id_number = value
                if 'owner' in obj:
                    owner = obj['owner']
                    self.owner = owner
                    filename = os.path.join(owner, str(value))
                    self.__filename = filename
                    self.__dir = os.path.join(
                        notebook_worksheet_directory, str(value))
            elif key in ['system', 'owner', 'viewers', 'collaborators',
                         'pretty_print', 'ratings', 'live_3D']:
                # ugly
                setattr(self, '_Worksheet__' + key, value)
            elif key == 'auto_publish':
                self.auto_publish = value
            elif key == 'tags':
                self.set_tags(value)
            elif key == 'last_change':
                self.last_change = value
            elif key == 'published_id_number' and value is not None:
                self.published_id_number = value
            elif key == 'worksheet_that_was_published':
                self.worksheet_that_was_published = value
        self.create_directories()

    def __cmp__(self, other):
        """
        We compare two worksheets.

        INPUT:

        -  ``self, other`` - worksheets

        OUTPUT:

        -  ``-1,0,1`` - comparison is on the underlying
           file names.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir(
                ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W2 = nb.create_wst('test2', 'admin')
            sage: W1 = nb.create_wst('test1', 'admin')
            sage: cmp(W1, W2)
            1
            sage: cmp(W2, W1)
            -1
        """
        try:
            return cmp(self.filename(), other.filename())
        except AttributeError:
            return cmp(type(self), type(other))

    def __repr__(self):
        r"""
        Return string representation of this worksheet, which is simply the
        string representation of the underlying list of cells.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('test1', 'admin')
            sage: W.__repr__()
            'admin/0: [Cell 1: in=, out=]'
            sage: W.edit_save(
                '{{{\n2+3\n///\n5\n}}}\n{{{id=10|\n2+8\n///\n10\n}}}')
            sage: W.__repr__()
            'admin/0: [Cell 0: in=2+3, out=\n5, Cell 10: in=2+8, out=\n10]'
        """
        return '%s/%s: %s' % (self.owner, self.id_number, self.cell_list())

    def __len__(self):
        r"""
        Return the number of cells in this worksheet.

        OUTPUT: int

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('test1', 'admin')
            sage: len(W)
            1
            sage: W.edit_save(
                '{{{\n2+3\n///\n5\n}}}\n{{{id=10|\n2+8\n///\n10\n}}}')
            sage: len(W)
            2
        """
        return len(self.cell_list())

    @property
    def worksheet_html_filename(self):
        """
        Return path to the underlying plane text file that defines the
        worksheet.
        """
        return os.path.join(self.__dir, 'worksheet.html')

    @property
    def download_name(self):
        """
        Return the download name of this worksheet.
        """
        return os.path.split(self.name)[-1]

    @property
    def docbrowser(self):
        """
        Return True if this is a docbrowser worksheet.

        OUTPUT: bool

        EXAMPLES: We first create a standard worksheet for which docbrowser
        is of course False::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('test1', 'admin')
            sage: W.docbrowser
            False

        We create a worksheet for which docbrowser is True::

            sage: W = nb.create_wst('doc_browser_0', '_sage_')
            sage: W.docbrowser
            True
        """
        return self.owner == '_sage_'

    # Basic properties

    @property
    def collaborators(self):
        """
        Return a (reference to the) list of the collaborators who can also
        view and modify this worksheet.

        OUTPUT: list

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('test1', 'admin')
            sage: C = W.collaborators; C
            []
            sage: C.append('sage')
            sage: W.collaborators
            ['sage']
        """
        return self.__collaborators

    @collaborators.setter
    def collaborators(self, v):
        """
        Set the list of collaborators to those listed in the list v of
        strings.

        INPUT:

        -  ``v`` - a list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: nb.user_manager.add_user(
                'hilbert','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('test1', 'admin')
            sage: W.set_collaborators = ['sage', 'admin', 'hilbert', 'sage']

        Note that repeats are not added multiple times and admin - the
        owner - isn't added::

            sage: W.collaborators
            ['hilbert', 'sage']
        """
        collaborators = set(v).difference(self.owner)
        self.__collaborators = sorted(collaborators)

    @property
    def viewers(self):
        """
        Return list of viewers of this worksheet.

        OUTPUT:

        -  ``list`` - of string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: nb.user_manager.add_user(
                'hilbert','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('test1', 'admin')
            sage: W.add_viewer('hilbert')
            sage: W.viewers
            ['hilbert']
            sage: W.add_viewer('sage')
            sage: W.viewers
            ['hilbert', 'sage']
        """
        return self.__viewers

    @property
    def name(self, username=None):
        ur"""
        Return the name of this worksheet.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.name
            u'A Test Worksheet'
            sage: W = nb.create_wst('ěščřžýáíéďĎ', 'admin')
            sage: W.name
            u'\u011b\u0161\u010d\u0159\u017e\xfd\xe1\xed\xe9\u010f\u010e'
        """
        return self.__name

    @name.setter
    def name(self, name):
        """
        Set the name of this worksheet.

        INPUT:

        -  ``name`` - string

        EXAMPLES: We create a worksheet and change the name::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.name = 'A renamed worksheet'
            sage: W.name
            u'A renamed worksheet'
        """
        if not name:
            name = gettext('Untitled')
        self.__name = unicode_str(name)

    def filename(self):
        """
        Return the filename (really directory) where the files associated
        to this worksheet are stored.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.filename()
            'admin/0'
            sage: os.path.isdir(os.path.join(nb.dir, 'home', W.filename()))
            True
        """
        return self.__filename

    def filename_without_owner(self):
        """
        Return the part of the worksheet filename after the last /, i.e.,
        without any information about the owner of this worksheet.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.filename_without_owner()
            '0'
            sage: W.filename()
            'admin/0'
        """
        return os.path.split(self.__filename)[-1]

    def directory(self):
        """
        Return the full path to the directory where this worksheet is
        stored.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.directory()
            '.../home/admin/0'
        """
        return self.__dir

    def data_directory(self):
        """
        Return path to directory where worksheet data is stored.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.data_directory()
            '.../home/admin/0/data'
        """
        d = os.path.join(self.directory(), 'data')
        if not os.path.exists(d):
            os.makedirs(d)
        return d

    def attached_data_files(self):
        """
        Return a list of the file names of files in the worksheet data
        directory.

        OUTPUT: list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.attached_data_files()
            []
            sage: open('%s/foo.data'%W.data_directory(),'w').close()
            sage: W.attached_data_files()
            ['foo.data']
        """
        D = self.data_directory()
        if not os.path.exists(D):
            return []
        return os.listdir(D)

    def cells_directory(self):
        """
        Return the directory in which the cells of this worksheet are
        evaluated.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.cells_directory()
            '.../home/admin/0/cells'
        """
        path = os.path.join(self.directory(), 'cells')
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def notebook(self):
        """
        Return the notebook that contains this worksheet.

        OUTPUT: a Notebook object.

        .. note::

           This really returns the Notebook object that is set as a
           global variable of the misc module.  This is done *even*
           in the Flask version of the notebook as it is set in
           func:`sagenb.notebook.notebook.load_notebook`.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.notebook()
            <...sagenb.notebook.notebook.Notebook...>
            sage: W.notebook() is sagenb.notebook.misc.notebook
            True
        """
        if not hasattr(self, '_notebook'):
            self._notebook = config.notebook
        return self._notebook

    def save(self, conf_only=False):
        self.notebook().save_worksheet(self, conf_only=conf_only)

    @property
    def system_index(self):
        """
        Return the index of the current system into the Notebook's
        list of systems.  If the current system isn't in the list,
        then change to the default system.  This can happen if, e.g.,
        the list changes, e.g., when changing from a notebook with
        Sage installed to running a server from the same directory
        without Sage installed.   We might as well support this.

        OUTPUT: integer
        """
        system_names = self.notebook().system_names
        try:
            return system_names.index(self.system)
        except ValueError:
            self.system = system_names[0]
            return 0

    @property
    def pretty_print(self):
        """
        Return True if output should be pretty printed by default.

        OUTPUT:

        -  ``bool`` - True of False

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.pretty_print
            False
            sage: W.pretty_print = True
            sage: W.pretty_print
            True
            sage: W.quit()
            sage: nb.delete()
        """
        return self.__pretty_print

    @pretty_print.setter
    def pretty_print(self, check):
        """
        Set whether or not output should be pretty printed by default.

        INPUT:

        -  ``check`` - string (default: 'false'); either 'true'
           or 'false'.

        .. note::

           The reason the input is a string and lower case instead of
           a Python bool is because this gets called indirectly from
           JavaScript. (And, Jason Grout wrote this and didn't realize
           how unpythonic this design is - it should be redone to use
           True/False.)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('A Test Worksheet', 'admin')
            sage: W.set_pretty_print = False
            sage: W.pretty_print
            False
            sage: W.set_pretty_print = True
            sage: W.pretty_print
            True
            sage: W.quit()
            sage: nb.delete()
        """
        self.__pretty_print = check
        self.eval_asap_no_output("pretty_print_default(%r)" % check)

    # Publication

    @property
    def worksheet_that_was_published(self):
        return self.__worksheet_that_was_published

    @worksheet_that_was_published.setter
    def worksheet_that_was_published(self, W):
        """
        Set the owner and id_number of the worksheet that was
        published to get self.

        INPUT:

            - ``W`` -- worksheet or 2-tuple ('owner', id_number)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: P = nb.publish_wst(W, 'admin')
            sage: nb.came_from_wst(P) is W
            True

        We fake things and make it look like P published itself::

            sage: P.worksheet_that_was_published = P
            sage: nb.came_from_wst(P) is P
            True
        """
        self.__worksheet_that_was_published = (W if isinstance(W, tuple)
                                               else (W.owner, W.id_number))

    def is_published(self):
        """
        Return True if this worksheet is a published worksheet.

        OUTPUT:

        -  ``bool`` - whether or not owner is 'pub'

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.is_published()
            False
            sage: W.owner = 'pub'
            sage: W.is_published()
            True
        """
        return self.owner == UN_PUB

    def publisher(self):
        """
        Return username of user that published this worksheet.

        OUTPUT: string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: S = nb.publish_wst(W, 'admin')
            sage: S.publisher()
            'admin'
        """
        return self.worksheet_that_was_published[0]

    def is_publisher(self, username):
        """
        Return True if username is the username of the publisher of this
        worksheet, assuming this worksheet was published.

        INPUT:

        -  ``username`` - string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: P = nb.publish_wst(W, 'admin')
            sage: P.is_publisher('hearst')
            False
            sage: P.is_publisher('admin')
            True
        """
        return self.publisher() == username

    def has_published_version(self):
        """
        Return True if there is a published version of this worksheet.

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: P = nb.publish_wst(W, 'admin')
            sage: P.has_published_version()
            False
            sage: W.has_published_version()
            True
        """
        return self.published_id_number is not None

    @property
    def published_filename(self):
        if self.published_id_number is None:
            return
        return os.path.join(UN_PUB, str(self.published_id_number))

    def published_version(self):
        """
        If this worksheet was published, return the published version of
        this worksheet. Otherwise, raise a ValueError.

        OUTPUT: a worksheet (or raise a ValueError)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: P = nb.publish_wst(W, 'admin')
            sage: W.published_version() is P
            True
        """
        if self.published_id_number is None:
            raise ValueError("no published version")

        filename = self.published_filename
        try:
            W = self.notebook().filename_wst(filename)
        except KeyError:
            self.__published_id_number = None
            raise ValueError

        return W

    def rate(self, x, comment, username):
        """
        Set the rating on this worksheet by the given user to x and also
        set the given comment.

        INPUT:

        -  ``x`` - integer

        -  ``comment`` - string

        -  ``username`` - string

        EXAMPLES: We create a worksheet and rate it, then look at the
        ratings.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.rate(3, 'this is great', 'hilbert')
            sage: W.ratings
            [('hilbert', 3, 'this is great')]

        Note that only the last rating by a user counts::

            sage: W.rate(1, 'this lacks content', 'riemann')
            sage: W.rate(0, 'this lacks content', 'riemann')
            sage: W.ratings
            [('hilbert', 3, 'this is great'),
             ('riemann', 0, 'this lacks content')]
        """
        r = self.ratings
        x = int(x)
        for i in range(len(r)):
            if r[i][0] == username:
                r[i] = (username, x, comment)
                return
        else:
            r.append((username, x, comment))

    def is_rater(self, username):
        """
        Return True is the user with given username has rated this
        worksheet.

        INPUT:

        -  ``username`` - string

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.rate(0, 'this lacks content', 'riemann')
            sage: W.is_rater('admin')
            False
            sage: W.is_rater('riemann')
            True
        """
        try:
            return username in [x[0] for x in self.ratings]
        except TypeError:
            return False

    @property
    def ratings(self):
        """
        Return all the ratings of this worksheet.

        OUTPUT:

        -  ``list`` - a reference to the list of ratings.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.ratings
            []
            sage: W.rate(0, 'this lacks content', 'riemann')
            sage: W.rate(3, 'this is great', 'hilbert')
            sage: W.ratings
            [('riemann', 0, 'this lacks content'),
             ('hilbert', 3, 'this is great')]
        """
        return self.__ratings

    def rating(self):
        """
        Return overall average rating of self.

        OUTPUT: float or the int -1 to mean "not rated"

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.rating()
            -1
            sage: W.rate(0, 'this lacks content', 'riemann')
            sage: W.rate(3, 'this is great', 'hilbert')
            sage: W.rating()
            1.5
        """
        r = [x[1] for x in self.ratings]
        if len(r) == 0:
            rating = -1    # means "not rated"
        else:
            rating = float(sum(r)) / float(len(r))
        return rating

    # Active, trash can and archive

    def everyone_has_deleted_this_worksheet(self):
        """
        Return True if all users have deleted this worksheet, so we know we
        can safely purge it from disk.

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.everyone_has_deleted_this_worksheet()
            False
            sage: W.move_to_trash('admin')
            sage: W.everyone_has_deleted_this_worksheet()
            True
        """
        for user in self.collaborators + [self.owner]:
            # When the worksheet has been deleted by the owner,
            # self.owner returns None, so we have to be careful
            # about that case.
            if user is not None and not self.is_trashed(user):
                return False
        return True

    def user_view(self, user):
        """
        Return the view that the given user has of this worksheet. If the
        user currently doesn't have a view set it to WS_ACTIVE and return
        WS_ACTIVE.

        INPUT:

        -  ``user`` - a string

        OUTPUT:

        -  ``Python int`` - one of WS_ACTIVE, WS_ARCHIVED, WS_TRASH,
           which are defined in worksheet.py

        EXAMPLES: We create a new worksheet and get the view, which is
        WS_ACTIVE::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.user_view('admin')
            1
            sage: sagenb.notebook.worksheet.ACTIVE
            1

        Now for the admin user we move W to the archive::

            sage: W.move_to_archive('admin')

        The view is now archive.

        ::

            sage: W.user_view('admin')
            0
            sage: sagenb.notebook.worksheet.ARCHIVED
            0

        For any other random viewer the view is set by default to WS_ACTIVE.

        ::

            sage: W.user_view('foo')
            1
        """
        try:
            return self.__user_view[user]
        except AttributeError:
            self.__user_view = {}
        except KeyError:
            pass
        self.__user_view[user] = WS_ACTIVE
        return WS_ACTIVE

    def tags(self):
        """
        A temporary trivial tags implementation.
        """
        try:
            d = dict(self.__user_view)
        except AttributeError:
            self.user_view(self.owner)
            d = copy.copy(self.__user_view)
        for user, val in d.iteritems():
            if not isinstance(val, list):
                d[user] = [val]
        return d

    def set_tags(self, tags):
        """
        Set the tags -- for now we ignore everything except WS_ACTIVE,
        WS_ARCHIVED, WS_TRASH.

        INPUT:

            - ``tags`` -- dictionary with keys usernames and values a
              list of tags, where a tag is a string or WS_ARCHIVED,
              WS_ACTIVE, WS_TRASH.
        """
        d = {}
        for user, v in tags.iteritems():
            if len(v) >= 1:
                d[user] = v[0]  # must be a single int for now, until
                # the tag system is implemented
        self.__user_view = d

    def set_user_view(self, user, x):
        """
        Set the view on this worksheet for the given user.

        INPUT:

        -  ``user`` - a string

        -  ``x`` - int, one of the variables WS_ACTIVE, WS_ARCHIVED,
           WS_TRASH in worksheet.py

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.set_user_view('admin', sagenb.notebook.worksheet.ARCHIVED)
            sage: W.user_view('admin') == sagenb.notebook.worksheet.ARCHIVED
            True
        """
        if not isinstance(user, (str, unicode)):
            raise TypeError("user (=%s) must be a string" % user)
        try:
            self.__user_view[user] = x
        except (KeyError, AttributeError):
            self.user_view(user)
            self.__user_view[user] = x

        # it is important to save the configuration and changing the
        # views, e.g., moving to trash, etc., since the user can't
        # easily click save without changing the view back.
        self.save(conf_only=True)

    def user_view_is(self, user, x):
        """
        Return True if the user view of user is x.

        INPUT:

        -  ``user`` - a string

        -  ``x`` - int, one of the variables WS_ACTIVE, WS_ARCHIVED,
           WS_TRASH in worksheet.py

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Publish Test', 'admin')
            sage: W.user_view_is('admin', sagenb.notebook.worksheet.ARCHIVED)
            False
            sage: W.user_view_is('admin', sagenb.notebook.worksheet.ACTIVE)
            True
        """
        return self.user_view(user) == x

    def is_archived(self, user):
        """
        Return True if this worksheet is archived for the given user.

        INPUT:

        -  ``user`` - string

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Archived Test', 'admin')
            sage: W.is_archived('admin')
            False
            sage: W.move_to_archive('admin')
            sage: W.is_archived('admin')
            True
        """
        return self.user_view_is(user, WS_ARCHIVED)

    def is_active(self, user):
        """
        Return True if this worksheet is active for the given user.

        INPUT:

        -  ``user`` - string

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Active Test', 'admin')
            sage: W.is_active('admin')
            True
            sage: W.move_to_archive('admin')
            sage: W.is_active('admin')
            False
        """
        return self.user_view_is(user, WS_ACTIVE)

    def is_trashed(self, user):
        """
        Return True if this worksheet is in the trash for the given user.

        INPUT:

        -  ``user`` - string

        OUTPUT: bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Trash Test', 'admin')
            sage: W.is_trashed('admin')
            False
            sage: W.move_to_trash('admin')
            sage: W.is_trashed('admin')
            True
        """
        return self.user_view_is(user, WS_TRASH)

    def move_to_archive(self, user):
        """
        Move this worksheet to be archived for the given user.

        INPUT:

        -  ``user`` - string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Archive Test', 'admin')
            sage: W.move_to_archive('admin')
            sage: W.is_archived('admin')
            True
        """
        self.set_user_view(user, WS_ARCHIVED)
        if self.viewers == [user]:
            self.quit()

    def set_active(self, user):
        """
        Set his worksheet to be active for the given user.

        INPUT:

        -  ``user`` - string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Active Test', 'admin')
            sage: W.move_to_archive('admin')
            sage: W.is_active('admin')
            False
            sage: W.set_active('admin')
            sage: W.is_active('admin')
            True
        """
        self.set_user_view(user, WS_ACTIVE)

    def move_to_trash(self, user):
        """
        Move this worksheet to the trash for the given user.

        INPUT:

        -  ``user`` - string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Trash Test', 'admin')
            sage: W.move_to_trash('admin')
            sage: W.is_trashed('admin')
            True
        """
        self.set_user_view(user, WS_TRASH)
        if self.viewers == [user]:
            self.quit()

    def move_out_of_trash(self, user):
        """
        Exactly the same as set_active(user).

        INPUT:

        -  ``user`` - string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Active Test', 'admin')
            sage: W.move_to_trash('admin')
            sage: W.is_active('admin')
            False
            sage: W.move_out_of_trash('admin')
            sage: W.is_active('admin')
            True
        """
        self.set_active(user)

    def delete_cells_directory(self):
        r"""
        Delete the directory in which all the cell computations occur.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.edit_save('{{{\n3^20\n}}}')
            sage: W.cell_list()[0].evaluate()
            sage: W.check_comp(
                )    # random output -- depends on computer speed
            sage: sorted(os.listdir(W.directory()))
            ['cells', 'data', 'worksheet.html', 'worksheet_conf.pickle']
            sage: W.save_snapshot('admin')
            sage: sorted(os.listdir(W.directory()))
            ['cells', 'data', 'snapshots', 'worksheet.html',
             'worksheet_conf.pickle']
            sage: W.delete_cells_directory()
            sage: sorted(os.listdir(W.directory()))
            ['data', 'snapshots', 'worksheet.html', 'worksheet_conf.pickle']
            sage: W.quit()
            sage: nb.delete()
        """
        dir = self.cells_directory()
        if os.path.exists(dir):
            shutil.rmtree(dir)

    # Owner/viewer/user management

    def is_owner(self, username):
        return self.owner == username

    def is_only_viewer(self, user):
        try:
            return user in self.viewers
        except AttributeError:
            return False

    def is_viewer(self, user):
        try:
            return (user in self.viewers or user in self.collaborators or
                    user == self.publisher())
        except AttributeError:
            return True

    def is_collaborator(self, user):
        return user in self.collaborators

    def user_can_edit(self, user):
        """
        Return True if the user with given name is allowed to edit this
        worksheet.

        INPUT:

        -  ``user`` - string

        OUTPUT: bool

        EXAMPLES: We create a notebook with one worksheet and two users.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: nb.user_manager.add_user(
                'william', 'william', 'wstein@sagemath.org', force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.user_can_edit('sage')
            True

        At first the user 'william' can't edit this worksheet::

            sage: W.user_can_edit('william')
            False

        After adding 'william' as a collaborator he can edit the
        worksheet.

        ::

            sage: W.add_collaborator('william')
            sage: W.user_can_edit('william')
            True

        Clean up::

            sage: nb.delete()
        """
        return self.is_collaborator(user) or self.is_owner(user)

    def delete_user(self, user):
        """
        Delete a user from having any view or ownership of this worksheet.

        INPUT:

        -  ``user`` - string; the name of a user

        EXAMPLES: We create a notebook with 2 users and 1 worksheet that
        both view.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'wstein','sage','wstein@sagemath.org',force=True)
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Sage', owner='sage')
            sage: W.add_viewer('wstein')
            sage: W.owner
            'sage'
            sage: W.viewers
            ['wstein']

        We delete the sage user from the worksheet W. This makes wstein the
        new owner.

        ::

            sage: W.delete_user('sage')
            sage: W.viewers
            ['wstein']
            sage: W.owner
            'wstein'

        Then we delete wstein from W, which makes the owner None.

        ::

            sage: W.delete_user('wstein')
            sage: W.owner is None
            True
            sage: W.viewers
            []

        Finally, we clean up.

        ::

            sage: nb.delete()
        """
        if user in self.collaborators:
            self.collaborators.remove(user)
        if user in self.viewers:
            self.viewers.remove(user)
        if self.owner == user:
            if len(self.collaborators) > 0:
                self.owner = self.collaborators[0]
            elif len(self.viewers) > 0:
                self.owner = self.viewers[0]
            else:
                # Now there is nobody to take over ownership.  We
                # assign the owner None, which means nobody owns it.
                # It will get purged elsewhere.
                self.owner = None

    def add_viewer(self, user):
        """
        Add the given user as an allowed viewer of this worksheet.

        INPUT:

        -  ``user`` - string (username)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: nb.user_manager.add_user(
                'diophantus','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Viewer test', 'admin')
            sage: W.add_viewer('diophantus')
            sage: W.viewers
            ['diophantus']
        """
        if user not in self.viewers:
            self.viewers.append(user)

    def add_collaborator(self, user):
        """
        Add the given user as a collaborator on this worksheet.

        INPUT:

        -  ``user`` - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: nb.user_manager.add_user(
                'diophantus','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Collaborator test', 'admin')
            sage: W.collaborators
            []
            sage: W.add_collaborator('diophantus')
            sage: W.collaborators
            ['diophantus']
        """
        if user not in self.collaborators:
            self.collaborators.append(user)

    # Searching

    def satisfies_search(self, search):
        """
        Return True if all words in search are in the saved text of the
        worksheet.

        INPUT:

        - ``search`` - a string that describes a search query, i.e., a
          space-separated collections of words.

        OUTPUT:

        - a boolean
        """
        # Load the worksheet data file from disk.
        filename = self.worksheet_html_filename

        if os.path.exists(filename):
            contents = open(filename).read().decode('utf-8', 'ignore')
        else:
            contents = u' '

        try:
            r = [unicode(x.lower()) for x in [self.owner,
                                              self.publisher(),
                                              self.name, contents]]
            r = u" ".join(r)
        except UnicodeDecodeError:
            return False

        # Check that every single word is in the file from disk.
        for W in split_search_string_into_keywords(search):
            W = unicode_str(W)
            if W.lower() not in r:
                # Some word from the text is not in the search list, so
                # we return False.
                return False
        # Every single word is there.
        return True

    # Saving

    def save_snapshot(self, user, E=None):
        if not self.body_is_loaded():
            return
        self.uncache_snapshot_data()
        path = self.snapshot_directory()
        basename = str(int(time.time()))
        filename = os.path.join(path, '%s.bz2' % basename)
        if E is None:
            E = self.edit_text()
        worksheet_html = self.worksheet_html_filename
        open(filename, 'w').write(bz2.compress(E.encode('utf-8', 'ignore')))
        open(worksheet_html, 'w').write(self.body().encode('utf-8', 'ignore'))
        self.limit_snapshots()
        self.saved_by_info[basename] = user
        if self.auto_publish:
            self.notebook().publish_wst(self, user)

    def get_snapshot_text_filename(self, name):
        path = self.snapshot_directory()
        return os.path.join(path, name)

    def user_autosave_interval(self, username):
        return self.notebook()[username]['autosave_interval']

    def revert_to_snapshot(self, name):
        path = self.snapshot_directory()
        filename = os.path.join(path, '%s.txt' % name)
        E = bz2.decompress(open(filename).read())
        self.edit_save(E)

    @property
    def saved_by_info(self):
        return self.__saved_by_info

    def snapshot_data(self):
        try:
            self.__filenames
        except AttributeError:
            filenames = os.listdir(self.snapshot_directory())
            filenames.sort()
            self.__filenames = filenames
        t = time.time()
        v = []
        for x in self.__filenames:
            base = os.path.splitext(x)[0]
            if self.saved_by_info[x]:
                v.append((_('%(t)s ago by %(le)s',) %
                          {'t': prettify_time_ago(t - float(base)),
                           'le': self.saved_by_info[base]},
                          x))
            else:
                v.append((_('%(seconds)s ago',
                            seconds=prettify_time_ago(t - float(base))), x))
        return v

    def uncache_snapshot_data(self):
        try:
            del self.__snapshot_data
        except AttributeError:
            pass

    def revert_to_last_saved_state(self):
        filename = self.worksheet_html_filename
        if os.path.exists(filename):
            E = open(filename).read()
        else:
            # nothing was ever saved!
            E = ''
        self.edit_save(E)

    def snapshot_directory(self):
        path = os.path.join(os.path.abspath(self.__dir), 'snapshots')
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def limit_snapshots(self):
        r"""
        This routine will limit the number of snapshots of a worksheet,
        as specified by a hard-coded value below.

        Prior behavior was to allow unlimited numbers of snapshots and
        so this routine will not delete files created prior to this change.

        This assumes snapshot names correspond to the ``time.time()``
        method used to create base filenames in seconds in UTC time,
        and that there are no other extraneous files in the directory.
        """

        # This should be user-configurable with an option like 'max_snapshots'
        max_snaps = 30
        amnesty = int(calendar.timegm(
            time.strptime("01 May 2009", "%d %b %Y")))

        path = self.snapshot_directory()
        snapshots = os.listdir(path)
        snapshots.sort()
        for i in range(len(snapshots) - max_snaps):
            creation = int(os.path.splitext(snapshots[i])[0])
            if creation > amnesty:
                os.remove(os.path.join(path, snapshots[i]))

    # Exporting the worksheet in plain text command-line format

    def plain_text(self, prompts=False, banner=True):
        """
        Return a plain-text version of the worksheet.

        INPUT:

        -  ``prompts`` - if True format for inclusion in
           docstrings.
        """
        s = ''
        if banner:
            s += "#" * 80 + '\n'
            s += "# Worksheet: %s" % self.name + '\n'
            s += "#" * 80 + '\n\n'

        for C in self.cell_list():
            t = C.plain_text(prompts=prompts).strip('\n')
            if t != '':
                s += '\n' + t
        return s

    def input_text(self):
        """
        Return text version of the input to the worksheet.
        """
        return '\n\n---\n\n'.join([C.input_text() for C in self.cell_list()])

    # Editing the worksheet in plain text format (export and import)

    def body(self):
        """
        OUTPUT:

            -- ``string`` -- Plain text representation of the body of
               the worksheet.
        """
        s = ''
        for C in self.cell_list():
            t = C.edit_text().strip()
            if t:
                s += '\n\n' + t
        return s

    def set_body(self, body):
        self.edit_save(body)

    def body_is_loaded(self):
        """
        Return True if the body if this worksheet has been loaded from disk.
        """
        try:
            self.__cells
            return True
        except AttributeError:
            return False

    def edit_text(self):
        """
        Returns a plain-text version of the worksheet with {{{}}}
        wiki-formatting, suitable for hand editing.
        """
        return self.body()

    def reset_interact_state(self):
        """
        Reset the interact state of this worksheet.
        """
        try:
            S = self.__sage
        except AttributeError:
            return
        try:
            S.execute('_interact_.reset_state()', mode='raw')
        except OSError:
            # Doesn't matter, since if S is not running, no need
            # to zero out the state dictionary.
            return

    def edit_save_old_format(self, text, username=None):
        text.replace('\r\n', '\n')

        name, text = extract_text(text)
        self.name = name

        self.system, text = extract_text(text, start='system:', default='sage')

        self.edit_save(text)

    def edit_save(self, text, ignore_ids=False):
        r"""
        Set the contents of this worksheet to the worksheet defined by
        the plain text string text, which should be a sequence of HTML
        and code blocks.

        INPUT:

        -  ``text`` - a string

        -  ``ignore_ids`` - bool (default: False); if True
           ignore all the IDs in the {{{}}} code block.


        EXAMPLES:

        We create a new test notebook and a worksheet.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test Edit Save', 'sage')

        We set the contents of the worksheet using the edit_save command.

        ::

            sage: W.edit_save('{{{\n2+3\n///\n5\n}}}\n{{{\n2+8\n///\n10\n}}}')
            sage: W
            sage/0: [Cell 0: in=2+3, out=
            5, Cell 1: in=2+8, out=
            10]
            sage: W.name
            u'Test Edit Save'

        We check that loading a worksheet whose last cell is a
        :class:`~sagenb.notebook.cell.TextCell` properly increments
        the worksheet's cell count (see Sage trac ticket `#8443`_).

        .. _#8443: http://trac.sagemath.org/sage_trac/ticket/8443

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage', 'sage', 'sage@sagemath.org', force=True)
            sage: W = nb.create_wst('Test trac #8443', 'sage')
            sage: W.edit_save('{{{\n1+1\n///\n}}}')
            sage: W.cell_id_list()
            [0]
            sage: W.next_id()
            1
            sage: W.edit_save("{{{\n1+1\n///\n}}}\n\n<p>a text cell</p>")
            sage: len(set(W.cell_id_list())) == 3
            True
            sage: W.cell_id_list()
            [0, 1, 2]
            sage: W.next_id()
            3
        """
        self.reset_interact_state()

        text.replace('\r\n', '\n')

        data = []
        while True:
            plain_text = extract_text_before_first_compute_cell(text).strip()
            if len(plain_text) > 0:
                T = plain_text
                data.append(('plain', T))
            try:
                meta, input, output, i = extract_first_compute_cell(text)
                data.append(('compute', (meta, input, output)))
            except EOFError:
                # print msg # -- don't print msg, just outputs a blank
                #                 line every time, which makes for an
                #                 ugly and unprofessional log.
                break
            text = text[i:]

        ids = set([x[0]['id']
                   for typ, x in data if typ == 'compute' and 'id' in x[0]])
        used_ids = set([])

        cells = []
        for typ, T in data:
            if typ == 'plain':
                if len(T) > 0:
                    id = next_available_id(ids)
                    ids.add(id)
                    cells.append(self._new_text_cell(T, id=id))
                    used_ids.add(id)
            elif typ == 'compute':
                meta, input, output = T
                if not ignore_ids and 'id' in meta:
                    id = meta['id']
                    if id in used_ids:
                        # In this case don't reuse, since ids must be unique.
                        id = next_available_id(ids)
                        ids.add(id)
                    html = True
                else:
                    id = next_available_id(ids)
                    ids.add(id)
                    html = False
                used_ids.add(id)
                try:
                    self.__cells
                    C = self.get_cell_with_id(id=id)
                    if C.is_text_cell():
                        C = self._new_cell(id)
                except AttributeError:
                    C = self._new_cell(id)
                C.set_input_text(input)
                C.set_output_text(output, '')
                if html:
                    C.update_html_output(output)
                cells.append(C)

        self.__cells = cells
        # Set the next id.  This *depends* on self.cell_list() being
        # set!!
        self.set_cell_counter()

        # There must be at least one cell.
        if len(cells) == 0 or cells[-1].is_text_cell():
            self.append_new_cell()

        if not self.is_published():
            for c in self.cell_list():
                if c.is_interactive_cell():
                    c.delete_output()

    def truncated_name(self, max=30):
        name = self.name
        if len(name) > max:
            name = name[:max] + ' ...'
        return name

    # Last edited

    @property
    def last_edited(self):
        return self.last_change[1]

    @property
    def date_edited(self):
        """
        Returns the date the worksheet was last edited.
        """
        return time.localtime(self.last_change[1])

    @property
    def last_to_edit(self):
        return self.last_change[0]

    @property
    def time_since_last_edited(self):
        return time.time() - self.last_edited

    def record_edit(self, user):
        self.last_change = (user, time.time())

    def warn_about_other_person_editing(self, username,
                                        threshold=WARN_THRESHOLD):
        r"""
        Check to see if another user besides username was the last to edit
        this worksheet during the last ``threshold`` seconds.
        If so, return True and that user name. If not, return False.

        INPUT:

        -  ``username`` - user who would like to edit this
           file.

        -  ``threshold`` - number of seconds, so if there was
           no activity on this worksheet for this many seconds, then editing
           is considered safe.
        """
        if self.time_since_last_edited < threshold:
            user = self.last_to_edit
            if user != username:
                return True, user
        return False

    # Managing cells and groups of cells in this worksheet

    def cell_id_list(self):
        r"""
        Returns a list of ID's of all cells in this worksheet.

        OUTPUT:

        - a new list of integers and/or strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Test Edit Save', 'admin')

        Now we set the worksheet to have two cells with the default id of 0
        and another with id 10.

        ::

            sage: W.edit_save(
                '{{{\n2+3\n///\n5\n}}}\n{{{id=10|\n2+8\n///\n10\n}}}')
            sage: W.cell_id_list()
            [0, 10]
        """
        return [C.id() for C in self.cell_list()]

    def compute_cell_id_list(self):
        """
        Returns a list of ID's of all compute cells in this worksheet.

        OUTPUT:

        - a new list of integers and/or strings
        """
        return [C.id() for C in self.cell_list() if C.is_compute_cell()]

    def onload_id_list(self):
        """
        Returns a list of ID's of cells the remote client should
        evaluate after the worksheet loads.  Unlike '%auto' cells,
        which the server chooses to evaluate, onload cells fire only
        after the client sends a request.  Currently, we use onload
        cells to set up published interacts.

        OUTPUT:

        - a new list of integer and/or string IDs
        """
        return [C.id() for C in self.cell_list() if C.is_interactive_cell()]

    def cell_list(self):
        r"""
        Returns a reference to the list of this worksheet's cells.

        OUTPUT:

        - a list of :class:`sagenb.notebook.cell.Cell_generic`
          instances

        .. note::

           This function loads the cell list from disk (the file
           worksheet.html) if it isn't available in memory.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Test Edit Save', 'admin')
            sage: W.edit_save('{{{\n2+3\n///\n5\n}}}\n{{{\n2+8\n///\n10\n}}}')
            sage: v = W.cell_list(); v
            [Cell 0: in=2+3, out=
            5, Cell 1: in=2+8, out=
            10]
            sage: v[0]
            Cell 0: in=2+3, out=
            5
        """
        try:
            return self.__cells
        except AttributeError:
            # load from disk
            worksheet_html = self.worksheet_html_filename
            if not os.path.exists(worksheet_html):
                self.__cells = []
            else:
                self.set_body(open(worksheet_html).read())
            return self.__cells

    def compute_cell_list(self):
        r"""
        Returns a list of this worksheet's compute cells.

        OUTPUT:

        - a list of :class:`sagenb.notebook.cell.Cell` instances

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Test', 'admin')
            sage: W.edit_save(
                'foo\n{{{\n2+3\n///\n5\n}}}bar\n{{{\n2+8\n///\n10\n}}}')
            sage: v = W.compute_cell_list(); v
            [Cell 1: in=2+3, out=
            5, Cell 3: in=2+8, out=
            10]
            sage: v[0]
            Cell 1: in=2+3, out=
            5
        """
        return [C for C in self.cell_list() if C.is_compute_cell()]

    def append_new_cell(self):
        """
        Creates and appends a new compute cell to this worksheet's
        list of cells.

        OUTPUT:

        - a new :class:`sagenb.notebook.cell.Cell` instance

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Test Edit Save', 'admin')
            sage: W
            admin/0: [Cell 1: in=, out=]
            sage: W.append_new_cell()
            Cell 2: in=, out=
            sage: W
            admin/0: [Cell 1: in=, out=, Cell 2: in=, out=]
        """
        C = self._new_cell()
        self.cell_list().append(C)
        return C

    def new_cell_before(self, id, input=''):
        """
        Inserts a new compute cell before a cell with the given ID.
        If the ID does not match any cell in this worksheet's list, it
        inserts a new cell at the end.

        INPUT:

        - ``id`` - an integer or a string; the ID of the cell to find

        - ``input`` - a string (default: ''); the new cell's input text

        OUTPUT:

        - a new :class:`sagenb.notebook.cell.Cell` instance
        """
        cells = self.cell_list()
        for i in range(len(cells)):
            if cells[i].id() == id:
                C = self._new_cell(input=input)
                cells.insert(i, C)
                return C
        C = self._new_cell(input=input)
        cells.append(C)
        return C

    def new_text_cell_before(self, id, input=''):
        """
        Inserts a new text cell before the cell with the given ID.  If
        the ID does not match any cell in this worksheet's list, it
        inserts a new cell at the end.

        INPUT:

        - ``id`` - an integer or a string; the ID of the cell to find

        - ``input`` - a string (default: ''); the new cell's input
          text

        OUTPUT:

        - a new :class:`sagenb.notebook.cell.TextCell` instance
        """
        cells = self.cell_list()
        for i in range(len(cells)):
            if cells[i].id() == id:
                C = self._new_text_cell(plain_text=input)
                cells.insert(i, C)
                return C
        C = self._new_text_cell(plain_text=input)
        cells.append(C)
        return C

    def new_cell_after(self, id, input=''):
        """
        Inserts a new compute cell into this worksheet's cell list
        after the cell with the given ID.  If the ID does not match
        any cell, it inserts the new cell at the end of the list.

        INPUT:

        - ``id`` - an integer or a string; the ID of the cell to find

        - ``input`` - a string (default: ''); the new cell's input text

        OUTPUT:

        - a new :class:`sagenb.notebook.cell.Cell` instance
        """
        cells = self.cell_list()
        for i in range(len(cells)):
            if cells[i].id() == id:
                C = self._new_cell(input=input)
                cells.insert(i + 1, C)
                return C
        C = self._new_cell(input=input)
        cells.append(C)
        return C

    def new_text_cell_after(self, id, input=''):
        """
        Inserts a new text cell into this worksheet's cell list after
        the cell with the given ID.  If the ID does not match any
        cell, it inserts the new cell at the end of the list.

        INPUT:

        - ``id`` - an integer or a string; the ID of the cell to find

        - ``input`` - a string (default: ''); the new cell's input text

        OUTPUT:

        - a new :class:`sagenb.notebook.cell.TextCell` instance
        """
        cells = self.cell_list()
        for i in range(len(cells)):
            if cells[i].id() == id:
                C = self._new_text_cell(plain_text=input)
                cells.insert(i + 1, C)
                return C
        C = self._new_text_cell(plain_text=input)
        cells.append(C)
        return C

    def delete_cell_with_id(self, id):
        r"""
        Deletes a cell from this worksheet's cell list.  This also
        deletes the cell's output and files.

        INPUT:

        - ``id`` - an integer or string; the cell's ID

        OUTPUT:

        - an integer or string; ID of the preceding cell

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.create_default_users('password')
            sage: W = nb.create_wst('Test Delete Cell', 'admin')
            sage: W.edit_save(
                '{{{id=foo|\n2+3\n///\n5\n}}}\n{{{id=9|\n2+8\n///\n10\n}}}'
                '{{{id=dont_delete_me|\n2*3\n///\n6\n}}}\n')
            sage: W.cell_id_list()
            ['foo', 9, 'dont_delete_me']
            sage: C = W.cell_list()[1]           # save a reference to the cell
            sage: C.output_text(raw=True)
            u'\n10'
            sage: open(os.path.join(C.directory(), 'bar'), 'w').write('hello')
            sage: C.files()
            ['bar']
            sage: C.files_html('')
            u'<a target="_new" href=".../cells/9/bar" class="file_link">bar'
            u'</a>'
            sage: W.delete_cell_with_id(C.id())
            'foo'
            sage: C.output_text(raw=True)
            u''
            sage: C.files()
            []
            sage: W.cell_id_list()
            ['foo', 'dont_delete_me']
        """
        cells = self.cell_list()
        for i in range(len(cells)):
            if cells[i].id() == id:

                # Delete this cell from the queued up calculation list:
                C = cells[i]
                if C in self.__queue and self.__queue[0] != C:
                    self.__queue.remove(C)

                # Delete the cell's output.
                C.delete_output()

                # Delete this cell from the list of cells in this worksheet:
                del cells[i]

                if i > 0:
                    return cells[i - 1].id()
                else:
                    break
        return cells[0].id()

    # Managing whether computing is happening: stop, start, clear, etc.

    def clear(self):
        self.__comp_is_running = False
        self.__queue = []
        self.__cells = []
        for i in range(INITIAL_NUM_CELLS):
            self.append_new_cell()

    def computing(self):
        """
        Return whether or not a cell is currently being run in the
        worksheet Sage process.
        """
        try:
            return self.__comp_is_running
        except AttributeError:
            return False

    def set_not_computing(self):
        self.__comp_is_running = False
        self.__queue = []

    def quit(self):
        try:
            S = self.__sage
        except AttributeError:
            # no sage running anyways!
            self.notebook().quit_worksheet(self)
            return

        try:
            S.quit()
        except AttributeError, msg:
            print "WARNING: %s" % msg
        except Exception, msg:
            print msg
            print "WARNING: Error deleting Sage object!"

        del self.__sage

        # We do this to avoid getting a stale Sage that uses old code.
        self.save()
        self.clear_queue()
        del self.__cells

        for cell in self.cell_list():
            try:
                dir = cell._directory_name()
            except AttributeError:
                continue
            if os.path.exists(dir) and not os.listdir(dir):
                shutil.rmtree(dir, ignore_errors=True)
        self.notebook().quit_worksheet(self)

    def next_block_id(self):
        try:
            i = self.__next_block_id
        except AttributeError:
            i = 0
        i += 1
        self.__next_block_id = i
        return i

    def compute_process_has_been_started(self):
        """
        Return True precisely if the compute process has been started,
        irregardless of whether or not it is currently churning away on a
        computation.
        """
        try:
            return self.__sage.is_started()
        except AttributeError:
            return False

    def sage(self):
        """
        Return a started up copy of Sage initialized for computations.

        If this is a published worksheet, just return None, since published
        worksheets must not have any compute functionality.

        OUTPUT: a Sage interface
        """
        if self.is_published():
            return None
        try:
            S = self.__sage
            if S.is_started():
                return S
        except AttributeError:
            pass
        try:
            init_code = '\n'.join((
                "DATA = '{}'".format(
                    os.path.join(os.path.abspath(self.data_directory()))),
                'sys.path.append(DATA)',
                ))
            self.__sage = self.notebook().new_worksheet_process(
                init_code=init_code)
        except Exception as msg:
            print "ERROR initializing compute process:\n"
            print msg
            del self.__sage
            raise RuntimeError(msg)
        all_worksheet_processes.append(self.__sage)
        self.__next_block_id = 0
        S = self.__sage

        # Check to see if the typeset/pretty print button is checked.
        # If so, send code to initialize the worksheet to have the
        # right pretty printing mode.
        if self.pretty_print:
            S.execute('pretty_print_default(True)', mode='raw')

        if not self.is_published():
            self._enqueue_auto_cells()
        return self.__sage

    def eval_asap_no_output(self, cmd, username=None):
        C = self._new_cell(hidden=True)
        C.set_asap(True)
        C.set_no_output(True)
        C.set_input_text(cmd)
        self.enqueue(C, username=username)

    def cell_directory(self, C):
        return C.directory()

    def start_next_comp(self):
        if len(self.__queue) == 0:
            return

        if self.__comp_is_running:
            # self._record_that_we_are_computing()
            return

        C = self.__queue[0]
        cell_system = self.get_cell_system(C)
        percent_directives = C.percent_directives()

        if C.interrupted():
            # don't actually compute
            return

        if cell_system == 'sage' and C.introspect():
            before_prompt, after_prompt = C.introspect()
            I = before_prompt
        else:
            I = C.cleaned_input_text()
            if I in ['restart', 'quit', 'exit']:
                self.restart_sage()
                S = self.system
                if S is None:
                    S = 'sage'
                C.set_output_text('Exited %s process' % S, '')
                return

        # Handle any percent directives
        if 'save_server' in percent_directives:
            self.notebook().save()

        id = self.next_block_id()
        C.code_id = id

        # prevent directory disappear problems
        input = ''

        # This is useful mainly for interact -- it allows a cell to
        # know its ID.
        input += (
            '_interact_.SAGE_CELL_ID=%r\n__SAGE_TMP_DIR__=os.getcwd()\n' %
            C.id())

        print_time = C.time()
        if C.time():
            input += '__SAGE_t__=cputime()\n__SAGE_w__=walltime()\n'
            print_time = not C.introspect()

        # If the input ends in a question mark and is *not* a comment
        # line, then we introspect on it.
        if cell_system == 'sage' and len(I) != 0:
            # Get the last line of a possible multiline input
            Istrip = I.strip().split('\n').pop()
            if Istrip.endswith('?') and not Istrip.startswith('#'):
                C.set_introspect(I, '')

        # Handle line continuations: join lines that end in a backslash
        # _except_ in LaTeX mode.
        if cell_system not in ['latex', 'sage', 'python']:
            I = I.replace('\\\n', '')

        C._before_preparse = input + I
        input += self.preparse_input(I, C)

        self.__comp_is_running = True
        mode = ('sage' if cell_system == 'sage' and not C.introspect()
                else 'python')
        self.sage().execute(
            input, os.path.abspath(self.data_directory()),
            mode=mode, print_time=print_time)

    def check_comp(self, wait=0.2):
        r"""
        Check on currently computing cells in the queue.

        INPUT:

        -  ``wait`` - float (default: 0.2); how long to wait
           for output.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.edit_save('{{{\n3^20\n}}}')
            sage: W.cell_list()[0].evaluate()
            sage: W.check_comp(
                )     # random output -- depends on computer speed
            ('d', Cell 0: in=3^20, out=
            3486784401
            )
            sage: W.quit()
            sage: nb.delete()
        """

        if len(self.__queue) == 0:
            return 'e', None
        S = self.sage()
        C = self.__queue[0]

        if C.interrupted():
            self.__comp_is_running = False
            del self.__queue[0]
            return 'd', C

        try:
            output_status = S.output_status()
        except RuntimeError:
            # verbose(
            #  "Computation was interrupted or failed. Restarting.\n%s" % msg)
            self.__comp_is_running = False
            self.start_next_comp()
            return 'w', C

        out = self.postprocess_output(output_status.output, C)

        if not output_status.done:
            # Still computing
            if not C.introspect():
                C.set_output_text(out, '')

                ########################################################
                # Create temporary symlinks to output files seen so far
                if len(output_status.filenames) > 0:
                    cell_dir = os.path.abspath(self.cell_directory(C))
                    if not os.path.exists(cell_dir):
                        os.makedirs(cell_dir)
                    for X in output_status.filenames:
                        target = os.path.join(cell_dir, os.path.split(X)[1])
                        if os.path.exists(target):
                            os.unlink(target)
                        os.symlink(X, target)
                ########################################################
            return 'w', C

        if C.introspect() and not C.is_no_output():
            before_prompt, after_prompt = C.introspect()
            if len(before_prompt) == 0:
                return
            if before_prompt[-1] != '?':
                # completions
                if hasattr(C, '_word_being_completed'):
                    c = self.best_completion(out, C._word_being_completed)
                else:
                    c = ''
                C.set_changed_input_text(before_prompt + c + after_prompt)
                out = self.completions_html(C.id(), out)
                C.set_introspect_html(out, completing=True)
            else:
                if C.eval_method == 'introspect':
                    C.set_introspect_html(out, completing=False)
                else:
                    C.set_introspect_html('')
                    C.set_output_text('<html><!--notruncate-->' + out +
                                      '</html>', '')

        # Finished a computation.
        self.__comp_is_running = False
        del self.__queue[0]

        if C.is_no_output():
            # Clean up the temp directories associated to C, and do
            # not set any output text that C might have got.
            d = self.cell_directory(C)
            for X in os.listdir(d):
                Y = os.path.join(d, X)
                if os.path.isfile(Y):
                    try:
                        os.unlink(Y)
                    except:
                        pass
                else:
                    shutil.rmtree(Y, ignore_errors=True)
            return 'd', C

        if not C.introspect():
            filenames = output_status.filenames
            if len(filenames) > 0:
                # Move files to the cell directory
                cell_dir = os.path.abspath(self.cell_directory(C))
                # We wipe the cell directory and make a new one to
                # clean up any cruft (like dead symbolic links to
                # temporary files that were deleted, old files from
                # old evaluations, ...).
                try:
                    shutil.rmtree(cell_dir)
                except OSError:
                    # Probably the directory didn't exist. If there
                    # is a different problem, the makedirs() below will
                    # see it.
                    pass
                os.makedirs(cell_dir)

                for X in filenames:
                    target = os.path.join(cell_dir, os.path.split(X)[1])
                    # We move X to target. Note that we don't actually
                    # do a rename: in a client/server setup, X might be
                    # owned by a different Unix user than ourselves.
                    if os.path.isdir(X):
                        shutil.copytree(X, target,
                                        ignore=ignore_nonexistent_files)
                        shutil.rmtree(X, ignore_errors=True)
                    else:
                        shutil.copy(X, target)
                        os.unlink(X)
                    set_restrictive_permissions(target)
            # Generate html, etc.
            html = C.files_html(out)
            C.set_output_text(out, html, sage=self.sage())
            C.set_introspect_html('')

        return 'd', C

    def interrupt(self, callback=None, timeout=1):
        r"""
        Interrupt all currently queued up calculations.

        INPUT:

        - ``timeout`` -- time to wait for interruption to succeed

        - ``callback`` -- callback to be called. Called with True if
          interrupt succeeds, else called with False.

        OUTPUT:

        -  ``deferred`` - a Deferred object with the given callbacks and
           errbacks

        EXAMPLES: We create a worksheet and start a large factorization
        going::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.edit_save('{{{\nfactor(2^997-1)\n}}}')
            sage: W.cell_list()[0].evaluate()

        It's running still::

            sage: W.check_comp()
            ('w', Cell 0: in=factor(2^997-1), out=...)

        We interrupt it successfully.

        ::

            sage: W.interrupt(
                )         # not tested -- needs running reactor
            True

        Now we check and nothing is computing.

        ::

            sage: W.check_comp(
                )        # random -- could fail on heavily loaded machine
            ('e', None)

        Clean up.

        ::

            sage: W.quit()
            sage: nb.delete()
        """
        if len(self.__queue) == 0:
            # nothing to do
            return True
        # stop the current computation in the running Sage
        S = self.__sage
        S.interrupt()

        time.sleep(timeout)

        if S.is_computing():
            return False
        else:
            return True

    def clear_queue(self):
        # empty the queue
        for C in self.__queue:
            C.interrupt()
        self.__queue = []
        self.__comp_is_running = False

    def restart_sage(self):
        """
        Restart Sage kernel.
        """
        self.quit()
        self.sage()
        self.start_next_comp()

    def worksheet_command(self, cmd):
        # return URL in the web browser of the given cmd
        return '/home/%s/%s' % (self.filename(), cmd)

    # Idle timeout

    def quit_if_idle(self, timeout):
        r"""
        Quit the worksheet process if it has been "idle" for more than
        ``timeout`` seconds, where idle is by definition that
        the worksheet has not reported back that it is actually computing.
        I.e., an ignored worksheet process (since the user closed their
        browser) is also considered idle, even if code is running.
        """
        # Quit only if timeout is greater than zero
        if timeout > 0 and self.time_idle() > timeout:
            # worksheet name may contain unicode, so we use %r, which prints
            # the \xXX form for unicode characters
            print "Quitting ignored worksheet process for %r." % self.name
            self.quit()

    def time_idle(self):
        return walltime() - self.last_compute_walltime()

    def last_compute_walltime(self):
        try:
            return self.__last_compute_walltime
        except AttributeError:
            t = walltime()
            self.__last_compute_walltime = t
            return t

    def _record_that_we_are_computing(self, username=None):
        self.__last_compute_walltime = walltime()
        if username:
            self.record_edit(username)

    def ping(self, username):
        if self.is_published():
            return
        self._record_that_we_are_computing(username)

    # Enqueuing cells

    def queue(self):
        return list(self.__queue)

    def queue_id_list(self):
        return [c.id() for c in self.__queue]

    def enqueue(self, C, username=None, next=False):
        r"""
        Queue a cell for evaluation in this worksheet.

        INPUT:

        -  ``C`` - a :class:`sagenb.notebook.cell.Cell` instance

        - ``username`` - a string (default: None); the name of the
           user evaluating this cell (mainly used for login)

        - ``next`` - a boolean (default: False); ignored

        .. note::

           If ``C.is_asap()`` is True, then we put ``C`` as close to
           the beginning of the queue as possible, but after all
           "asap" cells.  Otherwise, ``C`` goes at the end of the
           queue.
        """
        if self.is_published():
            return
        self._record_that_we_are_computing(username)
        if not C.is_compute_cell():
            raise TypeError
        if C.worksheet() != self:
            raise ValueError("C must be have self as worksheet.")

        # Now enqueue the requested cell.
        if not (C in self.__queue):
            if C.is_asap():
                if self.computing():
                    i = 1
                else:
                    i = 0
                while i < len(self.__queue) and self.__queue[i].is_asap():
                    i += 1
                self.__queue.insert(i, C)
            else:
                self.__queue.append(C)
        self.start_next_comp()

    def _enqueue_auto_cells(self):
        for c in self.cell_list():
            if c.is_auto_cell():
                self.enqueue(c)

    def next_id(self):
        try:
            return self.__next_id
        except AttributeError:
            self.set_cell_counter()
            return self.__next_id

    def set_cell_counter(self):
        self.__next_id = 1 + \
            max([C.id() for C in self.cell_list()
                 if isinstance(C.id(), int)] + [-1])

    def _new_text_cell(self, plain_text, id=None):
        if id is None:
            id = self.next_id()
            self.__next_id += 1
        return TextCell(id, plain_text, self)

    def next_hidden_id(self):
        try:
            i = self.__next_hidden_id
            self.__next_hidden_id -= 1
        except AttributeError:
            i = -1
            self.__next_hidden_id = -2
        return i

    def _new_cell(self, id=None, hidden=False, input=''):
        if id is None:
            if hidden:
                id = self.next_hidden_id()
            else:
                id = self.next_id()
                self.__next_id += 1
        return Cell(id, input, '', self)

    def append(self, L):
        self.cell_list().append(L)

    # Accessing existing cells

    def get_cell_with_id_or_none(self, id):
        """
        Gets a pre-existing cell with this id, or returns None.
        """
        for c in self.cell_list():
            if c.id() == id:
                return c
        return None

    def get_cell_with_id(self, id):
        """
        Get a pre-existing cell with this id, or creates a new one with it.
        """
        return self.get_cell_with_id_or_none(id) or self._new_cell(id)

    def check_cell(self, id):
        """
        Checks the status of a given compute cell.

        INPUT:

        -  ``id`` - an integer or a string; the cell's ID.

        OUTPUT:

        - a (string, :class:`sagenb.notebook.cell.Cell`)-tuple; the
          cell's status ('d' for "done" or 'w' for "working") and the
          cell itself.
        """
        cell = self.get_cell_with_id(id)

        if cell in self.__queue:
            status = 'w'
        else:
            status = 'd'
        return status, cell

    def is_last_id_and_previous_is_nonempty(self, id):
        if self.cell_list()[-1].id() != id:
            return False
        if len(self.cell_list()) == 1:
            return False
        if len(self.cell_list()[-2].output_text(ncols=0)) == 0:
            return False
        return True

    # (Tab) Completions

    def best_completion(self, s, word):
        completions = s.split()
        if len(completions) == 0:
            return ''
        n = len(word)
        i = n
        m = min([len(x) for x in completions])
        while i <= m:
            word = completions[0][:i]
            for w in completions[1:]:
                if w[:i] != word:
                    return w[n:i - 1]
            i += 1
        return completions[0][n:m]

    def completions_html(self, id, s, cols=3):
        if 'no completions of' in s:
            return ''

        completions = s.split()

        n = len(completions)
        l = n / cols + n % cols

        if n == 1:
            return ''  # don't show a window, just replace it

        rows = []
        for r in range(0, l):
            row = []
            for c in range(cols):
                try:
                    cell = completions[r + l * c]
                    row.append(cell)
                except:
                    row.append('')
            rows.append(row)
        return format_completions_as_html(id, rows)

    # Processing of input and output to worksheet process.

    def preparse_input(self, input, C):
        introspect = C.introspect()
        if introspect:
            input = self.preparse_introspection_input(input, C, introspect)
        else:
            switched, input = self.check_for_system_switching(input, C)
            if not switched:
                input = ignore_prompts_and_output(input).rstrip()
            input += '\n'
        return input

    def preparse_introspection_input(self, input, C, introspect):
        before_prompt, after_prompt = introspect
        i = 0
        while i < len(after_prompt):
            if after_prompt[i] == '?':
                if i < len(after_prompt) - 1 and after_prompt[i + 1] == '?':
                    i += 1
                before_prompt += after_prompt[:i + 1]
                after_prompt = after_prompt[i + 1:]
                C.set_introspect(before_prompt, after_prompt)
                break
            elif after_prompt[i] in ['"', "'", ' ', '\t', '\n']:
                break
            i += 1
        if before_prompt.endswith('??'):
            input = self._last_identifier.search(before_prompt[:-2]).group()
            input = (
                'print _support_.source_code("%s", globals(), system="%s")' % (
                    input, self.system))
        elif before_prompt.endswith('?'):
            input = self._last_identifier.search(before_prompt[:-1]).group()
            input = (
                'print _support_.docstring("%s", globals(), system="%s")' % (
                    input, self.system))
        else:
            input = self._last_identifier.search(before_prompt).group()
            C._word_being_completed = input
            input = ('print "\\n".join(_support_.completions("%s", '
                     'globals(), system="%s"))' % (input, self.system))
        return input

    def postprocess_output(self, out, C):
        if C.introspect():
            return out

        out = out.replace("NameError: name 'os' is not defined",
                          "NameError: name 'os' is not defined\n"
                          "THERE WAS AN ERROR LOADING THE SAGE LIBRARIES.  "
                          "Try starting Sage from the command line to see "
                          "what the error is.")

        # Todo: what does this do?  document this
        try:
            tb = 'Traceback (most recent call last):'
            i = out.find(tb)
            if i != -1:
                t = '.py", line'
                j = out.find(t)
                z = out[j + 5:].find(',')
                n = int(out[j + len(t):z + j + 5])
                k = out[j:].find('\n')
                if k != -1:
                    k += j
                    l = out[k + 1:].find('\n')
                    if l != -1:
                        l += k + 1
                        I = C._before_preparse.split('\n')
                        out = out[:i + len(tb) + 1] + \
                            '    ' + I[n - 2] + out[l:]
        except (ValueError, IndexError):
            pass
        return out

    # Loading and attaching files

    def _eval_cmd(self, system, cmd):
        return u"print _support_.syseval(%s, %r, __SAGE_TMP_DIR__)" % (
            system, cmd)

    # Parsing the %cython, %mathjax, %python, etc., extension.

    def get_cell_system(self, cell):
        r"""
        Returns the system that will run the input in cell.  This
        defaults to worksheet's system if there is not one
        specifically given in the cell.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.edit_save(
                '{{{\n2+3\n}}}\n\n{{{\n%gap\nSymmetricGroup(5)\n}}}')
            sage: c0, c1 = W.cell_list()
            sage: W.get_cell_system(c0)
            'sage'
            sage: W.get_cell_system(c1)
            u'gap'
            sage: W.edit_save(
                '{{{\n%sage\n2+3\n}}}\n\n{{{\nSymmetricGroup(5)\n}}}')
            sage: W.system = 'gap'
            sage: c0, c1 = W.cell_list()
            sage: W.get_cell_system(c0)
            u'sage'
            sage: W.get_cell_system(c1)
            'gap'
        """
        if cell.system() is not None:
            system = cell.system()
        else:
            system = self.system
        return system

    def cython_import(self, cmd, cell):
        # Choice: Can use either C.relative_id() or
        # self.next_block_id().  C.relative_id() has the advantage
        # that block evals are cached, i.e., no need to recompile.  On
        # the other hand tracebacks don't work if you change a cell
        # and create a new function in it.  Caching is also annoying
        # since the linked .c file disappears.

        # TODO: This design will *only* work on local machines -- need
        # to redesign so works even if compute worksheet process is
        # remote!
        id = self.next_block_id()
        code = os.path.join(self.directory(), 'code')
        if not os.path.exists(code):
            os.makedirs(code)
        spyx = os.path.abspath(os.path.join(code, 'sage%s.spyx' % id))
        if not (os.path.exists(spyx) and open(spyx).read() == cmd):
            open(spyx, 'w').write(cmd.encode('utf-8', 'ignore'))
        return '_support_.cython_import_all("%s", globals())' % spyx

    def check_for_system_switching(self, input, cell):
        r"""
        Check for input cells that start with ``%foo``, where
        ``foo`` is an object with an eval method.

        INPUT:

        -  ``s`` - a string of the code from the cell to be
           executed

        -  ``C`` - the cell object

        EXAMPLES: First, we set up a new notebook and worksheet.

        ::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')

        We first test running a native command in 'sage' mode and then a
        GAP cell within Sage mode.

        ::

            sage: W.edit_save(
                '{{{\n2+3\n}}}\n\n{{{\n%gap\nSymmetricGroup(5)\n}}}')
            sage: c0, c1 = W.cell_list()
            sage: W.check_for_system_switching(c0.cleaned_input_text(), c0)
            (False, u'2+3')
            sage: W.check_for_system_switching(c1.cleaned_input_text(), c1)
            (True, u"print _support_.syseval(gap, u'SymmetricGroup(5)',
             __SAGE_TMP_DIR__)")

        ::

            sage: c0.evaluate()
            sage: W.check_comp(
                )  #random output -- depends on the computer's speed
            ('d', Cell 0: in=2+3, out=
            5
            )
            sage: c1.evaluate()
            sage: W.check_comp(
                )  #random output -- depends on the computer's speed
            ('d', Cell 1: in=%gap
            SymmetricGroup(5), out=
            Sym( [ 1 .. 5 ] )
            )

        Next, we run the same commands but from 'gap' mode.

        ::

            sage: W.edit_save(
                '{{{\n%sage\n2+3\n}}}\n\n{{{\nSymmetricGroup(5)\n}}}')
            sage: W.system = 'gap'
            sage: c0, c1 = W.cell_list()
            sage: W.check_for_system_switching(c0.cleaned_input_text(), c0)
            (False, u'2+3')
            sage: W.check_for_system_switching(c1.cleaned_input_text(), c1)
            (True, u"print _support_.syseval(gap, u'SymmetricGroup(5)',
             __SAGE_TMP_DIR__)")
            sage: c0.evaluate()
            sage: W.check_comp(
                )  #random output -- depends on the computer's speed
            ('d', Cell 0: in=%sage
            2+3, out=
            5
            )
            sage: c1.evaluate()
            sage: W.check_comp(
                )  #random output -- depends on the computer's speed
            ('d', Cell 1: in=SymmetricGroup(5), out=
            Sym( [ 1 .. 5 ] )
            )
            sage: W.quit()
            sage: nb.delete()
        """
        system = self.get_cell_system(cell)
        if system == 'sage':
            return False, input
        elif system in ['cython', 'pyrex', 'sagex']:
            return True, self.cython_import(input, cell)
        else:
            cmd = self._eval_cmd(system, input)
            return True, cmd

    # Showing and hiding all cells

    def show_all(self):
        for C in self.cell_list():
            try:
                C.set_cell_output_type('wrap')
            except AttributeError:   # for backwards compatibility
                pass

    def hide_all(self):
        for C in self.cell_list():
            try:
                C.set_cell_output_type('hidden')
            except AttributeError:
                pass

    def delete_all_output(self, username):
        r"""
        Delete all the output, files included, in all the worksheet cells.

        INPUT:

        -  ``username`` - name of the user requesting the
           deletion.

        EXAMPLES: We create a new notebook, user, and a worksheet::

            sage: nb = sagenb.notebook.notebook.load_notebook(
                tmp_dir(ext='.sagenb'))
            sage: nb.user_manager.add_user(
                'sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_wst('Test', 'sage')
            sage: W.edit_save(
                "{{{\n2+3\n///\n5\n}}}\n{{{\nopen('afile', 'w').write(
                    'some text')\nprint 'hello'\n///\n\n}}}")

        We have two cells::

            sage: W.cell_list()
            [Cell 0: in=2+3, out=
            5, Cell 1: in=open('afile', 'w').write('some text')
            print 'hello', out=
            ]
            sage: C0 = W.cell_list()[1]
            sage: open(os.path.join(C0.directory(), 'xyz'), 'w').write('bye')
            sage: C0.files()
            ['xyz']
            sage: C1 = W.cell_list()[1]
            sage: C1.evaluate()
            sage: W.check_comp(
                )     # random output -- depends on computer speed
            ('w', Cell 1: in=open('afile', 'w').write('some text')
            print 'hello', out=)
            sage: W.check_comp(
                )     # random output -- depends on computer speed
            ('d', Cell 1: in=open('afile', 'w').write('some text')
            print 'hello', out=
            hello
            )
            sage: W.check_comp(
                )     # random output -- depends on computer speed
            ('e', None)
            sage: C1.files(
                )         # random output -- depends on computer speed
            ['afile']

        We now delete the output, observe that it is gone::

            sage: W.delete_all_output('sage')
            sage: W.cell_list()
            [Cell 0: in=2+3, out=,
             Cell 1: in=open('afile', 'w').write('some text')
            print 'hello', out=]
            sage: C0.files(), C1.files()
            ([], [])

        If an invalid user tries to delete all output, a ValueError is
        raised::

            sage: W.delete_all_output('hacker')
            Traceback (most recent call last):
            ...
            ValueError: user 'hacker' not allowed to edit this worksheet

        Clean up::

            sage: W.quit()
            sage: nb.delete()
        """
        if not self.user_can_edit(username):
            raise ValueError(
                "user '%s' not allowed to edit this worksheet" % username)
        for C in self.cell_list():
            C.delete_output()
