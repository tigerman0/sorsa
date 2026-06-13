# Embedded file name: /usr/lib/enigma2/python/Components/Renderer/Poster.py
from Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache, getBestPlayableServiceReference
import requests, json, re, os, socket, sys
from urllib2 import urlopen as uReq
from bs4 import BeautifulSoup as soup
from urllib2 import urlopen, quote
from thread import start_new_thread
epgcache = eEPGCache.getInstance()
REGEX = re.compile('([\\(\\[]).*?([\\)\\]])|(: odc.\\d+)|(\\d+: odc.\\d+)|(\\d+ odc.\\d+)|(:)|( -(.*?).*)|(,)|!|/.*|\\|\\s[0-9]+\\+|[0-9]+\\+|\\s\\d{4}\\Z|([\\(\\[\\|].*?[\\)\\]\\|])|(\\"|\\"\\.|\\"\\,|\\.)\\s.+|\\"|:|\xd0\x9f\xd1\x80\xd0\xb5\xd0\xbc\xd1\x8c\xd0\xb5\xd1\x80\xd0\xb0\\.\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x84\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x81\\s|\\s(\xd1\x81|\xd0\xa1)(\xd0\xb5\xd0\xb7\xd0\xbe\xd0\xbd|\xd0\xb5\xd1\x80\xd0\xb8\xd1\x8f|-\xd0\xbd|-\xd1\x8f)\\s.+|\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\.\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s\\d{1,3}.+|\\d{1,3}(-\xd1\x8f|-\xd0\xb9|\\s\xd1\x81-\xd0\xbd).+|', re.DOTALL)

class Poster(Renderer):

    def __init__(self):
        Renderer.__init__(self)
        self.pth = '/data/ArtWork/poster/'
        self.lngg = None
        self.sz = '185,278'
        self.nxts = 1
        return

    def applySkin(self, desktop, parent):
        attribs = []
        for attrib, value in self.skinAttributes:
            if attrib == 'path':
                self.pth = value
            if attrib == 'nexts':
                self.nxts = int(value)
            if attrib == 'size':
                self.sz = value.split(',')[0]
            attribs.append((attrib, value))

        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    GUI_WIDGET = ePixmap

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
        if what[0] != self.CHANGED_CLEAR:
            self.delay()

    def showPoster(self):
        self.instance.hide()
        self.event = self.source.event
        if self.event is None:
            self.instance.hide()
            return
        else:
            if self.event:
                evntNm = REGEX.sub('', self.event.getEventName()).strip()
                evntNm = evntNm.replace('\xc2\x86', '').replace('\xc2\x87', '')
                if not os.path.isdir(self.pth):
                    os.makedirs(self.pth)
                pstrNm = self.pth + evntNm + '.jpg'
                if os.path.exists(pstrNm):
                    self.instance.setPixmap(loadJPG(pstrNm))
                    os.system('echo 3 > /proc/sys/vm/drop_caches')
                    self.instance.show()
                else:
                    start_new_thread(self.downloadPoster, ())
            else:
                self.instance.hide()
                return
            return
            return

    def downloadPoster(self):
        events = None
        evntNm = ''
        try:
            import NavigationInstance
            ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
            events = epgcache.lookupEvent(['IBDCTESX', (ref,
              0,
              -1,
              -1)])
        except:
            pass

        try:
            for i in range(self.nxts):
                title = events[i][4]
                evntNm = title.replace('\xc2\x86', '').replace('\xc2\x87', '')
                evntNm = evntNm.replace('\xc2\x86', '').replace('\xc2\x87', '').replace('[0-9]\xd8\xa7\xd9\x84\xd8\xad\xd9\x84\xd9\x82\xd8\xa9:', '')
                pstrNm = self.pth + evntNm + '.jpg'
                if not os.path.exists(pstrNm):
                    try:
                        my_url = 'https://elcinema.com/search_entity/?q={}&entity=work'.format(quote(evntNm))
                        uClient = uReq(my_url)
                        page_html = uClient.read()
                        uClient.close()
                        page_soup = soup(page_html, 'html.parser')
                        containers = page_soup.findAll('div', {'class': 'columns small-12 min-body'})
                        for container in containers:
                            titles = [ link.get('href') for link in container.find_all('a') ]
                            link = container.findAll('div', {'class': 'padded-half'})
                            for links in link:
                                data = links.findAll('img', {'class': 'lazy-loaded'})
                                gdata = data[0]['data-src']
                                for x in range(len(data)):
                                    downloaded_image = requests.get(gdata).content
                                    with open(pstrNm, 'wb') as f:
                                        f.write(downloaded_image)

                    except:
                        pass

        except:
            pass

        return

    def delay(self):
        self.timer = eTimer()
        self.timer_conn = self.timer.timeout.connect(self.showPoster)
        self.timer.start(30, True)