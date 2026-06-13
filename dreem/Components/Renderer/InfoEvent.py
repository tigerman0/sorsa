# Embedded file name: /usr/lib/enigma2/python/Components/Renderer/InfoEvent.py
from Renderer import Renderer
from Components.VariableText import VariableText
from enigma import eLabel, eTimer, eEPGCache, getBestPlayableServiceReference
import requests
from urllib2 import urlopen, quote
from thread import start_new_thread
import json, re, os, socket
path_folder = '/data/event_images/infos/'
if not os.path.isdir(path_folder):
    os.makedirs(path_folder)
REGEX = re.compile('([\\(\\[]).*?([\\)\\]])|(: odc.\\d+)|(\\d+: odc.\\d+)|(\\d+ odc.\\d+)|(:)|( -(.*?).*)|(,)|!|/.*|\\|\\s[0-9]+\\+|[0-9]+\\+|\\s\\d{4}\\Z|([\\(\\[\\|].*?[\\)\\]\\|])|(\\"|\\"\\.|\\"\\,|\\.)\\s.+|\\"|:|\xd0\x9f\xd1\x80\xd0\xb5\xd0\xbc\xd1\x8c\xd0\xb5\xd1\x80\xd0\xb0\\.\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x84\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x81\\s|\\s(\xd1\x81|\xd0\xa1)(\xd0\xb5\xd0\xb7\xd0\xbe\xd0\xbd|\xd0\xb5\xd1\x80\xd0\xb8\xd1\x8f|-\xd0\xbd|-\xd1\x8f)\\s.+|\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\.\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s\\d{1,3}.+|\\d{1,3}(-\xd1\x8f|-\xd0\xb9|\\s\xd1\x81-\xd0\xbd).+|', re.DOTALL)
epgcache = eEPGCache.getInstance()
omdb_api = 'de34bce8'

class InfoEvent(Renderer, VariableText):

    def __init__(self):
        Renderer.__init__(self)
        VariableText.__init__(self)
        self.nxts = None
        return

    def applySkin(self, desktop, parent):
        attribs = []
        for attrib, value in self.skinAttributes:
            if attrib == 'nexts':
                self.nxts = int(value)

        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    GUI_WIDGET = eLabel

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            self.text = ''
        else:
            self.delay()

    def infos(self):
        if self.nxts != None or self.nxts != '0':
            try:
                events = None
                evntNm = ''
                import NavigationInstance
                ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
                events = epgcache.lookupEvent(['IBDCT', (ref,
                  0,
                  -1,
                  -1)])
                for i in range(self.nxts):
                    title = events[i + 1][4]
                    evntNm = REGEX.sub('', title).rstrip()
                    evntNm = evntNm.replace('\xc2\x86', '').replace('\xc2\x87', '')
                    if evntNm:
                        url_omdb = 'https://www.omdbapi.com/?apikey=%s&t=%s' % (omdb_api, quote(evntNm))
                        data = json.load(urlopen(url_omdb))
                        open('/tmp/url_omdb', 'w').write(url_omdb)
                        path_file = '/data/event_images/infos/' + evntNm + '.json'
                        with open(path_file, 'wb') as f:
                            f.write(json.dumps(data))
                            f.close()
                        Title = data['Title']
                        imdbRating = data['imdbRating']
                        Country = data['Country']
                        Year = data['Year']
                        Rated = data['Rated']
                        Genre = data['Genre']
                        Awards = data['Awards']
                        Actors = data['Actors']
                        Poster = data['Poster']
                        if Title != 'N/A' or Title != '':
                            open('/tmp/rating', 'w').write('%s\n%s' % (imdbRating, Rated))
                            self.text = 'Title : %s\nYear : %s\nImdb : %s\nCountry : %s\nGenre : %s\nAwards : %s\nActors : %s\n' % (str(Title),
                             str(Year),
                             str(imdbRating),
                             str(Country),
                             str(Genre),
                             str(Awards),
                             str(Actors))
                        if Poster != 'N/A' or Poster != '':
                            url = requests.get(url_omdb).json()['Poster']
                            path_poster = '/data/event_images/content/' + '{}_p.jpg'.format(evntNm).lower().replace(' ', '')
                            if not os.path.exists(path_poster):
                                open(path_poster, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
                        else:
                            return
                    else:
                        return ''

            except:
                return ''

        else:
            return
        return

    def dwn(self):
        start_new_thread(self.infos, ())

    def delay(self):
        self.timer = eTimer()
        self.timer_conn = self.timer.timeout.connect(self.dwn)
        self.timer.start(1000, True)