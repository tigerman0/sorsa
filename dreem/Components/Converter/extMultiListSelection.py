from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import gPixmapPtr
from enigma import eListbox, eListboxPythonMultiContent

class extMultiListSelection(Converter, object):
	def __init__(self, argstr):
		Converter.__init__(self, argstr)
		self.content = None
		self.element_index = 0
		self.available = -1
		self._visible = 1
		args = argstr.split(',')
		if args[0].isdigit():
			self.element_index = int(args[0])
		if len(args) >= 2 and args[1].isdigit():
			self.available = int(args[1])
			if len(args) >= 3 and args[2].isdigit():
				self._visible = int(args[2])
	#@cached
	def selChanged(self):
		#print 'selChanged'
		if self.source and self.master:
			cur = self.source.current
			if cur and not cur[self.element_index]:
				self.master.visible = 0
			elif cur and self.available >= 0:
				self.selAvailable(cur)
			else:
				self.master.visible = 1
			self.downstream_elements.changed((self.CHANGED_ALL, 0))

	#@cached
	def selAvailable(self, cur):
		#print 'selAvailable'
		if self.source:
			if cur and len(cur):
				if self.available <= len(cur):
					value = 1
					if self._visible == 0 and cur[self.available]:
						#print '0 = 1'
						value = 0
					elif self._visible == 1 and not cur[self.available]:
						#print '1 = 0'
						value = 0
					self.master.visible = value
	
	@cached
	def getCurrent(self):
		if self.master and self.element_index <= len(self.source.list):
			return self.source.list
		return None

	current = property(getCurrent)
	
	@cached
	def getText(self):
		cur = self.source.current
		if cur and self.element_index < len(cur):
			return cur[self.element_index]
		return None

	text = property(getText)
	
	@cached
	def getPixmap(self):
		cur = self.source.current
		if cur and self.element_index < len(cur):
			curindex = cur[self.element_index]
			if isinstance(curindex ,gPixmapPtr):
				return curindex
		return gPixmapPtr()
			
	pixmap = property(getPixmap)
	
	@cached
	def getValue(self):
		cur = self.source.current
		if cur and self.element_index < len(cur):
			curindex = cur[self.element_index]
			if isinstance(curindex ,int):
				return curindex
		return 0

	value = property(getValue)
	range = 100

	def changed(self, what):
		if what[0] == self.CHANGED_ALL and self.master is not None:
			if not self.content:
				self.content = eListboxPythonMultiContent()
			if self.source is not None:
				self.content.setList(self.source.list)
				self.selChanged()
			Converter.changed(self, what)
		elif what[0] == self.CHANGED_DEFAULT:
			if not self.selChanged in self.source.onSelectionChanged:
				self.source.onSelectionChanged.append(self.selChanged)

		
	#def connectDownstream__(self, downstream):
	#	Converter.connectDownstream(self, downstream)
	#	cur = self.source.current
	#	if cur and not cur[self.element_index]:
	#		downstream.visible = 0
	#		#print downstream.visible
	#	elif self.available >= 0:
	#		self.selAvailable(cur)
		
		