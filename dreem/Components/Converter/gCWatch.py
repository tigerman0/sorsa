# -*- coding: utf-8 -*-
#######################################################################
#
#    Converter for Dreambox-Enigma2
#    Coded based @shamann (c)2010
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#######################################################################

from Components.Converter.Converter import Converter
from Components.Element import cached
from time import localtime

class gCWatch(Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		value = type.split(',')
		if value[0] == "sec":
			self.type = 1
		elif value[0] == "min":
			self.type = 2
		elif value[0] == "hour":
			self.type = 3
		self.__size = int(value[1])
		
	@cached
	def getSize(self):
		return self.__size
		
	size = property(getSize)

	@cached
	def getValue(self):
		if self.type == 1:
			time = self.source.time
			if time is None:
				return 0
			t = localtime(time)
			return t.tm_sec
		elif self.type == 2:
			time = self.source.time
			if time is None:
				return 0
			t = localtime(time)
			return t.tm_min
		elif self.type == 3:
			time = self.source.time
			if time is None:
				return 0
			t = localtime(time)
			c = t.tm_hour
			m = t.tm_min
			if c > 11:
				c = c - 12
			return (c * 5) + (m / 12)
		return 0

	value = property(getValue)
