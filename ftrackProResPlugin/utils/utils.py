__author__ = 'Natasha'

import subprocess
import shlex
import os
import glob
from datetime import datetime

def getShotInfo(inputFolder, imageExt):
    '''
    Returns shot information
    :param inputFolder: Input Folder
    :param imageExt: Image extension
    :return: shotName, first frame, last frame and date
    '''
    date = datetime.now()
    dateStr = '%s/%s/%s' % (date.day, date.month, date.year)
    files = [file for file in os.listdir(inputFolder) if file.endswith(imageExt)]
    files.sort()
    if files:
        shotName = files[0].split('.')[0]
        firstFrame = files[0].split('.')[1]
        lastFrame = files[-1].split('.')[1]
        return shotName, int(firstFrame), int(lastFrame), dateStr, firstFrame
    else:
        return '',0,0,dateStr

def generateSlugImages(tmpDir, label, firstFrame, lastFrame, date, firstFrameStr, bar):
    '''
    Slug Images are generated and stored in tmpDir
    :param tmpDir: Temporary Directory in the Users local temp
    :param shotName: Name of the shot  type:str
    :param firstFrame: First frame type:int
    :param lastFrame: Last frame type: int
    :param date: Date mm/dd/yyyy type:str
    :param bar: Nuke Progress Bar object
    :return:
    '''

    slugCommand = 'convert.exe -size 450x40 -background black -fill white -pointsize 20 ' \
                  'label:"quarks %s ball frames:10" %s\\slug.jpg' % (date,tmpDir)
    args = shlex.split(slugCommand)
    result = []
    label = label.replace('Frame#', '')
    totalFrames = lastFrame - firstFrame
    incrValue = 100.0/totalFrames
    count = 0
    for i in range(firstFrame, lastFrame+1):
        frameStr = firstFrameStr[:-(len(str(i)))] + str(i)
        args[-1] = '%s\\slug.%s.jpg' % (tmpDir, frameStr)
        args[-2] = 'label:%s %s' % (label, str(frameStr))
        result.append(subprocess.call(args, shell=True))
        count = count + incrValue
        bar.setValue(int(count))
    for i in result:
        if i != 0:
            return 1
    return 0

def generateSlugMovie(tmpDir, firstFrame, firstFrameStr):
    '''
    Generates a movie of the slug images. Stores it in the same temp folder
    :param tmpDir: Temp Folder in the users local temp.
    :param firstFrame: first frame
    :return:
    '''
    if firstFrameStr[0] == '0':
        frameLen = len(str(firstFrameStr))
        slugMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\slug.%%0%sd.jpg" ' \
                     '-vcodec prores -profile:v 2 "%s\\slug.mov"' % (firstFrame, tmpDir, frameLen, tmpDir)
    else:
        frameLen = len(str(firstFrameStr))-1
        slugMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s\\slug.1%%0%sd.jpg" ' \
                     '-vcodec prores -profile:v 2 "%s\\slug.mov"' % (firstFrame, tmpDir, frameLen, tmpDir)
    args = shlex.split(slugMovCmd)
    result = subprocess.call(args, shell=True)
    return result

def generateFileMovie(inputFolder, tmpDir, outputFile, firstFrame, fileName, imageExt, lastFrame, firstFrameStr):
    '''
    Composites the slug movie with the input images to generate the final movie.
    '''
    if imageExt == 'exr':
        # Convert exr to exr using imagemagik to get the exr format correct.
        convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr)
        filePath = '%s\\exrTmp\\%s' % (os.environ['TEMP'], fileName)
    else:
        filePath = '%s\\%s' % (inputFolder, fileName)
    inputFile = '%s.%s.%s' % (fileName, firstFrame, imageExt)

    if firstFrameStr[0] == '0':
        frameLen = len(str(firstFrameStr))
        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s.%%0%sd.%s" ' \
                      '-i "%s\\slug.mov" -metadata comment="Source Image:%s" -filter_complex "overlay=1:1" ' \
                      '-vcodec prores -profile:v 2 "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                                             tmpDir, inputFile, outputFile)
    else:
        frameLen = len(str(firstFrameStr))-1
        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s.1%%0%sd.%s" ' \
                      '-i "%s\\slug.mov" -metadata comment="Source Image:%s" -filter_complex "overlay=1:1" ' \
                      '-vcodec prores -profile:v 2 "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                                             tmpDir, inputFile, outputFile)

    return finalMovCmd

def generateFileMovieNoSlug(inputFolder, outputFile, firstFrame, fileName, imageExt, lastFrame, firstFrameStr):
    '''
    Generate the movie without the slug, only from the input image sequence.
    '''
    if imageExt == 'exr':
        # Convert exr to correct format using imagemagik
        convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr)
        filePath = '%s\\exrTmp\\%s' % (os.environ['TEMP'], fileName)
    else:
        filePath = '%s\\%s' % (inputFolder, fileName)

    if firstFrameStr[0] == '0':
        frameLen = len(str(firstFrameStr))
        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s.%%0%sd.%s" ' \
                      '-metadata comment="Source Image:%s.%s.%s" -vcodec prores ' \
                      '-profile:v 2 "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                              fileName, firstFrame,imageExt, outputFile)
    else:
        frameLen = len(str(firstFrameStr))-1
        finalMovCmd = 'ffmpeg.exe -y -start_number %s -an -i "%s.1%%0%sd.%s" ' \
                      '-metadata comment="Source Image:%s.%s.%s" -vcodec prores ' \
                      '-profile:v 2 "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                              fileName, firstFrame,imageExt, outputFile)

    return finalMovCmd

def convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr):
    '''
    Generate new exr from input exr images using ImageMagik.
    This was required as the compression type of the input exr images was not supported.
    '''
    if not os.path.exists('%s/exrTmp' % os.environ['TEMP']):
        os.mkdir('%s/exrTmp' % os.environ['TEMP'])
    slugCommand = 'convert.exe %s\\%s.exr "%s\\exrTmp\\%s.exr"' % (inputFolder,fileName,os.environ['TEMP'],fileName)
    args = shlex.split(slugCommand)
    for i in range(firstFrame, lastFrame+1):
        frameStr = firstFrameStr[:-(len(str(i)))] + str(i)
        args[1] = '%s/%s.%s.exr' % (inputFolder, fileName, frameStr)
        args[2] = '%s/exrTmp/%s.%s.exr' % (os.environ['TEMP'], fileName, frameStr)
        subprocess.call(args, shell=True)

def getVideoPlayer():
    '''
    Checks if QuickTimePlayer exists. If not checks for VLC player.
    :return: videoPlayerDir: Path of the video player
    '''
    videoPlayerDir = ''
    videoPlayerDirList = glob.glob('C:\\Program*\\QuickTime*')
    if videoPlayerDirList:
        videoPlayerDir = '%s\\QuickTimePlayer.exe' % videoPlayerDirList[0]
    else:
        videoPlayerDirList = glob.glob('C:\Program*\\VideoLan*')
        if videoPlayerDirList:
            videoPlayerDir = '%s\\VLC\\vlc.exe' % videoPlayerDirList[0]
    return videoPlayerDir

def extractTiffToTmp(filename, tmpFolder):
    if not os.path.exists(tmpFolder):
        os.mkdir(tmpFolder)
    cmd = 'ffmpeg.exe -i %s -f image2 "%s/temp.0%%3d.tiff"' % (filename, tmpFolder)
    args = shlex.split(cmd)
    result = subprocess.call(args, shell=True)
    return result

def getProjectName(filename):
    filename = filename.replace('/', '\\')
    project = str(filename).split('\\')[1]
    return project
