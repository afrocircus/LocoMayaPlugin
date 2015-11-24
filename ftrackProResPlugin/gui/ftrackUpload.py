__author__ = 'natasha'

import os
import PySide.QtGui as QtGui
from PySide.QtCore import Qt
import threading
from utils import ftrackUtils
from PySide.QtCore import Signal

iconPath = 'P:\\dev\\ftrack-connect-package\\resource\\ftrack_connect_nuke\\nuke_path\\NukeProResPlugin'


class BrowserDialog(QtGui.QDialog):

    winClosed = Signal(str)

    def __init__(self, taskPath, parent=None, session=None):
        QtGui.QDialog.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.taskPath = taskPath
        viewerBox = QtGui.QGroupBox('Ftrack')
        self.layout().addWidget(viewerBox)
        vLayout = QtGui.QVBoxLayout()
        viewerBox.setLayout(vLayout)

        projList = QtGui.QListWidget()
        self.createProjList(session, projList)
        projList.itemClicked.connect(lambda: self.projItemClicked(session, projList.currentItem()))
        self.taskList = QtGui.QListWidget()
        self.taskList.itemClicked.connect(lambda: self.taskItemClicked(session, self.taskList.currentItem()))
        hLayout1 = QtGui.QHBoxLayout()
        hLayout1.addWidget(projList)
        hLayout1.addWidget(self.taskList)
        vLayout.addLayout(hLayout1)
        self.pathEdit = QtGui.QLineEdit()
        vLayout.addWidget(self.pathEdit)

        self.setButton = QtGui.QPushButton('Set')
        self.setButton.setDisabled(True)
        cancelButton = QtGui.QPushButton('Cancel')
        self.setButton.clicked.connect(self.setTaskPath)
        cancelButton.clicked.connect(self.closeWindow)
        hLayout2 = QtGui.QHBoxLayout()
        hLayout2.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        hLayout2.addWidget(self.setButton)
        hLayout2.addWidget(cancelButton)
        vLayout.addLayout(hLayout2)
        self.projPath = ''
        if not self.taskPath == '':
            self.pathEdit.setText(self.taskPath)
            self.createTaskList(session, self.taskPath)
            if ftrackUtils.isTask(session, taskPath):
                self.setProjPath(session)

    def createProjList(self, session, projList):
        projects = ftrackUtils.getAllProjectNames(session)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("%s\\PNG\\home.png" % iconPath))
        for project in projects:
            item = QtGui.QListWidgetItem(icon, project)
            projList.addItem(item)

    def projItemClicked(self, session, item):
        self.projPath = ''
        self.pathEdit.setText(str(item.text()))
        self.createTaskList(session, str(item.text()))
        self.setButton.setDisabled(True)

    def isAllTasks(self):
        for type, name in self.childList:
            if not type == 'task':
                return False
        return True

    def setProjPath(self, session):
        if self.isAllTasks():
            self.setButton.setDisabled(False)
            if self.projPath == '':
                tmpPath = str(self.pathEdit.text())
                self.projPath = tmpPath.split(' / ')[0]
                for p in tmpPath.split(' / ')[1:-1]:
                    self.projPath = '%s / %s' % (self.projPath, p)
                self.createTaskList(session, self.projPath)

    def taskItemClicked(self, session, item):
        pathtext = str(self.pathEdit.text())
        projPath = '%s / %s' % (pathtext, str(item.text()))
        if self.isAllTasks():
            if self.projPath == '':
                self.projPath = str(self.pathEdit.text())
            projPath = '%s / %s' % (self.projPath, str(item.text()))
            self.setButton.setDisabled(False)
        self.pathEdit.setText(projPath)
        self.createTaskList(session, projPath)

    def createTaskList(self, session, projPath):
        self.childList = ftrackUtils.getAllChildren(session, projPath)
        if not len(self.childList) == 0:
            self.taskList.clear()
            for type, name in self.childList:
                if type == 'assetbuild':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s\\PNG\\box.png" % iconPath))
                    item = QtGui.QListWidgetItem(icon, name)
                elif type == 'task':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s\\PNG\\signup.png" % iconPath))
                    item = QtGui.QListWidgetItem(icon, name)
                elif type == 'sequence':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s\\PNG\\movie.png" % iconPath))
                    item = QtGui.QListWidgetItem(icon, name)
                else:
                    item = QtGui.QListWidgetItem(name)
                self.taskList.addItem(item)

    def setTaskPath(self):
        self.winClosed.emit(self.getTaskPath())
        self.close()

    def getTaskPath(self):
        return str(self.pathEdit.text())

    def closeWindow(self):
        self.close()


class MyLabel(QtGui.QLabel):
    def paintEvent( self, event ):
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideMiddle, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class LoginWidget(QtGui.QWidget):

    loginSuccessful = Signal(str)

    def __init__(self, parent=None, filename=None, session=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout())
        frameBox = QtGui.QWidget()
        frameLayout = QtGui.QGridLayout()
        frameBox.setLayout(frameLayout)
        frameBox.setMaximumSize(500, 250)
        frameLayout.addWidget(QtGui.QLabel('Username:'), 0, 0)
        self.usernameEdit = QtGui.QLineEdit()
        frameLayout.addWidget(self.usernameEdit, 0, 1)
        self.loginButton = QtGui.QPushButton('Login')
        self.loginButton.clicked.connect(lambda: self.loginButtonPressed(session, filename))
        frameLayout.addWidget(self.loginButton, 2, 0)
        self.infoLabel = QtGui.QLabel()
        frameLayout.addWidget(self.infoLabel, 3, 1)
        self.layout().addWidget(frameBox)
        self.layout().addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 1, 0)

    def loginButtonPressed(self, session, filename):
        if not filename:
            loginFile = os.path.join(os.environ['TEMP'], 'ftrack_login.txt')
        f = open(filename, 'w')
        username = str(self.usernameEdit.text())
        f.write(('LOGNAME:%s' % username))
        f.close()
        if ftrackUtils.checkLogname(session, username):
            self.loginSuccessful.emit('Successful Login')
        else:
            self.infoLabel.setText('Incorrect username. Please try again.')


class MovieUploadWidget(QtGui.QWidget):

    uploadComplete = Signal(str)

    def __init__(self, parent=None, taskid=None, session=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout())
        self.frameIn = 0
        self.frameOut = 150
        frameBox = QtGui.QWidget()
        frameLayout = QtGui.QGridLayout()
        frameBox.setLayout(frameLayout)
        frameBox.setMaximumSize(500, 250)
        frameLayout.addWidget(QtGui.QLabel('Link To:'))
        taskid = taskid
        taskPath = ''
        if taskid:
            taskPath = ftrackUtils.getTaskPath(session, taskid)
        self.taskEdit = QtGui.QLineEdit(taskPath)
        self.taskEdit.setReadOnly(True)
        frameLayout.addWidget(self.taskEdit, 0, 1)
        self.taskEdit.textChanged.connect(lambda: self.updateAssetDrop(session))
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(lambda: self.openBrowserDialog(session))
        frameLayout.addWidget(self.browseButton, 0, 2)

        frameLayout.addWidget(QtGui.QLabel('Assets:'), 1, 0)
        hlayout = QtGui.QHBoxLayout()
        self.assetDrop = QtGui.QComboBox()
        self.assetDrop.addItem('Select')
        self.assetDrop.addItem('new')
        self.assetDrop.setMinimumWidth(100)
        self.assetDrop.activated[str].connect(self.assetSelected)
        hlayout.addWidget(self.assetDrop)
        hlayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        frameLayout.addLayout(hlayout, 1, 1)

        frameLayout.addWidget(QtGui.QLabel('Asset Name:'), 2, 0)
        self.assetEdit = QtGui.QLineEdit()
        self.assetEdit.setDisabled(True)
        frameLayout.addWidget(self.assetEdit)

        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(QtGui.QLabel('Comment'))
        vLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        frameLayout.addLayout(vLayout, 3, 0)
        self.commentBox = QtGui.QTextEdit()
        frameLayout.addWidget(self.commentBox, 3, 1)

        frameLayout.addWidget(QtGui.QLabel('Status:'), 4, 0)
        hlayout1 = QtGui.QHBoxLayout()
        self.statusDrop = QtGui.QComboBox()
        self.statusDrop.setMinimumWidth(100)
        hlayout1.addWidget(self.statusDrop)
        hlayout1.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        frameLayout.addLayout(hlayout1, 4, 1)

        frameLayout.addWidget(QtGui.QLabel('Output Movie'), 5, 0)
        self.movieLabel = MyLabel()
        self.movieLabel.setMinimumWidth(100)
        self.movieLabel.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        frameLayout.addWidget(self.movieLabel)
        self.framerate = '24'

        self.uploadButton = QtGui.QPushButton('Upload')
        self.uploadButton.setDisabled(True)
        self.uploadButton.clicked.connect(lambda: self.uploadMovie(session))
        frameLayout.addWidget(self.uploadButton, 6, 0)
        self.layout().addWidget(frameBox)
        self.layout().addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 1, 0)
        if not taskPath == '':
            self.updateAssetDrop(session)

    def setFrameCount(self, framein, frameout):
        self.frameIn = framein
        self.frameOut = frameout

    def setFrameRate(self, framerate):
        self.framerate = framerate

    def setMoviePath(self, moviePath):
        self.movieLabel.setText(str(moviePath))

    def setPath(self, newPath):
        self.taskEdit.setText(newPath)

    def assetSelected(self, assetName):
        if assetName == 'Select':
            self.assetEdit.setDisabled(True)
            self.uploadButton.setEnabled(False)
        elif assetName == 'new' :
            self.assetEdit.setDisabled(False)
            self.assetEdit.textChanged.connect(self.enableUploadButton)
        else:
            self.assetEdit.setDisabled(True)
            self.enableUploadButton()

    def updateAssetDrop(self, session):
        newPath = str(self.taskEdit.text())
        self.assetDrop.clear()
        self.assetDrop.addItem('Select')
        self.assetDrop.addItem('new')
        self.assetEdit.setDisabled(False)
        assetList = ftrackUtils.getAllAssets(session, newPath)
        self.assetDrop.addItems(assetList)
        self.updateStatusDrop(session, newPath)

    def updateStatusDrop(self, session, projectPath):
        statusList = ftrackUtils.getStatusList(session, projectPath)
        self.statusDrop.clear()
        self.statusDrop.addItems(statusList)
        currentStatus = ftrackUtils.getCurrentStatus(session, projectPath)
        self.statusDrop.setCurrentIndex(statusList.index(currentStatus))

    def openBrowserDialog(self, session):
        taskpath = str(self.taskEdit.text())
        self.gui = BrowserDialog(taskpath, parent=self, session=session)
        self.gui.show()
        self.gui.winClosed.connect(self.setPath)

    def enableUploadButton(self):
        self.uploadButton.setEnabled(True)

    def uploadMovie(self, session):
        self.uploadButton.setDisabled(True)
        self.uploadButton.setText('Uploading ...')
        inputFile = str(self.movieLabel.text())
        outfilemp4 =  os.path.splitext(inputFile)[0] + '.mp4'
        outfilewebm = os.path.splitext(inputFile)[0] + '.webm'
        thumnbail = os.path.join(os.path.split(inputFile)[0], 'thumbnail.png')
        threading.Thread( None, self.newThreadUpload, args=[session, inputFile, outfilemp4, outfilewebm, thumnbail]).start()

    def newThreadUpload(self, session, inputFile, outfilemp4, outfilewebm, thumnbail):
        result = self.convertFiles(inputFile, outfilemp4, outfilewebm)
        comment = str(self.commentBox.toPlainText())
        if result:
            thumbresult = ftrackUtils.createThumbnail(outfilemp4, thumnbail)
            taskPath = str(self.taskEdit.text())
            assetName = str(self.assetDrop.currentText())
            if assetName == 'new':
                assetName = str(self.assetEdit.text())
            asset = ftrackUtils.getAsset(session, taskPath, assetName)
            version = ftrackUtils.createAndPublishVersion(session, taskPath, comment, asset,
                                                outfilemp4, outfilewebm, thumnbail,
                                                self.frameIn, self.frameOut, self.framerate)
            ftrackUtils.setTaskStatus(session, taskPath, version, str(self.statusDrop.currentText()))
        self.deleteFiles(outfilemp4, outfilewebm, thumnbail)

    def deleteFiles(self, outfilemp4, outfilewebm, thumbnail):
        if os.path.exists(outfilemp4):
            os.remove(outfilemp4)
        if os.path.exists(outfilewebm):
            os.remove(outfilewebm)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)
        self.uploadButton.setEnabled(True)
        self.uploadButton.setText('Upload')
        self.uploadComplete.emit('Upload Complete!')

    def convertFiles(self, inputFile, outfilemp4, outfilewebm):
        mp4Result = ftrackUtils.convertMp4Files(inputFile, outfilemp4)
        webmResult = ftrackUtils.convertWebmFiles(inputFile, outfilewebm)

        if mp4Result == 0 and webmResult == 0:
            return True
        else:
            return False

'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = MovieUploadWidget()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''