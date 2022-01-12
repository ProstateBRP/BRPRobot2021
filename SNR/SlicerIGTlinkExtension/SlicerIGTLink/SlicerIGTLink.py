##=========================================================================

#  Program:   BRP Prostate Robot 2021 - Slicer Module
#  Language:  Python

#  Copyright (c) Brigham and Women's Hospital. All rights reserved.

#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.

#  Please see
#    https://github.com/ProstateBRP/BRPRobot2021/wiki
#  for the detail of the protocol.

#=========================================================================


import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import sitkUtils
import numpy as np
import time
import random
import string
import re
import csv
# from SlicerDevelopmentToolboxUtils.mixins import ModuleLogicMixin, ModuleWidgetMixin

class SlicerIGTLink(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Bakse/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Slicer IGTLink"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Rebecca Lisk"]
    self.parent.helpText = """
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""

class SlicerIGTLinkWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Server collapsible button
    serverCollapsibleButton = ctk.ctkCollapsibleButton()
    serverCollapsibleButton.text = "Start IGTLink Server"
    self.layout.addWidget(serverCollapsibleButton)

    # Layout within the path collapsible button
    serverFormLayout = qt.QGridLayout(serverCollapsibleButton)

    self.snrPortTextboxLabel = qt.QLabel('SNR server port:')
    self.snrPortTextbox = qt.QLineEdit("18944")
    self.snrPortTextbox.setReadOnly(False)
    self.snrPortTextbox.setMaximumWidth(250)

    serverFormLayout.addWidget(self.snrPortTextboxLabel, 0, 0)
    serverFormLayout.addWidget(self.snrPortTextbox, 0, 1)

    self.snrHostnameTextboxLabel = qt.QLabel('SNR hostname:')
    self.snrHostnameTextbox = qt.QLineEdit("localhost")
    self.snrHostnameTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setMaximumWidth(250)
    serverFormLayout.addWidget(self.snrHostnameTextboxLabel, 1, 0)
    serverFormLayout.addWidget(self.snrHostnameTextbox, 1, 1)

    # Create server button
    self.createServerButton = qt.QPushButton("Create server")
    self.createServerButton.toolTip = "Create the IGTLink server connection with shell."
    self.createServerButton.enabled = True
    self.createServerButton.setMaximumWidth(250)
    # serverFormLayout.addWidget(self.createServerButton, 2, 0, 1, 2)
    serverFormLayout.addWidget(self.createServerButton, 2, 0)
    self.createServerButton.connect('clicked()', self.onCreateServerButtonClicked)

    self.disconnectFromSocketButton = qt.QPushButton("Disconnect from socket")
    self.disconnectFromSocketButton.toolTip = "Disconnect from the socket when you finish using audio"
    self.disconnectFromSocketButton.enabled = False
    self.disconnectFromSocketButton.setMaximumWidth(250)
    # serverFormLayout.addWidget(self.disconnectFromSocketButton, 2, 2, 1, 2)
    serverFormLayout.addWidget(self.disconnectFromSocketButton, 2, 1)
    self.disconnectFromSocketButton.connect('clicked()', self.onDisconnectFromSocketButtonClicked)

    # Outbound messages collapsible button
    self.outboundCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outboundCollapsibleButton.text = "Outbound Commands"
    self.outboundCollapsibleButton.collapsed = True
    self.layout.addWidget(self.outboundCollapsibleButton)

    # Layout within the path collapsible button
    outboundFormLayout = qt.QGridLayout(self.outboundCollapsibleButton)
    
    nameLabelphase = qt.QLabel('Current phase:')
    self.phaseTextbox = qt.QLineEdit("")
    self.phaseTextbox.setReadOnly(True)
    self.phaseTextbox.setFixedWidth(250)
    self.phaseTextbox.toolTip = "Show current phase: in Blue if in the phase, green if phase successfully achieved"
    outboundFormLayout.addWidget(nameLabelphase, 0, 0)
    outboundFormLayout.addWidget(self.phaseTextbox, 0, 1)

    # startupButton Button
    self.startupButton = qt.QPushButton("START UP")
    self.startupButton.toolTip = "Send the startup command to the WPI robot."
    self.startupButton.enabled = True
    self.startupButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.startupButton, 2, 0)
    self.startupButton.connect('clicked()', self.onStartupButtonClicked)

    # planningButton Button # TODO Check protocol: should it print sucess after CURRENT_STATUS is sent?
    self.planningButton = qt.QPushButton("PLANNING")
    self.planningButton.toolTip = "Send the planning command to the WPI robot."
    self.planningButton.enabled = False
    self.planningButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.planningButton, 3, 0)
    self.planningButton.connect('clicked()', self.onPlanningButtonClicked)

    # calibrationButton Button
    self.calibrationButton = qt.QPushButton("CALIBRATION")
    self.calibrationButton.toolTip = "Send the calibration command to the WPI robot."
    self.calibrationButton.enabled = False
    self.calibrationButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.calibrationButton, 3, 1)
    self.calibrationButton.connect('clicked()', self.onCalibrationButtonClicked)

    # targetingButton Button
    self.targetingButton = qt.QPushButton("TARGETING")
    self.targetingButton.toolTip = "Send the targeting command to the WPI robot."
    self.targetingButton.enabled = False
    self.targetingButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.targetingButton, 4 , 0)
    self.targetingButton.connect('clicked()', self.onTargetingButtonClicked)

    # moveButton Button
    self.moveButton = qt.QPushButton("MOVE")
    self.moveButton.toolTip = "Send the move to target command to the WPI robot."
    self.moveButton.enabled = False
    self.moveButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.moveButton, 4, 1)
    self.moveButton.connect('clicked()', self.onMoveButtonClicked)

    # Lock Button to ask WPI to lock robot
    self.LockButton = qt.QPushButton("LOCK")
    self.LockButton.toolTip = "Send the command to ask the operator to lock the WPI robot."
    self.LockButton.enabled = False
    self.LockButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.LockButton, 5, 0)
    self.LockButton.connect('clicked()', self.onLockButtonClicked)

    # Unlock Button to ask WPI to unlock robot
    self.UnlockButton = qt.QPushButton("UNLOCK")
    self.UnlockButton.toolTip = "Send the command to ask the operator to unlock the WPI robot."
    self.UnlockButton.enabled = False
    self.UnlockButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.UnlockButton, 5, 1)
    self.UnlockButton.connect('clicked()', self.onUnlockButtonClicked)

    # Get robot pose Button to ask WPI to send the current robot position
    self.GetPoseButton = qt.QPushButton("GET POSE")
    self.GetPoseButton.toolTip = "Send the command to ask WPI to send the current robot position."
    self.GetPoseButton.enabled = False
    self.GetPoseButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.GetPoseButton, 6, 0)
    self.GetPoseButton.connect('clicked()', self.onGetPoseButtonClicked)

    # Get robot status Button to ask WPI to send the current status position
    self.GetStatusButton = qt.QPushButton("GET STATUS")
    self.GetStatusButton.toolTip = "Send the command to ask WPI to send the current robot status."
    self.GetStatusButton.enabled = False
    self.GetStatusButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.GetStatusButton, 6, 1)
    self.GetStatusButton.connect('clicked()', self.onGetStatusButtonClicked)

    # STOP Button 
    self.StopButton = qt.QPushButton("STOP")
    self.StopButton.toolTip = "Send the command to ask the operator to stop the WPI robot."
    self.StopButton.enabled = False
    self.StopButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.StopButton, 7, 0)
    self.StopButton.connect('clicked()', self.onStopButtonClicked)

    # EMERGENCY Button 
    self.EmergencyButton = qt.QPushButton("EMERGENCY")
    self.EmergencyButton.toolTip = "Send emergency command to WPI robot."
    self.EmergencyButton.enabled = False
    self.EmergencyButton.setMaximumWidth(250)
    outboundFormLayout.addWidget(self.EmergencyButton, 7, 1)
    self.EmergencyButton.connect('clicked()', self.onEmergencyButtonClicked)

    # Outbound tranform collapsible button
    self.outboundTransformCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outboundTransformCollapsibleButton.text = "Calibration Matrix"
    self.outboundTransformCollapsibleButton.collapsed = True
    self.layout.addWidget(self.outboundTransformCollapsibleButton)

    # Layout within the path collapsible button
    outboundTransformsFormLayout = qt.QFormLayout(self.outboundTransformCollapsibleButton)

    # Input volume selector for zFrame calibration
    self.zFrameVolumeSelector = slicer.qMRMLNodeComboBox()
    self.zFrameVolumeSelector.objectName = 'zFrameVolumeSelector'
    self.zFrameVolumeSelector.toolTip = "Select the ZFrame image."
    self.zFrameVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    self.zFrameVolumeSelector.hideChildNodeTypes = ['vtkMRMLAnnotationNode']  # hide all annotation nodes
    self.zFrameVolumeSelector.noneEnabled = False
    self.zFrameVolumeSelector.addEnabled = False
    self.zFrameVolumeSelector.removeEnabled = False
    self.zFrameVolumeSelector.setFixedWidth(250)
    outboundTransformsFormLayout.addRow('ZFrame image:', self.zFrameVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.zFrameVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Start and end slices for calibration step
    self.startSliceSliderWidget = qt.QSpinBox()
    self.endSliceSliderWidget = qt.QSpinBox()
    self.startSliceSliderWidget.setValue(5)
    self.endSliceSliderWidget.setValue(16)
    self.startSliceSliderWidget.setMaximumWidth(40)
    self.endSliceSliderWidget.setMaximumWidth(40)
    outboundTransformsFormLayout.addRow('Minimum slice:', self.startSliceSliderWidget)
    outboundTransformsFormLayout.addRow('Maximum slice:', self.endSliceSliderWidget)

    # Calibration matrix display
    row = 4
    column = 4
    self.calibrationTableWidget = qt.QTableWidget(row, column)
    self.calibrationTableWidget.verticalHeader().hide() # Remove line numbers
    self.calibrationTableWidget.horizontalHeader().hide() # Remove column numbers
    self.calibrationTableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.calibrationTableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)

    verticalheader = self.calibrationTableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    outboundTransformsFormLayout.addRow("Calibration matrix:  ", self.calibrationTableWidget)

    # Add ROI button
    self.addROIButton = qt.QPushButton("Add ROI")
    self.addROIButton.enabled = True
    outboundTransformsFormLayout.addWidget(self.addROIButton)
    self.addROIButton.connect('clicked()', self.onAddROI)

    # Create and send new calibration matrix button
    self.createCalibrationMatrixButton = qt.QPushButton("Create and send new calibration matrix")
    self.createCalibrationMatrixButton.enabled = True
    # self.createCalibrationMatrixButton.setMaximumWidth(250)
    outboundTransformsFormLayout.addWidget(self.createCalibrationMatrixButton)
    self.createCalibrationMatrixButton.connect('clicked()', self.initiateZFrameCalibration)

    # TO SELECT AN EXISTING CALIBRATION MATRIX CALUCLATED BY HARMONUS (outside of the module):
    # Delete once Calibration step is testing and working
    self.calibrationMatrixSelector = slicer.qMRMLNodeComboBox()
    self.calibrationMatrixSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.calibrationMatrixSelector.selectNodeUponCreation = True
    self.calibrationMatrixSelector.addEnabled = False
    self.calibrationMatrixSelector.removeEnabled = False
    self.calibrationMatrixSelector.noneEnabled = False
    self.calibrationMatrixSelector.showHidden = False
    self.calibrationMatrixSelector.showChildNodeTypes = False
    self.calibrationMatrixSelector.setMRMLScene( slicer.mrmlScene )
    self.calibrationMatrixSelector.setToolTip( "Select the calibration matrix." )
    outboundTransformsFormLayout.addRow("Calibration matrix:  ", self.calibrationMatrixSelector)

    # Send pre-calculated calibration matrix button
    self.sendCalibrationMatrixButton = qt.QPushButton("Send pre-existing calibration matrix")
    self.sendCalibrationMatrixButton.enabled = True
    # self.createCalibrationMatrixButton.setMaximumWidth(250)
    outboundTransformsFormLayout.addWidget(self.sendCalibrationMatrixButton)
    self.sendCalibrationMatrixButton.connect('clicked()', self.onSendCalibrationMatrixButtonClicked)

    # Outbound target fiducial collapsible button
    self.outboundTargetCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outboundTargetCollapsibleButton.text = "Target Point"
    self.outboundTargetCollapsibleButton.collapsed = True
    self.layout.addWidget(self.outboundTargetCollapsibleButton)

    # Layout within the path collapsible button
    outboundTargetFormLayout = qt.QGridLayout(self.outboundTargetCollapsibleButton)
   
    # Fiducial selector for target point
    self.targetPointNodeSelector = slicer.qSlicerSimpleMarkupsWidget()
    self.targetPointNodeSelector.objectName = 'targetPointNodeSelector'
    self.targetPointNodeSelector.toolTip = "Select a fiducial to use as the needle insertion target point."
    self.targetPointNodeSelector.setNodeBaseName("TARGET_POINT")
    self.targetPointNodeSelector.defaultNodeColor = qt.QColor(170,0,0)
    self.targetPointNodeSelector.tableWidget().hide()
    self.targetPointNodeSelector.markupsSelectorComboBox().noneEnabled = False
    self.targetPointNodeSelector.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup
    targetPointSelectorLabel = qt.QLabel("Target point: ")
    outboundTargetFormLayout.addWidget(targetPointSelectorLabel, 0, 0)
    outboundTargetFormLayout.addWidget(self.targetPointNodeSelector, 0, 1, 1, 3)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.targetPointNodeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Display for RAS coordinates of the selected fidudcial target point
    targetPointLabel = qt.QLabel("RAS coordinates:     ")
    self.targetPointTextbox_R = qt.QLineEdit()
    self.targetPointTextbox_A = qt.QLineEdit()
    self.targetPointTextbox_S = qt.QLineEdit()
    self.targetPointTextbox_R.setReadOnly(True)
    self.targetPointTextbox_A.setReadOnly(True)
    self.targetPointTextbox_S.setReadOnly(True)
    outboundTargetFormLayout.addWidget(targetPointLabel, 1, 0)
    outboundTargetFormLayout.addWidget(self.targetPointTextbox_R, 1, 1)
    outboundTargetFormLayout.addWidget(self.targetPointTextbox_A, 1, 2)
    outboundTargetFormLayout.addWidget(self.targetPointTextbox_S, 1, 3)

    # Button to send fiducial target point
    self.sendTargetPointButton = qt.QPushButton("Send selected target point")
    self.sendTargetPointButton.enabled = True
    # self.sendTargetPointButton.setMaximumWidth(250)
    outboundTargetFormLayout.addWidget(self.sendTargetPointButton, 2, 1, 1, 3)
    self.sendTargetPointButton.connect('clicked()', self.onSendTargetPointButtonClicked)

    # Inbound messages collapsible button
    self.inboundCollapsibleButton = ctk.ctkCollapsibleButton()
    self.inboundCollapsibleButton.text = "Inbound Messages"
    self.inboundCollapsibleButton.collapsed = True
    self.layout.addWidget(self.inboundCollapsibleButton)

    # Layout within the path collapsible button
    inboundFormLayout = qt.QFormLayout(self.inboundCollapsibleButton)

    self.messageTextbox = qt.QLineEdit("No message received")
    self.messageTextbox.setReadOnly(True)
    self.messageTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Message received:", self.messageTextbox)

    self.statusTextbox = qt.QLineEdit("No status received")
    self.statusTextbox.setReadOnly(True)
    self.statusTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Status received:", self.statusTextbox)

    self.statusCodeTextbox = qt.QLineEdit("No status code received")
    self.statusCodeTextbox.setReadOnly(True)
    self.statusCodeTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Status meaning:", self.statusCodeTextbox)

    row = 4
    column = 4
    self.tableWidget = qt.QTableWidget(row, column)
    self.tableWidget.verticalHeader().hide() # Remove line numbers
    self.tableWidget.horizontalHeader().hide() # Remove column numbers
    self.tableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.tableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)

    verticalheader = self.tableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    inboundFormLayout.addRow("Transform received:", self.tableWidget)

    # Visibility icon
    self.VisibleButton = qt.QPushButton()
    eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png");
    self.VisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
    self.VisibleButton.setFixedWidth(25)
    self.VisibleButton.setCheckable(True)
    inboundFormLayout.addRow("", self.VisibleButton)
    self.VisibleButton.connect('clicked()', self.onVisibleButtonClicked)
        
    # Info messages collapsible button
    self.infoCollapsibleButton = ctk.ctkCollapsibleButton()
    self.infoCollapsibleButton.text = "Info Messages"
    self.infoCollapsibleButton.collapsed = True
    self.layout.addWidget(self.infoCollapsibleButton)

    # Layout within the path collapsible button
    infoFormLayout = qt.QFormLayout(self.infoCollapsibleButton)

    self.infoTextbox = qt.QLineEdit("")
    self.infoTextbox.setReadOnly(True)
    #self.infoTextbox.setFixedWidth(500)
    infoFormLayout.addRow("", self.infoTextbox)

    # Add vertical spacer
    self.layout.addStretch(1)

    self.textNode = slicer.vtkMRMLTextNode()
    self.textNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(self.textNode)
    self.firstServer = True # Set to false the first time CreateServerButton is clicked so that nodes are not re-created

    # Empty nodes for calibration step
    self.zFrameROI = None
    self.zFrameROIAddedObserverTag = None
    self.outputTransform = None
    self.redSliceWidget = slicer.app.layoutManager().sliceWidget("Red")
    self.redSliceView = self.redSliceWidget.sliceView()
    self.redSliceLogic = self.redSliceWidget.sliceLogic()
    self.otsuFilter = sitk.OtsuThresholdImageFilter()
    # self.openSourceRegistration = OpenSourceZFrameRegistration(slicer.mrmlScene)
    self.templateVolume = None
    self.zFrameCroppedVolume = None
    self.zFrameLabelVolume = None
    self.zFrameMaskedVolume = None
    self.otsuOutputVolume = None
    self.startIndex = None
    self.endIndex = None
    self.zFrameModelNode = None

  def onCreateServerButtonClicked(self):
    # GUI changes to enable/disable button functionality
    self.createServerButton.enabled = False
    self.disconnectFromSocketButton.enabled = True
    self.snrPortTextbox.setReadOnly(True)
    self.snrHostnameTextbox.setReadOnly(True)
    self.outboundCollapsibleButton.collapsed = False
    self.inboundCollapsibleButton.collapsed = False
    self.infoCollapsibleButton.collapsed = False

    snrPort = self.snrPortTextbox.text
    snrHostname = self.snrHostnameTextbox.text
    print("Slicer-side port number: ", snrPort)
    #VisualFeedback: color in gray when server is created
    self.snrPortTextboxLabel.setStyleSheet('color: rgb(195,195,195)')
    self.snrHostnameTextboxLabel.setStyleSheet('color: rgb(195,195,195)')
    self.snrPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: rgb(195,195,195) }""")
    self.snrHostnameTextbox.setStyleSheet("""QLineEdit { background-color: white; color: rgb(195,195,195) }""")

    # Initialize the IGTLink Slicer-side server component
    self.openIGTNode = slicer.vtkMRMLIGTLConnectorNode()
    slicer.mrmlScene.AddNode(self.openIGTNode)
    self.openIGTNode.SetTypeServer(int(snrPort))
    self.openIGTNode.Start()
    print("openIGTNode: ", self.openIGTNode)
    self.IGTActive = True

    # Make a node for each message type IF the nodes are not already created
    if self.firstServer:
      self.firstServer = False
      # Create nodes to receive string, status, and transform messages
      ReceivedStringMsg = slicer.vtkMRMLTextNode()
      ReceivedStringMsg.SetName("StringMessage")
      slicer.mrmlScene.AddNode(ReceivedStringMsg)

      ReceivedStatusMsg = slicer.vtkMRMLIGTLStatusNode()
      ReceivedStatusMsg.SetName("StatusMessage")
      slicer.mrmlScene.AddNode(ReceivedStatusMsg)

      ReceivedTransformMsg = slicer.vtkMRMLLinearTransformNode()
      ReceivedTransformMsg.SetName("TransformMessage")
      slicer.mrmlScene.AddNode(ReceivedTransformMsg)

      ReceivedTransformInfo = slicer.vtkMRMLTextNode()
      ReceivedTransformInfo.SetName("TransformInfo")
      slicer.mrmlScene.AddNode(ReceivedTransformInfo)

      # Add observers on the 4 message type nodes
      ReceivedStringMsg.AddObserver(slicer.vtkMRMLTextNode.TextModifiedEvent, self.onTextNodeModified)
      ReceivedStatusMsg.AddObserver(slicer.vtkMRMLIGTLStatusNode.StatusModifiedEvent, self.onStatusNodeModified)
      ReceivedTransformMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTransformNodeModified)
      ReceivedTransformInfo.AddObserver(slicer.vtkMRMLTextNode.TextModifiedEvent, self.onTransformInfoNodeModified)

      # Create a node for sending transforms
      SendTransformNode = slicer.vtkMRMLLinearTransformNode()
      SendTransformNode.SetName("SendTransform")
      slicer.mrmlScene.AddNode(SendTransformNode)

    # Initialize global variables 
    global last_string_sent 
    last_string_sent = "nostring"
    global start
    start = 0
    global ack
    ack = 0
    global last_prefix_sent
    last_prefix_sent = ""
    global last_name_sent
    last_name_sent = ""
    global To_compare
    To_compare = 0
    global last_randomIDname_transform
    last_randomIDname_transform = "SendTransform"

  def onDisconnectFromSocketButtonClicked(self):
    # GUI changes to enable/disable button functionality
    self.disconnectFromSocketButton.enabled = False
    self.createServerButton.enabled = True
    self.snrPortTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setReadOnly(False)
    self.outboundCollapsibleButton.collapsed = True
    self.inboundCollapsibleButton.collapsed = True
    self.infoCollapsibleButton.collapsed = True
    self.outboundTransformCollapsibleButton.collapsed = True
    self.outboundTargetCollapsibleButton.collapsed = True

    # Close socket
    self.openIGTNode.Stop()
    #VisualFeedback: color in black when socket is disconnected
    self.snrPortTextboxLabel.setStyleSheet('color: black')
    self.snrHostnameTextboxLabel.setStyleSheet('color: black')
    self.snrPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")
    self.snrHostnameTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")

  def generateRandomNameID(self,last_prefix_sent):
    # Randomly choose 4 letter from all the ascii_letters
    randomID = [last_prefix_sent,"_"]
    for i in range(4):
      randomLetter = random.choice(string.ascii_letters)
      randomID.append(str(ord(randomLetter)))
    randomIDname = ''.join(randomID)
    return randomIDname

  def activateButtons(self):
    self.planningButton.enabled = True
    self.EmergencyButton.enabled = True
    self.StopButton.enabled = True
    self.GetStatusButton.enabled = True
    self.GetPoseButton.enabled = True
    self.UnlockButton.enabled = True
    self.LockButton.enabled = True
    self.moveButton.enabled = True
    self.targetingButton.enabled = True
    self.calibrationButton.enabled = True
    #self.transformButton.enabled = True

  def deactivateButtons(self):
    self.planningButton.enabled = False
    self.EmergencyButton.enabled = False
    self.StopButton.enabled = False
    self.GetStatusButton.enabled = False
    self.GetPoseButton.enabled = False
    self.UnlockButton.enabled = False
    self.LockButton.enabled = False
    self.moveButton.enabled = False
    self.targetingButton.enabled = False
    self.calibrationButton.enabled = False
    #self.transformButton.enabled = False
   
  def onGetStatusButtonClicked(self):
    # Send stringMessage containing the command "GET STATUS" to the script via IGTLink
    print("Send command to get current status of the robot")
    getstatusNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    getstatusNode.SetName(randomIDname)
    getstatusNode.SetText("GET_STATUS")
    getstatusNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(getstatusNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getstatusNode)
    self.openIGTNode.PushNode(getstatusNode)
    infoMsg =  "Sending STRING( " + randomIDname + ",  GET_STATUS )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onGetPoseButtonClicked(self):
    # Send stringMessage containing the command "GET POSE" to the script via IGTLink
    print("Send command to get current position of the robot")
    getposeNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    getposeNode.SetName(randomIDname)
    getposeNode.SetText("GET_POSE")
    getposeNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(getposeNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getposeNode)
    self.openIGTNode.PushNode(getposeNode)
    infoMsg =  "Sending STRING( " + randomIDname + ",  GET_POSE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onTargetingButtonClicked(self):
    # Send stringMessage containing the command "TARGETING" to the script via IGTLink
    print("Send command to enter targeting mode")
    targetingNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    targetingNode.SetName(randomIDname)
    targetingNode.SetText("TARGETING")
    targetingNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(targetingNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(targetingNode)
    self.openIGTNode.PushNode(targetingNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = targetingNode.GetText()
    last_prefix_sent = "TGT"
    infoMsg =  "Sending STRING( " + randomIDname + ",  TARGETING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

    # Show Target point GUI in the module
    self.outboundTargetCollapsibleButton.collapsed = False

  def onMoveButtonClicked(self):
    # Send stringMessage containing the command "MOVE" to the script via IGTLink
    print("Send command to ask robot to move to target")
    moveNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    moveNode.SetName(randomIDname)
    moveNode.SetText("MOVE_TO_TARGET")
    moveNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(moveNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(moveNode)
    self.openIGTNode.PushNode(moveNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = moveNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  MOVE_TO_TARGET )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)
  
  def onCalibrationButtonClicked(self):
    # Send stringMessage containing the command "CALIBRATION" to the script via IGTLink
    print("Sending calibration command to WPI robot")
    calibrationNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    calibrationNode.SetName(randomIDname)
    calibrationNode.SetText("CALIBRATION")
    calibrationNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(calibrationNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(calibrationNode)
    self.openIGTNode.PushNode(calibrationNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = calibrationNode.GetText()
    last_prefix_sent = "CLB"
    infoMsg =  "Sending STRING( " + randomIDname + ",  CALIBRATION )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg) 

    # Show Calibration matrix GUI in the module
    self.outboundTransformCollapsibleButton.collapsed = False

  def onPlanningButtonClicked(self):
    # Send stringMessage containing the command "PLANNING" to the script via IGTLink
    print("Sending planning command to WPI robot")
    planningNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    planningNode.SetName(randomIDname)
    planningNode.SetText("PLANNING")
    planningNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(planningNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(planningNode)
    self.openIGTNode.PushNode(planningNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = planningNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  PLANNING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg) 

  def onUnlockButtonClicked(self):
    print("Asking to Unlock the robot")
    # Send stringMessage containing the command "UNLOCK" to the script via IGTLink
    unlockNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    unlockNode.SetName(randomIDname)
    unlockNode.SetText("UNLOCK")
    unlockNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(unlockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(unlockNode)
    self.openIGTNode.PushNode(unlockNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = unlockNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  UNLOCK )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onLockButtonClicked(self):
    print("Asking to Lock the robot")
    # Send stringMessage containing the command "LOCK" to the script via IGTLink
    lockNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    lockNode.SetName(randomIDname)
    lockNode.SetText("LOCK")
    lockNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(lockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(lockNode)
    self.openIGTNode.PushNode(lockNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = lockNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  LOCK )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onStopButtonClicked(self):
    print("Sending STOP command")
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    stopNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    stopNode.SetName(randomIDname)
    stopNode.SetText("STOP")
    stopNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(stopNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(stopNode)
    self.openIGTNode.PushNode(stopNode);
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = stopNode.GetText()
    self.deactivateButtons()
    infoMsg =  "Sending STRING( " + randomIDname + ",  STOP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onEmergencyButtonClicked(self):
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    print("Sending Emergency command")
    emergencyNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    emergencyNode.SetName(randomIDname)
    emergencyNode.SetText("EMERGENCY")
    emergencyNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(emergencyNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(emergencyNode)
    self.openIGTNode.PushNode(emergencyNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = emergencyNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  EMERGENCY )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)

  def onStartupButtonClicked(self):
    # Send stringMessage containing the command "START_UP" to the script via IGTLink
    print("Sending Start up command")
    startupNode = slicer.vtkMRMLTextNode()
    global last_prefix_sent
    last_prefix_sent = "CMD"
    randomIDname = self.generateRandomNameID(last_prefix_sent)
    global last_name_sent
    last_name_sent = randomIDname
    startupNode.SetName(randomIDname)
    startupNode.SetText("START_UP")
    startupNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(startupNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(startupNode)
    self.openIGTNode.PushNode(startupNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = startupNode.GetText()
    infoMsg =  "Sending STRING( " + randomIDname + ",  START_UP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.infoTextbox.setText(infoMsg)
    
  # def onStatusButtonClicked(self):
  #   # Send Status message
  #   print("Sending Status")
  #   statusNode = slicer.vtkMRMLIGTLStatusNode()
  #   statusNode.SetStatusString("STATUS_OK")
  #   slicer.mrmlScene.AddNode(statusNode)
  #   self.openIGTNode.RegisterOutgoingMRMLNode(statusNode)
  #   self.openIGTNode.PushNode(statusNode)

  # def onTransformButtonClicked(self):
  #   # Send Transform message
  #   print("Sending Transform")
  #   transformMatrix = vtk.vtkMatrix4x4()
  #   SendTransformNode = slicer.mrmlScene.GetFirstNodeByName("SendTransform")
  #   SendTransformNode.GetMatrixTransformToParent(transformMatrix)
  #   randomIDname = self.generateRandomNameID(last_prefix_sent)
  #   global last_randomIDname_transform
  #   last_randomIDname_transform = randomIDname
  #   global last_name_sent
  #   last_name_sent = randomIDname
  #   SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
  #   SendTransformNodeTemp.SetName(randomIDname)
  #   SendTransformNodeTemp.GetMatrixTransformToParent(transformMatrix)
  #   slicer.mrmlScene.AddNode(SendTransformNodeTemp)
  #   print(transformMatrix)
  #   self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
  #   self.openIGTNode.PushNode(SendTransformNodeTemp)
  #   infoMsg =  "Sending TRANSFORM( " + randomIDname + " )"
  #   re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
  #   self.infoTextbox.setText(infoMsg)
  #   attr = SendTransformNodeTemp.GetAttribute("IGTLVisible");
  #   print("attribute is:", attr) 
    
  def onVisibleButtonClicked(self):
    # If button is checked
    if (self.VisibleButton.isChecked()):
      eyeIconVisible = qt.QPixmap(":/Icons/Small/SlicerVisible.png")
      self.VisibleButton.setIcon(qt.QIcon(eyeIconVisible))
      self.AddPointerModel()
      TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
      locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("PointerNode")
      locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID());
    # If it is unchecked
    else:
      eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png")
      self.VisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PointerNode")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)

  def onTextNodeModified(textNode, unusedArg2=None, unusedArg3=None):
    print("New string was received")
    ReceivedStringMsg = slicer.mrmlScene.GetFirstNodeByName("StringMessage")
    end = time.time()
    elapsed_time = (end - start)*100
    concatenateMsg = ReceivedStringMsg.GetText()
    delimit = ":"
    isVis = ReceivedStringMsg.GetAttribute("IGTLVisible")
    print("isVis =", isVis)
    if(concatenateMsg.find(delimit)!=-1): # found Delimiter is in the string
      nameonly = concatenateMsg[0: concatenateMsg.index(delimit)]
      msgonly = concatenateMsg[concatenateMsg.index(delimit) + 2: len(concatenateMsg)]
      textNode.messageTextbox.setText(msgonly)
      delimit2 = "_"
      if(nameonly.find(delimit2)!=-1):
        nameonlyType = nameonly[0: nameonly.index(delimit2)]
        nameonlyID = nameonly[nameonly.index(delimit2) + 1: len(nameonly)]
        print(nameonlyType)
        print(nameonlyID)
        global last_name_sent
        if(last_name_sent.find(delimit2)!=-1):
          last_name_sentType = last_name_sent[0: last_name_sent.index(delimit2)]
          last_name_sentID = last_name_sent[last_name_sent.index(delimit2) + 1: len(last_name_sent)]
          print(last_name_sentType)
          print(last_name_sentID)
          if((last_name_sentID == nameonlyID) and (nameonlyType == 'ACK') and(last_string_sent == msgonly)):  # if(elapsed_time > 100) print("Received knowledgment too late, after", elapsed_time, "ms")
            print("Acknowledgment received for command:", last_string_sent, "after", elapsed_time, "ms")
            global ack
            ack = 1
            infoMsg =  "Received STRING from WPI: ( " + nameonly + ", " + msgonly + " )"
            re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
            textNode.infoTextbox.setText(infoMsg)
    else:
      textNode.messageTextbox.setText(concatenateMsg)
      print("Received something different than expected, received: ", ReceivedStringMsg.GetText())      
      
  def onStatusNodeModified(statusNode, unusedArg2=None, unusedArg3=None):
    print("New Status was received")
    ReceivedStatusMsg = slicer.mrmlScene.GetFirstNodeByName("StatusMessage")
    s1 = str(ReceivedStatusMsg.GetCode())
    sep = ':'
    s2 = str(ReceivedStatusMsg.GetSubCode())
    s3 = ReceivedStatusMsg.GetErrorName()
    concatenateMsg = ReceivedStatusMsg.GetStatusString()
    delimit = ":"
    if(concatenateMsg.find(delimit)!=-1): # found delimiter is in the string
      nameonly = concatenateMsg[0: concatenateMsg.index(delimit)]
      msgonly = concatenateMsg[concatenateMsg.index(delimit) + 2: len(concatenateMsg)]
    else:
      msgonly = concatenateMsg
      nameonly = concatenateMsg
    s = s1 + sep + s2 + sep + s3 + sep + msgonly
    statusNode.statusTextbox.setText(s)
    global status_codes
    # Status codes -- see igtl_status.h
    status_codes = ['STATUS_INVALID', 'STATUS_OK', 'STATUS_UNKNOWN_ERROR', 'STATUS_PANICK_MODE', 'STATUS_NOT_FOUND', 'STATUS_ACCESS_DENIED', 'STATUS_BUSY', 'STATUS_TIME_OUT', 'STATUS_OVERFLOW','STATUS_CHECKSUM_ERROR','STATUS_CONFIG_ERROR','STATUS_RESOURCE_ERROR','STATUS_UNKNOWN_INSTRUCTION','STATUS_NOT_READY','STATUS_MANUAL_MODE','STATUS_DISABLED','STATUS_NOT_PRESENT','STATUS_UNKNOWN_VERSION','STATUS_HARDWARE_FAILURE','STATUS_SHUT_DOWN','STATUS_NUM_TYPES']
    statusNode.statusCodeTextbox.setText(status_codes[ReceivedStatusMsg.GetCode()])
    end = time.time()
    elapsed_time = end - start
    global ack
    global loading_phase
    infoMsg =  "Received STATUS from WPI: ( " + nameonly + ", " + status_codes[ReceivedStatusMsg.GetCode()] + " )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    statusNode.infoTextbox.setText(infoMsg)
    if((status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (ack == 1) and (nameonly == 'CURRENT_STATUS')): #and (elapsed_time *100< 100)
      print("Robot is in phase: ", s3, "after", elapsed_time*100, "ms")
      statusNode.phaseTextbox.setText(s3)
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 0, 255);") # Sets phase name in blue 
      loading_phase = s3
    elif((status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (ack ==1) and (loading_phase == nameonly)): #and (elapsed_time<= 10)
      print("Robot sucessfully achieved : ", loading_phase, "after", elapsed_time, "s")
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);")
      if(loading_phase == "START_UP"):
        statusNode.activateButtons()
      ack = 0
      # Initiate calibration matrix calculation when robot reaches CALIBRATION phase
      # if(loading_phase == "CALIBRATION"):
      #   print ("Robot is awaiting calibration matrix.")
      #   self.initiateZFrameCalibration()
    else:
      print("Error in changing phase")

  def onTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)

    print(transformMatrix)
    refMatrix = vtk.vtkMatrix4x4()
    LastTransformNode = slicer.mrmlScene.GetFirstNodeByName(last_randomIDname_transform)
    LastTransformNode.GetMatrixTransformToParent(refMatrix)
    print(refMatrix)
    nbRows = transformNode.tableWidget.rowCount
    nbColumns = transformNode.tableWidget.columnCount
    same_transforms = 1
    global To_compare
    for i in range(nbRows):
      for j in range(nbColumns):
        val = transformMatrix.GetElement(i,j)
        val = round(val,2)
        ref = refMatrix.GetElement(i,j)
        ref = round(val,2)
        if(To_compare == 1):
          if(val != ref):
            same_transforms = 0
        transformNode.tableWidget.setItem(i , j, qt.QTableWidgetItem(str(val)))
    if ((To_compare == 1) and (same_transforms == 0)):
      print("Received a transform different from transform sent") # TODO Do different cases in case Slicer sent a transform or not
      infoMsg =  "TRANSFORM received from WPI doesn't match transform sent"
      transformNode.infoTextbox.setText(infoMsg)
    elif((To_compare == 1) and (same_transforms == 1)):
      print("TRANSFORM received from WPI is the same than transform sent") # TODO Do different cases in case Slicer sent a transform or not
      infoMsg =  "TRANSFORM received from WPI is the same than transform sent"
      transformNode.infoTextbox.setText(infoMsg)

  def onTransformInfoNodeModified(InfoNode, unusedArg2=None, unusedArg3=None):
    print("New transform info was received")
    ReceivedTransformInfo = slicer.mrmlScene.GetFirstNodeByName("TransformInfo")
    info = ReceivedTransformInfo.GetText()
    delimit = "_"
    if((info == "CURRENT_POSITION") or (info == "TARGET")):
      print("Transform received")
    elif(info.find(delimit)!=-1): # Check for delimiter
      infoType = info[0: info.index(delimit)]
      infoID = info[info.index(delimit) + 1: len(info)]
      print(infoType)
      print(infoID)
      global last_name_sent
      if(last_name_sent.find(delimit)!=-1):
       #last_name_sentType = last_name_sent[0: last_name_sent.index(delimit)]
        last_name_sentID = last_name_sent[last_name_sent.index(delimit) + 1: len(last_name_sent)]
        print(last_name_sentID)
        infoMsg =  "Received TRANSFORM from WPI: ( " + info + " )"
        re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
        InfoNode.infoTextbox.setText(infoMsg)
        print(infoMsg)
      
        if((last_name_sentID == infoID) and (infoType == 'ACK')):
          print("Acknowledgment received for transform:", last_name_sent)
          global To_compare
        To_compare = 1
    #ReceivedTransformInfo.SetText("None")
      # else:
      #print("Received something different than expected, received: ", info)

  def AddPointerModel(self):   

    self.cyl = vtk.vtkCylinderSource()
    self.cyl.SetRadius(1.5)
    self.cyl.SetResolution(50)
    self.cyl.SetHeight(100)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(self.cyl.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetOrientation(0,0,90)
    actor.SetMapper(mapper)

    node = self.cyl.GetOutput()
    locatorModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "PointerNode")
    locatorModelNode.SetAndObservePolyData(node)
    locatorModelNode.CreateDefaultDisplayNodes()
    locatorModelNode.SetDisplayVisibility(True)
    self.cyl.Update()

    #Rotate cylinder
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transform = vtk.vtkTransform()
    transform.RotateX(90.0);
    transform.Translate(0.0, -50.0, 0.0);
    transform.Update();
    transformFilter.SetInputConnection(self.cyl.GetOutputPort());
    transformFilter.SetTransform(transform);

    self.sphere = vtk.vtkSphereSource()
    self.sphere.SetRadius(3.0);
    self.sphere.SetCenter(0, 0, 0);

    self.append = vtk.vtkAppendPolyData()
    self.append.AddInputConnection(self.sphere.GetOutputPort());
    self.append.AddInputConnection(transformFilter.GetOutputPort());
    self.append.Update();

    locatorModelNode.SetAndObservePolyData(self.append.GetOutput())

  def initiateZFrameCalibration(self):
    # If there is a zFrame image selected, perform the calibration step to calculate the CLB matrix
    self.inputVolume = self.zFrameVolumeSelector.currentNode()

    if self.inputVolume is not None:
      seriesNumber = self.inputVolume.GetName().split(":")[0]
      name = seriesNumber + "-ZFrameTransform"
      
      # Create an empty transform for the calibration matrix output
      if self.outputTransform:
        slicer.mrmlScene.RemoveNode(self.outputTransform)
        self.outputTransform = None
      self.outputTransform = slicer.vtkMRMLLinearTransformNode()
      self.outputTransform.SetName(name)
      slicer.mrmlScene.AddNode(self.outputTransform)

      print ("Initating calibration matrix calculation with zFrame image.")
      
      # Get start and end slices
      self.startSlice = int(self.startSliceSliderWidget.value)
      self.endSlice = int(self.endSliceSliderWidget.value)
      maxSlice = self.inputVolume.GetImageData().GetDimensions()[2]
      if self.endSlice == 0 or self.endSlice > maxSlice:
        # Use the image end slice
        self.endSlice = maxSlice
        self.endSliceSliderWidget.value = float(self.endSlice)

      # Check for the ZFrame ROI node and if it exists, use it for the start and end slices
      if self.zFrameROI is not None:
        print ("Found zFrame ROI: ", self.zFrameROI.GetID())
        center = [0.0, 0.0, 0.0]
        self.zFrameROI.GetXYZ(center)
        bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.zFrameROI.GetRASBounds(bounds)
        pMin = [bounds[0], bounds[2], bounds[4], 1]
        pMax = [bounds[1], bounds[3], bounds[5], 1]
        rasToIJKMatrix = vtk.vtkMatrix4x4()
        self.inputVolume.GetRASToIJKMatrix(rasToIJKMatrix)
        pos = [0,0,0,1]
        rasToIJKMatrix.MultiplyPoint(pMin, pos)
        self.startSlice = int(pos[2])
        rasToIJKMatrix.MultiplyPoint(pMax, pos)
        self.endSlice = int(pos[2])
        # Check if slices are in bounds
        if self.startSlice < 0:
          self.startSlice = 0
        if self.endSlice < 0:
          self.endSlice = 0
        endZ = self.inputVolume.GetImageData().GetDimensions()[2]
        endZ = endZ - 1
        if self.startSlice > endZ:
          self.startSlice = endZ
        if self.endSlice > endZ:
          self.endSlice = endZ
        self.startSliceSliderWidget.value = float(self.startSlice)
        self.endSliceSliderWidget.value = float(self.endSlice)

        # Begin zFrameRegistrationWithROI logic
        self.ZFRAME_MODEL_PATH = 'zframe-model.vtk'
        self.ZFRAME_MODEL_NAME = 'ZFrameModel'

        # Cleanup
        #self.clearVolumeNodes()
        #self.clearOldCalculationNodes()
        
        # Run ZFrame Open Source Registration
        self.loadZFrameModel()

        zFrameTemplateVolume = self.inputVolume
        coverTemplateROI = self.zFrameROI

        self.zFrameCroppedVolume = self.createCroppedVolume(zFrameTemplateVolume, coverTemplateROI)
        self.zFrameLabelVolume = self.createLabelMapFromCroppedVolume(self.zFrameCroppedVolume, "labelmap")
        self.zFrameMaskedVolume = self.createMaskedVolume(zFrameTemplateVolume, self.zFrameLabelVolume)
        self.zFrameMaskedVolume.SetName(zFrameTemplateVolume.GetName() + "-label")
        if self.startSlice is None or self.endSlice is None:
          self.startSlice, center, self.endSlice = self.getROIMinCenterMaxSliceNumbers(coverTemplateROI)
          self.otsuOutputVolume = self.applyITKOtsuFilter(self.zFrameMaskedVolume)
          self.dilateMask(self.otsuOutputVolume)
          self.startSlice, self.endSlice = self.getStartEndWithConnectedComponents(self.otsuOutputVolume, center)
        # self.openSourceRegistration.setInputVolume(self.zFrameMaskedVolume)
        # self.openSourceRegistration.runRegistration(self.startIndex, self.endIndex)
        
      
        # TODO


        # Run zFrameRegistration CLI module
        params = {'inputVolume': self.zFrameMaskedVolume, 'startSlice': self.startSlice, 'endSlice': self.endSlice,
                  'outputTransform': self.outputTransform}
        slicer.cli.run(slicer.modules.zframeregistration, None, params, wait_for_completion=True)

        self.zFrameModelNode.SetAndObserveTransformNodeID(self.outputTransform.GetID())
        self.zFrameModelNode.GetDisplayNode().SetSliceIntersectionVisibility(True)
        self.zFrameModelNode.SetDisplayVisibility(True)

        # self.setBackgroundAndForegroundIDs(foregroundVolumeID=None, backgroundVolumeID=self.inputVolume.GetID())
        # self.redSliceNode.SetSliceVisible(True)
        # self.clearVolumeNodes()

        # Update the calibration matrix table with the calculated matrix (currently just dummy code)
        print("1: ", self.outputTransform)
        outputMatrix = vtk.vtkMatrix4x4()
        self.outputTransform.GetMatrixTransformToParent(outputMatrix)
        print("2: ", outputMatrix)
        for i in range(4):
          for j in range(4):
            self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(outputMatrix.GetElement(i, j),2))))

        # Send the calculated calibration matrix to WPI as the CLB matrix
        SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
        SendTransformNodeTemp.SetName("REGISTRATION")
        SendTransformNodeTemp.SetMatrixTransformToParent(outputMatrix)
        slicer.mrmlScene.AddNode(SendTransformNodeTemp)
        self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
        self.openIGTNode.PushNode(SendTransformNodeTemp)
        infoMsg =  "Sending TRANSFORM( REGISTRATION )"
        re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
        self.infoTextbox.setText(infoMsg)
        attr = SendTransformNodeTemp.GetAttribute("IGTLVisible");

    else:
      print("No zFrame image found. Cannot calculate the calibration matrix.")

  def onSendCalibrationMatrixButtonClicked(self):
    # If there is a calibration matrix already defined in the Slicer scene (pre-calculated outside of the module for testing/development purposes)
    inputVolume = self.zFrameVolumeSelector.currentNode()
    predefinedCalibrationMatrixNode = self.calibrationMatrixSelector.currentNode()

    if predefinedCalibrationMatrixNode is not None:
      # Send the pre-determined calibration matrix to WPI as the CLB matrix
      calibrationMatrix = vtk.vtkMatrix4x4()
      predefinedCalibrationMatrixNode.GetMatrixTransformToParent(calibrationMatrix)
      SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
      SendTransformNodeTemp.SetName("REGISTRATION")
      SendTransformNodeTemp.SetMatrixTransformToParent(calibrationMatrix)
      slicer.mrmlScene.AddNode(SendTransformNodeTemp)
      self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
      self.openIGTNode.PushNode(SendTransformNodeTemp)
      infoMsg =  "Sending TRANSFORM( REGISTRATION )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.infoTextbox.setText(infoMsg)
      attr = SendTransformNodeTemp.GetAttribute("IGTLVisible");
      # print("attribute is:", attr) 
    
      # Update the calibration matrix table with the calculated matrix (currently just dummy code)
      for i in range(4):
        for j in range(4):
          self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(calibrationMatrix.GetElement(i, j),2))))

    elif inputVolume is not None:
      self.initiateZFrameCalibration()

    else:
      print("No zFrame image or pre-defined calibration matrix found. Cannot calculate the calibration matrix.")

  def onSendTargetPointButtonClicked(self):
    targetPointNode = self.targetPointNodeSelector.currentNode()
    if not targetPointNode:
      print ("No TARGET_POINT fiducial selected.")
    else:
      # Print RAS coordinates of the target point fiducial into the Target point GUI
      targetCoordinatesRAS = [0, 0, 0]
      targetPointNode.GetNthFiducialPosition(0, targetCoordinatesRAS)

      self.targetCoordinate_R = round(targetCoordinatesRAS[0],2)
      self.targetCoordinate_A = round(targetCoordinatesRAS[1],2)
      self.targetCoordinate_S = round(targetCoordinatesRAS[2],2)

      self.targetPointTextbox_R.setText(str(self.targetCoordinate_R))
      self.targetPointTextbox_A.setText(str(self.targetCoordinate_A))
      self.targetPointTextbox_S.setText(str(self.targetCoordinate_S))

      # Send target point via IGTLink as a 4x4 matrix transform called TARGET_POINT
      targetPointMatrix = vtk.vtkMatrix4x4()
      targetPointMatrix.Identity()
      targetPointMatrix.SetElement(0,3,self.targetCoordinate_R)
      targetPointMatrix.SetElement(1,3,self.targetCoordinate_A)
      targetPointMatrix.SetElement(2,3,self.targetCoordinate_S)
      SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
      SendTransformNodeTemp.SetName("TARGET_POINT")
      SendTransformNodeTemp.SetMatrixTransformToParent(targetPointMatrix)
      slicer.mrmlScene.AddNode(SendTransformNodeTemp)
      self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
      self.openIGTNode.PushNode(SendTransformNodeTemp)
      infoMsg =  "Sending TRANSFORM( TARGET_POINT )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.infoTextbox.setText(infoMsg)
      attr = SendTransformNodeTemp.GetAttribute("IGTLVisible");
      print("attribute is:", attr) 

# # ------------------------- FUNCTIONS FOR ROI BOUNDING BOX STEP ---------------------------

  def onAddROI(self):
    self.addROIAddedObserver()
    # Go into place ROI mode
    selectionNode =  slicer.util.getNode('vtkMRMLSelectionNodeSingleton')
    selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationROINode")
    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.StartPlaceMode(False)

  def removeZFrameROIAddedObserver(self):
    if self.zFrameROIAddedObserverTag is not None:
      if slicer.mrmlScene is not None:
        slicer.mrmlScene.RemoveObserver(self.zFrameROIAddedObserverTag)
      self.zFrameROIAddedObserverTag = None

  def addROIAddedObserver(self):
    @vtk.calldata_type(vtk.VTK_OBJECT)
    def onNodeAdded(caller, event, calldata):
      node = calldata
      if isinstance(node, slicer.vtkMRMLAnnotationROINode):
        self.removeZFrameROIAddedObserver()
        self.zFrameROI = node
        self.zFrameROI.SetName("Registration ROI")

    # Remove any previous node added observer
    self.removeZFrameROIAddedObserver()
    # Remove previous ROI if any
    if self.zFrameROI is not None:
      slicer.mrmlScene.RemoveNode(self.zFrameROI)
      self.zFrameROI = None
    self.zFrameROIAddedObserverTag = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, onNodeAdded)

# # ------------------------- FUNCTIONS FOR CALIBRATION STEP ---------------------------

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

  def clearOldCalculationNodes(self):
    #if self.openSourceRegistration.inputVolume:
    if self.inputVolume:
      #slicer.mrmlScene.RemoveNode(self.openSourceRegistration.inputVolume)
      #self.openSourceRegistration.inputVolume = None
      slicer.mrmlScene.RemoveNode(self.inputVolume)
      self.inputVolume = None
    if self.zFrameModelNode:
      slicer.mrmlScene.RemoveNode(self.zFrameModelNode)
      self.zFrameModelNode = None
    #if self.openSourceRegistration.outputTransform:
    if self.outputTransform:
      #slicer.mrmlScene.RemoveNode(self.openSourceRegistration.outputTransform)
      #self.openSourceRegistration.outputTransform = None
      slicer.mrmlScene.RemoveNode(self.outputTransform)
      self.outputTransform = None
  
  def loadZFrameModel(self):
    if self.zFrameModelNode:
      slicer.mrmlScene.RemoveNode(self.zFrameModelNode)
      self.zFrameModelNode = None
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    print("zframe current file path: ", currentFilePath)
    zFrameModelPath = os.path.join(currentFilePath, "Resources", "zframe", self.ZFRAME_MODEL_PATH)
    _, self.zFrameModelNode = slicer.util.loadModel(zFrameModelPath, returnNode=True)
    self.zFrameModelNode.SetName(self.ZFRAME_MODEL_NAME)
    modelDisplayNode = self.zFrameModelNode.GetDisplayNode()
    modelDisplayNode.SetColor(1, 1, 0)
    self.zFrameModelNode.SetDisplayVisibility(False)

  def applyITKOtsuFilter(self, volume):
    inputVolume = sitk.Cast(sitkUtils.PullVolumeFromSlicer(volume.GetID()), sitk.sitkInt16)
    self.otsuFilter.SetInsideValue(0)
    self.otsuFilter.SetOutsideValue(1)
    otsuITKVolume = self.otsuFilter.Execute(inputVolume)
    return sitkUtils.PushToSlicer(otsuITKVolume, "otsuITKVolume", 0, True)

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

  def createCroppedVolume(self, inputVolume, roi):
    cropVolumeLogic = slicer.modules.cropvolume.logic()
    cropVolumeParameterNode = slicer.vtkMRMLCropVolumeParametersNode()
    cropVolumeParameterNode.SetROINodeID(roi.GetID())
    cropVolumeParameterNode.SetInputVolumeNodeID(inputVolume.GetID())
    cropVolumeParameterNode.SetVoxelBased(True)
    cropVolumeLogic.Apply(cropVolumeParameterNode)
    croppedVolume = slicer.mrmlScene.GetNodeByID(cropVolumeParameterNode.GetOutputVolumeNodeID())
    return croppedVolume

  def createLabelMapFromCroppedVolume(self, volume, name):
    lowerThreshold = 0
    upperThreshold = 2000
    labelValue = 1
    volumesLogic = slicer.modules.volumes.logic()
    labelVolume = volumesLogic.CreateAndAddLabelVolume(volume, name)
    imageData = labelVolume.GetImageData()
    imageThreshold = vtk.vtkImageThreshold()
    imageThreshold.SetInputData(imageData)
    imageThreshold.ThresholdBetween(lowerThreshold, upperThreshold)
    imageThreshold.SetInValue(labelValue)
    imageThreshold.Update()
    labelVolume.SetAndObserveImageData(imageThreshold.GetOutput())
    return labelVolume

  def createMaskedVolume(self, inputVolume, labelVolume):
    maskedVolume = slicer.vtkMRMLScalarVolumeNode()
    maskedVolume.SetName("maskedTemplateVolume")
    slicer.mrmlScene.AddNode(maskedVolume)
    params = {'InputVolume': inputVolume, 'MaskVolume': labelVolume, 'OutputVolume': maskedVolume}
    slicer.cli.run(slicer.modules.maskscalarvolume, None, params, wait_for_completion=True)
    return maskedVolume

  # def setBackgroundAndForegroundIDs(self, foregroundVolumeID, backgroundVolumeID):
    # self.redCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    # self.redCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    # self.redSliceNode.SetOrientationToAxial()
    # self.yellowCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    # self.yellowCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    # self.yellowSliceNode.SetOrientationToSagittal()
    # self.greenCompositeNode.SetForegroundVolumeID(foregroundVolumeID)
    # self.greenCompositeNode.SetBackgroundVolumeID(backgroundVolumeID)
    # self.greenSliceNode.SetOrientationToCoronal()