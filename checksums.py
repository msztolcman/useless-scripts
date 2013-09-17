#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function

__version__   = 'version 0.1'
__author__    = 'Marcin Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2012'
__program__   = 'checksums.py - calculate checksums for files'
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

import os, os.path
import sys
import hashlib
import commands

class CheckSum (object):
    def __init__ (self, path):
        if not path or not os.path.isfile (path):
            raise Exception ('Invalid filename or file not found.')

        self.path = os.path.realpath (path)
        self.size = os.stat (self.path).st_size

    def read_checksum (self, hash):
        hash    = getattr (hashlib, hash) ()
        count   = 0
        with open (self.path) as fh:
            while count < self.size:
                hash.update (fh.read (102400))
                count += 4096
        return hash.hexdigest ()

    def read_rmd160 (self):
        return commands.getoutput ('openssl dgst -ripemd160 -hex ' + self.path).split ()[1]

    def read (self, hashes):
        ret = dict ()

        for hash in hashes:
            if not hasattr (self, 'read_'+hash):
                ret[hash] = self.read_checksum (hash)
            else:
                ret[hash] = getattr (self, 'read_' + hash) ()

        return ret

if __name__ == '__main__':
    if len (sys.argv) <= 1:
        print ('What?!', file=sys.stderr)
        sys.exit (1)

    for path in sys.argv[1:]:
        try:
            ck = CheckSum (path)
        except Exception, e:
            print (e, file=sys.stderr)
            sys.exit (2)

        print ('Filename'.ljust (10) + ':', ck.path)

        types = ['md5', 'sha1', 'rmd160']
        cks = ck.read (types)
        for t in sorted (types):
            print (t.upper ().ljust (10) + ':', cks[t])
        print ()
