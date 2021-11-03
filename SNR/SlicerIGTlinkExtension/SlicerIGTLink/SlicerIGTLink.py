import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
import time

class SlicerIGTLink(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
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
  last_string_sent = "nostring"
  start = 0
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
    # startupButton Button
    self.startupButton = qt.QPushButton("START UP")
    self.startupButton.toolTip = "Send the startup command to the WPI robot."
    self.startupButton.enabled = True
    self.startupButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.startupButton)
    self.startupButton.connect('clicked()', self.onStartupButtonClicked)

    # STOP Button 
    self.StopButton = qt.QPushButton("STOP")
    self.StopButton.toolTip = "Send the command to ask the operator to stop the WPI robot."
    self.StopButton.enabled = True
    self.StopButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.StopButton)
    self.StopButton.connect('clicked()', self.onStopButtonClicked)

    # planningButton Button
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

    # Lock Button to ask WPI to lock robot
    self.askLockButton = qt.QPushButton("LOCK")
    self.askLockButton.toolTip = "Send the command to ask the operator to lock the WPI robot."
    self.askLockButton.enabled = True
    self.askLockButton.setMaximumWidth(150)
    outboundFormLayout.addRow(self.askLockButton)
    self.askLockButton.connect('clicked()', self.onLockButtonClicked)

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
    outboundTransformCollapsibleButton.text = "Outbound transforms (WPI -> Slicer)"
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

    # Receive Button to show last message received
    
    self.ReceiveButton = qt.QPushButton("Receive")   
    self.ReceiveButton.toolTip = "Print last message received"
    self.ReceiveButton.enabled = True
    self.ReceiveButton.setMaximumWidth(150)
    inboundFormLayout.addRow(self.ReceiveButton)
    self.ReceiveButton.connect('clicked()', self.onReceiveButtonClicked)

    self.messageTextbox = qt.QLineEdit("No message received")
    self.messageTextbox.setReadOnly(True)
    self.messageTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Message received:", self.messageTextbox)

    self.statusTextbox = qt.QLineEdit("No status received")
    self.statusTextbox.setReadOnly(True)
    self.statusTextbox.setFixedWidth(200)
    inboundFormLayout.addRow("Status received (Code:Subcode:Error name:Message):", self.statusTextbox)
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
    Monserver = self.openIGTNode.GetServerHostname()
    print("Server name is: ", Monserver)
    self.openIGTNode.Start()
    print("openIGTNode: ", self.openIGTNode)
    self.IGTActive = True
    #print("Mon text: ", self.IGTActive)
    #if (self.IGTActive.GetAttribute(openIGTNode) == False):
     #   print("Could not make Server port active")

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

  def onCalibrationButtonClicked(self):
    # Send stringMessage containing the command "CALIBRATION" to the script via IGTLink
    print("Sending calibration command to WPI robot")
    calibrationNode = slicer.vtkMRMLTextNode()
    calibrationNode.SetText("CALIBRATION")
    slicer.mrmlScene.AddNode(calibrationNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(calibrationNode)
    self.openIGTNode.PushNode(calibrationNode)
    last_string_sent = calibrationNode.GetText() 


  def onPlanningButtonClicked(self):
    # Send stringMessage containing the command "PLANNING" to the script via IGTLink
    print("Sending planning command to WPI robot")
    planningNode = slicer.vtkMRMLTextNode()
    planningNode.SetText("PLANNING")
    slicer.mrmlScene.AddNode(planningNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(planningNode)
    self.openIGTNode.PushNode(planningNode)
    last_string_sent = planningNode.GetText() 

  def onLockButtonClicked(self):
    print("Asking to Lock the robot")
    # Send stringMessage containing the command "LOCK" to the script via IGTLink
    lockNode = slicer.vtkMRMLTextNode()
    lockNode.SetText("LOCK")
    slicer.mrmlScene.AddNode(lockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(lockNode)
    self.openIGTNode.PushNode(lockNode)
    last_string_sent = lockNode.GetText() 

  def onStopButtonClicked(self):
    print("Sending STOP command")
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    stopNode = slicer.vtkMRMLTextNode()
    stopNode.SetText("STOP")
    slicer.mrmlScene.AddNode(stopNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(stopNode)
    self.openIGTNode.PushNode(stopNode);
    last_string_sent = stopNode.GetText() 

  def onEmergencyButtonClicked(self):
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    print("Sending Emergency command")
    emergencyNode = slicer.vtkMRMLTextNode()
    emergencyNode.SetText("EMERGENCY")
    slicer.mrmlScene.AddNode(emergencyNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(emergencyNode)
    self.openIGTNode.PushNode(emergencyNode)
    last_string_sent = emergencyNode.GetText() 
    
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

  def onStatusButtonClicked(self):
    #Send Status message
    print("Sending Status")
    statusNode = slicer.vtkMRMLIGTLStatusNode()
    statusNode.SetStatusString("STATUS_OK")
    slicer.mrmlScene.AddNode(statusNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(statusNode)
    self.openIGTNode.PushNode(statusNode)

  def onTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    transformMatrix = vtk.vtkMatrix4x4()
    #transformNode.GetMatrixTransformToWorld(transformMatrix)
    print("New transform was received")
    print("Position: [{0}, {1}, {2}]".format(transformMatrix.GetElement(0,3), transformMatrix.GetElement(1,3), transformMatrix.GetElement(2,3)))

  def onTransformButtonClicked(self):
    #Send Transform message
    print("Sending Transform")
    obj = vtk.vtkMatrix4x4()
    print(obj)
    transformNode = slicer.vtkMRMLLinearTransformNode()
    transformNode.SetMatrixTransformToParent(obj);
    slicer.mrmlScene.AddNode(transformNode)
    #self.openIGTNode.RegisterOutgoingMRMLNode(transformNode)
    #self.openIGTNode.PushNode(transformNode)
  
  def onTextNodeModified(textNode, unusedArg2=None, unusedArg3=None):
    print("New string was received")
    ReceivedMsg = slicer.mrmlScene.GetFirstNodeByName("BridgeDevice")
    textNode.messageTextbox.setText(ReceivedMsg.GetText())
    if(last_string_sent == ReceivedMsg.GetText()):
      print("Acknowledgment received")
    else:
      print("Waiting for aknowledgment")

  def onStatusNodeModified(statusNode, unusedArg2=None, unusedArg3=None):
    print("New Status was received")
    ReceivedMsg = slicer.mrmlScene.GetFirstNodeByName("BridgeDevice")
    s1 = str(ReceivedMsg.GetCode())
    sep = ':'
    s2 = str(ReceivedMsg.GetSubCode())
    s3 = ReceivedMsg.GetErrorName()
    s4 = ReceivedMsg.GetStatusString()
    s = s1 + sep + s2 + sep + s3 + sep + s4
    statusNode.statusTextbox.setText(s)

  #def onReceiveStrButtonClicked(self):
    #ReceivedString = slicer.mrmlScene.GetFirstNodeByName("BridgeDevice")
    #ReceivedString.AddObserver(slicer.vtkMRMLTextNode.TextModifiedEvent, self.onTextNodeModified)

    #self.messageTextbox.setText(ReceivedString.GetText())
    #end = time.time()
    #elapsed_time = (end - start)*100
    #print("Elapsed time is:", elapsed_time)
    #if (elapsed_time > 10000):
     #   print("Operation failed: too long before aknowledgement")
    #else:
     #   print("Acknowledgment received, wait for statusmsg")

  def onReceiveButtonClicked(self):
    print("Waiting for messages")
    ReceivedMsg = slicer.mrmlScene.GetFirstNodeByName("BridgeDevice")
    #ReceivedMsg = slicer.mrmlScene.GetNodesByClass("vtkMRMLIGTLStatusNode")

    ReceivedClassName = ReceivedMsg.GetClassName()
    nodetype1 = "vtkMRMLTextNode"
    nodetype2 = "vtkMRMLIGTLStatusNode"
    nodetype3 = "vtkMRMLLinearTransformNode"
    
    if( ReceivedClassName == nodetype1):
      print("It is string message")
      ReceivedMsg.AddObserver(slicer.vtkMRMLTextNode.TextModifiedEvent, self.onTextNodeModified)
      self.messageTextbox.setText(ReceivedMsg.GetText()) 
    elif(ReceivedClassName == nodetype2):
      print("It is status message")
      ReceivedMsg.AddObserver(slicer.vtkMRMLIGTLStatusNode.StatusModifiedEvent, self.onStatusNodeModified)
      s1 = str(ReceivedMsg.GetCode())
      sep = ':'
      s2 = str(ReceivedMsg.GetSubCode())
      s3 = ReceivedMsg.GetErrorName()
      s4 = ReceivedMsg.GetStatusString()
      s = s1 + sep + s2 + sep + s3 + sep + s4
      self.statusTextbox.setText(s)

    elif(ReceivedClassName == nodetype3):
      print("It is transform message")
      ReceivedTransform = slicer.mrmlScene.GetFirstNodeByName("BridgeDevice")
      transformNode1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode") #vtkMRMLLinearTransformNode
      ReceivedMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTransformNodeModified)
    else:
      print("Message type sent not supported")




    #Mavaleur = slicer.mrmlScene.GetNodeByID("vtkMRMLTextNode1")
    #self.messageTextbox.text = startupNode.GetText()
    #text = vtkMRMLTextNode2->GetText(); 
    #self.messageTextbox.text = getNode(vtkMRMLTextNode2)

    #Mavaleur = slicer.mrmlScene.GetNodeByID(vtkMRMLTextNode3)
    #slicer.vtkIGTLToMRMLLinearTransform.CreateNewNode(mrmlScene, MaTransform)
 #def observeIncomingMessages(self):
   # while(1):
    #self.openIGTNode.RegisterIncomingMRMLNode(vtkMRMLNode* node);
      # continuously observe for incoming messages
      # when the messages are received, update the GUI
      # and execute tasks accordingly
       #NodeInfoType* RegisterIncomingMRMLNode(vtkMRMLNode* node);
       # print("i'm waiting for messages")


