from __future__ import absolute_import
from __future__ import print_function
from enigma import eWidget, eLabel, loadPNG, ePixmap
from Components.Renderer.Renderer import Renderer
from skin import parseColor, applySingleAttribute
from PIL import Image, ImageDraw
from time import time
from math import ceil as math_ceil

class ExtCircleProgress(Renderer):

    def __init__(self):
        Renderer.__init__(self)
        self.__start = 0
        self.__end = 100
        self.__value = 0
        self.width = 100
        self.height = 100
        self.thickness = 25
        self.backgroundColor = parseColor('#666666').argb()
        self.valueColor = parseColor('#0385b5').argb()
        self.ptr = None
        self.image = None
        self.text = None
        self.itemName = ""
        self.circleType = "showValue" # or "showRest", "showLast", "showLastRest"
        self.textType = "showValue"   # or "showPercent"
        self.circleStartPosition = "bottom" # or "right", "left", "top"
        self.circleFillDirection = "right"  # or "left"
        self.applySkinRunning = False
    
    GUI_WIDGET = eWidget

    def GUIcreate(self, parent):
        self.instance = eWidget(parent)
        self.image = ePixmap(self.instance)
        self.text = eLabel(self.instance)
        self.createCircle()

    def GUIdelete(self):
        self.image = None
        self.text = None
        self.instance = None

    def applyAllAttributes(self, guiObject, desktop, attributes, scale):
        for attrib, value in attributes:
            try:
                applySingleAttribute(guiObject, desktop, attrib, value, scale)
            except Exception as ex:
                pass
        return True

    def applySkin(self, desktop, parent):
        print("[CircleProgress] applySkin")
        attribs = []
        textattribs = []
        imageattribs = []
        if self.skinAttributes:
            for attrib, value in self.skinAttributes:
                if attrib == 'size':
                    attribs.append((attrib, value))
                    imageattribs.append((attrib, value))
                    textattribs.append((attrib, value))
                    self.width = int(value.split(',')[0])
                    self.height = int(value.split(',')[1])
                elif attrib == 'foregroundColor':
                    textattribs.append((attrib, value))
                elif attrib == 'backgroundColor':
                    attribs.append((attrib, value))
                    textattribs.append((attrib, value))
                elif attrib == 'shadowBlur':
                    textattribs.append((attrib, value))
                elif attrib == 'shadowColor':
                    textattribs.append((attrib, value))                                      
                elif attrib == 'circlebackgroundColor':
                    self.backgroundColor = parseColor(value).argb()
                elif attrib == 'circlevalueColor':
                    self.valueColor = parseColor(value).argb()
                elif attrib == 'borderthickness':
                    self.thickness = int(value)
                elif attrib == 'font':
                    textattribs.append((attrib, value))
                elif attrib == 'itemname':
                    self.itemName = str(value)
                elif attrib == 'circleType':
                    self.circleType = str(value)
                elif attrib == 'circleFillDirection':
                    self.circleFillDirection = str(value)
                elif attrib == 'circleStartPosition':
                    self.circleStartPosition = str(value)
                elif attrib == 'textType':
                    self.textType = str(value)
                elif attrib == 'valign':
                    textattribs.append((attrib, value))
                elif attrib == 'halign':
                    textattribs.append((attrib, value))
                else:
                    attribs.append((attrib, value))
            self.skinAttributes = attribs
        imageattribs.append(('position', '0,0')) #image-position in the main-widget
        textattribs.append(('position', '0,0'))  #text-position in the main-widget
        textattribs.append(('transparent', '1')) #set transparent for text-label
        self.applyAllAttributes(self.text, desktop, textattribs, parent.scale)
        self.applyAllAttributes(self.image, desktop, imageattribs, parent.scale)
        self.applyAllAttributes(self.instance, desktop, attribs, parent.scale)
        self.applySkinRunning=True
        return True

    def changed(self, what):
        print("[CircleProgress] changed", what)
        if what[0] == self.CHANGED_CLEAR:
            (self.value, self.range) = (0, (0, 1))
        else:
            if hasattr(self.source, "range"):
                range = self.source.range or 100
            else:
                range = 100
            if hasattr(self.source, "value"):
                value = self.source.value
            else:
                value = 0
            if value is None:
                value = 0
            (self.value, self.range) = (value, (0, range))

    def setRange(self, range):
        print("[CircleProgress] setRange", range)
        (self.__start, self.__end) = range
        self.createCircle()

    def getRange(self):
        return (self.__start, self.__end)

    def createCircle(self):
        try:
            print("[CircleProgress] createCircle")
            
            if self.image is None:
                print("CircleProgress createCircle return because image is None")
                return
            if not self.applySkinRunning:
                print("CircleProgress createCircle return because applySkin is not running")
                return
            
            if self.circleType in ("showLast", "showLastRest"):
                if hasattr(self.source, "source") and self.source.source:
                    source = self.source.source # use with converter
                else:
                    source = self.source # use without converter
                if source.service is None:
                    print("CircleProgress createCircle return because service is None")
                    return
                cuts = CutList(source.service.getPath() + ".cuts")
                last = cuts.getCutListLast()
                info = source.info
                durationtime = info.getLength(source.service)
                if durationtime < 0 and hasattr(source, "event") and hasattr(source.event, "getDuration"):
                    durationtime = source.event.getDuration()
                if last > 0:
                    progress = int( math_ceil ( float(last) / float(durationtime) * 100.0 ) )
                    self.value = progress
                else:
                    self.value = 0
                
                if self.textType == "showValue":
                    if self.circleType == "showLastRest":
                        circleText = "+%d" % ((durationtime - last) // 60)
                    else:
                        circleText = "%d" % (last // 60)
                else:
                    #showPercent
                    if self.circleType == "showLastRest":
                        circleText = "%d" % (100 - self.value) + "%"
                    else:
                        circleText = "%d" % self.value + "%" 
                self.text.setText(circleText)
            
            elif hasattr(self.source, "source") and hasattr(self.source.source, "event") and hasattr(self.source.source.event, "getBeginTime"):
                #show circleText with event time
                circleText = self.getRemaningTime(self.source.source.event)
                print("[CircleProgress] set remaining time", circleText)
                self.text.setText(circleText)
            else:
                #show circleText with normal value
                circleValue = self.value
                if self.circleType == "showRest":
                    circleValue = self.__end - self.value
                if self.textType == "showPercent":
                    circleText = "%s" % int(circleValue / float(self.__end) * 100) + "%"
                else:
                    circleText = "%s" % circleValue
                self.text.setText(circleText)
            
            if self.itemName:
                filename = "/tmp/circleprogress_%s.png" % self.itemName
            else:
                filename = "/tmp/circleprogress.png"
            
            im = Image.new('RGBA', (self.width * 2, self.height * 2), (0, 0, 0, 0))
            dr = ImageDraw.Draw(im)
            circleStartPosition = self.getCircleStartPosition()
            dr.ellipse((1,
             1,
             self.width * 2 - 2,
             self.height * 2 - 2), fill=self.getRGBAfromARGBint(self.backgroundColor))
            if self.circleType in ("showValue", "showLast"):
                #show current value circle
                if self.circleFillDirection == "right": # default
                    dr.pieslice((1,
                     1,
                     self.width * 2 - 2,
                     self.height * 2 - 2), circleStartPosition, circleStartPosition + int(float(float(360) / float(self.__end)) * float(self.value)), fill=self.getRGBAfromARGBint(self.valueColor))
                else:
                    dr.pieslice((1,
                     1,
                     self.width * 2 - 2,
                     self.height * 2 - 2), circleStartPosition - int(float(float(360) / float(self.__end)) * float(self.value)), circleStartPosition, fill=self.getRGBAfromARGBint(self.valueColor))
            else:
                #show rest value circle
                if self.circleFillDirection == "right": # default
                    dr.pieslice((1,
                     1,
                     self.width * 2 - 2,
                     self.height * 2 - 2), circleStartPosition + int(float(float(360) / float(self.__end)) * float(self.value)), circleStartPosition, fill=self.getRGBAfromARGBint(self.valueColor))
                else:
                    dr.pieslice((1,
                     1,
                     self.width * 2 - 2,
                     self.height * 2 - 2), circleStartPosition, circleStartPosition + (360 - int(float(float(360) / float(self.__end)) * float(self.value))), fill=self.getRGBAfromARGBint(self.valueColor))
            dr.ellipse((self.thickness * 2,
             self.thickness * 2,
             self.width * 2 - 2 - self.thickness * 2,
             self.height * 2 - 2 - self.thickness * 2), fill=(0, 0, 0, 0))
            im.thumbnail((self.width, self.height), Image.ANTIALIAS)
            im.save(filename)
            self.ptr = loadPNG(filename)
            self.image.setPixmap(self.ptr)
        except:
            print("[CircleProgress] Error on createCircle")
            import traceback, sys
            traceback.print_exc()

    def getRGBAfromARGBint(self, RGBint):
            blue =  RGBint & 255
            green = (RGBint >> 8) & 255
            red =   (RGBint >> 16) & 255
            alpha = abs(((RGBint >> 24) & 255) - 255)
            print("[CircleProgress] getRGBA", (red, green, blue, alpha))
            return (red, green, blue, alpha)
    
    def getRemaningTime(self, event):
        now = int(time())
        start_time = event.getBeginTime()
        duration = event.getDuration()
        end_time = start_time + duration
        if start_time <= now <= end_time:
            #current event
            if self.textType == "showValue":
                return "+%d" % ((end_time - now) // 60)
            else:
                #showPercent
                if self.circleType == "showValue":
                    return "%d" % ((now - start_time) / float(duration) *100) + "%"
                else:
                    #showRest
                    return "%d" % ((end_time - now) / float(duration) *100) + "%"
        else:
            #not a current event
            if self.textType == "showValue":
                return "+%d" % (duration // 60)
            else:
                #showPercent
                if self.circleType == "showValue":
                    return "0%"
                else:
                    #showRest
                    return "100%"
    
    def getCircleStartPosition(self):
        if self.circleStartPosition == "bottom":
            return 90
        elif self.circleStartPosition == "right":
            return 0
        elif self.circleStartPosition == "left":
            return 180
        elif self.circleStartPosition == "top":
            return 270
    
    def setValue(self, value):
        print("[CircleProgress] setValu", value)
        self.__value = value

    def getValue(self):
        return self.__value

    value = property(getValue, setValue)
    range = property(getRange, setRange)


import struct
import os
from bisect import insort

#reduced CutListClass from Enhanced Movie Center (EMC)

class CutList():

	CUT_TYPE_LAST = 3
	INSORT_SCOPE  = 45000  # 0.5 seconds * 90 * 1000

	def __init__(self, path=None):
		self.cut_file = path
		self.cut_mtime = 0
		self.cut_list = []
		
		self.__readCutFile(self.cut_file)
	
	def __insort(self, pts, what):
		if self.cut_list:
			for (clpts, clwhat) in self.cut_list[:]:
				if clwhat == what:
					if clpts-self.INSORT_SCOPE < pts < clpts+self.INSORT_SCOPE:
						# Found a conflicting entry, replace it to avoid doubles and short jumps
						self.cut_list.remove( (clpts, clwhat) )
			insort(self.cut_list, (pts, what))
		else:
			insort(self.cut_list, (pts, what))
	
	def __secondsToPts(self, seconds):
		return seconds * 90 * 1000
	
	def __ptsToSeconds(self, pts):
		# Cut files are using the presentation time stamp time format
		# pts has a resolution of 90kHz
		return pts / 90 / 1000
	
	def getCutListLast(self): # Wrapper in seconds
		return self.__ptsToSeconds( self.__getCutListLast() )

	def __getCutListLast(self): # Internal from cutlist in pts
		if self.cut_list:
			for (pts, what) in self.cut_list:
				if what == self.CUT_TYPE_LAST:
					return pts
		return 0
	
	def __readCutFile(self, path, update=False):
		data = ""
		if path and os.path.exists(path):
			mtime = os.path.getmtime(path)
			if self.cut_mtime == mtime:
				# File has not changed
				pass

			else:
				# New path or file has changed
				self.cut_mtime = mtime

				if not update:
					# No update clear all
					self.cut_list = []

				# Read data from file
				f = None
				try:
					f = open(path, 'rb')
					data = f.read()
				except Exception, e:
					print("[CUTS] Exception in __readCutFile: " + str(e))
				finally:
					if f is not None:
						f.close()

				# Parse and unpack data
				if data:
					pos = 0
					while pos+12 <= len(data):
						# Unpack
						(pts, what) = struct.unpack('>QI', data[pos:pos+12])
						self.__insort(long(pts), what)
						# Next cut_list entry
						pos += 12
		else:
			# No path or no file clear all
			self.cut_list = []

