# Embedded file name: /usr/lib/enigma2/python/Components/Renderer/NextEvents.py
from Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache, getBestPlayableServiceReference
import re, os

class NextEvents(Renderer):

    def __init__(self):
        Renderer.__init__(self)
        self.pth = '/media/hdd/ostende/event_images/content/'
        self.type = ''
        self.nxEvnt = 0
        self.epgcache = eEPGCache.getInstance()

    def applySkin(self, desktop, parent):
        attribs = self.skinAttributes[:]
        for attrib, value in self.skinAttributes:
            if attrib == 'size':
                self.piconsize = value
            if attrib == 'typeimage':
                self.type = value
            elif attrib == 'nextEvent':
                self.nxEvnt = int(value)

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
        if not self.source or not self.source.event:
            self.instance.hide()
            return

        try:
            event = self.source.event
            evntNm = event.getEventName()
            if not evntNm:
                import NavigationInstance
                ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
                events = epgcache.lookupEvent(['IBDCT', (ref,
                  0,
                  -1,
                  -1)])
                for i in range(self.nxEvnt):
                    title = events[i + 1][4]
                    evntNm = REGEX.sub('', title).rstrip()

            evntNm = re.sub(r'[^a-zA-Z0-9]+', '', evntNm).lower()
            pstrNm = os.path.join(self.pth, '{}_{}.jpg'.format(evntNm, self.type))

            if os.path.exists(pstrNm):
                self.instance.setPixmap(loadJPG(pstrNm))
                self.instance.show()
                os.system('echo 3 > /proc/sys/vm/drop_caches')
            else:
                self.instance.hide()
        except Exception as e:
            self.instance.hide()
            # optionally log to /tmp/next_events.log
            with open("/tmp/next_events.log", "a") as f:
                f.write("Error: {}\n".format(str(e)))


    def delay(self):
        self.timer = eTimer()
        self.timer_conn = self.timer.timeout.connect(self.showPoster)
        self.timer.start(30, True)
