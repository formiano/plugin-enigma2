# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. L�tsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigElement
from Components.config import ConfigIP
from Components.config import ConfigInteger
from Components.config import ConfigSelection
from Components.config import ConfigSubList
from Components.config import ConfigSubsection
from Components.config import ConfigSlider
from Components.config import ConfigText
from Components.config import ConfigYesNo
from Components.config import config
from Components.config import getConfigListEntry
from Screens.Screen import Screen
from VlcServer import VlcServer
from . import _

class ConfigMutable(ConfigElement):
	def __init__(self, configElementDict, defaultKey):
		ConfigElement.__init__(self)
		self.configElementDict = configElementDict
		if self.configElementDict.has_key(defaultKey):
			self.currentConfig = self.configElementDict[defaultKey]
			self.currentKey = defaultKey
			self.defaultKey = self.currentKey

	def addConfigElement(self, key, configElement):
		self.elements[key] = configElement

	def setAsCurrent(self, key):
		if self.configElementDict.has_key(key):
			self.currentConfig = self.configElementDict[key]
			self.currentKey = key
			self.saved_value = self.currentConfig.saved_value
			
	def setValue(self, val):
		self.currentConfig.value = val
		self.changed()

	def set_Value(self, val):
		self.currentConfig._value = val
		self.changed()

	def getValue(self):
		return self.currentConfig.value
	
	def get_Value(self):
		return self.currentConfig._value

	_value = property(get_Value, set_Value)
	
	def fromstring(self, value):
		return self.currentConfig.fromstring(value)

	def load(self):
		self.currentConfig.saved_value = self.saved_value
		self.currentConfig.load()

	def tostring(self, value):
		return self.currentConfig.tostring(value)

	def save(self):
		self.currentConfig.save()
		self.defaultKey = self.currentKey
		self.saved_value = self.currentConfig.saved_value

	def cancel(self):
		self.setAsCurrent(self.defaultKey)
		self.load()
		
	def isChanged(self):
		return self.currentConfig.isChanged()

	def changed(self):
		for x in self.notifiers:
			x(self)
			
	def addNotifier(self, notifier, initial_call = True):
		assert callable(notifier), "notifiers must be callable"
		self.notifiers.append(notifier)
		if initial_call:
			notifier(self)

	def disableSave(self):
		self.currentConfig.disableSave()

	def __call__(self, selected):
		return self.currentConfig(selected)

	def onSelect(self, session):
		self.currentConfig.onSelect(session)

	def onDeselect(self, session):
		self.currentConfig.onDeselect(session)

	def handleKey(self, key):
		self.currentConfig.handleKey(key)

	def getHTML(self, id):
		return self.currentConfig.getHTML(id)

	def genText(self):
		return self.currentConfig.genText()

	def getText(self):
		return self.currentConfig.getText()

	def getMulti(self, selected):
		return self.currentConfig.getMulti(selected)


class ConfigSelectionExtended(ConfigSelection):
	def __init__(self, choices, default = None):
		ConfigSelection.__init__(self, choices, default)

	def deleteNotifier(self, notifier):
		try: self.removeNotifier(notifier)
		except: pass


class __VlcServerConfig():
	def __init__(self):
		self.serverlist = []
		config.plugins.vlcplayer = ConfigSubsection()
		config.plugins.vlcplayer.servercount = ConfigInteger(0)
		config.plugins.vlcplayer.servers = ConfigSubList()
		config.plugins.vlcplayer.defaultserver = ConfigText("", False)
		for servernum in range(0, config.plugins.vlcplayer.servercount.value):
			self.new()

	# Add a new server or load a configsection if existing
	def new(self):
		newServerConfigSubsection = ConfigSubsection()
		config.plugins.vlcplayer.servers.append(newServerConfigSubsection)
		newServerConfigSubsection.name = ConfigText("Server " + str(self.__getServerCount()), False)
		if newServerConfigSubsection.name.value == newServerConfigSubsection.name.default:
			newServerConfigSubsection.name.default = ""
		newServerConfigSubsection.addressType = ConfigSelectionExtended(
				[("FQDN", "FQDN"),
				 ("IP", "IP-Address")
				], "IP")
		newServerConfigSubsection.hostip = ConfigMutable(
				{"IP": ConfigIP([192,168,1,1]),
				 "FQDN": ConfigText("fqdname", False)
				}, newServerConfigSubsection.addressType.value)
		newServerConfigSubsection.httpport = ConfigInteger(8080, (0,65535))
		newServerConfigSubsection.password = ConfigText("", False)
		newServerConfigSubsection.basedir = ConfigText("/", False)
		newServerConfigSubsection.dvdPath = ConfigText("", False)
		newServerConfigSubsection.transcodeVideo = ConfigYesNo()
		newServerConfigSubsection.transcodeAudio = ConfigYesNo(True)
		newServerConfigSubsection.videocodec = ConfigSelection(
				[("mp1v", "MPEG1"),
				 ("mp2v", "MPEG2")
				], "mp2v")
		newServerConfigSubsection.videobitrate = ConfigInteger(2000, (100, 9999))
		newServerConfigSubsection.audiocodec = ConfigSelection(
				[("mpga", "MPEG Layer 1 (mpga)"),
				 ("mp2a", "MPEG Layer 2 (mp2a)"),
				 ("mp3", "MPEG Layer 3 (mp3)")
				], "mp2a")
		newServerConfigSubsection.audiobitrate = ConfigInteger(128, (64, 320))
		newServerConfigSubsection.samplerate = ConfigSelection(
				[("32000", "32000"),
				 ("44100", "44100"),
				 ("48000", "48000")
				], "44100")
		newServerConfigSubsection.audiochannels = ConfigInteger(2, (1, 9))
		newServerConfigSubsection.videonorm = ConfigSelection(
				[("720,576,4:3,25,i", "720 x 576 (4:3) @ 25fps (PAL)"),
				 ("720,576,16:9,25,i", "720 x 576 (16:9) @ 25fps (PAL)"),
				 ("720,576,16:9,24,i", "720 x 576 (16:9) @ 24fps (PAL)"), 
				 ("704,576,4:3,25,i", "704 x 576 (4:3) @ 25fps (PAL)"),
				 ("704,576,16:9,25,i", "704 x 576 (16:9) @ 25fps (PAL)"),
				 ("544,576,4:3,25,i", "544 x 576 (4:3) @ 25fps (PAL)"),
				 ("544,576,16:9,25,i", "544 x 576 (16:9) @ 25fps (PAL)"),
				 ("480,576,4:3,25,i", "480 x 576 (4:3) @ 25fps (PAL)"),
				 ("480,576,16:9,25,i", "480 x 576 (16:9) @ 25fps (PAL)"),
				 ("480,288,4:3,25,i", "480 x 288 (4:3) @ 25fps (PAL)"),
				 ("480,288,16:9,25,i", "480 x 288 (16:9) @ 25fps (PAL)"),
				 ("352,576,4:3,25,i", "352 x 576 (4:3) @ 25fps (PAL)"),
				 ("352,576,16:9,25,i", "352 x 576 (16:9) @ 25fps (PAL)"),
				 ("352,288,4:3,25,i", "352 x 288 (4:3) @ 25fps (PAL)"),
				 ("352,288,16:9,25,i", "352 x 288 (16:9) @ 25fps (PAL)"),
				 ("720,480,4:3,30,i", "720 x 480 (4:3) @ 30fps (NTSC)"),
				 ("720,480,16:9,30,i", "720 x 480 (16:9) @ 30fps (NTSC)"),
				 ("640,480,4:3,30,i", "640 x 480 (4:3) @ 30fps (NTSC)"),
				 ("640,480,16:9,30,i", "640 x 480 (16:9) @ 30fps (NTSC)"),
				 ("544,480,4:3,30,i", "544 x 480 (4:3) @ 30fps (NTSC)"),
				 ("544,480,16:9,30,i", "544 x 480 (16:9) @ 30fps (NTSC)"),
				 ("480,480,4:3,30,i", "480 x 480 (4:3) @ 30fps (NTSC)"),
				 ("480,480,16:9,30,i", "480 x 480 (16:9) @ 30fps (NTSC)"),
				 ("480,240,4:3,30,i", "480 x 240 (4:3) @ 30fps (NTSC)"),
				 ("480,240,16:9,30,i", "480 x 240 (16:9) @ 30fps (NTSC)"),
				 ("353,480,4:3,30,i", "353 x 480 (4:3) @ 30fps (NTSC)"),
				 ("353,480,16:9,30,i", "353 x 480 (16:9) @ 30fps (NTSC)"),
				 ("352,240,4:3,30,i", "352 x 240 (4:3) @ 30fps (NTSC)"),
				 ("352,240,16:9,30,i", "352 x 240 (16:9) @ 30fps (NTSC)"),
				 ("1920,1080,16:9,50,p", "1920 x 1080 (16:9) @ 50p (HTDV)"),
				 ("1920,1080,16:9,25,p", "1920 x 1080 (16:9) @ 25p (HTDV)"),
				 ("1920,1080,16:9,25,i", "1920 x 1080 (16:9) @ 25i (HTDV)"),
				 ("1440,1080,16:9,25,p", "1440 x 1080 (16:9) @ 25p (HTDV)"),
				 ("1440,1080,16:9,25,i", "1440 x 1080 (16:9) @ 25i (HTDV)"),
				 ("1280,720,16:9,50,p", "1280 x 720 (16:9) @ 50p (HDTV)"),
				 ("1280,720,16:9,25,p", "1280 x 720 (16:9) @ 25p (HDTV)"),
				 ("720,576,16:9,50,p", "720 x 576 (16:9) @ 50p (HDTV)")
				], "352,288,4:3,25,i")
		newServerConfigSubsection.overscancorrection = ConfigInteger(0, (0, 100))
		newServerConfigSubsection.soverlay = ConfigYesNo()
		newServer = VlcServer(newServerConfigSubsection)

		self.serverlist.append(newServer)

		return newServer

	# Add was canceled or existing server should be removed
	def delete(self, server):
		config.plugins.vlcplayer.servers.remove(server.getCfg())
		self.serverlist.remove(server)
		self.__save()

	# Edit or Add should complete
	def save(self, server):
		server.getCfg().save()
		self.__save()

	# Edit has been canceled
	def cancel(self, server):
		for element in server.getCfg().dict().values():
			element.cancel()

	def getServerlist(self):
		return self.serverlist

	def getServerByName(self, name):
		for server in self.serverlist:
			if server.getName() == name:
				return server
		return None

	def getDefaultServer(self):
		return self.getServerByName(config.plugins.vlcplayer.defaultserver.value)

	def setAsDefault(self, defaultServer):
		if defaultServer is not None:
			config.plugins.vlcplayer.defaultserver.value = defaultServer.getName()
			config.plugins.vlcplayer.defaultserver.save()

	def __save(self):
		config.plugins.vlcplayer.servercount.value = self.__getServerCount()
		config.plugins.vlcplayer.servercount.save()

	def __getServerCount(self):
		return len(config.plugins.vlcplayer.servers)


vlcServerConfig = __VlcServerConfig()


class VlcServerConfigScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="VlcServerConfigScreen" position="80,100" size="560,320" title="Edit VLC Server">
			<widget name="config" position="10,10" size="540,250" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,280"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,280" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, server):
		Screen.__init__(self, session)
		self.server = server
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		cfglist = []
		cfglist.append(getConfigListEntry(_("Server Profile Name"), server.name()))
		cfglist.append(getConfigListEntry(_("Enter VLC-Server as FQDN or IP-Address"), server.addressType()))
		self.hostConfigListEntry = getConfigListEntry(_("Server Address"), server.host())
		cfglist.append(self.hostConfigListEntry)
		cfglist.append(getConfigListEntry(_("HTTP Port"), server.httpPort()))
		cfglist.append(getConfigListEntry(_("HTTP Password"), server.password()))
		cfglist.append(getConfigListEntry(_("Movie Directory"), server.basedir()))
		cfglist.append(getConfigListEntry(_("DVD Device (leave empty for default)"), server.dvdPath()))

		cfglist.append(getConfigListEntry(_("Transcode MPEG/DVD Video"), server.transcodeVideo()))
		cfglist.append(getConfigListEntry(_("Video Codec"), server.videoCodec()))
		cfglist.append(getConfigListEntry(_("Video Bitrate"), server.videoBitrate()))
		cfglist.append(getConfigListEntry(_("Video Norm"), server.videoNorm()))
		cfglist.append(getConfigListEntry(_("Overscan Correction [in %(percentsign)s of Video width]") % { "percentsign" : "%"}, server.overscanCorrection()))

		cfglist.append(getConfigListEntry(_("Subtitle overlay"), server.sOverlay()))

		cfglist.append(getConfigListEntry(_("Transcode MPEG/DVD Audio"), server.transcodeAudio()))
		cfglist.append(getConfigListEntry(_("Audio Codec"), server.audioCodec()))
		cfglist.append(getConfigListEntry(_("Audio Bitrate"), server.audioBitrate()))
		cfglist.append(getConfigListEntry(_("Audio Samplerate"), server.samplerate()))
		cfglist.append(getConfigListEntry(_("Audio Channels"), server.audioChannels()))

		ConfigListScreen.__init__(self, cfglist, session)

		server.addressType().addNotifier(self.switchAddressType, False)
		
		self.onClose.append(self.__onClose)
		
	def __onClose(self):
		self.server.addressType().deleteNotifier(self.switchAddressType)

	def switchAddressType(self, configElement):
		self.server.host().setAsCurrent(configElement.value)
		self["config"].invalidate(self.hostConfigListEntry)

	def keySave(self):
		self.close(True, self.server)

	def keyCancel(self):
		self.close(False, self.server)