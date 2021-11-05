import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import time

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

  # Status codes -- see igtl_status.h
  #status_codes = {'STATUS_INVALID': 0, 'STATUS_OK':1, 'STATUS_UNKNOWN_ERROR': 2, 'STATUS_PANICK_MODE': 3, 'STATUS_NOT_FOUND': 4, 'STATUS_ACCESS_DENIED': 5, 'STATUS_BUSY':6, 'STATUS_TIME_OUT':7, 'STATUS_OVERFLOW':8,'STATUS_CHECKSUM_ERROR':9,'STATUS_CONFIG_ERROR':10,'STATUS_RESOURCE_ERROR':11,'STATUS_UNKNOWN_INSTRUCTION':12,'STATUS_NOT_READY':13,'STATUS_MANUAL_MODE':14,'STATUS_DISABLED':15,'STATUS_NOT_PRESENT':16,'STATUS_UNKNOWN_VERSION':17,'STATUS_HARDWARE_FAILURE':18,'STATUS_SHUT_DOWN':19,'STATUS_NUM_TYPES':20}
  status_codes = ['STATUS_INVALID', 'STATUS_OK', 'STATUS_UNKNOWN_ERROR', 'STATUS_PANICK_MODE', 'STATUS_NOT_FOUND', 'STATUS_ACCESS_DENIED', 'STATUS_BUSY', 'STATUS_TIME_OUT', 'STATUS_OVERFLOW','STATUS_CHECKSUM_ERROR','STATUS_CONFIG_ERROR','STATUS_RESOURCE_ERROR','STATUS_UNKNOWN_INSTRUCTION','STATUS_NOT_READY','STATUS_MANUAL_MODE','STATUS_DISABLED','STATUS_NOT_PRESENT','STATUS_UNKNOWN_VERSION','STATUS_HARDWARE_FAILURE','STATUS_SHUT_DOWN','STATUS_NUM_TYPES']
 
  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Server collapsible button
    serverCollapsibleButton = ctk.ctkCollapsibleButton()
    serverCollapsibleButton.text = "Start IGTLink Server"
    self.layout.addWidget(serverCollapsibleButton)

    # Layout within the path collapsible button
    serverFormLayout = qt.QFormLayout(serverCollapsibleButton)

    # self.wpiPortTextbox = qt.QLineEdit("18944")
    # self.wpiPortTextbox.setReadOnly(False)
    # self.wpiPortTextbox.setFixedWidth(75)
    # serverFormLayout.addRow("WPI server port:", self.wpiPortTextbox)

    # self.wpiHostnameTextbox = qt.QLineEdit("localhost")
    # self.wpiHostnameTextbox.setReadOnly(False)
    # self.wpiHostnameTextbox.setFixedWidth(75)
    # serverFormLayout.addRow("WPI hostname:", self.wpiHostnameTextbox)

    self.snrPortTextbox = qt.QLineEdit("18944")
    self.snrPortTextbox.setReadOnly(False)
    self.snrPortTextbox.setFixedWidth(75)
    serverFormLayout.addRow("SNR server port:", self.snrPortTextbox)

    self.snrHostnameTextbox = qt.QLineEdit("localhost")
    self.snrHostnameTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setFixedWidth(75)
    serverFormLayout.addRow("SNR hostname:", self.snrHostnameTextbox)

    # self.testNumberTextbox = qt.QLineEdit("1")
    # self.testNumberTextbox.setReadOnly(False)
    # self.testNumberTextbox.setFixedWidth(75)
    # serverFormLayout.addRow("Test number:", self.testNumberTextbox)

    # Connect to client button
    self.connectToClientButton = qt.QPushButton("Connect to client")
    self.connectToClientButton.toolTip = "Create the IGTLink server connection with shell."
    self.connectToClientButton.enabled = True
    self.connectToClientButton.setMaximumWidth(150)
    serverFormLayout.addRow(self.connectToClientButton)
    self.connectToClientButton.connect('clicked()', self.onConnectToClientButtonClicked)

    self.disconnectFromSocketButton = qt.QPushButton("Disconnect from socket")
    self.disconnectFromSocketButton.toolTip = "Disconnect from the socket when you finish using audio"
    self.disconnectFromSocketButton.enabled = True
    self.disconnectFromSocketButton.setMaximumWidth(150)
    serverFormLayout.addRow(self.disconnectFromSocketButton)
    self.disconnectFromSocketButton.connect('clicked()', self.onDisconnectFromSocketButtonClicked)

    # Outbound messages collapsible button
    outboundCollapsibleButton = ctk.ctkCollapsibleButton()
    outboundCollapsibleButton.text = "Outbound string messages (Slicer -> WPI)"
    self.layout.addWidget(outboundCollapsibleButton)

    # Layout within the path collapsible button
    outboundFormLayout = qt.QFormLayout(outboundCollapsibleButton)

    # TODO -- send messages
    self.phaseTextbox = qt.QLineEdit("")
    self.phaseTextbox.setReadOnly(True)
    self.phaseTextbox.setFixedWidth(150)
    self.phaseTextbox.toolTip = "Blue if in the phase, green if phase successfully achieved"
    outboundFormLayout.addRow("Current phase:", self.phaseTextbox)

    # startupButton Button
    self.startupButton = qt.QPushButton("START UP")
    self.startupButton.toolTip = "Send the startup command to the WPI robot."
    self.startupButton.enabled = True
    self.startupButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.startupButton)
    self.startupButton.connect('clicked()', self.onStartupButtonClicked)

    # planningButton Button # TODO Check protocol: should it print sucess after CURRENT_STATUS is sent?
    self.planningButton = qt.QPushButton("PLANNING")
    self.planningButton.toolTip = "Send the planning command to the WPI robot."
    self.planningButton.enabled = True
    self.planningButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.planningButton)
    self.planningButton.connect('clicked()', self.onPlanningButtonClicked)

    # calibrationButton Button
    self.calibrationButton = qt.QPushButton("CALIBRATION")
    self.calibrationButton.toolTip = "Send the calibration command to the WPI robot."
    self.calibrationButton.enabled = True
    self.calibrationButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.calibrationButton)
    self.calibrationButton.connect('clicked()', self.onCalibrationButtonClicked)

    # targetingButton Button
    self.targetingButton = qt.QPushButton("TARGETING")
    self.targetingButton.toolTip = "Send the targeting command to the WPI robot."
    self.targetingButton.enabled = True
    self.targetingButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.targetingButton)
    self.targetingButton.connect('clicked()', self.onTargetingButtonClicked)

    # moveButton Button
    self.moveButton = qt.QPushButton("MOVE")
    self.moveButton.toolTip = "Send the move to target command to the WPI robot."
    self.moveButton.enabled = True
    self.moveButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.moveButton)
    self.moveButton.connect('clicked()', self.onMoveButtonClicked)

    # Lock Button to ask WPI to lock robot
    self.LockButton = qt.QPushButton("LOCK")
    self.LockButton.toolTip = "Send the command to ask the operator to lock the WPI robot."
    self.LockButton.enabled = True
    self.LockButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.LockButton)
    self.LockButton.connect('clicked()', self.onLockButtonClicked)

    # Unlock Button to ask WPI to unlock robot
    self.UnlockButton = qt.QPushButton("UNLOCK")
    self.UnlockButton.toolTip = "Send the command to ask the operator to unlock the WPI robot."
    self.UnlockButton.enabled = True
    self.UnlockButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.UnlockButton)
    self.UnlockButton.connect('clicked()', self.onUnlockButtonClicked)

    # Get robot pose Button to ask WPI to send the current robot position
    self.GetPoseButton = qt.QPushButton("GET POSE")
    self.GetPoseButton.toolTip = "Send the command to ask WPI to send the current robot position."
    self.GetPoseButton.enabled = True
    self.GetPoseButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.GetPoseButton)
    self.GetPoseButton.connect('clicked()', self.onGetPoseButtonClicked)

    # Get robot status Button to ask WPI to send the current status position
    self.GetStatusButton = qt.QPushButton("GET STATUS")
    self.GetStatusButton.toolTip = "Send the command to ask WPI to send the current robot status."
    self.GetStatusButton.enabled = True
    self.GetStatusButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.GetStatusButton)
    self.GetStatusButton.connect('clicked()', self.onGetStatusButtonClicked)

    # STOP Button 
    self.StopButton = qt.QPushButton("STOP")
    self.StopButton.toolTip = "Send the command to ask the operator to stop the WPI robot."
    self.StopButton.enabled = True
    self.StopButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.StopButton)
    self.StopButton.connect('clicked()', self.onStopButtonClicked)

    # EMERGENCY Button 
    self.EmergencyButton = qt.QPushButton("EMERGENCY")
    self.EmergencyButton.toolTip = "Send emergency command to WPI robot."
    self.EmergencyButton.enabled = True
    self.EmergencyButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.EmergencyButton)
    self.EmergencyButton.connect('clicked()', self.onEmergencyButtonClicked)

    # Outbound Status message collapsible button
    outboundStatusCollapsibleButton = ctk.ctkCollapsibleButton()
    outboundStatusCollapsibleButton.text = "Outbound status messages (Slicer -> WPI)"
    self.layout.addWidget(outboundStatusCollapsibleButton)

    # Layout within the path collapsible button
    outboundStatusFormLayout = qt.QFormLayout(outboundStatusCollapsibleButton)

    # statusButton Button
    self.statusButton = qt.QPushButton("STATUS")
    self.statusButton.toolTip = "Send the Slicer Status command to the WPI robot."
    self.statusButton.enabled = True
    self.statusButton.setMaximumWidth(150)
    outboundStatusFormLayout.addRow(self.statusButton)
    self.statusButton.connect('clicked()', self.onStatusButtonClicked)

    # Outbound tranform collapsible button
    outboundTransformCollapsibleButton = ctk.ctkCollapsibleButton()
    outboundTransformCollapsibleButton.text = "Outbound transforms (Slicer -> WPI)"
    self.layout.addWidget(outboundTransformCollapsibleButton)


    # Layout within the path collapsible button
    outboundTransformsFormLayout = qt.QFormLayout(outboundTransformCollapsibleButton)

    # transformButton Button
    self.transformButton = qt.QPushButton("TRANSFORM")
    self.transformButton.toolTip = "Send transform to the WPI robot."
    self.transformButton.enabled = True
    self.transformButton.setMaximumWidth(150)
    outboundTransformsFormLayout.addRow(self.transformButton)
    self.transformButton.connect('clicked()', self.onTransformButtonClicked)

    # Inbound messages collapsible button
    inboundCollapsibleButton = ctk.ctkCollapsibleButton()
    inboundCollapsibleButton.text = "Inbound messages (WPI -> Slicer)"
    self.layout.addWidget(inboundCollapsibleButton)


    # Layout within the path collapsible button
    inboundFormLayout = qt.QFormLayout(inboundCollapsibleButton)

    # TODO -- receive messages
  
    # potentially insert a table here that will auto-update as messages
    # are received via IGTLink so that the incoming messages can be
    # seen on the GUI without switching to another module

    self.messageTextbox = qt.QLineEdit("No message received")
    self.messageTextbox.setReadOnly(True)
    self.messageTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Message received:", self.messageTextbox)

    self.statusTextbox = qt.QLineEdit("No status received")
    self.statusTextbox.setReadOnly(True)
    self.statusTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Status received\n(Code:Subcode:ErrorName:Message):", self.statusTextbox)

    self.statusCodeTextbox = qt.QLineEdit("No status Code received")
    self.statusCodeTextbox.setReadOnly(True)
    self.statusCodeTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Status Code meaning: ", self.statusCodeTextbox)

    #self.newItem = qt.QTableWidgetItem()
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


    #self.MonWidget = qt.QTableWidget.setItem(row, column, self.newItem);
    #QTableWidgetItem *newItem = new QTableWidgetItem(tr("%1").arg(pow(row, column+1)));
    #tableWidget->setItem(row, column, newItem);
    #self.mamatrix = qt.QMatrix4x4 ()
    #self.transformTextbox = qt.QLineEdit("No transform received")
    #self.transformTextbox.setReadOnly(True)
    #self.transformTextbox.setFixedWidth(200)
    #inboundFormLayout.addRow("Transform received:", self.transformTextbox)
    

    #slicer.vtkMRMLTableNode()

    # choosing phase collapsible button
    #phaseCollapsibleButton = ctk.ctkCollapsibleButton()
    #phaseCollapsibleButton.text = "Choosing phase to enter"
    #self.layout.addWidget(phaseCollapsibleButton)

    # Layout within the path collapsible button
    #outboundFormLayout = qt.QFormLayout(phaseCollapsibleButton)

    # Allow user to enter different phases of protocol
    #
    # the text selectors
    #

    #self.textSelector = slicer.qMRMLNodeComboBox()
    #self.textSelector.nodeTypes = ["vtkMRMLTextNode"]
    #self.textSelector.addEnabled = False
    #self.textSelector.removeEnabled = False
    #self.textSelector.setMRMLScene(slicer.mrmlScene)
    #outboundFormLayout.addRow("Text input: ", self.textSelector)

  
    # Add vertical spacer
    self.layout.addStretch(1)

    self.textNode = slicer.vtkMRMLTextNode()
    self.textNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(self.textNode)

  def onConnectToClientButtonClicked(self):
    snrPort = self.snrPortTextbox.text
    snrHostname = self.snrHostnameTextbox.text
    print("Slicer-side port number: ", snrPort)

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

    # Add observers on the 3 message type nodes
    ReceivedStringMsg.AddObserver(slicer.vtkMRMLTextNode.TextModifiedEvent, self.onTextNodeModified)
    ReceivedStatusMsg.AddObserver(slicer.vtkMRMLIGTLStatusNode.StatusModifiedEvent, self.onStatusNodeModified)
    ReceivedTransformMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTransformNodeModified)

    # Initialize las_string_sent 
    global last_string_sent 
    last_string_sent = "nostring"
    global start
    start = 0
    global ack
    ack = 0
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

   
  def onGetStatusButtonClicked(self):
    # Send stringMessage containing the command "GET STATUS" to the script via IGTLink
    print("Send command to get current status of the robot")
    getstatusNode = slicer.vtkMRMLTextNode()
    getstatusNode.SetText("GET_STATUS")
    slicer.mrmlScene.AddNode(getstatusNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getstatusNode)
    self.openIGTNode.PushNode(getstatusNode)

  def onGetPoseButtonClicked(self):
    # Send stringMessage containing the command "GET POSE" to the script via IGTLink
    print("Send command to get current position of the robot")
    getposeNode = slicer.vtkMRMLTextNode()
    getposeNode.SetText("GET_POSE")
    slicer.mrmlScene.AddNode(getposeNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getposeNode)
    self.openIGTNode.PushNode(getposeNode)


  def onTargetingButtonClicked(self):
    # Send stringMessage containing the command "TARGETING" to the script via IGTLink
    print("Send command to enter targeting mode")
    targetingNode = slicer.vtkMRMLTextNode()
    targetingNode.SetText("TARGETING")
    slicer.mrmlScene.AddNode(targetingNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(targetingNode)
    self.openIGTNode.PushNode(targetingNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = targetingNode.GetText()
    global ack
    ack = 0

  def onMoveButtonClicked(self):
    # Send stringMessage containing the command "MOVE" to the script via IGTLink
    print("Send command to ask robot to move to target")
    moveNode = slicer.vtkMRMLTextNode()
    moveNode.SetText("MOVE_TO_TARGET")
    slicer.mrmlScene.AddNode(moveNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(moveNode)
    self.openIGTNode.PushNode(moveNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = moveNode.GetText()
    global ack
    ack = 0
  
  def onCalibrationButtonClicked(self):
    # Send stringMessage containing the command "CALIBRATION" to the script via IGTLink
    print("Sending calibration command to WPI robot")
    calibrationNode = slicer.vtkMRMLTextNode()
    calibrationNode.SetText("CALIBRATION")
    slicer.mrmlScene.AddNode(calibrationNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(calibrationNode)
    self.openIGTNode.PushNode(calibrationNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = calibrationNode.GetText()
    global ack
    ack = 0


  def onPlanningButtonClicked(self):
    # Send stringMessage containing the command "PLANNING" to the script via IGTLink
    print("Sending planning command to WPI robot")
    planningNode = slicer.vtkMRMLTextNode()
    planningNode.SetText("PLANNING")
    slicer.mrmlScene.AddNode(planningNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(planningNode)
    self.openIGTNode.PushNode(planningNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = planningNode.GetText()
    global ack
    ack = 0
    

  def onUnlockButtonClicked(self):
    print("Asking to Unlock the robot")
    # Send stringMessage containing the command "UNLOCK" to the script via IGTLink
    unlockNode = slicer.vtkMRMLTextNode()
    unlockNode.SetText("UNLOCK")
    slicer.mrmlScene.AddNode(unlockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(unlockNode)
    self.openIGTNode.PushNode(unlockNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = unlockNode.GetText()
    global ack
    ack = 0

  def onLockButtonClicked(self):
    print("Asking to Lock the robot")
    # Send stringMessage containing the command "LOCK" to the script via IGTLink
    lockNode = slicer.vtkMRMLTextNode()
    lockNode.SetText("LOCK")
    slicer.mrmlScene.AddNode(lockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(lockNode)
    self.openIGTNode.PushNode(lockNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = lockNode.GetText()
    global ack
    ack = 0

  def onStopButtonClicked(self):
    print("Sending STOP command")
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    stopNode = slicer.vtkMRMLTextNode()
    stopNode.SetText("STOP")
    slicer.mrmlScene.AddNode(stopNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(stopNode)
    self.openIGTNode.PushNode(stopNode);
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = stopNode.GetText()
    global ack
    ack = 0

  def onEmergencyButtonClicked(self):
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    print("Sending Emergency command")
    emergencyNode = slicer.vtkMRMLTextNode()
    emergencyNode.SetText("EMERGENCY")
    slicer.mrmlScene.AddNode(emergencyNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(emergencyNode)
    self.openIGTNode.PushNode(emergencyNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = emergencyNode.GetText()
    global ack
    ack = 0
    
  def onStartupButtonClicked(self):
    # Send stringMessage containing the command "START_UP" to the script via IGTLink
    print("Sending Start up command")
    startupNode = slicer.vtkMRMLTextNode()
    startupNode.SetText("START_UP")
    slicer.mrmlScene.AddNode(startupNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(startupNode)
    self.openIGTNode.PushNode(startupNode)
    global start   
    start = time.time()
    global last_string_sent
    last_string_sent = startupNode.GetText()
    global ack
    ack = 0


  def onStatusButtonClicked(self):
    #Send Status message
    print("Sending Status")
    statusNode = slicer.vtkMRMLIGTLStatusNode()
    statusNode.SetStatusString("STATUS_OK")
    slicer.mrmlScene.AddNode(statusNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(statusNode)
    self.openIGTNode.PushNode(statusNode)

  def onTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)
    print(transformMatrix)
    nbRows = transformNode.tableWidget.rowCount
    nbColumns = transformNode.tableWidget.columnCount
    for i in range(nbRows):
      for j in range(nbColumns):
        val = transformMatrix.GetElement(i,j)
        transformNode.tableWidget.setItem(i , j, qt.QTableWidgetItem(str(val)))

  def onTransformButtonClicked(self):
    #Send Transform message
    print("Sending Transform")
    obj = vtk.vtkMatrix4x4()
    print(obj)
    transformNode = slicer.vtkMRMLLinearTransformNode()
    transformNode.SetMatrixTransformToParent(obj);
    slicer.mrmlScene.AddNode(transformNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(transformNode)
    self.openIGTNode.PushNode(transformNode)
  
  def onTextNodeModified(textNode, unusedArg2=None, unusedArg3=None):
    print("New string was received")
    ReceivedStringMsg = slicer.mrmlScene.GetFirstNodeByName("StringMessage")
    textNode.messageTextbox.setText(ReceivedStringMsg.GetText())
    end = time.time()
    elapsed_time = (end - start)*100
    if(last_string_sent == ReceivedStringMsg.GetText()): #and (elapsed_time<= 100)
      print("Acknowledgment received for command:", last_string_sent, "after", elapsed_time, "ms")
      global ack
      ack = 1
    else: # if(elapsed_time > 100) print("Received knowledgment too late, after", elapsed_time, "ms")
      print("Received something different than aknowledgment, received: ", ReceivedStringMsg.GetText())
      
  def onStatusNodeModified(statusNode, unusedArg2=None, unusedArg3=None):
    print("New Status was received")
    ReceivedStatusMsg = slicer.mrmlScene.GetFirstNodeByName("StatusMessage")
    s1 = str(ReceivedStatusMsg.GetCode())
    sep = ':'
    s2 = str(ReceivedStatusMsg.GetSubCode())
    s3 = ReceivedStatusMsg.GetErrorName()
    s4 = ReceivedStatusMsg.GetStatusString()
    s = s1 + sep + s2 + sep + s3 + sep + s4
    statusNode.statusTextbox.setText(s)
    global status_codes
    status_codes = ['STATUS_INVALID', 'STATUS_OK', 'STATUS_UNKNOWN_ERROR', 'STATUS_PANICK_MODE', 'STATUS_NOT_FOUND', 'STATUS_ACCESS_DENIED', 'STATUS_BUSY', 'STATUS_TIME_OUT', 'STATUS_OVERFLOW','STATUS_CHECKSUM_ERROR','STATUS_CONFIG_ERROR','STATUS_RESOURCE_ERROR','STATUS_UNKNOWN_INSTRUCTION','STATUS_NOT_READY','STATUS_MANUAL_MODE','STATUS_DISABLED','STATUS_NOT_PRESENT','STATUS_UNKNOWN_VERSION','STATUS_HARDWARE_FAILURE','STATUS_SHUT_DOWN','STATUS_NUM_TYPES']
    statusNode.statusCodeTextbox.setText(status_codes[ReceivedStatusMsg.GetCode()])
    end = time.time()
    elapsed_time = end - start
    global ack
    global loading_phase
    print(ack)
    if((status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (ack == 1)): #and (elapsed_time *100< 100)
      print("Robot is in phase: ", s3, "after", elapsed_time*100, "ms")
      statusNode.phaseTextbox.setText(s3)
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 0, 255);")
      if(s3 == "PLANNING"):
        ack = 0
      else:
        ack = 2
        loading_phase = s3
    elif((status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (ack ==2)): #and (elapsed_time<= 10)
      print("Robot sucessfully achieved : ", loading_phase, "after", elapsed_time, "s")
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);")
      ack = 0
    