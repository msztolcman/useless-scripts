#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

__version__   = 'version 0.3'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2012'
__program__   = 'calc - simple math operation on it\'s stdin'
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

try:
    from functools import reduce
except ImportError:
    pass
import os.path
import sys

def op_add(a, b):
    return float(a) + float(b)

def op_sub(a, b):
    return float(a) - float(b)

def op_mul(a, b):
    return float(a) * float(b)

def op_div(a, b):
    return float(a) / float(b)

def op_pow(a, b):
    return pow(float(a), float(b))

def op_sqr(a, b):
    return pow(float(a), (1 / float(b)))

ops = {
    '+': op_add,    '-': op_sub,    '*': op_mul,    '/': op_div,    '**': op_pow,
    'add': op_add,  'sub': op_sub,  'mul': op_mul,  'div': op_div,  'pow': op_pow,
    'sqr': op_sqr,  'sqrt': op_sqr,
}

if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help', ):
    print('[INPUT] | math [+|add|-|sub|*|mul|/|div|**|pow|sqr|sqrt]')
    sys.exit(0)
elif len(sys.argv) > 1 and sys.argv[1] in ('-v', '--version', ):
    print(__desc__)
    sys.exit(0)
elif len(sys.argv) > 1:
    op = ops[sys.argv[1]]
elif os.path.basename(sys.argv[0]) in ('mul', 'div', 'sub', 'pow', 'sqr', 'sqrt', ):
    op = ops[os.path.basename(sys.argv[0])]
else:
    op = ops['+']

print(reduce(op, sys.stdin))
