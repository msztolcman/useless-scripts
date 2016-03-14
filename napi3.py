#!/usr/bin/env python3

__version__ = 'version 0.8'
__author__ = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net> (based od napi.py from http://hacking.apcoh.com/2008/01/napi_06.html - 0.15b)'
__copyright__ = '(r) 2008 - 2014'
__program__ = 'napi.py - find and download polish subtitles for films (from http://www.napiprojekt.pl/)'
__date__ = '2012-12-22'
__license__ = 'GPL v.2'

__desc__ = '''%(desc)s
%(author)s %(copyright)s
license: %(license)s
%(version)s (%(date)s)''' % {
    'desc': __program__,
    'author': __author__,
    'copyright': __copyright__,
    'license': __license__,
    'version': __version__,
    'date': __date__
}

import codecs
import hashlib
import os, os.path
import re
import subprocess
import sys
import tempfile
import urllib.request


def napiprojekt_calculate_md5(path):
    with open(path, 'rb') as fh:
        return hashlib.md5(fh.read(10485760)).hexdigest()


def napiprojekt_calculate_f(md5digest):
    idx = ( 0xe, 0x3,  0x6, 0x8, 0x2 )
    mul = (   2,   2,    5,   4,   3 )
    add = (   0, 0xd, 0x10, 0xb, 0x5 )

    b = []
    for a, m, i in zip(add, mul, idx):
        t = a + int(md5digest[i], 16)
        v = int(md5digest[t:t+2], 16)
        b.append(('%x' % (v*m))[-1])

    return ''.join(b)


def napiprojekt_extract_subtitles(data):
    # create temporary archive for 7zip
    with tempfile.NamedTemporaryFile(mode='wb', prefix='napi_') as fh:
        fh.write(data)
        fh_arch_path = fh.name

        # extract archive and write it to second temporary file
        cmd = ('7za', 'x', '-y', '-so', '-bd', '-piBlm8NTigvru0Jr0', fh_arch_path, )

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            return False

    # return content of subtitles
    return stdout


def napiprojekt_get_subtitles(film, dst_encoding, output=None):
    if not os.path.isfile(film):
        return False

    md5 = napiprojekt_calculate_md5(film)

    url = 'http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s'
    url %= (md5, napiprojekt_calculate_f(md5), os.name)

    # download and extract subtitles if found
    subtitles = urllib.request.urlopen(url).read()
    if subtitles == b'NPc0':
        return False

    subtitles = napiprojekt_extract_subtitles(subtitles)
    if not subtitles:
        return False

    src_encoding = None
    if dst_encoding:
        if subtitles.startswith((codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE)):
            subtitles = subtitles[len(codecs.BOM_UTF16_BE):]
            src_encoding = 'utf-16'
        elif subtitles.startswith(codecs.BOM_UTF8):
            subtitles = subtitles[len(codecs.BOM_UTF8):]
            src_encoding = 'utf-8'
        elif subtitles.startswith((codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE)):
            src_encoding = 'utf-32'

        try:
            subtitles = subtitles.decode(src_encoding)
        except UnicodeDecodeError:
            subtitles = subtitles.decode()

    # find output directory and correct subtitles filename
    dname, fname = os.path.split(film)
    if output and os.path.isdir(output):
        dname = output
    elif not dname:
        dname = os.getcwd()

    # write subtitles file in right directory
    fname = os.path.splitext(fname)[0] + '.txt'

    if dst_encoding:
        with open(os.path.join(dname, fname), 'w', encoding=dst_encoding) as fh:
            fh.write(subtitles)
    else:
        with open(os.path.join(dname, fname), 'wb') as fh:
            fh.write(subtitles)

    return True


def has_subtitle(film):
    p = os.path.splitext(film)
    return os.path.isfile(p[0] + '.txt')


def is_film(path):
    return not os.path.basename(path).startswith('.') and \
            os.path.isfile(path) and \
            re.search('\.(?:avi|mpe?g|mp4|mkv|rmvb|m4v|wmv|asf|ogm)$', path.lower())


def find_films__recursive(path):
    ret = []
    for root, dirs, files in os.walk(path):
        for f in files:
            p = os.path.join(root, f)
            if is_film(p):
                ret.append(p)
    return ret


def find_films__nonrecursive(path):
    ret = []
    for fname in os.listdir(path):
        p = os.path.join(path, fname)
        if is_film(p):
            ret.append(p)
    return ret


def find_films(path, recursive=False):
    if not os.path.isdir(path):
        return

    if recursive:
        return find_films__recursive(path)
    else:
        return find_films__nonrecursive(path)


def main():
    import getopt

    usage = __desc__ + "\n\n" + '''%s [-h|--help] [-v|--version] [-d|--directory] [-r|--recursive] [-o|--output output_dir] [-n|--no-validate] [-w|--overwrite] input1 input2 .. inputN
-h|--help           - this help message
-d|--directory      - if specified, scan every passed argument (input1 .. inputN) for files with extensions: avi, mpeg, mpg, mp4, mkv, rmvb
-r|--recursive      - if specified, every directory passed as input will be scanned recursively. Skipped when -d is not specified
-o|--output_dir     - specify directory when you want to save downloaded files. If not specified, try to save every subtitle in films directory
-n|--no-validate    - if given, specified list of films will not be validated for being movie files (work only without -d parameter)
-w|--overwrite      - if specified, existent subtitles will not be overwritten
-e|--encoding       - convert subtitles to given encoding (default: cp1250)
--do-not-convert    - do not convert subtitles
--verbose           - show info about every film, even if subtitles are not found
input1 .. inputN    - if -d is not specified, this is treaten like films files, to which you want to download subtitles. In other case, this is list of directories whis are scanned for files''' % (os.path.basename(sys.argv[0]),)

    # parsing getopt options
    opts_short = 'hdo:rnwe:'
    opts_long = ['help', 'directory', 'output=', 'recursive', 'no-validate', 'overwrite', 'verbose', 'encoding', 'do-not-convert']
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], opts_short, opts_long)
    except getopt.GetoptError as exc:
        print(exc)
        sys.exit(1)

    recursive = False
    directory = False
    output = None
    validate = True
    overwrite = False
    verbose = False
    encoding = 'cp1250'
    for o, a in opts:
        if o in ('-h', '--help'):
            print(usage)
            sys.exit(0)
        elif o in ('-v', '--version'):
            print(__version__)
            sys.exit(0)
        elif o in ('-d', '--directory'):
            directory = True
        elif o in ('-r', '--recursive'):
            recursive = True
        elif o in ('-o', '--output'):
            output = a
        elif o in ('-n', '--no-validate'):
            validate = False
        elif o in ('-w', '--overwrite'):
            overwrite = True
        elif o in ('-e', '--encoding'):
            encoding = a.lower()
        elif o == '--do-not-convert':
            encoding = False
        elif o == '--verbose':
            verbose = True

    # find all films
    fnames = []
    if directory:
        dirs = []
        if not args:
            dirs.append(os.getcwd())
        else:
            dirs.extend(args)
        for dname in dirs:
            fname = find_films(dname, recursive)
            if fname:
                fnames.extend(fname)

    # all files from current dir
    elif not args:
        fnames.extend(find_films(os.getcwd()))

    # check files given by user
    elif validate:
        fnames.extend(fname for fname in args if is_film(fname))

    # don't check, every given file is a file (skip only nonfile)
    else:
        fnames.extend(fname for fname in args if os.path.isfile(fname))

    # skip searching for existent subtitles
    if not overwrite:
        fnames = [fname for fname in fnames if not has_subtitle(fname)]

    if not fnames:
        print('Cannot find any film.')
        sys.exit(2)

    # find longest filename
    length = max(map(len, fnames)) + 1

    # download all subtitles
    found = 0
    for fname in fnames:
        r = napiprojekt_get_subtitles(fname, encoding, output)
        if r:
            found += 1
            status = 'done'
        elif not verbose:
            continue
        else:
            status = 'not found'
        fname += ' '
        print('%s: %s' % (fname.ljust(length, '-'), status))

    if fnames:
        print()
    print('Searched for subtitles to %d films, found %d' % (len(fnames), found, ))


if __name__ == '__main__':
    main()

# vim: ft=python
