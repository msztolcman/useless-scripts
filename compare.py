#!/usr/bin/env python
# $Id$
__version__   = 'version 0.3'
__author__    = 'Marcin ``MySZ`` Sztolcman'
__copyright__ = __author__ + '(r) 2005'
__program__   = "compare.py - tool for comparising directories for different or modified files and directories"
__date__      = '2005-08-09'
__license__   = 'GPL v.2'

__desc__      = '''%(desc)s
%(author)s (r) 2005
license: %(license)s
version %(version)s (%(date)s)''' % {
  'desc': __program__,
  'author': __author__,
  'license': __license__,
  'version': __version__,
  'date': __date__
}

import os
import sys
import time
import re

import getopt
import difflib

def usage(full = False, p = True):
  opts = {
  'prog': os.path.basename(sys.argv[0]),
  'desc': __desc__
}
  m = '''%(desc)s

usage:
%(prog)s [options] [old_directory new_directory]''' % opts
  m2 = '''

where options can be:
-i|--ignore ignore_path
    ignore_path is a path which will be ignored at scanning (needs all
    path, relative to {old,new}_directory)
-d|--ign-dir ignored_dirname
    ignore one directory name, for example:
    %(prog)s -d .svn old new
    will be ignore all occurence of '.svn' and it's content
-f|--ign-file ignore_filename
    the same as -d, but for filenames
-l|--log_dir log_dir
    if options is passed, in log_dir will be created unified diff files,
    with original directory structure of modified files
-u|--diff-type
    specify diff files type. values can be:
      'unified', 'context'
    ignored without '-l' option
-s|--suffix suffix
    by default, newly created diff files (with -l option) have '.diff' suffix.
    it can be changed by this option
    ignored without '-l' option
-v|--version
    prints program name and exits
-h|--help
    prints help and exit

old_directory
    directory name with orginal, unchanged files
new_directory
    directory with new versions of files''' % opts
  ret = m
  if full: ret += m2
  if not p: return ret
  print ret

def version(p = True):
  global __desc__
  if not p:
    return __desc__
  print __desc__

def normalize_path(path):
  path = os.path.expanduser(path)
  path = os.path.normcase(path)
  return path

def compare_files(f1, f2, return_diff = False):
  if not os.path.isfile(f1): return False
  if not os.path.isfile(f2): return False

  f1_content = file(f1, 'r').readlines()
  f2_content = file(f2, 'r').readlines()

  if not return_diff: #nie ma zwracac diffow, wiec metoda uproszczona:
    lines = len(f1_content)
    if not lines == len(f2_content):
      return True
    for i in range(lines):
      if not f1_content[i] == f2_content[i]:
        return True
    return False
  else:
    t1 = time.ctime(os.path.getctime(f1))
    t2 = time.ctime(os.path.getctime(f2))

    diff_content = []
    for l in g_diff_function(f1_content, f2_content, f1, f2, t1, t2, n=5, lineterm='\n'):
      diff_content.append(l) #.rstrip() + "\n")
    return diff_content

def exit(msg, code = 0, usg = False):
  if not code:
    if msg: print msg
    if usg: usage()
    raise SystemExit
  if usg: print >>sys.stderr, usage(p = False) + "\n"
  print >>sys.stderr, msg
  raise SystemExit, code

def check_ignore(path, path_suffix = ''):
  global g_ignore

  for e in g_ignore:
    e += path_suffix
    if path.startswith(e):
      return True
  return False

def check_igndir(path):
  global g_igndir

  if not path: return False
  for d in g_igndir:
    if path.startswith(d + os.sep) or\
        (os.sep + d + os.sep) in path or\
        path.endswith(os.sep + d):
      return True
  return False

def generate_dir_list(d):
  global g_ignfile, g_igndir, g_ignore

  _directories = []
  _files = []
  for root, dirs, files in os.walk(d):
    relative = root[len(d)+1:]
    suffix = relative and os.sep or ''
    relative += suffix

    if not check_ignore(relative, suffix) and not check_igndir(relative):
      for o in dirs:
        full_path = os.path.join(relative, o)
        if not o in g_igndir and not full_path in g_ignore:
          _directories.append(full_path)
      _files.extend([ os.path.join(relative, o)
          for o in files
          if o not in g_ignore and o not in g_ignfile ])
  return (_directories, _files)

def print_result(msg, list = None, exc = None):
  print
  print msg + ':'
  if list is not None and exc is not None:
    print "\n".join([ o for o in list if o not in exc ])

def print_ignore(msg, list):
  print
  print msg + ':'
  if len(list):
    print ' '.join(list)
  else:
    print 'None'




try:
  #ustalamy opcje z jakimi uruchomiono program
  try:
    s_opt = 'i:d:f:l:u:s:vh'
    l_opt = ('ignore=', 'ign-dir=', 'ign-file=', 'log-dir=', 'diff-type=', 'suffix=', 'version', 'help')
    opts, args = getopt.gnu_getopt(sys.argv[1:], s_opt, l_opt)
  except getopt.GetoptError:
    exit('', 1, True)

  #ustawienia domyslne
  g_logdir  = None
  g_ignore  = []
  g_suffix  = '.diff'
  g_igndir  = []
  g_ignfile = []
  g_diff_function = difflib.unified_diff

  for o, a in opts:
    if o in ('-i', '--ignore'):
      g_ignore.append(a.strip())
    elif o in ('-d', '--ign-dir'):
      g_igndir.append(a.strip())
    elif o in ('-f', '--ign-file'):
      g_ignfile.append(a.strip())
    elif o in ('-l', '--log-dir'):
      g_logdir = a.strip()
    elif o in ('-u', '--diff-type'):
      if a == 'unified':
        g_diff_function = difflib.unified_diff
      elif a == 'context':
        g_diff_function = difflib.context_diff
      else:
        exit('Unknown diff type \'%s\'. Diff types must be one of \'unified\' or \'context\'.' % a, 11, True)
    elif o in ('-s', '--suffix'):
      g_suffix = a.strip()
    elif o in ('-v', '--version'):
      version()
      sys.exit(0)
    elif o in ('-h', '--help'):
      usage(full = True, p = True)
      sys.exit(0)

  #sprawdzamy czy sa podane katalogi wejsciowe
  l_args = len(args)
  if l_args < 2:
    exit('Needs both directory names, source and destination.', 2, True)
  elif l_args > 2:
    exit('Too many data.', 3, True)

  #sprawdzamy poprawnosc danych wejsciowych
  g_src, g_dst = args
  g_src = normalize_path(g_src)
  g_dst = normalize_path(g_dst)

  if not os.path.isdir(g_src):
    exit('Source path \'%s\' is not a directory.' % (g_src,), 4, True)
  if not os.access(g_src, os.R_OK):
    exit('Cannot read source path (%s).' % (g_src,), 5, True)
  if not os.path.isdir(g_dst):
    exit('Destination path \'%s\' is not a directory.' % (g_dst,), 6, True)
  if not os.access(g_dst, os.R_OK):
    exit('Cannot read destination path (%s).' % (g_dst,), 7, True)
  if g_logdir is not None:
    g_logdir = normalize_path(g_logdir)
    if not os.path.isdir(g_logdir):
      try:
        os.mkdir(g_logdir, 0755)
      except:
        exit('Cannot create log directory \'%s\'. System returns message:' % (g_logdir,), 8)
    if not os.access(g_logdir, os.W_OK):
      if 'y' == raw_input('Cannot write into specified log directory \'%s\'. Continue ? (Y|n)' % (g_logdir,)):
        g_logdir = None
      else:
        exit('Aborted.', 9)



  dst_directories, dst_files = generate_dir_list(g_dst)
  src_directories, src_files = generate_dir_list(g_src)



  #wyswietlamy co pomijamy
  print_ignore('Ignored paths', g_ignore)
  print_ignore('Ignored directories', g_igndir)
  print_ignore('Ignored files', g_ignfile)

  print "\n======================================"
  print "======================================"
  print "==                                  =="
  print "==           Scan results:          =="
  print "==                                  =="
  print "======================================"
  print "======================================"
  
  #sa nowe katalogi ?
  print_result('Added folders', dst_directories, src_directories)
  #usuwamy katalogi ?
  print_result('Removed folders', src_directories, dst_directories)
  #nowe pliki ?
  print_result('Added files', dst_files, src_files)
  #usuwamy pliki?
  print_result('Removed files', src_files, dst_files)

  #a co zmienione ?
  print_result('Modified files')

  write_error = False
  create_diff = bool(g_logdir)
  for f in dst_files:
    if f in src_files:
      s = os.path.join(g_src, f)
      d = os.path.join(g_dst, f)
      diff = compare_files(s, d, create_diff)
      if diff:
        print f
        #tworzymy diffa ?
        if create_diff and not write_error:
          try:
            dirs = os.path.join(g_logdir, os.path.dirname(f))
            if not os.path.isdir(dirs):
              os.makedirs(dirs, 0755)
            fh = file(os.path.join(dirs, os.path.basename(f) + g_suffix), 'w')
            fh.writelines(diff)
            fh.close()
          except:
            write_error = True
            write_msg   = sys.exc_info()[1]
            pass
  if write_error:
    exit('Cannot write diff files into specified directory(%s).' % g_logdir, 10)
except KeyboardInterrupt:
  exit('Interrupted by user.', 128, False)





'''
ChangeLog:

2005-08-09  - v.0.3 - added '-u' switch (-u specify type of diff files:
                      unified or context)
                    - changed how version() and help() displays
2005-08-08  - v.0.2 - rewritten

TODO:
  - obsluga masek '?' i '*'
'''

# vim: ft=python fdm=manual foldlevel=10000
