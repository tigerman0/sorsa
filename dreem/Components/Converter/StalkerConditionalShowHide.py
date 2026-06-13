# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from enigma import eTimer
from Components.Converter.Converter import Converter
from Components.Renderer.Renderer import Renderer

from Plugins.Extensions.StalkerClient.StalkerChannels import stalkerCurrentSelection
from Plugins.Extensions.StalkerClient.api import StalkerVodService, StalkerCategorie, StalkerGenre, StalkerEpisodeService
from Plugins.Extensions.StalkerClient.__init__ import stalker_print

class StalkerConditionalShowHide(Converter, object):
	
	#=== params ===
	# hideOnVOD
	# hideOnITV
	# hideIfHasImdbRating
	# hideOnFolder
	# hideIfNoEvent

	def __init__(self, argstr):
		Converter.__init__(self, argstr)
		
		if not argstr:
			self.args = "hideonvod"
		else:
			self.args = argstr.lower().split(',')
		
		stalker_print("Converter - init", self.args)
		
		self.text = None
		self.service = None
		self.event = None
		self.range = None
		self.value = None
		self.visible = True

	def calcVisibility(self):
		service = stalkerCurrentSelection.stalkerservice
		if service:
			if "hideonvod" in self.args and isinstance(service, (StalkerVodService, StalkerEpisodeService, StalkerCategorie)):
				stalker_print("Converter - hide because is VODService or StalkerCategorie", service)
				return False
			if "hideonitv" in self.args and (service.type == "itv" or isinstance(service, StalkerGenre)):
				stalker_print("Converter - hide because is ITVService", service)
				return False
			if "hideifhasimdbrating" in self.args and hasattr(service,"rating_imdb"):
				stalker_print("Converter - rating_imdb", service.rating_imdb)
				if service.rating_imdb and service.rating_imdb != "N/A" and float(service.rating_imdb):
					stalker_print("Converter - hide because has rating_imdb")
					return False
			if "hideonfolder" in self.args and service.isFolder():
				stalker_print("Converter - hide because isFolder", service)
				return False
			if "hideifnoevent" in self.args and not stalkerCurrentSelection.event:
				stalker_print("Converter - hide because if no event")
				return False
		else:
			stalker_print("Converter - hide because if no service")
			return False
		
		stalker_print("Converter - show because no conditions")
		return True

	def changed(self, what):
		
		self.visible = vis = self.calcVisibility()
		
		stalker_print("Converter - changed", self.args, self.visible, what, self.source)
		if vis:
			for attr in ("text", "service", "event", "range", "value", "pixmap", "time", "boolean"):
				if hasattr(self.source, attr):
					stalker_print("Converter - %s" % attr, self.source, getattr(self.source, attr))
					setattr(self, attr, getattr(self.source, attr))
			
			if hasattr(self.source, "source") and hasattr(self.source.source, "event"):
				stalker_print("Converter - source.source.event", self.source.source.event)
				self.source.event = self.source.source.event
		
		self.downstream_elements.changed(what)
		for x in self.downstream_elements:
			stalker_print("Converter - changed downstream_element", x)
			x.visible = vis

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		self.visible = self.calcVisibility()
		downstream.visible = self.visible

	def destroy(self):
		pass
