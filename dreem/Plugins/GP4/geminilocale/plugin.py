# -*- coding: utf-8 -*-
from gLocale import ArchBox, OEversion, isAIOImage
from Tools.Directories import createDir, pathExists
from Tools.HardwareInfo import HardwareInfo
from Tools.Log import Log
from gVersion import gVersion
from Components.config import config

def _createFeedConf(version, url, typ):
		fname="/etc/apt/sources.list.d/%s-%s-feed.list" %(version,typ)
		if not pathExists(fname):
			try:
				wfile = open(fname, 'w')
				wfile.write("deb [trusted=yes] %s%s ./\n" % (url,typ))
				wfile.close()
				Log.i("'%s' create"%fname)
			except Exception as e:
				Log.e(e)
		#else:
		#	Log.i("'%s' found"%fname)

def CheckGeminiApt():
	if pathExists("/etc/issue.net"):
		try:
			issue = open("/etc/issue.net", "r").read()
			if issue:
				if issue.find("Gemini")<0:
					text ="*****************************\n"
					text+="*                           *\n"
					text+="*   The Gemini Project 4.2  *\n"
					text+="*                           *\n"
					text+="*****************************\n"
					open("/etc/issue.net", "w").write(text)
		except Exception as e:
			Log.e(e)
			
	if not pathExists("/root/.profile"):
		try:
			text ='TERM=xterm\n'
			text+='alias ls="ls --color"'
			open("/root/.profile", "w").write(text)
		except Exception as e:
			Log.e(e)

	#Aufnahme auf Netzlaufwerke
	if not config.misc.recording_allowed.getValue():
		config.misc.recording_allowed.setValue(True)
		config.misc.recording_allowed.save()
	
	#if pathExists("/usr/lib/enigma2/python/Plugins/GP4/geminicomm"):
	#	return
	
	oe="krogoth"
	if OEversion=="2.6.0":
		oe="pyro"

	#data und cache Ordner anlegen
	if pathExists("/data")==False:
		createDir("/data")
	if pathExists("/tmp/.cache/gemini")==False:
		createDir("/tmp/.cache/gemini",True)
		
	apturl="http://download.blue-panel.com/gemini4/%s-gemini4-unstable/" %oe
	extraPlugins="extraPluginsAarch64"
	if ArchBox=="armhf":
		extraPlugins="extraPluginsArmhf"
	elif ArchBox=="mipsel":
		extraPlugins="extraPluginsMipsel"

	if apturl:
		v=gVersion.split(" ")[0]
		_createFeedConf(v,apturl,ArchBox)
		_createFeedConf(v,apturl,'all')
		_createFeedConf(v,apturl,'allcodes')
		_createFeedConf(v,apturl,extraPlugins)
		if isAIOImage:
			_createFeedConf(v,apturl,"aio")
		else:
			_createFeedConf(v,apturl,HardwareInfo().get_device_name())

CheckGeminiApt()
