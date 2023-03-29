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
    imagesCollapsibleButton.text = 'Image selection'
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
    imagesFormLayout.addRow('Magnitude/Real Image: ', self.firstVolumeSelector)

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
    imagesFormLayout.addRow('Phase/Imaginary Image: ', self.secondVolumeSelector)
   
    # Select which scene view to track
    self.sceneViewButton_red = qt.QRadioButton('Red')
    self.sceneViewButton_yellow = qt.QRadioButton('Yellow')
    self.sceneViewButton_green = qt.QRadioButton('Green')
    self.sceneViewButton_green.checked = 1
    self.sceneViewButtonGroup = qt.QButtonGroup()
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_red)
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_yellow)
    self.sceneViewButtonGroup.addButton(self.sceneViewButton_green)
    layout = qt.QHBoxLayout()
    layout.addWidget(self.sceneViewButton_red)
    layout.addWidget(self.sceneViewButton_yellow)
    layout.addWidget(self.sceneViewButton_green)
    imagesFormLayout.addRow('Scene view:',layout)


    ## Needle Tracking                
    ####################################

    trackingCollapsibleButton = ctk.ctkCollapsibleButton()
    trackingCollapsibleButton.text = 'Needle tracking'
    self.layout.addWidget(trackingCollapsibleButton)
    trackingFormLayout = qt.QFormLayout(trackingCollapsibleButton)
    
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
    
    # Mask threshold
    self.maskThresholdWidget = ctk.ctkSliderWidget()
    self.maskThresholdWidget.singleStep = 1
    self.maskThresholdWidget.setDecimals(0)
    self.maskThresholdWidget.minimum = 0
    self.maskThresholdWidget.maximum = 255
    self.maskThresholdWidget.value = 60
    self.maskThresholdWidget.setToolTip('Set intensity threshold value (0-255) for creating tissue mask. Voxels that have intensities lower than this value will be masked out.')
    advancedFormLayout.addRow('Mask Threshold:', self.maskThresholdWidget)
    
    # Mask closing
    self.maskClosingWidget = ctk.ctkSliderWidget()
    self.maskClosingWidget.singleStep = 1
    self.maskClosingWidget.setDecimals(0)
    self.maskClosingWidget.minimum = 0
    self.maskClosingWidget.maximum = 30
    self.maskClosingWidget.value = 15
    self.maskClosingWidget.setToolTip('Set kernel size (px) for closing operation on mask.')
    advancedFormLayout.addRow('Mask Closing:', self.maskClosingWidget)
    
    # ROI size
    self.roiSizeWidget = ctk.ctkSliderWidget()
    self.roiSizeWidget.singleStep = 1
    self.roiSizeWidget.setDecimals(0)
    self.roiSizeWidget.minimum = 30
    self.roiSizeWidget.maximum = 100
    self.roiSizeWidget.value = 15
    self.roiSizeWidget.setToolTip('Set ROI window size (px).')
    advancedFormLayout.addRow('ROI Size:', self.roiSizeWidget)
    
    # Blob threshold
    self.blobThresholdWidget = ctk.ctkSliderWidget()
    self.blobThresholdWidget.singleStep = 0.1
    self.blobThresholdWidget.minimum = 0
    self.blobThresholdWidget.maximum = 2*np.pi
    self.blobThresholdWidget.value = np.pi
    self.blobThresholdWidget.setToolTip('Set phase threshold value (0-2pi rad) for blob detection.')
    advancedFormLayout.addRow('Blob Threshold:', self.blobThresholdWidget)
    
    # Error threshold
    self.errorThresholdWidget = ctk.ctkSliderWidget()
    self.errorThresholdWidget.singleStep = 0.1
    self.errorThresholdWidget.minimum = 0
    self.errorThresholdWidget.maximum = 15
    self.errorThresholdWidget.value = 5
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
    self.firstVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.secondVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.sceneViewButton_red.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.sceneViewButton_yellow.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.sceneViewButton_green.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.tipPredictionSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateParameterNodeFromGUI)
    self.maskThresholdWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.maskClosingWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.roiSizeWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.blobThresholdWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.errorThresholdWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.debugFlagCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    
    # Connect UI buttons to event calls
    self.startTrackingButton.connect('clicked(bool)', self.startTracking)
    self.stopTrackingButton.connect('clicked(bool)', self.stopTracking)
    self.firstVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.secondVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)
    self.tipPredictionSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.updateButtons)

    # Internal variables
    self.isTrackingOn = False
    self.firstVolume = None
    self.secondVolume = None
    self.sliceIndex = None
    self.inputMode = None
    self.maskThreshold = None
    self.maskClosing = None
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
    self.firstVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('FirstVolume'))
    self.secondVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference('SecondVolume'))
    self.inputModeMagPhase.checked = (self._parameterNode.GetParameter('InputMode') == 'MagPhase')
    self.inputModeRealImag.checked = (self._parameterNode.GetParameter('InputMode') == 'RealImag')
    self.sceneViewButton_red.checked = (self._parameterNode.GetParameter('SceneView') == 'Red')
    self.sceneViewButton_yellow.checked = (self._parameterNode.GetParameter('SceneView') == 'Yellow')
    self.sceneViewButton_green.checked = (self._parameterNode.GetParameter('SceneView') == 'Green')
    self.tipPredictionSelector.setCurrentNode(self._parameterNode.GetNodeReference('TipPrediction'))
    self.maskThresholdWidget.value = float(self._parameterNode.GetParameter('MaskThreshold'))
    self.maskClosingWidget.value = float(self._parameterNode.GetParameter('MaskClosing'))
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
    self._parameterNode.SetNodeReferenceID('FirstVolume', self.firstVolumeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID('SecondVolume', self.secondVolumeSelector.currentNodeID)
    self._parameterNode.SetParameter('InputMode', 'MagPhase' if self.inputModeMagPhase.checked else 'RealImag')
    self._parameterNode.SetParameter('SceneView', self.getSelectedView())
    self._parameterNode.SetNodeReferenceID('TipPrediction', self.tipPredictionSelector.currentNodeID)
    self._parameterNode.SetParameter('MaskThreshold', str(self.maskThresholdWidget.value))
    self._parameterNode.SetParameter('MaskClosing', str(self.maskClosingWidget.value))
    self._parameterNode.SetParameter('ROISize', str(self.roiSizeWidget.value))
    self._parameterNode.SetParameter('BlobThreshold', str(self.blobThresholdWidget.value))
    self._parameterNode.SetParameter('ErrorThreshold', str(self.errorThresholdWidget.value))
    self._parameterNode.SetParameter('Debug', 'True' if self.debugFlagCheckBox.checked else 'False')
    self._parameterNode.EndModify(wasModified)
                        
  # Update button states
  def updateButtons(self):
    volumeNodesDefined = self.firstVolumeSelector.currentNode() and self.secondVolumeSelector.currentNode()
    positionNodeDefined = self.tipPredictionSelector.currentNode()
    self.startTrackingButton.enabled = volumeNodesDefined and positionNodeDefined and not self.isTrackingOn
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
  
  def startTracking(self):
    print('UI: startTracking()')
    self.isTrackingOn = True
    self.updateButtons()
    # Get parameters
    self.inputMode = 'MagPhase' if self.inputModeMagPhase.checked else 'RealImag'
    self.maskThreshold = int(self.maskThresholdWidget.value)
    self.maskClosing = int(self.maskClosingWidget.value)
    self.roiSize = int(self.roiSizeWidget.value)
    self.sliceIndex = self.getSliceIndex(self.getSelectedView())
    self.blobThreshold = float(self.blobThresholdWidget.value)
    self.errorThreshold = float(self.errorThresholdWidget.value)
    self.debugFlag = self.debugFlagCheckBox.checked
    # Get selected nodes
    self.firstVolume = self.firstVolumeSelector.currentNode()
    self.secondVolume = self.secondVolumeSelector.currentNode()    
    self.tipPrediction = self.tipPredictionSelector.currentNode()
    # Set base images
    self.logic.updateBaseImages(self.firstVolume, self.secondVolume, self.inputMode, self.maskThreshold, self.maskClosing, self.debugFlag)
    # Create listener to sequence node
    self.addObserver(self.secondVolume, self.secondVolume.ImageDataModifiedEvent, self.receivedImage)
  
  def stopTracking(self):
    self.isTrackingOn = False
    self.updateButtons()
    #TODO: Define what should to be refreshed
    print('UI: stopTracking()')
    self.removeObserver(self.secondVolume, self.secondVolume.ImageDataModifiedEvent, self.receivedImage)
  
  def receivedImage(self, caller=None, event=None):
    if self.isTrackingOn:
      print('UI: receivedImage()')
      # Execute one tracking cycle
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
    print('Logic: __init__')
    
    # Phase rescaling filter
    self.phaseRescaleFilter = sitk.RescaleIntensityImageFilter()
    self.phaseRescaleFilter.SetOutputMaximum(2*np.pi)
    self.phaseRescaleFilter.SetOutputMinimum(0)
    
    # ROI filter
    self.roiFilter = sitk.RegionOfInterestImageFilter()

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
    if not parameterNode.GetParameter('MaskThreshold'):
        parameterNode.SetParameter('MaskThreshold', '60')
    if not parameterNode.GetParameter('MaskClosing'):
        parameterNode.SetParameter('MaskClosing', '15')
    if not parameterNode.GetParameter('ROISize'):
        parameterNode.SetParameter('ROISize', '15')   
    if not parameterNode.GetParameter('BlobThreshold'):
        parameterNode.SetParameter('BlobThreshold', '3.14')   
    if not parameterNode.GetParameter('ErrorThreshold'):
        parameterNode.SetParameter('ErrorThreshold', '5.0')   
    if not parameterNode.GetParameter('Debug'):
        parameterNode.SetParameter('Debug', 'False')   
          
  # Create Slicer node and push ITK image to it
  def pushitkToSlicer(self, sitkImage, name):
    node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')
    node.SetName(name)
    sitkUtils.PushVolumeToSlicer(sitkImage, name, 0, True)
        
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
  def createBlankItk(self, sitkReference, type=None):
    if (type is None):
      image = sitk.Image(sitkReference.GetSize(), sitkReference.GetPixelID())
    else:
      image = sitk.Image(sitkReference.GetSize(), type)  
    image.CopyInformation(sitkReference)
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


  # Update the stored base images
  def updateBaseImages(self, firstVolume, secondVolume, inputMode, maskThreshold, maskClosing, debugFlag=False):
    # Initialize sequence counter
    self.count = 0
    # Get itk images from MRML volume nodes 
    if (inputMode == 'RealImag'): # Convert to magnitude/phase
      (self.sitk_base_m, self.sitk_base_p) = self.realImagToMagPhase(firstVolume, secondVolume)
    else:                         # Already as magnitude/phase
      self.sitk_base_m = sitkUtils.PullVolumeFromSlicer(firstVolume)
      self.sitk_base_p = sitkUtils.PullVolumeFromSlicer(secondVolume)
    # Phase scaling to angle interval [0 to 2*pi]
    self.sitk_base_p = self.phaseRescaleFilter.Execute(self.sitk_base_p) 
    # Get base mask: Generate bool mask from magnitude image to remove background
    self.sitk_mask = (self.sitk_base_m > maskThreshold)
    closingFilter = sitk.BinaryMorphologicalClosingImageFilter()    # Closing to fill bigger holes
    closingFilter.SetKernelRadius(maskClosing)
    self.sitk_mask = closingFilter.Execute(self.sitk_mask)  
    # Unwrapped base phase
    numpy_base_p = sitk.GetArrayFromImage(self.sitk_base_p)
    numpy_mask = sitk.GetArrayFromImage(self.sitk_mask)
    self.numpy_base_unwraped_p = self.unwrap_phase_array(numpy_base_p, numpy_mask)
    # Push debug images to Slicer
    if debugFlag:
      self.pushitkToSlicer(self.sitk_base_m, 'debug_base_m')
      self.pushitkToSlicer(self.sitk_base_p, 'debug_base_p')
      self.pushitkToSlicer(self.sitk_mask, 'debug_mask')
      sitk_base_unwraped_p = self.numpyToitk(self.numpy_base_unwraped_p, self.sitk_base_p)
      self.pushitkToSlicer(sitk_base_unwraped_p, 'debug_base_unwraped_p')
  
  
  def getNeedle(self, firstVolume, secondVolume, sliceIndex, tipPrediction, inputMode, roiSize, blobThreshold, errorThreshold, debugFlag=False):
    # Using only one slice volumes for now
    # TODO: extend to 3 stacked slices
    print('Logic: getNeedle()')    
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
    # Phase scaling to angle interval [0 to 2*pi]
    sitk_img_p = self.phaseRescaleFilter.Execute(sitk_img_p)
    # Push debug images to Slicer     
    if debugFlag:
      self.pushitkToSlicer(sitk_img_m, 'debug_img_m_'+str(self.count))
      self.pushitkToSlicer(sitk_img_p, 'debug_img_p_'+str(self.count))

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
      self.pushitkToSlicer(sitk_img_unwraped_p, 'debug_img_unwraped_p_'+str(self.count))

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
      self.pushitkToSlicer(sitk_diff_p, 'debug_phase_diff_'+str(self.count))
    
    ######################################
    ##                                  ##
    ## Step 3: Select ROI               ##
    ##                                  ##
    ######################################
    
    # Get tip predicted coordinates: 3D Slicer (RAS)
    transformMatrix = vtk.vtkMatrix4x4()
    tipPrediction.GetMatrixTransformToParent(transformMatrix)
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
      self.pushitkToSlicer(sitk_roi, 'debug_roi_'+str(self.count))    
    
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
      sitk_phaseGradientVolume = self.createBlankItk(sitk_roi)
      sitk_phaseGradientVolume[:,:,sliceIndex] = sitk_phaseGradient
      self.pushitkToSlicer(sitk_phaseGradientVolume, 'debug_phase_gradient_'+str(self.count))    

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
      self.pushitkToSlicer(sitk_blobsVolume, 'debug_blobs_'+str(self.count))  
          
    # Label blobs
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(sitk.ConnectedComponent(sitk_blobsVolume))

    # Get blobs sizes and centroid physical coordinates
    labels_size = []
    labels_centroid = []
    for l in stats.GetLabels():
      if debugFlag:
        print('Label %s: -> Size: %s, Center: %s, Flatness: %s, Elongation: %s' %(l, stats.GetNumberOfPixels(l), stats.GetCentroid(l), stats.GetFlatness(l), stats.GetElongation(l)))
        if (stats.GetElongation(l) < 4): 
          labels_size.append(stats.GetNumberOfPixels(l))
          labels_centroid.append(stats.GetCentroid(l))    

    ####################################
    ##                                ##
    ## Step 6: Get tip physical point ##
    ##                                ##
    ####################################
    
    # Get biggest centroid
    try:
      label_index = labels_size.index(max(labels_size))
    except:
      print('No centroids found')
      return False
    center = labels_centroid[label_index]
    
    # Convert to 3D Slicer coordinates (RAS)
    centerRAS = (-center[0], -center[1], center[2])

    # Plot
    if debugFlag:
      print('Chosen label: %i' %(label_index+1))
      print(centerRAS)

    # Calculate prediction error
    predError = sqrt(pow((tipRAS[0]-centerRAS[0]),2)+pow((tipRAS[1]-centerRAS[1]),2)+pow((tipRAS[2]-centerRAS[2]),2))

    # Check error threshold
    if(predError>errorThreshold):
      print('Tip too far from prediction')
      return False

    # Push coordinates to tip Node
    transformMatrix.SetElement(0,3, centerRAS[0])
    transformMatrix.SetElement(1,3, centerRAS[1])
    transformMatrix.SetElement(2,3, centerRAS[2])
    self.tipTrackedNode.SetMatrixTransformToParent(transformMatrix)

    return True
