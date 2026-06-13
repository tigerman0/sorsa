# coders by Vlamo 2012
# mod.zombi & Sven H 2025-03-23
# LN - add getPathInfo
from Components.Converter.Converter import Converter
from Components.config import config
from Components.Element import cached
from Components.Converter.Poll import Poll
from os import popen, statvfs, path as os_path
from enigma import eTimer, iServiceInformation, iPlayableServicePtr, iPlayableService

SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]


class ExtDiskSpaceInfo(Poll, Converter):
	LOADAVG = 0
	MEMINFO = 1
	MEMFREE = 2
	USBINFO = 3
	HDDINFO = 4
	FLASHINFO = 5
	DATAINFO = 6
	MOVIEDIR = 7
	RLVERSION = 8
	FLASH0 = 9
	FLASH1 = 10
	FLASH2 = 11
	FLASH3 = 12
	FLASH4 = 13
	SDCARD = 14
	SERVICEREFERENCE = 15
	SKINVERSION = 16

	def __init__(self, type):  # @ReservedAssignment
		Converter.__init__(self, type)
		Poll.__init__(self)

		type = type.split(',')  # @ReservedAssignment
		self.shortFormat = "Short" in type
		self.fullFormat = "Full"  in type
		if "LoadAvg" in type:
			self.type = self.LOADAVG
		elif "MemInfo" in type:
			self.type = self.MEMINFO
		elif "MemFree" in type:
			self.type = self.MEMFREE
		elif "UsbInfo" in type:
			self.type = self.USBINFO
		elif "HddInfo" in type:
			self.type = self.HDDINFO
		elif "DataInfo" in type:
			self.type = self.DATAINFO
		elif "MovieDir" in type:
			self.type = self.MOVIEDIR
		elif "RescueLoaderVersion" in type:
			self.type = self.RLVERSION
		elif "Flash0" in type:
			self.type = self.FLASH0
		elif "Flash1" in type:
			self.type = self.FLASH1
		elif "Flash2" in type:
			self.type = self.FLASH2
		elif "Flash3" in type:
			self.type = self.FLASH3
		elif "Flash4" in type:
			self.type = self.FLASH4
		elif "Sdcard" in type:
			self.type = self.SDCARD
		elif "SkinVersion" in type:
			self.type = self.SKINVERSION
			self.skinpackagename = None
			self.showVersionstext = True
			if len(type)>1:
				self.skinpackagename = type[1]
			if "showNoVersionstext" in type:
				self.showVersionstext = False
		elif "ServiceReference" in type:
			self.type = self.SERVICEREFERENCE
		else:
			self.type = self.FLASHINFO

		if self.type in (self.FLASHINFO, self.FLASH0, self.FLASH1, self.FLASH2, self.FLASH3, self.FLASH4, self.SDCARD, self.DATAINFO, self.HDDINFO, self.USBINFO):
			self.poll_interval = 5000
			self.poll_enabled = True
		elif self.type in (self.RLVERSION,):
			self.poll_interval = 10000
			self.poll_enabled = True
			self.dataString =""
			self.startTimer = eTimer()
		elif self.type in (self.SERVICEREFERENCE,):
			self.poll_interval = 60*60*1000
			self.poll_enabled = True
		else:
			self.poll_interval = 1000
			self.poll_enabled = True

		self.path = ""

	def doSuspend(self, suspended):
		if suspended:
			self.poll_enabled = False
		else:
			if self.type in (self.RLVERSION, self.SKINVERSION): return # don't reload RL-Version
			self.downstream_elements.changed((self.CHANGED_POLL,))
			self.poll_enabled = True

	@cached
	def getText(self):
		text = "N/A"
		if self.type == self.LOADAVG:
			text = self.getLoadAvg()
		elif self.type == self.RLVERSION:
			self.startTimer_conn = self.startTimer.timeout.connect(self.getDateStringFomRecovery)
			self.startTimer.start(1000,True)
			text = "Rescue Loader: loading info..."
		elif self.type == self.SKINVERSION:
			text == "unknown"
			if self.skinpackagename:
				cmdResult = popen("dpkg -s %s | grep Version" % self.skinpackagename).readline()
				if "Version:" in cmdResult:
					text = cmdResult.replace("Version:","").strip()
				if self.showVersionstext:
					text = "Version: %s" % text
			print("[ExtDiskSpaceInfo] read Skin version", text)
		elif self.type == self.SERVICEREFERENCE:
			return self.getServiceInfoValue(self.source.service, iServiceInformation.sServiceref)
		else:
			entry = {
					self.MEMINFO:  ("Mem","Ram"),
					self.MEMFREE:  ("Mem","Ram"),
					self.USBINFO:   ("/media/usb", "USB"),
					self.HDDINFO:   ("/media/hdd", "HDD"),
					self.FLASHINFO: ("/", "Flash"),
					self.FLASH0: ("/dev/mmcblk0p5", "Flash0"),
					self.FLASH1: ("/dev/mmcblk0p6", "Flash1"),
					self.FLASH2: ("/dev/mmcblk0p7", "Flash2"),
					self.FLASH3: ("/dev/mmcblk0p8", "Flash3"),
					self.FLASH4: ("/dev/mmcblk0p9", "Flash4"),
					self.SDCARD: ("/dev/mmcblk1p2", "SD Card"),
					self.DATAINFO: ("/data", "Data"),
					self.MOVIEDIR:   (config.movielist.last_videodir.value, ""),
				}[self.type]
			if self.type in (self.USBINFO, self.HDDINFO, self.FLASHINFO, self.DATAINFO):
				list = self.getDiskInfo(entry[0])  # @ReservedAssignment
			elif self.type in (self.FLASH0, self.FLASH1, self.FLASH2, self.FLASH3, self.FLASH4):
				list = self.getFlashInfo(entry[0])  # @ReservedAssignment
			elif self.type in (self.SDCARD, ):
				list = self.getSdcardInfo(entry[0])  # @ReservedAssignment
			elif self.type == self.MOVIEDIR:
				list = self.getPathInfo()  # @ReservedAssignment
			else:
				list = self.getMemInfo(entry[0])  # @ReservedAssignment
			if list[0] == 0:
				if config.osd.language.value == "de_DE":
					if self.type in (self.FLASH0, self.FLASH1, self.FLASH2, self.FLASH3, self.FLASH4, self.SDCARD):
						text = "%s nicht vorhanden" % (entry[1])
					else:
						text = "%s nicht gemountet" % (entry[1])
				else:
					text = "%s not Available" % (entry[1])
			elif self.shortFormat:
				if config.osd.language.value == "de_DE":
					text = "%s Gesamt: %s Belegt: %s%%" % (entry[1], self.getSizeStr(list[0]), list[3])
				else:
					text = "%s Total: %s Used: %s%%" % (entry[1], self.getSizeStr(list[0]), list[3])
			elif self.fullFormat:
				if config.osd.language.value == "de_DE":
					text = "%s Gesamt: %s Frei: %s Belegt: %s (%s%%)" % (entry[1], self.getSizeStr(list[0]), self.getSizeStr(list[2]), self.getSizeStr(list[1]), list[3])
				else:
					text = "%s Total: %s Free: %s Available: %s (%s%%)" % (entry[1], self.getSizeStr(list[0]), self.getSizeStr(list[2]), self.getSizeStr(list[1]), list[3])
			else:
				if config.osd.language.value == "de_DE":
					text = "%s Gesamt: %s Belegt: %s Frei: %s" % (entry[1], self.getSizeStr(list[0]), self.getSizeStr(list[1]), self.getSizeStr(list[2]))
				else:
					text = "%s Total: %s Used: %s Available: %s" % (entry[1], self.getSizeStr(list[0]), self.getSizeStr(list[1]), self.getSizeStr(list[2]))
		if self.type in (self.FLASH0, self.FLASH1, self.FLASH2, self.FLASH3, self.FLASH4, self.SDCARD):
			if list[4] == 1:
				text = "*" + text #show device as booted
		return text

	@cached
	def getValue(self):
		result = 0
		if self.type in (self.MEMINFO,self.MEMFREE):
			entry = {self.MEMINFO: "Mem", self.MEMFREE: "Mem"}[self.type]
			result = self.getMemInfo(entry)[3]
		elif self.type in (self.USBINFO, self.HDDINFO, self.FLASHINFO, self.DATAINFO):
			path = {self.USBINFO: "/media/usb", self.HDDINFO: "/media/hdd", self.FLASHINFO: "/", self.DATAINFO: "/data"}[self.type]
			result = self.getDiskInfo(path)[3]
		elif self.type in (self.FLASH0, self.FLASH1, self.FLASH2, self.FLASH3, self.FLASH4):
			path = {self.FLASH0: "/dev/mmcblk0p5", self.FLASH1: "/dev/mmcblk0p6", self.FLASH2: "/dev/mmcblk0p7", self.FLASH3: "/dev/mmcblk0p8", self.FLASH4: "/dev/mmcblk0p9", }[self.type]
			result = self.getFlashInfo(path)[3]
		elif self.type in (self.SDCARD, ):
			path = {self.SDCARD: "/dev/mmcblk1p2", }[self.type]
			result = self.getSdcardInfo(path)[3]
		elif self.type == self.MOVIEDIR:
			result = self.getPathInfo()[3]
		return result

	text = property(getText)
	value = property(getValue)
	range = 100

	def changed(self, *args, **kwargs):
		if self.type == self.SERVICEREFERENCE:
			if args[0] != self.CHANGED_SPECIFIC or args[1] in (iPlayableService.evStart,):
				Converter.changed(self, *args, **kwargs)
			return
		else:
			if len(args[0])>1 and args[0][0] == self.CHANGED_SPECIFIC:
				return #don't reload on SPECIFIC event
			Converter.changed(self, *args, **kwargs)

	def getLoadAvg(self):
		textvalue = "No info"
		info = "0"
		try:
			out_line = popen("cat /proc/loadavg").readline()
			info = "load average: " + out_line[:15] + ' (1,5,15min)'
			textvalue = info
		except:
			pass
		return textvalue

	def getMemInfo(self, value):
		result = [0, 0, 0, 0]  # (size, used, avail, use%)
		try:
			check = 0
			fd = open("/proc/meminfo")
			for line in fd:
				if value + "Total" in line:
					check += 1
					result[0] = int(line.split()[1]) * 1024  # size
				elif value + "Free" in line:
					check += 1
					result[2] = int(line.split()[1]) * 1024  # avail
				if check > 1:
					if result[0] > 0:
						result[1] = result[0] - result[2]  # used
						result[3] = result[1] * 100 / result[0]  # use%
					break
			fd.close()
		except:
			pass
		return result

	def getDiskInfo(self, path):
		def isMountPoint():
			try:
				fd = open('/proc/mounts', 'r')
				for line in fd:
					l = line.split()
					if len(l) > 1 and l[1] == path:
						return True
				fd.close()
			except:
				return None
			return False

		result = [0, 0, 0, 0]  # (size, used, avail, use%)
		if isMountPoint():
			try:
				st = statvfs(path)
			except:
				st = None
			if not st is None and not 0 in (st.f_bsize, st.f_blocks):
				result[0] = st.f_bsize * st.f_blocks  # size
				result[2] = st.f_bsize * st.f_bavail  # avail
				result[1] = result[0] - result[2]  # used
				result[3] = result[1] * 100 / result[0]  # use%
		return result

	def getFlashInfo(self, path):
		cmdResult = popen("lsblk -ln %s" % path).readline().strip().split()
		isBootet = False
		if len(cmdResult)>0:
			if cmdResult[-1].startswith("/"): #use mount to check size data
				path = cmdResult[-1]
				isMounted = True
				if path == "/":
					isBootet = True
			else: #mount to check size data
				flashnumber = int(path[-1]) -5
				cmd = "mkdir -p /tmp/ExtDiskSpaceInfo_flash%s && mount -t ext4 --read-only %s /tmp/ExtDiskSpaceInfo_flash%s" % (flashnumber, path, flashnumber)
				cmdResult = popen(cmd).readline().strip()
				path = "/tmp/ExtDiskSpaceInfo_flash%s" % flashnumber
				self.path = path
				isMounted = True
		else:
			isMounted = False

		result = [0, 0, 0, 0, 0]  # (size, used, avail, use%, booted)
		if isMounted:
			try:
				st = statvfs(path)
			except:
				st = None
			if not st is None and not 0 in (st.f_bsize, st.f_blocks):
				result[0] = st.f_bsize * st.f_blocks  # size
				result[2] = st.f_bsize * st.f_bavail  # avail
				result[1] = result[0] - result[2]  # used
				result[3] = result[1] * 100 / result[0]  # use%
				if isBootet:
					result[4] = 1 # booted
		return result

	def getSdcardInfo(self, path):
		cmdResult = popen("lsblk -ln %s" % path).readline().strip().split()
		isBootet = False
		if len(cmdResult)>0:
			if cmdResult[-1].startswith("/"): #use mount to check size data
				path = cmdResult[-1]
				isMounted = True
				if path == "/":
					isBootet = True
			else: #mount to check size data
				cmd = "mkdir -p /tmp/ExtDiskSpaceInfo_sdcard && mount -t ext4 --read-only %s /tmp/ExtDiskSpaceInfo_sdcard" % (path, )
				cmdResult = popen(cmd).readline().strip()
				path = "/tmp/ExtDiskSpaceInfo_sdcard"
				self.path = path
				isMounted = True
		else:
			isMounted = False

		result = [0, 0, 0, 0, 0]  # (size, used, avail, use%, booted)
		if isMounted:
			try:
				st = statvfs(path)
			except:
				st = None
			if not st is None and not 0 in (st.f_bsize, st.f_blocks):
				result[0] = st.f_bsize * st.f_blocks  # size
				result[2] = st.f_bsize * st.f_bavail  # avail
				result[1] = result[0] - result[2]  # used
				result[3] = result[1] * 100 / result[0]  # use%
				if isBootet:
					result[4] = 1 # booted
		return result

	def getPathInfo(self):
		result = [0, 0, 0, 0]  # (size, used, avail, use%)
		try:
			if os_path.exists(config.movielist.last_videodir.value):
				stat = statvfs(config.movielist.last_videodir.value)
				result[0] = stat.f_bsize * stat.f_blocks  # size
				result[2] = (stat.f_bavail if stat.f_bavail != 0 else stat.f_bfree) * stat.f_bsize  # available
				result[1] = stat.f_bsize * (stat.f_blocks - stat.f_bfree)  # used
				result[3] = result[1] * 100 / result[0]  # used%
			return result
		except:
			return result

	def getSizeStr(self, value, u=0):
		fractal = 0
		if value >= 1024:
			#fmt = "%(size)u.%(frac)d %(unit)s"
			fmt = "%(size).1f %(unit)s"
			while (value >= 1024) and (u < len(SIZE_UNITS)):
				#(value, mod) = divmod(value, 1024)
				#fractal = mod * 10 / 1024
				value = value / 1024.0
				u += 1
		else:
			fmt = "%(size)u %(unit)s"
		return fmt % {"size": value, "frac": fractal, "unit": SIZE_UNITS[u]}

	def getDateStringFomRecovery(self):
		if os_path.exists("/dev/recovery"):
			with open("/dev/recovery", 'r') as f:
				for line in f:
					result = line.find("dreambox-rescue-image")
					if result > 0:
						result2 = line.find(".rootfs.cpio")
						cmdResult = line[result:result2]
						break

			dateString = ""
			if "-" in cmdResult:
				dateString = cmdResult.split("-")[-1]

			if dateString:
				text = "Rescue Loader: #%s (%s)" % (self.getVersionFromDate(dateString),dateString)
			else:
				text = "Rescue Loader: #unknown"
		else:
			text = "Rescue Loader: #unknown"

		for x in self.downstream_elements:
			if hasattr(x.instance, "setText"):
				x.instance.setText(text)
		self.poll_enabled = False

	def getServiceInfoValue(self, service, what):
		if isinstance(service, iPlayableServicePtr):
			info = service and service.info()
			ref = None
		else: # reference
			info = service and self.source.info
			ref = service
		if info is None:
			return ""
		v = ref and info.getInfo(ref, what) or info.getInfo(what)
		if v != iServiceInformation.resIsString:
			ret = "N/A" if not ref or self.type != self.SERVICEREFERENCE else ref.toString()
		elif ref:
			ret = info.getInfoString(ref, what) or self.type == self.SERVICEREFERENCE and ref.toString()
		else:
			ret = info.getInfoString(what)
		return ret

	def getVersionFromDate(self, dateString=""):

		DATE_VERSION_MAP = {
		"20241224"  : "124", "20241220"  : "124",
		"20240901"  : "117",
		"20240808"  : "116", "20240530"  : "115", "20240421"  : "114", "20240310"  : "113Y",
		"20240309"  : "113X", "20240226"  : "113L", "20240224"  : "113K", "20240217"  : "113H",
		"20240216"  : "113G", "20240203"  : "113E", "20240202"  : "113D", "20240131"  : "113C",
		"20231230"  : "113B", "20231226"  : "113A", "20231224"  : "113",
		"20231212"  : "112F", "20231208"  : "112E", "20231203"  : "112D", "20231202"  : "112A",
		"20231201"  : "112",
		"20231126"  : "111Z", "20231125"  : "111Y", "20231124"  : "111X", "20231121"  : "111D",
		"20231117"  : "111C", "20231114"  : "111B", "20231112"  : "111A", "20231111"  : "111",
		"20231106"  : "110",
		"20231105"  : "109",
		"20231103"  : "108",
		"20231101"  : "107",
		"20230508"  : "106",
		"20230421"  : "105",
		"20211029"  : "104", # last #104
		#... all other #104
		"20200513"  : "104", # first #104
		#... all other #103
		"20190510"  : "103", # first #103
		""  : "",
		}

		dateString = dateString[:8]
		version = DATE_VERSION_MAP.get(dateString, "unknown")

		if version == "unknown" and dateString > "20241224":
			cmdResult = popen("dpkg -s rescue-image | grep Version").readline()
			if "Version:" in cmdResult:
				version = cmdResult.replace("Version:","").strip()
			else:
				version = ">124"
			print("[ExtDiskSpaceInfo] read RL version from dpkg")
		elif version == "unknown" and dateString > "20230000" and dateString < "20230508":
			version = "105"
		elif version == "unknown" and dateString > "20200513" and dateString < "20211029":
			version = "104"
		elif version == "unknown" and dateString > "20190510" and dateString < "20200513":
			version = "103"
		elif version == "unknown" and dateString < "20190510":
			version = "<=103"

		print("[ExtDiskSpaceInfo] RL version: %s" % version)
		return version

	def destroy(self):
		Converter.destroy(self)
		if self.path.startswith("/tmp/ExtDiskSpaceInfo_flash") or self.path.startswith("/tmp/ExtDiskSpaceInfo_sdcard"):
			#unmount flash or sc card partition
			cmdResult = popen("umount %s" % self.path).readline().strip()

