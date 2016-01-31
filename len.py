#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Show length of data
"""

from __future__ import print_function, unicode_literals

import sys

__version__ = 'version 0.2'
__author__ = 'Marcin Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2012'
__program__ = 'len.py - show length of data'
__date__ = '2012-07-13'
__license__ = 'GPL v.2'

__desc__ = '''%(desc)s
%(author)s %(copyright)s
license: %(license)s
version %(version)s (%(date)s)''' % {
  'desc': __program__,
  'author': __author__,
  'copyright': __copyright__,
  'license': __license__,
  'version': __version__,
  'date': __date__
}

# pylint: disable=invalid-name
data = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()

try:
    data = data.decode('utf-8')
except AttributeError:
    pass

print(len(data))
