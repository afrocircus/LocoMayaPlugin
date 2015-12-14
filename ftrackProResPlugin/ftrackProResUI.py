__author__ = 'Natasha'

import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import threading
import re
import shutil
import maya.cmds as cmds
import maya.mel as mm
import subprocess
import shlex
from utils import ftrackUtils
from utils import utils
from gui import fileBrowser
from gui import ftrackUpload


class FtrackProResMayaPlugin(QtGui.QWidget):

    tick = QtCore.Signal(int, name="upload_changed")

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        session = ftrackUtils.startASession()
        self.setWindowTitle('Loco VFX - ProRes Plugin')
        self.setLayout(QtGui.QGridLayout())
        self.setMinimumSize(320,200)
        self.setObjectName('FtrackProResMayaPlugin')
        self.tabWidget = QtGui.QTabWidget()
        frameBox = QtGui.QWidget()
        viewerBox = QtGui.QGroupBox('')
        viewerBox.setMaximumSize(500, 150)
        vLayout = QtGui.QVBoxLayout()
        infile = ''
        if os.environ.has_key('FTRACK_SHOTID'):
            basedir, infile = ftrackUtils.getInputFilePath(os.environ['FTRACK_SHOTID'])

        if not infile == '':
            outfile = ftrackUtils.getOutputFilePath(basedir, infile)
        else:
            outfile = ''
        self.inputWidget = fileBrowser.FileBrowseWidget("Input Image File  ", infile, outfile)
        self.inputWidget.addOpenFileDialogEvent()
        self.outputWidget = fileBrowser.FileBrowseWidget("Output Movie File", outfile, outfile)
        self.outputWidget.addSaveFileDialogEvent()
        # Set trigger to change output path when input file is selected.
        self.inputWidget.fileEdit.textChanged.connect(self.outputWidget.setFilePath)
        # Set trigger to change label when input file is selected.
        #self.inputWidget.fileEdit.textChanged.connect(self.setSlugLabel)
        vLayout.addWidget(self.inputWidget)
        vLayout.addWidget(self.outputWidget)
        viewerBox.setLayout(vLayout)
        frameLayout = QtGui.QVBoxLayout()
        frameBox.setLayout(frameLayout)
        frameLayout.addWidget(viewerBox)

        if os.environ.has_key('FTRACK_TASKID'):
            self.movieWidget = ftrackUpload.MovieUploadWidget(taskid=os.environ['FTRACK_TASKID'], session=session)
        else:
            self.movieWidget = ftrackUpload.MovieUploadWidget(session=session)
        self.movieWidget.setMoviePath(str(self.outputWidget.getFilePath()))
        self.outputWidget.fileEdit.textChanged.connect(self.movieWidget.setMoviePath)
        self.movieWidget.uploadComplete.connect(self.showUploadCompleteDialog)

        # Setup the slug checkbox
        hLayout = QtGui.QHBoxLayout()
        self.slugBox = QtGui.QCheckBox('Slug')
        hLayout.addWidget(self.slugBox)
        self.slugBox.stateChanged.connect(lambda: self.showSlugOptions(session, self.slugBox.checkState()))
        hLayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        hLayout.addWidget(QtGui.QLabel('Frame Rate'))
        self.frameDrop = QtGui.QComboBox()
        self.frameDrop.addItems(['24', '25', '30'])
        hLayout.addWidget(self.frameDrop)
        hLayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        vLayout.addLayout(hLayout)
        vLayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        # Setup the slug options and set visibility to False.
        self.slugFrameBox = QtGui.QGroupBox('Slug Options')
        frameLayout.addWidget(self.slugFrameBox)
        hslugLayout = QtGui.QGridLayout()
        self.slugFrameBox.setLayout(hslugLayout)
        hslugLayout.addWidget(QtGui.QLabel('Slug Label'),0,0)
        self.slugTextBox = QtGui.QLineEdit('Customize Slug Label')
        hslugLayout.addWidget(self.slugTextBox,0,1)
        self.slugFrameBox.setVisible(False)
        self.slugFrameBox.setMaximumSize(500, 150)

        self.pLabel = QtGui.QLabel('')
        self.pBar = QtGui.QProgressBar()
        self.pBar.setVisible(False)
        self.pLabel.setVisible(False)
        frameLayout.addWidget(self.pLabel)
        frameLayout.addWidget(self.pBar)

        hLayout2 = QtGui.QHBoxLayout()
        self.createButton = QtGui.QPushButton('Create Movie')
        self.createButton.clicked.connect(self.createMovie)
        hLayout2.addWidget(self.createButton)
        self.openVideoButton = QtGui.QPushButton('Open Movie')
        hLayout2.addWidget(self.openVideoButton)
        self.openVideoButton.clicked.connect(self.openMovieFile)
        hLayout2.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        frameLayout.addLayout(hLayout2)
        frameLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        self.tabWidget.addTab(frameBox, 'ProRes Options')

        self.tabWidget.addTab(self.movieWidget, 'Ftrack Upload Options')
        self.layout().addWidget(self.tabWidget)
        self.getFrameCount()

    def updateTabWidget(self, tabStr):
        self.tabWidget.removeTab(1)
        self.tabWidget.addTab(self.movieWidget, 'Ftrack Upload Options')

    def getFrameCount(self):
        infile = str(self.inputWidget.getFilePath())
        if infile:
            inputFolder = os.path.dirname(str(infile))
            imageExt = str(infile).split('.')[-1]
            if imageExt.lower() == 'avi' or imageExt.lower() == 'mov':
                inputFolder = '%s/tiffSeq' % os.environ['TEMP']
                imageExt = 'tiff'
            shotName, firstFrame, lastFrame, date, firstFrameStr = utils.getShotInfo(str(inputFolder), str(imageExt))
            self.movieWidget.setFrameCount(firstFrame, lastFrame)

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = cmds.paneLayout(parent=gMainWindow, width=500)
        dockControl = cmds.dockControl(l='FtrackProResPlugin', allowedArea='all',\
                                        area='right', content=columnLay, width=500)
        cmds.control(str(self.objectName()),e=True,p=columnLay)

    def showSlugOptions(self, session, state):
        '''
        Sets visibilty of slug options based on state of slug check box.
        Resizes the window appropriately.
        :param state: State of the slug check box.
        '''
        if state == 2:
            self.slugFrameBox.setVisible(True)
            infile = str(self.inputWidget.getFilePath())
            if infile:
                self.setSlugLabel(session, infile)
        else:
            self.slugFrameBox.setVisible(False)

    def setSlugLabel(self, session, filename):
        '''
        Sets the slug label based on input file name.
        :param filename: Name of the input file
        '''
        inputFolder = os.path.dirname(str(filename))
        imageExt = str(filename).split('.')[-1]
        if inputFolder:
            if os.environ.has_key('FTRACK_SHOTID'):
                project = ftrackUtils.getProjectFromShot(session, os.environ['FTRACK_SHOTID'])
            else:
                project = utils.getProjectName(inputFolder)
            if imageExt.lower() == 'avi' or imageExt.lower() == 'mov':
                inputFolder = '%s/tiffSeq' % os.environ['TEMP']
                result = utils.extractTiffToTmp(filename, inputFolder)
                if result != 0:
                    QtGui.QMessageBox.warning(self, "Error", "Error while extracting images from input file!")
                shotName = filename.split('/')[-1].split('.')[0]
                from datetime import datetime
                d = datetime.now()
                date = '%s/%s/%s' % (d.day, d.month, d.year)
            else:
                shotName, firstFrame,lastFrame, date, firstFrameStr = utils.getShotInfo(str(inputFolder), str(imageExt))
            label = '%s %s %s Frame#' % (project, date, shotName)
        else:
            label = 'Customize Slug Label'
        self.slugTextBox.setText(label)

    def createMovie(self):
        frameRate = self.frameDrop.currentText()
        self.movieWidget.setFrameRate(frameRate)
        self.pBar.setVisible(True)
        self.pLabel.setVisible(True)
        self.pBar.setValue(0)
        self.pBar.setMinimum(0)
        self.pBar.setMaximum(100)

        self.createButton.setDisabled(True)
        inputFile = self.inputWidget.getFilePath()
        outputFile = str(self.outputWidget.getFilePath())

        slugChoice = self.slugBox.checkState()
        if 'Select' in inputFile or 'Select' in outputFile or inputFile == '' or outputFile == '':
            QtGui.QMessageBox.warning(self, 'Warning', 'Please select input and output folder')
            return

        inputFolder = os.path.dirname(str(inputFile))
        imageExt = str(inputFile).split('.')[-1]
        if not outputFile.endswith('.mov'):
            outputFile = '%s.mov' % outputFile

        if imageExt.lower() == 'avi' or imageExt.lower() == 'mov':
            inputFolder = '%s/tiffSeq' % os.environ['TEMP']
            imageExt = 'tiff'
            if not os.path.exists(inputFolder):
                result = utils.extractTiffToTmp(inputFile, inputFolder)
                if result != 0:
                    QtGui.QMessageBox.warning(self, "Error", "Error while extracting images from input file!")
                    return

        shotName, firstFrame, lastFrame, date, firstFrameStr = utils.getShotInfo(inputFolder, imageExt)
        self.movieWidget.setFrameCount(firstFrame, lastFrame)

        if slugChoice == 2:
            self.pLabel.setText("Creating slug files")
            tmpDir = '%s\\tmp' % os.environ['TEMP']
            if not os.path.exists(tmpDir):
                os.mkdir(tmpDir)

            slugResult = utils.generateSlugImages(tmpDir, self.slugTextBox.text(), firstFrame,
                                                  lastFrame, date, firstFrameStr, self.pBar)
            if slugResult != 0:
                QtGui.QMessageBox.warning(self, 'Error', "Error while creating slug images!")
                self.createButton.setEnabled(True)
                return
            slugMovResult = utils.generateSlugMovie(tmpDir, firstFrame, firstFrameStr)
            if slugMovResult != 0:
                QtGui.QMessageBox.warning(self, 'Error', "Error while creating slug movie!")
                self.createButton.setEnabled(True)
                return
            self.pBar.reset()
            finalMovCmd = utils.generateFileMovie(inputFolder, tmpDir, outputFile, firstFrame,
                                                shotName, imageExt, lastFrame, firstFrameStr)
        else:
            finalMovCmd = utils.generateFileMovieNoSlug(inputFolder, outputFile, firstFrame,
                                                  shotName, imageExt, lastFrame, firstFrameStr)
        threading.Thread( None, self.movieProgress, args=[finalMovCmd]).start()

        #if os.path.exists('%s/imageSeq' % os.environ['TEMP']):
         #   shutil.rmtree('%s/imageSeq' % os.environ['TEMP'])

    def movieProgress(self, finalMovCmd):
        self.pLabel.setText("Encoding Movie")
        p = subprocess.Popen(finalMovCmd, shell=True, bufsize=64, stderr=subprocess.PIPE)
        self.tick.connect(self.pBar.setValue)
        self.updateProgressBar(p)

    def updateProgressBar(self, process):
        while True:
            chatter = process.stderr.read(1024)
            durationRes = re.search(r"Duration:\s(?P<duration>\S+)", chatter)
            if durationRes:
                durationList = durationRes.groupdict()['duration'][:-1].split(':')
                duration = int(durationList[0])*3600 + int(durationList[1])*60 + float(durationList[2])
            result = re.search(r'\stime=(?P<time>\S+)', chatter)
            if result:
                elapsed_time = result.groupdict()['time'].split(':')
                secs = int(elapsed_time[0])*3600 + int(elapsed_time[1])*60 + float(elapsed_time[2])
                curValue = 10
                outOf = 100-curValue
                progress = secs/duration * outOf
                #self.pBar.setValue(int(progress))
                self.tick.emit(int(progress))
            if not chatter:
                #self.pBar.setValue(100)
                self.tick.emit(100)
                self.pLabel.setText("Encoding complete")
                self.createButton.setEnabled(True)
                if os.path.exists('%s/tiffSeq' % os.environ['TEMP']):
                   shutil.rmtree('%s/tiffSeq' % os.environ['TEMP'])
                if os.path.exists('%s/tmp' % os.environ['TEMP']):
                   shutil.rmtree('%s/tmp' % os.environ['TEMP'])
                break

    def openMovieFile(self):
        outfile = str(self.outputWidget.getFilePath())
        outfile = outfile.replace('/', '\\')
        if os.path.exists(outfile):
            videoPlayerDir = utils.getVideoPlayer()
            if not videoPlayerDir == '':
                self.openVideoButton.setText('Opening Movie ...')
                self.openVideoButton.setDisabled(True)
                threading.Thread(None, self.playMovie, args=[outfile, videoPlayerDir]).start()
            else:
                QtGui.QMessageBox.warning(self, 'Error', 'Video player error: QuickTime or VLC not installed.')
        else:
            QtGui.QMessageBox.warning(self, 'Error', 'Movie does not exist. Cannot play the video.')

    def showUploadCompleteDialog(self, txt):
        QtGui.QMessageBox.about(self, 'Success!', 'Upload Complete!')

    def playMovie(self, movFile, videoPlayerDir):
        cmd = '"%s" "%s"' % (videoPlayerDir, movFile)
        args = shlex.split(cmd)
        result = subprocess.call(args,  shell=True)
        self.openVideoButton.setText('Open Movie')
        self.openVideoButton.setEnabled(True)
        return result

'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = FtrackProResMayaPlugin()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''