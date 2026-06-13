# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Log import Log
from os import environ as os_environ
import gettext

def _getArch():
	try:
		file = open("/etc/apt/apt.conf", 'r')
		lines = file.readlines()
		file.close()
		for x in lines:
			entry = x.strip().split(' ')
			if len(entry)==2:
				if entry[1].find("mipsel")>=0:
					return "mipsel"
				elif entry[1].find("armhf")>=0:
					return "armhf"
				elif entry[1].find("arm64")>=0:
					return "aarch64"
	except Exception, e:
		Log.e(e)
	return None
	
ArchBox=_getArch()

def _isAIOImage():
	try:
		from enigma import RT_NO_ELLIPSIS
		Log.i("AIO-Image found")
		return True
	except:
		return False

isAIOImage=_isAIOImage()

def _getOEversion():
	try:
		with open("/etc/os-release", "r") as f:
			for line in f:
				if line.find("VERSION=")==0:
					return line[9:14]
	except Exception, e:
		Log.e(e)
	return None
	
OEversion=_getOEversion()

def localeInit():
	lang = language.getLanguage()[:2]
	os_environ["LANGUAGE"] = lang
	gettext.bindtextdomain("geminilocale", resolveFilename(SCOPE_PLUGINS, "GP4/geminilocale/locale"))

def _(txt):
	t = gettext.dgettext("geminilocale", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

