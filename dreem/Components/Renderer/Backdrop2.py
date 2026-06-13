# Embedded file name: /usr/lib/enigma2/python/Components/Renderer/Backdrop2.py
from Renderer import Renderer
from enigma import ePixmap, eSize, ePoint, eTimer, loadJPG, eEPGCache, getBestPlayableServiceReference
import json, re, os, socket, sys, math
tvdb_api = 'a99d487bb3426e5f3a60dea6d3d3c7ef'
tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
epgcache = eEPGCache.getInstance()
PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.parse import quote, urlencode
    from urllib.request import urlopen, Request
    from _thread import start_new_thread
else:
    from urllib2 import urlopen, quote
    from thread import start_new_thread
path_folder = '/data/event_images/content/'
if not os.path.isdir(path_folder):
    os.makedirs(path_folder)
REGEX = re.compile('([\\(\\[]).*?([\\)\\]])|(: odc.\\d+)|(\\d+: odc.\\d+)|(\\d+ odc.\\d+)|(:)|( -(.*?).*)|(,)|!|/.*|\\|\\s[0-9]+\\+|[0-9]+\\+|\\s\\d{4}\\Z|([\\(\\[\\|].*?[\\)\\]\\|])|(\\"|\\"\\.|\\"\\,|\\.)\\s.+|\\"|:|\xd0\x9f\xd1\x80\xd0\xb5\xd0\xbc\xd1\x8c\xd0\xb5\xd1\x80\xd0\xb0\\.\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x84\\s|(\xd1\x85|\xd0\xa5|\xd0\xbc|\xd0\x9c|\xd1\x82|\xd0\xa2|\xd0\xb4|\xd0\x94)/\xd1\x81\\s|\\s(\xd1\x81|\xd0\xa1)(\xd0\xb5\xd0\xb7\xd0\xbe\xd0\xbd|\xd0\xb5\xd1\x80\xd0\xb8\xd1\x8f|-\xd0\xbd|-\xd1\x8f)\\s.+|\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\.\\s\\d{1,3}\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s.+|\\s(\xd1\x87|\xd1\x87\\.|\xd1\x81\\.|\xd1\x81)\\s\\d{1,3}.+|\\d{1,3}(-\xd1\x8f|-\xd0\xb9|\\s\xd1\x81-\xd0\xbd).+|', re.DOTALL)

class Backdrop2(Renderer):

    def __init__(self):
        Renderer.__init__(self)
        self.noanimation = False
        self.movetimer = None
        self.WCover = self.HCover = 0
        self.posterwidth = 0
        self.lngg = None
        self.sz = '185,278'
        self.src = None
        self.nxts = None
        self.timer = eTimer()
        self.timer_conn = self.timer.timeout.connect(self.curPoster)
        return

    def applySkin(self, desktop, parent):
        attribs = []
        for attrib, value in self.skinAttributes:
            if attrib == 'language':
                self.lngg = value
            if attrib == 'nexts':
                self.nxts = int(value)
            if attrib == 'size':
                attribs.append((attrib, value))
                x, y = value.split(',')
                self.WCover, self.HCover = int(x), int(y)
            elif attrib == 'disableAnimation':
                if str(value) == '1':
                    self.noanimation = True
            if attrib.find('source'):
                self.src = value.split('.')[0]
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
            self.timer.start(30, True)

    def curPoster(self):
        self.instance.hide()
        self.event = self.source.event
        if self.event is None:
            self.instance.hide()
            return
        else:
            if self.event:
                evntNm = REGEX.sub('', self.event.getEventName()).strip()
                evntNm = evntNm.replace('\xc2\x86', '').replace('\xc2\x87', '')
                pstrNm = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                if os.path.exists(pstrNm):
                    self.posteranimation(pstrNm)
                    os.system('echo 3 > /proc/sys/vm/drop_caches')
                else:
                    if self.src == '100':
                        self.instance.hide()
                        os.system('echo 3 > /proc/sys/vm/drop_caches')
                        return
                    try:
                        self.year = self.filterSearch()
                        url_tmdb = 'https://api.themoviedb.org/3/search/{}?api_key={}&query={}'.format(self.srch, tmdb_api, quote(evntNm))
                        if self.year:
                            url_tmdb += '&year={}'.format(self.year)
                        if self.lngg != '':
                            url_tmdb += '&language={}'.format(self.lngg)
                        poster = json.load(urlopen(url_tmdb))['results'][0]['backdrop_path']
                        if poster:
                            url_poster = 'https://image.tmdb.org/t/p/original{}'.format(poster)
                            dwn_poster = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                            with open(dwn_poster, 'wb') as f:
                                f.write(urlopen(url_poster).read())
                            self.delay2()
                    except:
                        try:
                            url_tvdb = 'https://thetvdb.com/api/GetSeries.php?seriesname={}'.format(quote(evntNm))
                            url_read = urlopen(url_tvdb).read()
                            series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
                            if series_id:
                                url_tvdb = 'https://thetvdb.com/api/a99d487bb3426e5f3a60dea6d3d3c7ef/series/{}/en.xml'.format(series_id)
                                url_read = urlopen(url_tvdb).read()
                                poster = re.findall('<fanart>(.*?)</fanart>', url_read)[0]
                                if poster:
                                    url_poster3 = 'https://artworks.thetvdb.com/banners/{}'.format(poster)
                                    dwn_poster3 = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                                    with open(dwn_poster3, 'wb') as f:
                                        f.write(urlopen(url_poster3).read())
                            else:
                                return
                        except:
                            try:
                                url = 'https://www.google.com/search?q={}+backdrop&tbm=isch&tbs=sbd:0'.format(evntNm.replace(' ', '+'))
                                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
                                fatima = requests.get(url, stream=True, headers=headers).text
                                yassine = re.findall('"https://(.*?).jpg",(\\d*),(\\d*)', fatima)
                                redou = 9
                                for i in range(redou):
                                    url = 'https://' + yassine[i + 1][0] + '.jpg'
                                    dwn_poster3 = path_folder + '{}_b.jpg'.format(evntNm, i + 1).lower().replace(' ', '')
                                    open(dwn_poster3, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)

                            except:
                                return

            else:
                self.delay2()
                self.instance.hide()
                os.system('echo 3 > /proc/sys/vm/drop_caches')
                return
            return
            return

    def filterSearch(self):
        try:
            fd = '%s\n%s\n%s' % (self.event.getEventName(), self.event.getShortDescription(), self.event.getExtendedDescription())
            checkTV = ['serial',
             'series',
             'serie',
             'serien',
             's\xc3\xa9rie',
             's\xc3\xa9ries',
             'serious',
             'folge',
             'episodio',
             'episode',
             '\xc3\xa9pisode',
             "l'\xc3\xa9pisode",
             'ep.',
             'staffel',
             'soap',
             'doku',
             'tv',
             'talk',
             'show',
             'news',
             'factual',
             'entertainment',
             'telenovela',
             'dokumentation',
             'dokutainment',
             'documentary',
             'informercial',
             'information',
             'sitcom',
             'reality',
             'program',
             'magazine',
             'mittagsmagazin',
             '\xd1\x82/\xd1\x81',
             '\xd0\xbc/\xd1\x81',
             '\xd1\x81\xd0\xb5\xd0\xb7\xd0\xbe\xd0\xbd',
             '\xd1\x81-\xd0\xbd',
             '\xd1\x8d\xd0\xbf\xd0\xb8\xd0\xb7\xd0\xbe\xd0\xb4',
             '\xd1\x81\xd0\xb5\xd1\x80\xd0\xb8\xd0\xb0\xd0\xbb',
             '\xd1\x81\xd0\xb5\xd1\x80\xd0\xb8\xd1\x8f']
            checkMovie = ['film',
             'movie',
             '\xd1\x84\xd0\xb8\xd0\xbb\xd1\x8c\xd0\xbc',
             '\xd0\xba\xd0\xb8\xd0\xbd\xd0\xbe',
             '\xcf\x84\xce\xb1\xce\xb9\xce\xbd\xce\xaf\xce\xb1',
             'pel\xc3\xadcula',
             'cin\xc3\xa9ma',
             'cine',
             'cinema',
             'filma']
            for i in checkMovie:
                if i in fd.lower():
                    self.srch = 'movie'
                    break

            for i in checkTV:
                if i in fd.lower():
                    self.srch = 'tv'
                    break
                else:
                    self.srch = 'multi'

            if self.srch == 'movie':
                pattern = re.findall('\\d{4}', fd)
                return pattern[0]
        except:
            pass

    def epgs(self):
        if self.nxts != None or self.nxts != '0':
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
                pstrNm = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                if not os.path.exists(pstrNm):
                    try:
                        url_tmdb = 'https://api.themoviedb.org/3/search/multi?api_key={}&query={}'.format(tmdb_api, quote(evntNm))
                        if self.lngg != '':
                            url_tmdb += '&language={}'.format(self.lngg)
                        poster = json.load(urlopen(url_tmdb))['results'][0]['backdrop_path']
                        url_poster = 'https://image.tmdb.org/t/p/original{}'.format(poster)
                        dwn_poster = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                        with open(dwn_poster, 'wb') as f:
                            f.write(urlopen(url_poster).read())
                    except:
                        try:
                            url_tvdb = 'https://thetvdb.com/api/GetSeries.php?seriesname={}'.format(quote(evntNm))
                            url_read = urlopen(url_tvdb).read()
                            series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
                            if series_id:
                                url_tvdb = 'https://thetvdb.com/api/a99d487bb3426e5f3a60dea6d3d3c7ef/series/{}/en.xml'.format(series_id)
                                url_read = urlopen(url_tvdb).read()
                                poster = re.findall('<fanart>(.*?)</fanart>', url_read)[0]
                                if poster:
                                    url_poster2 = 'https://artworks.thetvdb.com/banners/{}'.format(poster)
                                    dwn_poster2 = path_folder + '{}_b.jpg'.format(evntNm).lower().replace(' ', '')
                                    with open(dwn_poster2, 'wb') as f:
                                        f.write(urlopen(url_poster2).read())
                            else:
                                return
                        except:
                            try:
                                url = 'https://www.google.com/search?q={}+backdrop&tbm=isch&tbs=sbd:0'.format(evntNm.replace(' ', '+'))
                                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
                                fatima = requests.get(url, stream=True, headers=headers).text
                                yassine = re.findall('"https://(.*?).jpg",(\\d*),(\\d*)', fatima)
                                redou = 9
                                for i in range(redou):
                                    url_y = 'https://' + yassine[i + 1][0] + '.jpg'
                                    dwn_poster3 = path_folder + '{}_b.jpg'.format(evntNm, i + 1).lower().replace(' ', '')
                                    open(dwn_poster3, 'wb').write(requests.get(url_y, stream=True, allow_redirects=True).content)

                            except:
                                return

            return
        else:
            return
            return

    def posteranimation(self, PstrNm):
        if self.noanimation:
            self.instance.resize(eSize(self.WCover, self.HCover))
            self.instance.setPixmap(loadJPG(PstrNm))
            self.instance.show()
        else:
            self.coveraniwidth = 0
            self.anistep = int(math.floor(float(self.WCover / 5)))
            self.instance.resize(eSize(self.coveraniwidth, self.HCover))
            self.movetimer = eTimer()
            self.movetimer_conn = self.movetimer.timeout.connect(self.slidefromleft)
            self.instance.setPixmap(loadJPG(PstrNm))
            self.instance.show()
            self.movetimer.start(18, True)

    def slidefromleft(self):
        go = True
        self.movetimer.stop()
        if self.coveraniwidth + self.anistep < self.WCover:
            self.coveraniwidth += self.anistep
        else:
            self.coveraniwidth = self.WCover
            go = False
        self.instance.resize(eSize(self.coveraniwidth, self.HCover))
        if go:
            self.movetimer.start(58, True)

    def delay2(self):
        self.timer2 = eTimer()
        self.timer2_conn = self.timer2.timeout.connect(self.dwn)
        self.timer2.start(1000, True)

    def dwn(self):
        start_new_thread(self.epgs, ())
        os.system('echo 3 > /proc/sys/vm/drop_caches')
