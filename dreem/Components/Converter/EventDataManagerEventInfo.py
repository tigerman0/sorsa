#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
## EventDataManager EventInfo-Converter
##

# Version 1.0-r31

# =================================================================
# format for Multi-Type
# <convert type="EventDataManagerEventInfo">Multi,{%s }{FSK: %F }{Rate: %r }{Genre: %G}</convert>
# Text between {} will be written only if value is not empty
# Text before { or after } will written every time
#
# '%T' = Title
# '%G' = Genre
# '%S' = Season
# '%E' = Episode
# '%e' = Episodetitle
# '%s' = SeasonEpisode
# '%r' = Rating
# '%F' = FSK
# '%d' = Episodetitle or Event-Description as fallback
#
# ==================================================================

from __future__ import print_function

from Components.Converter.Converter import Converter
from Components.Element import cached
from re import sub as re_sub
try:
	from Plugins.Extensions.EventDataManager.plugin import dbapi, getEventImageName, getCleanContentTitle, getContentYearFromEvent, getContentTypeFromEvent, getContentData, edm_print
	edmPluginInstalled = True
except:
	edmPluginInstalled = False

class EventDataManagerEventInfo(Converter, object):
	TITLE = 0
	GENRE = 1
	FSK   = 2
	SEASON = 3
	EPISODE = 4
	EPISODETITLE = 5
	SEASONEPISODE = 6
	RATING = 7
	CONDITIONALSHOWHIDE = 8
	MULTI = 9

	def __init__(self, type):
		Converter.__init__(self, type)
		edm_print("[EDM] Converter init", type)
		
		self.txt_format = "%s" # default
		args = type.split(',')
		type = args.pop(0)
		
		if args:
			self.txt_format = args[0] # given user format
			if "%" not in args[0]:
				self.txt_format += "%s"
		
		if type == "Genre":
			self.type = self.GENRE
		elif type == "Fsk":
			self.type = self.FSK
		elif type == "Season":
			self.type = self.SEASON
		elif type == "Episode":
			self.type = self.EPISODE
		elif type == "EpisodeTitle":
			self.type = self.EPISODETITLE
		elif type == "SeasonEpisode":
			self.type = self.SEASONEPISODE
			self.txt_format = "S%02dE%02d" # set special format - user format not used
		elif type == "Rating":
			self.type = self.RATING
		elif type == "ConditionalShowHide":
			self.type = self.CONDITIONALSHOWHIDE
		elif type == "Multi":
			self.type = self.MULTI
		else:
			self.type = self.TITLE
		
		self.event = None
		self.eventName = None
		EventDataManagerEventInfo.rating = None
		EventDataManagerEventInfo.lastEvent = None
		self.force_changed = False
		
		if edmPluginInstalled:
			self.dbApi = dbapi

	def getSeasonEpisode(self, txt_format="S%02dE%02d"):
		season = int(str(EventDataManagerEventInfo.season or "").strip() or 0)
		episode = str(EventDataManagerEventInfo.episode or "") or 0 #for episodes like E4+5
		if (episode and EventDataManagerEventInfo.episode.isdigit()) or episode == 0:
			episode = int(str(EventDataManagerEventInfo.episode or "").strip() or 0)
			if season == 0 and episode == 0:
				return ""
			return txt_format % (season, episode)
		else:
			txt_format = txt_format.replace("E%02d","E%s",1)
			return txt_format % (season, episode)

	def getRatingText(self, txt_format="%s"):
		edm_print("[EDM] Converter getText for Rating", txt_format % EventDataManagerEventInfo.rating)
		rating = EventDataManagerEventInfo.rating
		if rating is None or float(rating) == 0:
			return txt_format % ""
		else:
			return txt_format % format(float(rating), '.1f')
	
	@cached
	def getText(self):
		if not edmPluginInstalled:
			print("[EDM] Converter getText - Plugin not installed")
			return ""
		edm_print("[EDM] Converter getText start")
		self.event = self.source.event
		if self.event is None:
			return ""
		self.checkLoadData()
		
		if self.type == self.TITLE:
			return self.txt_format % EventDataManagerEventInfo.title
		elif self.type == self.GENRE:
			return self.txt_format % EventDataManagerEventInfo.genre
		elif self.type == self.FSK:
			return self.txt_format % EventDataManagerEventInfo.fsk
		elif self.type == self.SEASON:
			return self.txt_format % EventDataManagerEventInfo.season
		elif self.type == self.EPISODE:
			return self.txt_format % EventDataManagerEventInfo.episode
		elif self.type == self.EPISODETITLE:
			return self.txt_format % EventDataManagerEventInfo.episodetitle
		elif self.type == self.SEASONEPISODE:
			return self.getSeasonEpisode(self.txt_format)
		elif self.type == self.RATING:
			return self.getRatingText(self.txt_format)
		elif self.type == self.MULTI:
			tmp = self.txt_format[:].replace("}","")
			paramlist = tmp.split("{")
			result = ''
			for param in paramlist:
				p_value = ''
				pos = param.find('%')
				if pos == -1:
					result += param
					continue
				pre_value_txt = param[:pos]
				pos += 1
				l = len(param)
				f = pos < l and param[pos] or '%'
				post_value_txt = param[pos+1:]
				if f == 'T':
					p_value = "%s" % EventDataManagerEventInfo.title
				elif f == 'G':
					p_value = "%s" % EventDataManagerEventInfo.genre
				elif f == 'F':
					p_value = "%s" % EventDataManagerEventInfo.fsk
				elif f == 'S':
					p_value = "%s" % EventDataManagerEventInfo.season
				elif f == 'E':
					p_value = "%s" % EventDataManagerEventInfo.episode
				elif f == 'e':
					p_value = "%s" % EventDataManagerEventInfo.episodetitle
				elif f == 'd':
					p_value = "%s" % EventDataManagerEventInfo.episodetitle
					if not p_value:
						shortDesc = self.event.getShortDescription()
						if shortDesc and shortDesc != EventDataManagerEventInfo.title:
							if shortDesc.startswith(EventDataManagerEventInfo.title + "\n"):
								shortDesc = shortDesc.replace(EventDataManagerEventInfo.title + "\n", "")
								shortDesc = re_sub('\\n\(WH vom .*\)', '', shortDesc)
							p_value = "%s" % shortDesc
				elif f == 's':
					p_value = self.getSeasonEpisode()
				elif f == 'r':
					p_value = self.getRatingText()
				else:
					p_value = f
				#fill text only if get a param-value
				if len(p_value):
					result += pre_value_txt + p_value + post_value_txt
			return '%s' % (result)

	@cached
	def getValue(self):
		if not edmPluginInstalled:
			print("[EDM] Converter getValue - Plugin not installed")
			return 0
		edm_print("[EDM] Converter getValue start")
		self.event = self.source.event
		if self.event is None:
			return 0
		self.checkLoadData()
		if EventDataManagerEventInfo.rating is None:
			edm_print("[EDM] Converter getValue return Rating Value 0 because no data")
			return 0
		edm_print("[EDM] Converter getValue return Rating Value", int(float(EventDataManagerEventInfo.rating) * 10))
		return int(float(EventDataManagerEventInfo.rating) * 10)
	
	text  = property(getText)
	value = property(getValue)
	range = 100 # range/value are for the rating progress renderer

	def doSuspend(self, suspended):
		if self.type == self.RATING and not suspended:
			edm_print("[EDM] Converter doSuspend", suspended)
			self.downstream_elements.changed((self.CHANGED_DEFAULT,))

	def checkLoadData(self):
		if EventDataManagerEventInfo.lastEvent != self.event or self.force_changed:
			self.force_changed = False
			edm_print("[EDM] Converter checkLoadData loading data")
			EventDataManagerEventInfo.lastEvent = self.event
			self.eventName = self.event.getEventName().encode('utf-8')
			eventImageName = getEventImageName(self.eventName, self.event.getBeginTime())
			self.loadDataFromDB(eventImageName)
		else:
			edm_print("[EDM] Converter checkLoadData not loading needed")

	def loadDataFromDB(self, eventImageName):
		self.dbApi.c.execute('SELECT title, genre, fsk, season, episode, episodetitle FROM events WHERE image_save = ? LIMIT 4', (eventImageName,))
		datas = self.dbApi.c.fetchall()
		edm_print("[EDM] Converter get data from events", datas)
		if datas is not None:
			EventDataManagerEventInfo.title = EventDataManagerEventInfo.genre = EventDataManagerEventInfo.fsk = EventDataManagerEventInfo.season = EventDataManagerEventInfo.episode = EventDataManagerEventInfo.episodetitle = ""
			for data in datas:
				(title, genre, fsk, season, episode, episodetitle) = data
				if title and not EventDataManagerEventInfo.title:
					EventDataManagerEventInfo.title = title
				if genre and not EventDataManagerEventInfo.genre:
					EventDataManagerEventInfo.genre = genre
				if fsk and not EventDataManagerEventInfo.fsk:
					EventDataManagerEventInfo.fsk = fsk
				if season and not EventDataManagerEventInfo.season:
					EventDataManagerEventInfo.season = season
				if episode and not EventDataManagerEventInfo.episode:
					EventDataManagerEventInfo.episode = episode
				if episodetitle and not EventDataManagerEventInfo.episodetitle:
					EventDataManagerEventInfo.episodetitle = episodetitle
		else:
			EventDataManagerEventInfo.title = EventDataManagerEventInfo.genre = EventDataManagerEventInfo.fsk = EventDataManagerEventInfo.season = EventDataManagerEventInfo.episode = EventDataManagerEventInfo.episodetitle = ""
		
		if not EventDataManagerEventInfo.title:
			EventDataManagerEventInfo.title = self.eventName
		
		eventname = getCleanContentTitle(self.eventName, getLinkedTitle=True)
		contentYear = getContentYearFromEvent(self.event)
		contentType = getContentTypeFromEvent(self.event)
		data = getContentData("rating", eventname, valueNotEmpty=False, event=self.event, year=contentYear, contentType=contentType)
		edm_print("[EDM] Converter get rating from content", data, self.eventName, eventname)

		if data is not None:
			(EventDataManagerEventInfo.rating, contentYear, contentType, eventName) = data
		else:
			EventDataManagerEventInfo.rating = None

	def changed(self, what):
		if edmPluginInstalled:
			self.force_changed = False
			if len(what)>1 and what[1] == "force_changed":
				self.force_changed = True
			if self.type == self.CONDITIONALSHOWHIDE:
				edm_print("[EDM] Converter changed start for ConditionalShowHide")
				self.event = self.source.event
				if self.event:
					self.checkLoadData()
					for x in self.downstream_elements:
						x.visible = EventDataManagerEventInfo.rating is not None
				else:
					for x in self.downstream_elements:
						x.visible = False
			elif self.force_changed: #reload data on force_changed
				edm_print("[EDM] Converter changed after force_changed")
				self.event = self.source.event
				if self.event:
					edm_print("[EDM] Converter changed checkLoadData after force_changed")
					self.checkLoadData()
		Converter.changed(self, what)

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		if self.type == self.CONDITIONALSHOWHIDE:
			downstream.visible = EventDataManagerEventInfo.rating is not None

