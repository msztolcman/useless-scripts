#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

__version__   = 'version 0.1'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2013'
__program__   = 'word2phone - translate word to numbers on phone keybord'
__date__      = '2013-06-12'
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

import sys

m = {
    'a': 2, 'b': 2, 'c': 2, 'd': 3, 'e': 3, 'f': 3, 'g': 4, 'h': 4, 'i': 4,
    'j': 5, 'k': 5, 'l': 5, 'm': 6, 'n': 6, 'o': 6, 'p': 7, 'q': 7, 'r': 7,
    's': 7, 't': 8, 'u': 8, 'v': 8, 'w': 9, 'x': 9, 'y': 9, 'z': 9,

    'ą': 2, 'ć': 2, 'ę': 3, 'ł': 5, 'ń': 6, 'ó': 6, 'ś': 7, 'ż': 9, 'ź': 9,
}

if len(sys.argv) > 1:
    word = sys.argv[1]
else:
    word = sys.stdin.read()

word = word.lower()
for letter in word:
    try:
        print(m[letter], sep='', end='')
    except KeyError as e:
        print(letter, sep='', end='')
print()
