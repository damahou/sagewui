# -*- coding: utf-8 -*
"""
Support for Notebook Introspection and Setup

AUTHORS:

- William Stein (much of this code is from IPython).

- Nick Alexander
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ast
import base64
import os
import sys
from itertools import chain

from docutils.core import publish_parts
from importlib import import_module
from pydoc import describe
from pydoc import html
from pydoc import resolve

from sage.misc import sageinspect
from sage.misc.cython import cython
from displayhook import DisplayHook
from sage.misc.inline_fortran import InlineFortran
from sage.misc.sagedoc import format_src
from sage.misc.session import init as session_init
from sage.repl.interpreter import _do_preparse
from sage.repl.preparse import preparse
from sage.repl.preparse import preparse_file
from sage.symbolic.all import Expression
from sage.symbolic.all import SR

from sage.misc.sphinxify import sphinxify

from temporary_file import doc_filename


sys.displayhook = DisplayHook()


######################################################################
# Initialization
######################################################################
sage_globals = None


def init(globs=None):
    r"""
    Initialize Sage for use with the web notebook interface.
    """
    global sage_globals
    if globs is None:
        globs = {}
    sage_globals = globs

    os.environ['PAGER'] = 'cat'

    setup_systems(globs)
    session_init(globs)


def setup_systems(globs):
    fortran = InlineFortran(globs)
    globs['fortran'] = fortran


######################################################################
# Introspection
######################################################################
def help(obj):
    """
    Display HTML help for ``obj``, a Python object, module, etc.  This
    help is often more extensive than that given by 'obj?'.  This
    function does not return a value --- it prints HTML as a side
    effect.

    .. note::

       This a wrapper around the built-in help. If formats the output
       as HTML without word wrap, which looks better in the notebook.

    INPUT:

    -  ``obj`` - a Python object, module, etc.

    TESTS::

        sage: import numpy.linalg
        sage: current_dir = os.getcwd()
        sage: os.chdir(tmp_dir('server_doctest'))
        sage: sagenb.misc.support.help(numpy.linalg.norm)
        <html>
        <table notracebacks bgcolor="#386074" cellpadding=10 cellspacing=10>
        <tr><td bgcolor="#f5f5f5"><font color="#37546d">
        &nbsp;&nbsp;&nbsp;<a target='_new' href='cell://docs-....html'>
        Click to open help window</a>&nbsp;&nbsp;&nbsp;
        <br></font></tr></td></table></html>
        sage: os.chdir(current_dir)
    """

    print('<html><table notracebacks bgcolor="#386074" cellpadding=10 '
          'cellspacing=10><tr><td bgcolor="#f5f5f5"><font color="#37546d">')
    object, name = resolve(obj)
    page = html.page(describe(object), html.document(object, name))
    page = page.replace('<a href', '<a ')
    filename = doc_filename()

    with open(filename, 'w') as f:
        f.write(page)

    print("&nbsp;&nbsp;&nbsp;<a target='_new' href='cell://%s'>"
          "Click to open help window</a>&nbsp;&nbsp;&nbsp;" % filename)
    print('<br></font></tr></td></table></html>')


def completions(s, globs, system="None"):
    """
    Return a list of completions in the given context.

    INPUT:

    - ``globs`` - a string:object dictionary; context in which to
      search for completions, e.g., :func:`globals()`

    - ``system`` - a string (default: 'None'); system prefix for the
      completions

    OUTPUT:

    - a list of strings
    """
    prepend = '{}.'.format(system) if system not in ['sage', 'python'] else ''
    s = '{}{}'.format(prepend, s)
    if s == '':
        return '(empty string)'

    if '.' not in s and '(' not in s:
        v = [x for x in chain(globs.keys(), __builtins__.keys())
             if x.startswith(s)]
    else:
        if ')' not in s:
            try:
                obj, method = s.rsplit('.', 1)
            except ValueError:
                obj = s
                method = ''

        else:
            obj = preparse(s)
            method = ''

        try:
            obj_eval = eval(obj, globs)
        except Exception:
            return []

        D = dir(obj_eval)
        try:
            D.extend(obj_eval.trait_names())
        except (AttributeError, TypeError):
            pass

        if method == '':
            v = ['{}.{}'.format(obj, x) for x in D if not x.startswith('_')]
        else:
            v = ['{}.{}'.format(obj, x) for x in D if x.startswith(method)]

    v = sorted(set(v))

    if prepend:
        i = len(prepend)
        v = [x[i:] for x in v]

    return v


def docstring(obj_name, globs, system='sage'):
    r"""
    Format an object's docstring to process and display in the Sage
    notebook.

    INPUT:

    - ``obj_name`` - a string; a name of an object

    - ``globs`` - a string:object dictionary; a context in which to
      evaluate ``obj_name``

    - ``system`` - a string (default: 'sage'); the system to which to
      confine the search

    OUTPUT:

    - a string containing the object's file, type, definition, and
      docstring or a message stating the object is not defined

    AUTHORS:

    - William Stein: partly taken from IPython for use in Sage

    - Nick Alexander: extensions

    TESTS:

    Check that Trac 10860 is fixed and we can handle Unicode help
    strings in the notebook::

        sage: from sagenb.misc.support import docstring
        sage: D = docstring("r.lm", globs=globals())
    """
    if system not in ['sage', 'python']:
        obj_name = '{}.{}'.format(system, obj_name)

    try:
        obj = eval(obj_name, globs)
    except Exception:
        return "No object '{}' currently defined.".format(obj_name)

    s = ''
    newline = "\n\n"  # blank line to start new paragraph
    try:
        filename = sageinspect.sage_getfile(obj)
        s = '{}**File:** {}{}'.format(s, filename, newline)
    except TypeError:
        pass

    s = newline.join((
        '{}**Type:** {}'.format(s, type(obj)),
        '**Definition:** {}'.format(sageinspect.sage_getdef(obj, obj_name)),
        '**Docstring:**',
        sageinspect.sage_getdoc(obj, obj_name),
    )).rstrip()

    return html_markup(s)


def html_markup(s):
    try:
        return sphinxify(s)
    except Exception:
        pass
    # Not in ReST format, so use docutils
    # to process the preamble ("**File:**" etc.)  and put
    # everything else in a <pre> block.
    i = s.find("**Docstring:**")
    if i != -1:
        preamble = publish_parts(s[:i + 14], writer_name='html')['body']
        s = s[i + 14:]
    else:
        preamble = ""
    return '<div class="docstring">{}<pre>{}</pre></div>'.format(preamble, s)


def source_code(s, globs, system='sage'):
    r"""
    Format an object's source code to process and display in the
    Sage notebook.

    INPUT:

    - ``s`` - a string; a name of an object

    - ``globs`` - a string:object dictionary; a context in which to
      evaluate ``s``

    - ``system`` - a string (default: 'sage'); the system to which to
      confine the search

    OUTPUT:

    - a string containing the object's file, starting line number, and
      source code

    AUTHORS:

    - William Stein: partly taken from IPython for use in Sage

    - Nick Alexander: extensions
    """
    if system not in ['sage', 'python']:
        s = '{}.{}'.format(system, s)

    try:
        obj = eval(s, globs)
    except Exception:
        return html_markup("No object %s" % s)

    try:
        try:
            return html_markup(obj._sage_src_())
        except Exception:
            pass

        newline = "\n\n"  # blank line to start new paragraph
        indent = "    "   # indent source code to mark it as a code block

        filename = sageinspect.sage_getfile(obj)

        try:
            lines, lineno = sageinspect.sage_getsourcelines(obj)
        except IOError as msg:
            return html_markup(str(msg))

        src = indent.join(lines)
        src = '{}{}'.format(indent, format_src(src))
        if lineno is not None:
            output = newline.join((
                "**File:** {}".format(filename),
                "**Source Code** (starting at line {})::".format(lineno),
                src,
            ))
        return html_markup(output)
    except (TypeError, IndexError):
        return html_markup(
            "Source code for {0} is not available.\n"
            "Use {0}? to see the documentation.".format(s))


def syseval(system, cmd, dir=None):
    """
    Evaluate an input with a "system" object that can evaluate inputs
    (e.g., python, gap).

    INPUT:

    - ``system`` - an object with an eval method that takes an input

    - ``cmd`` - a string input

    - ``sage_globals`` - a string:object dictionary

    - dir - a string (default: None); an optional directory to change
      to before calling :func:`system.eval`

    OUTPUT:

    - :func:`system.eval`'s output

    EXAMPLES::

        sage: from sage.misc.python import python
        sage: sagenb.misc.support.syseval(python, '2+4//3')
        3
        ''
        sage: sagenb.misc.support.syseval(python, 'import os; os.chdir(".")')
        ''
        sage: sagenb.misc.support.syseval(python, 'import os; os.chdir(1,2,3)')
        Traceback (most recent call last):
        ...
        TypeError: chdir() takes exactly 1 argument (3 given)
        sage: sagenb.misc.support.syseval(gap, "2+3")
        '5'
    """
    if dir:
        if hasattr(system.__class__, 'chdir'):
            system.chdir(dir)
    # if isinstance(cmd, unicode):
    #     cmd = cmd.encode('utf-8', 'ignore')
    return system.eval(cmd, sage_globals, locals=sage_globals)


######################################################################
# Cython
######################################################################

def cython_import(filename, verbose=False, compile_message=False,
                  use_cache=False, create_local_c_file=True):
    """
    Compile a file containing Cython code, then import and return the
    module.  Raises an ``ImportError`` if anything goes wrong.

    INPUT:

    - ``filename`` - a string; name of a file that contains Cython
      code

    OUTPUT:

    - the module that contains the compiled Cython code.
    """
    name, build_dir = cython(filename, verbose=verbose,
                             compile_message=compile_message,
                             use_cache=use_cache,
                             create_local_c_file=create_local_c_file)
    sys.path.append(build_dir)
    return import_module(name)


def cython_import_all(filename, globals, verbose=False, compile_message=False,
                      use_cache=False, create_local_c_file=True):
    """
    Imports all non-private (i.e., not beginning with an underscore)
    attributes of the specified Cython module into the given context.
    This is similar to::

        from module import *

    Raises an ``ImportError`` exception if anything goes wrong.

    INPUT:

    - ``filename`` - a string; name of a file that contains Cython
      code
    """
    m = cython_import(filename, verbose=verbose,
                      compile_message=compile_message,
                      use_cache=use_cache,
                      create_local_c_file=create_local_c_file)
    for k, x in vars(m).items():
        if not k.startswith('_'):
            globals[k] = x


###################################################
# Preparser
###################################################

# Fallback functions in case sage is not present
def preparse_fb(line, *args, **kwds):
    return line


def do_preparse():
    """
    Return True if the preparser is set to on, and False otherwise.
    """
    return _do_preparse


########################################################################
#
# Automatic Creation of Variable Names
#
# See the docstring for automatic_names below for an explanation of how
# this works.
#
########################################################################

_automatic_names = False


class AutomaticVariable(Expression):
    """
    An automatically created symbolic variable with an additional
    :meth:`__call__` method designed so that doing self(foo,...)
    results in foo.self(...).
    """
    def __call__(self, *args, **kwds):
        """
        Call method such that self(foo, ...) is transformed into
        foo.self(...).  Note that self(foo=...,...) is not
        transformed, it is treated as a normal symbolic
        substitution.
        """
        if len(args) == 0:
            return super(self.__class__, self).__call__(**kwds)
        return args[0].__getattribute__(str(self))(*args[1:], **kwds)


def automatic_name_eval(s, globals, max_names=10000):
    """
    Exec the string ``s`` in the scope of the ``globals``
    dictionary, and if any :exc:`NameError` are raised, try to
    fix them by defining the variable that caused the error to be
    raised, then eval again.  Try up to ``max_names`` times.

    INPUT:

       - ``s`` -- a string
       - ``globals`` -- a dictionary
       - ``max_names`` -- a positive integer (default: 10000)
    """
    # This entire automatic naming system really boils down to
    # this bit of code below.  We simply try to exec the string s
    # in the globals namespace, defining undefined variables and
    # functions until everything is defined.
    for _ in range(max_names):
        try:
            exec(s, globals)
            return
        except NameError as msg:
            # Determine if we hit a NameError that is probably
            # caused by a variable or function not being defined:
            if len(msg.args) == 0:
                raise  # not NameError with
                # specific variable name
            v = msg.args[0].split("'")
            if len(v) < 2:
                raise  # also not NameError with
                # specific variable name We did
                # find an undefined variable: we
                # simply define it and try
                # again.
            nm = v[1]
            globals[nm] = AutomaticVariable(SR, SR.var(nm))
    raise NameError(
        "Too many automatic variable names and functions created "
        "(limit=%s)" % max_names)


def automatic_name_filter(s):
    """
    Wrap the string ``s`` in a call that will cause evaluation of
    ``s`` to automatically create undefined variable names.

    INPUT:

       - ``s`` -- a string

    OUTPUT:

       - a string
    """
    return (
        '_support_.automatic_name_eval(_support_.base64.b64decode("%s"),'
        'globals())' % base64.b64encode(s))


def automatic_names(state=None):
    """
    Turn automatic creation of variables and functional calling of
    methods on or off.  Returns the current ``state`` if no
    argument is given.

    This ONLY works in the Sage notebook.  It is not supported on
    the command line.

    INPUT:

    - ``state`` -- a boolean (default: None); whether to turn
      automatic variable creation and functional calling on or off

    OUTPUT:

    - a boolean, if ``state`` is None; otherwise, None

    EXAMPLES::

        sage: automatic_names(True)      # not tested
        sage: x + y + z                  # not tested
        x + y + z

    Here, ``trig_expand``, ``y``, and ``theta`` are all
    automatically created::

        sage: trig_expand((2*x + 4*y + sin(2*theta))^2)   # not tested
        4*(sin(theta)*cos(theta) + x + 2*y)^2

    IMPLEMENTATION: Here's how this works, internally.  We define
    an :class:`AutomaticVariable` class derived from
    :class:`~sage.symbolic.all.Expression`.  An instance of
    :class:`AutomaticVariable` is a specific symbolic variable,
    but with a special :meth:`~AutomaticVariable.__call__` method.
    We overload the call method so that ``foo(bar, ...)`` gets
    transformed to ``bar.foo(...)``.  At the same time, we still
    want expressions like ``f^2 - b`` to work, i.e., we don't want
    to have to figure out whether a name appearing in a
    :exc:`NameError` is meant to be a symbolic variable or a
    function name. Instead, we just make an object that is both!

    This entire approach is very simple---we do absolutely no
    parsing of the actual input.  The actual real work amounts to
    only a few lines of code.  The primary catch to this approach
    is that if you evaluate a big block of code in the notebook,
    and the first few lines take a long time, and the next few
    lines define 10 new variables, the slow first few lines will
    be evaluated 10 times.  Of course, the advantage of this
    approach is that even very subtle code that might inject
    surprisingly named variables into the namespace will just work
    correctly, which would be impossible to guarantee with static
    parsing, no matter how sophisticated it is.  Finally, given
    the target audience: people wanting to simplify use of Sage
    for Calculus for undergrads, I think this is an acceptable
    tradeoff, especially given that this implementation is so
    simple.
    """
    global _automatic_names
    if state is None:
        return _automatic_names
    _automatic_names = bool(state)


# Code execution

def break_code(code, nodes=True):
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    tree = ast.parse(code)
    limits = ((node.lineno - 1, node.col_offset) for node in tree.body)
    line_offsets = [0]
    for line in code.splitlines(True)[:-1]:
        line_offsets.append(line_offsets[-1] + len(line))
    offsets = [line_offsets[lin] + col for lin, col in limits]
    offsets.append(len(code))
    lines = []
    for i, offset in enumerate(offsets[:-1]):
        node = tree.body[i]
        line = code[offset:offsets[i + 1]].rstrip(' \t')
        lines.append([line, node] if nodes else line)
    return lines


def test_fimp(code, code0, code1):
    node = code[1]
    test = isinstance(node, ast.ImportFrom) and node.module == '__future__'
    if test:
        code0.append(code)
    else:
        code1.append(code)
    return test


def relocate_future_imports(brk_code):
    """
    Relocates imports from __future__ to the beginning of the
    file. Raises ``SyntaxError`` if the string does not have proper
    syntax.

    OUTPUT:

    - (string, string) -- a tuple consisting of the string without
      ``__future__`` imports and the ``__future__`` imports.

    EXAMPLES::

        sage: from sagenb.misc.format import relocate_future_imports
        sage: relocate_future_imports('')
        '\n'
        sage: relocate_future_imports('foobar')
        '\nfoobar'
        sage: relocate_future_imports(
            'from __future__ import division\nprint("Hi!")')
        'from __future__ import division\n\nprint("Hi!")'
        sage: relocate_future_imports(
            'from __future__ import division;print("Testing")')
        'from __future__ import division\nprint("Testing")'
        sage: relocate_future_imports(
            'from __future__ import division\nprint("Testing!") '
            '# from __future__ import division does Blah')
        'from __future__ import division\n\nprint("Testing!") '\
        '# from __future__ import division does Blah'
        sage: relocate_future_imports(
            '# -*- coding: utf-8 -*-\nprint("Testing!")\n'
            'from __future__ import division, operator\nprint("Hey!")')
            'from __future__ import division,operator\n# -*- '\
            'coding: utf-8 -*-\nprint("Testing!")\n\nprint("Hey!")'
    """
    try:
        node = brk_code[0]
    except IndexError:
        return brk_code

    code0 = []
    code1 = []
    first = 0
    test = True
    while test:
        try:
            code = brk_code[first]
        except IndexError:
            return brk_code

        test = test_fimp(code, code0, code1)
        first += 1

    for i in range(first, len(brk_code)):
        code = brk_code[i]
        if test_fimp(code, code0, code1):
            prev = code1[-1]
            if code[0].endswith('\n') and prev[0].endswith(';'):
                prev[0] = '{}\n'.format(prev[0][:-1])

    if code0:
        code0[-1][0] = '{}\n'.format(code0[-1][0])

    code0.extend(code1)
    return code0

    fimp = (i for i, node in enumerate(brk_code)
            if isinstance(node[1], ast.ImportFrom) and
            node[1].module == '__future__')
    iprev = -1
    for i in fimp:
        code1.extend(brk_code[iprev+1:i-2])
        node = brk_code[i]
        end_char = node[0][-1]
        code0.append(('{}\n'.format(node[0]), node[1]))
        try:
            prev = brk_code[i-1]
        except IndexError:
            pass
        else:
            if end_char == '\n' and prev[0][-1] == ';':
                prev = ('{}\n'.format(prev[0][:-1]), prev[1])
        code1.append(prev)
        iprev = i
    code1.extend(brk_code[iprev+1:])
    code0.extend(code1)
    return code0


def displayhook_hack(brk_code):
    """
    Modified version of string so that ``exec``'ing it results in
    displayhook possibly being called.

    STRING:

        - ``string`` - a string

    OUTPUT:

        - string formated so that when exec'd last line is printed if
          it is an expression
    """
    code = [node[0] for node in brk_code]
    i = len(brk_code)-1
    if not isinstance(brk_code[i][1], ast.Expr):
        return ''.join(code)
    while (i > 0 and isinstance(brk_code[i-1][1], ast.Expr) and
            brk_code[i-1][0].endswith(';')):
        i -= 1
    code0 = ''.join(code[:i])
    code1 = ''.join(code[i:])
    code1 = "exec(compile({!r}, '', 'single'))".format(code1 if code1 else '')
    return ''.join((code0, code1))


def reformat_code(code):
    return displayhook_hack(relocate_future_imports(break_code(code)))


def preparse_worksheet_cell(s, globals):
    """
    Preparse the contents of a worksheet cell in the notebook,
    respecting the user using ``preparser(False)`` to turn off the
    preparser.  This function calls
    :func:`~sage.repl.preparse.preparse_file` which also reloads
    attached files.  It also does displayhook formatting by calling
    the :func:`~sagenb.notebook.interfaces.format.displayhook_hack`
    function.

    INPUT:

    - ``s`` - a string containing code

    - ``globals`` - a string:object dictionary; passed directly to
      :func:`~sage.repl.preparse.preparse_file`

    OUTPUT:

        - a string
    """
    if do_preparse():
        s = preparse_file(s, globals=globals)
    s = reformat_code(s)
    if _automatic_names:
        s = automatic_name_filter(s)
    return s


def execute_code(code, globals, mode='raw', start_label='', print_time=False):
    code = base64.b64decode(code.encode('utf-8')).decode('utf-8')
    if mode != 'raw':
        print(start_label)

    if mode == 'raw':
        pass
    elif mode == 'python':
        code = reformat_code(code)
    elif mode == 'sage':
        code = preparse_worksheet_cell(code, globals)
    else:
        code = 'pass'
    if print_time and code != 'raw':
        code = '\n'.join((
            code, '\nprint("CPU time: %.2f s,  Wall time: %.2f '
                  's"%(cputime(__SAGE_t__), walltime(__SAGE_w__)))'))

    # TODO: use previous ast analisys done when code is reformated
    exec(code, globals)
