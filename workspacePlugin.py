__author__ = 'Natasha'

import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm
from gui import FileWidget


class WorkspaceWidget(QtGui.QWidget):

    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout())
        self.setWindowTitle('Loco Workspace Manager')
        self.setMinimumSize(450,200)
        self.setObjectName('WorkspaceWidget')
        baseFile = os.path.join(os.environ['TEMP'], 'workspace_config.txt')
        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(QtGui.QLabel('Base Path'))
        baseEdit = QtGui.QLineEdit()
        baseEdit.setReadOnly(True)
        hlayout.addWidget(baseEdit)
        self.browseButton = QtGui.QToolButton()
        self.browseButton.setText('...')
        self.browseButton.clicked.connect(lambda: self.browseDirs(baseFile, baseEdit))
        hlayout.addWidget(self.browseButton)
        self.layout().addLayout(hlayout, 0, 0)
        basedir = self.getBaseDir(baseFile)
        if not basedir == '':
            self.setPath(basedir, baseFile)
            baseEdit.setText(basedir)

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = cmds.paneLayout(parent=gMainWindow, width=500)
        dockControl = cmds.dockControl(l='WorkspaceWidget', allowedArea='all',\
                                        area='right', content=columnLay, width=500)
        cmds.control(str(self.objectName()),e=True,p=columnLay)

    def browseDirs(self, baseFile, baseEdit):
        dialog = QtGui.QFileDialog()
        dirname = dialog.getExistingDirectory(self, "Select Directory",
                                              os.path.dirname(baseEdit.text()),
                                              options= QtGui.QFileDialog.DontUseNativeDialog)
        baseEdit.setText(str(dirname))
        self.setPath(str(dirname), baseFile)

    def setPath(self, basedir, baseFile):
        fileWidget = FileWidget.FileWidget(basedir)
        self.layout().addWidget(fileWidget, 2, 0)
        self.writePathToFile(basedir, baseFile)
        fileWidget.fileOpen.connect(self.openMayaFile)
        fileWidget.screenShot.connect(self.takeScreenshot)

    def takeScreenshot(self, fileName):
        import maya.OpenMaya as api
        import maya.OpenMayaUI as apiUI
        view = apiUI.M3dView.active3dView()
        image = api.MImage()
        view.readColorBuffer(image, True)
        image.writeToFile(fileName, 'jpg')

    def openMayaFile(self, filename):
        filename = filename.replace('\\', '/')
        cmds.file(filename, o=True, f=True)

    def writePathToFile(self, basedir, baseFile):
        f = open(baseFile, 'w')
        f.write(('Base Dir=%s' % basedir))
        f.close()

    def getBaseDir(self, baseFile):
        if os.path.exists(baseFile):
            f = open(baseFile, 'r')
            line = f.readline()
            basedir = line.split('=')[-1]
            return basedir
        else:
            return ''


'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = WorkspaceWidget()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''
