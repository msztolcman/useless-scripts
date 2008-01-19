#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Marcin Sztolcman <http://urzenia.net>
# License: GPL v.2
# Copyright: (r) 2008

import os.path
import re
import subprocess

import gconf

class MetacityKeybindingsEditor (object):
	TITLE	= 'Metacity Keybindings Editor (c) 2008 Marcin Sztolcman'
	def __init__ (self):
		self.client = gconf.client_get_default ()
		self.current_keybindings = {}

		self.get_current_keybindings ()

	def get_current_keybindings (self):
		for d in self.client.all_entries ('/apps/metacity/global_keybindings'):
			k = os.path.basename (d.get_key ())
			m = re.match ('^run_command_(\d+)$', k)
			if not m:
				continue
			m = int (m.groups ()[0])

			v = d.get_value ().to_string ()
			self.current_keybindings[m] = {'keybinding': v}

		for d in self.client.all_entries ('/apps/metacity/keybinding_commands'):
			k = os.path.basename (d.get_key ())
			m = re.match ('^command_(\d+)$', k)
			if not m:
				continue
			m = int (m.groups ()[0])

			v = d.get_value ().to_string ()
			self.current_keybindings[m]['action'] = v

	def zenity_list (self):
		cmd	= ['/usr/bin/zenity', '--title='+self.TITLE, '--width=700', '--height=420', '--list', '--print-column=ALL', '--text=Select command to edit and click "OK" (click "Cancel" to finish):', '--column=Command', '--column=Action', '--column=Keybinding']
		for d in self.current_keybindings.keys ():
			cmd += [str (d), self.current_keybindings[d]['action'], self.current_keybindings[d]['keybinding']]

		ret = self.system (cmd)[0].strip ()
		ret = ret.split ('|')

		return ret

	def zenity_action (self, data):
		cmd		= ['/usr/bin/zenity', '--title='+self.TITLE, '--entry', '--entry-text='+data, '--text=Get full path to application:']

		ret = self.system (cmd)[0].strip ()
		return ret

	def zenity_keybinding (self, data):
		cmd		= ['/usr/bin/zenity', '--title='+self.TITLE, '--entry', '--entry-text='+data, '--text=Get keybinding to use to start yout application (special keys: <Control>, <Shift>, <Alt>, F1-F12)']

		ret = self.system (cmd)[0].strip ()
		return ret

	def gconf_set (self, cmdno, action, keybinding):
		if not keybinding:
			keybinding = 'disabled'

		self.client.set_string ('/apps/metacity/keybinding_commands/command_'+str(cmdno), action)
		self.client.set_string ('/apps/metacity/global_keybindings/run_command_'+str(cmdno), keybinding)

		self.current_keybindings[int (cmdno)] = {'action':action, 'keybinding':keybinding}
#        self.get_current_keybindings ()

	def system (self, cmd):
		return subprocess.Popen (cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate ()


if __name__ == '__main__':
	S = MetacityKeybindingsEditor ()
	while True:
		elem = S.zenity_list ()
		if len (elem) % 3:
			break

		action		= S.zenity_action (elem[1])
		keybinding	= S.zenity_keybinding (elem[2])
		S.gconf_set (elem[0], action, keybinding)

# vim: ft=python
