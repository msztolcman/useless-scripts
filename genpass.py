#!/usr/bin/env python
"""
	version: 0.3.1
	date: 2004-10-20
	author: Marcin Sztolcman <marcin@urzenia.net>
	license: GPL
"""

import random, sys
from getopt import gnu_getopt as getopt

USAGE = '''%(prog)s [-l|--letters] [-b|--bigletters] [-d|--digits] [-c|--chars] [-s|--special] [-g|--length length] [-q|--quant quant] [-h|--help]
DEFAULT:
    %(prog)s --letters --length=8 --quant=1''' % {'prog': sys.argv[0]}

def exit(code, msg):
  print >>sys.stderr, msg
  raise SystemExit, code



# opcje
sh_opts='lbdcsq:g:h'
lg_opts=('letters', 'bigletters', 'digits', 'chars', 'special', 'quant=', 'length=', 'help')
try:    opts, args = getopt(sys.argv[1:], sh_opts, lg_opts)
except: exit(1, USAGE)

quant = 1
length = 8

# zestawy znakow
z1=r'qwertyuiopasdfghjklzxcvbnm'
z2=r'QWERTYUIOPASDFGHJKLZXCVBNM'
z3=r'1234567890'
z4=r'!@#$%^&*_+=-~;:.>,<?'
z5=r'''`(){}[]'"\|/'''

# ustalamy zestaw z ktorego losujemy
chars = r''
for o, a in opts:
  if o in ('-h', '--help'):
    exit(0, USAGE)
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
  length = int(length)
  quant = int(quant)
except:
  exit(2, USAGE)

all_chars = len(chars)
if all_chars == 0:
  chars = z1[:]
  all_chars = len(chars)



random.seed()
for j in xrange(quant):
	passwd = ''
	for i in xrange(length): passwd += random.choice(chars)
	print passwd

'''
ChangeLog:
2005-04-16 - random.seed() wyrzucone poza petle + kosmetyka
2005-03-23 - drobne poprawki
'''
