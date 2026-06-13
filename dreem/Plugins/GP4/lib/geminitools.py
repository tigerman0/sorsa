# -*- coding: utf-8 -*-
import socket, struct, os, time

from ctypes import c_char
from fcntl import ioctl
from ioctl.linux import IOC
O_CLOEXEC = 0o2000000

def AudioDevices():
	alist=[]
	from Plugins.GP4.lib.libgeminiplayer import Cplayer
	__libbgplayer = Cplayer()
	for x in __libbgplayer.getAlsaDevices():
		name=x[2]
		if name=="SPDIF-B-dummy-alsaPORT-HDMI dummy-0":
			name="One-HDMI"
		elif name=="SPDIF-dummy-alsaPORT-spdif dummy-1":
			name="One-SPDIF"
		elif name=="TDM-B-dummy-alsaPORT-btpcm multicodec-2":
			name="One-Bluetooth"
		elif name=="BCM PCM":
			name="HDMI/SPDIF"
		typ="Card"
		if x[3]==0:
			typ="Virtual"
		alist.append({'addr':x[0], 'devname': x[1], 'name': name, 'type': typ})
	del __libbgplayer
	return alist

def getNetworkdevices():
	devlist=[]
	IFF_UP = 0x1
	IFF_BROADCAST = 0x2
	IFF_DEBUG = 0x4
	IFF_LOOPBACK = 0x8
	IFF_POINTOPOINT = 0x10
	IFF_NOTRAILERS = 0x20
	IFF_RUNNING = 0x40
	IFF_NOARP = 0x80
	IFF_PROMISC = 0x100
	IFF_ALLMULTI = 0x200
	IFF_MASTER = 0x400
	IFF_SLAVE = 0x800
	IFF_MULTICAST = 0x1000
	IFF_PORTSEL = 0x2000
	IFF_AUTOMEDIA = 0x4000
	IFF_DYNAMIC = 0x8000

	
	for dev in sorted(os.listdir("/sys/class/net/")):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			# SIOCGIFADDR
			#print "###########"
			#print dev
			flags=0
			ip = socket.inet_ntoa(ioctl(s.fileno(),0x8915, struct.pack('256s', dev[:15]))[20:24])
			mac = ioctl(s.fileno(), 0x8927,  struct.pack('256s', dev[:15]))[18:24]
			if mac:
				mac = ':'.join(['%02x' % ord(char) for char in mac])
				flags = ioctl(s.fileno(), 0x8913, struct.pack("18s",dev))
				if flags:
					flags = struct.unpack("16sh",flags)[1]
				
			if mac and flags:
				flagstr=""
				if (flags & IFF_LOOPBACK):
					continue
						
				flagstr += "UP " if (flags & IFF_UP) else ""
				flagstr += "BROADCAST " if (flags & IFF_BROADCAST) else ""
				flagstr += "POINTOPOINT " if (flags & IFF_POINTOPOINT) else ""
				flagstr += "RUNNING " if (flags & IFF_RUNNING) else ""
				flagstr += "PROMISC " if (flags & IFF_PROMISC) else ""
				flagstr += "ALLMULTI " if (flags & IFF_ALLMULTI) else ""
				flagstr += "MULTICAST " if (flags & IFF_MULTICAST) else ""
				flagstr += "MASTER " if (flags & IFF_MASTER) else ""
				flagstr += "SLAVE" if (flags & IFF_SLAVE) else ""
					
				entry={}
				entry["dev"]=dev
				entry["mac"]=mac
				entry["ip"]=ip
				entry['flags']=flagstr
				devlist.append(entry)
		except:
			pass
	return devlist

def getInputDevices():
	INT = "i"
	INT2 = "ii"
	INT5 = "iiiii"
	SHORT = "h"
	USHORT = "H"
	SHORT4 = "hhhh"
	
	def EVIOCGNAME(length=255):
		return IOC('r', 'E', 0x06, length)
	
	def EVIOCGBIT(evtype,length=255):
		return IOC('r', 69, 0x20+evtype, length)

	devlist=[]
	for evdev in sorted(os.listdir("/dev/input")):
		if not evdev.startswith("event"):
			continue

		try:
			fd = os.open("/dev/input/%s" % evdev, os.O_RDONLY | O_CLOEXEC)
		except:
			continue

		buf = (c_char * 256)()
		try:
			size = ioctl(fd, EVIOCGNAME(), buf, True)
			caps = ioctl(fd, EVIOCGBIT(0), '\x00\x00\x00\x00')
			if size <= 0:
				continue
			
			entry={"dev":"/dev/input/"+evdev}
			entry['name']=str(buf[:size - 1])
			entry['caps']=0
			if caps:
				entry['caps']=struct.unpack(INT, caps)[0]
			devlist.append(entry)
			
		except Exception, e:
			print("[getInputDevices] <%s>" %str(e))
		os.close(fd)
	return devlist

def getDefaultInfos():
	infos={}
	try:
		#CPU
		processor=0
		cpuname=""
		bogomips=""
		file = open("/proc/cpuinfo", 'r')
		lines = file.readlines()
		file.close()
		for x in lines:
			line = x.strip()
			entry=line.split(': ',1)
			if len(entry)==2:
				#print entry
				if "processor" in entry[0]:
					processor+=1
				if "cpu model" in entry[0]:
					cpuname=entry[1]
				if "BogoMIPS" in entry[0]:
					bogomips=entry[1]
		infos['CPU-Count'] = str(processor)
		infos['CPU-Name'] = cpuname
		infos['BogoMIPS'] = bogomips
		#Load
		if hasattr(os, 'getloadavg'):
			av1, av2, av3 = os.getloadavg()
			infos['Load'] = "%.1f %.1f %.1f" %(av1, av2, av3)
		#Hostname
		infos['Hostname'] = socket.gethostname()
		#Uptime
		file = open("/proc/stat", 'r')
		lines = file.readlines()
		file.close()
		for x in lines:
			line = x.strip()
			entry=line.split(' ',1)
			if len(entry)==2:
				if "btime"==entry[0]:
					diff=int(time.time()-int(entry[1]))
					infos['Uptime'] = time.strftime('%H:%M', time.localtime(diff))
					
		#uname
		if hasattr(os, 'uname'):
			val=os.uname()
			if len(val)>=5:
				infos['Uname'] = "%s: %s" %(val[0],val[2])
		#memory
		file = open("/proc/meminfo", 'r')
		lines = file.readlines()
		file.close()
		for x in lines:
			line = x.strip()
			entry=line.split(':',1)
			if len(entry)==2:
				infos[entry[0]] = entry[1].replace(" ","")
		
	except Exception, e:
		print("[getDefaultInfos] <%s>" %str(e))
	return infos

def getUSBDevices(path="/sys/bus/usb/devices/"):
	ulist=[]
	prefix = path
	try:
		def readattr(path, name):
			f = open(prefix + path + "/" + name);
			return f.readline().rstrip("\n");
			
		def readlink(path, name):
			return os.path.basename(os.readlink(prefix + path + "/" + name));
			
		def readUevent(path, name):
			l=[]
			file = open(prefix + path + "/" + name, 'r')
			lines = file.readlines()
			file.close()
			for x in lines:
				line = x.strip()
				l.append(line)
			return l
	
		for dirname in os.listdir(prefix):
			if dirname[0].isdigit():
				entry={}
				#print dirname
				#entry['Path']=dirname
				if os.path.exists(prefix+dirname+"/driver"):
					entry['Driver']=readlink(dirname, "driver")
				if os.path.exists(prefix+dirname+"/product"):
					entry['Product']=readattr(dirname, "product")
				if os.path.exists(prefix+dirname+"/manufacturer"):
					entry['Manufacturer']=readattr(dirname, "manufacturer")
				if os.path.exists(prefix+dirname+"/speed"):
					entry['Speed']=readattr(dirname, "speed")#MBit/s
				if os.path.exists(prefix+dirname+"/model"):
					entry['Model']=readattr(dirname, "model")
				if os.path.exists(prefix+dirname+"/vendor"):
					entry['Typ']=readattr(dirname, "vendor")
				if os.path.exists(prefix+dirname+"/uevent"):
					entry['Uevent']=readUevent(dirname, "uevent")
				ulist.append(entry.copy())
				entry.clear()
		
	except Exception, e:
		print("[getUSBDevices] <%s>" %str(e))
	return ulist
