# mod.zombi and Sven H - 03.03.2024
from __future__ import division
from Components.Converter.Converter import Converter
from Components.Element import cached, ElementError
from enigma import iServiceInformation, iServiceInformationPtr, iPlayableServicePtr, iPlayableService, eServiceCenter, eServiceReference
from ServiceReference import ServiceReference

class ExtMovieInfo(Converter, object):
	MOVIE_SHORT_DESCRIPTION = 0 # meta description when available.. when not .eit short description
	MOVIE_META_DESCRIPTION = 1 # just meta description when available
	MOVIE_REC_SERVICE_NAME = 2 # name of recording service
	MOVIE_REC_FILESIZE = 3 # filesize of recording
	MOVIE_NAME_SHORT_DESCRIPTION = 4
	MOVIE_EXTENDED_DESCRIPTION = 5
	MOVIE_SHORT_EXTENDED_DESCRIPTION = 6
	MOVIE_NAME = 7
	MOVIE_PICON = 8

	def __init__(self, type):
	
		args = type.split(',')
		type = args.pop(0)

		#set params
		self._noShortDescNewline = "noShortDescEnter" in args or "noShortDescNewline" in args
		self._noExtDescDoubleNewline = "noExtDescDoubleEnter" in args or "noExtDescDoubleNewline" in args

		if type == "ShortDescription":
			self.type = self.MOVIE_SHORT_DESCRIPTION
		elif type == "ExtendedDescription":
			self.type = self.MOVIE_EXTENDED_DESCRIPTION
		elif type == "NameShortDescription":
			self.type = self.MOVIE_NAME_SHORT_DESCRIPTION
		elif type == "ShortExtendedDescription":
			self.type = self.MOVIE_SHORT_EXTENDED_DESCRIPTION
		elif type == "Name":
			self.type = self.MOVIE_NAME
		elif type == "MetaDescription":
			self.type = self.MOVIE_META_DESCRIPTION
		elif type == "RecordServiceName":
			self.type = self.MOVIE_REC_SERVICE_NAME
		elif type == "FileSize":
			self.type = self.MOVIE_REC_FILESIZE
		elif type == "Picon":
			self.type = self.MOVIE_PICON
		else:
			self.type = self.MOVIE_NAME
		Converter.__init__(self, type)

	@cached
	def getText(self):
		service = self.source.service
		info = None
		event = None
		

		if isinstance(service, iPlayableServicePtr): 
			#for movieplayer
			from Screens.InfoBar import InfoBar
			service = InfoBar.instance.session.nav.getCurrentlyPlayingServiceReference()
			info = service and eServiceCenter.getInstance().info(service)
			event = info and info.getEvent(service)
			
			if not info:
				info = self.source.service and self.source.service.info()
				service = self.source.service
				event = info and info.getEvent(0)
		
		elif hasattr(self.source, "info"):
			info = self.source.info
			event = self.source.event
		
		if info and service:
			if self.type == self.MOVIE_SHORT_DESCRIPTION:
				shortdescr = self.getShortDescription(info, service, event)
				return shortdescr
			elif self.type == self.MOVIE_EXTENDED_DESCRIPTION:
				extDescr = event and event.getExtendedDescription()
				if extDescr and self._noExtDescDoubleNewline:
					extDescr = extDescr.replace("\n\n","\n").replace("\xc2\x8a\xc2\x8a","\n")
				return extDescr
			elif self.type == self.MOVIE_NAME:
				namestr = self.getEventName(info, service, event)
				return namestr
			elif self.type == self.MOVIE_NAME_SHORT_DESCRIPTION:
				nameShortDescr = self.getNameShortDescription(info, service, event)
				return nameShortDescr
			elif self.type == self.MOVIE_SHORT_EXTENDED_DESCRIPTION:
				shortDescr = self.getShortDescription(info, service, event)
				extDescr = event and event.getExtendedDescription()
				if extDescr and self._noExtDescDoubleNewline:
					extDescr = extDescr.replace("\n\n","\n").replace("\xc2\x8a\xc2\x8a","\n")
				if shortDescr:
					shortDescr = "%s\n" % (shortDescr,)
				return "%s%s" % (shortDescr, extDescr)
			elif self.type == self.MOVIE_META_DESCRIPTION:
				return self.getInfoString(info, service, iServiceInformation.sDescription)
			elif self.type == self.MOVIE_REC_SERVICE_NAME:
				rec_ref_str = self.getInfoString(info, service, iServiceInformation.sServiceref)
				return ServiceReference(rec_ref_str).getServiceName()
			elif self.type == self.MOVIE_REC_FILESIZE:
				if isinstance(info,iServiceInformationPtr):
					filesize = info.getInfoObject(iServiceInformation.sFileSize)
				else:
					filesize = info.getInfoObject(service, iServiceInformation.sFileSize)
				if filesize is not None:
					filesize = filesize // (1024*1024)
					if filesize > 1024:
						filesize = filesize / 1024
						return "%.2f GB" % (filesize)
					return "%d MB" % (filesize)
			elif self.type == self.MOVIE_PICON:
				return self.getInfoString(info, service, iServiceInformation.sServiceref)
		return ""

	text = property(getText)
	
	def changed(self, what):
		# change only on this SPECIFIC iPlayableService-Events:
		# iPlayableService.evStart = 0 or iPlayableService.evVideoTypeReady = 14
		if what[0] != self.CHANGED_SPECIFIC or what[1] in (0, 14):
			Converter.changed(self, what)
	
	def getInfoString(self, info, service, what):
		if isinstance(info,iServiceInformationPtr):
			return info and info.getInfoString(what)
		else:
			return info and info.getInfoString(service, what)

	def getNameShortDescription(self, info, service, event):
		descr = self.getShortDescription(info, service, event).strip(" ")
		namestr = self.getEventName(info, service, event)
		#clean descr if name is at begin of descr
		if descr and namestr and descr.replace("-","").replace(" ","").replace(",","").startswith(namestr.replace("-","").replace(" ","").replace(",","")):
			descr = descr.replace(namestr,"").strip().lstrip("\n")
			descr = descr.replace("\n\n","\n").replace("\xc2\x8a\xc2\x8a","\n")
			namestr = namestr + " - " + descr.replace("\n", " - ")
		#add descr to name if descr not exist in name 
		elif descr and namestr and descr.replace("-","").replace(" ","").replace(",","") not in namestr.replace("-","").replace(" ","").replace(",",""):
			descr = descr.replace("\n\n","\n").replace("\xc2\x8a\xc2\x8a","\n")
			namestr = namestr + " - " + descr.replace("\n", " - ")
		return namestr

	def getShortDescription(self, info, service, event):
		descr = self.getInfoString(info, service, iServiceInformation.sDescription)
		if descr == "" and event:
			descr = event.getShortDescription()
		descr = descr.lstrip(" ").lstrip("\n").lstrip("\xc2\x8a").replace("\\n","\n")
		if descr and self._noShortDescNewline:
			descr = descr.replace("\n\n","\n").replace("\xc2\x8a\xc2\x8a","\n")
		return descr

	def getEventName(self, info, service, event):
		namestr = ""
		# read EventName from filename
		if isinstance(info,iServiceInformationPtr):
			namestr = info.getName()
		else:
			namestr = info.getName(service)
		# read EventName from movie.txt or eit
		# if event:
			# namestr = event.getEventName()
		if not namestr and event:
			namestr = event.getEventName()
		if namestr:
			namestr = self.cleanNameString(namestr)
		return namestr

	def cleanNameString(self, nameString=""):
		if nameString.endswith(".ts"):
			nameString = nameString[:-3]
		elif nameString.endswith((".mp4",".avi",".mkv",".mov",".flv",".m4v",".mpg",".iso")):
			nameString = nameString[:-4]
		elif nameString.endswith((".divx",".m2ts",".mpeg")):
			nameString = nameString[:-5]
		return nameString.replace('\xc2\x86', '').replace('\xc2\x87', '')

