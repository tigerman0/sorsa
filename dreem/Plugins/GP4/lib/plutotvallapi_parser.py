# -*- coding: utf-8 -*-
from Plugins.GP4.geminicomm.gcommtools import *
from Plugins.GP4.geminilocale.gLocale import _
from Plugins.GP4.gemininetcast.netcasttools import EXTRALIBPATH

import gzip

PLUTOTV=0

def parseMainlist(filename,Server):
	retlist=[]
	errorstr=""
	jdata=None
	try:
		data = gzip.GzipFile(filename).read()
		if data:
			jdata=readjson(jsonstr=data)
	except Exception as e:
		errorstr=str(e)
		
	try:
		if jdata:
			for regions,data in jdata.get("regions").items():
				name=data.get('name')
				logo=data.get('logo')
				channels=data.get('channels',{})
				grouplist={}
				if name and len(channels):
					#LänderDir
					#print str(name), str(logo)
					mitem=CDirItem(name=str(name))
					mitem.ID=Server.ID+regions
					mitem.dynPicUrl=str(logo)
					mitem.dynPicPath="/data/piconpool/netcastpicon/%s%s" %(str(regions), getUrlExtension(mitem.dynPicUrl))
					mitem.metadata["Server-ID"]=Server.metadata.get("Server-ID")
					mitem.metadata["Server-Logo"]=Server.metadata.get("Server-Logo")
					mitem.items=[]
					if regions=="de":
						mitem.sortPara=-1
				
					for ID,cha in channels.items():
						url='https://jmp2.uk/plu-%s.m3u8' % str(ID)
						citem=CStreamItem()
						citem.url=str(url)
						citem.sortPara=int(cha.get('chno',0))
						citem.name=str(cha.get('name',""))
						citem.staticCover="no_iptv.svg"
						citem.staticPic="plutotvallapi_logo.png"
						citem.staticPicFolder=EXTRALIBPATH
						citem.mediatype="videobroadcast"
						citem.metadata['Live']=True
						citem.metadata['TVG-ID']=str(ID)
						citem.metadata['dashManifestUrl'] = citem.url
						citem.metadata['Description']=str(cha.get('description',""))
						logourl=cha.get('logo')
						if logourl:
							citem.dynPicUrl=str(logourl)
							citem.dynPicPath="/data/piconpool/netcastpicon/%s%s" %(getTVGID2Service(citem.metadata.get('TVG-ID'),asPicon=True),getUrlExtension(citem.dynPicUrl))
						
						groupname=cha.get('group')
						if groupname not in grouplist:
							#GroupDir
							ditem=CDirItem(name=str(groupname))
							ditem.ID=str(uuid.uuid4())+"_"+groupname
							ditem.items=[]
							ditem.staticPic="folder_genre.svg"
							grouplist[groupname]=ditem
						if groupname in grouplist:
							grouplist[groupname].items.append(citem)
				
					for name, data in sorted(grouplist.items(), key=lambda x: x[1].sortPara, reverse=False):
						data.items.sort()
						mitem.items.append(data)
					retlist.append(mitem)
		
		if PLUTOTV:
			Log.e("regionslist=%d" %len(retlist))
		
		cleanModul(__name__,PLUTOTV)
		retlist.sort()
		return retlist
	except Exception as e:
		errorstr=str(e)
	Log.e(errorstr)
	cleanModul(__name__,PLUTOTV)
