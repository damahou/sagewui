# -*- coding: utf-8 -*-
"""
Code formatting functions for the notebook

Functions used to format code to be used in the notebook.

AUTHORS:

 - William Stein (?) - Initial revision

 - Tim Dumol (Oct. 16, 2009) - Added additional formatting functions
"""
from __future__ import absolute_import


import ast
import re

from .misc import unicode_str

_futureimport_re = re.compile(
    r'((?:from __future__ import [^;\n]+)+)(?:;\s*)?(.*)')


def break_code(string, nodes=True):
    tree = ast.parse(string)
    limits = ((node.lineno - 1, node.col_offset) for node in tree.body)
    line_offsets = [0]
    for line in string.splitlines(True)[:-1]:
        line_offsets.append(line_offsets[-1] + len(line))
    offsets = [line_offsets[lin] + col for lin, col in limits]
    offsets.append(len(string))
    lines = []
    for i, offset in enumerate(offsets[:-1]):
        node = tree.body[i]
        line = string[offset:offsets[i + 1]].rstrip(u' \t')
        lines.append((line, node) if nodes else line)
    return lines


def relocate_future_imports(string):
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
            'from __future__ import division\nprint "Hi!"')
        'from __future__ import division\n\nprint "Hi!"'
        sage: relocate_future_imports(
            'from __future__ import division;print "Testing"')
        'from __future__ import division\nprint "Testing"'
        sage: relocate_future_imports(
            'from __future__ import division\nprint "Testing!" '
            '# from __future__ import division does Blah')
        'from __future__ import division\n\nprint "Testing!" '\
        '# from __future__ import division does Blah'
        sage: relocate_future_imports(
            '# -*- coding: utf-8 -*-\nprint "Testing!"\n'
            'from __future__ import division, operator\nprint "Hey!"')
            'from __future__ import division,operator\n# -*- '\
            'coding: utf-8 -*-\nprint "Testing!"\n\nprint "Hey!"'
    """
    lines = string.splitlines()
    import_lines = []
    parse_tree = ast.parse(string)
    future_imports = [x for x in parse_tree.body
                      if x.__class__ == ast.ImportFrom and
                      x.module == '__future__']
    for imp in future_imports:
        line = lines[imp.lineno - 1]
        lines[imp.lineno - 1] = line[:imp.col_offset] + re.sub(
            r'from\s+__future__\s+import\s+%s;?\s*' % ''.join(
                [r'\s*%s\s*,?\s*' % name.name for name in imp.names]),
            '',
            line[imp.col_offset:], 1)
        import_lines.append('from __future__ import %s' %
                            ','.join([name.name for name in imp.names]))

    return '\n'.join(import_lines) + '\n' + '\n'.join(lines)


def format_for_pexpect(string, number):
    """
    Formats a string for execution by the pexpect WorksheetProcess
    implementation.

    Currently does the following:

    * Adds a magic comment to enable utf-8 encoding
    * Moves all __future__ imports to start of file.
    * Changes system prompt to `prompt`
    * Prints a START message appended with `number`
    * Appends `string` after processing with :meth: `displayhook_hack`
    """
    string = '\n'.join((
        'print "START%s"',
        '%s',
        )) % (number,
              displayhook_hack(string).encode('utf-8', 'ignore'))
    try:
        string = relocate_future_imports(string)
    except SyntaxError:
        # Syntax error anyways, so no need to relocate future imports.
        pass
    return string


def displayhook_hack(string):
    """
    Modified version of string so that ``exec``'ing it results in
    displayhook possibly being called.

    STRING:

        - ``string`` - a string

    OUTPUT:

        - string formated so that when exec'd last line is printed if
          it is an expression

    EXAMPLES::

        sage: from sagenb.misc.format import displayhook_hack
        sage: displayhook_hack('\n12\n')
        "\nexec compile(u'12' + '\\n', '', 'single')"
        sage: displayhook_hack('\ndef my_fun(foo):\n    print foo\n')
        '\ndef my_fun(foo):\n        print foo'
        sage: print displayhook_hack(
            '\nclass A:\n    def __init__(self, foo):\n        self.foo\nb = '
            'A(8)\nb')
        <BLANKLINE>
        class A:
            def __init__(self, foo):
                self.foo
        b = A(8)
        exec compile(u'b' + '\n', '', 'single')
    """
    # This function is all so the last line (or single lines) will
    # implicitly print as they should, unless they are an assignment.
    # If anybody knows a better way to do this, please tell me!
    string = string.splitlines()
    i = len(string) - 1
    if i >= 0:
        while len(string[i]) > 0 and string[i][0] in ' \t':
            i -= 1
        final_lines = unicode_str('\n'.join(string[i:]))
        if not final_lines.startswith('def '):
            try:
                compile(final_lines + '\n', '', 'single')
                string[
                    i] = "exec compile(%r + '\\n', '', 'single')" % final_lines
                string = string[:i + 1]
            except SyntaxError:
                pass
    return '\n'.join(string)
