# -*- coding: utf-8 -*-
from Renderer import Renderer
from enigma import ePixmap

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, pathExists, SCOPE_CURRENT_SKIN, SCOPE_SKIN

class gMultiPixmap(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.__pixmaps = []

	GUI_WIDGET = ePixmap

	def connect(self, source):
		Renderer.connect(self, source)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if what[0] == self.CHANGED_CLEAR:
			if self.instance:
				self.instance.hide()
		else:
			if self.instance:
				self.__setPixmapNum(self.source.get_value)
				self.instance.show()
	
	def applySkin(self, desktop, screen):
		if self.skinAttributes:
			attribs = [ ]
			for (attrib, value) in self.skinAttributes:
				if attrib == "pixmaps":
					for pixmap in value.split(','):
						if len(pixmap):
							if pixmap[0]=="/":
								self.__pixmaps.append(LoadPixmap(pixmap, desktop))
							else:
								file = resolveFilename(SCOPE_CURRENT_SKIN) + pixmap
								if pathExists(file):
									self.__pixmaps.append(LoadPixmap(file, desktop))
								else:
									file = resolveFilename(SCOPE_SKIN) + pixmap
									if pathExists(file):
										self.__pixmaps.append(LoadPixmap(file, desktop))
				else:
					attribs.append((attrib,value))
			self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, screen)

	def __setPixmapNum(self, x):
		if len(self.__pixmaps) > x:
			self.instance.setPixmap(self.__pixmaps[x])
