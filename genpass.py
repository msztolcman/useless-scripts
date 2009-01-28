#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
# $Id$

from __future__ import print_function

__version__   = 'version 0.3.1'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2004 - 2009'
__program__   = 'genpass.py - generate secure passwords'
__date__      = '2009-01-28'
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
import os.path
import random
import sys

USAGE = '''%s [-l|--letters] [-b|--bigletters] [-d|--digits] [-c|--chars] [-s|--special] [-g|--length length] [-q|--quant quant] [-h|--help]
DEFAULT:
    %s --letters --length=8 --quant=1''' % (os.path.basename (sys.argv[0]), os.path.basename (sys.argv[0]))

def exit (code, msg):
  print (msg, file=sys.stderr)
  raise SystemExit (code)



# opcje
opts_short  = 'lbdcsq:g:h'
opts_long   = ('letters', 'bigletters', 'digits', 'chars', 'special', 'quant=', 'length=', 'help')
try:
    opts, args = getopt.gnu_getopt (sys.argv[1:], opts_short, opts_long)
except getopt.GetoptError:
    exit (1, USAGE)

quant   = 1
length  = 8

# zestawy znakow
z1      =r'qwertyuiopasdfghjklzxcvbnm'
z2      =r'QWERTYUIOPASDFGHJKLZXCVBNM'
z3      =r'1234567890'
z4      =r'!@#$%^&*_+=-~;:.>,<?'
z5      =r'''`(){}[]'"\|/'''

# ustalamy zestaw z ktorego losujemy
chars = r''
for o, a in opts:
  if o in ('-h', '--help'):
    exit (0, USAGE)
  elif o in ('-l', '--letters'):
    chars += z1
  elif o in ('-b', '--bigletters'):
    chars += z2
  elif o in ('-d', '--digits'):
    chars += z3
  elif o in ('-c', '--chars'):
    chars += z4
  elif o in ('-s', '--special'):
    chars += z5
  elif o in ('-q', '--quant'):
    quant = a
  elif o in ('-g', '--length'):
    length = a

try:
  length    = int (length)
  quant     = int (quant)
except:
  exit (2, USAGE)

all_chars = len (chars)
if all_chars == 0:
  chars = z1[:]
  all_chars = len (chars)

random.seed ()
for j in range (quant):
	passwd = ''
	for i in range (length):
		passwd += random.choice (chars)
	print (passwd)

# vim: ft=python
