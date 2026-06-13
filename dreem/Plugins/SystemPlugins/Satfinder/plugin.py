## Edit To DreamOS Images OE2.5 By RAED 14-12-2018
## Update By RAED & mfaraj fix some bugs 20-12-2018
## Update By RAED & mfaraj fix some bugs 24-12-2018

from enigma import eDVBResourceManager,\
	eDVBFrontendParametersSatellite, eDVBFrontendParametersTerrestrial, iDVBFrontend

from Screens.Screen import Screen
from Screens.ScanSetup import ScanSetup
from Screens.ServiceScan import ServiceScan
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Label import Label
from Components.Sources.FrontendStatus import FrontendStatus
from Components.ActionMap import ActionMap
from Components.NimManager import nimmanager, getConfigSatlist
from Components.MenuList import MenuList
from Components.config import ConfigSelection, getConfigListEntry
from Components.TuneTest import Tuner

feTerrestrial = iDVBFrontend.feTerrestrial
feSatellite = iDVBFrontend.feSatellite
feCable = iDVBFrontend.feCable
stateLock = iDVBFrontend.stateLock
stateFailed = iDVBFrontend.stateFailed
stateTuning = iDVBFrontend.stateTuning

Ver = "5.7"

logfile='/tmp/satfinder.log'

def logdata(label_name = '', data = None):
    try:
        data=str(data)
        fp = open(logfile, 'a')
        fp.write( str(label_name) + ': ' + data+"\n")
        fp.close()
    except:
        pass

def trace_error():
    import sys
    import traceback
    try:
        traceback.print_exc(file=sys.stdout)
        if os.path.exists(logfile):
            pass
        else:
            return
        traceback.print_exc(file=open(logfile, 'a'))
    except:
        pass
    
def dellog(label_name = '', data = None):
    import os
    if os.path.exists(logfile):
       os.remove(logfile)

class Satfinder(ScanSetup, ServiceScan):
	def openFrontend(self):
		res_mgr = eDVBResourceManager.getInstance()
		if res_mgr:
			self.raw_channel = res_mgr.allocateRawChannel(self.feid)
			if self.raw_channel:
				self.frontend = self.raw_channel.getFrontend()
				if self.frontend:
					return True
				else:
					print "getFrontend failed"
			else:
				print "getRawChannel failed"
		else:
			print "getResourceManager instance failed"
		return False

	def __init__(self, session, feid=0):
		self.frontendData = None
		self.initcomplete = False
		self.feid = feid
		dellog()
		self.oldref = None
		service = session and session.nav.getCurrentService()
		feinfo = service and service.frontendInfo()
		self.frontendData = feinfo and feinfo.getAll(True)
		del feinfo
		del service
                 
		if not self.openFrontend():
			self.oldref = session.nav.getCurrentlyPlayingServiceReference()
			session.nav.stopService() # try to disable foreground service
			if not self.openFrontend():
				if session.pipshown: # try to disable pip
					session.pipshown = False
					session.deleteDialog(session.pip)
					del session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen	
		ScanSetup.__init__(self, session, 'S')
		self.scan_nims.value=str(feid)
		self.scan_nims.save()
		self.tuner = Tuner(self.frontend)		
		#self["introduction"].setText("")
		self["introduction"].setText(_("Press OK to scan"))
		self["Frontend"] = FrontendStatus(frontend_source = lambda : self.frontend, update_interval = 100)
		self["actions"] = ActionMap(["SetupActions"],
		{
			"save": self.keyGoScan,
			"ok": self.keyGoScan,
			"cancel": self.keyCancel,
		}, -3)
		self.initcomplete = True
		self.onClose.append(self.__onClose)
		self.onShow.append(self.prepareFrontend)
                self.onLayoutFinish.append(self.layoutFinished)

                
        def layoutFinished(self):
                self.setTitle("Satfinder by (RAED & mfaraj) V" + str(Ver))

	def __onClose(self):
		self.session.nav.playService(self.oldref)

	def newConfig(self):
		cur = self["config"].getCurrent()
		print "cur is", cur
		if cur is None:
			pass
		elif cur == self.typeOfScanEntry or \
			cur == self.tunerEntry or \
			(self.systemEntry and cur == self.systemEntry) or \
			(self.modulationEntry and cur == self.modulationEntry) or \
			(self.satelliteEntry and cur == self.satelliteEntry) or \
			(self.enableMisEntry and cur == self.enableMisEntry) or \
			(self.plsModeEntry and cur == self.plsModeEntry) or \
			(self.plpidAutoEntry and cur == self.plpidAutoEntry):
			self.createSetup()

	def nimChanged(self, configElement):
		choices = configElement.getChoices()
		nim_idx = choices[configElement.index][2]
		nim = nimmanager.nim_slots[nim_idx]

		systems = [ ]
		systems_filtered = [ ]
		if 'S' in self.systems_enabled:
			s2_en = nim.isEnabled("DVB-S2")
			if s2_en:
				systems.append(("DVB-S2", _("DVB-S2")))
				systems_filtered.append(("DVB-S2", _("DVB-S2")))
			if nim.isEnabled("DVB-S"):
				systems.append(("DVB-S", _("DVB-S")))
				if not s2_en:
					systems_filtered.append(("DVB-S", _("DVB-S")))

		if 'C' in self.systems_enabled and nim.isEnabled("DVB-C"):
			systems.append(("DVB-C", _("DVB-C")))
			systems_filtered.append(("DVB-C", _("DVB-C")))

		if 'T' in self.systems_enabled:
			t2_en = nim.isEnabled("DVB-T2")
			if t2_en:
				systems.append(("DVB-T2", _("DVB-T2")))
				systems_filtered.append(("DVB-T2", _("DVB-T2")))
			if nim.isEnabled("DVB-T"):
				systems.append(("DVB-T", _("DVB-T")))
				if not t2_en:
					systems_filtered.append(("DVB-T", _("DVB-T")))

		self.systems = systems
		self.systems_filtered = systems_filtered
		# for compability with old plugins...
		self.scan_sat.system = ConfigSelection(default = eDVBFrontendParametersSatellite.System_DVB_S, choices = [
			(eDVBFrontendParametersSatellite.System_DVB_S, _("DVB-S")),
			(eDVBFrontendParametersSatellite.System_DVB_S2, _("DVB-S2"))])
		self.scan_sat.system.addNotifier(self.satSystemChanged, False, True, False)

		if nim_idx == self.tuned_slot:
			if self.tuned_type == feSatellite:
				system = self.defaultSat["system"] == eDVBFrontendParametersSatellite.System_DVB_S and "DVB-S" or "DVB-S2"
			elif self.tuned_type == feCable:
				system = "DVB-C"
			elif self.tuned_type == feTerrestrial:
				system = self.defaultTer["system"] == eDVBFrontendParametersTerrestrial.System_DVB_T and "DVB-T" or "DVB-T2"
			self.scan_system = ConfigSelection(default = system, choices = systems)
		else:
			self.scan_system = ConfigSelection(choices = systems)

		self.scan_system.addNotifier(self.systemChanged)

		self.scan_sat.pilot.value = eDVBFrontendParametersSatellite.Pilot_Unknown
		if nim.can_modulation_auto:
			self.scan_sat.modulation_auto.value = eDVBFrontendParametersSatellite.Modulation_Auto
			self.scan_cab.modulation_auto.value = eDVBFrontendParametersSatellite.Modulation_Auto
		if nim.can_auto_fec_s2:
			self.scan_sat.fec_s2_8psk_auto.value = eDVBFrontendParametersSatellite.FEC_Auto
			self.scan_sat.fec_s2_qpsk_auto.value = eDVBFrontendParametersSatellite.FEC_Auto

	def prepareFrontend(self):
		self.frontend = None
		if not self.openFrontend():
			self.session.nav.stopService()
			if not self.openFrontend():
				if self.session.pipshown: # try to disable pip
					self.session.pipshown = False
					del self.session.pip
					if not self.openFrontend():
						self.frontend = None # in normal case this should not happen
		self.tuner = Tuner(self.frontend)
		self.retune(None)

	def createSetup(self):
		self.plpidAutoEntry = None
		try:
                    self.fecEntry = None
                except:
                    trace_error()
                    return
		self.systemEntry = None
		self.modulationEntry = None
		self.satelliteEntry = None
		self.enableMisEntry = None
		self.plsModeEntry = None
		self.tunerEntry = None
		self.list = []
                slot_number = -1
                ttype = 0
                if self.frontendData is not None:
                        slot_number = self.frontendData.get("slot_number", -1)
                        ttype = self.frontendData.get("tuner_type", 0)

                tuned_slot = None
                idx = -1
                nim_list = []
                # collect all nims which are *not* set to "nothing"
                for n in nimmanager.nim_slots:
                        idx += 1
#				if n.config_mode == "nothing":
#					continue
#				if n.config_mode == "advanced" and len(nimmanager.getSatListForNim(n.slot)) < 1:
#					continue
#				if n.config_mode in ("loopthrough", "satposdepends"):
#					# Skip connected LNBs
#					continue
                                # TODO: this would cause trouble if someone connects a S2 tuner to an S Tuner
                                # If so i'd propose we automatically only show the "most capable" tuner:
                                #  * the T2 tuner if it's connected with a T-only tuner
                                #  * the S2 tuner when it's connected with a S-only tuner ...
                                # Listing both would be required whenever non-backwards-compatible demods show up
                                # Currently none if the above is actually possible
                        if n.isEnabled('DVB-S') or n.isEnabled('DVB-C') or n.isEnabled('DVB-T'):
                                nim_list.append((str(n.slot), n.friendly_full_description, idx))
                                if idx == slot_number:
                                        tuned_slot = str(n.slot)

                tuned_slot=str(self.feid)

                if tuned_slot:
                        self.scan_nims = ConfigSelection(choices = nim_list, default = tuned_slot)
                else:
                        self.scan_nims = ConfigSelection(choices = nim_list)
		self.tunerEntry = getConfigListEntry(_("Tuner"), self.scan_nims)
		self.list.append(self.tunerEntry)		
		self.typeOfScanEntry = getConfigListEntry(_('Tune'), self.tuning_type)
		self.list.append(self.typeOfScanEntry)
		
		try:
                    self.tuning_sat = self.scan_satselection[self.getSelectedSatIndex(self.feid)]
                except:
                    trace_error

		self.satEntry = getConfigListEntry(_('Satellite'), self.tuning_sat)
		self.list.append(self.satEntry)

		nim = nimmanager.nim_slots[self.feid]

		self.systemEntry = None
		if self.tuning_type.value == "manual_transponder":
			if nim.isCompatible("DVB-S2"):
				self.systemEntry = getConfigListEntry(_('System'), self.scan_sat.system)
				self.list.append(self.systemEntry)
			else:
				# downgrade to dvb-s, in case a -s2 config was active
				self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S
			self.list.append(getConfigListEntry(_('Frequency'), self.scan_sat.frequency))
			self.list.append(getConfigListEntry(_('Inversion'), self.scan_sat.inversion))
			self.list.append(getConfigListEntry(_('Symbol rate'), self.scan_sat.symbolrate))
			self.list.append(getConfigListEntry(_('Polarization'), self.scan_sat.polarization))
			if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S2:
				self.modulationEntry = getConfigListEntry(_('Modulation'), nim.can_modulation_auto and self.scan_sat.modulation_auto or self.scan_sat.modulation)
				mod = self.modulationEntry[1].value
				if mod == eDVBFrontendParametersSatellite.Modulation_8PSK:
					self.fecEntry = getConfigListEntry(_("FEC"), nim.can_auto_fec_s2 and self.scan_sat.fec_s2_8psk_auto or self.scan_sat.fec_s2_8psk)
				else:
					self.fecEntry = getConfigListEntry(_("FEC"), nim.can_auto_fec_s2 and self.scan_sat.fec_s2_qpsk_auto or self.scan_sat.fec_s2_qpsk)
				self.list.append(self.fecEntry)
				self.list.append(self.modulationEntry)
				self.list.append(getConfigListEntry(_('Roll-off'), self.scan_sat.rolloff))
				self.list.append(getConfigListEntry(_('Pilot'), self.scan_sat.pilot))
				if nim.can_multistream_s2:
					self.enableMisEntry = getConfigListEntry(_('Multistream'), self.scan_sat.enable_mis)
					self.list.append(self.enableMisEntry)
					if self.scan_sat.enable_mis.value:
						self.list.append(getConfigListEntry(_('Stream ID'), self.scan_sat.is_id))
				if nim.can_pls_s2:
					self.plsModeEntry = getConfigListEntry(_('PLS Mode'), self.scan_sat.pls_mode)
					self.list.append(self.plsModeEntry)
					if self.scan_sat.pls_mode.value != eDVBFrontendParametersSatellite.PLS_Unknown:
						self.list.append(getConfigListEntry(_('PLS Code'), self.scan_sat.pls_code))
			else:
				self.fecEntry = getConfigListEntry(_("FEC"), self.scan_sat.fec)
				self.list.append(self.fecEntry)
		elif self.tuning_transponder and self.tuning_type.value == "predefined_transponder":
			if nim.isCompatible("DVB-S2"):
				self.systemEntry = getConfigListEntry(_('System'), self.scan_sat.system)
				#self.list.append(self.systemEntry)
			else:
				# downgrade to dvb-s, in case a -s2 config was active
				self.scan_sat.system.value = eDVBFrontendParametersSatellite.System_DVB_S
                        self.modulationEntry = getConfigListEntry(_('Modulation'), nim.can_modulation_auto and self.scan_sat.modulation_auto or self.scan_sat.modulation)
                        self.fecEntry = getConfigListEntry(_("FEC"), self.scan_sat.fec)
			self.list.append(getConfigListEntry(_("Transponder"), self.tuning_transponder))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur is None:
			pass
		elif cur == self.satEntry:
			self.updateSats()
			self.createSetup()
		else:
			ScanSetup.newConfig(self)
		if self.systemEntry and cur == self.systemEntry or \
			cur == self.tuning_type:
			self.retune(None)

	def sat_changed(self, config_element):
		self.newConfig()
		self.retune(config_element)

	def retune(self, configElement):
		returnvalue = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
		satpos = int(self.tuning_sat.value)
		if self.tuning_type.value == "manual_transponder":
			if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S:
				fec = self.scan_sat.fec.value
				mod = eDVBFrontendParametersSatellite.Modulation_QPSK
			else:
				mod = self.modulationEntry[1].value
				fec = self.fecEntry[1].value
			returnvalue = (
				self.scan_sat.frequency.float,
				self.scan_sat.symbolrate.value,
				self.scan_sat.polarization.value,
				fec,
				self.scan_sat.inversion.value,
				satpos,
				self.scan_sat.system.value,
				mod,
				self.scan_sat.rolloff.value,
				self.scan_sat.pilot.value,
				self.scan_sat.is_id.value if self.scan_sat.enable_mis.value else -1,
				self.scan_sat.pls_mode.value,
				self.scan_sat.pls_code.value if self.scan_sat.pls_mode.value < eDVBFrontendParametersSatellite.PLS_Unknown else 0)
			self.tune(returnvalue)
		elif self.tuning_type.value == "predefined_transponder":
			tps = nimmanager.getTransponders(satpos)
			l = len(tps)
			if self.scan_sat.system.value == eDVBFrontendParametersSatellite.System_DVB_S:
				fec = self.scan_sat.fec.value
				mod = eDVBFrontendParametersSatellite.Modulation_QPSK
			else:
				mod = self.modulationEntry[1].value
				fec = self.fecEntry[1].value
			if l > self.tuning_transponder.index:
				transponder = tps[self.tuning_transponder.index]
				self.scan_sat.frequency.value=[transponder[1] / 1000,0]
				self.scan_sat.symbolrate.value=transponder[2] / 1000
				self.scan_sat.polarization.value=transponder[3]
				self.scan_sat.fec.value=transponder[4]
				self.scan_sat.inversion.value=2
				self.scan_sat.system.value=transponder[5]
				self.scan_sat.rolloff.value=transponder[7]
				self.scan_sat.pilot.value=transponder[8]
				self.scan_sat.is_id.value=transponder[9]
				self.scan_sat.modulation_auto.value = eDVBFrontendParametersSatellite.Modulation_Auto
				returnvalue = (transponder[1] / 1000, transponder[2] / 1000,
					transponder[3], transponder[4], 2, satpos, transponder[5], transponder[6], transponder[8], transponder[9])
				self.tune(returnvalue)

	def createConfig(self, foo):
		self.tuning_transponder = None
		self.tuning_type = ConfigSelection(choices = [("predefined_transponder", _("Predefined transponder")), ("manual_transponder", _("Manual transponder"))])
		self.tuning_sat = getConfigSatlist(192, nimmanager.getSatListForNim(self.feid))
                self.orbital_position = 192
		if self.frontendData and self.frontendData.has_key('orbital_position'):
			self.orbital_position = self.frontendData['orbital_position']
		ScanSetup.createConfig(self, self.frontendData)
		self.updateSats()

		for x in (self.tuning_sat, self.scan_sat.frequency,
			self.scan_sat.inversion, self.scan_sat.symbolrate,
			self.scan_sat.polarization, self.scan_sat.fec,
			self.scan_sat.fec_s2_8psk, self.scan_sat.fec_s2_8psk_auto, 
			self.scan_sat.fec_s2_qpsk, self.scan_sat.fec_s2_qpsk_auto,
			self.scan_sat.modulation, self.scan_sat.modulation_auto,
			self.scan_sat.enable_mis, self.scan_sat.is_id, 
			self.scan_sat.pls_mode, self.scan_sat.pls_code,
			self.scan_sat.pilot, self.scan_sat.rolloff):
			x.addNotifier(self.retune, initial_call = False)

		self.satList = []
		self.scan_satselection = []
		for slot in nimmanager.nim_slots:
			if slot.isCompatible("DVB-S"):
				self.satList.append(nimmanager.getSatListForNim(slot.slot))
				self.scan_satselection.append(getConfigSatlist(self.orbital_position, self.satList[slot.slot]))
			else:
				self.satList.append(None)

	def getSelectedSatIndex(self, v):
		index    = 0
		none_cnt = 0
		for n in self.satList:
			if self.satList[index] == None:
				none_cnt = none_cnt + 1
			if index == int(v):
				return (index-none_cnt)
			index = index + 1
		return -1

	def updateSats(self):
		orb_pos = self.tuning_sat.orbital_position
		if orb_pos is not None:
			transponderlist = nimmanager.getTransponders(orb_pos)
			list = []
			default = None
			index = 0
			for x in transponderlist:
				if x[3] == 0:
					pol = "H"
				elif x[3] == 1:
					pol = "V"
				elif x[3] == 2:
					pol = "CL"
				elif x[3] == 3:
					pol = "CR"
				else:
					pol = "??"
				if x[4] == 0:
					fec = "FEC Auto"
				elif x[4] == 1:
					fec = "FEC 1/2"
				elif x[4] == 2:
					fec = "FEC 2/3"
				elif x[4] == 3:
					fec = "FEC 3/4"
				elif x[4] == 4:
					fec = "FEC 5/6"
				elif x[4] == 5:
					fec = "FEC 7/8"
				elif x[4] == 6:
					fec = "FEC 8/9"
				elif x[4] == 7:
					fec = "FEC 3/5"
				elif x[4] == 8:
					fec = "FEC 4/5"
				elif x[4] == 9:
					fec = "FEC 9/10"
				elif x[4] == 15:
					fec = "FEC None"
				else:
					fec = "FEC Unknown"
				e = str(x[1]) + "," + str(x[2]) + "," + pol + "," + fec
				if default is None:
					default = str(index)
				list.append((str(index), e))
				index += 1
			self.tuning_transponder = ConfigSelection(choices = list, default = default)
			self.tuning_transponder.addNotifier(self.retune, initial_call = False)

	def keyGoScan(self):
                self.retune(None)
		self.frontend = None
		self.raw_channel = None
		if self.raw_channel:
			del(self.raw_channel)
		self.updateSatList()
		#self.scan_satselection = [ self.tuning_sat ]
		self.satfinder = True
		tlist = []
		if type == iDVBFrontend.feSatellite:
			self.addSatTransponder(tlist,
				self.transponder[0], # frequency
				self.transponder[1], # sr
				self.transponder[2], # pol
				self.transponder[3], # fec
				self.transponder[4], # inversion
				self.tuning_sat.orbital_position,
				self.transponder[6], # system
				self.transponder[7], # modulation
				self.transponder[8], # rolloff
				self.transponder[9], # pilot
				self.transponder[10],# input stream id
				self.transponder[11],# pls mode
				self.transponder[12] # pls code
			)
		elif type == iDVBFrontend.feCable:
			parm = buildTerTransponder(
				self.transponder[1],  # frequency
				self.transponder[9],  # inversion
				self.transponder[2],  # bandwidth
				self.transponder[4],  # fechigh
				self.transponder[5],  # feclow
				self.transponder[3],  # modulation
				self.transponder[7],  # transmission
				self.transponder[6],  # guard
				self.transponder[8],  # hierarchy
				self.transponder[10], # system
				self.transponder[11]  # plp_id
			)
			tlist.append(parm)
		elif type == iDVBFrontend.feTerrestrial:
			self.addCabTransponder(tlist,
				self.transponder[0], # frequency
				self.transponder[1], # sr
				self.transponder[2], # modulation
				self.transponder[3], # fec_inner
				self.transponder[4]  # inversion
			)
		if True:
                    #self.buildTransponderList()
                    self.keyGo()
                else:
                    trace_error()

	def restartPrevService(self, yesno):
		if yesno:
			if self.frontend:
				self.frontend = None
				del self.raw_channel
		else:
			self.oldref = None
		self.close(None)

	def keyCancel(self):
		if self.oldref:
			self.session.openWithCallback(self.restartPrevService, MessageBox, _("Zap back to service before satfinder?"), MessageBox.TYPE_YESNO)
		else:
			self.restartPrevService(False)

	def tune(self, transponder):
		if self.initcomplete:
			if transponder is not None:
				self.tuner.tune(transponder)

class SatNimSelection(Screen):
	skin = """
		<screen position="140,165" size="400,130" title="select Slot">
			<widget name="nimlist" position="20,10" size="360,100" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		nimlist = nimmanager.getNimListOfType("DVB-S")
		nimMenuList = []
		for x in nimlist:
			nimMenuList.append((nimmanager.nim_slots[x].friendly_full_description, x))
		self["nimlist"] = MenuList(nimMenuList)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.okbuttonClick ,
			"cancel": self.close
		}, -1)

	def okbuttonClick(self):
		selection = self["nimlist"].getCurrent()[1]
		self.session.open(Satfinder, selection)

def SatfinderMain(session, **kwargs):
	nims = nimmanager.getNimListOfType("DVB-S")
	nimList = []
	try:
            for x in nims:
                    nim = nimmanager.getNimConfig(x)
                    if not nim.sat.configMode.value in ("loopthrough", "satposdepends", "nothing"):
                            nimList.append(x)

            if len(nimList) == 0:
                    session.open(MessageBox, _("No satellite frontend found!!"), MessageBox.TYPE_ERROR)
            else:
                    if session.nav.RecordTimer.isRecording():
                            session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start the satfinder."), MessageBox.TYPE_ERROR)
                    else:
                            #session.open(Satfinder)
                            #return
                            if len(nimList) == 1:
                                    session.open(Satfinder, nimList[0])
                            else:
                                    session.open(SatNimSelection)
	except:
            pass
            trace_error()

def SatfinderStart(menuid, **kwargs):
	if menuid == "scan":
		return [(_("Satfinder"), SatfinderMain, "satfinder", None)]
	else:
		return []

def Plugins(**kwargs):
	if (nimmanager.hasNimType("DVB-S")):
		return PluginDescriptor(name=_("Satfinder"), description=_("Helps setting up your dish"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=SatfinderStart)
	else:
		return []
