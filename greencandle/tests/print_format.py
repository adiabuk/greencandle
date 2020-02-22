# pylint: disable=too-few-public-methods,attribute-defined-outside-init,no-else-return

"""
helper functions for print formatting
"""

#from cStringIO import StringIO
from io import StringIO
import datetime
import os
import sys
import textwrap
import time

ROWS, COLUMNS = os.popen('stty size', 'r').read().split()

class SuppressStdoutStderr():
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).
    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])

class CaptureText(list):
    """ class for capturing stdout """

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

def print_line(length=111, char='-'):
    """ print a line of a given length """
    print(char * length)

def print_if_not_silent(text, silent):
    """ Print text if silent is False """
    if not silent:
        print(text)

def print_banner(text, length=48, char='-'):
    """
    print given text as a banner with a border of given length
    and keep all line lengths wrapped to given length
    """

    print_line(length, char)
    dedented_text = textwrap.dedent(text).strip()
    print(textwrap.fill(dedented_text, width=length))
    print_line(length, char)

def get_date_stamp():
    """ Return string timestamp for use in filenames """
    epoch = time.time()
    date_stamp = datetime.datetime.fromtimestamp(epoch).strftime('%Y-%m-%d_'
                                                                 '%H-%M-%S')
    return date_stamp

def print_status_line(strings, exit_code):
    """
    print given string along with colored OK / FAILED message on the right
    depending on given status code, 0=SUCCESS, other=FAILED
    """
    # Colors used to print status block
    bold = '\033[1m'
    green = '\033[92m'
    red = '\033[31m'
    end = '\033[0m'

    # populate OK/FAILED string with color in bold
    status = green + "OK" if exit_code == 0 else red + 'FAILED'
    status_block = (bold + '[ ' + '  ' + status + '  ' +  end + bold
                    + ' ]' + end)

    offset = len(strings)
    line_new = strings +":" + status_block.rjust(int(COLUMNS)-offset)
    print(line_new + '\n')
    return exit_code
