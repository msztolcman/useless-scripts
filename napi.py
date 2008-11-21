#!/usr/bin/python -W ignore
# -*- coding: utf-8 -*-

from __future__ import with_statement

__version__   = 'version 0.5'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net> (based od napi.py from http://hacking.apcoh.com/2008/01/napi_06.html - 0.15b)'
__copyright__ = '(r) 2008'
__program__   = 'napi.py - find and download polish subtitles for films (from http://www.napiprojekt.pl/)'
__date__      = '2008-11-21'
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
import re
import subprocess
import sys
import urllib

def calculate_md5 (path):
    with open (path, 'r') as fh:
        return hashlib.md5 (fh.read (10485760)).hexdigest ()

def calculate_f (md5digest):
    idx = ( 0xe, 0x3,  0x6, 0x8, 0x2 )
    mul = (   2,   2,    5,   4,   3 )
    add = (   0, 0xd, 0x10, 0xb, 0x5 )

    b = []
    for a, m, i in zip (add, mul, idx):
        t = a + int (md5digest[i], 16)
        v = int (md5digest[t:t+2], 16)
        b.append ( ('%x' % (v*m))[-1] )

    return ''.join (b)

def extract_subtitles (data):
    # create temporary archive for 7zip
    fh_arch_path = os.tempnam (None, 'sub_')
    with open (fh_arch_path, 'w') as fh:
        fh.write (data)

    # extract archive and write it to second temporary file
    fh_sub = os.tmpfile ()
    cmd = ['7z', 'x', '-y', '-so', '-bd', '-piBlm8NTigvru0Jr0', fh_arch_path]
    p = subprocess.Popen (cmd, stdout=fh_sub, stderr=subprocess.PIPE)
    r = p.communicate ()

    # remove temporary archive
    try:
        os.remove (fh_arch_path)
    except:
        pass

    if p.returncode != 0:
#         print >>sys.stderr, "\n".join (r[1].strip().split ("\n")[5:])
        return False

    # return content of subtitles
    fh_sub.seek (0)
    return fh_sub.read ()

def get_subtitles (film, output=None):
    if not os.path.isfile (film):
        return False

    md5 = calculate_md5 (film)

    url = 'http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s'
    url %= (md5, calculate_f (md5), os.name)

    # download and extract subtitles if found
    data = urllib.urlopen (url).read ()
    data = extract_subtitles (data)
    if not data:
        return False

    # find output directory and correct subtitles filename
    dname, fname = os.path.split (film)
    if output and os.path.isdir (output):
        dname   = output
    elif not dname:
        dname   = os.getcwd ()

    # write subtitles file in right directory
    fname = os.path.splitext (fname)[0] + '.txt'
    with open (os.path.join (dname, fname), 'w') as fh:
        fh.write (data)

    return True


def is_film (path):
    if os.path.isfile (path) and re.search ('\.(?:avi|mpe?g|mp4|mkv|rmvb)$', path, re.I):
        return True
    return False

def find_films__recursive (path):
    ret = []
    for root, dirs, files in os.walk (path):
        for f in files:
            p = os.path.join (root, f)
            if is_film (p):
                ret.append (p)
    return ret

def find_films__nonrecursive (path):
    ret = []
    for fname in os.listdir (path):
        p = os.path.join (path, fname)
        if is_film (p):
            ret.append (p)
    return ret

def find_films (path, recursive=False):
    if not os.path.isdir (path):
        return

    if recursive:
        return find_films__recursive (path)
    else:
        return find_films__nonrecursive (path)


def main ():
    usage = '''%s [-h|--help] [-v|--version] [-d|--directory] [-r|--recursive] [-o|--output output_dir] input1 input2 .. inputN
-h|--help           - this help message
-d|--directory      - if specified, scan every passed argument (input1 .. inputN) for files with extensions: avi, mpeg, mpg, mp4, mkv, rmvb
-r|--recursive      - if specified, every directory passed as input will be scanned recursively. Skipped when -d is not specified
-o|--output_dir     - specify directory when you want to save downloaded files. If not specified, try to save every subtitle in films directory
input1 .. inputN    - if -d is not specified, this is treaten like films files, to which you want to download subtitles. In other case, this is list of directories whis are scanned for files'''

    opts_short  = 'hdo:r'
    opts_long   = ['help', 'directory', 'output=', 'recursive']
    try:
        opts, args = getopt.gnu_getopt (sys.argv[1:], opts_short, opts_long)
    except getopt.GetoptError, e:
        print e
        raise SystemExit (1)

    recursive   = False
    directory   = False
    output      = None
    for o, a in opts:
        if o in ('-h', '--help'):
            print __desc__ + "\n\n" + usage
            raise SystemExit (0)
        elif o in ('-v', '--version'):
            print __version__
            raise SystemExit (0)
        elif o in ('-d', '--directory'):
            directory = True
        elif o in ('-r', '--recursive'):
            recursive = True
        elif o in ('-o', '--output'):
            output = a


    fnames = []
    if not directory:
        if not args:
            print usage
            raise SystemExit (1)
        fnames = filter (lambda a: is_film (a), args)
    else:
        dirs = []
        if not args:
            dirs = (os.getcwd (), )
        else:
            dirs = args

        for d in dirs:
            f = find_films (d, recursive)
            if f:
                fnames += f

    # find longest filename
    length = max (map (len, fnames)) + 1

    for fname in fnames:
        r = get_subtitles (fname, output)
        if r:
            status = u'done'
        else:
            status = u'not found'
        fname += ' '
        print '%s: %s' % (fname.ljust (length, '-'), status)


if __name__ == '__main__':
	main ()

# $Id$
# vim: ft=python
