Example netcastserver_foobar.json
---------------------------------

desc			= Description
pic				= Picture Url
id				= must be unique
mediatype		= "playlist", "playlist_vod", "playlist_live" or "api"

AttachUrl		= all stream urls end with value
StreamUrlType	= all streams starts with "http" or "https"
UserAgent		= UserAgent for Stream

TVServiceType	= 4097 or 1
RadioServiceType = 4097 or 1

UpdateTime		= in hours until new list is fetched (default 12h)

{
	"serverlist": [	
		{
			"name" : "string",
			"mainUrl" : "string",
			
			"desc" : "string",
			"pic" : "string",
			"id" : "string",
			"mediatype" : "string",
			
			"AttachUrl" : "string",
			"StreamUrlType" : "string",
			"UserAgent" : "string",
			
			"TVServiceType" : integer,
			"RadioServiceType" : integer,
			
			"UpdateTime" : integer,
			"Username" : "string",
			"Password" : "string",
		}								
	]
}


Example netcastepg_foobar.json
---------------------------------

url				= After downloading a GZ or XZ file
id				= must be unique
EPGrefreshHour	= Updates the EPG-Data after x hours (default 12h)
UserAgent		= UserAgent for Download
Offset			= Offset to the EPG times

{
	"entrys": [
	{
		"name" : "string",
		"url" : "string",
		"id" : "string",
		
		"EPGrefreshHour" : integer,
		"UserAgent" : "string",
		"Offset" : integer
	}
}

Extra parameters for playlist m3u files
---------------------------------------
#EXT-X-PLAYLIST-TYPE:VOD	= VOD-Streams
#EXT-X-PLAYLIST-TYPE:EVENT	= Live-Streams
