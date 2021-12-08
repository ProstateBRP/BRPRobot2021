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
import numpy as np
import time
import random
import string
import re
#import SNR.SlicerIGTlinkExtension.SlicerIGTLink.Workflow.workflowFunctions as workflowFunctions

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
    # nameLabel1 = qt.QLabel('SNR server port:');
    # nameLabel2 = qt.QLabel('SNR hostname: ');
    # serverFormLayout.addWidget(nameLabel1, 0, 0)
    # serverFormLayout.addWidget(nameLabel2, 1, 0)

    # self.snrPortTextbox = qt.QLineEdit("18944")
    # self.snrPortTextbox.setReadOnly(False)
    # self.snrPortTextbox.setFixedWidth(75)
    # serverFormLayout.addWidget(self.snrPortTextbox, 0, 1)

    # self.snrHostnameTextbox = qt.QLineEdit("localhost")
    # self.snrHostnameTextbox.setReadOnly(False)
    # self.snrHostnameTextbox.setFixedWidth(75)
    # serverFormLayout.addWidget(self.snrHostnameTextbox, 1, 1)

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
    self.disconnectFromSocketButton.enabled = True
    self.disconnectFromSocketButton.setMaximumWidth(250)
    # serverFormLayout.addWidget(self.disconnectFromSocketButton, 2, 2, 1, 2)
    serverFormLayout.addWidget(self.disconnectFromSocketButton, 2, 1)
    self.disconnectFromSocketButton.connect('clicked()', self.onDisconnectFromSocketButtonClicked)

    # Outbound messages collapsible button
    outboundCollapsibleButton = ctk.ctkCollapsibleButton()
    outboundCollapsibleButton.text = "Outbound Commands"
    self.layout.addWidget(outboundCollapsibleButton)

    # Layout within the path collapsible button
    outboundFormLayout = qt.QGridLayout(outboundCollapsibleButton)
    
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

    # Outbound Status message collapsible button
    #outboundStatusCollapsibleButton = ctk.ctkCollapsibleButton()
    #outboundStatusCollapsibleButton.text = "Outbound status messages (Slicer -> WPI)"
    #self.layout.addWidget(outboundStatusCollapsibleButton)

    # Layout within the path collapsible button
    #outboundStatusFormLayout = qt.QFormLayout(outboundStatusCollapsibleButton)

    # statusButton Button
    #self.statusButton = qt.QPushButton("STATUS")
    #self.statusButton.toolTip = "Send the Slicer Status to the WPI robot."
    #self.statusButton.enabled = True
    #self.statusButton.setMaximumWidth(150)
    #outboundStatusFormLayout.addRow(self.statusButton)
    #self.statusButton.connect('clicked()', self.onStatusButtonClicked)

    # Outbound tranform collapsible button
    outboundTransformCollapsibleButton = ctk.ctkCollapsibleButton()
    outboundTransformCollapsibleButton.text = "Calibration Matrix"
    self.layout.addWidget(outboundTransformCollapsibleButton)

    # Layout within the path collapsible button
    outboundTransformsFormLayout = qt.QFormLayout(outboundTransformCollapsibleButton)

    # transformButton Button
    # self.transformButton = qt.QPushButton("TRANSFORM")
    # self.transformButton.toolTip = "Send transform to the WPI robot."
    # self.transformButton.enabled = False
    # self.transformButton.setMaximumWidth(250)
    # outboundTransformsFormLayout.addWidget(self.transformButton)
    # self.transformButton.connect('clicked()', self.onTransformButtonClicked)

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
    # zFrameLabel = qt.QLabel('ZFrame image:')
    # outboundTransformsFormLayout.addWidget(zFrameLabel, 1, 0)
    # outboundTransformsFormLayout.addWidget(self.zFrameVolumeSelector, 1, 1)
    outboundTransformsFormLayout.addRow('ZFrame image: ', self.zFrameVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.zFrameVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Start and end slices for calibration step
    self.startSliceSliderWidget = qt.QSpinBox()
    self.endSliceSliderWidget = qt.QSpinBox()
    self.startSliceSliderWidget.setValue(5)
    self.endSliceSliderWidget.setValue(16)
    self.startSliceSliderWidget.setMaximumWidth(40)
    self.endSliceSliderWidget.setMaximumWidth(40)
    outboundTransformsFormLayout.addRow('Minimum slice: ', self.startSliceSliderWidget)
    outboundTransformsFormLayout.addRow('Maximum slice: ', self.endSliceSliderWidget)

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
    outboundTransformsFormLayout.addRow("Calibration matrix:       ", self.calibrationTableWidget)

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
    outboundTransformsFormLayout.addRow("Calibration matrix: ", self.calibrationMatrixSelector)
    # self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
    #                 self.calibrationMatrixSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Send pre-calculated calibration matrix button
    self.sendCalibrationMatrixButton = qt.QPushButton("Send pre-existing calibration matrix")
    self.sendCalibrationMatrixButton.enabled = True
    # self.createCalibrationMatrixButton.setMaximumWidth(250)
    outboundTransformsFormLayout.addWidget(self.sendCalibrationMatrixButton)
    self.sendCalibrationMatrixButton.connect('clicked()', self.onSendCalibrationMatrixButtonClicked)

    # Inbound messages collapsible button
    inboundCollapsibleButton = ctk.ctkCollapsibleButton()
    inboundCollapsibleButton.text = "Inbound Messages"
    self.layout.addWidget(inboundCollapsibleButton)

    # Layout within the path collapsible button
    inboundFormLayout = qt.QFormLayout(inboundCollapsibleButton)

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
    inboundFormLayout.addRow("Status code meaning: ", self.statusCodeTextbox)

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
    inboundFormLayout.addRow("Transform received: ", self.tableWidget)

    # Visibility icon
    self.VisibleButton = qt.QPushButton()
    eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png");
    self.VisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
    self.VisibleButton.setFixedWidth(25)
    self.VisibleButton.setCheckable(True)
    inboundFormLayout.addRow("", self.VisibleButton)
    self.VisibleButton.connect('clicked()', self.onVisibleButtonClicked)
        
    # Info messages collapsible button
    infoCollapsibleButton = ctk.ctkCollapsibleButton()
    infoCollapsibleButton.text = "Info Messages"
    self.layout.addWidget(infoCollapsibleButton)

    # Layout within the path collapsible button
    infoFormLayout = qt.QFormLayout(infoCollapsibleButton)

    self.infoTextbox = qt.QLineEdit("")
    self.infoTextbox.setReadOnly(True)
    self.infoTextbox.setFixedWidth(500)
    infoFormLayout.addRow("", self.infoTextbox)

    #const char* attr3 = inode->GetAttribute("IGTLVisible");
  
    # Add vertical spacer
    self.layout.addStretch(1)

    self.textNode = slicer.vtkMRMLTextNode()
    self.textNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(self.textNode)

  def onCreateServerButtonClicked(self):
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

    # Make a node for each message type
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

    # wpiPort = self.wpiPortTextbox.text
    # wpiHostname = self.wpiHostnameTextbox.text
    # testNumber = self.testNumberTextbox.text    

    # # Auto-run navigationTestSimulator.cxx:
    # import inspect, platform, subprocess
    # plt = platform.system()
    # moduleDirectory = inspect.getabsfile(inspect.currentframe())
    # print("Directory of SlicerIGTLink.py: ", moduleDirectory)
    # moduleDirectory = moduleDirectory.split('SlicerIGTlinkExtension')[0]

    # if plt == 'Windows':
    #   bat_command = moduleDirectory + 'client/RunNavigationTestSimulator.bat'
    #   moduleDirectory = moduleDirectory + 'client'
    #   subprocess.Popen([bat_command, wpiHostname, wpiPort, snrHostname, snrPort, testNumber, moduleDirectory], creationflags=subprocess.CREATE_NEW_CONSOLE, env=slicer.util.startupEnvironment())
    # else: # Linux or Mac
    #   bat_command = moduleDirectory + 'client/RunNavigationTestSimulator.sh'
    #   #c_command = moduleDirectory + 'client/NavigationTestSimulator'
    #   moduleDirectory = moduleDirectory + 'client'
    #   subprocess.Popen(args=['%s %s %s %s %s %s %s' % (bat_command, wpiHostname, wpiPort, snrHostname, snrPort, testNumber, moduleDirectory)], env=slicer.util.startupEnvironment(), shell=True)

  def onDisconnectFromSocketButtonClicked(self):
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
    self.transformButton.enabled = True

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
    self.transformButton.enabled = False
   
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
      if(loading_phase == "CALIBRATION"):
        print ("Robot is awaiting calibration matrix.")
        self.initiateZFrameCalibration()
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
    self.zFrameNode = self.zFrameVolumeSelector.currentNode()
    calibrationMatrix = self.calibrationMatrixSelector.currentNode()

    # self.ngw = slicer.modules.HMS_NeedleGuideWidget

    # if self.zFrameNode is not None:
    #   print ("Initating calibration matrix calculation with zFrame image.")
      
    #   startSlice = int(self.startSliceSliderWidget.value)
    #   # Make sure end slice is within the volume
    #   endSlice = int(self.endSliceSliderWidget.value)
    #   maxSlice = self.zFrameNode.GetImageData().GetDimensions()[2]
    #   if endSlice == 0 or endSlice > maxSlice:
    #     # Use the image end slice
    #     endSlice = maxSlice
    #     self.endSliceSliderWidget.value = float(endSlice)

    #   self.zTransNode = None
    #   self.zTransNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
    #   self.zTransNode.UnRegister(None)
    #   self.zTransNode.SetName('CalibrationTransform')
    #   slicer.mrmlScene.AddNode(self.zTransNode)
    #   workflowFunctions.setParameter('CalibrationTransformNodeID', self.zTransNode.GetID())
      
    #   # The transform between the centers of calibration configuration markers and the guide sheet
    #   # It will be applied to the guide sheet as well as the zTransNode
    #   self.guideSheetTransformNode = None
    #   self.guideSheetTransformNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
    #   self.guideSheetTransformNode.UnRegister(None)
    #   self.guideSheetTransformNode.SetName('GuideSheetTransform')
    #   slicer.mrmlScene.AddNode(self.guideSheetTransformNode)
    #   workflowFunctions.setParameter('GuideSheetTransformID', self.guideSheetTransformNode.GetID())

    #   # To scale and shift the guide sheet holes model
    #   self.guideSheetHolesTransformNode = slicer.vtkMRMLLinearTransformNode()
    #   self.guideSheetHolesTransformNode.SetName('GuideSheetHolesTransform')
    #   slicer.mrmlScene.AddNode(self.guideSheetHolesTransformNode)
    #   workflowFunctions.setParameter('GuideSheetHolesTransformID', self.guideSheetHolesTransformNode.GetID())

    #   # The translation between the center of the guide sheet and it's origin, for use
    #   # when calculating target zone and grid coordinates
    #   self.guideSheetCenterTransformNode = slicer.vtkMRMLLinearTransformNode()
    #   self.guideSheetCenterTransformNode.SetName('GuideSheetCenterTransform')
    #   slicer.mrmlScene.AddNode(self.guideSheetCenterTransformNode)
    #   workflowFunctions.setParameter('GuideSheetCenterTransformID', self.guideSheetCenterTransformNode.GetID())

    #   self.regSuccess = None
    #   self.regSuccess = slicer.mrmlScene.CreateNodeByClass('vtkMRMLLinearTransformNode')
    #   self.regSuccess.UnRegister(None)
    #   self.regSuccess.SetName('regSuccess')
    #   slicer.mrmlScene.AddNode(self.regSuccess)
    #   workflowFunctions.setParameter('RegSuccessNodeID', self.regSuccess.GetID())
    #   self.regSuccess = slicer.util.getNode('regSuccess')
    #   self.goodRegistration = False
    #   self.registrationUserVerified = False

    #   self.guideSheetCenter = np.zeros(3)
    #   self.markersCenter = np.zeros(3)
    #   # Translation between calibration markers and guide sheet corners centers
    #   self.markersToSheetTranslation = np.zeros(3)
    #   self.calibrationOutLabelMapNode = None
    #   self.calibrationMarkerPath = None

    #   parameters = {}
    #   # from nodes:
    #   parameters['inputVolume'] = self.zFrameNode.GetID()
    #   parameters['startSlice'] = startSlice
    #   parameters['endSlice'] = endSlice
    #   parameters['markerConfigFile'] = self.calibrationMarkerPath
    #   parameters['outputVolume'] = self.calibrationOutLabelMapNode.GetID()
    #   parameters['markerTransform'] = self.zTransNode.GetID()
    #   parameters['regSuccess'] = self.regSuccess.GetID()
    #   # from settings:
    #   # ZFrame registration algorithm settings
    #   self.ngw.settings.beginGroup('zframe')
    #   calibrationKeys = self.ngw.settings.allKeys()
    #   self.ngw.settings.endGroup()
    #   for key in calibrationKeys:
    #       parameters[key] = self.getSetting(self.optionsGroup + key)

    #   # Unset the variables that hold post registration flags
    #   self.goodRegistration = False
    #   self.registrationUserVerified = False

    #   linereg = slicer.modules.hms_marker_detection
    #   self.cliNode = slicer.cli.run(linereg, None, parameters, waitForCompletion=True, deleteTemporaryFiles=False)
    #   self.progressBar.setCommandLineModuleNode(self.cliNode)
    #   workflowFunctions.appendToStatusBox("Calibration Started...")
    #   slicer.util.showStatusMessage( "Calibration Started...", 2000 )

    #   workflowFunctions.setStatusLabel("Calibration running...")
    #   self.cliObserver = self.cliNode.AddObserver('ModifiedEvent',self.observeCalibration)

    #   # TODO

    #   # Update the calibration matrix table with the calculated matrix (currently just dummy code)
    #   for i in range(4):
    #     for j in range(4):
    #       self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(1)))

    #   # Send the calculated calibration matrix to WPI as the CLB matrix
    #   # TODO

    # else:
    #   print("No zFrame image found. Cannot calculate the calibration matrix.")
      
  def onSendCalibrationMatrixButtonClicked(self):
    # If there is a calibration matrix already defined in the Slicer scene (pre-calculated outside of the module for testing/development purposes)
    zFrameNode = self.zFrameVolumeSelector.currentNode()
    calibrationMatrixNode = self.calibrationMatrixSelector.currentNode()

    if calibrationMatrixNode is not None:
      # Send the pre-determined calibration matrix to WPI as the CLB matrix
      calibrationMatrix = vtk.vtkMatrix4x4()
      calibrationMatrixNode.GetMatrixTransformToParent(calibrationMatrix)
      randomIDname = self.generateRandomNameID(last_prefix_sent)
      global last_randomIDname_transform
      last_randomIDname_transform = randomIDname
      global last_name_sent
      last_name_sent = randomIDname
      SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
      SendTransformNodeTemp.SetName(randomIDname)
      SendTransformNodeTemp.GetMatrixTransformToParent(calibrationMatrix)
      slicer.mrmlScene.AddNode(SendTransformNodeTemp)
      self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
      self.openIGTNode.PushNode(SendTransformNodeTemp)
      infoMsg =  "Sending TRANSFORM( " + randomIDname + " )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.infoTextbox.setText(infoMsg)
      attr = SendTransformNodeTemp.GetAttribute("IGTLVisible");
      print("attribute is:", attr) 
    
      # Update the calibration matrix table with the calculated matrix (currently just dummy code)
      for i in range(4):
        for j in range(4):
          self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(calibrationMatrix.GetElement(i, j))))

    elif zFrameNode is not None:
      self.initiateZFrameCalibration()

    else:
      print("No zFrame image or pre-defined calibration matrix found. Cannot calculate the calibration matrix.")
