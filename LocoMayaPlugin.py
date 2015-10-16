__author__ = 'Natasha'

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mm

kPluginCmdName = 'spLoadLocoPlugins'


class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self, argList):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        if cmds.menu('LocoVFX', exists=True):
            cmds.deleteUI('LocoVFX')
        showMyMenuCtrl = cmds.menu('LocoVFX', parent=gMainWindow, tearOff=False, label='LocoVFX')
        cmd = self.constructProResCmd()
        cmds.menuItem(parent=showMyMenuCtrl, label='ProResPlugin', command=cmd)

    def constructProResCmd(self):
        proresPluginPath = 'P:\\dev\\ftrack-connect-package\\resource\\legacy_plugins\\LocoMayaPlugin\\ftrackProResPlugin'
        if not proresPluginPath in sys.path:
            sys.path.append(proresPluginPath)
        cmd = 'from ftrackProResUI import FtrackProResMayaPlugin\n'
        cmd += 'form = FtrackProResMayaPlugin()\n'
        cmd += 'form.createDockLayout()'
        return cmd


def cmdCreator():
    return OpenMayaMPx.asMPxPtr(scriptedCommand())


def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator)
        cmds.spLoadLocoPlugins()
    except:
        sys.stderr.write("Failed to register command: %s\n" % kPluginCmdName)


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginCmdName)
