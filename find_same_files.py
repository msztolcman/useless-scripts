#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function

__version__   = 'version 0.1'
__author__    = 'Marcin Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2012'
__program__   = 'find_same_files.py - find identical files using their checksums'
__date__      = '2012-12-22'
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

import getopt
import hashlib
import os, os.path
import sys

DEBUG = False
MULTI = False
OMMIT_LINKS = True

def usage():
    print('%s [-s|--size size_in_bytes|MAX] [-v|--verbose] [-m|--multi] [-l|--ommit-links] root_directory' % (sys.argv[0], ))

try:
    opts_short  = 's:vml'
    opts_long   = ('size=', 'verbose', 'multi', 'ommit-links')
    opts, args = getopt.gnu_getopt(sys.argv[1:], opts_short, opts_long)

    if len(args) < 1:
        raise getopt.GetoptError('Missing root dorectory')
except getopt.GetoptError:
    usage()
    sys.exit(1)

ROOT        = args[0]
MAX_SIZE    = 4096
for o, a in opts:
    if o in ('-s', '--size'):
        if a == 'MAX':
            MAX_SIZE = -1
        else:
            MAX_SIZE = int(a)
    elif o in ('-v', '--verbose'):
        DEBUG = True
    elif o in ('-m', '--multi'):
        MULTI = True
    elif o in ('-l', '--ommit-links'):
        OMMIT_LINKS = False

def debug(*a):
    if not DEBUG:
        return
    print('DEBUG:', ", ".join( [str(i) for i in a] ))

FILES = {}
for root, dirs, files in os.walk(ROOT):
    for f in files:
        path = os.path.join(root, f)
        debug('PATH:', path)
        if not os.access(path, os.R_OK) or not os.path.isfile(path) or (OMMIT_LINKS and os.path.islink(path)):
            debug('Skipping "%s".' % path)
            continue
        try:
            s = os.path.getsize(path)
            debug('REAL SIZE:', s)
            if -1 < MAX_SIZE < s: # MAX_SIZE > -1 and s > MAX_SIZE:
                s = MAX_SIZE
            debug('SIZE:', s)

            with open(path) as fh:
                md5sum = hashlib.md5(fh.read(s)).hexdigest()
                debug('MD5SUM:', md5sum)

            ret = (path, s)
            try:
                FILES[md5sum].append(ret)
            except KeyError:
                FILES[md5sum] = [ ret, ]
        except Exception, e:
            print('ERROR:', e, type(e))

# jeśli były debugi, to oddzielamy od nich wyniki
if DEBUG:
    print("\n\n")

for md5sum, data in sorted(FILES.items(), key=lambda a: a[0]):
    if MULTI and len(data) == 1:
        continue
    print(md5sum)
    print(", ".join( "%s (%s)" % i for i in data ))
    print()

