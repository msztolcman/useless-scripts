#!/usr/bin/env python3

import os, os.path
import sys
import subprocess
import getopt

class Stat (object):
    def __size2human (size):
        size = int (size)
        if size < 1024:
            return '%d kB' % size
        elif size < 1024 ** 2:
            return '%d MB' % (size/1024)
        elif size < 1024 ** 3:
            return '%d GB' % (size/1024**2)
        else:
            return '%d TB' % (size/1024**3)

    size2other = dict (
        size2b      = lambda size: '%d B' % (int (size) * 1024),
        size2kb     = lambda size: '%d kB' % (int (size)),
        size2mb     = lambda size: '%d MB' % (int (size) / 1024),
        size2gb     = lambda size: '%d GB' % (int (size) / 1024 / 1024),
        size2tb     = lambda size: '%d TB' % (int (size) / 1024 / 1024 / 1024),
        size2human  = __size2human,
    )

    _sort_reverse   = True
    _line_tpl       = '%12s %6s - %s'

    def __init__ (self, setts):
        for k, v in setts.items ():
            setattr (self, '_' + k, v)
        self.read_processes ()

    def read_processes (self):
        pax = subprocess.getoutput ('ps awux').split ("\n")[1:]

        if len (pax) < self._quant:
            self._quant = len (pax)

        pax = [ line.split (None, 10) for line in pax ]
        pax.sort (key = self._sort_key, reverse = self._sort_reverse)
        self._pax = pax

    def legend (self):
        return self._line_tpl % (self.col_name, 'PID', 'Command')

    @staticmethod
    def line (value, pid, command):
        return Stat._line_tpl % (value, pid, command)


class StatMem (Stat):
    col_name = 'Memory'
    def _sort_key (self, line):
        return int (line[5])

    def __call__ (self):
        unitize = Stat.size2other[self._conv]
        for line in self._pax[:self._quant]:
            yield Stat.line (unitize (line[5]), int (line[1]), line[-1])

class StatCpu (Stat):
    col_name = 'CPU'
    def _sort_key (self, line):
        return float (line[2].replace (',', '.'))

    def __call__ (self):
        for line in self._pax[:self._quant]:
            yield Stat.line ('%0.2f %%' % float (line[2].replace (',', '.')), int (line[1]), line[-1])

def main ():
    try:
        opts_sh     = 'ukmbgvhq:lt:'
        opts_long   = ('human', 'kilo', 'mega', 'giga', 'byte', 'version', 'help', 'quant=', 'legend', 'type=', )
        opts, args = getopt.gnu_getopt (sys.argv[1:], opts_sh, opts_long)
    except getopt.GetoptError as e:
        print (e, file=sys.stderr)
        raise SystemExit (1)

    stats = dict (
        mem     = StatMem,
        cpu     = StatCpu,
    )

    setts = dict (
        conv    = 'size2kb',
        quant   = 10,
        legend  = False,
        type    = 'mem',
    )

    for o, a in opts:
        if o in ('-b', '--byte'):
            setts['conv'] = 'size2b'
        elif o in ('-k', '--kilo'):
            setts['conv'] = 'size2kb'
        elif o in ('-g', '--giga'):
            setts['conv'] = 'size2gb'
        elif o in ('-m', '--mega'):
            setts['conv'] = 'size2mb'
        elif o in ('-u', '--human'):
            setts['conv'] = 'size2human'
        elif o in ('-q', '--quant'):
            setts['quant'] = int (a)
        elif o in ('-l', '--legend'):
            setts['legend'] = True
        elif o in ('-t', '--type'):
            if a not in stats:
                raise Exception ('Incorrect type.')
            setts['type'] = a
        elif o in ('-v', '--version'):
            print ('version')
            raise SystemExit
        elif o in ('-h', '--help'):
            print ('help')
            raise SystemExit

    pax = stats[setts['type']] (setts)

    if setts['legend']:
        print (pax.legend ())
    for line in pax ():
        print (line)

if __name__ == '__main__':
    main ()

