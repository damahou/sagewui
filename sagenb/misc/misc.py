# -*- coding: utf-8 -*-
"""
Miscellaneous Notebook Functions

TESTS:

Check that github issue #195 is fixed::

    sage: from sagenb.misc.misc import mathjax_macros
    sage: type(mathjax_macros)
    <type 'list'>

"""

#############################################################################
#       Copyright (C) 2006, 2007 William Stein <wstein@gmail.com>
#                 (C) 2015 J Miguel Farto <jmfarto@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################
from __future__ import absolute_import

import os
import resource
import signal
import socket
import stat
import subprocess
import tempfile
import time


def tmp_filename(name='tmp', ext='', **kwargs):
    # TODO: rethink this
    # based on sage.misc.temporary_file
    handle, tmp = tempfile.mkstemp(prefix=name, suffix=ext, **kwargs)
    os.close(handle)
    return tmp


def tmp_dir(name='dir', ext='', **kwargs):
    # TODO: rethink this
    # based on sage.misc.temporary_file
    tmp = tempfile.mkdtemp(prefix=name, suffix=ext, **kwargs)
    return '{}{}'.format(tmp, os.sep)


def cputime(t=0):
    try:
        t = float(t)
    except TypeError:
        t = 0.0
    u, s = resource.getrusage(resource.RUSAGE_SELF)[:2]
    return u + s - t


def walltime(t=0):
    return time.time() - t


def word_wrap(s, ncols=85):
    t = []
    if ncols == 0:
        return s
    for x in s.split('\n'):
        if len(x) == 0 or x.lstrip()[:5] == 'sage:':
            t.append(x)
            continue
        while len(x) > ncols:
            k = ncols
            while k > 0 and x[k] != ' ':
                k -= 1
            if k == 0:
                k = ncols
                end = '\\'
            else:
                end = ''
            t.append(x[:k] + end)
            x = x[k:]
            k = 0
            while k < len(x) and x[k] == ' ':
                k += 1
            x = x[k:]
        t.append(x)
    return '\n'.join(t)


#############################################################
# File permissions
# May need some changes on Windows.
#############################################################
def set_restrictive_permissions(filename, allow_execute=False):
    x = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    if allow_execute:
        x = x | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(filename, x)


def set_permissive_permissions(filename):
    os.chmod(filename, stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH |
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
             stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)


def encoded_str(obj, encoding='utf-8'):
    ur"""
    Takes an object and returns an encoded str human-readable representation.

    EXAMPLES::

        sage: from sagenb.misc.misc import encoded_str
        sage: encoded_str(
            u'\u011b\u0161\u010d\u0159\u017e\xfd\xe1\xed\xe9\u010f\u010e'
            ) == 'ěščřžýáíéďĎ'
        True
        sage: encoded_str(u'abc')
        'abc'
        sage: encoded_str(123)
        '123'
    """
    if isinstance(obj, unicode):
        return obj.encode(encoding, 'ignore')
    return str(obj)


def unicode_str(obj, encoding='utf-8'):
    ur"""
    Takes an object and returns a unicode human-readable representation.

    EXAMPLES::

        sage: from sagenb.misc.misc import unicode_str
        sage: unicode_str('ěščřžýáíéďĎ'
            ) == u'\u011b\u0161\u010d\u0159\u017e\xfd\xe1\xed\xe9\u010f\u010e'
        True
        sage: unicode_str('abc')
        u'abc'
        sage: unicode_str(123)
        u'123'
    """
    if isinstance(obj, str):
        return obj.decode(encoding, 'ignore')
    elif isinstance(obj, unicode):
        return obj
    return unicode(obj)


def ignore_nonexistent_files(curdir, dirlist):
    """
    Returns a list of non-existent files, given a directory and its
    contents.  The returned list includes broken symbolic links.  Use
    this, e.g., with :func:`shutil.copytree`, as shown below.

    INPUT:

    - ``curdir`` - a string; the name of the current directory

    - ``dirlist`` - a list of strings; names of ``curdir``'s contents

    OUTPUT:

    - a list of strings; names of ``curdir``'s non-existent files

    EXAMPLES::

        sage: import os, shutil
        sage: from sagenb.misc.misc import ignore_nonexistent_files
        sage: opj = os.path.join; ope = os.path.exists; t = tmp_dir()
        sage: s = opj(t, 'src'); t = opj(t, 'trg'); hi = opj(s, 'hi.txt');
        sage: os.makedirs(s)
        sage: f = open(hi, 'w'); f.write('hi'); f.close()
        sage: os.symlink(hi, opj(s, 'good.txt'))
        sage: os.symlink(opj(s, 'bad'), opj(s, 'bad.txt'))
        sage: slist = sorted(os.listdir(s)); slist
        ['bad.txt', 'good.txt', 'hi.txt']
        sage: map(lambda x: ope(opj(s, x)), slist)
        [False, True, True]
        sage: map(lambda x: os.path.islink(opj(s, x)), slist)
        [True, True, False]
        sage: shutil.copytree(s, t)
        Traceback (most recent call last):
        ...
        Error: [('.../src/bad.txt',
                 '.../trg/bad.txt',
                 "[Errno 2] No such file or directory: '.../src/bad.txt'")]
        sage: shutil.rmtree(t); ope(t)
        False
        sage: shutil.copytree(s, t, ignore = ignore_nonexistent_files)
        sage: tlist = sorted(os.listdir(t)); tlist
        ['good.txt', 'hi.txt']
        sage: map(lambda x: ope(opj(t, x)), tlist)
        [True, True]
        sage: map(lambda x: os.path.islink(opj(t, x)), tlist)  # Note!
        [False, False]
    """
    ignore = []
    for x in dirlist:
        if not os.path.exists(os.path.join(curdir, x)):
            ignore.append(x)
    return ignore


def N_(message):
    return message


def nN_(message_singular, message_plural):
    return [message_singular, message_plural]


def print_open_msg(address, port, secure=False, path=""):
    """
    Print a message on the screen suggesting that the user open their
    web browser to a certain URL.

    INPUT:

    - ``address`` -- a string; a computer address or name

    - ``port`` -- an int; a port number

    - ``secure`` -- a bool (default: False); whether to prefix the URL
      with 'http' or 'https'

    - ``path`` -- a string; the URL's path following the port.

    EXAMPLES::

        sage: from sagenb.misc.misc import print_open_msg
        sage: print_open_msg('localhost', 8080, True)
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        │ Open your web browser to https://localhost:8080  │
        │                                                  │
        └──────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 8080, False)
        ┌────────────────────────────────────────────────────┐
        │                                                    │
        │ Open your web browser to http://sagemath.org:8080  │
        │                                                    │
        └────────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 90, False)
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        │ Open your web browser to http://sagemath.org:90  │
        │                                                  │
        └──────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 80, False)
        ┌────────────────────────────────────────────────┐
        │                                                │
        │  Open your web browser to http://sagemath.org  │
        │                                                │
        └────────────────────────────────────────────────┘
    """
    if port == 80:
        port = ''
    else:
        port = ':%s' % port
    s = "Open your web browser to http%s://%s%s%s" % (
        's' if secure else '', address, port, path)
    t = len(s)
    if t % 2:
        t += 1
        s += ' '
    n = max(t + 4, 50)
    k = n - t - 1
    j = k / 2
    msg = '┌' + '─' * (n - 2) + '┐\n'
    msg += '│' + ' ' * (n - 2) + '│\n'
    msg += '│' + ' ' * j + s + ' ' * j + '│\n'
    msg += '│' + ' ' * (n - 2) + '│\n'
    msg += '└' + '─' * (n - 2) + '┘'
    print msg


def find_next_available_port(interface, start, max_tries=100, verbose=False):
    """
    Find the next available port at a given interface, that is, a port for
    which a current connection attempt returns a 'Connection refused'
    error message.  If no port is found, raise a RuntimeError exception.

    INPUT:

    - ``interface`` - address to check

    - ``start`` - an int; the starting port number for the scan

    - ``max_tries`` - an int (default: 100); how many ports to scan

    - ``verbose`` - a bool (default: True); whether to print information
      about the scan

    OUTPUT:

    - an int - the port number

    EXAMPLES::

        sage: from sagenb.misc.misc import find_next_available_port
        sage: find_next_available_port(
            '127.0.0.1',
            9000, verbose=False)   # random output -- depends on network
        9002
    """
    def handler(signum, frame):
        raise UserWarning('timed out')

    alarm_count = 0
    for port in range(start, start + max_tries + 1):
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((interface, port))
        except socket.error, msg:
            if msg[1] == 'Connection refused':
                if verbose:
                    print "Using port = %s" % port
                return port
        except UserWarning:
            if verbose:
                print "Port %s timed out." % port
                print "Trying next port..."
            continue
        except KeyboardInterrupt:
            if verbose:
                print "alarm"
            alarm_count += 1
            if alarm_count >= 10:
                break
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            signal.alarm(0)
        if verbose:
            print "Port %s is already in use." % port
            print "Trying next port..."
    raise RuntimeError("no available port.")


def open_page(browser, address, port, secure, path=""):
    rsrc = 'https' if secure else 'http'

    os.system('%s %s://%s:%s%s 1>&2 > /dev/null &' %
              (browser, rsrc, address, port, path))


def system_command(cmd, msg=None):
    msg = cmd if msg is None else '\n'.join((msg, cmd))
    print(msg)
    subprocess.call([cmd], shell=True)
