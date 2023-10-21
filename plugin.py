# Zgemma H9 zukonMOD selector
# coded by zukon
# https://zukon.pl
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Console import Console
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os
import time
try:
	from subprocess import getoutput
except:
	from commands import getoutput

path = resolveFilename(SCOPE_PLUGINS, "Extensions/H9_zukonMOD_selector")
try:
	cat = gettext.translation('lang', path + '/po', [config.osd.language.getText()])
	_ = cat.gettext
except IOError:
	pass

class zukonSelector(Screen):
	skin = """
		<screen position="center,center" size="720,550" title="Zgemma h9 zukonMOD selector" >
		<widget name="imageList" position="50,60" size="605,425" scrollbarMode="showOnDemand"/>
		<ePixmap pixmap="skin_default/buttons/key_red.png" position="30,517" size="40,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_green.png" position="160,517" size="40,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_yellow.png" position="290,517" size="40,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_blue.png" position="420,517" size="40,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/key_menu.png" position="550,517" size="40,40" alphatest="on" />
		<widget name="key_red" position="45,510" zPosition="1" size="125,40" font="Regular;14" halign="center" valign="left" backgroundColor="transpBlack" transparent="1" />
		<widget name="key_green" position="175,510" zPosition="1" size="125,40" font="Regular;14" halign="center" valign="left" backgroundColor="transpBlack" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.Console = Console()
		self.disks = []
		self.systems = []
		self.systemsName = []
		self.kernel = ""
		self.listDisk("mmc")
		self.listDisk("sda")
		w = self.searchBoot()
		if w != 0:
			self.Console.ePopen("mount %s /boot" %str(w))
		self.selectImage()
		self.setSystemName()
		self["imageList"] = MenuList(self.systemsName)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Boot"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.runSys,
		}, -2)
	
	def listDisk(self, zadane):
		listDisk = getoutput("blkid")
		listDisk = listDisk.split("\n")
		x = 0
		while x < len(listDisk):
			if zadane in listDisk[x]:
				s = listDisk[x]
				s = " ".join(s.split())
				self.disks.append(s.replace(":","").split(" "))
			x += 1

	def searchBoot(self):
		y = 0
		while y < len(self.disks):
			if 'LABEL="zukonMOD_system"' in self.disks[y] and 'TYPE="ext4"' in self.disks[y]:
				return self.disks[y][0]
			y += 1
		return 0

	def selectImage(self):
		f = open("/boot/systems", "r")
		w = f.read().split("\n")
		f.close()
		w[:] = [x for x in w if x]
		self.systems.extend(w)

	def setSystemName(self):
		x = 0
		while x < len(self.systems):
			y = self.systems[x].split(";")
			self.systemsName.append(y[1])
			x += 1

	def cancel(self):
		self.Console.ePopen("umount -f /boot")
		self.close()
	
	def runSys(self):
		selName = self["imageList"].getCurrent()
		try:
			selIndex = self["imageList"].getCurrentIndex()
		except:
			selIndex = self["imageList"].getSelectionIndex()
		toRun = self.systems[selIndex].split(";")
		self.kernel, device = toRun[0], toRun[2]
		testFiles = self.checkAllFiles(self.kernel)
		if self.kernel == "nand":
			testSystem =True
		else:
			testSystem = self.cheskSystem(device)
		if testFiles and testSystem:
			self.session.openWithCallback(self.copySysFiles, MessageBox, _("Run %s and restart STB?") %selName, MessageBox.TYPE_YESNO, default=False)
		else:
			self.session.open(MessageBox, _("Image not found!"), MessageBox.TYPE_ERROR, timeout=4)

	def checkAllFiles(self, kernel):
		kernelFile = "/boot/kernel.%s" %kernel
		bootargsFile = "/boot/%s.bin" %kernel
		if os.path.isfile(kernelFile) and os.path.isfile(bootargsFile):
			return True
		else:
			return False

	def cheskSystem(self, device):
		try:
			testPath = "/tmp/testIMG"
			testFile = "%s/bin/bash" %testPath
			if not os.path.exists(testPath):
				os.mkdir(testPath)
			self.Console.ePopen("mount %s %s" %(device, testPath))
			if os.path.exists(testFile):
				self.Console.ePopen("umount -f %s" %(testPath))
				return True
			else:
				self.Console.ePopen("umount -f %s" %(testPath))
				return False
		except:
			return False

	def copySysFiles(self, data):
		if data:
			kernelFile = "/boot/kernel.%s" %self.kernel
			bootargsFile = "/boot/%s.bin" %self.kernel
			if os.path.exists(kernelFile) and os.path.exists(bootargsFile):
				self.Console.ePopen("dd if=%s of=/dev/mtdblock6" %str(kernelFile))
				time.sleep(1)
				self.Console.ePopen("dd if=%s of=/dev/mtdblock1 bs=65536 count=1" %str(bootargsFile))
				time.sleep(1)
				self.session.open(TryQuitMainloop, 2)
			else:
				self.session.open(MessageBox,_("Image was not detected on %s!") % self.kernel, MessageBox.TYPE_INFO, timeout=5)
		
def main(session, **kwargs):
	session.open(zukonSelector)

def Plugins(**kwargs):
	return [ PluginDescriptor(name="Zgemma h9 zukonMOD selector", description="Multiboot selector", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main) ]