#######################################################################
#
#  Channel Number Renderer for Dreambox/Enigma-2
#  Coded by Vali (c)2010 - modify by Sven H 13.03.2024
#  Support: https://www.i-have-a-dreambox.com/
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#######################################################################

from Components.VariableText import VariableText
from enigma import eLabel, eServiceCenter
from Components.Renderer.Renderer import Renderer
from Screens.InfoBar import InfoBar

MYCHANSEL = InfoBar.instance.servicelist

class ExtChNumber(Renderer, VariableText):

	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		
		# default type-value: "chNumber"
		# allowed type-attribute-values: 
		# "chNumber", "chNumberWithDot", "chNumberName", "chNumberNameWithDot"
		# example for type-attribute-value: type="chNumberWithDot"
		
		self.format = "$number" # default format-value
		# example for allowed format-attribute-value: format="$number. $name"
	
	GUI_WIDGET = eLabel
	
	def changed(self, what):
		change = False
		if not self.suspended:
			#change chNumber if chNumber-widget is shown
			change = True
		elif what and what[0] == self.CHANGED_SPECIFIC and what[1] == 0:
			#change chNumber after iPlayableService.evStart in CurrentService if chNumber-widget is not shown
			change = True
		if change:
			service = self.source.service
			info = service and service.info()
			if info is None:
				self.text = " "
				return
			markersOffset = 0
			myRoot = MYCHANSEL.getRoot()
			mySrv = MYCHANSEL.servicelist.getCurrent()
			chx = MYCHANSEL.servicelist.l.lookupService(mySrv)
			if not MYCHANSEL.inBouquet():
				pass
			else:
				serviceHandler = eServiceCenter.getInstance()
				mySSS = serviceHandler.list(myRoot)
				SRVList = mySSS and mySSS.getContent("SN", True)
				for i in range(len(SRVList)):
					if chx == i:
						break
					testlinet = SRVList[i]
					testline = testlinet[0].split(":")
					if testline[1] == "64":
						markersOffset = markersOffset + 1
			chx = (chx - markersOffset) + 1
			rx = MYCHANSEL.getBouquetNumOffset(myRoot)
			sNumber = str(chx + rx)
			
			if "$name" in self.format:
				sName = info and info.getName()
				sName = sName.replace('\xc2\x86', '').replace('\xc2\x87', '')
				self.text = self.format.replace("$number",sNumber).replace("$name", sName)
			else:
				self.text = self.format.replace("$number",sNumber)
	
	def applySkin(self, desktop, parent):
		attribs = [ ]
		for (attrib, value) in self.skinAttributes:
			if attrib == "type":
				type_format = {
					"chNumberWithDot":     "$number.", 
					"chNumberName":        "$number $name", 
					"chNumberNameWithDot": "$number. $name"
					}
				self.format = type_format.get(value, "$number") # with fallback to "$number"
			elif attrib == "format":
				self.format = value
			else:
				attribs.append((attrib,value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

