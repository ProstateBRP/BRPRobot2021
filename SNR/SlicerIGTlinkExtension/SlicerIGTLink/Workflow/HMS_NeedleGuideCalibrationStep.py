import vtk, qt, ctk, slicer
import workflowFunctions as workflowFunctions
import csv
import numpy
import sys
import datetime
from ProstateBxLib.DataStructs import CalibrationMarker
from ProstateBxLib.StyleUtils import colorPalette

import os

class HMS_NeedleGuideCalibrationStep(ctk.ctkWorkflowWidgetStep):

    def __init__(self, stepID):
        self.initialize(stepID)

        # hide the unnecessary buttons in the marker detection gui
        # so that only the workflow button can run it
        qt.QTimer.singleShot(0, self.killButtons)

        self.setName('Calibration')
        self.setDescription('Register the Calibration scan.')

        self.logFileName ='3CALIBRATION.txt'

        # to get at the qsettings
        self.ngw = slicer.modules.HMS_NeedleGuideWidget
        self.optionsGroup = 'zframe/'

        self.zTransNode = None
        self.zTransNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
        self.zTransNode.UnRegister(None)
        self.zTransNode.SetName('CalibrationTransform')
        slicer.mrmlScene.AddNode(self.zTransNode)
        workflowFunctions.setParameter('CalibrationTransformNodeID', self.zTransNode.GetID())

        # Zcalibration ROI
        self.zFrameROI = None
        self.zFrameROIAddedObserverTag = None
        self.zFrameROIDisplayTag = None

        # the transform between the centers of calibration configuration markers and the guide sheet
        # it will be applied to the guide sheet as well as the zTransNode
        self.guideSheetTransformNode = None
        self.guideSheetTransformNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
        self.guideSheetTransformNode.UnRegister(None)
        self.guideSheetTransformNode.SetName('GuideSheetTransform')
        slicer.mrmlScene.AddNode(self.guideSheetTransformNode)
        workflowFunctions.setParameter('GuideSheetTransformID', self.guideSheetTransformNode.GetID())

        # To scale and shift the guide sheet holes model
        self.guideSheetHolesTransformNode = slicer.vtkMRMLLinearTransformNode()
        self.guideSheetHolesTransformNode.SetName('GuideSheetHolesTransform')
        slicer.mrmlScene.AddNode(self.guideSheetHolesTransformNode)
        workflowFunctions.setParameter('GuideSheetHolesTransformID', self.guideSheetHolesTransformNode.GetID())

        # The translation between the center of the guide sheet and it's origin, for use
        # when calculating target zone and grid coordinates
        self.guideSheetCenterTransformNode = slicer.vtkMRMLLinearTransformNode()
        self.guideSheetCenterTransformNode.SetName('GuideSheetCenterTransform')
        slicer.mrmlScene.AddNode(self.guideSheetCenterTransformNode)
        workflowFunctions.setParameter('GuideSheetCenterTransformID', self.guideSheetCenterTransformNode.GetID())

        self.regSuccess = None
        self.regSuccess = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
        self.regSuccess.UnRegister(None)
        self.regSuccess.SetName('regSuccess')
        slicer.mrmlScene.AddNode(self.regSuccess)
        workflowFunctions.setParameter('RegSuccessNodeID', self.regSuccess.GetID())
        self.regSuccess = slicer.util.getNode('regSuccess')
        self.goodRegistration = False
        self.registrationUserVerified = False

        # Verify registration message box needs to be persistent
        self.verifyRegistrationMsgBox = None

        self.cliObserver = None

        self.calibrationInputVolumeNode = None
        self.calibrationOutLabelMapNode = None
        self.calibrationOutLabelDisplayNode = None
        self.volumeRenderingDisplayNode = None

        self.calibrationButton = None

        self.calibrationMarkers = None
        self.calibrationMarkerPath = None

        self.guideSheetCenter = numpy.zeros(3)
        self.calibratorModelNode = None

        # set from marker configuration file
        self.markerConfigurationDescription = None
        self.markerConfigurationID = None
        self.markerConfigurationGridID = None
        self.markersCenter = numpy.zeros(3)

        # translation between calibration markers and guide sheet corners centers
        self.markersToSheetTranslation = numpy.zeros(3)

        # set from guide sheet configuration file
        self.guideSheetConfigurationDescription = None
        self.guideSheetConfigurationID = None

        # create a custom layout
        self.customLayout = ("<layout type=\"horizontal\">"
                        "  <item>"
                        "   <view class=\"vtkMRMLSliceNode\" singletontag=\"Red\">"
                        "    <property name=\"orientation\" action=\"default\">Axial</property>"
                        "    <property name=\"viewlabel\" action=\"default\">R</property>"
                        "    <property name=\"viewcolor\" action=\"default\">#F34A33</property>"
                        "   </view>"
                        "  </item>"
                        " <item>"
                        "  <view class=\"vtkMRMLViewNode\" singletontag=\"1\">"
                        "    <property name=\"viewlabel\" action=\"default\">1</property>"
                        "  </view>"
                        " </item>"
                        "</layout>")
      
        self.customLayoutId = slicer.vtkMRMLLayoutNode.SlicerLayoutUserView + 34

        # save it for other steps to use
        workflowFunctions.setParameter('Red3DViewID', str(self.customLayoutId))

        # will watch the parameter node for changes in the selected calibration scan
        self.parameterNodeModifiedTag = None

        # UI elements to be init by createUserInterface
        self.widget = None
        self.sheetConfigPathEdit = None
        self.calibrationConfigPathEdit = None

        # Calibration settings that need to be saved/restored as integers
        self.integerCalibrationSettings = ['startSlice', 'endSlice', 'minFrameLocks', 'peakRadius', 'maxBadPeaks', 'burnFlag', 'recursionLimit', 'binsPerDimension', 'histogramUpperBound', 'histogramAutoBounds']

    def killButtons(self):
        pass

    def createUserInterface(self):
        # A custom layout for the Calibration
        layoutManager = slicer.app.layoutManager()
        layoutLogic = layoutManager.layoutLogic()
        layoutNode = layoutLogic.GetLayoutNode()
        layoutNode.AddLayoutDescription(self.customLayoutId, self.customLayout)
        layoutNode.SetViewArrangement(self.customLayoutId)

    
        # uses the marker detection CLI GUI (as advanced)
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.widget = workflowFunctions.loadUI('HMS_NeedleGuideCalibration.ui')
        if self.widget is None:
            print 'ERROR: unable to load Calibration step UI file'
            return
        layout.addWidget(self.widget)


        # Calibration area
        calibrationCollapsibleButton = ctk.ctkCollapsibleButton()
        calibrationCollapsibleButton.text = "Calibration"
        calibrationLayout = qt.QVBoxLayout(calibrationCollapsibleButton)
        

        # run registration CLI module with these settings
        calibrationGroupBox = workflowFunctions.get(self.widget, "calibrationGroupBox")
        self.startSliceSliderWidget = workflowFunctions.get(self.widget, "startSliceSliderWidget")
        self.endSliceSliderWidget = workflowFunctions.get(self.widget, "endSliceSliderWidget")

        self.minFrameLocksSliderWidget = workflowFunctions.get(self.widget, "minFrameLocksSliderWidget")
        # Connect the changed value signal to a slot that will update the parameter node and qsettings for the correct variable.
        self.minFrameLocksSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('minFrameLocks', value))

        self.peakRadiusSliderWidget = workflowFunctions.get(self.widget, "peakRadiusSliderWidget")
        self.peakRadiusSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('peakRadius', value))

        self.maxBadPeaksSliderWidget = workflowFunctions.get(self.widget, "maxBadPeaksSliderWidget")
        self.maxBadPeaksSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('maxBadPeaks', value))

        self.offPeakPercentSliderWidget = workflowFunctions.get(self.widget, "offPeakPercentSliderWidget")
        self.offPeakPercentSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('offPeakPercent', value))

        self.maxStdDevPosSliderWidget = workflowFunctions.get(self.widget, "maxStdDevPosSliderWidget")
        self.maxStdDevPosSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('maxStdDevPos', value))


        self.burnFlagCheckBox = workflowFunctions.get(self.widget, "burnFlagCheckBox")
        self.burnFlagCheckBox.connect('toggled(bool)', lambda value: self.onRegistrationWidgetChanged('burnFlag', value))

        self.burnThresholdPercentSliderWidget = workflowFunctions.get(self.widget, "burnThresholdPercentSliderWidget")
        self.burnThresholdPercentSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('burnThresholdPercent', value))

        self.burnSurroundPercentSliderWidget = workflowFunctions.get(self.widget, "burnSurroundPercentSliderWidget")
        self.burnSurroundPercentSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('surroundPercent', value))

        self.burnRecursionLimitSliderWidget = workflowFunctions.get(self.widget, "burnRecursionLimitSliderWidget")
        self.burnRecursionLimitSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('recursionLimit', value))

        self.burnHistogramBinsSliderWidget = workflowFunctions.get(self.widget, "burnHistogramBinsSliderWidget")
        self.burnHistogramBinsSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('binsPerDimension', value))

        self.burnHistogramUpperBoundSliderWidget = workflowFunctions.get(self.widget, "burnHistogramUpperBoundSliderWidget")
        self.burnHistogramUpperBoundSliderWidget.connect('valueChanged(double)', lambda value: self.onRegistrationWidgetChanged('histogramUpperBound', value))

        self.burnHistogramAutoBoundsCheckBox = workflowFunctions.get(self.widget, "burnHistogramAutoBoundsCheckBox")
        self.burnHistogramAutoBoundsCheckBox.connect('toggled(bool)', lambda value: self.onRegistrationWidgetChanged('histogramAutoBounds', value))

        # Set from the settings rather than relying on the .ui file to have been updated
        self.updateRegistrationWidgetsFromSettings()

        # Button to reset the widgets to defaults
        self.resetToDefaultsButton = workflowFunctions.get(self.widget, "resetToDefaultsButton")
        self.resetToDefaultsButton.connect('clicked(bool)', self.onResetToDefaultsButton)
        workflowFunctions.colorPushButtonFromPalette(self.resetToDefaultsButton, 'Secondary')

        # Calibration volume, set from DICOM assignment window
        self.calibrationInputVolumeLabel = workflowFunctions.get(calibrationGroupBox, "CalibrationScanLabel")

        # Calibration button (needed before trigger selecting an input volume)
        self.calibrationButton = workflowFunctions.get(self.widget, "CalibrationButton")
        workflowFunctions.setButtonIcon(self.calibrationButton, 'Large/lg_calibrate.png')
        self.calibrationButton.connect('clicked(bool)', self.onCalibrationButton)
        workflowFunctions.colorPushButtonFromPalette(self.calibrationButton, 'Primary')

        # Add ROI button
        self.addROIButton = workflowFunctions.get(self.widget, "AddROIButton")
        self.addROIButton.connect('clicked(bool)',self.onAddROI)
        workflowFunctions.colorPushButtonFromPalette(self.addROIButton, 'Secondary')
        # Reset the ROI button
        self.resetROIButton = workflowFunctions.get(self.widget, "ResetROIButton")
        self.resetROIButton.connect('clicked(bool)',self.onResetROI)
        workflowFunctions.colorPushButtonFromPalette(self.resetROIButton, 'Secondary')
        # ROI visibility button
        self.roiVisibleButton = workflowFunctions.get(self.widget, "ROIVisibleToolButton")
        self.roiVisibleButton.connect('toggled(bool)', self.onROIVisibleButtonToggled)

        # Enable ROI
        self.addROIButton.enabled = True
        self.roiVisibleButton.enabled = True

        # Configuration options
        self.sheetConfigPathEdit = workflowFunctions.get(self.widget, "sheetPathLineEdit")
        self.sheetConfigPathEdit.connect('currentPathChanged(QString)', self.onSheetConfigPathChanged)

        self.calibrationConfigPathEdit = workflowFunctions.get(self.widget, "calibrationPathLineEdit")
        self.calibrationConfigPathEdit.connect('currentPathChanged(QString)', self.onCalibrationConfigPathChanged)

        sheetFilePath = workflowFunctions.getParameter('sheetFile')
        # print 'sheetFilePath = ',sheetFilePath
        if (sheetFilePath is not None and os.path.isfile(sheetFilePath)):
            # and workflowFunctions.get(self.widget, 'sheetFromFile').checked):
            self.sheetConfigPathEdit.setCurrentPath(sheetFilePath)
            # self.loadSheetConfigFile(sheetFilePath)
        else:
            self.sheetConfigPathEdit.setCurrentPath("")

        calibrationFilePath = workflowFunctions.getParameter('calibrationFile')
        if (calibrationFilePath is not None and os.path.isfile(calibrationFilePath)):
            self.calibrationConfigPathEdit.setCurrentPath(calibrationFilePath)
        else:
            print 'WARNING: did not find calibration configuration file: ',calibrationFilePath
            if calibrationFilePath is not None:
                workflowFunctions.popupWarning("W:301 WARNING: did not find calibration configuration file: " + calibrationFilePath)
            else:
                workflowFunctions.popupWarning("W:302 WARNING: calibration configuration file not set yet.")
            self.calibrationConfigPathEdit.setCurrentPath("")

        # Check the ids of the hardware that each configuration file expects to work with, if set.
        if not self.checkHardwareIDs():
            self.writeLog("Hardware ID mismatch.")

        # lock down the configuration file paths and advanced options, depending
        # on the admin panel setting the parameter node flag
        if workflowFunctions.getParameter('lockCalibrationFlag'):
            self.enableCalibrationOptions(0)
        else:
            self.enableCalibrationOptions(1)

        # Display options

        self.showCalibratorCheckBox = workflowFunctions.get(self.widget, "showCalibratorCheckBox")
        self.showCalibratorCheckBox.connect('toggled(bool)', self.onShowCalibrator)
        self.showCalibratorCheckBox.checked = workflowFunctions.getParameter('CALIBRATOR_VIS_Flag')

        self.showVolumeRenderingCheckBox = workflowFunctions.get(self.widget, "showVolumeRenderingCheckBox")
        self.showVolumeRenderingCheckBox.connect('toggled(bool)', self.onShowVolumeRendering)

        self.showLabelMapCheckBox = workflowFunctions.get(self.widget, "showLabelMapCheckBox")
        self.showLabelMapCheckBox.checked = workflowFunctions.getParameter('CALIBRATOR_LABELS_Flag')
        self.showLabelMapCheckBox.connect('toggled(bool)', self.onShowLabelMap)


        # Get the collapsible group to hide the calibration options.
        markerDetectionCollapsibleButton = workflowFunctions.get(self.widget, "markerDetectionCollapsibleGroupBox")

        markerDetectionCollapsibleButton.collapsed = True

        # add progress bar from the marker detection GUI
        markerDetectionGUI = slicer.modules.hms_marker_detection.widgetRepresentation()
        self.progressBar = markerDetectionGUI.findChild('qSlicerCLIProgressBar')
        self.progressBar.progressVisibility = self.progressBar.AlwaysVisible
        # adding it to the advanced options area so can lock down
        # the registration parameters
        markerDetectionCollapsibleButton.layout().addWidget(self.progressBar)

    def onEntry(self, comingFrom, transitionType):
        comingFromId = "None"
        if comingFrom:
            comingFromId = comingFrom.id()
        super(HMS_NeedleGuideCalibrationStep, self).onEntry(comingFrom, transitionType)

        layoutNode = slicer.util.getNode('Layout')

        layoutNode.SetViewArrangement(self.customLayoutId)
        # pause to process events in case the attempt at calibration
        # goes too fast and interrupts the layout change
        slicer.app.processEvents()

        workflowFunctions.sendIGTString("FRAM")

        self.calibrationScanDICOMID = workflowFunctions.getParameter('calibrationScanDICOMID')
        "CalibrationStep: checking calibration scan id"
        if self.calibrationScanDICOMID is not None:
          workflowFunctions.setActiveVolume(self.calibrationScanDICOMID)
          dicomNode = slicer.mrmlScene.GetNodeByID(self.calibrationScanDICOMID)
          workflowFunctions.setVolumeLabel(self.calibrationInputVolumeLabel, dicomNode.GetName())

          if workflowFunctions.getParameter('regOnceFlag') is 1:
            self.onCalibrationButton()

          # show the axial slice in 3d
          redSlice = slicer.util.getNode('vtkMRMLSliceNodeRed')
          if redSlice is not None:
              redSlice.SetSliceVisible(1)

        # show the volume rendering
        self.setVolumeRenderingVisibility(self.showVolumeRenderingCheckBox.checked)
        if self.calibrationOutLabelMapNode is not None and self.calibrationOutLabelMapNode.GetImageData() is not None:
            # update showing it in the label layer according to the check
            self.onShowLabelMap()

            # show the markers according to system settings
            self.setCalibratorVisibility(workflowFunctions.getParameter('CALIBRATOR_VIS_Flag'))

        workflowFunctions.fitTo3DView()
        slicer.app.processEvents()

        # then observe for updates on the calibrationScanDICOMID parameter
        self.addObservers()

    def validate(self, desiredBranchId):
        validation = False
        # Has the target scan been set
        if workflowFunctions.getParameter('targetScanDICOMID') is not None and self.registrationUserVerified == True:
            validation = True
        else:
            warningString = ''
            if self.registrationUserVerified == False:
                warningString = warningString + 'W:303 You must verify that the registration succeeded.\nYou may need to Register again.\n\n'
            if workflowFunctions.getParameter('targetScanDICOMID') is None:
                warningString = warningString + 'W:304 You must assign a Target scan.'
            # don't conflict with the verify registration success in case next step was clicked too fast
            if self.verifyRegistrationMsgBox is not None and self.verifyRegistrationMsgBox.visible:
                workflowFunctions.appendToStatusBox(warningString)
            else:
                workflowFunctions.popupWarning(warningString)
        super(HMS_NeedleGuideCalibrationStep, self).validate(validation, desiredBranchId)
        
    def onExit(self, goingTo, transitionType):
        # hide the volume rendering
        self.setVolumeRenderingVisibility(0)
        # remove the label map from the layer
        if self.calibrationOutLabelMapNode is not None:
            workflowFunctions.setLabelVolume(None)
        # hide the markers
        self.setCalibratorVisibility(False)
        # hide any zframe ROI
        self.setZFrameROIVisibility(0)
        self.removeObservers()
        goingToId = "None"
        if goingTo:
            goingToID = goingTo.id()
        # execute the transition
        super(HMS_NeedleGuideCalibrationStep, self).onExit(goingTo, transitionType)


    # Add an observer on the parameter node to track changes in the calibration
    # scan selection. Called from onEntry
    def addObservers(self):
        parameterNode = workflowFunctions.getParameterNode()
        if parameterNode is not None:
            self.removeObservers()
            self.parameterNodeModifiedTag = parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)
        else:
            self.parameterNodeModifiedTag = None

    # Remove any observers this step added, called from addObservers and onExit
    def removeObservers(self):
        if self.parameterNodeModifiedTag is not None:
            parameterNode = workflowFunctions.getParameterNode()
            if parameterNode is not None:
                parameterNode.RemoveObserver(self.parameterNodeModifiedTag)
                self.parameterNodeModifiedTag = None

        # Observers on the ZFrame ROI
        if self.zFrameROIAddedObserverTag is not None:
            if slicer.mrmlScene is not None:
                slicer.mrmlScene.RemoveObserver(self.zFrameROIAddedObserverTag)
                self.zFrameROIAddedObserverTag = None

        if self.zFrameROIDisplayTag is not None:
            if self.zFrameROI is not None:
                self.zFrameROI.RemoveObserver(self.zFrameROIDisplayTag)
                self.zFrameROIDisplayTag = None

    def onParameterNodeModified(self, caller, event):
        # compare the node label to the parameter node's calibration scan id and
        # update if necessary
        parameterID = workflowFunctions.getParameter('calibrationScanDICOMID')
        redSlice = slicer.util.getNode('vtkMRMLSliceNodeRed')
        if parameterID is None:
            # unset the label
            workflowFunctions.setVolumeLabel(self.calibrationInputVolumeLabel, '')
            self.dicomCalibrationScanID = None
            workflowFunctions.setActiveVolume(None)
            if self.calibrationOutLabelMapNode is not None and self.calibrationOutLabelMapNode.GetImageData() is not None:
                # clear out the registration results
                slicer.modules.volumes.logic().ClearVolumeImageData(self.calibrationOutLabelMapNode)
            # don't show the slice in 3d
            if redSlice is not None:
                redSlice.SetSliceVisible(0)
            return
        node = None
        nodeID = None
        labelText = self.calibrationInputVolumeLabel.text
        if labelText is not None and labelText != '':
            node = slicer.util.getFirstNodeByName(labelText)
        if node is not None:
            nodeID = node.GetID()
        if nodeID is None or nodeID != parameterID:
            self.calibrationInputVolumeNode = slicer.util.getNode(parameterID)
            if self.calibrationInputVolumeNode is not None:
                workflowFunctions.setVolumeLabel(self.calibrationInputVolumeLabel, self.calibrationInputVolumeNode.GetName())
                self.dicomCalibrationScanID = self.calibrationInputVolumeNode.GetID()
                # show it
                workflowFunctions.setActiveVolume(self.dicomCalibrationScanID)
                if redSlice is not None:
                    redSlice.SetSliceVisible(1)

                # update slider ranges
                maxSlice = self.calibrationInputVolumeNode.GetImageData().GetDimensions()[2]
                self.startSliceSliderWidget.maximum = maxSlice
                self.endSliceSliderWidget.maximum = maxSlice
                # see if it registers with current settings
                self.tryCalibration()
            else:
                workflowFunctions.setVolumeLabel(self.calibrationInputVolumeLabel, '')
                self.dicomCalibrationScanID = None
                workflowFunctions.setActiveVolume(None)
                if redSlice is not None:
                    redSlice.SetSliceVisible(0)
                if self.calibrationOutLabelMapNode is not None and self.calibrationOutLabelMapNode.GetImageData() is not None:
                    # clear out the registration results
                    slicer.modules.volumes.logic().ClearVolumeImageData(self.calibrationOutLabelMapNode)
        # update the locking of the GUI from the flag
        if workflowFunctions.getParameter('lockCalibrationFlag'):
            self.enableCalibrationOptions(0)
        else:
            self.enableCalibrationOptions(1)
        # show/hide the label map
        checked = workflowFunctions.getParameter('CALIBRATOR_LABELS_Flag')
        if checked:
            workflowFunctions.setLabelVolume(self.calibrationOutLabelMapNode.GetID())
        else:
            workflowFunctions.setLabelVolume(None)

    def addROIAddedObserver(self):
        @vtk.calldata_type(vtk.VTK_OBJECT)
        def onNodeAdded(caller, event, calldata):
            node = calldata
            if isinstance(node, slicer.vtkMRMLAnnotationROINode):
                self.removeZFrameROIAddedObserver()
                self.zFrameROI = node
                self.zFrameROI.SetName("Registration ROI")
                # add observer for display visibility
                self.zFrameROIDisplayTag = self.zFrameROI.AddObserver(slicer.vtkMRMLDisplayableNode.DisplayModifiedEvent, self.onZFrameROIDisplayModified)
                # update the button
                self.roiVisibleButton.checked = (self.zFrameROI.GetDisplayVisibility() != 0)

        # remove any previous node added observer
        self.removeZFrameROIAddedObserver()
        # remove previous ROI if any
        if self.zFrameROI is not None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'addROIAddedObserver: removing zFrameROI node'
            if self.zFrameROIDisplayTag is not None:
                self.zFrameROI.RemoveObserver(self.zFrameROIDisplayTag)
            slicer.mrmlScene.RemoveNode(self.zFrameROI)
            self.zFrameROI = None
        self.zFrameROIAddedObserverTag = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, onNodeAdded)

    def removeZFrameROIAddedObserver(self):
        if self.zFrameROIAddedObserverTag is not None:
            if slicer.mrmlScene is not None:
                slicer.mrmlScene.RemoveObserver(self.zFrameROIAddedObserverTag)
            self.zFrameROIAddedObserverTag = None

    # Update the parameter node and the qsettings from the GUI widgets
    def onRegistrationWidgetChanged(self, option, value):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Calibration step: onRegistrationWidgetChanged:\n\toption: ', option, '\n\tval = ', value
        # check for integers, convert to string
        if option in self.integerCalibrationSettings:
            stringValue = str(int(value))
        else:
            stringValue = str(value)
        # don't update the parameter node as the registration settings are not saved
        # there, just update the settings
        self.ngw.settings.setValue(self.optionsGroup + option, stringValue)
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onRegistrationWidgetChanged:', option, 'set to', self.ngw.settings.value(self.optionsGroup + option)

    def onResetToDefaultsButton(self):
        # Create a fresh command line module node and use it to set the values
        # for registration
        if not hasattr(slicer.modules, 'hms_marker_detection'):
            workflowFunctions.popupError('No defaults', 'E:310 Marker detection module not found.')
            return
        markerDetection = slicer.modules.hms_marker_detection
        markerDetectionLogic = markerDetection.cliModuleLogic()
        if markerDetectionLogic is None:
            workflowFunctions.popupError('No logic', 'E:311 Unable to set marker detection defaults.')
            return
        cliNode = markerDetectionLogic.CreateNode()
        if cliNode is None:
            workflowFunctions.popupError('No default settings', 'E:312 Unable to set marker detection defaults.')
            return
        self.startSliceSliderWidget.value = int(cliNode.GetParameterAsString('startSlice'))
        endSlice = cliNode.GetParameterAsString('endSlice')
        if endSlice == '':
            # end slice may not have a default value
            endSlice = '0';
        self.endSliceSliderWidget.value = int(endSlice)
        self.minFrameLocksSliderWidget.value = int(cliNode.GetParameterAsString('minFrameLocks'))
        self.peakRadiusSliderWidget.value = int(cliNode.GetParameterAsString('peakRadius'))
        self.maxBadPeaksSliderWidget.value = int(cliNode.GetParameterAsString('maxBadPeaks'))
        self.offPeakPercentSliderWidget.value = float(cliNode.GetParameterAsString('offPeakPercent'))
        self.maxStdDevPosSliderWidget.value = float(cliNode.GetParameterAsString('maxStdDevPos'))

        self.burnFlagCheckBox.checked = int(cliNode.GetParameterAsString('burnFlag'))
        self.burnThresholdPercentSliderWidget.value = float(cliNode.GetParameterAsString('burnThresholdPercent'))
        self.burnSurroundPercentSliderWidget.value = float(cliNode.GetParameterAsString('surroundPercent'))
        self.burnRecursionLimitSliderWidget.value = int(cliNode.GetParameterAsString('recursionLimit'))
        self.burnHistogramBinsSliderWidget.value = int(cliNode.GetParameterAsString('binsPerDimension'))
        self.burnHistogramUpperBoundSliderWidget.value = int(cliNode.GetParameterAsString('histogramUpperBound'))
        # check for case insenstive boolean value or 1 in the string, update the checkbox
        self.burnHistogramAutoBoundsCheckBox.checked = self.getSetting(cliNode.GetParameterAsString('histogramAutoBounds'))

    def onAddROI(self):
        workflowFunctions.popupInfo("Click once in the center of the markers, once outside a corner marker.\n\nAfter placement, it can be adjusted axially with the handles to surround just the slices with 7 bright markers.\n\nThen click on the Register button to use the Axial start/end slices defined by the ROI.\n", 'HMS/Calibration/AlwaysAddROI')
        self.addROIAddedObserver()

        # go into place ROI mode
        selectionNode =  slicer.util.getNode('vtkMRMLSelectionNodeSingleton')
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationROINode")
        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.StartPlaceMode(False)

    # reset the Calibration ROI to be centered in the Calibration volume and fully cover it
    def onResetROI(self):
        if self.zFrameROI is None:
            return
        if self.calibrationInputVolumeNode is None:
            workflowFunctions.popupError("No Calibration scan", "E:305 Select a Calibration scan for the ROI.")
            return
        bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.calibrationInputVolumeNode.GetRASBounds(bounds)
        rx = (bounds[1] - bounds[0])/2.0
        x = bounds[0] + rx
        ry = (bounds[3] - bounds[2])/2.0
        y = bounds[2] + ry
        rz = (bounds[5] - bounds[4])/2.0
        z = bounds[4] + rz
        self.zFrameROI.SetXYZ(x,y,z)
        self.zFrameROI.SetRadiusXYZ(rx, ry, rz)

    def onROIVisibleButtonToggled(self, flag):
        if self.zFrameROI is not None:
            # update the ROI from the button
            self.setZFrameROIVisibility(flag)

    def setZFrameROIVisibility(self, visible):
        if self.zFrameROI is None:
            return
        # avoid triggering modified events on all the display nodes
        numberOfDisplayNodes = self.zFrameROI.GetNumberOfDisplayNodes()
        wasModifying = []
        for i in xrange(numberOfDisplayNodes):
            wasModifying.append(self.zFrameROI.GetNthDisplayNode(i).StartModify())

        self.zFrameROI.SetDisplayVisibility(visible)

        for i in xrange(numberOfDisplayNodes):
            self.zFrameROI.GetNthDisplayNode(i).EndModify(wasModifying[i])


    def onZFrameROIDisplayModified(self, caller, event):
        if self.zFrameROI is not None:
            # update the visible/invisible button
            flag = self.zFrameROI.GetDisplayVisibility()
            # GetDisplayVisibility is 0 if all display nodes are set to invisible, 1
            # if all are visible, 2 if some are visible and some are invisible. ROIs
            # have three display nodes.
            if flag != 0:
                self.roiVisibleButton.checked = True
            else:
                self.roiVisibleButton.checked = False

    def onSheetConfigPathChanged(self):
        path = self.sheetConfigPathEdit.currentPath
        self.loadSheetConfigFile(path)
        # self.settings.setValue("config/sheetFilePath", path)
        workflowFunctions.setParameter('sheetFilePath', path)

    def onCalibrationConfigPathChanged(self):
        ''
        self.calibrationMarkerPath = workflowFunctions.get(self.widget, 'calibrationPathLineEdit').currentPath
        self.calibrationMarkers = self.loadCalibratorConfigFile(path=self.calibrationMarkerPath)
        # self.settings.setValue("config/calibrationFilePath", self.calibrationMarkerPath)
        workflowFunctions.setParameter('config/calibrationFilePath', self.calibrationMarkerPath)
        self.tryCalibration()
    
    def onShowCalibrator(self):
        self.setCalibratorVisibility(self.showCalibratorCheckBox.checked)

    def onShowVolumeRendering(self):
        self.setVolumeRenderingVisibility(self.showVolumeRenderingCheckBox.checked)

    def onShowLabelMap(self):
        checked = self.showLabelMapCheckBox.checked
        workflowFunctions.updateParameterFlagFromChecked('CALIBRATOR_LABELS_Flag', checked)

    def tryCalibration(self):
        ''
        # pass
        # print 'tryCalibration'
        # TODO after output defaults are created new run automatically
        # self.runCalibration(self.calibrationInputVolumeNode, self.calibrationMarkerPath, self.calibrationOutLabelMapNode, self.calibrationTransformNode)
        # Run the calibration with the current settings
        self.onCalibrationButton()


    def onCalibrationButton(self):
        if self.calibrationMarkerPath is None:
            workflowFunctions.popupError("Calibration", "E:306 Select Calibration Model Configuration file!")
            return
        if self.calibrationInputVolumeNode is None:
            # print 'onCalibrationButton: self.calibrationInputVolumeNode has not been set'
            # try getting it from the node selector
            volumeName = self.calibrationInputVolumeLabel.text
            if volumeName is None or volumeName == '':
                self.calibrationInputVolumeNode = None
            else:
                self.calibrationInputVolumeNode = slicer.util.getFirstNodeByName(volumeName)
            if self.calibrationInputVolumeNode is None:
                calibrationScanID = workflowFunctions.getParameter('calibrationScanDICOMID')
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print 'onCalibrationButton: no current node, parameter = ',calibrationScanID
                # this could get triggered on entry when setting the config file paths,
                # but before the volume is selected properly. If the parameter is set
                # but the node selector is still unset, just return. Otherwise pop up
                # an error to select a scan.
                if calibrationScanID is None:
                    workflowFunctions.popupError("Select calibration scan", "E:307 Select a calibration scan volume to register.")
                return

        # can be called from other methods
        if self.calibrationButton is not None:
            self.calibrationButton.setEnabled(False)
        'Run the calibration model to intraoperative detected calibration model '
        
        self.calibrationOutLabelMapNode = slicer.util.getNode('CalibrationOutVolume')
        if self.calibrationOutLabelMapNode is None:
            #make
            self.calibrationOutLabelMapNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLabelMapVolumeNode')
            self.calibrationOutLabelMapNode.UnRegister(None)
            self.calibrationOutLabelMapNode.SetName('CalibrationOutVolume')
            slicer.mrmlScene.AddNode(self.calibrationOutLabelMapNode)
            self.calibrationOutLabelMapNode = slicer.util.getNode('CalibrationOutVolume')
            checked = workflowFunctions.getParameter('CALIBRATOR_LABELS_Flag')
            if checked:
                workflowFunctions.setLabelVolume(self.calibrationOutLabelMapNode.GetID())
            else:
                workflowFunctions.setLabelVolume(None)
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'calibrationOutLabelMapNode: created a new one, with ID ',self.calibrationOutLabelMapNode.GetID()
        else:
            # clear it out
            volumesLogic = slicer.modules.volumes.logic()
            volumesLogic.ClearVolumeImageData(self.calibrationOutLabelMapNode)

        self.zTransNode = None
        zTransNodeID = workflowFunctions.getParameter('CalibrationTransformNodeID')
        if zTransNodeID is not None:
            self.zTransNode = slicer.util.getNode(zTransNodeID)

        if self.zTransNode is None:
            print 'onCalibrationButton:\n\tERROR: failed to get the transform node with id ', zTransNodeID
            if self.calibrationButton is not None:
             self.calibrationButton.setEnabled(True)
            return
        else:
            # reset to identity
            workflowFunctions.setTransformToIdentity(self.zTransNode)

        self.regSuccess = None
        regSuccessID = workflowFunctions.getParameter('RegSuccessNodeID')
        if regSuccessID is not None:
            self.regSuccess = slicer.util.getNode(regSuccessID)

        if self.regSuccess is None:
            print 'onCalibrationButton:\n\tERROR: failed to get the registration success node with id ', workflowFunctions.getParameter('RegSuccessNodeID')
            if self.calibrationButton is not None:
                self.calibrationButton.setEnabled(True)
            return
        else:
            workflowFunctions.setTransformToIdentity(self.regSuccess)

        if workflowFunctions.getParameter('devModeFlag') == 1:
            print "onCalibrationButton:"
            if self.calibrationInputVolumeNode is not None:
                print "\tinput volume node: ", self.calibrationInputVolumeNode.GetName()
            print "\tcalibration marker path: ", self.calibrationMarkerPath
            if self.calibrationOutLabelMapNode is not None:
                print "\toutput volume node: ", self.calibrationOutLabelMapNode.GetName()
            if self.zTransNode is not None:
                print "\ttransform node: ", self.zTransNode.GetName()

        # write report start of calibration
        self.writeLog("Calibration Started\nCalibration Input Node : " + self.calibrationInputVolumeNode.GetName() + "\nCalibration Marker Path : " + self.calibrationMarkerPath)

        if self.cliObserver is not None:
          self.cliNode.RemoveObserver(self.cliObserver)

        startSlice = int(self.startSliceSliderWidget.value)
        # make sure end slice is within the volume
        endSlice = int(self.endSliceSliderWidget.value)
        maxSlice = self.calibrationInputVolumeNode.GetImageData().GetDimensions()[2]
        if endSlice == 0 or endSlice > maxSlice:
            # use the image end slice
            endSlice = maxSlice
            self.endSliceSliderWidget.value = float(endSlice)

        # check for the ZFrame ROI node and if it exists, use it for the start and end slices
        if self.zFrameROI is not None and self.zFrameROI.GetDisplayVisibility() != 0:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'Found zframe roi: ', self.zFrameROI.GetID()
            center = [0.0, 0.0, 0.0]
            self.zFrameROI.GetXYZ(center)
            bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.zFrameROI.GetRASBounds(bounds)
            pMin = [bounds[0], bounds[2], bounds[4], 1]
            pMax = [bounds[1], bounds[3], bounds[5], 1]
            rasToIJKMatrix = vtk.vtkMatrix4x4()
            self.calibrationInputVolumeNode.GetRASToIJKMatrix(rasToIJKMatrix)
            pos = [0,0,0,1]
            rasToIJKMatrix.MultiplyPoint(pMin, pos)
            startSlice = int(pos[2])
            rasToIJKMatrix.MultiplyPoint(pMax, pos)
            endSlice = int(pos[2])
            # check slices are in bounds
            if startSlice < 0:
                startSlice = 0
            if endSlice < 0:
                endSlice = 0
            endZ = self.calibrationInputVolumeNode.GetImageData().GetDimensions()[2]
            endZ = endZ - 1
            if startSlice > endZ:
                startSlice = endZ
            if endSlice > endZ:
                endSlice = endZ
            self.startSliceSliderWidget.value = float(startSlice)
            self.endSliceSliderWidget.value = float(endSlice)
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'onCalibrationButton: calc slice numbers: startSlice = ',startSlice, ', endSlice = ',endSlice

        # reset the run once flag
        if workflowFunctions.getParameter('regOnceFlag') is 1:
            workflowFunctions.setParameter('regOnceFlag', '0')

        parameters = {}
        # from nodes:
        parameters['inputVolume'] = self.calibrationInputVolumeNode.GetID()
        parameters['startSlice'] = startSlice
        parameters['endSlice'] = endSlice
        parameters['markerConfigFile'] = self.calibrationMarkerPath
        parameters['outputVolume'] = self.calibrationOutLabelMapNode.GetID()
        parameters['markerTransform'] = self.zTransNode.GetID()
        parameters['regSuccess'] = self.regSuccess.GetID()
        # from settings:
        # ZFrame registration algorithm settings
        self.ngw.settings.beginGroup('zframe')
        calibrationKeys = self.ngw.settings.allKeys()
        self.ngw.settings.endGroup()
        for key in calibrationKeys:
            parameters[key] = self.getSetting(self.optionsGroup + key)
        # Note: there are no widgets for the object size settings,
        # they're in the zframe configuration settings only


        if workflowFunctions.getParameter('devModeFlag') == 1:
            print("Calibration parameters: %s"%(parameters))

        linereg = slicer.modules.hms_marker_detection
        deleteTemporaryFiles = True
        if  workflowFunctions.getParameter('devModeFlag') == 1:
            # don't delete temp files if in dev mode
            deleteTemporaryFiles = False
        waitForCompletion = False
        if workflowFunctions.getParameter('TestingFlag'):
            deleteTemporaryFiles = False
            waitForCompletion = True

        # Unset the variables that hold post registration flags
        self.goodRegistration = False
        self.registrationUserVerified = False

        self.cliNode = slicer.cli.run(linereg, None, parameters, waitForCompletion, deleteTemporaryFiles)
        self.progressBar.setCommandLineModuleNode(self.cliNode)
        workflowFunctions.appendToStatusBox("Calibration Started...")
        slicer.util.showStatusMessage( "Calibration Started...", 2000 )

        workflowFunctions.setStatusLabel("Calibration running...")
        self.cliObserver = self.cliNode.AddObserver('ModifiedEvent',self.observeCalibration)

    def createVolumeRenderingNode(self):
        if self.volumeRenderingDisplayNode is not None:
            return
        self.volumeRenderingDisplayNode = slicer.vtkMRMLCPURayCastVolumeRenderingDisplayNode()
        self.volumeRenderingDisplayNode.SetName("Registration_DispNode")

        volPropNode = slicer.vtkMRMLVolumePropertyNode()
        volPropNode.SetName("Registration_PropNode")
        slicer.mrmlScene.AddNode(volPropNode)

        volAnnoNode = slicer.vtkMRMLAnnotationROINode()
        volAnnoNode.SetDisplayVisibility(False)
        #volAnnoNode.SetName("Registration_AnnoNode")
        slicer.mrmlScene.AddNode(volAnnoNode)

        vprop = volPropNode.GetVolumeProperty()
        vprop.SetInterpolationTypeToLinear()
        vprop.SetShade(1)
        vprop.SetAmbient(0.3)
        vprop.SetDiffuse(0.6)
        vprop.SetSpecular(0.5)
        # TBD: markers are shiny, but using default specular power of 40 doesn't change it
        vprop.SetSpecularPower(40.0)

        vopac = vtk.vtkPiecewiseFunction()
        vopac.AddSegment(0.0,0.0,1.0,1.0)
        volPropNode.SetScalarOpacity(vopac)

        vcolo = vtk.vtkColorTransferFunction()
        vcolo.AddRGBPoint(0.0,0.0,0.0,0.0)
        vcolo.AddRGBPoint(0.5,0.75,0.75,0.75)
        vcolo.AddRGBPoint(1.0,1.0,1.0,1.0)
        vcolo.AddRGBPoint(5.0,1.0,1.0,1.0)
        volPropNode.SetColor(vcolo)

        #FOR NOW HARDCODE ROI
        volAnnoNode.SetXYZ(4.44,-10.615,-24.61)
        volAnnoNode.SetRadiusXYZ(135,135,58.5)
        volAnnoNode.SetDisplayVisibility(False)

        # set up observations
        self.volumeRenderingDisplayNode.SetAndObserveVolumePropertyNodeID(volPropNode.GetID())
        self.volumeRenderingDisplayNode.SetAndObserveROINodeID(volAnnoNode.GetID())
        # then add the volume rendering display node
        slicer.mrmlScene.AddNode(self.volumeRenderingDisplayNode)

    def observeCalibration(self,caller,event):
        status = caller.GetStatusString()
        workflowFunctions.appendToStatusBox("CALIBRATION STATUS: " + caller.GetStatusString())
        regSuccessMatrix = vtk.vtkMatrix4x4()
        self.regSuccess.GetMatrixTransformToParent(regSuccessMatrix)
        if (caller.GetStatusString() == 'Completed with errors'):
            self.writeLog("REGISTRATION FAILED")
            self.goodRegistration = False
            # TBD: do I need to remove the observation?
            # Pop up an error that registration failed.
            workflowFunctions.popupError('Registration Failure', 'E:308 Unable to detect calibration markers in scan.')
            self.onRegistrationCompleted()
        elif (caller.GetStatusString() == 'Completed'):
          # the registration success matrix holds
          if (regSuccessMatrix.GetElement(0,3)==1.0):
            self.writeLog("Registration success")
            self.goodRegistration = True
          else:
            self.writeLog("REGISTRATION FAILED")
            self.goodRegistration = False
            workflowFunctions.popupError('Registration Failure', 'E:309 Unable to detect calibration markers in scan and calculate transformation.')
          self.onRegistrationCompleted()

    def onRegistrationCompleted(self):
        # called when registration thread completes, errors or no
        if self.cliObserver is not None:
          self.cliNode.RemoveObserver(self.cliObserver)
          cliObserver = None

        # Transform the markers, either by identity or the found transform
        if self.zTransNode is not None:
          markersID = workflowFunctions.getParameter("calibratorModelNodeID")
          markers = None
          if markersID is not None and markersID != '':
              markers = slicer.util.getNode(markersID)
          if self.goodRegistration == False:
              identityMatrix = vtk.vtkMatrix4x4()
              self.zTransNode.SetMatrixTransformToParent(identityMatrix)
          if markers is not None:
              markers.SetAndObserveTransformNodeID(self.zTransNode.GetID())

        self.hideAllROIs()
        # Recenter the 3d view
        workflowFunctions.fitTo3DView()

        # Did it find the calibrator or not?
        if self.goodRegistration == False:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                errorCode = self.cliNode.GetParameterAsString("returnCode")
                errorString = self.cliNode.GetParameterAsString("returnString")
                regSuccessMatrix = vtk.vtkMatrix4x4()
                self.regSuccess.GetMatrixTransformToParent(regSuccessMatrix)
                matrixErrorCode =  regSuccessMatrix.GetElement(0,3)
                print '\tError:', errorCode, errorString, ', matrix:', matrixErrorCode
            workflowFunctions.setStatusLabel("Registration Failed, retry")
            self.onRegistrationCompletedWithErrors()
        else:
            if workflowFunctions.getParameter('targetScanDICOMID') is not None:
                workflowFunctions.setStatusLabel("Waiting for user to start targeting")
            else:
                workflowFunctions.setStatusLabel("Waiting for user to assign TARGET SCAN")
            self.onRegistrationCompletedNoErrors()

        # Then re-enable the calibration button for the next attempt
        if self.calibrationButton is not None:
            self.calibrationButton.setEnabled(True)

    def onRegistrationCompletedWithErrors(self):
        if self.goodRegistration == True:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'onRegistrationCompletedWithErrors: called in error, registration was true. Returning.'
            return
        # give a hint in the status window
        errorString = self.cliNode.GetParameterAsString("returnString")
        if errorString != '':
            workflowFunctions.appendToStatusBox(errorString)
        # disable volume rendering
        if self.volumeRenderingDisplayNode is not None:
            self.volumeRenderingDisplayNode.SetAndObserveVolumeNodeID(None)
        # don't show the label map
        workflowFunctions.setLabelVolume(None)

    def onRegistrationCompletedNoErrors(self):
        # only proceed if we have a good registration
        if self.goodRegistration == False:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'onRegistrationCompletedNoErrors: called in error, registration was false'
            return

        # Get the returned parameters from the file
        markerConfigurationID = self.cliNode.GetParameterAsString("markerConfigurationID")
        markerConfigurationDescription = self.cliNode.GetParameterAsString("markerConfigurationDescription")
        markerConfigurationGridID = self.cliNode.GetParameterAsString("markerConfigurationGridID")
        self.writeLog("Registration used marker configuration file " + markerConfigurationID + ": " + markerConfigurationDescription + ", to be used with grid " + markerConfigurationGridID)
        positionStdDev =  self.cliNode.GetParameterAsString("positionStdDev")
        quaternionStdDev =  self.cliNode.GetParameterAsString("quaternionStdDev")

        self.volumeRenderingDisplayNode = slicer.util.getNode("Registration_DispNode")
        if self.volumeRenderingDisplayNode is None:
            self.createVolumeRenderingNode()
        # set visibility from the checkbox
        self.setVolumeRenderingVisibility(self.showVolumeRenderingCheckBox.checked)

        if self.volumeRenderingDisplayNode is not None:
            if self.calibrationOutLabelMapNode.GetImageData() is not None:
                self.volumeRenderingDisplayNode.SetAndObserveVolumeNodeID(self.calibrationOutLabelMapNode.GetID())
            else:
                self.volumeRenderingDisplayNode.SetAndObserveVolumeNodeID(None)

        if (self.calibrationOutLabelDisplayNode is None):
            self.calibrationOutLabelDisplayNode = self.calibrationOutLabelMapNode.GetDisplayNode()
        # set the scalar range on the display node from the range on the image data
        if self.calibrationOutLabelMapNode.GetImageData() is not None:
            self.calibrationOutLabelDisplayNode.SetScalarRange(self.calibrationOutLabelMapNode.GetImageData().GetScalarRange())
        if (self.volumeRenderingDisplayNode is not None):
            # make sure the volume rendering gets updated with necessary settings
            volumeRenderingLogic = slicer.modules.volumerendering.logic()
            if (volumeRenderingLogic is not None):
                volumeRenderingLogic.CopyDisplayToVolumeRenderingDisplayNode(self.volumeRenderingDisplayNode, self.calibrationOutLabelDisplayNode)

            # the label map node should only have two display nodes, a label map
            # display and a volume rendering one, only observe the volume rendering
            # one again if it's missing
            if (not self.calibrationOutLabelMapNode.HasNodeReferenceID('display', self.volumeRenderingDisplayNode.GetID())):
                self.calibrationOutLabelMapNode.AddAndObserveDisplayNodeID(self.volumeRenderingDisplayNode.GetID())


        # Communicate results
        zMatrix = vtk.vtkMatrix4x4()
        self.zTransNode.GetMatrixTransformToParent(zMatrix)
        zMatrixStr = ''
        for i in range(4):
            for j in range(4):
                zMatrixStr += '\t' + '{:.3f}'.format(zMatrix.GetElement(i, j))
            zMatrixStr += '\n'
        self.writeLog("Registration Ended\nTransform Node:\n" + zMatrixStr)


        # Ask the user to verify the results
        if self.verifyRegistrationMsgBox is None:
            self.verifyRegistrationMsgBox = ctk.ctkMessageBox()
            self.verifyRegistrationMsgBox.setWindowTitle('Verify Registration Success')
            # non modal so can rotate view
            self.verifyRegistrationMsgBox.modal = False
            # keep it on top
            self.verifyRegistrationMsgBox.setWindowFlags(self.verifyRegistrationMsgBox.windowFlags() | qt.Qt.WindowStaysOnTopHint)
            self.verifyRegistrationMsgBox.setStandardButtons(qt.QMessageBox.Yes | qt.QMessageBox.No)
            self.verifyRegistrationMsgBox.setDefaultButton(qt.QMessageBox.No)
            resourcePath = workflowFunctions.getParameter('resources')
            if resourcePath is not None:
                questionPixmap = qt.QPixmap(os.path.join(resourcePath, "Icons/Small/sm_blue1help.png"))
                self.verifyRegistrationMsgBox.setIconPixmap(questionPixmap)
            else:
                self.verifyRegistrationMsgBox.setIcon(qt.QMessageBox.Question)
            # set up the call back to get the results
            self.verifyRegistrationMsgBox.connect('finished(int)', self.verifyRegistrationCallback)
        # get the translation from the calibration matrix
        translation = workflowFunctions.getTransformNodeWorldPosition(self.zTransNode)
        translationString = '\nTranslation: ' + workflowFunctions.formatPositionString(translation)
        translationString = translationString + " (stdev " + positionStdDev + ")"
        # get the rotation encoded in the calibration matrix
        orientationString = workflowFunctions.getOrientationString(self.zTransNode)
        orientationStdDevString = "\n  (quaternion stdev " + quaternionStdDev + ")"
        orientationString = orientationString + orientationStdDevString
        registrationOutputString = translationString + orientationString
        self.writeLog(registrationOutputString)

        newOrientation = self.adjustForMaxRotation()
        if newOrientation:
            # update the orientation string
            orientationString = workflowFunctions.getOrientationString(self.zTransNode)


        devInfoStr = ''
        if workflowFunctions.getParameter('devModeFlag') == 1:
            devInfoStr = '\n\n\nCalibration volume:\n\n\t' + self.calibrationInputVolumeNode.GetName() + '\n\nMarker configuration used:\n   ' + markerConfigurationID + '\n   ' + markerConfigurationDescription + '\n   for grid ' + markerConfigurationGridID + '\n\nTransform:\n' + zMatrixStr + translationString + orientationString

        registrationVerifyString = '\nDo the fiducial markers line up with the calibrator\'s cylinders?\n\n\n' + devInfoStr
        self.verifyRegistrationMsgBox.setText(registrationVerifyString)
        # is the patient name verification question message box showing?
        # or a warning popup?
        conflictingPopup = False
        for w in slicer.app.topLevelWidgets():
            if w.windowTitle == 'Verify Patient Name':
                # the patient name verificaiton pop up holds focus, but verifying
                # registration pop up box stays on top so they conflict
                conflictingPopup = True
                break
            if w.windowTitle == 'WARNING':
                # A warning can pop up if the user clicked too fast on the
                # navigation button to proceed to the target step without
                # having verified registration success
                conflictingPopup = True
                break
        if conflictingPopup:
            # don't stay on top
            self.verifyRegistrationMsgBox.setWindowFlags(self.verifyRegistrationMsgBox.windowFlags() & ~qt.Qt.WindowStaysOnTopHint)
        else:
            # stay on top
            self.verifyRegistrationMsgBox.setWindowFlags(self.verifyRegistrationMsgBox.windowFlags() | qt.Qt.WindowStaysOnTopHint)
        self.verifyRegistrationMsgBox.show_()


    def verifyRegistrationCallback(self, result):
        self.registrationUserVerified = False
        if result == qt.QMessageBox.Yes:
            self.registrationUserVerified = True
        else:
            # pop up a suggestion on how to fix it
            adjustRegistrationString = 'Try adding or adjusting a calibration ROI,\nin the Advanced Registration Options.'
            workflowFunctions.popupInfo(adjustRegistrationString)
        self.writeLog('Registration visually verified: ' + str(self.registrationUserVerified))

    def hideAllROIs(self):
        # hides the volume rendering and zframe ROIs
        roiClass = 'vtkMRMLAnnotationROINode'
        numberOfROIs = slicer.mrmlScene.GetNumberOfNodesByClass(roiClass)
        for i in range(numberOfROIs):
            curNode = slicer.mrmlScene.GetNthNodeByClass(i, roiClass)
            curNode.SetDisplayVisibility(False)

    def adjustForMaxRotation(self):
        # Check if the rotation around all axes is within scan distortion
        # parameters so that it can be discounted. If above, check with user
        # if they wish to use it.
        # If max rotation is set to 0, don't check the rotation.
        # Return True if adjusted, False otherwise
        maxRotationStr = workflowFunctions.getParameter('maxRotationDegrees')
        # if max rotation is not set in the settings file, don't check it
        if maxRotationStr is None:
            return False
        maxRotation = float(maxRotationStr)
        # if the settings file has max rotation of 0, don't check it
        epsilon = float(workflowFunctions.getParameter('epsilon'))
        if abs(maxRotation) < epsilon:
            return False

        useRotation = False
        orientation = workflowFunctions.getTransformNodeOrientation(self.zTransNode)
        if abs(orientation[0]) > maxRotation or abs(orientation[1]) > maxRotation or abs(orientation[2]) > maxRotation:
            orientationString = workflowFunctions.getOrientationString(self.zTransNode)
            useRotationString = "Calibration calculated a rotation that is larger than the tolerance of " + str(maxRotation) + " degrees around any one axis:\n" + orientationString + "\n\nDo you wish to use these values and the calculated translation (otherwise uses a rotation of 0 degrees and the calculated translation)?\n"
            useRotation = workflowFunctions.popupQuestion("Rotation", useRotationString)

        if useRotation:
            return False

        # remove rotation from the calibration matrix
        workflowFunctions.removeTransformNodeOrientation(self.zTransNode)
        # get the new rotation, expected 0 on all axes
        orientation = workflowFunctions.getTransformNodeOrientation(self.zTransNode)
        orientationString = '\n  Pitch %.3f degrees\n  Yaw   %.3f degrees\n  Roll  %.3f degrees' % (orientation[0], orientation[1], orientation[2])
        quaternionStdDev =  self.cliNode.GetParameterAsString("quaternionStdDev")
        orientationString = orientationString + "\n  Standard deviation of quaternion that was not used: " + quaternionStdDev
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Not using rotation:', orientationString
            workflowFunctions.appendToStatusBox("Using:\n\t" + orientationString)
        # print out the adjusted matrix
        zMatrix = vtk.vtkMatrix4x4()
        self.zTransNode.GetMatrixTransformToParent(zMatrix)
        zMatrixStr = ''
        for i in range(4):
            for j in range(4):
                zMatrixStr += '\t' + '{:.3f}'.format(zMatrix.GetElement(i, j))
            zMatrixStr += '\n'
        self.writeLog("Adjusted Transform Node:\n" + zMatrixStr)
        return True

    # Check if the hardwars IDs are set and compare between what the grid and
    # calibrator want to work with and what is set.
    # If the grid or calibrator hasn't specified a corresponding calibrator or
    # grid, skip checking that hardware ID.
    # Pops up error messages if expected hardware IDs don't match set IDs
    # Returns True if test passes, False otherwise.
    def checkHardwareIDs(self):
        # Calibrator expects a grid
        if self.markerConfigurationGridID is not None and self.guideSheetConfigurationID is not None:
            if self.markerConfigurationGridID != self.guideSheetConfigurationID:
                errStr = "Calibrator expects Grid with ID:\n\n    "
                errStr = errStr + self.markerConfigurationGridID + "\n\nbut have:\n\n    "
                errStr = errStr + self.guideSheetConfigurationID + ""
                self.writeLog(errStr)
                workflowFunctions.popupError("Wrong Grid for Calibrator", "E:313 " + errStr)
                return False

        # Grid expects a calibrator
        gridMarkerID = workflowFunctions.getGridParameter('MarkerConfigurationID')
        if gridMarkerID is not None and gridMarkerID != '' and self.markerConfigurationID is not None:
            if gridMarkerID != self.markerConfigurationID:
                errStr = "Grid expects Calibrator with ID:\n\n    "
                errStr = errStr + gridMarkerID + "\n\nbut have:\n\n    "
                errStr = errStr + self.markerConfigurationID + ""
                self.writeLog(errStr)
                workflowFunctions.popupError("Wrong Calibrator for Grid", "E:314 " + errStr)
                return False

        return True

    # When loading a new set of configuration files, it's necessary to reset the
    # expected hardware IDs so that the tests don't fail as the program is
    # loading them and checking them one at a time against the currently
    # loaded configurations.
    # When the second configuration is loaded the check will be done fully.
    def unsetHardwareIDs(self):
        # Unset the grid id expeced by the calibrator
        self.markerConfigurationGridID = None
        # Unset the calibrator id expected by the grid
        workflowFunctions.setGridParameter('MarkerConfigurationID', '')

    # Load the guide sheet configuration file from the given path.
    # Returns True on success, False on failure.
    def loadSheetConfigFile(self, path):
        if not os.path.exists(path):
            workflowFunctions.popupError('Invalid Grid Configuration', 'E:315 Grid configuration file not found:\n\n' + path)
            return False

        # Set up the node to read it into
        guideSheetCornersID = workflowFunctions.getParameter('guideSheetCornersID')
        if guideSheetCornersID is None:
            guideSheetCornersNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
            guideSheetCornersNode.SetHideFromEditors(1)
            guideSheetCornersNode.SetName('Guide Sheet Corners')
            slicer.mrmlScene.AddNode(guideSheetCornersNode)
            guideSheetCornersNode.UnRegister(None)
            guideSheetCornersID = guideSheetCornersNode.GetID()
            workflowFunctions.setParameter('guideSheetCornersID', guideSheetCornersID)
            # don't show the fiducials
            guideSheetCornersNode.SetDisplayVisibility(0)
            # print 'Added guide sheet corners fiducial node with id', guideSheetCornersID, ', GetID:',guideSheetCornersNode.GetID()

        # get node by id is failing:
        # slicer.mrmlScene.GetNodeByID(guideSheetCornersID)
        guideSheetCornersNode = slicer.util.getNode(guideSheetCornersID)
        if guideSheetCornersNode is None:
            print 'ERROR: failed to get the fiducial node with id',guideSheetCornersID
            return False

        # make sure it's empty
        guideSheetCornersNode.RemoveAllMarkups()
        self.guideSheetConfigurationDescription = None
        self.guideSheetConfigurationID = None
        guideSheetIDNumber = 0

        stringPrefix = '# Harmonus Guide Sheet '
        descriptionString = stringPrefix + 'Description = '
        idString = stringPrefix + 'ID = '
        markerIDString = '# Harmonus Marker Configuration ID = '
        holesXString = stringPrefix + 'Number Of Holes {} = '
        holesYString = stringPrefix + 'Number Of Holes {} = '
        spacingXString = stringPrefix + 'Hole Spacing {} = '
        spacingYString = stringPrefix + 'Hole Spacing {} = '
        holeDiameterString = stringPrefix + 'Hole Diameter = '
        offsetXString = stringPrefix + 'Origin Offset {} = '
        offsetYString = stringPrefix + 'Origin Offset {} = '

        reader = csv.reader(open(path, 'rb'))
        try:
          for row in reader:
            # Original guide sheet file had a quoted description line to start, but the
            # csv reader parses that as a single value with no quotes around it, so check
            # if the first character is alphabetic. Will fail if the quoted line starts
            # with a space.
            if row[0][0:1].isalpha() or row[0][0:1] == '#':
              # Check for the description or ID or parameters on the second half of a comment line
              if row[0][0:2] == '# ':
                  if (row[0].find(descriptionString) != -1):
                      # description may have commas in it, rejoin the list into a string
                      # before removing the prefix
                      self.guideSheetConfigurationDescription = ','.join(row).replace(descriptionString, "")
                  elif (row[0].find(idString) != -1):
                      self.guideSheetConfigurationID = ','.join(row).replace(idString, "")
                      # parse out the ID number for version checks, remove the prefix, take the first three characters and convert to int
                      guideSheetIDNumber = int(self.guideSheetConfigurationID.replace('RGS-', '')[0:3])
                      if workflowFunctions.getParameter('devModeFlag') == 1:
                          print 'guideSheetIDNumber = ', guideSheetIDNumber
                      if guideSheetIDNumber >= 7:
                          # at RGS-007 we moved from X,Y to R,A in the strings
                          str1 = 'R'
                          str2 = 'A'
                      else:
                          str1 = 'X'
                          str2 = 'Y'
                      # reset the strings
                      holesXString = holesXString.format(str1)
                      holesYString = holesYString.format(str2)
                      spacingXString = spacingXString.format(str1)
                      spacingYString = spacingYString.format(str2)
                      offsetXString = offsetXString.format(str1)
                      offsetYString = offsetYString.format(str2)
                  elif (row[0].find(markerIDString) != -1):
                      # Parse out the ID of the calibration configuration file
                      # with which this grid is paired
                      sheetMarkersID = row[0].replace(markerIDString, "")
                      workflowFunctions.setGridParameter('MarkerConfigurationID', sheetMarkersID)
                  elif (row[0].find(holesXString) != -1):
                      numHolesX = row[0].replace(holesXString, "")
                      workflowFunctions.setGridParameter('NumberOfHolesPerRow', numHolesX)
                  elif (row[0].find(holesYString) != -1):
                      numHolesY = row[0].replace(holesYString, "")
                      workflowFunctions.setGridParameter('NumberOfHolesPerColumn', numHolesY)
                  elif (row[0].find(offsetXString) != -1):
                      offsetX = row[0].replace(offsetXString, "")
                      workflowFunctions.setGridParameter('OriginOffsetX', offsetX)
                  elif (row[0].find(offsetYString) != -1):
                      offsetY = row[0].replace(offsetYString, "")
                      workflowFunctions.setGridParameter('OriginOffsetY', offsetY)
                  elif (row[0].find(spacingXString) != -1):
                      spacingX = row[0].replace(spacingXString, "")
                      workflowFunctions.setGridParameter('SpacingBetweenColumns', spacingX)
                  elif (row[0].find(spacingYString) != -1):
                      spacingY = row[0].replace(spacingYString, "")
                      workflowFunctions.setGridParameter('SpacingBetweenRows', spacingY)
                  elif (row[0].find(holeDiameterString) != -1):
                      holeDiameter = row[0].replace(holeDiameterString, "")
                      workflowFunctions.setGridParameter('HoleDiameter', holeDiameter)
            else:
              # Values that define the guide sheet
              try:
                  rowValues = [float(v) for v in row]
              except ValueError:
                  print 'Error parsing file, found non floating point numbers on line ', reader.line_num, '\n\t',row
                  return False
              if len(rowValues) == 3:
                  if guideSheetCornersNode is not None:
                      guideSheetCornersNode.AddFiducial(rowValues[0], rowValues[1], rowValues[2])
                      numFids = guideSheetCornersNode.GetNumberOfFiducials()
                      if numFids > 4:
                          print "Error: too many points parsed from the file! Have ", numFids, ", expected 4."
                          return False
              else:
                  print 'Error: expected 3 values on line ', reader.line_num, ', but have ', len(rowValues), '\n', row
                  return False

        except csv.Error as e:
          print("Error reading file %s, line %d: %s" %(path, reader.line_num, e))
          return False

        numberOfCorners = guideSheetCornersNode.GetNumberOfFiducials()
        if numberOfCorners != 4:
            print "Error: expected four corners, have", numberOfCorners
            return False

        sheetPoints = workflowFunctions.getGuideSheetCorners()
        # use numpy mean to calculate the average per column (axis = 0)
        self.guideSheetCenter = numpy.array(numpy.mean(sheetPoints, 0))
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Guide sheet center = ',self.guideSheetCenter
        self.setGuideSheetTransform()

        # update the GUI
        if hasattr(self, 'widget') and self.widget is not None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'loadSheetConfigFile: setting the GUI labels for id', self.guideSheetConfigurationID, 'and description', self.guideSheetConfigurationDescription
            # Set the guide sheet configuration ID
            label = workflowFunctions.get(self.widget, "sheetConfigurationIDLabel")
            if label is not None:
                if self.guideSheetConfigurationID is not None:
                    label.setText(self.guideSheetConfigurationID)
                else:
                    label.setText('')
            label = workflowFunctions.get(self.widget, "sheetConfigurationDescriptionLabel")
            if label is not None:
                if self.guideSheetConfigurationDescription is not None:
                    label.setText(self.guideSheetConfigurationDescription)
                    # in case it's cut off, also put in the tool tip
                    label.setToolTip(self.guideSheetConfigurationDescription)
                else:
                    label.setText('')
                    label.setToolTip('')
            label = workflowFunctions.get(self.widget, "sheetConfigurationMarkerIDLabel")
            if label is not None:
                sheetConfigurationMarkerID = workflowFunctions.getGridParameter('MarkerConfigurationID')
                if sheetConfigurationMarkerID is not None:
                    label.setText(sheetConfigurationMarkerID)
                else:
                    label.setText('')

        # end loadSheetConfigFile
        if self.checkHardwareIDs():
            return True
        else:
            return False

    def loadCalibratorConfigFile(self, path, lineLen=CalibrationMarker.CALIBRATOR_LENGTH):
        # print('load calibrator configuration file %s length=%f'%(path, lineLen))
        if path is None:
            print 'ERROR: no file passed to loadCalibratorConfigFile'
            return
        if path is '':
            print 'ERROR: empty path pased to loadCalibratorConfigFile'
            return
        if not os.path.exists(path):
            workflowFunctions.popupError('Invalid Calibrator Configuration', 'E:316 Calibrator configuration file not found:\n\n' + path)
            return

        tokens = path.split('/')
        length = len(tokens)
        fname = tokens[length-1]
        extInx = fname.rfind('.')
        calibrationBaseName = fname[0:extInx]
        reader = csv.reader(open(path, 'rb'))
        calibrationMarkers = []
        descriptionString = '# Harmonus Marker Configuration Description = '
        idString = '# Harmonus Marker Configuration ID = '
        gridIDString = '# Harmonus Guide Sheet ID = '
        try:
          for row in reader:
            if row[0][0:2] == '# ':
                # comment line
                # check for description and ID, on second half of comment line
                if (row[0].find(descriptionString) != -1):
                    # in case the description has commas in it, which would result in the
                    # post comma parts of the description ending up in the next element
                    # of row[0], join the elements with a comma before removing the prefix
                    self.markerConfigurationDescription = ','.join(row).replace(descriptionString, "")
                elif (row[0].find("Configuration ID") != -1):
                    self.markerConfigurationID = ','.join(row).replace(idString, "")
                elif (row[0].find(gridIDString) != -1):
                    self.markerConfigurationGridID = ','.join(row).replace(gridIDString, "")
            else:
                row = [float(v) for v in row]
                if len(row) >=6:
                    calibrationMarker = CalibrationMarker(pos=row[0:3], orientation=row[3:6], flen=lineLen)
                    calibrationMarkers.append(calibrationMarker)
        except csv.Error as e:
          print("error reading file %s, line %d: %s" % (path, reader.line_num, e))
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Calibrator configuration: ID = ', self.markerConfigurationID, ', description = ', self.markerConfigurationDescription
        # when called from the self test, no widget
        if hasattr(self, 'widget') and self.widget is not None:
            # set the Configuration section marker ID label
            label = workflowFunctions.get(self.widget, "markerConfigurationIDLabel")
            if label is not None:
                if self.markerConfigurationID is not None:
                    label.setText(self.markerConfigurationID)
                else:
                    label.setText('')
            # set the Configuration section marker description label
            label = workflowFunctions.get(self.widget, "markerConfigurationDescriptionLabel")
            if label is not None:
                if self.markerConfigurationDescription is not None:
                    label.setText(self.markerConfigurationDescription)
                    # text length may be limited by the GUI, also set in tool tip
                    label.setToolTip(self.markerConfigurationDescription)
                else:
                    label.setText('')
                    label.setToolTip('')
            # set the Configuration section marker grid ID label
            label = workflowFunctions.get(self.widget, "markerConfigurationGridIDLabel")
            if label is not None:
                if self.markerConfigurationGridID is not None:
                    label.setText(self.markerConfigurationGridID)
                else:
                    label.setText('')

        self.markersCenter = numpy.array(self.calculateCenterOfMarkers(calibrationMarkers))
        self.setGuideSheetTransform()

        if not self.checkHardwareIDs():
            self.writeLog("Hardware ID mismatch.")

        self.createCalibratorModel(calibrationMarkers, calibrationBaseName)
        return calibrationMarkers

    def calculateMarkersBoundingBox(self, markers):
        # set up the end points of the markers in a numpy array then
        # calculate the min and max values using numpy min and max
        bounds = [0,0,0,0,0,0]
        if markers is None:
            return bounds
        markerArray = []
        for marker in markers:
            markerArray.append(numpy.array(marker.pos0()))
            markerArray.append(numpy.array(marker.pos2()))
        # convert to a matrix to get the min and max for the columns
        mat = numpy.matrix(markerArray)
        lo = numpy.array(mat.min(0))[0]
        hi = numpy.array(mat.max(0))[0]
        bounds = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]
        return bounds

    def calculateCenterOfMarkers(self, markers):
        center = [0.0, 0.0, 0.0]
        markerBounds = self.calculateMarkersBoundingBox(markers)
        for a in xrange(3):
            center[a]= (markerBounds[a*2] + markerBounds[a*2+1])/2.0
        return center

    def createCalibratorModel(self, markers, name):
        newModel = False
        calibratorModelNodeID = workflowFunctions.getParameter('calibratorModelNodeID')
        self.calibratorModelNode = None
        if calibratorModelNodeID is not None:
           self.calibratorModelNode = slicer.mrmlScene.GetNodeByID(calibratorModelNodeID)
        if self.calibratorModelNode == None:
          self.calibratorModelNode = slicer.vtkMRMLModelNode()
          slicer.mrmlScene.AddNode(self.calibratorModelNode)
          calibratorModelNodeID = self.calibratorModelNode.GetID()
          workflowFunctions.setParameter('calibratorModelNodeID', calibratorModelNodeID)
          # print 'createCalibratorModel: calibratorModelNodeID = ', calibratorModelNodeID
          dnode = slicer.vtkMRMLModelDisplayNode()
          slicer.mrmlScene.AddNode(dnode)
          # increase weight of outline for slice intersections
          dnode.SetSliceIntersectionThickness(2)
          # Set the color to match mouse over on buttons
          colors = colorPalette()
          blue = colors['ButtonHover']
          dnode.SetColor(blue.redF(),blue.greenF(),blue.blueF())
          self.calibratorModelNode.SetAndObserveDisplayNodeID(dnode.GetID())
          # print("Created calibration model ID=%s display node ID=%s" % (calibratorModelNodeID, dnode.GetID()))
          newModel = True
        self.calibratorModelNode.SetName('Calibrator Model')
        calibratorModelAppend = vtk.vtkAppendPolyData()
        for marker in markers:
          pt1 = numpy.array(marker.pos0() - self.markersCenter)
          pt2 = numpy.array(marker.pos2() - self.markersCenter)
          lineSource = vtk.vtkLineSource()
          lineSource.SetPoint1(pt1)
          lineSource.SetPoint2(pt2)
          # print("marker=%s pt1=%s pt2=%s" %(marker, pt1, pt2))
          tubeFilter = vtk.vtkTubeFilter()
          tubeFilter.SetInputConnection(lineSource.GetOutputPort())
          tubeFilter.SetRadius(2.0)
          tubeFilter.SetNumberOfSides(18)
          tubeFilter.CappingOn()
          tubeFilter.Update()
          calibratorModelAppend.AddInputData(tubeFilter.GetOutput())
        calibratorModelAppend.Update()
        self.calibratorModelNode.SetAndObservePolyData(calibratorModelAppend.GetOutput())

        self.setCalibratorVisibility(workflowFunctions.getParameter('CALIBRATOR_VIS_Flag'))
        if newModel:
          self.calibratorModelNode.SetAndObserveTransformNodeID(self.zTransNode.GetID())

    def calculateCenterOfPoints(self, points):
        center = [0.0, 0.0, 0.0]
        numPoints = 0
        for point in points:
            numPoints += 1
            for i in xrange(3):
                center[i] = center[i] + point[i]
        if numPoints != 0:
            for i in xrange(3):
                center[i] = center[i] / float(numPoints)
        return center

    def setGuideSheetTransform(self):
        # Set up the transform node that holds the transform between the calibration
        # configuration markers and the guide sheet. The configuration files
        # are defined in the same coordinate system.
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'setGuideSheetTransform'
            print '\tguide sheet center = ', self.guideSheetCenter
            print '\tmarkers center = ', self.markersCenter
        self.markersToSheetTranslation = self.guideSheetCenter - self.markersCenter
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'markersToSheetTranslation = ', self.markersToSheetTranslation
        # make a transformation matrix with the translation set
        translationMatrix = vtk.vtkMatrix4x4()
        translationMatrix.SetElement(0,3,self.markersToSheetTranslation[0])
        translationMatrix.SetElement(1,3,self.markersToSheetTranslation[1])
        translationMatrix.SetElement(2,3,self.markersToSheetTranslation[2])
        self.guideSheetTransformNode.SetMatrixTransformToParent(translationMatrix)

        # then set it's transform node to be the marker registration transform node
        self.guideSheetTransformNode.SetAndObserveTransformNodeID(self.zTransNode.GetID())

        # set up the transform that defines the offset of the sheet center from
        # the XY origin, used for grid calculations
        centerMatrix = vtk.vtkMatrix4x4()
        centerMatrix.SetElement(0,3,-self.guideSheetCenter[0])
        centerMatrix.SetElement(1,3,-self.guideSheetCenter[1])
        centerMatrix.SetElement(2,3,-self.guideSheetCenter[2])
        self.guideSheetCenterTransformNode.SetMatrixTransformToParent(centerMatrix)
        self.guideSheetCenterTransformNode.SetAndObserveTransformNodeID(self.guideSheetTransformNode.GetID())

        # set up the transform that scales the grid holes model according to the needle length
        holesMatrix = vtk.vtkMatrix4x4()
        needleLength = 1.0
        needleLengthStr = workflowFunctions.getParameter('needleLength')
        if not (needleLengthStr is None or needleLengthStr == ''):
            needleLength = float(needleLengthStr)
        # scale by the needle length in Z
        holesMatrix.SetElement(2, 2, needleLength)
        # position by half the needle length as the holes are defined as
        # unit length tubes at the guiide sheet plane
        holesMatrix.SetElement(2, 3, needleLength / 2.0)
        self.guideSheetHolesTransformNode.SetMatrixTransformToParent(holesMatrix)
        # set it as a child of the guide sheet transform
        self.guideSheetHolesTransformNode.SetAndObserveTransformNodeID(self.guideSheetTransformNode.GetID())

        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'setGuideSheetTransform: guide sheet transform node id = ', self.guideSheetTransformNode.GetID(), ', ztransnode id = ', self.zTransNode.GetID(), ', guide sheet center transform node id = ', self.guideSheetCenterTransformNode.GetID()



    def setModelSliceIntersectionVisibilityByID(self, id, visible):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print("setModelSliceIntersectionVisibilityByID ID=%s visibile=%d"%(id, visible))
        mnode = slicer.mrmlScene.GetNodeByID(id)
        if mnode is not None:
          dnode = mnode.GetDisplayNode()
          if dnode is not None:
            dnode.SetSliceIntersectionVisibility(visible)

    def setCalibratorVisibility(self, visibility):
        if self.calibratorModelNode is not None:
            self.calibratorModelNode.SetDisplayVisibility(visibility)
            # show the intersection with slices
            self.setModelSliceIntersectionVisibilityByID(self.calibratorModelNode.GetID(), visibility)

    def setVolumeRenderingVisibility(self, visibility):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print("set volume rendering visibility=%s" %(visibility))
        if self.volumeRenderingDisplayNode is None:
            if self.calibrationOutLabelMapNode is not None:
                if self.calibrationOutLabelMapNode.GetNumberOfDisplayNodes() > 1:
                    # get the volume rendering display node
                    self.volumeRenderingDisplayNode = self.calibrationOutLabelMapNode.GetNthDisplayNode(1)
        if self.volumeRenderingDisplayNode is not None:
            if self.volumeRenderingDisplayNode.GetClassName().find('VolumeRendering') != -1:
                self.volumeRenderingDisplayNode.SetVisibility(visibility)

            
    def writeLog(self, message):
        workflowFunctions.writeLog(self.logFileName, message)

    def enableCalibrationOptions(self, enableFlag):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'enableCalibrationOptions: ', enableFlag
        if self.sheetConfigPathEdit is not None:
            self.sheetConfigPathEdit.setEnabled(enableFlag)
        if  self.calibrationConfigPathEdit is not None:
            self.calibrationConfigPathEdit.setEnabled(enableFlag)
        if self.widget is not None:
            zFrameParametersFrame = workflowFunctions.get(self.widget, "zFrameParametersFrame")
            if zFrameParametersFrame is not None:
                zFrameParametersFrame.setEnabled(enableFlag)

    # Update the registration widgets from the current qsettings
    def updateRegistrationWidgetsFromSettings(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'updateRegistrationWidgetsFromSettings: optionsGroup = ' + self.optionsGroup + '\n'
        self.minFrameLocksSliderWidget.value = self.getSetting(self.optionsGroup + 'minFrameLocks')
        self.peakRadiusSliderWidget.value = self.getSetting(self.optionsGroup + 'peakRadius')
        self.maxBadPeaksSliderWidget.value = self.getSetting(self.optionsGroup + 'maxBadPeaks')
        self.offPeakPercentSliderWidget.value = self.getSetting(self.optionsGroup + 'offPeakPercent')
        self.maxStdDevPosSliderWidget.value = self.getSetting(self.optionsGroup + 'maxStdDevPos')

        self.burnFlagCheckBox.checked = self.getSetting(self.optionsGroup + 'burnFlag')
        self.burnThresholdPercentSliderWidget.value = self.getSetting(self.optionsGroup + 'burnThresholdPercent')
        self.burnSurroundPercentSliderWidget.value = self.getSetting(self.optionsGroup + 'surroundPercent')
        self.burnRecursionLimitSliderWidget.value = self.getSetting(self.optionsGroup + 'recursionLimit')
        self.burnHistogramBinsSliderWidget.value = self.getSetting(self.optionsGroup + 'binsPerDimension')
        self.burnHistogramUpperBoundSliderWidget.value = self.getSetting(self.optionsGroup + 'histogramUpperBound')
        self.burnHistogramAutoBoundsCheckBox.checked = self.getSetting(self.optionsGroup + 'histogramAutoBounds')

    # Get a qsettings value, converting from string to bool, int, float.
    # key needs to include the group if necessary
    # Returns None if not found (qsettings value will return None if key not found)
    def getSetting(self, key):
        settingString = self.ngw.settings.value(key)
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'getSetting: key = ', key, ', settingString = ', settingString
        if settingString is None:
            return None
        # check for bool string
        if settingString.isalpha():
            if settingString.lower() == 'true':
                return 1
            else:
                return 0
        # numbers
        if key in self.integerCalibrationSettings:
            print 'integer setting:', key
            # to convert from string to integer, go through float to avoid thrown error
            setting = int(float(settingString))
        else:
            setting = float(settingString)
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'getSetting: key = ', key, ', setting = ', setting
        return setting
