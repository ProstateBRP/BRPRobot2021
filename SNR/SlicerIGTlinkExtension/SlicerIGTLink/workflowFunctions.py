import sys, os, random
import vtk, ctk, slicer, qt
import numpy

import math
import string
import datetime
# for showing/hiding the task bar
import ctypes
from ctypes import wintypes

from ProstateBxLib.StyleUtils import buttonColors, buttonDisabledColors, colorPalette
from ProstateBxLib.DataStructs import SheetHole

# Utility functions used by the workflow steps


#Get object of a widget by a given name
def get(widget, objectName):
    if widget.objectName == objectName:
        return widget
    else:
        for w in widget.children():
            resulting_widget = get(w, objectName)
            if resulting_widget:
                return resulting_widget
        return None

#Set the given widget and children to the Slicer MRML Scene if possible
def setScene(widget):
    try:
       widget.setMRMLScene(slicer.mrmlScene)
    except AttributeError:
        for w in widget.children():
            resulting_widget = setScene(w)
            if resulting_widget:
                try:
                    resulting_widget.setMRMLScene(slicer.mrmlScene)
                except AttributeError:
                    continue

#Load UI from files for the Needle Guide Module
def loadUI(UIFileName):
    loader = qt.QUiLoader()
    moduleName = 'hms_needleguide'
    scriptedModulesPath = eval('slicer.modules.%s.path' % moduleName.lower())
    scriptedModulesPath = os.path.dirname(scriptedModulesPath)
    path = os.path.join(scriptedModulesPath, 'Resources', 'UI', UIFileName)
    if os.path.exists(path) is False:
        print 'loadUI: ERROR, file does not exist: ',path
        return None
    qfile = qt.QFile(path)
    qfile.open(qt.QFile.ReadOnly)
    widget = loader.load(qfile)
    return widget

# Get the Open IGT Link Connector node from the scene, creating a new one if necessary
def getIGTNode():
    igtNode = slicer.util.getNode('HMS_IGT_Node')
    if igtNode is None:
        igtNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLIGTLConnectorNode')
        # the node is owned by the Python variable, so can release the reference that
        # CreateNodeByClass added
        igtNode.UnRegister(None)
        igtNode.SetName('HMS_IGT_Node')
        slicer.mrmlScene.AddNode(igtNode)
    return igtNode


def getTimeString():
    hour = datetime.datetime.now().time().hour
    min = datetime.datetime.now().time().minute
    sec = datetime.datetime.now().time().second
    hStr = format(hour, '02d')
    mStr = format(min, '02d')
    sStr = format(sec, '02d')

    timeString =  datetime.datetime.now().date().isoformat() + 'T' + hStr + mStr + sStr

    return timeString

# Get the scripted module's parameter node
def getParameterNode():
    node = None
    size =  slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLScriptedModuleNode")
    for i in xrange(size):
      n  = slicer.mrmlScene.GetNthNodeByClass( i, "vtkMRMLScriptedModuleNode" )
      if n.GetModuleName() == "HMS_NeedleGuide":
        node = n
    return node

# Get the parameter value for key from the scripted module's parameter node.
# If the string key ends with the text Flag, convert to integer before returning.
# Returns None if parameter node not found, or key is not found on node
def getParameter(key):
    node = getParameterNode()
    if node is None:
        print 'ERROR: unable to get Needle Guide parameter node! Can\'t find parameter:', key
        return None

    value = node.GetParameter(key)
    if value == '':
        # print 'WARNING: unable to find parameter ',key
        return None
    if key.endswith('Flag'):
        # Return as integer
        parameter = int(value)
    else:
        # return as string
        parameter = value
    return parameter

def setParameter(key, value):
    parameterNode = getParameterNode()
    if parameterNode is not None:
        parameterNode.SetParameter(key, value)
    else:
        print 'Warning: Unable to set parameter ', key, ' to ', value, ', no parameter node found'

# Get the guide sheet corner holes fiducial node and return the 4 RAS
# coordinates in a numpy array. Returns None on error.
def getGuideSheetCorners():
    guideSheetCornersID = getParameter('guideSheetCornersID')
    if guideSheetCornersID is None:
        print 'Error: unable to get the parameter for the guide sheet corners fiducial node'
        return None
    # TBD: GetNodeByID is failing on this node
    # slicer.mrmlScene.GetNodeByID(guideSheetCornersID)
    guideSheetCornersNode = slicer.util.getNode(guideSheetCornersID)
    if guideSheetCornersNode is None:
        print 'Error: unable to get the guide sheet corners fiducial list node from id', guideSheetCornersID
        return None
    numHoles = guideSheetCornersNode.GetNumberOfFiducials()
    if numHoles != 4:
        print 'Warning: Don\'t have four points in the fiducial node: ', numHoles
    sheetPoints = []
    for n in range(numHoles):
        pos = [0,0,0]
        guideSheetCornersNode.GetNthFiducialPosition(n, pos)
        posArray = numpy.array(pos)
        sheetPoints.append(posArray)
    return sheetPoints

# Set the active volume from the given id
def setActiveVolume(volumeID):
    selectionNode = slicer.util.getNode('vtkMRMLSelectionNodeSingleton')
    if selectionNode is None:
        return

    currentVolumeID = selectionNode.GetActiveVolumeID()

    # With propogating of volume selection off, on receiving a new scan
    # it will already be set active but not displayed in the widgets.
    if currentVolumeID is None or currentVolumeID != volumeID:
        selectionNode.SetActiveVolumeID(volumeID)
    # Propagate the volume to all the slice composite nodes and refit
    setShowOnLoad(True)
    slicer.app.applicationLogic().PropagateBackgroundVolumeSelection()
    fitToSlices()
    fitTo3DView()
    setShowOnLoad(False)

# Set the foreground volume from the given id
def setForegroundVolume(volumeID):
    selectionNode = slicer.util.getNode('vtkMRMLSelectionNodeSingleton')
    if selectionNode is None:
        return

    currentVolumeID = selectionNode.GetSecondaryVolumeID()
    if currentVolumeID is None or currentVolumeID != volumeID:
        selectionNode.SetSecondaryVolumeID(volumeID)

        # Propagate the volume to all the slice composite nodes and re-fit
        setShowOnLoad(True)
        slicer.app.applicationLogic().PropagateForegroundVolumeSelection()
        setShowOnLoad(False)
        fitToSlices()


# Set the label volume from the given id
def setLabelVolume(volumeID):
    selectionNode = slicer.util.getNode('vtkMRMLSelectionNodeSingleton')
    if selectionNode is None:
        return

    currentVolumeID = selectionNode.GetActiveLabelVolumeID()
    if currentVolumeID != volumeID:
        selectionNode.SetActiveLabelVolumeID(volumeID)

        # Propagate the volume to all the slice composite nodes and re-fit
        setShowOnLoad(True)
        slicer.app.applicationLogic().PropagateLabelVolumeSelection()
        setShowOnLoad(False)
        fitToSlices()

def fitToSlices():
    # Ensure that the volume is fit to the slice windows that we use
    layoutManager = slicer.app.layoutManager()
    if not layoutManager:
        return
    # if in target, selection, confirmation, fit to the target zone
    ngw = slicer.modules.HMS_NeedleGuideWidget
    currentID = ngw.workflow.currentStep().id()
    updateFOV = False
    targetZoneBounds = None
    if currentID == ngw.targetStep.id() or currentID == ngw.fabricationStep.id() or currentID == ngw.confirmationStep.id():
        targetZoneBounds = [0,0,0,0,0,0]
        cubeModel = slicer.util.getNode('GreenZoneCube')
        if cubeModel is not None:
            cubeModel.GetRASBounds(targetZoneBounds)
            fovR = abs(targetZoneBounds[1] - targetZoneBounds[0])
            fovA = abs(targetZoneBounds[3] - targetZoneBounds[2])
            fovS = abs(targetZoneBounds[5] - targetZoneBounds[4])
            centerR = targetZoneBounds[0] + (fovR / 2.0)
            centerA = targetZoneBounds[2] + (fovA / 2.0)
            centerS = targetZoneBounds[4] + (fovS / 2.0)
            if getParameter('devModeFlag') == 1:
                print 'fitToSlices:\n\tfov = ', fovR, fovA, fovS, '\n\tcenter = ', centerR, centerA, centerS
            updateFOV = True
    widgetNames = layoutManager.sliceViewNames()
    for widgetName in widgetNames:
        widget = layoutManager.sliceWidget(widgetName)
        if widget is None:
            continue
        sliceNode = widget.sliceLogic().GetSliceNode()
        if sliceNode is None:
            continue
        # collapse slice node events
        modifyFlag = sliceNode.StartModify()
        widget.sliceLogic().FitSliceToAll()
        # only zoom in on axial slice as the grid is square in that
        # orientation, fit to slices will work well on the other orientations
        if updateFOV and sliceNode.GetOrientation() == 'Axial':
            widgetW = widget.width
            widgetH = widget.height
            # reset the widget field of view to zoom in, leave z alone
            oldFOV = sliceNode.GetFieldOfView()
            fovX = oldFOV[0]
            fovY = oldFOV[1]
            # scale the fov if the windows aren't square
            if (widgetW < widgetH):
                scaleX = 1.0
                scaleY = (float(widgetH) / float(widgetW))
            else:
                scaleX = (float(widgetW) / float(widgetH))
                scaleY = 1.0
            if getParameter('devModeFlag') == 1:
                print '\tscale X: ', scaleX, ', Y: ', scaleY
            if sliceNode.GetOrientation() == 'Axial':
                fovX = fovR * scaleX
                fovY = fovA * scaleY
            newFOV = [fovX, fovY, oldFOV[2]]
            if getParameter('devModeFlag') == 1:
                print '\t', widgetName, sliceNode.GetOrientation(), ': newFOV = ', newFOV
            sliceNode.SetFieldOfView(newFOV[0], newFOV[1], newFOV[2])
            if currentID == ngw.confirmationStep.id():
                # some confirmation scans may be centered around a target rather
                # than centered in the target zone, check that the S coordinate
                # is within the volume
                sliceBounds = [0,0,0,0,0,0]
                widget.sliceLogic().GetVolumeSliceBounds(widget.sliceLogic().GetBackgroundLayer().GetVolumeNode(), sliceBounds)
                if centerS < sliceBounds[4] or centerS > sliceBounds[5]:
                    sliceMiddle = (sliceBounds[4] + sliceBounds[5]) / 2
                    # make sure this is still within the target zone
                    if targetZoneBounds[4] < sliceMiddle and targetZoneBounds[5] > sliceMiddle:
                        if getParameter('devModeFlag') == 1:
                            print 'Fit to slices: resetting centerS from', centerS, 'to middle of background volume slice bounds:', sliceBounds, ': ', sliceMiddle
                        centerS = sliceMiddle
                    else:
                        if getParameter('devModeFlag') == 1:
                            print 'Fit to slices: new centerS ', sliceMiddle, ' not within target zone:', targetZoneBounds
            sliceNode.JumpSliceByCentering(centerR, centerA, centerS)
        sliceNode.EndModify(modifyFlag)
    slicer.app.processEvents()

def fitTo3DView():
    # recenter the 3d view
    viewerWidget = slicer.app.layoutManager().threeDWidget(0)
    if viewerWidget is not None:
        viewerWidget.threeDView().resetFocalPoint()
        # if in calibration, don't focus on the grid as the calibrator
        # is not in the same plane as the grid
        ngw = slicer.modules.HMS_NeedleGuideWidget
        if (ngw.workflow.currentStep().id() == ngw.calibrationStep.id()):
            reset3DCamera()
        else:
            reset3DCameraOnGrid()

# Pop up an information message in a dialog with an Ok button.
# Add the option to not pop up this information again if the
# infoKey is not an empty string.
def popupInfo(msg, infoKey = ''):
    if getParameter("TestingFlag"):
        # don't pop up information while testing
        print msg
        return
    qinfo = ctk.ctkMessageBox()
    qinfo.setWindowTitle('Information')
    resourcePath = getParameter('resources')
    if resourcePath is not None:
        infoPixmap = qt.QPixmap(os.path.join(resourcePath, "Icons/Small/sm_blue1info.png"))
        qinfo.setIconPixmap(infoPixmap)
    else:
        qinfo.setIcon(qt.QMessageBox.Information)
    qinfo.setStandardButtons(qt.QMessageBox.Ok)
    qinfo.setText(msg)
    if infoKey is not '':
        qinfo.dontShowAgainVisible = True
        qinfo.dontShowAgainSettingsKey = infoKey
    qinfo.exec_()

# Pop up a warning message in a dialog with an Ok button
def popupWarning(msg):
    if getParameter("TestingFlag"):
        # don't pop up warnings while testing
        print msg
        return
    qmsg = qt.QMessageBox()
    qmsg.setWindowTitle('WARNING')
    resourcePath = getParameter('resources')
    if resourcePath is not None:
        msgPixmap = qt.QPixmap(os.path.join(resourcePath, "Icons/Small/sm_blue1alert-message.png"))
        qmsg.setIconPixmap(msgPixmap)
    else:
        qmsg.setIcon(qt.QMessageBox.Warning)
    qmsg.setText(msg)
    qmsg.exec_()

# Pop up an error message in a dialog with an Ok button
def popupError(title, msg):
    if getParameter("TestingFlag"):
        # don't pop up errors while testing
        print title, '\n', msg
        return
    qmsg = qt.QMessageBox()
    qmsg.setWindowTitle(title)
    qmsg.setIcon(qt.QMessageBox.Critical)
    qmsg.setText(msg)
    qmsg.exec_()

# Pop up a question message box with Yes and No. If No is clicked,
# return False, if Yes is clicked, return True. Add the option to not ask
# this question again and save that in the questionKey if not an empty string.
# Defaults to No.
def popupQuestion(questionTitle, questionString, questionKey='', informationString=''):
    if getParameter("TestingFlag"):
        # don't pop up questions while testing, return True
        return True
    msgBox = ctk.ctkMessageBox()
    msgBox.setWindowTitle(questionTitle)
    # remove close, min, max buttons, but leave the title
    msgBox.setWindowFlags(qt.Qt.CustomizeWindowHint | qt.Qt.FramelessWindowHint | qt.Qt.WindowTitleHint)
    msgBox.setText(questionString)
    if informationString != '':
        msgBox.setInformativeText(informationString)
    msgBox.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No)
    msgBox.setDefaultButton(qt.QMessageBox.No)
    resourcePath = getParameter('resources')
    if resourcePath is not None:
        questionPixmap = qt.QPixmap(os.path.join(resourcePath, "Icons/Small/sm_blue1help.png"))
        msgBox.setIconPixmap(questionPixmap)
    else:
        msgBox.setIcon(qt.QMessageBox.Question)
    if questionKey is not '':
        msgBox.dontShowAgainVisible = True
        msgBox.dontShowAgainSettingsKey = questionKey
    ret = msgBox.exec_()
    if ret == qt.QMessageBox.No:
        return False
    else:
        return True

# Set the main module widget's status label
def setStatusLabel(message):
    if not hasattr(slicer.modules, 'HMS_NeedleGuideWidget'):
        print 'ERROR: Unable to get NeedleGuide widget to set status'
        return
    ngw = slicer.modules.HMS_NeedleGuideWidget
    if ngw is None:
        print 'ERROR: needle guide widget not defined, cannot set status'
        return
    ngw.setStatusLabel(message)

# Append to the status box
def appendToStatusBox(message):
    if not hasattr(slicer.modules, 'HMS_NeedleGuideWidget'):
        return
    ngw = slicer.modules.HMS_NeedleGuideWidget
    if ngw is None:
        print 'ERROR: needle guide widget not defined, cannot set status'
        return
    ngw.appendStatus(message)

# Use the Harmonus color palette to set the passed in button's style sheet.
# Valid buttonType
# Primary
# Secondary
def colorPushButtonFromPalette(button, buttonType):
    if buttonType != 'Primary' and buttonType != 'Secondary':
        print 'Invalid button type, please choose one of Primary or Secondary'
        return

    # get the style util colors
    colors = colorPalette()
    if buttonType == 'Primary':
        buttonColor = colors['ButtonNormal']
        textColor = colors['ButtonText']
        buttonHoverColor = colors['ButtonHover']
        buttonPressedColor = colors['ButtonPressed']
        buttonDisabledColor = colors['ButtonDisabled']
        textDisabledColor = colors['ButtonTextDisabled']
    elif buttonType == 'Secondary':
        buttonColor = colors['ButtonColorSecondary']
        textColor = colors['ButtonTextSecondary']
        buttonHoverColor = colors['ButtonHoverSecondary']
        buttonPressedColor = colors['ButtonPressedSecondary']
        buttonDisabledColor = colors['ButtonDisabled']
        textDisabledColor = colors['ButtonTextDisabled']

    # color is text color, background-color is the button color
    button.setStyleSheet('QPushButton { color: %s; background-color: %s; } QPushButton:hover:!pressed { color: %s; background-color: %s; } QPushButton:pressed { color: %s; background-color: %s; } QPushButton:disabled { color: %s; background-color: %s; }' % (textColor, buttonColor, textColor, buttonHoverColor, textColor, buttonPressedColor, textDisabledColor, buttonDisabledColor))
    # set it shadowed
    graphicsEffect = button.graphicsEffect()
    if graphicsEffect is None:
        # add a new shadow effect
        graphicsEffect = qt.QGraphicsDropShadowEffect()
        button.setGraphicsEffect(graphicsEffect)

# Use the style button colors to set the passed in button's style sheet.
# state: 0 is off, 1 is okay, 2 is warning, 3 is error
def colorPushButton(button, state):
    # get the style util colors
    colors = buttonColors()
    disabledColors = buttonDisabledColors()

    if state < 0 or state >= len(colors) or state >= len(disabledColors):
        print 'ERROR: invalid button state ', state, ', valid values are 0-', len(colors)
        return

    color = colors[state]
    disabledColor = disabledColors[state]

    # set the button's style sheet so that the active background is the selected color
    # while when it's disabled the text will still be black and the background will be
    # the disabled color
    button.setStyleSheet('QPushButton { background-color: %s; } QPushButton:disabled { color: #000000; background-color: %s; }' % (color, disabledColor))

def setButtonIcon(button, iconFile):
    if not hasattr(slicer.modules, 'hms_needleguide'):
        return
    scriptedModulesPath = os.path.dirname(slicer.modules.hms_needleguide.path)
    resourcePath = os.path.join(scriptedModulesPath, 'Resources')
    icon = qt.QIcon(os.path.join(resourcePath, 'Icons', iconFile))
    # icon.setStyleSheet('border-right-style: solid')
    # TBD: set separator between icon and text
    button.setIcon(icon)

# Use the Harmonus color palette to style the selected target label.
# Valid label types: 'Name', 'Grid', 'Depth'
def styleTargetLabel(label, labelType):
    # get the style util colors
    colors = colorPalette()
    if labelType == 'Name':
        textColor = 'black'
        backgroundColor = colors['SeparatorLine']
    elif labelType == 'Grid':
        textColor = colors['ButtonText']
        backgroundColor = colors['ButtonHover']
    elif labelType == 'Depth':
        textColor = colors['ButtonText']
        backgroundColor = colors['ButtonNormal']
    else:
        print 'styleTargetLabel: invalid label type ', labelType, ', please choose one of Name, Grid, Depth'
        return
    # add a black border around the colored background
    label.setStyleSheet('QLabel { border : 1px solid black; color: %s; background-color: %s; }' % (textColor, backgroundColor))

def genCode():
    setParameter('expectACKFlag', '1')
    IGTCode = str(random.randint(1000,9999))
    setParameter('IGTCode', IGTCode)
    if getParameter('devModeFlag') == 1:
        print 'genCode: ', IGTCode
    return "_" + IGTCode

def sendIGTString(string):
    devModeFlag = getParameter('devModeFlag')
    if devModeFlag:
        print 'sendIGTString: ', string
    igtNode = getIGTNode()
    if igtNode is None:
        print 'ERROR: sendIGTString: no communication node defined!'
        return
    output = slicer.mrmlScene.CreateNodeByClass('vtkMRMLTextNode')
    output.UnRegister(None)
    output.SetName("CMD"+genCode())
    output.SetText(string)
    slicer.mrmlScene.AddNode(output)
    igtNode.RegisterOutgoingMRMLNode(output)
    igtNode.PushNode(output)
    slicer.mrmlScene.RemoveNode(output)
    if getParameter('gfmPresentFlag') is 0:
        initStep = None
        ngw = slicer.modules.HMS_NeedleGuideWidget
        if ngw is not None:
            initStep = ngw.initializationStep
        if string == "STAR":
            if getParameter('expectACKFlag') == 1:
                # spoof an ACK first
                if devModeFlag:
                    print 'No fabricator, spoofing an ack'
                ackString = 'ACK_' + str(getParameter('IGTCode'))
                ackSpoof = slicer.vtkMRMLTextNode()
                ackSpoof.SetName(ackString)
                slicer.mrmlScene.AddNode(ackSpoof)
                if initStep is not None:
                    initStep.onMessageReceived(ackSpoof)
                else:
                    if devModeFlag:
                        print 'WARNING: unable to spoof ACK: ', ackString
                slicer.mrmlScene.RemoveNode(ackSpoof)

            # spoof the response to init the fabricator
            if devModeFlag:
                print 'No fabricator, spoofing the Initialization reponse'
            spoof = slicer.mrmlScene.CreateNodeByClass('vtkMRMLIGTLStatusNode')
            spoof.UnRegister(None)
            spoof.SetName(string)
            spoof.SetCode(1)
            spoof.SetSubCode(1)
            spoof.SetStatusString("OK")
            slicer.mrmlScene.AddNode(spoof)
            if devModeFlag:
                print '\tTrying to spoof IGT with string = ', string
            if initStep is not None:
                initStep.onMessageReceived(spoof)
            else:
                if devModeFlag:
                    print 'WARNING: unable to spoof init fabricator!'
            slicer.mrmlScene.RemoveNode(spoof)

# Return the 0 based index of the columnName based the columns list
# of column name/header tuples, -1 on failure to find the columnName
# as first element of any tuple
def getColumnIndex(columns, columnName):
    if columns is None:
        return -1
    for index, nameHeaders in enumerate(columns):
        if nameHeaders[0] == columnName:
            return index
    return -1

# Return just the column headers from the column name/headers list.
def getColumnHeaders(columns):
    return [c[1] for c in columns]

# Set/Get a parameter of the guide grid by name.
# Grids have rows and columns of holes with spacing between the holes.
# The origin is defined as the center of the patient right posterior hole.
# The guide sheet corner points define the default coordinate system, so there is an
# offset to that origin from the grid center hole (when drilling, the diameter of the
# needle guide part defines the limit of the working area on the sheet).
# OriginOffsetX
# OriginOffsetY
# NumberOfHolesPerRow
# NumberOfHolesPerColumn
# SpacingBetweenColumns (mm) - hole center to hole center
# SpacingBetweenRows (mm)
# HoleDiameter - 18 gauge needles are 1.24mm in diameter, with clearance the hole is 1.3mm
def setGridParameter(paramName, paramValue):
    guideSheetCornersID = getParameter('guideSheetCornersID')
    if guideSheetCornersID is None:
        print 'Error: unable to get the parameter for the guide sheet fiducial node'
        return
    guideSheetCornersNode = slicer.util.getNode(guideSheetCornersID)
    if guideSheetCornersNode is None:
        print 'Error: unable to get the guide sheet corners fiducial list node from id', guideSheetCornersID
        return
    guideSheetCornersNode.SetAttribute(paramName, paramValue)

# Get grid parameter as a number, returns None if can't find it
def getGridParameter(paramName):
    guideSheetCornersID = getParameter('guideSheetCornersID')
    if guideSheetCornersID is None:
        return None
    guideSheetCornersNode = slicer.util.getNode(guideSheetCornersID)
    if guideSheetCornersNode is None:
        return None
    value = guideSheetCornersNode.GetAttribute(paramName)
    if value is None:
        return None
    # associated calibration markers file id is a string
    if paramName == 'MarkerConfigurationID':
        return value
    # otherwise return as integer or float
    if paramName == 'NumberOfHolesPerRow' or paramName == 'NumberOfHolesPerColumn':
        return int(value)
    else:
        return float(value)

# Calculate the custom needle guide sheet drilling locations given an
# input fiducial node containing a list of RAS locations.
# Gets the calibration transformation node from the scene.
# Gets the guide sheet corners from the workflow function getGuideSheetCorners.
# Returns a list of ProstateBxLib.DataStructs SheetHole, one per fiducial.
def calcGuideSheetHoles(fiducialNode):
    # def calcGuideSheetHoles(self, zTrans, guideSheet, markerMat):
    sheetHoles = []

    devModeFlag = getParameter('devModeFlag')

    if fiducialNode is None:
        print 'ERROR: no input positions from which to calculate guide sheet holes'
        return sheetHoles

    # Get the calibration transform. The guide sheet center transform is inside the
    # guide sheet transform which is inside the calibration transform, so get the
    # transform to world to apply to the guide sheet corners.
    transformNode = slicer.mrmlScene.GetNodeByID(getParameter('GuideSheetCenterTransformID'))
    if transformNode is None:
        print 'ERROR: cannot calculate guide sheet holes with no calibration transform'
        return sheetHoles

    numberOfPoints = fiducialNode.GetNumberOfFiducials()
    if numberOfPoints is 0:
        if devModeFlag:
            print 'Warning: no points for which to calculate guide sheet holes'
        return sheetHoles

    zTransVMat = vtk.vtkMatrix4x4()
    zTransRet = transformNode.GetMatrixTransformToWorld(zTransVMat)
    if devModeFlag == 1:
        for x in range(4):
            for y in range(4):
                print ' ', zTransVMat.GetElement(x, y),
            print ''

    guideSheetCorners = getGuideSheetCorners()
    if guideSheetCorners is None:
        print 'ERROR: calcGuideSheetHoles: no guide sheet corners!'
        return sheetHoles
    # apply the transform matrix to the corners
    pt1 = zTransVMat.MultiplyPoint([guideSheetCorners[0][0], guideSheetCorners[0][1], guideSheetCorners[0][2], 1.0])
    pt2 = zTransVMat.MultiplyPoint([guideSheetCorners[1][0], guideSheetCorners[1][1], guideSheetCorners[1][2], 1.0])
    pt4 = zTransVMat.MultiplyPoint([guideSheetCorners[3][0], guideSheetCorners[3][1], guideSheetCorners[3][2], 1.0])
    if devModeFlag:
        print '\tpt1 = ', pt1
        print '\tpt2 = ', pt2
        print '\tpt4 = ', pt4
    # normalized vector in RAS along Y from sheet configuration origin
    yarray = [pt2[0] - pt1[0], pt2[1] - pt1[1], pt2[2] - pt1[2]]
    yLength = numpy.linalg.norm(yarray)
    yVector = [yarray[0] / yLength, yarray[1] / yLength, yarray[2] / yLength]
    # RAS along X
    xarray = [pt4[0] - pt1[0], pt4[1] - pt1[1], pt4[2] - pt1[2]]
    xLength = numpy.linalg.norm(xarray)
    xVector = [xarray[0] / xLength, xarray[1] / xLength, xarray[2] / xLength]
    # normal along depth
    normalVector = numpy.cross(xVector, yVector)
    if devModeFlag:
        print '\txVector = ', xVector
        print '\tyVector = ', yVector
        print '\tnormalVector = ', normalVector

    # iterate over the RAS positions
    numberOfPoints = fiducialNode.GetNumberOfFiducials()
    for i in range(numberOfPoints):
        markerPos = [0.0, 0.0, 0.0]
        fiducialNode.GetNthFiducialPosition(i, markerPos)
        # vector of fiducial from guide sheet corner origin
        originToPoint = [markerPos[0] - pt1[0], markerPos[1] - pt1[1], markerPos[2] - pt1[2]]
        # calculating from right posterior corner of guide sheet
        M = originToPoint[0]*xVector[0] + originToPoint[1]*xVector[1] + originToPoint[2]*xVector[2]
        N = originToPoint[0]*yVector[0] + originToPoint[1]*yVector[1] + originToPoint[2]*yVector[2]
        D = originToPoint[0]*normalVector[0] + originToPoint[1]*normalVector[1] + originToPoint[2]*normalVector[2]
        if devModeFlag == 1:
            print('M=%s N=%s D=%s' %(M, N, D))
        # now have the hole in sheet coordinates, 0,0 is corner of reachable area
        hole = SheetHole(x=M, y=N, depth=D)
        hole.normal = normalVector
        sheetHoles.append(hole)

    return sheetHoles

def getGridColumn(columnNumber):
    # Maps columnNumbers 0 to numberOfHolesX into A to
    # Q if numberOfHolesX is 17
    # ColumnNumber increases toward clinician right/patient left
    numberOfHolesX = getGridParameter('NumberOfHolesPerRow')
    if columnNumber < 0 or columnNumber >= numberOfHolesX:
        return '?'
    letterStart = ord('A')
    letterEnd = ord('A') + numberOfHolesX
    columnLetters = list(map(chr, range(letterStart, letterEnd)))
    if getParameter('devModeFlag'):
        print 'getGridColumn: columnLetters = ', columnLetters
    columnLetter = columnLetters[columnNumber]
    return columnLetter

# from the grid letter, get the column index
def getColumnNumber(gridLetter):
    if getParameter('devModeFlag'):
        print 'getColumnNumber: letter = ', gridLetter
    numberOfHolesX = getGridParameter('NumberOfHolesPerRow')
    letterStart = ord('A')
    letterEnd = ord('A') + numberOfHolesX
    columnLetters = list(map(chr, range(letterStart, letterEnd)))
    columnNumber = columnLetters.index(gridLetter)
    if getParameter('devModeFlag'):
        print '\tcolumnNumber = ', columnNumber
    return columnNumber

# For RGS006 onwards
def calculateGridLocation(sheetHole):
    # From the given SheetHole, calculate the corresponding grid column (letter) and row (number).
    # On success returns ['X', 'n']
    # On failure returns a question mark in the corresponding tuple location '?'
    gridLocation = []

    # Calculate the grid column
    # sheet hole position xy is from the corner of the sheet, which is not the origin of the coordinate system
    # col 0 row 0 is no column, results in ?'s
    spacingX = getGridParameter('SpacingBetweenColumns')
    columnNumber = math.floor(sheetHole.x / spacingX)
    columnInteger = int(columnNumber)
    # column integer 0 maps to highest letter
    gridColumn = getGridColumn(columnInteger)

    # Calculate the grid row
    numberOfHolesY = getGridParameter('NumberOfHolesPerColumn')
    spacingY = getGridParameter('SpacingBetweenRows')
    rowsFromBottom = int(math.ceil(sheetHole.y / spacingY))
    row = numberOfHolesY - rowsFromBottom
    if row < 0 or row >= numberOfHolesY:
      gridRow = '?'
    else:
      # 1 index the rows rather than 0 index to avoid confusion between zero and letter O
      # Adding 1 because indexing down from the top row
      gridRow = str(row + 1)

    gridLocation = [gridColumn, gridRow]

    return gridLocation

def getGridColumnPreRGS6(inNum):
    return {
          1 : 'A',
          2 : 'B',
          3 : 'C',
          4 : 'D',
          5 : 'E',
          6 : 'F',
          7 : 'G',
          8 : 'H',
          9 : 'I',
          10 : 'J',
          11 : 'K',
          12 : 'L',
          13 : 'M',
          14 : 'N',
          15 : 'O',
          16 : 'P',
          17 : 'Q',
          18 : 'R',
          19 : 'S',
          20 : 'T',
          21 : 'U',
          22 : 'V',
          23 : 'W',
    }.get(inNum, '?')

def calculateGridLocationPreRGS6(sheetPosition):
    # From the given SheetHole, calculate the corresponding grid column (letter) and row (number).
    # On success returns ['X', 'n']
    # On failure returns a question mark in the corresponding tuple location '?'
    gridLocation = []

    # Calculate the grid column
    # sheet positiion xy is from the corner of the sheet, which is not the origin of the coordinate system
    # col 0 row 0 is no column, results in ?'s
    # - 8.5 : z frame config was slightly off (0.5), would have been -4 if start at col 0, but doubled for starting at column 1 (because grid is larger than guide sheet?)
    # / 4.0: assumes 4mm hole to hole, h and v
    # 1.5 : 0.5 is to round up (consider ceil, Phill had a reason why not to use ceil), 1 is so don't start at 0 but 1
    gridColumn = getGridColumnPreRGS6(int((sheetPosition.x-8.5)/4.0+1.5))

    # Calculate the grid row
    # 24 = number of holes, now 17, minus to number from top in Y
    # -9.5 is becasue drilling of old grid was off by 1mm, should have been 8.5 due to same as columns
    # 4 distance between  holes
    #-1.5 because of the 1mm vertical offset in frame, .5 is to round up, 1 is to stop it from using row 0
    heig = (24 - int((sheetPosition.y-9.5)/4.0+1.5))
    if (heig < 1 or heig > 23):
        gridRow = '?'
    else:
        gridRow = str(heig)

    gridLocation = [gridColumn, gridRow]

    return gridLocation

def setTransformToIdentity(transformNode):
    if transformNode is None:
        return
    if transformNode.GetTransformToParent() is None:
        return
    if transformNode.GetTransformToParent().GetMatrix() is None:
        return
    transformNode.GetTransformToParent().GetMatrix().Identity()

# return a triple with the input transform node's world position,
# [0,0,0] on failure
def getTransformNodeWorldPosition(transformNode):
    if transformNode is None:
        return [0,0,0]
    transformMatrix = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToWorld(transformMatrix)
    thisTransform = vtk.vtkTransform()
    thisTransform.SetMatrix(transformMatrix)
    translation = thisTransform.GetPosition()
    if getParameter('devModeFlag'):
        print 'getTransformNodeWorldPosition: ', translation
    return translation

# Return rotation in degrees around x,y,z world axes for this transform node,
# [0,0,0] on error
def getTransformNodeOrientation(transformNode):
    if transformNode is None:
        return [0,0,0]
    transformMatrix = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToWorld(transformMatrix)
    thisTransform = vtk.vtkTransform()
    thisTransform.SetMatrix(transformMatrix)
    orientation = thisTransform.GetOrientation()
    return orientation

# Set the rotation around X, Y, Z axes for the transform node to 0
# Warning: only have access to set matrix to parent, only call for top
# level nodes in transform chain.
def removeTransformNodeOrientation(transformNode):
    if transformNode is None:
        return
    if transformNode.GetParentTransformNode() is not None:
        popupWarning("W:001 removeTransformNodeOrientation cannot be used on this transform, " + transformNode.GetName() + " " + transformNode.GetID() + ", it is not a top level one (has a parent).")
        return

    # get the translation out to save it
    translation = getTransformNodeWorldPosition(transformNode)

    # put the translation in an identity matrix
    transformMatrix = vtk.vtkMatrix4x4()
    transformMatrix.SetElement(0,3, translation[0])
    transformMatrix.SetElement(1,3, translation[1])
    transformMatrix.SetElement(2,3, translation[2])

    transformNode.SetMatrixTransformToParent(transformMatrix)

def getOrientationString(transformNode):
    # get orientation from node
    orientation = getTransformNodeOrientation(transformNode)
    # format orientation into a standard string
    if len(orientation) != 3:
        return 'Invalid orientation: ' + orientation
    orientationString = '\n  Pitch %.3f degrees\n  Yaw   %.3f degrees\n  Roll  %.3f degrees' % (orientation[0], orientation[1], orientation[2])
    return orientationString

def goToCalibrationStep():
    # Go to the workflow Calibration step.
    # Return True on success, False on failure
    ngw = slicer.modules.HMS_NeedleGuideWidget
    if ngw is None:
        # try again
        ngw = slicer.modules.hms_needleguide.widgetRepresentation().self()
        if ngw is None:
            print 'Unable to get needle guide widget, cannot go to calibration step!'
            return False

    if getParameter('devModeFlag'):
        print 'goToCalibrationStep: workflow running = ', ngw.workflow.isRunning
    if not ngw.workflow.isRunning:
        # try starting it
        ngw.workflow.start()
        slicer.app.processEvents()
        if getParameter('devModeFlag'):
            print '\trunning now = ', ngw.workflow.isRunning

    # Check for the landing screen
    if ngw.landingWidget.visible:
        if getParameter('devModeFlag'):
            print 'Closing landing widget'
        ngw.landingWidget.close()

    # Check if we're already in the calibration setp
    calibrationID = ngw.calibrationStep.id()
    if ngw.workflow.currentStep().id() == calibrationID:
        # already in calibration step
        return True

    # Go via the init step, turning off the guide sheet fabricator if necessary
    initID = ngw.workflow.initialStep().id()

    # Ensure that starting from the init step
    if ngw.workflow.currentStep().id() != initID:
        # try going to the init step
        if getParameter('devModeFlag'):
            print 'Workflow not in Initialization step, trying to go to it'
        ngw.workflow.goToStep(initID)
        if ngw.workflow.currentStep().id() != initID:
            # Try going to Calibration directly in case that works
            if getParameter('devModeFlag'):
                print 'Failed to go to Initialization step, trying direct to Calibration'
            ngw.workflow.goToStep(calibrationID)
            if ngw.workflow.currentStep().id() != calibrationID:
                print 'Failed to get to Calibration step, returning'
                return False
    if getParameter('devModeFlag'):
        print('goToCalibrationStep: Going to Calibration step')
    if not ngw.initializationStep.isConnected():
        ngw.initializationStep.connectButton.clicked()
        slicer.app.processEvents()
    if getParameter('gfmPresentFlag') is 1:
        ngw.initializationStep.gfmPresentCheckButton.checked = False
        ngw.initializationStep.initializeFabricatorButton.clicked()
    if getParameter('devModeFlag'):
        print('goToCalibrationStep: going forward from init')
    ngw.workflow.goForward()
    slicer.app.processEvents()

    # is the observation step present?
    observationID = None
    if hasattr(ngw, 'observationStep'):
        observationID = ngw.observationStep.id()
        if observationID is not None and ngw.workflow.currentStep().id() == observationID:
            if getParameter('devModeFlag'):
                print('goToCalibrationStep: going forward from observation')
            ngw.workflow.goForward()
            slicer.app.processEvents()

    # sanity check
    if ngw.workflow.currentStep().id() != calibrationID:
        print 'goToCalibrationStep: Failed to get to the Calibration step! Currently in ', ngw.workflow.currentStep().id(), '\n\n'
        return False
    else:
        return True

# Reset the 3D camera view to our default
def reset3DCamera():
    view3d = slicer.util.getNode('View1')
    if view3d is not None and view3d.GetRenderMode() != view3d.Orthographic:
        # Parallel projection scale is set from 3d view node FOV when
        # set render mode to orthographic
        view3d.SetRenderMode(view3d.Orthographic)
    cameraNode = slicer.util.getNode('vtkMRMLCameraNode1')
    if cameraNode is not None:
        cameraNode.SetPosition([0,0,-600])
        cameraNode.SetViewUp([0,1,0])

# Set the 3D camera view to focus on the grid
def reset3DCameraOnGrid():
    view3d = slicer.util.getNode('View1')
    if view3d is not None:
        view3d.SetRenderMode(view3d.Orthographic)
    cameraNode = slicer.util.getNode('vtkMRMLCameraNode1')
    if cameraNode is None:
        return
    # get the center of the grid in world
    guideSheetTransformID = getParameter('GuideSheetTransformID')
    if guideSheetTransformID is None:
        print 'Error: unable to get the transform for the guide sheet'
        reset3DCamera()
        return None
    transformNode = slicer.util.getNode(guideSheetTransformID)
    if transformNode is None:
        print 'Error: unable to get the guide sheet transform node with id', guideSheetTransformID
        reset3DCamera()
        return
    transformMatrix = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToWorld(transformMatrix)
    origin = [0,0,0,1]
    center = [0,0,0,1]
    transformMatrix.MultiplyPoint(origin, center)
    cameraNode.SetPosition([center[0],center[1],center[2]-200])
    cameraNode.SetFocalPoint(center[:3])
    cameraNode.SetViewUp([0,1,0])
    # zoom in on the grid with space around it for
    # the guide sheet outline and letters
    cameraScale = 55
    cubeModel = slicer.util.getNode('GreenZoneCube')
    if cubeModel is not None:
        targetZoneBounds = [0,0,0,0,0,0]
        cubeModel.GetRASBounds(targetZoneBounds)
        fovR = abs(targetZoneBounds[1] - targetZoneBounds[0])
        fovA = abs(targetZoneBounds[3] - targetZoneBounds[2])
        # take the max size
        fov = max(fovR, fovA)
        # add 15mm  for the letters and numbers and divide by 2
        cameraScale = (fov + 15.0) / 2.0
    cameraNode.SetParallelScale(cameraScale)
    # Possible bug workaround: when new volumes are loaded, the 3d view's FOV is
    # used to reset the parallel scale. It never gets set away from 200, so
    # reset it now so that it doesn't zoom when new volumes come in
    if view3d is not None:
        view3d.SetFieldOfView(cameraScale)

# Iterate through all the slice composite nodes in the scene
# and set the slice intersection visibility for the slice viewers.
def setSliceIntersections(visible):
    compositeNodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLSliceCompositeNode")
    numNodes = compositeNodes.GetNumberOfItems()
    for n in range(numNodes):
        compositeNode = compositeNodes.GetItemAsObject(n)
        if compositeNode is not None:
            compositeNode.SetSliceIntersectionVisibility(visible)

# Iterate through all the slice composite nodes in the scene
# and set the volume propagation to turn on or off the showing of
# newly loaded volumes.
# When setting our volumes active, the utility methods above will set
# this back to True.
def setShowOnLoad(show):
    compositeNodes = slicer.mrmlScene.GetNodesByClass("vtkMRMLSliceCompositeNode")
    numNodes = compositeNodes.GetNumberOfItems()
    for n in range(numNodes):
        compositeNode = compositeNodes.GetItemAsObject(n)
        if compositeNode is not None:
            compositeNode.SetDoPropagateVolumeSelection(show)
    slicer.app.processEvents()

# Calculate the hash of the plainText input and return it.
# Returns None on failure.
def hashString(plainText):
    if plainText is None or plainText == '':
        print 'hashString: no input'
        return None
    # TBD: figure out why can't encode unicode, works from python console
    # unicodeText = unicode(plainText, 'utf-8')
    byteText = qt.QByteArray()
    byteText.append(plainText)

    byteHash = qt.QCryptographicHash.hash(byteText, qt.QCryptographicHash.Sha1)
    hashText = str(byteHash.toHex())

    if getParameter('devModeFlag'):
        print 'hashString = ', hashText

    return hashText

# Use the markups logic to jump all slice viewers to the given position.
def jumpSlices(pos):
    if pos is None:
        if getParameter('devModeFlag'):
            print 'jumpSlices: no position given'
        return
    if len(pos) < 3:
        if getParameter('devModeFlag'):
            print 'jumpSlices: position invalid, need 3 RAS coordinates: ', pos
        return

    markupsLogic = slicer.modules.markups.logic()
    # last argument is centered, pass False for offset
    markupsLogic.JumpSlicesToLocation(pos[0], pos[1], pos[2], False)

# Hide the windows task bar if flag is True, show if False.
# Try to hide the start button as well.
def hideTaskBar(flag):
    if getParameter('devModeFlag'):
        print 'hideTaskBar: flag = ', flag

    trayName = unicode("Shell_traywnd")
    START_ATOM = wintypes.LPCWSTR("0xC017")
    startButtonName = START_ATOM.value

    # hide and show flags hard coded as defined as SW_HIDE and SW_SHOW in pywin32 package
    sw_hide = 0
    sw_show = 5

    user32 = ctypes.WinDLL("user32")
    # system tray
    trayWindow = user32.FindWindowW(trayName, None)
    # start button
    startButton = user32.FindWindowW(startButtonName, None)
    if getParameter('devModeFlag'):
        print 'HideTaskBar: tray = ', trayWindow, ', start = ', startButton

    if flag:
        # hide it
        if trayWindow:
            user32.ShowWindow(trayWindow, sw_hide)
        if startButton:
            user32.ShowWindow(startButton, sw_hide)
    else:
        # show it
        if trayWindow:
            user32.ShowWindow(trayWindow, sw_show)
        if startButton:
            user32.ShowWindow(startButton, sw_show)

# Shut down the computer, asking to make sure.
def shutDownComputer():
    # custom pop up to make sure it can go over the landing widget
    landingWidget = None
    ngw = slicer.modules.HMS_NeedleGuideWidget
    if ngw is not None:
        landingWidget = ngw.landingWidget

    msgBox = ctk.ctkMessageBox(landingWidget)
    msgBox.setWindowTitle("Verify Shut Down")
    resourcePath = getParameter('resources')
    if resourcePath is not None:
        questionPixmap = qt.QPixmap(os.path.join(resourcePath, "Icons/Small/sm_blue1help.png"))
        msgBox.setIconPixmap(questionPixmap)
    else:
        msgBox.setIcon(qt.QMessageBox.Question)
    questionString = 'This will turn off the computer, losing any unsaved Reports.\n\nAre you sure?'
    msgBox.setText(questionString)
    msgBox.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No)
    msgBox.setDefaultButton(qt.QMessageBox.No)
    msgBox.setWindowFlags(msgBox.windowFlags() | qt.Qt.WindowStaysOnTopHint)
    pressed = msgBox.exec_()
    if pressed == qt.QMessageBox.No:
      return

    print 'Shutting down...'
    # Hide the landing widget so any prompts can be seen
    if landingWidget is not None:
        landingWidget.close()
    os.system('shutdown -s')
    # that gets the system ready and then shuts down,
    # don't close the software as that will give a short
    # period of access to the desktop

# Utility function to set a model node's visibility
def setModelVisibilityByID(id, visible):
    if id is None or id == '':
        return
    mnode = slicer.mrmlScene.GetNodeByID(id)
    if mnode != None:
        dnode = mnode.GetDisplayNode()
        if dnode != None:
            dnode.SetVisibility(visible)

# Update a parameter node flag from a check box setting. The node flag is a
# string, the check is an int 0 or 1 (works with true or false as well)
def updateParameterFlagFromChecked(parameterString, checked):
    flag = getParameter(parameterString)
    if flag is None:
        print 'ERROR: invalid parameteter passed to updateParameterFlagFromChecked: ', parameterString
        return
    if getParameter('devModeFlag') == 1:
        print '\tchecked = ',checked, ', flag = ',flag
    if flag and not checked:
        setParameter(parameterString, '0')
    elif not flag and checked:
        setParameter(parameterString, '1')

# Get the installed checksum generator, returns None on failure
def getFCIV():
    ng = slicer.modules.hms_needleguide
    needleGuidePythonPath = os.path.dirname(ng.path)
    needleGuideModulePath = os.path.dirname(os.path.dirname(os.path.dirname(needleGuidePythonPath)))
    needleGuideBinPath = os.path.join(needleGuideModulePath, 'bin')
    if getParameter('devModeFlag'):
        print 'Looking for fciv in bin path: ', needleGuideBinPath
    fcivExe = os.path.normpath(os.path.join(needleGuideBinPath, 'fciv.exe'))
    if not os.path.exists(fcivExe):
        return None
    return fcivExe

# utility method to generate valid checksums file, only works if in
# developer mode
def generateChecksums():
    if not getParameter('devModeFlag'):
        popupError("generateChecksums", "E:002 cannot run if not in developer mode")
        return

    from subprocess import call

    fcivExe = getFCIV()
    currentPath = os.path.realpath(__file__)
    print 'current path = ', currentPath
    binaryDirName = os.path.dirname(os.path.dirname(currentPath))
    print '\tbinaryDirName = ', binaryDirName

    resourcePath = getParameter('resources')
    validCheckSumsFilePath = os.path.join(resourcePath, 'Config', 'valid_checksums.txt')
    print 'Writing current checksums to ', validCheckSumsFilePath
    validCheckSumsFile = open(validCheckSumsFilePath, 'w')

    # Get the list of files to checksum
    result = listOfFilesToChecksum(binaryDirName)

    # use the checksum exe's directory as a place to write temp checksum files
    checkSumDir = os.path.dirname(fcivExe)
    if not os.access(checkSumDir, os.W_OK):
      popupError("Unable to write", "E:003 Unable to write to checksums directory " + checkSumDir)
      return False
    checkSumFilePath = os.path.join(checkSumDir, 'checksums.txt')

    # subprocess call flag to avoid console popping up on win10
    CREATE_NO_WINDOW = 0x08000000

    print 'Current checksums:\n'
    for fileName in result:
      checkSumFile = open(os.path.normpath(checkSumFilePath), 'w')
      returnFlag = call([fcivExe, '-md5', fileName, '-wp'], stdout=checkSumFile, creationflags = CREATE_NO_WINDOW)
      checkSumFile.close()
      if returnFlag == 0:
        # parse the file for the checksum
        readCheckSumFile = open(os.path.normpath(checkSumFilePath), 'r')
        lines = readCheckSumFile.readlines()
        readCheckSumFile.close()
        for line in lines:
          if len(line) < 2:
            continue
          if not (line[0] == '/' and line[1] == '/'):
            checkSum, fileName = str.split(line)
            print fileName, checkSum
	    validCheckSumsFile.write(fileName + " " + checkSum + "\n")

    validCheckSumsFile.close()

# Get the installed password protected zipfile generator
# Returns None on failure
def getZip():
    ng = slicer.modules.hms_needleguide
    needleGuidePythonPath = os.path.dirname(ng.path)
    needleGuideModulePath = os.path.dirname(os.path.dirname(os.path.dirname(needleGuidePythonPath)))
    needleGuideBinPath = os.path.join(needleGuideModulePath, 'bin')
    if getParameter('devModeFlag'):
        print 'Looking for 7zip in bin path: ', needleGuideBinPath
    zipExe = os.path.normpath(os.path.join(needleGuideBinPath, '7za.exe'))
    if not os.path.exists(zipExe):
        return None
    return zipExe

# Zip the .txt files in a directory with the given password into an
# archive at the absolute location zipFileName
# Returns True or False
def passwordZipTxt(directoryName, password, zipFileName):
    if not os.path.exists(directoryName):
        slicer.util.delayDisplay("Cannot find directory to zip: " + directoryName)
        return False
    zipExe = getZip()
    if zipExe is None:
        slicer.util.delayDisplay("No zip executable found!")
        return False
    # get the list of files in the directory
    import glob
    from subprocess import call
    txtList = [y for x in os.walk(directoryName) for y in glob.glob(os.path.join(x[0], '*.txt'))]
    # also find html reports
    htmlList = [y for x in os.walk(directoryName) for y in glob.glob(os.path.join(x[0], '*.html'))]
    # also find pdf reports
    pdfList = [y for x in os.walk(directoryName) for y in glob.glob(os.path.join(x[0], '*.pdf'))]
    # also find fiducial files
    fidsList = [y for x in os.walk(directoryName) for y in glob.glob(os.path.join(x[0], '*.csv'))]
    fileList = txtList + htmlList + pdfList + fidsList
    CREATE_NO_WINDOW = 0x08000000
    rc = call([zipExe, 'a', '-p'+password, '-y', zipFileName] + fileList, creationflags = CREATE_NO_WINDOW)

    if rc != 0:
        popupError("Archive creation error", "Error running " + zipExe + " on directory " + directoryName)
        return False

    # check that the zip file exists
    if not os.path.exists(zipFileName):
        popupError("Archive error", "Error archiving the reports in " + directoryName)
        return False

    # remove the unprotected files
    for fileName in fileList:
        print 'Deleting archived ', fileName
        os.remove(os.path.normpath(fileName))

    # check that the text files are gone
    postDeleteList = [y for x in os.walk(directoryName) for y in glob.glob(os.path.join(x[0], '*.*'))]
    if len(postDeleteList) != 0:
        popupError("Files unprotected", "Failed to remove plain text log files after making a password protected archive from " + directoryName)
        return False

    return True

def listOfFilesToChecksum(binaryDirName):
    # get all the python compiled files
    import glob
    result = [y for x in os.walk(binaryDirName) for y in glob.glob(os.path.join(x[0], '*.pyc'))]

    # add grid configuration file
    result.append(getParameter('sheetFile'))

    # add the program settings file
    result.append(getParameter('settings'))

    # add marker detection exe
    markerDetection = slicer.modules.hms_marker_detection
    markerDetectionExe = os.path.normpath(markerDetection.path)
    result.append(markerDetectionExe)

    # add markers configuration file
    result.append(getParameter('calibrationFile'))

    # add storescp and the batch file that starts it and HMS
    # Manual client from the Harmonus_IGT dir
    dcmtkBat = getParameter('dcmtk')
    harmonusIGTDir = os.path.dirname(dcmtkBat)
    storescpPath = os.path.join(harmonusIGTDir, "storescp.exe")
    hmsManualClientPath = os.path.join(harmonusIGTDir, "HMS_ManualClient.exe")
    for p in [dcmtkBat, storescpPath, hmsManualClientPath]:
      result.append(os.path.normpath(p))

    # add Slicer
    result.append(os.path.normpath(slicer.app.launcherExecutableFilePath))

    return result

def checkVector(dicomValues, expectedValues, epsilon):
    if len(dicomValues) != 3 or len(expectedValues) != 3:
        return False
    # convert to float
    inputVector = [float(dicomValues[0]), float(dicomValues[1]), float(dicomValues[2])]
    vectorLength =  numpy.sqrt(pow(inputVector[0],2) + pow(inputVector[1],2) + pow(inputVector[2],2))
    if vectorLength != 0.0:
        inputVector = inputVector / vectorLength
    expectedVectorStrings = expectedValues
    expectedVector = [float(expectedVectorStrings[0]), float(expectedVectorStrings[1]), float(expectedVectorStrings[2])]
    vectorDiff = numpy.sqrt(pow((inputVector[0] - expectedVector[0]),2) + pow((inputVector[1] - expectedVector[1]),2) + pow((inputVector[2] - expectedVector[2]),2))
    if vectorDiff > epsilon:
        return False
    return True

# Return a standard format string for a position consisting of three floats.
# Puts round brackets around the comma separated numbers.
# places used as a number of places paramter to build the format string.
def formatPositionString(pos, places=2):
    if len(pos) != 3:
        return ''
    formatString = '(%.' + str(places) + 'f, %.' + str(places) + 'f, %.' + str(places) + 'f)'
    formattedString = formatString % (pos[0], pos[1], pos[2])
    return formattedString

# Format a single number string
def formatLengthString(length, places=1):
    formatString = '%.' + str(places) + 'f'
    formattedString = formatString % (length)
    return formattedString

# Write a string to the given file in the reports directory and append to status box.
# Opens the file for writing if it doesn't exist yet, otherwise appends.
# logFile: name of a file in the reports directory
# message: string to time stamp and add to logFile and status box
def writeLog(logFileName, message):
    reportDir = getParameter('reports')
    if reportDir is None:
        popupError("Reports", "Reports directory is not set!")
        return
    if os.path.exists(reportDir) == False:
        os.mkdir(reportDir)
    if os.path.isabs(logFileName):
        logPath = os.path.join(reportDir, os.path.basename(logFileName))
    else:
        logPath = os.path.join(reportDir, logFileName)
    if os.path.exists(logPath):
        logFile = open(logPath, 'a')
    else:
        logFile = open(logPath,'w')
    logFile.write(getTimeString() + "\n" + message + "\n\n")
    logFile.close()

# Utility method to set the text and tooltip on a label widget that holds
# a volume name. Text is truncated to keep the GUI sizing consistent, so
# add the full text to a tooltip as well.
# volumeLabel: input QLabel
# txt: text to set on the label's text and toolTip fields
def setVolumeLabel(volumeLabel, txt):
    if volumeLabel is None:
        return
    volumeLabel.setText(txt)
    volumeLabel.toolTip = txt

# Replace disallowed characters in a potential file name with dashes.
# Works just on the file base name and returns the path to it unchanged
# if passed in.
# On Windows, legal file names may not have the following characters:
# < > : " / \ | ? *
def fileNameWithDashes(inName):
    outName = os.path.basename(inName)
    for illegalChar in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        outName = outName.replace(illegalChar, '-')
    return os.path.join(os.path.dirname(inName), outName)

# The current vtkMRMLMarkupsFiducialNode doesn't have a good way to
# associate more text than an associated node id, which is used to
# keep track of on which volume the fiducial was placed. This program
# needs to track an association between two lists of fiducials that
# has to get saved to disk, as well as notes on fiducials. Use the
# description field to store both for now using these utility methods.
# get methods return empty strings if invalid node or not found
def getNthFiducialNoteAndID(fiducialNode, n):
    noteAndID = ['', '']
    if fiducialNode is None:
        return noteAndID
    description = fiducialNode.GetNthMarkupDescription(n)
    if description.find(" ||| ") != -1:
        noteAndID = description.split(" ||| ")
    else:
        # either legacy with one or other of note, id, or empty string
        if len(description) == 0:
            noteAndID = ['', '']
        else:
            # is there an id in the string?
            if description.find('vtkMRMLMarkupsFiducialNode_') != -1:
                noteAndID = ['', description]
            else:
                noteAndID = [description, '']
    return noteAndID

def getNthFiducialNote(fiducialNode, n):
    if fiducialNode is None:
        return ''
    noteAndID = getNthFiducialNoteAndID(fiducialNode, n)
    return noteAndID[0]

def getNthFiducialID(fiducialNode, n):
    if fiducialNode is None:
        return ''
    noteAndID = getNthFiducialNoteAndID(fiducialNode, n)
    return noteAndID[1]

def setNthFiducialNoteAndID(fiducialNode, n, noteAndID):
    if fiducialNode is None:
        return
    if len(noteAndID) != 2:
        return
    descriptionString = noteAndID[0] + " ||| " + noteAndID[1]
    fiducialNode.SetNthMarkupDescription(n, descriptionString)

def setNthFiducialNote(fiducialNode, n, note):
    if fiducialNode is None:
        return
    noteAndID = getNthFiducialNoteAndID(fiducialNode, n)
    noteAndID[0] = note
    setNthFiducialNoteAndID(fiducialNode, n, noteAndID)

def setNthFiducialID(fiducialNode, n, id):
    if fiducialNode is None:
        return
    noteAndID = getNthFiducialNoteAndID(fiducialNode, n)
    noteAndID[1] = id
    setNthFiducialNoteAndID(fiducialNode, n, noteAndID)

# Return the number of patients that are in the DICOM database.
# Returns 0 on invalid database.
def numberOfPatientsInDB(dicomDatabase):
    if dicomDatabase is None:
        return 0
    patients = dicomDatabase.patients()
    return len(patients)

# Examines the DICOMLoad folder for CTK DICOM database directories
# that contain patient data and returns an array with entries for
# each database containing the path, number of patients, and last
# modified time.
# Will include the current DB that's currently in use, but don't
# create a new connection to it.
def getPatientDBs():
    dicomLoadDBs = []
    # get the root directory from where the DICOMs are loaded
    dbsDir = getParameter('DICOMLoad')
    # is the parameter set?
    if dbsDir is None or dbsDir == '':
        return dicomLoadDBs
    # does the directory exist?
    dbsDir = os.path.normpath(dbsDir)
    if not os.path.exists(dbsDir):
        return dicomLoadDBs
    dirsToCheck = os.listdir(dbsDir)
    ngw = slicer.modules.hms_needleguide.widgetRepresentation().self()
    currentDB = os.path.normpath(ngw.dicomDatabase.databaseFilename)
    for dir in dirsToCheck:
        fullPath = os.path.join(dbsDir, dir)
        sqlPath = os.path.normpath(os.path.join(fullPath, 'ctkDICOM.sql'))
        sqlExists = os.path.exists(sqlPath)
        dicomPath = os.path.normpath(os.path.join(fullPath, 'dicom'))
        dicomExists = os.path.exists(dicomPath)

        if sqlExists and dicomExists and os.path.isdir(dicomPath):
            numPatients = 0
            lastModified = None
            # check when last modified
            lastModified = qt.QFileInfo(sqlPath).lastModified()
            # check it for patients
            isCurrentDBDir = (currentDB == sqlPath)
            if isCurrentDBDir:
                if getParameter('devModeFlag') == 1:
                    print 'Found current slicer dir:', dicomPath
                numPatients = numberOfPatientsInDB(ngw.dicomDatabase)
            else:
                # make a new connection
                thisDB = ctk.ctkDICOMDatabase()
                if thisDB.lastError == '':
                    thisDB.openDatabase(sqlPath, "PATIENT-COUNT")
                    if thisDB.lastError == '':
                        numPatients = numberOfPatientsInDB(thisDB)
                    else:
                        popupWarning('Last error on opening database: ' + thisDB.lastError)
                    thisDB.closeDatabase()
                else:
                    popupWarning('Created dicom database, last error = ' + thisDB.lastError)
            dicomLoadDBs.append([sqlPath, numPatients, lastModified])
    if len(dicomLoadDBs) == 0:
        return dicomLoadDBs
    # sort by last modified time
    dicomLoadDBs.sort(key = lambda x: x[2])
    return dicomLoadDBs
