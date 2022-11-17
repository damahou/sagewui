import os


def graphics_filename(ext='.png'):
    """
    Return the next available canonical
    filename for a plot/graphics file in the current working directory.

    INPUT:

    - ``ext`` -- (default: ``".png"``) A file extension (including the dot)
      for the filename.

    OUTPUT:

    The path of the temporary file created. In the notebook, this is
    a filename without path in the current directory. Otherwise, this
    an absolute path.

    EXAMPLES::

        sage: from sage.misc.temporary_file import graphics_filename
        sage: print(graphics_filename())  # random, typical filename for sagenb
        sage0.png

    TESTS:

    When doctesting, this returns instead a random temporary file.
    We check that it's a file inside ``SAGE_TMP`` and that the extension
    is correct::

        sage: fn = graphics_filename(ext=".jpeg")
        sage: fn.startswith(str(SAGE_TMP))
        True
        sage: fn.endswith('.jpeg')
        True
    """
    i = 0
    while os.path.exists('sage{}{}'.format(i, ext)):
        i += 1
    filename = 'sage{}{}'.format(i, ext)
    return filename
