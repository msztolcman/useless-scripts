#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
# $Id$

from __future__ import print_function

__version__   = 'version 0.3'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2008-2009'
__program__   = 'rstool - tool for rapidshare.com (download, get stats, check for files existence)'
__date__      = '2009-01-25'
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
import time
import types
import urllib, urllib2

class RS_Actions (object):
    download_cmd    = "curl -u '%s:%s' -G --location-trusted -w 'Done: %%{url_effective}\n\n' -C - "
    download_max    = 10
    stat_url        = 'https://ssl.rapidshare.com/cgi-bin/premiumzone.cgi'
    check_url       = 'http://rapidshare.com/cgi-bin/checkfiles.cgi'
    check_max       = 100
    check_rxp        = re.compile (r'''
        <table[^>]*>                        # table rozpoczynajacy
        <tr[^>]*>                           # zaraz pozniej tr rozpoczynajacy
        <td[^>]*>                           # zaraz pozniej td rozpoczynajacy
        (.*?)                               # zawartosc komorki
        <td[^>]*>                           # td konczace
        .*?                                 # dalszy ciag smieci
        </table>                            # koniec tabelki
        \s*                                 # ew biale znaki
        <div\s+class="downloadlink"[^>]*>   # div rozpoczynajacy
        (.*?)                               # zawartosc div
        </div>                              # div konczacy
        ''',

        re.I|re.S|re.X
    )

    stat_types      = dict (
        t = (
            'Traffic left',
            re.compile (r'<td>traffic\s+left:</td><td.*?(\d+/\d+).*?</td>\s*<td><b>\(.*?(\+\d+\s*GB).*?\)', re.I|re.S),
            lambda x: '%d MB (%s)' % (eval (x[0]), x[1])
        ),
        x = (
            'Expiration date',
            re.compile (r'<td>expiration\s+date:</td><td.*?<b>([^<]+)</b>.*?</td>', re.I|re.S),
        ),
        p = (
            'Rapid points',
            re.compile (r'<td>rapidpoints:</td><td.*?<b>(\d+)</b></td>', re.I|re.S),
        ),
        s = (
            'Used storage',
            re.compile (r'<td>used\s+storage:</td><td.*?\("(\d+)"\)', re.I|re.S),
        ),
        u = (
            'RapidPoints PU',
            re.compile (r'RapidPoints\s+PU</a>:</td><td.*?<b>(\d+)</b></td>', re.I|re.S),
        ),
        r = (
            'Traffic share',
            re.compile (r'trafficshare\s+left:</td><td.*?<b>(\d+(?:\.\d+)?\s+[a-z]+)</b></td>', re.I|re.S),
        ),
        f = (
            'Files',
            re.compile (r'Files:</td><td.*?<b>(\d+)</b></td>', re.I|re.S),
        ),
    )


    def __download (self, urls, destdir):
        if not isinstance (urls, (types.ListType, types.TupleType)):
            urls = ( urls, )

        if destdir == '.':
            destdir = os.getcwd ()

        ## wywołanie curla: curl [...] -o output1 -o output2 file1 file2
        cmd = self.download_cmd % (Config.login, Config.password, )
        for url in urls:
            url = url.strip ()
            cmd += ' -o "%s" "%s"' % (os.path.join (destdir, os.path.basename (url)), url)

        return os.system (cmd)

    def action__download (self, files, ):
        for fname in files:
            ## url, nie plik
            if not os.path.isfile (fname):
                self.__download (fname, Config.root)

            else:
                ## obsluga downloadu do katalogow w ktorych sa pliki z lista urli
                if Config.root_change:
                    Config.root = os.path.dirname (fname)

                all_urls = []
                ## lecimy po pliku i zbieramy wszystkie urle
                with open (fname, 'r') as fh:
                    for url in fh:
                        url = url.strip ()
                        if not url or url[0] == '#':
                            continue
                        all_urls.append (url)

                ## a teraz pobieramy w paczkach po self.download_max
                while all_urls:
                    end = min (len (all_urls), self.download_max)
                    urls = all_urls[:end]
                    all_urls = all_urls[end:]

                    print (time.strftime ('%Y-%m-%d %H:%M:%S', time.localtime (time.time ())))
                    self.__download (urls, Config.root)

    def action__stat (self, args, ):
        ## pola jakich oczekuje formularz logowania
        data        = dict ( uselandingpage = 1, login = Config.login, password = Config.password )
        data        = urllib.urlencode (data)

        ## pobieramy zawartosc strony
        request     = urllib2.Request (self.stat_url, data)
        response    = urllib2.urlopen (request)
        html        = response.read ()

        max_len = 0
        stats   = []

        ## filtrujemy podane pola oraz ustalamy najdluzszy opis (dla ladnego wygladu ;) )
        ## zachowujemy przy tym oryginalna kolejnosc pol
        for arg in Config.stat_options:
            if arg in stats or arg not in self.stat_types:
                continue

            stats.append (arg)
            if len (self.stat_types[arg][0]) > max_len:
                max_len = len (self.stat_types[arg][0])
        max_len += 1

        ## szukamy printujemy wybranych statystyk
        for arg in stats:
            ## naglowek
            print (self.stat_types[arg][0].ljust (max_len), ': ', sep='', end='')

            ## jesli jesy funcja formatujaca to jej uzywamy
            if len (self.stat_types[arg]) > 2:
                print ( self.stat_types[arg][2] (self.stat_types[arg][1].findall (html)[0]) )

            ## jak nie to gola zawartosc pola
            else:
                print ( self.stat_types[arg][1].findall (html)[0] )

    def action__check (self, files, ):
        for fname in files:
            if not os.path.isfile (fname):
                print ('File "%s" not found.' % fname, file = sys.stderr)
                print ()
                continue

            print ('File: "%s":' % fname)

            with open (fname, 'r') as fh:
                all_urls = []
                for line in fh:
                    line = line.strip ()
                    if not line or line[0] == '#':
                        continue
                    all_urls.append (line)

                i, data = 1, ''

                ## odpytujemy po self.check_max urli - ten formularz ma ograniczenia co do ilosci urli naraz
                while all_urls:
                    end         = min (len (all_urls), self.check_max)
                    urls        = all_urls[0:end]
                    all_urls    = all_urls[end:]

                    data = urllib.urlencode ({ 'urls': "\n".join (urls) })
                    if data:
                        request     = urllib2.Request (self.check_url, data)
                        response    = urllib2.urlopen (request)
                        html        = response.read ()

                        ## ucinamy spora czesc niepotrzebnego tekstu
                        html        = html[html.find ('id="inhaltbox"'):]

                        ## szukamy ...
                        rsfiles     = self.check_rxp.findall (html)

                        ## ... i wyswietlamy
                        for rsfile in rsfiles:
                            print ("% 5d. %s: %s" % (i, rsfile[1], 'missing' if 'does not exist' in rsfile[0] else 'OK' ))
                            i += 1
                print ()

rs_actions = RS_Actions ()

class Config (object):
    login           = None
    password        = None
    root_change     = False
    root            = '.'
    action          = rs_actions.action__download
    stat_options    = ('x', 't', )



def main ():
    import getopt

    usage = '''%s [-a|--action download|stat|check] [-l|--login login] [-p|--password password] [-s|--stat_options options] [-c|--root-change] [-r|--root] [-h|--help] [-v|--version]
Actions:
    download - download given files (default)
    stat - read some statistics
    check - check for existance of files

Options:
    -l|--login LOGIN - login to your premium account
    -p|--password PASSWORD - password
    -s|--stat-options OPTIONS - string (defaults to 'xt') composed from letters:
        t - traffic left
        x - expiration date
        p - rapid points
        s - used storage
        u - rapidpoints pu
        r - traffic share
        f - files
    -c|--root-change - if given, destination directory will be parent directory for input file
    -r|--root ROOT - if given, all files will be saved in ROOT directory
    -v|--version - version info
    -h|--help - this help ''' % os.path.basename (sys.argv[0])

    ## parsowanie opcji i ustawien
    opts_short  = 'a:l:p:cr:hvs:'
    opts_long   = ('action=', 'login=', 'password=', 'root_change', 'root=', 'help', 'version', 'stat-options=', )
    try:
        opts, args = getopt.gnu_getopt (sys.argv[1:], opts_short, opts_long)

        for o, a in opts:
            if o in ('-a', '--action'):
                if not hasattr (RS_Actions, 'action__'+ a):
                    raise getopt.GetoptError ('Incorrect value for action: ' + a + '.')

                Config.action = getattr (rs_actions, 'action__'+ a)

            elif o in ('-l', '--login'):
                Config.login = a

            elif o in ('-p', '--password'):
                Config.password = a

            elif o in ('-c', '--root-change'):
                Config.root_change = True

            elif o in ('-r', '--root'):
                if not os.path.isdir (a):
                    raise getopt.GetoptError ('Root directory not found.')

                Config.root = a

            elif o in ('-s', '--stat-options'):
                Config.stat_options = list (a)

            elif o in ('-h', '--help'):
                print (usage)
                raise SystemExit (0)

            elif o in ('-v', '--version'):
                print (__desc__)
                raise SystemExit (0)

    except getopt.GetoptError as e:
        print (e, file=sys.stderr)
        raise SystemExit (1)

    ## jesli nie ma loginu lub hasla, pobieramy je sobie z pliku
    if Config.login is None or Config.password is None:
        try:
            with open (os.path.expanduser ('~/.rs_login'), 'r') as fh:
                Config.login    = fh.readline ().strip ()
                Config.password = fh.readline ().strip ()
        except IOError as e:
            print ('Put your login and password to rapidshare account in ~/.rs_login or help me with -l and -p options.', file=sys.stderr)
            raise SystemExit (2)


    ## wykonujemy wybraną akcję
    Config.action (args)

if __name__ == '__main__':
    main ()

# vim: ft=python
