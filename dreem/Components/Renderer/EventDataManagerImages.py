##
## EventDataManager Image-Renderer
##
# Version 1.0-r31

from __future__ import print_function
from __future__ import absolute_import
from enigma import ePixmap, eCanvas
from Components.config import config
from Components.Renderer.Renderer import Renderer
from Components.ServiceList import PiconLoader
from os import path as os_path, listdir as os_listdir, remove as os_remove
from Tools.BoundFunction import boundFunction
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_SKIN_IMAGE
from enigma import ePicLoad, gPixmapPtr, ePixmap, gFont, eRect, iServiceInformation, iPlayableServicePtr, eServiceReference, eServiceCenter
from ServiceReference import ServiceReference
from Components.AVSwitch import AVSwitch
from skin import parseColor
try:
	from Plugins.Extensions.EventDataManager.plugin import getExistEventImageName, getEventImageName, downloadEventImage, downloadContentImage, edm_print
	edmPluginInstalled = True
except:
	edmPluginInstalled = False

#changed-value-dict for logouput
changedValues = {
	0: "CHANGED_DEFAULT",  # initial "pull" state
	1: "CHANGED_ALL",      # really everything changed
	2: "CHANGED_CLEAR",    # we're expecting a real update soon. don't bother polling NOW, but clear data.
	3: "CHANGED_SPECIFIC", # second tuple will specify what exactly changed
	4: "CHANGED_POLL",     # a timer expired
	5: "CHANGED_PULSATE",  # element should pulsate
	6: "CHANGED_ANIMATED", # element should be animated
	}

class EventDataManagerImages(Renderer):
	GUI_WIDGET = eCanvas #has ePixmap as base-class

	def __init__(self):
		Renderer.__init__(self)
		self.eventImageName = ""
		self.defaultImageName = ""
		self.defaultPiconName = ""
		self.imagetype = "event,backdrop"
		self.imagetype_list = self.imagetype.split(",")
		self.picload = ePicLoad()
		self.loadColor = parseColor("#80212121")
		self.showAltLogoText = 0
		self.lastEventID = None
		self.force_changed = False
		self.imageScale = self.lastimageScale = ePixmap.SCALE_TYPE_ASPECT
		self.setImagetypeOptions()
		self.firstExec = True
		self.widgetName = ""
	
	def setImagetypeOptions(self):
		if config.plugins.eventdatamanager.showCoverFallback.value and ("backdrop" in self.imagetype_list or "event" in self.imagetype_list) and "cover" not in self.imagetype_list:
			self.imagetype += ",cover"
			self.imagetype_list = self.imagetype.split(",")
		if config.plugins.eventdatamanager.showPiconFallback.value and ("backdrop" in self.imagetype_list or "event" in self.imagetype_list) and "picon" not in self.imagetype_list:
			self.imagetype += ",picon"
			self.imagetype_list = self.imagetype.split(",")
		if config.plugins.eventdatamanager.showEventFallback.value and ("backdrop" in self.imagetype_list) and "event" not in self.imagetype_list:
			if self.imagetype.endswith(",picon"):
				self.imagetype = self.imagetype.rstrip(",picon")
				self.imagetype += ",event,picon"
			else:
				self.imagetype += ",event"
			self.imagetype_list = self.imagetype.split(",")
		if not config.plugins.eventdatamanager.showLogo.value and self.imagetype == "logo":
			self.imagetype = ""
	
	def applySkin(self, desktop, parent):
		attribs = [ ]
		for (attrib, value) in self.skinAttributes:
			if attrib == "defaultimage":
				self.defaultImageName = value
			elif attrib == "defaultpicon":
				self.defaultPiconName = value
			elif attrib == "imagetype":
				self.imagetype = value.lower()
				self.imagetype_list = self.imagetype.split(",")
				self.setImagetypeOptions()
			elif attrib == "showAltLogoText":
				self.showAltLogoText = value
			elif attrib == "widgetName":
				self.widgetName = value
			else:
				if attrib == "scale": 
					self.imageScale = self.lastimageScale = self.getScaleValue(value)
					edm_print("[EDM] renderer applySkin scale value", value, self.imagetype)
				attribs.append((attrib,value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	def postWidgetCreate(self, instance):
		instance.setDefaultAnimationEnabled(self.source.isAnimated)

	def doSuspend(self, suspended):
		if not suspended and self.firstExec and self.lastEventID is None:
			self.firstExec = False
			edm_print("[EDM] Renderer doSuspend", suspended, self.lastEventID, self.imagetype, self.widgetName)
			self.changed((self.CHANGED_DEFAULT,))

	def getScaleValue(self, scaleValue):
		return {
			"off" :  ePixmap.SCALE_TYPE_NONE,
			"none" :  ePixmap.SCALE_TYPE_NONE,
			"on" :  ePixmap.SCALE_TYPE_ASPECT,
			"aspect" : ePixmap.SCALE_TYPE_ASPECT,
			"center" : ePixmap.SCALE_TYPE_CENTER,
			"width" : ePixmap.SCALE_TYPE_WIDTH,
			"height" : ePixmap.SCALE_TYPE_HEIGHT,
			"stretch" : ePixmap.SCALE_TYPE_STRETCH,
			"fill" : ePixmap.SCALE_TYPE_FILL,
		}.get(scaleValue, ePixmap.SCALE_TYPE_ASPECT)

	def changed(self, what):
		if self.instance:
			if what[0] == self.CHANGED_ANIMATED:
				self.instance.setDefaultAnimationEnabled(self.source.isAnimated)
				return
			
			elif what[0] == self.CHANGED_CLEAR:
				edm_print("[EDM] Renderer CALL CHANGED", what, changedValues.get(what[0]), "exit with no action", self.widgetName)
				self.resetPixmap()
				self.lastEventID = "clear_clear_clear"
				self.eventImageName = ""
				return
			
			if what[0] == 3:# and len(what)>1 and what[1] >0:
				#don't use CHANGED_SPECIFIC #use only CHANGED_SPECIFIC with 0
				edm_print("[EDM] Renderer change - wrong changed-event", what, self.widgetName)
				return
			
			if not edmPluginInstalled:
				edm_print("[EDM] Renderer change - plugin is not installed")
				return
			
			if self.imagetype == "":
				edm_print("[EDM] Renderer change - no imagetype selected", self.widgetName)
				return
			
			eventImageName = ""
			showLogo = "logo" in self.imagetype
			currentService = None
			#event = self.source.event
			event = None
			eventName = ""
			
			edm_print("[EDM] Renderer CALL CHANGED", what, changedValues.get(what[0]), self.widgetName)
			
			#edm_print("[EDM] Renderer change self.source", self.source, self.imagetype)

			# if hasattr(self.source, "service"):
				# edm_print("[EDM] Renderer change - source.service", self.source.service)
			# else:
				# edm_print("[EDM] Renderer change - no source.service")
			# if hasattr(self.source, "navcore"):
				# edm_print("[EDM] Renderer change - navcore service", self.source.navcore.getCurrentServiceReference().toString())
			# else:
				# edm_print("[EDM] Renderer change - no navcore service")
			# if hasattr(self.source, "currentService"):
				# edm_print("[EDM] Renderer change - source.currentService", self.source.currentService)
			# else:
				# edm_print("[EDM] Renderer change - no source.currentService")

			if hasattr(self.source, "service"):
				edm_print("[EDM] Renderer - changed - source.service", self.source.service, self.widgetName)
				service = self.source.service
				if isinstance(service, iPlayableServicePtr): #for movieplayer
					info = service and service.info()
					currentService = info.getInfoString(iServiceInformation.sServiceref)
					event = info and info.getEvent(0)
					if event:
						eventName = event.getEventName()
					info = eServiceCenter.getInstance().info(eServiceReference(currentService))
					if info:
						currentService = info.getInfoString(eServiceReference(currentService), iServiceInformation.sServiceref)
					edm_print("[EDM] Renderer - changed - iplayable service", currentService, eventName, self.widgetName)
				elif isinstance(service, eServiceReference):
					currentService = service.toString()
					event = self.source.event
			
			#get currentService and event from live-tv or movieplayer for Infobar
			elif hasattr(self.source, "navcore"):
				currentService = self.source.navcore.getCurrentServiceReference().toString()
				if currentService.startswith("-1:"): 
					currentService = None
				event = self.source.event
				if event:
					eventName = event.getEventName()
				edm_print("[EDM] Renderer - changed - navcore service '%s' '%s'" % (currentService, eventName), self.widgetName)

				#if movieplayer - get service from info.getInfoString
				currentService1 = ServiceReference(self.source.navcore.getCurrentServiceReference())
				if isinstance(currentService, str) and currentService.startswith("1:0:0:0:0:0:0:0:0:0:/") and isinstance(currentService1, ServiceReference) and currentService1.getPath():
					info = currentService1 and currentService1.info()
					currentService = info and info.getInfoString(eServiceReference(currentService1.ref.toString()), iServiceInformation.sServiceref)
					edm_print("[EDM] Renderer - changed - navcore info-service '%s' '%s'" % (currentService, eventName), self.widgetName)
				else:
					edm_print("[EDM] Renderer - changed - navcore service '%s' '%s'" % (currentService, eventName), self.widgetName)

			#get currentService from EDM-EventView
			elif hasattr(self.source, "currentService"):
				currentService = self.source.currentService
				event = self.source.event
				edm_print("[EDM] Renderer - changed - source.currentService", currentService, type(currentService), self.widgetName)
				if isinstance(currentService, ServiceReference) and currentService.getPath() and currentService.ref.toString().startswith("1:0:0:0:0:0:0:0:0:0:/") :
					edm_print("[EDM] Renderer - changed - source.currentService getPath", currentService, self.widgetName)
					info = currentService and currentService.info()
					currentService = info and info.getInfoString(eServiceReference(currentService.ref.toString()), iServiceInformation.sServiceref)
					edm_print("[EDM] Renderer - changed - source.currentService by getInfoString", currentService, self.widgetName)
				else:
					edm_print("[EDM] Renderer - changed - source.currentService", self.source.currentService, self.widgetName)
					currentService = self.source.currentService.ref.toString()
				
			# elif hasattr(self.source, "info"):
				# edm_print("[EDM] Renderer change - source.info", self.source.info)
				# # event = self.source.info and self.source.info.getEvent(self.source.service)
				# info = self.source.info
				# currentService = info.getInfoString(iServiceInformation.sServiceref)
			elif hasattr(self.source, "event") and hasattr(self.source.event, "getEventId"):
				event = self.source.event
			
			
			edm_print("[EDM] Renderer - changed - used currentService, source", currentService, self.source, self.widgetName)
			
			imagetype = self.imagetype
			self.force_changed = False
			if len(what)>1 and what[1] == "force_changed":
				self.force_changed = True
			
			picon_pixmap = None
			if "picon" in self.imagetype and currentService:
				edm_print("[EDM] Renderer - currentService for picon", type(currentService), currentService, self.widgetName)
				picon_pixmap = PiconLoader().getPicon(currentService)
				if not picon_pixmap:
					picon_pixmap = LoadPixmap(self.getDefaultPicon())
				edm_print("[EDM] Renderer - load picon", picon_pixmap, self.imagetype, self.widgetName)
			
			if what[0] != self.CHANGED_CLEAR:
				if event is not None:
					#edm_print("EDM] Renderer - changed - type event", type(event))
					currentEventID = "%s_%s_%s" % (event.getEventId(), event.getEventName(),currentService)
					#edm_print("[EDM] Renderer - change currentEventID", currentEventID, self.widgetName)
					if not self.force_changed and currentEventID == self.lastEventID:
						edm_print("[EDM] Renderer - no change action because no new event", self.widgetName, event.getEventName())
						return
					edm_print("[EDM] Renderer - change event from '%s' to '%s'" % (self.lastEventID, currentEventID), self.widgetName)
					self.lastEventID = currentEventID
					edm_print("[EDM] Renderer - changed", what, self.imagetype, self.imagetype_list, self, self.source, event.getEventName(), self.widgetName)
					#try to load image live from url
					existFilename = ""
					event_backdrop_checked = False
					self.loadingImage = False #break show downloaded image if change event
					
					for imagetype in self.imagetype_list:
						if "event" == imagetype:
							existFilename = downloadEventImage(event, boundFunction(self.downloadCallback, imagetype, showLogo, event), boundFunction(self.downloadErrorInfoEvent, event, showLogo,""))
							if existFilename == True: # not existing, but download from url
								edm_print("[EDM] Renderer - clear Image on event", event.getEventName())
								self.resetPixmap(picon_pixmap, gradient=True)
								self.loadingImage = True
								edm_print("[EDM] Renderer - download with downloadEventImage", existFilename, self.imagetype, event.getEventName(), self.widgetName)
								return
							edm_print("[EDM] Renderer - existFilename after downloadEventImage", existFilename, self.imagetype, event.getEventName(), self.widgetName)
						
						if "backdrop" == imagetype and not existFilename:
							existFilename = downloadContentImage(event, self.downloadCallbackContent, self.downloadErrorInfo, imageType="backdrop", returnImageType=True)
							if existFilename == True: # not existing, but download from url
								edm_print("[EDM] Renderer - clear Image on backdrop", event.getEventName())
								self.resetPixmap(picon_pixmap)
								self.loadingImage = True
								edm_print("[EDM] Renderer - download backdrop with downloadContentImage", existFilename, self.imagetype, event.getEventName(), self.widgetName)
								return
							edm_print("[EDM] Renderer - existFilename after downloadContentImage", existFilename, self.imagetype, event.getEventName(), self.widgetName)
						
						if imagetype == "cover" and self.imagetype_list[0] != "cover" and not existFilename:
							#try to load existing images from image-folder before check cover if mixed imagetype with cover
							showEvent = "event" in self.imagetype
							showBackdrop = "backdrop" in self.imagetype
							event_backdrop_checked = True
							edm_print("[EDM] Renderer - check for existEventImage", imagetype, self.widgetName)
							existFilename = getExistEventImageName(event.getEventName().encode('utf-8'), event.getBeginTime(), checkEvent=showEvent, checkBackdrop=showBackdrop, checkCover=False, checkLogo=False)
							if existFilename: imagetype = self.imagetype_list[0]
						
						if "cover" == imagetype and not existFilename:
							existFilename = downloadContentImage(event, self.downloadCallbackContent, self.downloadErrorInfo, imageType="cover", returnImageType=True)
							if existFilename == True: # not existing, but download from url
								edm_print("[EDM] Renderer - clear Image on cover")
								self.resetPixmap(picon_pixmap)
								edm_print("[EDM] Renderer - download cover with downloadContentImage", existFilename, self.imagetype, self.widgetName)
								self.loadingImage = True
								return
						
						if "logo" == imagetype and not existFilename:
							existFilename = downloadContentImage(event, self.downloadCallbackContent, self.downloadErrorInfo, imageType="logo", returnImageType=True)
							if existFilename == True: # not existing, but download from url
								edm_print("[EDM] Renderer - clear Image on logo")
								self.resetPixmap(picon_pixmap)
								edm_print("[EDM] Renderer - download logo with downloadContentImage", existFilename, self.imagetype, self.widgetName)
								self.loadingImage = True
								return
						
						if existFilename:
							break
					
					edm_print("[EDM] Renderer - existFilename", existFilename, self.imagetype, self.widgetName)
					if not existFilename:
						#try to load existing images from image-folder
						if event_backdrop_checked: #not check twice if already checked 
							showEvent = False
							showBackdrop = False
						else:
							showEvent = "event" in self.imagetype
							showBackdrop = "backdrop" in self.imagetype
						showCover = "cover" in self.imagetype
						edm_print("[EDM] Renderer - check for existEventImage", imagetype, self.widgetName)
						eventImageName = getExistEventImageName(event.getEventName().encode('utf-8'), event.getBeginTime(), checkEvent=showEvent, checkBackdrop=showBackdrop, checkCover=showCover, checkLogo=showLogo)
						if imagetype == "cover" and self.imagetype_list[0] != "cover": 
							imagetype = self.imagetype_list[0]
					else:
						eventImageName = existFilename
				# else:
					# if self.lastEventID != "none_none_none":
						# self.resetPixmap()
						# self.lastEventID = "none_none_none"
			
			edm_print("[EDM] Renderer - after check eventImage '%s'" % eventImageName, picon_pixmap, imagetype, self.widgetName)
			if picon_pixmap and eventImageName == "":
				eventImageName = "picon_" + currentService
				if self.eventImageName != eventImageName:
					self.setImageScale("picon")
					self.instance.setPixmap(picon_pixmap)
					self.force_changed = False
					edm_print("[EDM] Renderer - set picon - current, last, type", eventImageName, self.eventImageName, self.imagetype, self.widgetName)
					self.eventImageName = eventImageName
				else:
					edm_print("[EDM] Renderer - set picon not needed - same picon", eventImageName, self.widgetName)
			
			#get default imagename if no eventImage was found
			if eventImageName == "":
				eventImageName = self.getDefaultImage(event, showLogo)
				edm_print("[EDM] Renderer - set defaultImage", eventImageName, imagetype, self.widgetName)

			#set image from folder
			if self.force_changed or self.eventImageName != eventImageName:
				edm_print("[EDM] Renderer - set local image - current, last, type", eventImageName, self.eventImageName, imagetype, self.widgetName)
				self.resetPixmap(picon_pixmap)
				self.setImage(eventImageName, imagetype, showLogo, event)
			elif eventImageName.startswith("picon_"):
				pass
			else:
				edm_print("[EDM] Renderer - set image not needed  - same Image", eventImageName, imagetype, self.widgetName)
			
			if event:
				currentEventID = "%s_%s_%s" % (event.getEventId(), event.getEventName(), currentService)
				if self.lastEventID != currentEventID:
					edm_print("[EDM] Renderer - change lastEventID '%s' to '%s'" % (self.lastEventID, currentEventID), self.widgetName)
					self.lastEventID = currentEventID
			else:
				edm_print("[EDM] Renderer - change no event", self.widgetName)
				self.lastEventID = None

	def resetPixmap(self, picon_pixmap=None, gradient=False):
		if picon_pixmap:
			self.setImageScale()
			self.instance.setPixmap(picon_pixmap)
		else:
			self.instance.setPixmap(gPixmapPtr())
			if gradient:
				self.instance.setGradient(self.loadColor,self.loadColor,ePixmap.GRADIENT_HORIZONTAL)

	def getDefaultPicon(self):
		PiconImageName = ""
		if self.defaultPiconName:
			PiconImageName = self.defaultPiconName
		else:
			tmp = resolveFilename(SCOPE_CURRENT_SKIN, "picon_default.png")
			if fileExists(tmp):
				PiconImageName = tmp
			else:
				PiconImageName = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/picon_default.png")
		return PiconImageName

	def getDefaultImage(self, event=None, showLogo=None):
		eventImageName = ""
		if event and showLogo and self.showAltLogoText:
			self.writeEventText(event)
		else:
			if self.defaultImageName:
				eventImageName = self.defaultImageName
			else:
				tmp = resolveFilename(SCOPE_CURRENT_SKIN, "picon_default.png")
				if fileExists(tmp):
					eventImageName = tmp
				else:
					eventImageName = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/picon_default.png")
		return eventImageName
		
	def setImage(self, eventImageName, imagetype=None, showLogo=False, event=None):
		#set image to the widget
		size = self.instance.size()
		self.scale = AVSwitch().getFramebufferScale()
		self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 0, "#FF000000"))
		edm_print("[EDM] Renderer - setImage startDecode", str(eventImageName), self.widgetName)
		res = self.picload.startDecode(str(eventImageName), False)
		# self.picload_conn = self.picload.PictureData.connect(boundFunction(self.picloadStartDecodeCallback,eventImageName, imagetype, showLogo, event))
		# self.picload.startDecode(str(eventImageName))
		# return
		
		if not res:
			ptr = self.picload.getData()
			edm_print("[EDM] Renderer - setPixmap ptr", ptr)
			if ptr != None:
				self.setImageScale(imagetype)
				edm_print("[EDM] Renderer - setPixmap ptr", ptr, self.widgetName)
				self.instance.setPixmap(ptr)
				self.loadingImage = False
			else:
				edm_print("[EDM] Renderer - problem on getData with ePicload", eventImageName, self.widgetName)
				if imagetype == "event" and "backdrop" in self.imagetype:
					self.downloadErrorInfoEvent(event, showLogo, eventImageName, "Error on set eventImage", "none")
					return
				edm_print("[EDM] Renderer try to show defaultImage after image could not load with ePicload", eventImageName)
				eventImageName = self.getDefaultImage()
				res = self.picload.startDecode(str(eventImageName), False)
				if not res:
					ptr = self.picload.getData()
					if ptr != None:
						self.setImageScale(imagetype)
						edm_print("[EDM] Renderer - setDefaultPixmap ptr", ptr, self.widgetName)
						self.instance.setPixmap(ptr)
						self.loadingImage = False
					else:
						edm_print("[EDM] Renderer - problem on getData DefaultImage with ePicload", eventImageName, self.widgetName)
				else:
					edm_print("[EDM] Renderer - problem on startDecode DefaultImage with ePicload", eventImageName, self.widgetName)
		else:
			edm_print("[EDM] Renderer - problem on startDecode with ePicload", eventImageName, self.widgetName)
		self.eventImageName = eventImageName

	# def picloadStartDecodeCallback(self, eventImageName, imagetype=None, showLogo=False, event=None, picInfo=None):
		# ptr = self.picload.getData()
		# edm_print("[EDM] Renderer - picloadStartDecodeCallback ptr", ptr, picInfo.replace("\n"," "), self.widgetName)
		# if ptr != None:
			# self.setImageScale(imagetype)
			# edm_print("[EDM] Renderer - setPixmap ptr", ptr, eventImageName, self.widgetName)
			# self.instance.setPixmap(ptr)
			# self.loadingImage = False
		# else:
			# edm_print("[EDM] Renderer - problem on getData with ePicload", eventImageName, self.widgetName)
			# if imagetype == "event" and "backdrop" in self.imagetype:
				# self.downloadErrorInfoEvent(event, showLogo, eventImageName, "Error on set eventImage", "none")
				# return
			# edm_print("[EDM] Renderer try to show defaultImage after image could not load with ePicload", eventImageName, self.widgetName)
			# eventImageName = self.getDefaultImage()
			# self.picload_conn = None
			# res = self.picload.startDecode(str(eventImageName), False)
			# if not res:
				# ptr = self.picload.getData()
				# if ptr != None:
					# self.setImageScale(imagetype)
					# edm_print("[EDM] Renderer - setDefaultPixmap ptr", ptr, self.widgetName)
					# self.instance.setPixmap(ptr)
					# self.loadingImage = False
				# else:
					# edm_print("[EDM] Renderer - problem on getData DefaultImage with ePicload", eventImageName, self.widgetName)
			# else:
				# edm_print("[EDM] Renderer - problem on startDecode DefaultImage with ePicload", eventImageName, self.widgetName)
		# self.eventImageName = eventImageName

	def setImageScale(self, imagetype=None):
		if imagetype == "cover" and self.imagetype_list[0] != "cover":
			if self.lastimageScale != ePixmap.SCALE_TYPE_HEIGHT:
				edm_print("[EDM] renderer setImageScale to 'height'", imagetype, self.imagetype)
				self.lastimageScale = ePixmap.SCALE_TYPE_HEIGHT
				self.instance.setScale(ePixmap.SCALE_TYPE_HEIGHT)
		elif imagetype == "picon":
			if self.lastimageScale != ePixmap.SCALE_TYPE_ASPECT:
				self.lastimageScale = ePixmap.SCALE_TYPE_ASPECT
				self.instance.setScale(ePixmap.SCALE_TYPE_ASPECT)
		else:
			if self.lastimageScale != self.imageScale:
				self.lastimageScale = self.imageScale
				edm_print("[EDM] renderer setImageScale to default", self.imageScale, imagetype, self.imagetype)
				self.instance.setScale(self.imageScale)

	def writeEventText(self, event):
		#write Event-Title in the image
		self.instance.setPixmap(gPixmapPtr())
		self.font = gFont("Regular", 40)
		self.backgroundColor = parseColor("background")
		self.foregroundColor = parseColor("#00FFFFFF")
		self.instance.setGradient(self.backgroundColor,self.backgroundColor,ePixmap.GRADIENT_HORIZONTAL)
		size = self.instance.size()
		rect = eRect(0,0, size.width(), size.height())
		self.instance.writeText(rect, self.foregroundColor, self.backgroundColor, self.font, event.getEventName().encode('utf-8'), 2|8)
		#useable Flags: 
		#RT_HALIGN_LEFT=0, RT_HALIGN_RIGHT=1, RT_HALIGN_CENTER=2, RT_HALIGN_BLOCK=4,
		#RT_VALIGN_CENTER=8, RT_VALIGN_BOTTOM=16, RT_WRAP=32

	def downloadCallback(self, imagetype="", showLogo=False, event=None, retValue=None, eventImageName=""):
		edm_print("[EDM] Renderer downloadCallback '%s' '%s'" % (self.eventImageName, eventImageName), self.loadingImage, imagetype, self.widgetName)
		if self.force_changed or self.eventImageName != eventImageName:
			if self.loadingImage:
				edm_print("[EDM] Renderer set downloaded image", self.eventImageName, eventImageName, self.widgetName)
				self.setImage(eventImageName, imagetype, showLogo, event)

	def downloadCallbackContent(self, retValue, eventImageName, imagetype):
		edm_print("[EDM] Renderer downloadCallbackContent '%s' '%s'" % (self.eventImageName, eventImageName), self.loadingImage, imagetype, self.widgetName)
		if self.force_changed or self.eventImageName != eventImageName:
			if self.loadingImage:
				edm_print("[EDM] Renderer set downloaded content-image", self.eventImageName, eventImageName)
				filename, file_extension = os_path.splitext(eventImageName)
				if file_extension == ".svg": #convert to png
					self.pixmap = ePixmap(None)
					self.pixmap.setPixmapFromFile(eventImageName)
					file_extension = ".png"
					self.pixmap.save(ePixmap.FMT_PNG, filename + file_extension)
					os_remove(eventImageName)
				self.setImage(filename + file_extension, imagetype)

	def downloadErrorInfoEvent(self, event, showLogo, last_eventImageName, error, url):
		edm_print("[EDM] Renderer EventImageDownload ERROR:", self.imagetype, error, url, self.widgetName)
		edm_print("[EDM] Renderer try to load exist EventImage after error on EventImageDownload")
		eventImageName = getExistEventImageName(event.getEventName().encode('utf-8'), event.getBeginTime(), checkEvent=True, checkBackdrop=False, checkCover=False, checkLogo=showLogo, event=event)
		if eventImageName == last_eventImageName and "backdrop" in self.imagetype:
			edm_print("[EDM] Renderer try to load backdrop after error on EventImageDownload")
			existFilename = downloadContentImage(event, self.downloadCallbackContent, self.downloadErrorInfo, imageType="backdrop", returnImageType=True)
			if existFilename == True: # not existing, but download from url
				edm_print("[EDM] Renderer - clear Image on ErrorInfoEvent")
				self.instance.setPixmap(gPixmapPtr())
				self.loadingImage = True
				edm_print("[EDM] Renderer download backdrop with downloadContentImage", existFilename, self.imagetype)
				return
			elif existFilename:
				eventImageName = existFilename
			else:
				eventImageName = self.getDefaultImage(event, showLogo)

		edm_print("[EDM] Renderer set local image on error - current, last, type", eventImageName, self.eventImageName, self.imagetype, self.widgetName)
		self.instance.setPixmap(gPixmapPtr())
		self.setImage(eventImageName)

	def downloadErrorInfo(self, error, url):
		edm_print("[EDM] Renderer ImageDownload ERROR:", error, url, self.widgetName)
		self.loadingImage = False
		eventImageName = self.getDefaultImage()
		if self.force_changed or self.eventImageName != eventImageName:
			edm_print("[EDM] Renderer try to set default image after error - current, last", eventImageName, self.eventImageName)
			self.instance.setPixmap(gPixmapPtr())
			self.setImage(eventImageName)

