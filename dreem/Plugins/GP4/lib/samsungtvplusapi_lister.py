from Plugins.GP4.geminicomm.gcommtools import *
from Plugins.GP4.geminilocale.gLocale import _
from Plugins.GP4.gemininetcast.netcasttools import NETCASTPLAYLISTFOLDER

class Csamsungtvplusapi(object):

    def __init__(self):
        self.__Server = None
        self.__netcastinstance = None
        return

    def setInstance(self, server = None, instance = None):
        self.__Server = server
        self.__filename = NETCASTPLAYLISTFOLDER + '/server/' + self.__Server.ID
        self.__netcastinstance = instance

    def FirstAction(self, item):
        pass

    def SecoundAction(self, kwargs, data):
        item = kwargs.get('item')
        if item.ID == 'netcastserver_samsungtvplusapi':
            from samsungtvplusapi_parser import parseMainlist
            return parseMainlist(self.__filename, self.__Server)

    def getMainlist(self, val = None):
        if pathExists(self.__filename) and time.time() - getFileTime(self.__filename) < self.__Server.metadata['UpdateTime']:
            from samsungtvplusapi_parser import parseMainlist
            return parseMainlist(self.__filename, self.__Server)
        url = self.__Server.url + '.channels.json.gz'
        gcommthread.add(ThreadItem({'url': url,
         'file': self.__filename,
         'item': self.__Server,
         'type': 'func'}, self.__netcastinstance.CheckBGAction, simpleUrllibDownload))


samsungtvplusapi = Csamsungtvplusapi()
