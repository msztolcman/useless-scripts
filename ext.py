#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id$

__version__   = 'version 0.1'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2008 - 2009'
__program__   = 'ext.py - simple wrapper for unarchivizers'
__date__      = '2008-12-17'
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
import re
import subprocess
import sys

usage = '''%s [-p|--password password] [-o|--options options] [-t|--type type] [-c|--change-root] [-v|--version] [-h|--help]''' % os.path.basename (sys.argv[0])

class Settings (dict):
    pass

def system (*a):
#     p = subprocess.Popen (a, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen (a, stdout=sys.stdout, stderr=subprocess.PIPE)
    o, e = p.communicate ()
    return (p.returncode, o, e)

def special_rar (arch_args, path, params):
    if params['password']:
        return arch_args
    return arch_args + '-p-'

def main ():
    import getopt
    opts_sh     = 'vhp:o:t:c'
    opts_long   = ('verion', 'help', 'password=', 'options=', 'type=','change-root' )

    try:
        opts, args = getopt.getopt (sys.argv[1:], opts_sh, opts_long)
    except getopt.GetoptError, e:
        print >>sys.stderr, e
        raise SystemExit (1)

    S = Settings (
        password    = None,
        options     = None,
        type        = '',
        change_root = False,
    )

    for o, a in opts:
        if o in ('-v', '--version'):
            print __desc__
            raise SystemExit
        elif o in ('-h', '--help'):
            print usage
            raise SystemExit
        elif o in ('-p', '--password'):
            S['password'] = a
        elif o in ('-o', '--options'):
            S['options'] = a
        elif o in ('-t', '--type'):
            S['type'] = a
        elif o in ('-c', '--change-root'):
            S['change_root'] = True

    if not args:
        print >>sys.stderr, 'Give me some files to extract!'
        raise SystemExit (2)


    archive_types = dict (
        rar     = ('unrar x -y %(arch_args)s %(fname)s', '-p', special_rar),
        Z       = ('uncompress %(arch_args)s %(fname)s', None, None),
        zip     = ('unzip -n %(arch_args)s %(fname)s', '-P ', None),
        tar     = ('tar -x -f %(arch_args)s %(fname)s', None, None),
        gz      = ('gunzip %(arch_args)s %(fname)s', None, None),
        bz2     = ('bunzip2 %(arch_args)s %(fname)s', None, None),
        tbz     = ('tar -x -j %(arch_args)s -f %(fname)s', None, None),
        tgz     = ('tar -x -z %(arch_args)s -f %(fname)s', None, None),
        sevenz  = ('7za x %(arch_args)s %(fname)s', '-p', None),
    )

    cur = os.getcwd ()
    for obj in args:
        os.chdir (cur)
        if not os.path.isfile (obj) or os.path.islink (obj):
            print >>sys.stderr, 'Unrecognized file type: %s' % obj
            continue

        arch_type = ''
        if S['type']:
            arch_type = S['type']

        if arch_type not in archive_types:
            if arch_type in ('tar.bz2', 'tbz2') or obj.lower ().endswith ('.tar.bz2') or obj.lower ().endswith ('.tbz2'):
                arch_type = 'tbz'
            elif arch_type in ('tar.gz',) or obj.lower ().endswith ('.tar.gz'):
                arch_type = 'tgz'
            elif arch_type in ('7zip', '7z') or obj.lower ().endswith ('.7zip') or obj.lower ().endswith ('.7z'):
                arch_type = 'sevenz'
            else:
                arch_type = os.path.splitext (obj)[1].lstrip ('.')

        if arch_type:
            arch_type = arch_type.lower ()
        if arch_type not in archive_types:
            print >>sys.stderr, 'Unrecognized file type: %s' % (arch_type if arch_type else obj)
            continue

        arch_args = ''
        if S['password'] is not None and archive_types[arch_type][1] is not None:
            arch_args += archive_types[arch_type][1] + S['password']

        if archive_types[arch_type][2]:
            arch_args = archive_types[arch_type][2] (arch_args, obj, S, )

        cmd = archive_types[arch_type][0]
        if S['change_root']:
            root, fname = os.path.split (obj)
            os.chdir (root)
        else:
            fname = obj

        cmd %= {
            'fname':        fname,
            'arch_args':    arch_args,
        }
#         print arch_args
#         print cmd
#         raise SystemExit

        print obj + ':'
        cmd = system (*cmd.split ())
        if cmd[0]:
            print 'ERROR:'
        if cmd[2]:
            print cmd[2].strip ()
#         if cmd[1]:
#             print 'Result:'
#             print cmd[1]
        if not cmd[0]:
            print 'OK :', obj
        else:
            print 'FAIL [%d]: %s' % (cmd[0], obj)
        print

if __name__ == '__main__':
    main ()

# vim: ft=python
