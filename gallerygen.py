#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
# $Id$

from __future__ import print_function

__version__   = 'version 0.1'
__author__    = 'Marcin ``MySZ`` Sztolcman <marcin@urzenia.net>'
__copyright__ = '(r) 2008 - 2009'
__program__   = 'gallerygen.py - simple tool for fast creating static image gallery'
__date__      = '2009-01-28'
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



import commands
import math
import os, os.path
import re
import sys
import time

## configuration
class Config (dict):
    def __repr__ (self):
        return "\n".join ( '%s: %s' % (c, getattr (self, c)) for c in sorted (dir (self)) if not c.startswith ('_') and not callable (getattr (self, c)))
    def load (self, path):
        import ConfigParser
        cfg = ConfigParser.RawConfigParser ()
        cfg.read ((path, ))

        ## first templates:
        if cfg.has_section ('templates'):
            for k, v in cfg.items ('templates'):
                setattr (self, k, v)

        ## and the rest:
        if cfg.has_section ('config'):
            for option in cfg.options ('config'):
                if option in ('th_width', 'th_height', 'th_rows', 'th_cols'):
                    setattr (self, option, cfg.getint ('config', option))
                elif option == 'images':
                    setattr (self, option, re.compile (cfg.get ('config', 'images'), re.I))
                else:
                    setattr (self, option, cfg.get ('config', option))

    config              = None
    th_width            = 200
    th_height           = 200
    th_rows             = 3
    th_cols             = 3
    single_width        = 1024
    single_height       = 768
    big_width           = 0
    big_height          = 0
    directory           = None
    images              = re.compile (r'\.(?:jpe?g|gif|png)$', re.I)
    sharpen             = 1
    skip_images         = False
    title               = 'Gallery - %(date)s - %(pageno)s'
    css                 ='''
* { margin: 0; padding: 0; border: 0; }
body { font-size: 62.5%; /*10px*/ background-color: #ccc; font-family: Tahoma, Arial, Helvetica, sans-serif; color: black; }
a { color: red; text-decoration: none; }
a:visited { color: #888; }
a:hover { color: blue; text-decoration: underline; }
br.clear, li.clear { clear: both; }
br.clear { display: inline; height: 0.1px; }
#header { position: relative; }
#header h1, #navi { border-bottom: 4px solid #666; border-left: 4px solid #666; margin-bottom: 0em; height: 3.5em; float: right; }
#header h1 { float: left; border-bottom: 4px solid #666; border-right: 4px solid #666; border-left: none; height: 3em; margin-bottom: none; }
#navi li { float: right; list-style-type: none; height: 3em; width: 5em; }
#navi_prev { text-align: right; }
#navi_next { text-align: left; }
#navi #navi_top { text-align: center; width: 1em; }
#header h1, #navi li { font-size: 3em; padding: 3px 1.5em; }
#thumbs { margin: 0 auto; }
#thumbs td { padding: 10px; text-align: center; }
#thumbs img { padding: 3px; border: 3px solid #999; opacity: 0.6; }
#thumbs img:hover { border-color: #000; border-bottom-color: #000; opacity: 1; }
#single { margin: 0 auto; padding-top: 1px; position: relative; }
#single #img_name { width: 1em; padding-bottom: 1em; vertical-align: top; }
#single #img_desc { padding: 0 2em 1em 2em; vertical-align: bottom; font-size: 2em; }
#single h2 { font-size: 4em; }
#single img { padding: 3px; border: 3px solid #999; }
#single img:hover { border-color: #000; }
'''
    tpl_index           = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
    <head>
        <title>%(TITLE)s</title>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <link rel="stylesheet" href="gallerygen.css" type="text/css" />
        <meta name="generator" content="gallerygen by MySZ (c) 2008" />
    </head>
    <body>
        %(BODY)s
    </body>
</html>'''
    tpl_thumbs          = '''
        <div id="header">
            <ul id="navi">
                <li id="navi_next">%(next)s</li>
                <li id="navi_top">%(top)s</li>
                <li id="navi_prev">%(prev)s</li>
            </ul>
            <br class="clear" />
        </div>
        <table id="thumbs">
            %(thumbs_rows)s
        </table>'''
    tpl_thumbs_row      = '''
            <tr>
                %(thumbs_cols)s
            </tr>
    '''
    tpl_thumbs_col      = '''
                <td>
                    <a href="%(href_small)s"><img src="%(img_th)s" width="%(th_width)s" height="%(th_height)s" title="%(img_desc)s" /></a>
                    <p>%(img_name)s</p>
                </td>
    '''
    tpl_single          = '''
        <div id="header">
            <ul id="navi">
                <li id="navi_next">%(next)s</li>
                <li id="navi_top">%(top)s</li>
                <li id="navi_prev">%(prev)s</li>
            </ul>
            <br class="clear" />
        </div>
        <table id="single" width="%(img_width)s">
            <tr>
                <td colspan="2"><a href="%(href_big)s"><img src="%(img_small)s" width="%(img_width)s" height="%(img_height)s"></a></td>
            </tr>
            <tr>
                <td id="img_name"><h2>%(img_name)s</h2></td>
                <td id="img_desc">%(img_desc)s</td>
            </tr>
        </table>
    '''

def thumb_create (images, width=100, height=100):
    ret = 0
    for src, dst in images:
        try:
            w, h = commands.getoutput ('identify ' + src).split ()[2].split ('x')
            w, h, l, t = int (w), int (h), 0, 0

            if w > h:
                l = round ((w - h) / 2)
                w = h
            elif h > w:
                t = round ((h - w) / 2)
                h = w

            commands.getoutput ('convert -crop %dx%d+%d+%d %s %s' % (w, h, l, t, src, dst))
            commands.getoutput ('convert -resize %dx%d %s %s' % (width, height, dst, dst))
#             commands.getoutput ('convert -blur 15 %s %s' % (dst, dst + '.jpg'))
            ret += 1
        except:
            try:
                if os.path.isfile (dst):
                    os.remove (dst)
            except:
                pass

    return ret
def image_resize (path, size='50%', sharpen=2):
    src, dst = path
    try:
        if sharpen:
            sharpen = '-sharpen ' + str (sharpen)
        else:
            sharpen = ''
        commands.getoutput ('convert -resize %s %s %s %s' % (size, sharpen, src, dst))
    except:
        try:
            if os.path.isfile (dst):
                os.remove (dst)
        except:
            pass
        return False

    return True

def main ():
    try:
        cfg = Config ()
        cfg.load ('/Users/mysz/.gallerygen.rc')
    except Exception:
        print (e, file=sys.stderr)
        raise SystemExit (5)

    ## parsing parameters
    import getopt
    opt_short   = 'vd:m:n:r:c:t:sk:l:f:o:p:a:'
    opt_long    = ('version', 'directory=', 'width=', 'height=', 'rows=', 'cols=', 'title=', 'skip-images',
        'single-width=', 'single-height=', 'config=', 'big-width=', 'big-height=', 'sharpen=', 'help'
    )

    try:
        opts, args = getopt.gnu_getopt (sys.argv[1:], opt_short, opt_long)
    except getopt.GetoptError, e:
        print (repr (e))
        raise SystemExit (1)

    try:
        for o, a in opts:
            if o in ('--help'):
                print (usage)
                raise SystemExit (0)
            elif o in ('-v', '--version'):
                print (version)
                raise SystemExit (0)
            elif o in ('-d', '--directory'):
                cfg.directory = a
            elif o in ('-m', '--width'):
                cfg.th_width = a
            elif o in ('-n', '--height'):
                cfg.th_height = a
            elif o in ('-r', '--rows'):
                cfg.th_rows = a
            elif o in ('-c', '--cols'):
                cfg.th_cols = a
            elif o in ('-s', '--skip-images'):
                cfg.skip_images = True
            elif o in ('-t', '--title'):
                cfg.title = a
            elif o in ('-k', '--single-width'):
                cfg.single_width = a
            elif o in ('-l', '--single-height'):
                cfg.single_height = a
            elif o in ('-o', '--big-width'):
                cfg.big_width = a
            elif o in ('-p', '--big-height'):
                cfg.big_height = a
            elif o in ('-f', '--config'):
                cfg.config = a
            elif o in ('-a', '--sharpen'):
                cfg.sharpen = a
    except Exception, e:
        print ('Error occured: %s' % repr (e), file=sys.stderr)
        raise SystemExit (2)

    ## validating
    if not cfg.directory:
        print ("Give me some directory!", file=sys.stderr)
        raise SystemExit (7)
    elif not os.path.isdir (cfg.directory):
        print ('"%s" is not a directory.' % cfg.directory, file=sys.stderr)
        raise SystemExit (3)
    try:
        cfg.th_width        = int (cfg.th_width)
        cfg.th_height       = int (cfg.th_height)
        cfg.th_rows         = int (cfg.th_rows)
        cfg.th_cols         = int (cfg.th_cols)
        cfg.single_width    = int (cfg.single_width)
        cfg.single_height   = int (cfg.single_height)
        cfg.big_width       = int (cfg.big_width)
        cfg.big_height      = int (cfg.big_height)
    except Exception, e:
        print ('Some error occured: "%s".' % e)
        raise SystemExit (6)

    ## search for local config (per album)
    if os.path.isfile (os.path.join (cfg.directory, 'gengallery.rc')):
        cfg.load (os.path.join (cfg.directory, 'gengallery.rc'))

    ## another config - specified with parameters
    if cfg.config:
        cfg.load (cfg.config)

    ## search for images, create thumbs and read descriptions
    files = list ()
    for o in os.listdir (cfg.directory):
        path = os.path.join (cfg.directory, o)
        if not cfg.images.search (o) or not os.path.isfile (path):
            continue

        path_small = os.path.splitext (path)
        path_small = '_small'.join (path_small)

        path_th = os.path.splitext (path)
        path_th = '_th'.join (path_th)

        if not cfg.skip_images:
            if cfg.big_width and cfg.big_height:
                image_resize ((path, path), '%dx%d' % (cfg.big_width, cfg.big_height))
            image_resize ((path, path_small), '%dx%d' % (cfg.single_width, cfg.single_height))
            thumb_create (((path, path_th), ), cfg.th_width, cfg.th_height)
        elif os.path.splitext (o)[0].endswith ('_small') or\
                os.path.splitext (o)[0].endswith ('_th'):
            continue

        desc    = os.path.splitext (path)[0] + '.txt'
        if not os.path.isfile (desc):
            desc = ''
        else:
            with open (desc, 'r') as fh:
                desc = fh.read ()

        files.append ((o, os.path.basename (path_small), os.path.basename (path_th), desc))

    if not files:
        print ('Directory is empty.', file=sys.stderr)
        raise SystemExit (4)

    th_per_page = cfg.th_rows * cfg.th_cols
    pages       = int (math.ceil (len (files) / float (th_per_page)))
    index       = -1

    ## create css
    if cfg.css:
        with open (os.path.join (cfg.directory, 'gallerygen.css'), 'w') as fh:
            fh.write (cfg.css)

    ## iterate with pages
    for page in range (1, pages+1):
        with open (os.path.join (cfg.directory, 'page_%05d.html' % page), 'w') as fh:

            ## iterate with rows of thumbs
            rows = []
            for row in range (1, cfg.th_rows + 1):

                ## iterate with columns of thumbs
                cols = []
                for col in range (1, cfg.th_cols + 1):
                    index += 1
                    try:
                        f = files[index]
                    except IndexError:
                        pass
                    else:
                        ## create single image page
                        with open (os.path.join (cfg.directory, f[0] + '.html'), 'w') as fs:
                            small_width = small_height = 0
                            img_path = os.path.join (cfg.directory, f[1])
                            if os.path.isfile (img_path):
                                data = commands.getoutput ('identify ' + img_path)
                                if data:
                                    small_width, small_height = data.split ()[2].split ('x')
                                    small_width     = int (small_width)
                                    small_height    = int (small_height)
                            if not small_width or not small_height:
                                small_width     = cfg.single_width
                                small_height    = cfg.single_height

                            print (cfg.tpl_index % dict (
                                BODY    = cfg.tpl_single % dict (
                                    top         = '<a href="page_%05d.html">top</a>' % page,
                                    prev        = '<a href="%s.html">prev</a>' % files[index-1][0] if index - 1 > 0 else 'prev',
                                    next        = '<a href="%s.html">next</a>' % files[index+1][0] if index + 1 < len (files) else 'next',
                                    href_big    = f[0],
                                    img_name    = f[0],
                                    img_small   = f[1],
                                    img_width   = small_width,
                                    img_height  = small_height,
                                    img_desc    = f[3],
                                ),
                                TITLE   = cfg.title % dict (
                                    date    = time.strftime ('%Y-%m-%d', time.localtime ()),
                                    pageno  = f[0],
                                ),
                            ), file=fs)

                        ## parse tpl: single thumbnail
                        cols.append (cfg.tpl_thumbs_col % dict (
                            href_small  = f[0] + '.html',
                            img_th      = f[2],
                            img_name    = f[0],
                            img_desc    = f[3],
                            th_width    = cfg.th_width,
                            th_height   = cfg.th_height,
                        ))
                ## parse tpl: single row of thumbs
                rows.append (cfg.tpl_thumbs_row % dict (thumbs_cols = ''.join (cols)))

            ## parse tpl and create page
            print (cfg.tpl_index % dict (
                TITLE       = cfg.title % dict (
                    date    = time.strftime ('%Y-%m-%d', time.localtime ()),
                    pageno  = page,
                ),
                BODY        = cfg.tpl_thumbs % dict (
                    top         = page,
                    prev        = '<a href="page_%05d.html">prev (%d)</a>' % (page-1, page-1) if page > 1 else 'prev',
                    next        = '<a href="page_%05d.html">next (%d)</a>' % (page+1, page+1) if page < pages else 'next',
                    thumbs_rows = ''.join (rows),
                    title       = cfg.title % dict (
                        date    = time.strftime ('%Y-%m-%d', time.localtime ()),
                        pageno  = page,
                    ),
                ),
            ), file=fh)


if __name__ == '__main__':
    main ()

# vim: ft=python
