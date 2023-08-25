import logging
import os

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import SimpleITK as sitk
import sitkUtils
import numpy as np
from skimage.restoration import unwrap_phase

from math import sqrt, pow


class SimpleNeedleTracking(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SimpleNeedleTracking"
    self.parent.categories = ["IGT"] 
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Mariana Bernardes (BWH), Junichi Tokuda (BWH), Ahmed Mahran (BWH)"] 
    self.parent.helpText = """ This is a 2D needle tracking module used to track the needle tip in RT-MRI images. Input requirement: 
    Magnitude/Phase image or Real/Imaginary image. Uses scikit unwrapping algorithm. """
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """ """

    # Additional initialization step after application startup is complete
    # TODO: include sample data and testing routines
    # slicer.app.connect("startupCompleted()", registerSampleData)

################################################################################################################################################
# Custom Widget  - Separator
################################################################################################################################################
class SeparatorWidget(qt.QWidget):
    def __init__(self, label_text='Separator Widget Label', parent=None):
        super().__init__(parent)

        spacer = qt.QWidget()
        spacer.setFixedHeight(10)
        
        self.label = qt.QLabel(label_text)
        font = qt.QFont()
        font.setItalic(True)
        self.label.setFont(font)
        
        line = qt.QFrame()
        line.setFrameShape(qt.QFrame.HLine)
        line.setFrameShadow(qt.QFrame.Sunken)
        
        layout = qt.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(qt.Qt.AlignVCenter)
        layout.addWidget(spacer)
        layout.addWidget(self.label)
        layout.addWidget(line)
        
        self.setLayout(layout)


################################################################################################################################################
# Widget Class
################################################################################################################################################

class SimpleNeedleTrackingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
  """
  # Called when the user opens the module the first time and the widget is initialized.
  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    ####################################
    ##                                ##
    ## UI Components                  ##
    ##                                ##
    ####################################
    
    ## Image selection                
    ####################################
    
    imagesCollapsibleButton = ctk.ctkCollapsibleButton()
    imagesCollapsibleButton.text = 'Setup and initialization'
    self.layout.addWidget(imagesCollapsibleButton)
    imagesFormLayout = qt.QFormLayout(imagesCollapsibleButton)
    
    # Input mode
    self.inputModeMagPhase = qt.QRadioButton('Magnitude/Phase')
    self.inputModeRealImag = qt.QRadioButton('Real/Imaginary')
    self.inputModeMagPhase.checked = 1
    self.inputModeButtonGroup = qt.QButtonGroup()
    self.inputModeButtonGroup.addButton(self.inputModeMagPhase)
    self.inputModeButtonGroup.addButton(self.inputModeRealImag)
    inputModeHBoxLayout = qt.QHBoxLayout()
    inputModeHBoxLayout.addWidget(self.inputModeMagPhase)
    inputModeHBoxLayout.addWidget(self.inputModeRealImag)
    imagesFormLayout.addRow('Input Mode:',inputModeHBoxLayout)
    
    ### Baseline images
    imagesFormLayout.addRow(SeparatorWidget('Baseline images'))
    
    # Input magnitude/real volume (first volume)
    self.firstBaselineVolumeSelector = slicer.qMRMLNodeComboBox()
    self.firstBaselineVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.firstBaselineVolumeSelector.selectNodeUponCreation = True
    self.firstBaselineVolumeSelector.addEnabled = True
    self.firstBaselineVolumeSelector.removeEnabled = True
    self.firstBaselineVolumeSelector.noneEnabled = True
    self.firstBaselineVolumeSelector.showHidden = False
    self.firstBaselineVolumeSelector.showChildNodeTypes = False
    self.firstBaselineVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.firstBaselineVolumeSelector.setToolTip('Select the magnitude/real image')
    imagesFormLayout.addRow('Magnitude/Real: ', self.firstBaselineVolumeSelector)

    # Input phase/imaginary volume (second volume)
    self.secondBaselineVolumeSelector = slicer.qMRMLNodeComboBox()
    self.secondBaselineVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.secondBaselineVolumeSelector.selectNodeUponCreation = True
    self.secondBaselineVolumeSelector.addEnabled = True
    self.secondBaselineVolumeSelector.removeEnabled = True
    self.secondBaselineVolumeSelector.noneEnabled = True
    self.secondBaselineVolumeSelector.showHidden = False
    self.secondBaselineVolumeSelector.showChildNodeTypes = False
    self.secondBaselineVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.secondBaselineVolumeSelector.setToolTip('Select the phase/imaginary image')
    imagesFormLayout.addRow('Phase/Imaginary: ', self.secondBaselineVolumeSelector)
    
    # Create a segmentation node selector widget
    self.manualMaskSelector = slicer.qMRMLNodeComboBox()
    self.manualMaskSelector.nodeTypes = ['vtkMRMLSegmentationNode']
    self.manualMaskSelector.selectNodeUponCreation = True
    self.manualMaskSelector.noneEnabled = True
    self.manualMaskSelector.showChildNodeTypes = False
    self.manualMaskSelector.showHidden = False
    self.manualMaskSelector.setMRMLScene(slicer.mrmlScene)
    self.manualMaskSelector.setToolTip('Select segmentation with manual mask')
    imagesFormLayout.addRow('Mask (optional): ', self.manualMaskSelector)

    # Save baseline 
    trackingHBoxLayout = qt.QHBoxLayout()    
    self.saveBaselineButton = qt.QPushButton('Save Baseline')
    self.saveBaselineButton.toolTip = 'Save or update baseline images'
    self.saveBaselineButton.enabled = False
    imagesFormLayout.addRow('',self.saveBaselineButton)
    
    ### Real-time images
    imagesFormLayout.addRow(SeparatorWidget('Real-time images'))

    # Input magnitude/real volume (first volume)
    self.firstVolumeSelector = slicer.qMRMLNodeComboBox()
    self.firstVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.firstVolumeSelector.selectNodeUponCreation = True
    self.firstVolumeSelector.addEnabled = True
    self.firstVolumeSelector.removeEnabled = True
    self.firstVolumeSelector.noneEnabled = True
    self.firstVolumeSelector.showHidden = False
    self.firstVolumeSelector.showChildNodeTypes = False
    self.firstVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.firstVolumeSelector.setToolTip('Select the magnitude/real image')
    imagesFormLayout.addRow('Magnitude/Real: ', self.firstVolumeSelector)

    # Input phase/imaginary volume (second volume)
    self.secondVolumeSelector = slicer.qMRMLNodeComboBox()
    self.secondVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.secondVolumeSelector.selectNodeUponCreation = True
    self.secondVolumeSelector.addEnabled = True
    self.secondVolumeSelector.removeEnabled = True
    self.secondVolumeSelector.noneEnabled = True
    self.secondVolumeSelector.showHidden = False
    self.secondVolumeSelector.showChildNodeTypes = False
    self.secondVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.secondVolumeSelector.setToolTip('Select the phase/imaginary image')
    imagesFormLayout.addRow('Phase/Imaginary: ', self.secondVolumeSelector)

    ## Needle Tracking                
    ####################################

    trackingCollapsibleButton = ctk.ctkCollapsibleButton()
    trackingCollapsibleButton.text = 'Needle tracking'
    self.layout.addWidget(trackingCollapsibleButton)
    trackingFormLayout = qt.QFormLayout(trackingCollapsibleButton)
    
    # Select which scene view to track
    self.sceneViewButton_red = qt.QRadioButton('Red')
    self.sceneViewButton_yellow = qt.QRadioButton('Yellow')
    self.sceneViewButton_green = qt.QRadioButton('Green')
    self.sceneViewButton_red.checked = 1
    self.sceneViewButtonGroup = qt.QButtonGroup()
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_red)
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_yellow)
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_green)
    layout = qt.QHBoxLayout()
    layout.addWidget(self.sceneViewButton_red)
    layout.addWidget(self.sceneViewButton_yellow)
    layout.addWidget(self.sceneViewButton_green)
    trackingFormLayout.addRow('Scene view:',layout)    
    
    # Tip prediction 
    self.tipPredictionSelector = slicer.qMRMLNodeComboBox()
    self.tipPredictionSelector.nodeTypes = ['vtkMRMLLinearTransformNode']
    self.tipPredictionSelector.selectNodeUponCreation = True
    self.tipPredictionSelector.addEnabled = True
    self.tipPredictionSelector.removeEnabled = False
    self.tipPredictionSelector.noneEnabled = True
    self.tipPredictionSelector.showHidden = False
    self.tipPredictionSelector.showChildNodeTypes = False
    self.tipPredictionSelector.setMRMLScene(slicer.mrmlScene)
    self.tipPredictionSelector.setToolTip('Select the tip prediction node')
    trackingFormLayout.addRow('Tip prediction:', self.tipPredictionSelector)

    # Start/Stop tracking 
    trackingHBoxLayout = qt.QHBoxLayout()    
    self.startTrackingButton = qt.QPushButton('Start Tracking')
    self.startTrackingButton.toolTip = 'Start needle tracking in image sequence'
    self.startTrackingButton.enabled = False
    trackingHBoxLayout.addWidget(self.startTrackingButton)
    self.stopTrackingButton = qt.QPushButton('Stop Tracking')
    self.stopTrackingButton.toolTip = 'Stop the needle tracking'
    self.stopTrackingButton.enabled = False    
    trackingHBoxLayout.addWidget(self.stopTrackingButton)
    trackingFormLayout.addRow('', trackingHBoxLayout)
    
    ## Advanced parameters            
    ####################################

    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = 'Advanced'
    advancedCollapsibleButton.collapsed=1
    self.layout.addWidget(advancedCollapsibleButton)
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)
    
    # Debug mode check box (output images at intermediate steps)
    self.debugFlagCheckBox = qt.QCheckBox()
    self.debugFlagCheckBox.checked = False
    self.debugFlagCheckBox.setToolTip('If checked, output images at intermediate steps')
    advancedFormLayout.addRow('Debug', self.debugFlagCheckBox)
    
    # ROI size
    self.roiSizeWidget = ctk.ctkSliderWidget()
    self.roiSizeWidget.singleStep = 1
    self.roiSizeWidget.setDecimals(0)
    self.roiSizeWidget.minimum = 15
    self.roiSizeWidget.maximum = 100
    self.roiSizeWidget.value = 30
    self.roiSizeWidget.setToolTip('Set ROI window size (px).')
    advancedFormLayout.addRow('ROI Size:', self.roiSizeWidget)
    
    # Blob threshold
    self.blobThresholdWidget = ctk.ctkSliderWidget()
    self.blobThresholdWidget.singleStep = 0.1
    self.blobThresholdWidget.minimum = 0
    self.blobThresholdWidget.maximum = 2*np.pi
    self.blobThresholdWidget.value = 2
    self.blobThresholdWidget.setToolTip('Set phase threshold value (0-2pi rad) for blob detection.')
    advancedFormLayout.addRow('Blob Threshold:', self.blobThresholdWidget)
    
    # Error threshold
    self.errorThresholdWidget = ctk.ctkSliderWidget()
    self.errorThresholdWidget.singleStep = 0.1
    self.errorThresholdWidget.minimum = 0
    self.errorThresholdWidget.maximum = 30
    self.errorThresholdWidget.value = 15
    self.errorThresholdWidget.setToolTip('Set error threshold value (mm) for valid tip detection.')
    advancedFormLayout.addRow('Error Threshold:', self.errorThresholdWidget)

    self.layout.addStretch(1)
    
    ####################################
    ##                                ##
    ## UI Behavior                    ##
    ##                                ##
    ####################################
    
    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
    # TODO: Create observer for phase image sequence and link to the self.receivedImage callback function

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.inputModeMagPhase.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.inputModeRealImag.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.firstBaselineVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.secondBaselineVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.firstVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.secondVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.sceneViewButton_red.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.sceneViewButton_yellow.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.sceneViewButton_green.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.tipPredictionSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.roiSizeWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.blobThresholdWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.errorThresholdWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.debugFlagCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    
    # Connect UI buttons to event calls
    self.saveBaselineButton.connect('clicked(bool)', self.saveBaseline)
    self.startTrackingButton.connect('clicked(bool)', self.startTracking)
    self.stopTrackingButton.connect('clicked(bool)', self.stopTracking)
    self.firstBaselineVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.secondBaselineVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.firstVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.secondVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.tipPredictionSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)

    # Internal variables
    self.isBaselineSaved = False
    self.firstBaselineVolume = None
    self.secondBaselineVolume = None
    self.segmentationNode = None
    self.isTrackingOn = False
    self.firstVolume = None
    self.secondVolume = None
    self.sliceIndex = None
    self.inputMode = None
    self.roiSize = None
    self.sliceIndex = None
    self.blobThreshold = None
    self.debugFlag = None

    # Initialize module logic
    self.logic = SimpleNeedleTrackingLogic()
  
    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()
          
    # Refresh button states
    self.updateButtons()

  # Called when the application closes and the module widget is destroyed.
  def cleanup(self):
    self.removeObservers()

  # Called each time the user opens this module.
  # Make sure parameter node exists and observed
  def enter(self):
    self.initializeParameterNode() 

  # Called each time the user opens a different module.
  # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
  def exit(self):
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  # Called just before the scene is closed.
  # Parameter node will be reset, do not use it anymore
  def onSceneStartClose(self, caller, event):
    self.setParameterNode(None)

  # Called just after the scene is closed.
  # If this module is shown while the scene is closed then recreate a new parameter node immediately
  def onSceneEndClose(self, caller, event):
    if self.parent.isEntered:
      self.initializeParameterNode()
        
  # Ensure parameter node exists and observed
  # Parameter node stores all user choices in parameter values, node selections, etc.
  # so that when the scene is saved and reloaded, these settings are restored.
  def initializeParameterNode(self):
    # Load default parameters in logic module
    self.setParameterNode(self.logic.getParameterNode())
            
  # Set and observe parameter node.
  # Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
  def setParameterNode(self, inputParameterNode):
    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)
    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None and self.hasObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode):
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
        self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    # Initial GUI update
    self.updateGUIFromParameterNode()

  # This method is called whenever parameter node is changed.
  # The module GUI is updated to show the current state of the parameter node.
  def updateGUIFromParameterNode(self, caller=None, event=None):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True
    # Update node selectors and sliders
    self.firstBaselineVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('FirstBaselineVolume'))
    self.secondBaselineVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('SecondBaselineVolume'))
    self.manualMaskSelector.setCurrentNode(self._parameterNode.GetNodeReference('ManualMaskSegmentation'))
    self.firstVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('FirstVolume'))
    self.secondVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('SecondVolume'))
    self.inputModeMagPhase.checked = (self._parameterNode.GetParameter('InputMode') == 'MagPhase')
    self.inputModeRealImag.checked = (self._parameterNode.GetParameter('InputMode') == 'RealImag')
    self.sceneViewButton_red.checked = (self._parameterNode.GetParameter('SceneView') == 'Red')
    self.sceneViewButton_yellow.checked = (self._parameterNode.GetParameter('SceneView') == 'Yellow')
    self.sceneViewButton_green.checked = (self._parameterNode.GetParameter('SceneView') == 'Green')
    self.tipPredictionSelector.setCurrentNode(self._parameterNode.GetNodeReference('TipPrediction'))
    self.roiSizeWidget.value = float(self._parameterNode.GetParameter('ROISize'))
    self.blobThresholdWidget.value = float(self._parameterNode.GetParameter('BlobThreshold'))
    self.errorThresholdWidget.value = float(self._parameterNode.GetParameter('ErrorThreshold'))
    self.debugFlagCheckBox.checked = (self._parameterNode.GetParameter('Debug') == 'True')
    
    # Update buttons states
    self.updateButtons()
    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  # This method is called when the user makes any change in the GUI.
  # The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
  def updateParameterNodeFromGUI(self, caller=None, event=None):
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    # Modify all properties in a single batch
    wasModified = self._parameterNode.StartModify()  
    self._parameterNode.SetNodeReferenceID('FirstBaselineVolume', self.firstBaselineVolumeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID('SecondBaselineVolume', self.secondBaselineVolumeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID('ManualMaskSegmentation', self.manualMaskSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID('FirstVolume', self.firstVolumeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID('SecondVolume', self.secondVolumeSelector.currentNodeID)
    self._parameterNode.SetParameter('InputMode', 'MagPhase' if self.inputModeMagPhase.checked else 'RealImag')
    self._parameterNode.SetParameter('SceneView', self.getSelectedView())
    self._parameterNode.SetNodeReferenceID('TipPrediction', self.tipPredictionSelector.currentNodeID)
    self._parameterNode.SetParameter('ROISize', str(self.roiSizeWidget.value))
    self._parameterNode.SetParameter('BlobThreshold', str(self.blobThresholdWidget.value))
    self._parameterNode.SetParameter('ErrorThreshold', str(self.errorThresholdWidget.value))
    self._parameterNode.SetParameter('Debug', 'True' if self.debugFlagCheckBox.checked else 'False')
    self._parameterNode.EndModify(wasModified)
                        
  # Update button states
  def updateButtons(self):
    baselineNodesDefined = self.firstBaselineVolumeSelector.currentNode() and self.secondBaselineVolumeSelector.currentNode()
    rtNodesDefined = self.firstVolumeSelector.currentNode() and self.secondVolumeSelector.currentNode()
    positionNodeDefined = self.tipPredictionSelector.currentNode()
    self.saveBaselineButton.enabled = baselineNodesDefined and not self.isTrackingOn
    self.startTrackingButton.enabled = rtNodesDefined and positionNodeDefined and self.isBaselineSaved and not self.isTrackingOn
    self.stopTrackingButton.enabled = self.isTrackingOn
    
  # Get selected scene view for tracking
  def getSelectedView(self):
    selectedView = None
    if (self.sceneViewButton_red.checked == True):
      selectedView = ('Red')
    elif (self.sceneViewButton_yellow.checked ==True):
      selectedView = ('Yellow')
    elif (self.sceneViewButton_green.checked ==True):
      selectedView = ('Green')
    return selectedView
  
  # Get current slice index displayed in selected viewer
  def getSliceIndex(self, selectedView):   
    layoutManager = slicer.app.layoutManager()
    sliceWidgetLogic = layoutManager.sliceWidget(str(selectedView)).sliceLogic()
    return sliceWidgetLogic.GetSliceIndexFromOffset(sliceWidgetLogic.GetSliceOffset()) - 1
  
  def saveBaseline(self):
    self.isBaselineSaved = True
    self.updateButtons()    
    # Get selected nodes
    self.firstBaselineVolume = self.firstBaselineVolumeSelector.currentNode()
    self.secondBaselineVolume = self.secondBaselineVolumeSelector.currentNode()    
    self.segmentationNode = self.manualMaskSelector.currentNode()
    # Get parameters
    self.inputMode = 'MagPhase' if self.inputModeMagPhase.checked else 'RealImag'
    self.debugFlag = self.debugFlagCheckBox.checked
    # Set base images
    self.logic.updateBaseImages(self.firstBaselineVolume, self.secondBaselineVolume, self.segmentationNode, self.inputMode, self.debugFlag)

    
  def startTracking(self):
    print('Start Tracking')
    self.isTrackingOn = True
    self.updateButtons()
    # Get parameters
    # Get selected nodes
    self.firstVolume = self.firstVolumeSelector.currentNode()
    self.secondVolume = self.secondVolumeSelector.currentNode()    
    self.tipPrediction = self.tipPredictionSelector.currentNode()
    # Create listener to sequence node
    self.addObserver(self.secondVolume, self.secondVolume.ImageDataModifiedEvent, self.receivedImage)
    # Initialize CurrentTrackedTipNode with current prediction value
    self.logic.initializeTipPrediction(self.tipPrediction)
  
  def stopTracking(self):
    self.isTrackingOn = False
    self.updateButtons()
    #TODO: Define what should to be refreshed
    print('Stop Tracking')
    self.removeObserver(self.secondVolume, self.secondVolume.ImageDataModifiedEvent, self.receivedImage)
  
  def receivedImage(self, caller=None, event=None):
    # Execute one tracking cycle
    if self.isTrackingOn:
      # Get parameters
      self.inputMode = 'MagPhase' if self.inputModeMagPhase.checked else 'RealImag'
      self.roiSize = int(self.roiSizeWidget.value)
      self.sliceIndex = self.getSliceIndex(self.getSelectedView())
      self.blobThreshold = float(self.blobThresholdWidget.value)
      self.errorThreshold = float(self.errorThresholdWidget.value)
      self.debugFlag = self.debugFlagCheckBox.checked
      # Get needle tip
      if self.logic.getNeedle(self.firstVolume, self.secondVolume, self.sliceIndex, self.tipPrediction, self.inputMode, self.roiSize, self.blobThreshold, self.errorThreshold, self.debugFlag):
        print('Tracking successful')
      else:
        print('Tracking failed')
      
    
################################################################################################################################################
# Logic Class
################################################################################################################################################

class SimpleNeedleTrackingLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.cliParamNode = None
    
    # Phase rescaling filter
    self.phaseRescaleFilter = sitk.RescaleIntensityImageFilter()
    self.phaseRescaleFilter.SetOutputMaximum(2*np.pi)
    self.phaseRescaleFilter.SetOutputMinimum(0)
    
    # ROI filter
    self.roiFilter = sitk.RegionOfInterestImageFilter()

    # Image file writer
    self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'Debug')
    self.fileWriter = sitk.ImageFileWriter()

    # Check if tracked tip node exists, if not, create a new one
    try:
        self.tipTrackedNode = slicer.util.getNode('CurrentTrackedTipTransform')
    except:
        self.tipTrackedNode = slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(self.tipTrackedNode)
        self.tipTrackedNode.SetName('CurrentTrackedTipTransform')
        print('Created Tracked Tip TransformNode')

    # Base ITK images
    self.sitk_base_m = None
    self.sitk_base_p = None
    self.sitk_mask = None
    self.count = None
    
  # Initialize parameter node with default settings
  def setDefaultParameters(self, parameterNode):
    if not parameterNode.GetParameter('ROISize'):
        parameterNode.SetParameter('ROISize', '15')   
    if not parameterNode.GetParameter('BlobThreshold'):
        parameterNode.SetParameter('BlobThreshold', '2')   
    if not parameterNode.GetParameter('ErrorThreshold'):
        parameterNode.SetParameter('ErrorThreshold', '15.0')   
    if not parameterNode.GetParameter('Debug'):
        parameterNode.SetParameter('Debug', 'False')   
          
  # Create Slicer node and push ITK image to it
  def pushitkToSlicer(self, sitkImage, name, debugFlag=False):
    # Check if tracked tip node exists, if not, create a new one
    try:
      node = slicer.util.getNode(name)
    except:
      node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
      node.SetName(name)
    sitkUtils.PushVolumeToSlicer(sitkImage, node)
    if (debugFlag==True):
      self.fileWriter.Execute(sitkImage, os.path.join(self.path, name)+'.nrrd', False, 0)

  # Return sitk Image from numpy array
  def numpyToitk(self, array, sitkReference, type=None):
    image = sitk.GetImageFromArray(array, isVector=False)
    if (type is None):
      image = sitk.Cast(image, sitkReference.GetPixelID())
    else:
      image = sitk.Cast(image, type)
    image.CopyInformation(sitkReference)
    return image
  
  # Return blank itk Image with same information from reference volume
  def createBlankItk(self, sitkReference, type=None, pixelValue=0):
    image = sitk.Image(sitkReference.GetSize(), sitk.sitkUInt8)
    image.CopyInformation(sitkReference)
    if pixelValue != 0: 
      image = sitk.Not(image)
    if (type is None):
      image = sitk.Cast(image, sitkReference.GetPixelID())
    else:
      image = sitk.Cast(image, type)  
    if pixelValue != 0:
      image = pixelValue*image 
    return image

  # Unwrap phase images with implementation from scikit-image (module: restoration)
  def unwrap_phase_array(self, array_p, array_mask):
    array_p_masked = np.ma.array(array_p, mask=np.logical_not(array_mask).astype(int))  # Mask phase image (inverted mask)
    if array_p.shape[0] == 1: # 2D image in a 3D array: make it 2D array for improved performance
        array_p_unwraped = np.ma.copy(array_p_masked)  # Initialize unwraped array as the original
        array_p_unwraped[0,:,:] = unwrap_phase(array_p_masked[0,:,:], wrap_around=(False,False))               
    else:
        array_p_unwraped = unwrap_phase(array_p_masked, wrap_around=(False,False,False))   
    return array_p_unwraped
  
  def realImagToMagPhase(self, realVolume, imagVolume):
    # Pull the real/imaginary volumes from the MRML scene and convert them to magnitude/phase volumes
    sitk_real = sitkUtils.PullVolumeFromSlicer(realVolume)
    sitk_imag = sitkUtils.PullVolumeFromSlicer(imagVolume)
    numpy_real = sitk.GetArrayFromImage(sitk_real)
    numpy_imag = sitk.GetArrayFromImage(sitk_imag)
    numpy_comp = numpy_real + 1.0j * numpy_imag
    numpy_magn = np.absolute(numpy_comp)
    numpy_phase = np.angle(numpy_comp)
    sitk_magn = self.numpyToitk(numpy_magn, sitk_real)
    sitk_phase = self.numpyToitk(numpy_phase, sitk_real)
    return (sitk_magn, sitk_phase)

  def getMaskFromSegmentation(self, segmentationNode, referenceVolumeNode):
    if segmentationNode is None:
      sitk_reference = sitkUtils.PullVolumeFromSlicer(referenceVolumeNode)
      sitk_mask = self.createBlankItk(sitk_reference, pixelValue=1)
    else:
      labelmapVolumeNode = slicer.util.getFirstNodeByName('mask_labelmap')
      if labelmapVolumeNode is None or labelmapVolumeNode.GetClassName() != 'vtkMRMLLabelMapVolumeNode':      
        labelmapVolumeNode = slicer.vtkMRMLLabelMapVolumeNode()
        slicer.mrmlScene.AddNode(labelmapVolumeNode)
        labelmapVolumeNode.SetName('mask_labelmap')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelmapVolumeNode, referenceVolumeNode)
      sitk_mask = sitkUtils.PullVolumeFromSlicer(labelmapVolumeNode)
    return sitk.Cast(sitk_mask, sitk.sitkUInt8)

  def initializeTipPrediction(self, tipPredictedNode):
    try:
      transformMatrix = vtk.vtkMatrix4x4()
      tipPredictedNode.GetMatrixTransformToWorld(transformMatrix)
      self.tipTrackedNode.SetMatrixTransformToParent(transformMatrix)
      print('Initialized CurrentTrackedTipNode')
      return True
    except:
      print('Could not initilize CurrentTrackedTipNode')
      return False
  
  # Update the stored base images
  def updateBaseImages(self, firstBaselineVolume, secondBaselineVolume, segmentationNode, inputMode, debugFlag=False):
    # Initialize sequence counter
    self.count = 0
    # Get itk images from MRML volume nodes 
    if (inputMode == 'RealImag'): # Convert to magnitude/phase
      (self.sitk_base_m, self.sitk_base_p) = self.realImagToMagPhase(firstBaselineVolume, secondBaselineVolume)
    else:                         # Already as magnitude/phase
      self.sitk_base_m = sitkUtils.PullVolumeFromSlicer(firstBaselineVolume)
      self.sitk_base_p = sitkUtils.PullVolumeFromSlicer(secondBaselineVolume)
    # Force 32Float
    self.sitk_base_m = sitk.Cast(self.sitk_base_m, sitk.sitkFloat32)
    self.sitk_base_p = sitk.Cast(self.sitk_base_p, sitk.sitkFloat32)
    # Phase scaling to angle interval [0 to 2*pi]
    self.sitk_base_p = self.phaseRescaleFilter.Execute(self.sitk_base_p)
    # Get base mask: Generate bool mask from magnitude image to remove background
    self.sitk_mask = self.getMaskFromSegmentation(segmentationNode, firstBaselineVolume)
    # Unwrapped base phase
    numpy_base_p = sitk.GetArrayFromImage(self.sitk_base_p)
    numpy_mask = sitk.GetArrayFromImage(self.sitk_mask)
    self.numpy_base_unwraped_p = self.unwrap_phase_array(numpy_base_p, numpy_mask)# Rescale MARIANA
    # Push debug images to Slicer
    if debugFlag:
      self.pushitkToSlicer(self.sitk_base_m, 'debug_base_m', debugFlag)
      self.pushitkToSlicer(self.sitk_base_p, 'debug_base_p', debugFlag)
      self.pushitkToSlicer(self.sitk_mask, 'debug_mask', debugFlag)
      sitk_base_unwraped_p = self.numpyToitk(self.numpy_base_unwraped_p, self.sitk_base_p)
      self.pushitkToSlicer(sitk_base_unwraped_p, 'debug_base_unwraped_p', debugFlag)
      print('Baseline saved')
    
  
  def getNeedle(self, firstVolume, secondVolume, sliceIndex, tipPrediction, inputMode, roiSize, blobThreshold, errorThreshold, debugFlag=False):
    if (self.sitk_base_m is None) or (self.sitk_base_p is None):
      print('ERROR: Mag/Phase base images were not initialized')    
      return False
    # Increment sequence counter
    self.count += 1    
    # Get itk images from MRML volume nodes 
    if (inputMode == 'RealImag'): # Convert to magnitude/phase
      (sitk_img_m, sitk_img_p) = self.realImagToMagPhase(firstVolume, secondVolume)
    else:                         # Already as magnitude/phase
      sitk_img_m = sitkUtils.PullVolumeFromSlicer(firstVolume)
      sitk_img_p = sitkUtils.PullVolumeFromSlicer(secondVolume)
    # Force 32Float
    sitk_img_m = sitk.Cast(sitk_img_m, sitk.sitkFloat32)
    sitk_img_p = sitk.Cast(sitk_img_p, sitk.sitkFloat32)
    numpy_base_p = sitk.GetArrayFromImage(self.sitk_base_p)
    numpy_mask = sitk.GetArrayFromImage(self.sitk_mask)
    # Phase scaling to angle interval [0 to 2*pi]
    sitk_img_p = self.phaseRescaleFilter.Execute(sitk_img_p) # Rescale MARIANA
    # Push debug images to Slicer     
    if debugFlag:
      self.pushitkToSlicer(sitk_img_m, 'debug_img_m', debugFlag)
      self.pushitkToSlicer(sitk_img_p, 'debug_img_p', debugFlag)

    ######################################
    ##                                  ##
    ## Step 1: Unwrap phase image       ##
    ##                                  ##
    ######################################

    # Unwrapped img phase
    numpy_img_p = sitk.GetArrayFromImage(sitk_img_p)
    numpy_mask = sitk.GetArrayFromImage(self.sitk_mask)
    numpy_img_unwraped_p = self.unwrap_phase_array(numpy_img_p, numpy_mask)

    # Plot
    if debugFlag:
      sitk_img_unwraped_p = self.numpyToitk(numpy_img_unwraped_p, self.sitk_base_p)
      self.pushitkToSlicer(sitk_img_unwraped_p, 'debug_img_unwraped_p', debugFlag)
      

    ######################################
    ##                                  ##
    ## Step 2: Get phase difference     ##
    ##                                  ##
    ######################################

    # Get phase difference
    numpy_diff_p = numpy_img_unwraped_p - self.numpy_base_unwraped_p

    # Set background to mean phase value
    numpy_diff_p = numpy_diff_p.filled(numpy_diff_p.mean())
    sitk_diff_p = self.numpyToitk(numpy_diff_p, sitk_img_p)
    sitk_diff_p = self.phaseRescaleFilter.Execute(sitk_diff_p)

    # Plot
    if debugFlag:
      self.pushitkToSlicer(sitk_diff_p, 'debug_phase_diff', debugFlag)
    
    ######################################
    ##                                  ##
    ## Step 3: Select ROI               ##
    ##                                  ##
    ######################################
    
    # Get tip predicted coordinates: 3D Slicer (RAS)
    transformMatrix = vtk.vtkMatrix4x4()
    tipPrediction.GetMatrixTransformToWorld(transformMatrix)
    tipHorizontal = transformMatrix.GetElement(0,3) # Right-Left
    tipSlice = transformMatrix.GetElement(1,3)      # Anterior-Posteriot
    tipVertical = transformMatrix.GetElement(2,3)   # Inferior-Superior
    tipRAS = (tipHorizontal, tipSlice, tipVertical)

    # Convert to pixel coordinates in ITK (LPS)
    tipIndex = sitk_img_p.TransformPhysicalPointToIndex((-tipHorizontal, -tipSlice, tipVertical))
    sliceDepth = sitk_img_p.GetDepth()
    
    # Define ROI filter size/index (pixels)
    self.roiFilter.SetSize((roiSize,roiSize,sliceDepth))
    roiIndex = (round(tipIndex[0]-0.5*roiSize), round(tipIndex[1]-0.5*roiSize), 0)
    self.roiFilter.SetIndex(roiIndex)

    try:
      sitk_roi = self.roiFilter.Execute(sitk_diff_p)
    except:
      print('Invalid ROI')
      return False
    sitk_roi = self.phaseRescaleFilter.Execute(sitk_roi)
    # Plot
    if debugFlag:
      self.pushitkToSlicer(sitk_roi, 'debug_roi', debugFlag)    
    
    ####################################
    ##                                ##
    ## Step 4: Image gradient         ##
    ##                                ##
    ####################################
    
    # 3D Gradient Filter only works with >=4 slices
    # Perform 2D gradient instead
    gradientFilter = sitk.GradientMagnitudeRecursiveGaussianImageFilter()
    sitk_phaseGradient = gradientFilter.Execute(sitk_roi[:,:,sliceIndex])
    sitk_phaseGradient = self.phaseRescaleFilter.Execute(sitk_phaseGradient)
    
    # Plot
    if debugFlag:
      # Put slice in the volume
      sitk_phaseGradientVolume = self.createBlankItk(sitk_roi, type=sitk.sitkFloat32)
      sitk_phaseGradientVolume[:,:,sliceIndex] = sitk_phaseGradient
      self.pushitkToSlicer(sitk_phaseGradientVolume, 'debug_phase_gradient', debugFlag)    

    ####################################
    ##                                ##
    ## Step 5: Blob detection         ##
    ##                                ##
    ####################################

    # Threshold roi to create blobs
    sitk_blobs = (sitk_phaseGradient > blobThreshold)
    # Put slice in the volume
    sitk_blobsVolume = self.createBlankItk(sitk_roi, sitk_blobs.GetPixelID())
    sitk_blobsVolume[:,:,sliceIndex] = sitk_blobs
    # Plot
    if debugFlag:
      self.pushitkToSlicer(sitk_blobsVolume, 'debug_blobs', debugFlag)  
          
    # Label blobs
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(sitk.ConnectedComponent(sitk_blobsVolume))

    # Get blobs sizes and centroid physical coordinates
    labels_size = []
    labels_centroid = []
    labels_depth = []
    for l in stats.GetLabels():
        if debugFlag:
            print('Label %s: -> Size: %s, Center: %s, Flatness: %s, Elongation: %s' %(l, stats.GetNumberOfPixels(l), stats.GetCentroid(l), stats.GetFlatness(l), stats.GetElongation(l)))
        if (stats.GetElongation(l) < 4): 
            labels_size.append(stats.GetNumberOfPixels(l))
            labels_centroid.append(stats.GetCentroid(l))    
            labels_depth.append(stats.GetCentroid(l)[2])

    ####################################
    ##                                ##
    ## Step 6: Get tip physical point ##
    ##                                ##
    ####################################
    # Check number of centroids found
    if len(labels_size)>15:
      print('Too many centroids, probably noise')
      return False
    # Reasonable number of centroids: get the largest one
    try:
      sorted_by_size = np.argsort(labels_size) 
      first_largest = sorted_by_size[-1]
      # second_largest = sorted_by_size[-2]
    except:
      print('No centroids found')
      return False
    
    # Check centroid size with respect to ROI size
    if (labels_size[first_largest] > 0.5*roiSize*0.5*roiSize):
      print('Centroid too big, probably noise')
      return False
    
    # # Get significantly bigger centroid
    # if (labels_size[first_largest] > 3.5*labels_size[second_largest]):
    #   label_index = first_largest
    # else: # Get centroid further inserted
    #   label_index = labels_depth.index(max(labels_depth))

    # Get selected centroid center
    # center = labels_centroid[label_index]
    center = labels_centroid[first_largest]
    # Convert to 3D Slicer coordinates (RAS)
    centerRAS = (-center[0], -center[1], center[2])

    # Plot
    if debugFlag:
      # print('Chosen label: %i' %(label_index+1))
      print('Chosen label: %i' %(first_largest+1))
      print(centerRAS)

    # Calculate prediction error
    predError = sqrt(pow((tipRAS[0]-centerRAS[0]),2)+pow((tipRAS[1]-centerRAS[1]),2)+pow((tipRAS[2]-centerRAS[2]),2))
    # Check error threshold
    if(predError>errorThreshold):
      print('Tip too far from prediction: Err = %f' %predError)
      return False
    
    # Push coordinates to tip Node
    transformMatrix.SetElement(0,3, centerRAS[0])
    transformMatrix.SetElement(1,3, centerRAS[1])
    transformMatrix.SetElement(2,3, centerRAS[2])
    self.tipTrackedNode.SetMatrixTransformToParent(transformMatrix)

    return True
