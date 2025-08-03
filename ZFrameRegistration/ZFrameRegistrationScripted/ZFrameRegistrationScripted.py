import os, sys
moduleDir = os.path.dirname(os.path.realpath(__file__))
if moduleDir not in sys.path:
    sys.path.append(moduleDir)

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
from ZFrame.Registration import zf, ZFrameRegistration

class ZFrameRegistrationScripted(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ZFrameRegistration Scripted"
        self.parent.categories = ["IGT"]
        self.parent.dependencies = []
        self.parent.contributors = ["Junichi Tokuda (SPL), Longquan Chen (SPL), Christian Herz (SPL), Andriy Fedorov (SPL), Rebecca Lisk (SPL), Franklin King (SPL)"]
        self.parent.helpText = """
            This module performs Z-frame registration for image-guided interventions.
            It supports both 7-fiducial and 9-fiducial Z-frame configurations.
            """
        self.parent.acknowledgementText = """
            
            """
        for iconExtension in ['.svg', '.png']:
            iconPath = os.path.join(moduleDir, 'Resources/Icons', self.__class__.__name__ + iconExtension)
            if os.path.isfile(iconPath):
                parent.icon = qt.QIcon(iconPath)
                break

class ZFrameRegistrationScriptedWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
    
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
            self.setup()
            self.parent.show()

    def onReload(self,moduleName="ZFrameRegistrationScripted"):
        self.zFrameTopologies = {}
        if 'ZFrame.Registration' in sys.modules:
            del sys.modules['ZFrame.Registration']
            print("ZFrame.Registration Deleted")

        globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        self.logic = ZFrameRegistrationScriptedLogic()
        self.zFrameTopologies = {}
        
        # Parameters Area
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        
        # Input volume selector
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.showChildNodeTypes = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.setToolTip("Pick the input volume.")
        parametersFormLayout.addRow("Input Volume: ", self.inputSelector)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputVolumeSelected)

        # Fiducial type selector
        self.fiducialTypeSelector = qt.QComboBox()
        self.fiducialTypeSelector.addItems(["7-fiducial", "9-fiducial"])
        parametersFormLayout.addRow("Fiducial Frame Type: ", self.fiducialTypeSelector)
        self.fiducialTypeSelector.setCurrentIndex(0)
        
        # Z-frame configuration selector
        
        self.zframeConfigSelector = qt.QComboBox()
        self.loadZFrameConfigs()
        parametersFormLayout.addRow("Z-Frame Configuration: ", self.zframeConfigSelector)
        self.zframeConfigSelector.setCurrentIndex(3)
        self.zframeConfigSelector.connect("currentTextChanged(QString)", self.onZFrameConfigChanged)

        # Frame Topology Text Edit
        self.frameTopologyTextEdit = qt.QTextEdit()
        self.frameTopologyTextEdit.setReadOnly(False)
        self.frameTopologyTextEdit.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Fixed)
        self.frameTopologyTextEdit.setMaximumHeight(40)
        parametersFormLayout.addRow("Frame Topology: ", self.frameTopologyTextEdit)

        # Initialize topology text for default selection
        self.onZFrameConfigChanged(self.zframeConfigSelector.currentText)

        # Slice range
        self.sliceRangeWidget = slicer.qMRMLRangeWidget()
        self.sliceRangeWidget.decimals = 0
        self.sliceRangeWidget.minimum = 0
        self.sliceRangeWidget.maximum = 20  # Default range, will update when image is loaded
        self.sliceRangeWidget.minimumValue = 6
        self.sliceRangeWidget.maximumValue = 11
        self.sliceRangeWidget.singleStep = 1
        parametersFormLayout.addRow("Slice Range: ", self.sliceRangeWidget)
        self.onInputVolumeSelected(self.inputSelector.currentNode())
        
        # Output transform selector
        self.outputSelector = slicer.qMRMLNodeComboBox()
        self.outputSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
        self.outputSelector.selectNodeUponCreation = True
        self.outputSelector.addEnabled = True
        self.outputSelector.removeEnabled = True
        self.outputSelector.noneEnabled = True
        self.outputSelector.showHidden = False
        self.outputSelector.showChildNodeTypes = False
        self.outputSelector.setMRMLScene(slicer.mrmlScene)
        self.outputSelector.setToolTip("Pick the output transform")
        parametersFormLayout.addRow("Output Transform: ", self.outputSelector)
        
        # Apply Button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the Z-frame registration."
        self.applyButton.enabled = True
        parametersFormLayout.addRow(self.applyButton)
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        
        self.layout.addStretch(1)
        
    def onInputVolumeSelected(self, node):
        if node:
            dims = node.GetImageData().GetDimensions()
            self.sliceRangeWidget.minimum = 0
            self.sliceRangeWidget.maximum = dims[2]-1

    def loadZFrameConfigs(self):
        """Load Z-frame configurations from configs.txt file"""
        configPath = os.path.join(os.path.dirname(__file__), 'Resources', 'configs.txt')

        self.zframeConfigSelector.clear()
        
        try:
            with open(configPath, 'r') as f:
                lines = f.readlines()
            
            self.zFrameTopologies = {}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines and comments
                    continue
                
                # Split the line into config name and topology data
                try:
                    config_name, topology = line.split(':', 1)
                    config_name = config_name.strip()
                    topology = topology.strip()
                    self.zFrameTopologies[config_name] = topology
                except ValueError:
                    logging.warning(f"Skipping invalid line in configs.txt: {line}")
                    continue
            
            # Update the combo box with the config names
            self.zframeConfigSelector.clear()
            if self.zFrameTopologies:
                self.zframeConfigSelector.addItems(sorted(self.zFrameTopologies.keys()))
            else:
                self.zframeConfigSelector.addItems(["Configs not found"])
            
        except Exception as e:
            logging.error(f"Error loading Z-frame configurations: {str(e)}")
            self.zframeConfigSelector.clear()
            self.zframeConfigSelector.addItems(["Configs not found"])

    def onZFrameConfigChanged(self, configName):
        """Update the topology text based on the selected Z-frame configuration"""
        # Update to use the loaded configurations
        self.frameTopologyTextEdit.setText(self.zFrameTopologies.get(configName, "Unknown configuration"))


    def onApplyButton(self):
        try:
            self.logic.run(self.inputSelector.currentNode(),
                     self.outputSelector.currentNode(),
                     self.zframeConfigSelector.currentText,
                     self.fiducialTypeSelector.currentText,
                     self.frameTopologyTextEdit.toPlainText(),
                     int(self.sliceRangeWidget.minimumValue),
                     int(self.sliceRangeWidget.maximumValue))
        except Exception as e:
            slicer.util.errorDisplay("Failed to compute results: "+str(e))
            import traceback
            traceback.print_exc()

class ZFrameRegistrationScriptedLogic(ScriptedLoadableModuleLogic):
    def run(self, inputVolume, outputTransform, zframeConfig, zframeType, frameTopology, startSlice, endSlice):
        """
        Run the Z-frame registration algorithm
        """
        logging.info('Processing started')
        
        if not inputVolume or not outputTransform:
            raise ValueError("Input volume or output transform is missing")
            
        # Get image data
        imageData = inputVolume.GetImageData()
        if not imageData:
            raise ValueError("Input image is invalid")
        # Convert vtkImageData to numpy array
        dim = imageData.GetDimensions()
        imageData = vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars())
        imageData = imageData.reshape(dim[2], dim[1], dim[0]).transpose(2,1,0) # Note: VTK uses opposite order (z,y,x)

        # Get image properties
        origin = inputVolume.GetOrigin()
        spacing = inputVolume.GetSpacing()
        directions = vtk.vtkMatrix4x4()
        inputVolume.GetIJKToRASDirectionMatrix(directions)

        # Create the RAS to LPS transform
        ras2lps = vtk.vtkMatrix4x4()
        ras2lps.Identity()
        ras2lps.SetElement(0,0,-1)
        ras2lps.SetElement(1,1,-1)
        
        # Create the image to world transform as numpy array
        imageTransform = np.eye(4)  # Start with 4x4 identity matrix
        for i in range(3):
            for j in range(3):
                imageTransform[i,j] = spacing[j] * directions.GetElement(i,j)
            imageTransform[i,3] = origin[i]

        ZmatrixBase = np.eye(4)
        ZquaternionBase = [0.0, 0.0, 0.0, 1.0]
        ZquaternionBase = zf.MatrixToQuaternion(ZmatrixBase)

        sliceRange = [startSlice, endSlice]
        Zposition = [0.0, 0.0, 0.0]
        Zorientation = [0.0, 0.0, 0.0, 1.0]
        result = False

        #dim = [dimensions[0], dimensions[1], dimensions[2]]
        #manualRegistration = False 
        
        # Convert frameTopology string back into an array of floats
        # "[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]"
        frameTopologyArr = []
        # Remove whitespace from the string and split
        frameTopologyList = ''.join(frameTopology.split()).strip("[]").split("],[")
        for n in frameTopologyList:
            # Convert each coordinate string into floats
            x, y, z = map(float, n.split(","))
            frameTopologyArr.append([x, y, z])
        # Final result is stored in frameTopologyArr[6][3]
        # The first 3 rows contain the origin points in RAS coordinates of Side 1, Base, and Side 2, respectively. 
        # The 4th, 5th, and 6th rows contain the diagonal vectors in RAS coordinates of Side 1, Base, and Side 2.

        # TODO: Implement manual registration

        # Toggle registration algorithm based on zframe configuration
        if zframeType == "7-fiducial":
            # 7-fiducial registration
            logging.info("Running 7-fiducial registration")
            registration = ZFrameRegistration(numFiducials=7)
        elif zframeType == "9-fiducial":
            # 9-fiducial registration
            logging.info("Running 9-fiducial registration")
            registration = ZFrameRegistration(numFiducials=9)
        else:
            raise ValueError("Invalid Z-frame configuration")
        
        if registration:
            registration.SetInputImage(imageData, imageTransform)
            registration.SetOrientationBase(ZquaternionBase)
            registration.SetFrameTopology(frameTopologyArr)
            result, Zposition, Zorientation = registration.Register(sliceRange)
        else:
            raise ValueError("Invalid Z-frame configuration")
        
        if result:
            matrix = zf.QuaternionToMatrix(Zorientation)

            zMatrix = vtk.vtkMatrix4x4()
            
            # Combine quaternion and position into a single matrix
            zMatrix.SetElement(0,0, matrix[0][0])
            zMatrix.SetElement(1,0, matrix[1][0])
            zMatrix.SetElement(2,0, matrix[2][0])
            zMatrix.SetElement(0,1, matrix[0][1])
            zMatrix.SetElement(1,1, matrix[1][1])
            zMatrix.SetElement(2,1, matrix[2][1])
            zMatrix.SetElement(0,2, matrix[0][2])
            zMatrix.SetElement(1,2, matrix[1][2])
            zMatrix.SetElement(2,2, matrix[2][2])
            zMatrix.SetElement(0,3, Zposition[0])
            zMatrix.SetElement(1,3, Zposition[1])
            zMatrix.SetElement(2,3, Zposition[2])
            
            print(f'RAS Transformation Matrix:\n {zMatrix}')
            outputTransform.SetMatrixTransformToParent(zMatrix)
            logging.info('Processing completed')
            return True
        else:
            logging.error('Processing failed')
            return False

        
        
        
        

# class ZFrameRegistrationScriptedTest(ScriptedLoadableModuleTest):
#     def setUp(self):
#         slicer.mrmlScene.Clear(0)

#     def runTest(self):
#         self.setUp()
#         self.test_ZFrameRegistration1()

#     def test_ZFrameRegistration1(self):
#         self.delayDisplay("Starting the test")
        
#         # Get/create input data
#         import SampleData
#         inputVolume = SampleData.downloadFromURL(
#             nodeNames='MRHead',
#             fileNames='MR-Head.nrrd',
#             uris='https://github.com/Slicer/SlicerTestingData/releases/download/MD5/39b01631b7b38232a220007230624c8e',
#             checksums='MD5:39b01631b7b38232a220007230624c8e')[0]
#         self.delayDisplay('Finished with download and loading')
        
#         outputTransform = slicer.vtkMRMLLinearTransformNode()
#         slicer.mrmlScene.AddNode(outputTransform)
        
#         logic = ZFrameRegistrationScriptedLogic()
#         self.assertTrue(logic.run(inputVolume, outputTransform, "z001", 0, 10))
        
#         self.delayDisplay('Test passed!') 