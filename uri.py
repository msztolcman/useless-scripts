#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

__version__   = 'version 0.1'
__author__    = 'Marcin Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2012'
__program__   = 'uri.py - uri encode/uri decode data'
__date__      = '2012-07-13'
__license__   = 'GPL v.2'

__desc__      = '''%(desc)s
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

import os, os.path
import sys

import argparse
try:
    from urllib.parse import quote_plus, unquote_plus, quote, unquote
except ImportError:
    from urllib import quote_plus, unquote_plus, quote, unquote

def main ():
    parser = argparse.ArgumentParser (description='URI data encode or decode')
    parser.add_argument ('-d', '--decode', action='store_true', help='decode data if given')
    parser.add_argument ('-s', '--space_as_plus', action='store_false', help='encode/decode space as plus sign instead of %%20')
    parser.add_argument ('input', nargs='?', help='data to process')

    args = parser.parse_args ()

    if args.decode:
        if args.space_as_plus:
            func = unquote
        else:
            func = unquote_plus
    else:
        if args.space_as_plus:
            func = quote
        else:
            func = quote_plus

    if not args.input:
        data = sys.stdin.read ().rstrip (os.linesep)
    else:
        data = args.input

    print (func (data))

if __name__ == '__main__':
    main ()

