import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
from SlicerDevelopmentToolboxUtils.mixins import ModuleLogicMixin, ModuleWidgetMixin
from SlicerDevelopmentToolboxUtils.icons import Icons


#
# ZFrameRegistrationWithROI
#

class OpenSourceZFrameRegistration(object):
  def __init__(self, mrmlScene, volume=None):
    self.inputVolume = volume
    self.mrmlScene = mrmlScene
    self.outputTransform = None
    self._setTransform()

  def setInputVolume(self, volume):
    self.inputVolume = volume
    self._setTransform()

  def _setTransform(self):
    if self.inputVolume:
      seriesNumber = self.inputVolume.GetName().split(":")[0]
      name = seriesNumber + "-ZFrameTransform"
      if self.outputTransform:
        self.mrmlScene.RemoveNode(self.outputTransform)
        self.outputTransform = None
      self.outputTransform = slicer.vtkMRMLLinearTransformNode()
      self.outputTransform.SetName(name)
      self.mrmlScene.AddNode(self.outputTransform)

  def runRegistration(self, start, end):
    if self.inputVolume:
      assert start != -1 and end != -1

      params = {'inputVolume': self.inputVolume, 'startSlice': start, 'endSlice': end,
                'outputTransform': self.outputTransform}
      slicer.cli.run(slicer.modules.zframeregistration, None, params, wait_for_completion=True)


class ZFrameRegistrationWithROI(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ZFrameRegistrationWithROI"  # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Christian Herz (SPL), Longquan Chen (SPL), Junichi Tokuda (SPL), "
                                "Simon Di Maio (SPL), Andrey Fedorov (SPL). Updated by Mariana Bernardes (SPL)"]
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.

Update (Nov 22, 2023): Replaced AnnotationROINode (legacy) by MarkupsROINode.

"""  # replace with organization, grant and thanks.


#
# ZFrameRegistrationWithROIWidget
#

class ZFrameRegistrationWithROIWidget(ScriptedLoadableModuleWidget, ModuleWidgetMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def onReload(self, moduleName="ZFrameRegistrationWithROI"):
    self.logic.cleanup()
    self.disconnectAll()
    slicer.mrmlScene.Clear(0)
    ScriptedLoadableModuleWidget.onReload(self)
    # globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    self.logic = ZFrameRegistrationWithROILogic()
    self.setupSliceWidgets()
    # self.annotationLogic = slicer.modules.annotations.logic()
    self.markupsLogic = slicer.modules.markups.logic()
    self.zFrameRegistrationClass = OpenSourceZFrameRegistration
    self.roiObserverTag = None
    self.coverTemplateROI = None
    self.setupGUIAndConnections()

  def disconnectAll(self):
    self.zFrameTemplateVolumeSelector.disconnect('currentNodeChanged(bool)')
    self.retryZFrameRegistrationButton.clicked.disconnect()
    self.runZFrameRegistrationButton.clicked.disconnect()

  def setupSliceWidgets(self):
    self.createSliceWidgetClassMembers("Red")
    self.createSliceWidgetClassMembers("Yellow")
    self.createSliceWidgetClassMembers("Green")

  def setupGUIAndConnections(self):
    # Select zFrame model
    modelGroupBox = qt.QGroupBox()
    self.layout.addWidget(modelGroupBox)
    modelLayout = qt.QFormLayout(modelGroupBox)    
    self.modelFileSelector = qt.QComboBox()
    modelPath= os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources/zframe')
    self.modelList = [f for f in os.listdir(modelPath) if os.path.isfile(os.path.join(modelPath, f))]
    self.modelFileSelector.addItems(self.modelList)
    modelLayout.addRow('zFrame Model:',self.modelFileSelector)    
    
    iconSize = qt.QSize(36, 36)
    self.inputVolumeGroupBox = qt.QGroupBox()
    self.inputVolumeGroupBoxLayout = qt.QFormLayout()
    self.inputVolumeGroupBox.setLayout(self.inputVolumeGroupBoxLayout)
    self.inputVolumeGroupBox.setFlat(True)
    self.zFrameTemplateVolumeSelector = self.createComboBox(nodeTypes=["vtkMRMLScalarVolumeNode", ""])
    self.inputVolumeGroupBoxLayout.addRow("ZFrame template volume: ", self.zFrameTemplateVolumeSelector)
    self.layout.addWidget(self.inputVolumeGroupBox)
    self.layout.addStretch()
    self.zFrameRegistrationManualIndexesGroupBox = qt.QGroupBox("Use manual start/end indexes")
    self.zFrameRegistrationManualIndexesGroupBox.setCheckable(True)
    self.zFrameRegistrationManualIndexesGroupBoxLayout = qt.QGridLayout()
    self.zFrameRegistrationManualIndexesGroupBox.setLayout(self.zFrameRegistrationManualIndexesGroupBoxLayout)
    self.zFrameRegistrationManualIndexesGroupBox.checked = False
    self.zFrameRegistrationStartIndex = qt.QSpinBox()
    self.zFrameRegistrationEndIndex = qt.QSpinBox()
    hBox = qt.QWidget()
    hBox.setLayout(qt.QHBoxLayout())
    hBox.layout().addWidget(qt.QLabel("start"))
    hBox.layout().addWidget(self.zFrameRegistrationStartIndex)
    hBox.layout().addWidget(qt.QLabel("end"))
    hBox.layout().addWidget(self.zFrameRegistrationEndIndex)
    self.zFrameRegistrationManualIndexesGroupBoxLayout.addWidget(hBox, 1, 1, qt.Qt.AlignRight)
    self.runZFrameRegistrationButton = self.createButton("", enabled=False, icon=Icons.apply, iconSize=iconSize,
                                                         toolTip="Run ZFrame Registration")
    self.retryZFrameRegistrationButton = self.createButton("", enabled=False, icon=Icons.retry, iconSize=iconSize,
                                                           toolTip="Reset")
    self.layout.addWidget(self.zFrameRegistrationManualIndexesGroupBox)
    widget = qt.QWidget()
    widget.setLayout(qt.QHBoxLayout())
    widget.layout().addWidget(self.runZFrameRegistrationButton)
    widget.layout().addWidget(self.retryZFrameRegistrationButton)
    self.layout.addWidget(widget)
    self.layout.addStretch(1)
    self.zFrameTemplateVolumeSelector.connect('currentNodeChanged(bool)', self.loadVolumeAndEnableEditor)
    self.retryZFrameRegistrationButton.clicked.connect(self.onRetryZFrameRegistrationButtonClicked)
    self.runZFrameRegistrationButton.clicked.connect(self.onApplyZFrameRegistrationButtonClicked)
    
  def loadVolumeAndEnableEditor(self):
    zFrameTemplateVolume = self.zFrameTemplateVolumeSelector.currentNode()
    if zFrameTemplateVolume:
      self.logic.templateVolume = zFrameTemplateVolume
      self.activateZFrameRegistration()
    else:
      self.logic.templateVolume = None
      self.resetZFrameRegistration()
      self.setROIMode(False)
      self.setBackgroundAndForegroundIDs(foregroundVolumeID=None, backgroundVolumeID=None)

  def activateZFrameRegistration(self):
    self.zFrameRegistrationManualIndexesGroupBox.checked = False
    if self.logic.templateVolume:
      self.resetZFrameRegistration()
      self.setBackgroundAndForegroundIDs(foregroundVolumeID=None, backgroundVolumeID=self.logic.templateVolume.GetID())
      self.redSliceNode.SetSliceVisible(True)
      if self.zFrameRegistrationClass is OpenSourceZFrameRegistration:
        self.addROIObserver()
        self.setROIMode(True)

  def resetZFrameRegistration(self):
    self.logic.clearVolumeNodes()
    if self.coverTemplateROI:
      slicer.mrmlScene.RemoveNode(self.coverTemplateROI)
      self.coverTemplateROI = None
    self.runZFrameRegistrationButton.enabled = False
    self.retryZFrameRegistrationButton.enabled = False
    if self.logic.zFrameModelNode:
      self.logic.zFrameModelNode.GetDisplayNode().SetSliceIntersectionVisibility(False)
      self.logic.zFrameModelNode.SetDisplayVisibility(False)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

  def setBackgroundAndForegroundIDs(self, foregroundVolumeID, backgroundVolumeID):
    self.redCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    self.redCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    self.redSliceNode.SetOrientationToAxial()
    self.yellowCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    self.yellowCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    self.yellowSliceNode.SetOrientationToSagittal()
    self.greenCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    self.greenCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    self.greenSliceNode.SetOrientationToCoronal()

  def addROIObserver(self):
    @vtk.calldata_type(vtk.VTK_OBJECT)
    def onNodeAdded(caller, event, calldata):
      node = calldata
      # if isinstance(node, slicer.vtkMRMLAnnotationROINode) :
      if isinstance(node, slicer.vtkMRMLMarkupsROINode) : #Mariana
        self.removeROIObserver()
        self.coverTemplateROI = node
        self.runZFrameRegistrationButton.enabled = self.isRegistrationPossible()

    if self.roiObserverTag:
      self.removeROIObserver()
    self.roiObserverTag = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, onNodeAdded)

  def isRegistrationPossible(self):
    return self.coverTemplateROI is not None and self.logic.templateVolume

  def removeROIObserver(self):
    if self.roiObserverTag:
      self.roiObserverTag = slicer.mrmlScene.RemoveObserver(self.roiObserverTag)

  def setROIMode(self, mode):
    if mode == False:
      self.markupsLogic.StopPlaceMode(False)
    else:
      self.markupsLogic.StartPlaceMode(False)
    mrmlScene = self.markupsLogic.GetMRMLScene()
    selectionNode = mrmlScene.GetNthNodeByClass(0, "vtkMRMLSelectionNode")
    # selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationROINode")
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsROINode") # Mariana    

  def onApplyZFrameRegistrationButtonClicked(self):
    self.retryZFrameRegistrationButton.enabled = True
    zFrameTemplateVolume = self.logic.templateVolume
    zFrameModelName = self.modelFileSelector.currentText
    try:
      # self.annotationLogic.SetAnnotationLockedUnlocked(self.coverTemplateROI.GetID())
      self.markupsLogic.ToggleAllControlPointsLocked(self.coverTemplateROI) # Mariana
      
      if not self.zFrameRegistrationManualIndexesGroupBox.checked:
        self.logic.runZFrameOpenSourceRegistration(zFrameModelName, zFrameTemplateVolume, self.coverTemplateROI)
        self.zFrameRegistrationStartIndex.value = self.logic.startIndex
        self.zFrameRegistrationEndIndex.value = self.logic.endIndex
      else:
        startIndex = self.zFrameRegistrationStartIndex.value
        endIndex = self.zFrameRegistrationEndIndex.value
        self.logic.runZFrameOpenSourceRegistration(zFrameModelName, zFrameTemplateVolume, self.coverTemplateROI, start=startIndex,
                                                   end=endIndex)
      self.setBackgroundAndForegroundIDs(foregroundVolumeID=None, backgroundVolumeID=self.logic.templateVolume.GetID())
      self.logic.zFrameModelNode.SetAndObserveTransformNodeID(self.logic.openSourceRegistration.outputTransform.GetID())
      self.logic.zFrameModelNode.GetDisplayNode().SetSliceIntersectionVisibility(True)
      self.logic.zFrameModelNode.SetDisplayVisibility(True)
    except AttributeError as exc:
      slicer.util.errorDisplay("An error occurred. For further information click 'Show Details...'",
                               windowTitle=self.__class__.__name__, detailedText=str(exc.message))

  def onRetryZFrameRegistrationButtonClicked(self):
    self.activateZFrameRegistration()


#
# ZFrameRegistrationWithROILogic
#

class ZFrameRegistrationWithROILogic(ScriptedLoadableModuleLogic, ModuleLogicMixin):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  # ZFRAME_MODEL_PATH = 'zframe-model.vtk'
  # ZFRAME_MODEL_NAME = 'ZFrameModel'

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.redSliceWidget = slicer.app.layoutManager().sliceWidget("Red")
    self.redSliceView = self.redSliceWidget.sliceView()
    self.redSliceLogic = self.redSliceWidget.sliceLogic()
    self.otsuFilter = sitk.OtsuThresholdImageFilter()
    self.openSourceRegistration = OpenSourceZFrameRegistration(slicer.mrmlScene)
    self.templateVolume = None
    self.zFrameCroppedVolume = None
    self.zFrameLabelVolume = None
    self.zFrameMaskedVolume = None
    self.otsuOutputVolume = None
    self.startIndex = None
    self.endIndex = None
    self.zFrameModelNode = None
    self.resetAndInitializeData()

  def resetAndInitializeData(self):
    self.cleanup()
    self.startIndex = None
    self.endIndex = None

  def clearVolumeNodes(self):
    if self.zFrameCroppedVolume:
      slicer.mrmlScene.RemoveNode(self.zFrameCroppedVolume)
      self.zFrameCroppedVolume = None
    if self.zFrameLabelVolume:
      slicer.mrmlScene.RemoveNode(self.zFrameLabelVolume)
      self.zFrameLabelVolume = None
    if self.zFrameMaskedVolume:
      slicer.mrmlScene.RemoveNode(self.zFrameMaskedVolume)
      self.zFrameMaskedVolume = None
    if self.otsuOutputVolume:
      slicer.mrmlScene.RemoveNode(self.otsuOutputVolume)
      self.otsuOutputVolume = None

  def cleanup(self):
    self.clearVolumeNodes()
    self.clearOldCalculationNodes()

  def clearOldCalculationNodes(self):
    if self.openSourceRegistration.inputVolume:
      slicer.mrmlScene.RemoveNode(self.openSourceRegistration.inputVolume)
      self.openSourceRegistration.inputVolume = None
    if self.zFrameModelNode:
      slicer.mrmlScene.RemoveNode(self.zFrameModelNode)
      self.zFrameModelNode = None
    if self.openSourceRegistration.outputTransform:
      slicer.mrmlScene.RemoveNode(self.openSourceRegistration.outputTransform)
      self.openSourceRegistration.outputTransform = None

  def loadZFrameModel(self, zFrameModelName):
    if self.zFrameModelNode:
      slicer.mrmlScene.RemoveNode(self.zFrameModelNode)
      self.zFrameModelNode = None
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    zFrameModelPath = os.path.join(currentFilePath, "Resources", "zframe", zFrameModelName)
    _, self.zFrameModelNode = slicer.util.loadModel(zFrameModelPath, returnNode=True)
    self.zFrameModelNode.SetName('ZFrameModel')
    modelDisplayNode = self.zFrameModelNode.GetDisplayNode()
    modelDisplayNode.SetColor(1, 1, 0)
    self.zFrameModelNode.SetDisplayVisibility(False)

  def runZFrameOpenSourceRegistration(self, zFrameModelName, zFrameTemplateVolume, coverTemplateROI, start=None, end=None):
    self.startIndex = start
    self.endIndex = end
    self.loadZFrameModel(zFrameModelName) # Load selected zFrame Model
    self.zFrameCroppedVolume = self.createCroppedVolume(zFrameTemplateVolume, coverTemplateROI)
    self.zFrameLabelVolume = self.createLabelMapFromCroppedVolume(self.zFrameCroppedVolume, "labelmap")
    self.zFrameMaskedVolume = self.createMaskedVolume(zFrameTemplateVolume, self.zFrameLabelVolume,
                                                      outputVolumeName="maskedTemplateVolume")
    self.zFrameMaskedVolume.SetName(zFrameTemplateVolume.GetName() + "-label")
    if self.startIndex is None or self.endIndex is None:
      self.startIndex, center, self.endIndex = self.getROIMinCenterMaxSliceNumbers(coverTemplateROI)
      self.otsuOutputVolume = self.applyITKOtsuFilter(self.zFrameMaskedVolume)
      self.dilateMask(self.otsuOutputVolume)
      self.startIndex, self.endIndex = self.getStartEndWithConnectedComponents(self.otsuOutputVolume, center)
    self.openSourceRegistration.setInputVolume(self.zFrameMaskedVolume)
    self.openSourceRegistration.runRegistration(self.startIndex, self.endIndex)
    self.clearVolumeNodes()
    return True

  def getROIMinCenterMaxSliceNumbers(self, coverTemplateROI):
    center = [0.0, 0.0, 0.0]
    coverTemplateROI.GetXYZ(center)
    bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    coverTemplateROI.GetRASBounds(bounds)
    pMin = [bounds[0], bounds[2], bounds[4]]
    pMax = [bounds[1], bounds[3], bounds[5]]
    return [self.getIJKForXYZ(self.redSliceWidget, pMin)[2], self.getIJKForXYZ(self.redSliceWidget, center)[2],
            self.getIJKForXYZ(self.redSliceWidget, pMax)[2]]

  def getStartEndWithConnectedComponents(self, volume, center):
    address = sitkUtils.GetSlicerITKReadWriteAddress(volume.GetName())
    image = sitk.ReadImage(address)
    start = self.getStartSliceUsingConnectedComponents(center, image)
    end = self.getEndSliceUsingConnectedComponents(center, image)
    return start, end

  def getStartSliceUsingConnectedComponents(self, center, image):
    sliceIndex = start = center
    while sliceIndex > 0:
      if self.getIslandCount(image, sliceIndex) > 6:
        start = sliceIndex
        sliceIndex -= 1
        continue
      break
    return start

  def getEndSliceUsingConnectedComponents(self, center, image):
    imageSize = image.GetSize()
    sliceIndex = end = center
    while sliceIndex < imageSize[2]:
      if self.getIslandCount(image, sliceIndex) > 6:
        end = sliceIndex
        sliceIndex += 1
        continue
      break
    return end

  def applyITKOtsuFilter(self, volume):
    inputVolume = sitk.Cast(sitkUtils.PullVolumeFromSlicer(volume.GetID()), sitk.sitkInt16)
    self.otsuFilter.SetInsideValue(0)
    self.otsuFilter.SetOutsideValue(1)
    otsuITKVolume = self.otsuFilter.Execute(inputVolume)
    # return sitkUtils.PushToSlicer(otsuITKVolume, "otsuITKVolume", 0, True)
    return sitkUtils.PushVolumeToSlicer(otsuITKVolume, name="otsuITKVolume") # Mariana fix
    

class ZFrameRegistrationWithROITest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  groundTruthMatrix = [0.9999315859310454, 0.009689047677719153, -0.006549676681617225, 5.971096704891779,
                       -0.009774406649458021, 0.9998660159742193, -0.013128544923338871, -18.918600331582244,
                       0.006421595844729844, 0.013191666276940213, 0.999892377445857, 102.1792443094631,
                       0.0, 0.0, 0.0, 1.0]
  
  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ZFrameRegistrationWithROI1()

  def isclose(self, a, b, rel_tol=1e-05, abs_tol=0.0):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

  def test_ZFrameRegistrationWithROI1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #

    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    imageDataPath = os.path.join(os.path.abspath(os.path.join(currentFilePath, os.pardir)), "ZFrameRegistration",
                                 "Data", "Input", "CoverTemplateMasked.nrrd")
    print(imageDataPath)
    _, imageDataNode = slicer.util.loadVolume(imageDataPath, returnNode=True)
    slicer.app.processEvents()
    self.delayDisplay('Finished with loading')

    zFrameRegistrationLogic = ZFrameRegistrationWithROILogic()
    # ROINode = slicer.vtkMRMLAnnotationROINode()
    ROINode = slicer.vtkMRMLMarkupsROINode() #  Mariana  
    ROINode.SetName("ROINodeForCropping")
    ROICenterPoint = [-6.91920280456543, 15.245062828063965, -101.13504791259766]
    ROINode.SetXYZ(ROICenterPoint)
    ROIRadiusXYZ = [36.46055603027344, 38.763328552246094, 36.076759338378906]
    ROINode.SetRadiusXYZ(ROIRadiusXYZ)
    slicer.mrmlScene.AddNode(ROINode)
    slicer.app.processEvents()

    zFrameRegistrationLogic.runZFrameOpenSourceRegistration('zframe_original_vertical.vtk', imageDataNode, coverTemplateROI=ROINode)
    slicer.app.processEvents()
    transformNode = zFrameRegistrationLogic.openSourceRegistration.outputTransform
    transformMatrix = transformNode.GetTransformFromParent().GetMatrix()
    testResultMatrix = [0.0] * 16
    transformMatrix.DeepCopy(testResultMatrix, transformMatrix)
    for index in range(len(self.groundTruthMatrix)):
      self.assertEqual(self.isclose(float(testResultMatrix[index]), float(self.groundTruthMatrix[index])), True)
    zFrameRegistrationLogic.clearVolumeNodes()

    self.delayDisplay('Test passed!')


class ZFrameRegistrationWithROISlicelet(qt.QWidget):
  def __init__(self):
    qt.QWidget.__init__(self)
    self.setLayout(qt.QVBoxLayout())
    self.mainWidget = qt.QWidget()
    self.mainWidget.objectName = "qSlicerAppMainWindow"
    self.mainWidget.setLayout(qt.QVBoxLayout())

    self.setupLayoutWidget()

    self.moduleFrame = qt.QWidget()
    self.moduleFrameLayout = qt.QVBoxLayout()
    self.moduleFrame.setLayout(self.moduleFrameLayout)

    self.buttons = qt.QFrame()
    self.buttons.setLayout(qt.QHBoxLayout())
    self.moduleFrameLayout.addWidget(self.buttons)
    self.addDataButton = qt.QPushButton("Add Data")
    self.buttons.layout().addWidget(self.addDataButton)
    self.addDataButton.connect("clicked()", slicer.app.ioManager().openAddDataDialog)
    self.loadSceneButton = qt.QPushButton("Load Scene")
    self.buttons.layout().addWidget(self.loadSceneButton)
    self.loadSceneButton.connect("clicked()", slicer.app.ioManager().openLoadSceneDialog)

    self.zFrameRegistrationWidget = ZFrameRegistrationWithROIWidget(self.moduleFrame)
    self.zFrameRegistrationWidget.setup()
    self.zFrameRegistrationWidget.reloadCollapsibleButton.visible = False

    # TODO: resize self.widget.parent to minimum possible width

    self.scrollArea = qt.QScrollArea()
    self.scrollArea.setWidget(self.zFrameRegistrationWidget.parent)
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setMinimumWidth(self.zFrameRegistrationWidget.parent.minimumSizeHint.width())

    self.splitter = qt.QSplitter()
    self.splitter.setOrientation(qt.Qt.Horizontal)
    self.splitter.addWidget(self.scrollArea)
    self.splitter.addWidget(self.layoutWidget)
    self.splitter.splitterMoved.connect(self.onSplitterMoved)

    self.splitter.setStretchFactor(0, 0)
    self.splitter.setStretchFactor(1, 1)
    self.splitter.handle(1).installEventFilter(self)

    self.mainWidget.layout().addWidget(self.splitter)
    self.mainWidget.show()

  def setupLayoutWidget(self):
    self.layoutWidget = qt.QWidget()
    self.layoutWidget.setLayout(qt.QHBoxLayout())
    layoutWidget = slicer.qMRMLLayoutWidget()
    layoutManager = slicer.qSlicerLayoutManager()
    layoutManager.setMRMLScene(slicer.mrmlScene)
    layoutManager.setScriptedDisplayableManagerDirectory(slicer.app.slicerHome + "/bin/Python/mrmlDisplayableManager")
    layoutWidget.setLayoutManager(layoutManager)
    slicer.app.setLayoutManager(layoutManager)
    layoutWidget.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    self.layoutWidget.layout().addWidget(layoutWidget)

  def eventFilter(self, obj, event):
    if event.type() == qt.QEvent.MouseButtonDblClick:
      self.onSplitterClick()

  def onSplitterMoved(self, pos, index):
    vScroll = self.scrollArea.verticalScrollBar()
    vScrollbarWidth = 4 if not vScroll.isVisible() else vScroll.width + 4
    if self.scrollArea.minimumWidth != self.zFrameRegistrationWidget.parent.minimumSizeHint.width() + vScrollbarWidth:
      self.scrollArea.setMinimumWidth(self.zFrameRegistrationWidget.parent.minimumSizeHint.width() + vScrollbarWidth)

  def onSplitterClick(self):
    if self.splitter.sizes()[0] > 0:
      self.splitter.setSizes([0, self.splitter.sizes()[1]])
    else:
      minimumWidth = self.zFrameRegistrationWidget.parent.minimumSizeHint.width()
      self.splitter.setSizes([minimumWidth, self.splitter.sizes()[1] - minimumWidth])


if __name__ == "__main__":
  import sys

  print(sys.argv)

  slicelet = ZFrameRegistrationWithROISlicelet()        
