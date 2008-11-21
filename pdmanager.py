#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-

from __future__ import with_statement

__version__   = 'version 0.3'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2007-2008'
__program__   = 'pdmanager.py - tool for managing password database stored in plain text files'
__date__      = '2008-11-21'
__license__   = 'GPL v.2'

__desc__      = '''%(desc)s
%(author)s (r) 2007-2008
license: %(license)s
version %(version)s (%(date)s)''' % {
  'desc': __program__,
  'author': __author__,
  'license': __license__,
  'version': __version__,
  'date': __date__
}

import glob
import hashlib
import os, os.path
import re
import shutil
import sys

class PwdActions (object):
    VIMLINE     = "\n# vim: ft=txt"
    try:
        EDITOR = os.environ['EDITOR']
    except KeyError:
        try:
            EDITOR = os.environ['VISUAL']
        except KeyError:
            EDITOR = 'vim'

    def md5 (self, fname):
        """Calculate file md5 sum"""
        m = hashlib.md5 ()
        with open (fname) as fh:
            # it's small files
            m.update (fh.read ())
        return m.hexdigest ()

    def action__add (self, params):
        """Create new entry"""
        path = os.path.join (params['root'], params['name'])
        if os.path.exists (path) or os.path.isfile (path):
            raise Exception ('Entry already exists!')

        with open (path, 'w') as fh:
            fh.write ("user: %s\n" % params['login'])
            fh.write ("pass: %s\n" % params['passwd'])
            if 'desc' in params:
                fh.write (params['desc'].replace (r'\n', "\n"))
            fh.write ("\n")
            fh.write (self.VIMLINE)
        return path

    def action__read (self, params):
        """Read entry"""
        names = params['name']
        if isinstance (names, str):
            names = [ names, ]

        ret = dict ()
        for name in names:
            path = os.path.join (params['root'], name)
            if not os.path.exists (path) or not os.path.isfile (path):
                continue
            with open (path, 'r') as fh:
                data = fh.readlines ()
                data = dict (
                    login   = data[0][5:].strip (),
                    passwd  = data[1][5:].strip (),
                    desc    = ''.join (data[2:-1]).strip (),
                )
                ret[name] = data
        return ret

    def action__update (self, params):
        """Update entry data"""
        if not os.path.isfile (params['path']):
            raise Exception (u'Entry not found.')

        login   = params.get ('login', None)
        passwd  = params.get ('passwd', None)
        desc    = params.get ('desc', None)
        name    = params.get ('name', None)
        path    = params['path']
        if login is not None or passwd is not None or desc is not None:
            with open (path, 'r+') as fh:
                fh.seek (0)
                o_login     = fh.readline ().strip ()
                o_passwd    = fh.readline ().strip ()
                o_desc      = ''.join (fh.readlines ()[:-1]).strip ()

                if login is not None:
                    o_login = 'user: ' + login

                if passwd is not None:
                    o_passwd = 'pass: ' + passwd

                if desc is not None:
                    o_desc = desc.replace (r'\n', "\n")

                fh.seek (0)
                fh.truncate ()
                fh.write ("\n".join ((o_login, o_passwd, o_desc, self.VIMLINE)))

        if name is not None:
            new_path = os.path.join (os.path.dirname (path), name)
            shutil.move (path, new_path)
            path = new_path

        return path

    def action__delete (self, params):
        """Delete entry"""
        if not isinstance (params['name'], str):
            params['name'] = params['name'][0]
        path = os.path.join (params['root'], params['name'])
        if not os.path.isfile (path):
            raise Exception (u'Entry not found.')

        os.remove (path)
        return True

    def action__search (self, params):
        """Search for entry by name"""
        names = params['name']
        if isinstance (names, str):
            names = [ names, ]

        ret     = dict ()
        paths   = []
        for name in names:
            path = os.path.join (params['root'], name)
            paths.extend ( glob.glob (path))

        return self.action__read (dict (name = paths, root = params['root']))

    def action__edit (self, params):
        """Edit entry in external editor"""
        cmd = '%s %s' % (self.EDITOR, params['path'],)
        md5_before = self.md5 (params['path'])
        os.system (cmd)
        md5_after = self.md5 (params['path'])

        if md5_before == md5_after:
        	print 'Entry "%s" does not change.' % params['path']
        else:
        	print 'Entry "%s" saved.' % params['path']


def main ():
    import getopt

    # TODO
    usage = __desc__ + """\n\n%s [action] [data] [options]
    action:
        add|read|update|delete|search|edit - defaults to read
    options:
        -n|--name name          - entry name    (required)
        -l|--login login        - login         (required)
        -p|--password password  - password      (required)
        -d|--desc some desc     - some additional info (WARNING: \\n string is replaced with new line character!)
        -r|--root path          - directory where store entries files (defaults to ~/.passwd)
        -w|--show-password      - display plain text password (without this password is starred)
        -d|--debug              -
        -v|--version            - version info
        -h|--help               - this help
    data:
        For action 'read' or 'search' it can be name/pattern for some entry (instead of -n option).
        For action 'update' it must be name of entry to update (value for -n option means _new name_ of entry)""" % (sys.argv[0], )

    # calling getopt
    opts_short  = 'hvn:d:l:p:r:w'
    opts_long   = ('help', 'version', 'name=', 'desc=', 'login=', 'password=',
                    'root=', '--show-password',
                    'debug')
    try:
        opts, args = getopt.gnu_getopt (sys.argv[1:], opts_short, opts_long)
    except getopt.GetoptError, e:
        print >>sys.stderr, e
        raise SystemExit (1)

    # parsing data from getopt
    params  = dict (
        action      = 'read',
        show_passwd = False,
    )
    for o, a in opts:
        if o in ('-h', '--help'):
            print usage
            raise SystemExit (0)
        elif o in ('-v', '--version'):
            print '%s (%s)' % (__version__, __date__)
            raise SystemExit (0)
        elif o in ('-n', '--name'):
            params['name']      = a
        elif o in ('-d', '--desc'):
            params['desc']      = a
        elif o in ('-l', '--login'):
            params['login']     = a
        elif o in ('-p', '--password'):
            params['passwd']    = a
        elif o in ('-r', '--root'):
            params['root']   = a
        elif o in ('-w', '--show-password'):
            params['show_passwd'] = True
        elif o == '--debug':
            easysqlite.DEBUG = True

    # additional validaton of parameters - getopt can't do it
    # if there is no -r parameter, we try to find root
    if 'root' not in params:
        try:
            params['root'] = os.environ['HOME']
        except KeyError:
            params['root'] = os.path.expanduser ('~')
        if not params['root']:
            params['root'] = os.getcwd ()
        params['root'] = os.path.join (params['root'], '.passwd')

    # change action if valid
    if args and args[0] in ('add', 'read', 'update', 'delete', 'search', 'edit'):
        params['action'] = args.pop (0)
    if params['action'] in ('update', 'edit'):
        params['path'] = os.path.join (params['root'], args.pop (0))

    if 'name' not in params and args:
        params['name'] = args

    try:
        result = getattr (PwdActions (), 'action__' + params['action']) (params)
    except Exception, e:
        print 'Some error ocured:', e
    else:
        if params['action'] in ('read', 'search'):
            if result:
                for name, data in result.items ():
                    print os.path.join (params['root'], os.path.dirname (name)), '::', os.path.basename (name)
                    print 'Login:', data['login']
                    print 'Password:', data['passwd'] if params['show_passwd'] else '***'
                    print
                    if data['desc']:
                        print data['desc']
                        print
                    print
            else:
                print 'Nothing found'

        elif params['action'] == 'add':
            print 'Entry created "%s".' % result

        elif params['action'] == 'update':
            print 'Entry "%s" updated.' % os.path.basename (params['path'])
            if params['path'] != result:
                print 'Entry renamed to: "%s".' % result

        elif params['action'] == 'delete':
            if result:
                print 'Entry "%s" deleted.' % os.path.basename (params['name'])


if __name__ == '__main__':
	main ()

