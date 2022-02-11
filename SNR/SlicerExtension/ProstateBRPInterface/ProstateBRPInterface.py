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
import datetime
import random
import string
import re
import csv
from sys import platform

class ProstateBRPInterface(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Bakse/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Prostate BRP Interface"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Rebecca Lisk"]
    self.parent.helpText = """
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""

class ProstateBRPInterfaceWidget(ScriptedLoadableModuleWidget):
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
    self.createServerButton.setFixedWidth(250)
    serverFormLayout.addWidget(self.createServerButton, 2, 0)
    self.createServerButton.connect('clicked()', self.onCreateServerButtonClicked)

    self.disconnectFromSocketButton = qt.QPushButton("Disconnect from socket")
    self.disconnectFromSocketButton.toolTip = "Disconnect from the socket when you finish using audio"
    self.disconnectFromSocketButton.enabled = False
    self.disconnectFromSocketButton.setFixedWidth(250)
    serverFormLayout.addWidget(self.disconnectFromSocketButton, 2, 1)
    self.disconnectFromSocketButton.connect('clicked()', self.onDisconnectFromSocketButtonClicked)

    # ----- MRI <--> Slicer connection GUI ------
    # Slicer <--> MRI collapsible button
    self.MRICommunicationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.MRICommunicationCollapsibleButton.text = "Slicer <--> MRI"
    self.MRICommunicationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.MRICommunicationCollapsibleButton)

    # Overall layout within the path collapsible button
    MRICommunicationLayout = qt.QVBoxLayout(self.MRICommunicationCollapsibleButton)

    # Outbound layout within the path collapsible button
    MRIOutboundCommunicationLayout = qt.QGridLayout()
    MRICommunicationLayout.addLayout(MRIOutboundCommunicationLayout)
    
    MRIphaseTextboxLabel = qt.QLabel('Current phase:')
    self.MRIphaseTextbox = qt.QLineEdit("")
    self.MRIphaseTextbox.setReadOnly(True)
    self.MRIphaseTextbox.setFixedWidth(250)
    self.MRIphaseTextbox.toolTip = "Show current phase: in Blue if in the phase, green if phase successfully achieved"
    MRIOutboundCommunicationLayout.addWidget(MRIphaseTextboxLabel, 0, 0)
    MRIOutboundCommunicationLayout.addWidget(self.MRIphaseTextbox, 0, 1)

    # MRI Start up button
    self.MRIstartupButton = qt.QPushButton("START UP SCANNER")
    self.MRIstartupButton.toolTip = "Send the MRI scanner startup command."
    self.MRIstartupButton.enabled = True
    self.MRIstartupButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIstartupButton, 2, 0)
    self.MRIstartupButton.connect('clicked()', self.onMRIStartupButtonClicked)

    # MRI Disconnect scanner button
    self.MRIdisconnectButton = qt.QPushButton("DISCONNECT SCANNER")
    self.MRIdisconnectButton.toolTip = "Disconnect the MRI scanner."
    self.MRIdisconnectButton.enabled = False
    self.MRIdisconnectButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIdisconnectButton, 2, 1)
    self.MRIdisconnectButton.connect('clicked()', self.onMRIDisconnectButtonClicked)

    # MRI Start scan button
    self.MRIstartScanButton = qt.QPushButton("START SCAN")
    self.MRIstartScanButton.toolTip = "Begin scanning."
    self.MRIstartScanButton.enabled = False
    self.MRIstartScanButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIstartScanButton, 3, 0)
    self.MRIstartScanButton.connect('clicked()', self.onMRIStartScanButtonClicked)

    # MRI Stop scan button
    self.MRIstopScanButton = qt.QPushButton("STOP SCAN")
    self.MRIstopScanButton.toolTip = "Stop scanning."
    self.MRIstopScanButton.enabled = False
    self.MRIstopScanButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIstopScanButton, 3, 1)
    self.MRIstopScanButton.connect('clicked()', self.onMRIStopScanButtonClicked)

    # MRI Update scan target button
    self.MRIupdateTargetButton = qt.QPushButton("UPDATE SCAN TARGET")
    self.MRIupdateTargetButton.toolTip = "Open command pane to select a new scanning target."
    self.MRIupdateTargetButton.enabled = False
    self.MRIupdateTargetButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIupdateTargetButton, 4, 0)
    self.MRIupdateTargetButton.connect('clicked()', self.onMRIUpdateTargetButtonClicked)

    # MRI Get current scan target button
    self.MRIgetTargetButton = qt.QPushButton("GET CURRENT SCAN TARGET")
    self.MRIgetTargetButton.toolTip = "Request current MRI scanning target."
    self.MRIgetTargetButton.enabled = False
    self.MRIgetTargetButton.setMaximumWidth(250)
    MRIOutboundCommunicationLayout.addWidget(self.MRIgetTargetButton, 4, 1)
    self.MRIgetTargetButton.connect('clicked()', self.onMRIGetTargetButtonClicked)

    # Inbound layout within the path collapsible button
    MRIInboundCommunicationLayout = qt.QGridLayout()
    MRICommunicationLayout.addLayout(MRIInboundCommunicationLayout)

    # Add 1 line of spacing
    MRIInboundCommunicationLayout.addWidget(qt.QLabel(" "), 0, 0)

    self.MRImessageTextbox = qt.QLineEdit("No message received")
    self.MRImessageTextbox.setReadOnly(True)
    self.MRImessageTextbox.setFixedWidth(200)
    MRImessageTextboxLabel = qt.QLabel("   Message received:")
    MRIInboundCommunicationLayout.addWidget(MRImessageTextboxLabel, 1, 0)
    MRIInboundCommunicationLayout.addWidget(self.MRImessageTextbox, 1, 1)

    self.MRIstatusCodeTextbox = qt.QLineEdit("No status code received")
    self.MRIstatusCodeTextbox.setReadOnly(True)
    self.MRIstatusCodeTextbox.setFixedWidth(200)
    MRIstatusCodeTextboxLabel = qt.QLabel("   Status received:")
    MRIInboundCommunicationLayout.addWidget(MRIstatusCodeTextboxLabel, 2, 0)
    MRIInboundCommunicationLayout.addWidget(self.MRIstatusCodeTextbox, 2, 1)

    row = 4
    column = 4
    self.MRItableWidget = qt.QTableWidget(row, column)
    #self.MRItableWidget.setMaximumWidth(400)
    self.MRItableWidget.setMinimumHeight(95)
    self.MRItableWidget.verticalHeader().hide() # Remove line numbers
    self.MRItableWidget.horizontalHeader().hide() # Remove column numbers
    self.MRItableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.MRItableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)

    verticalheader = self.MRItableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    MRItableWidgetLabel = qt.QLabel("   Transform received:")
    MRIInboundCommunicationLayout.addWidget(MRItableWidgetLabel, 3, 0)
    MRIInboundCommunicationLayout.addWidget(self.MRItableWidget, 3, 1)

    # -------- Slicer <--> WPI connection GUI ---------

    # Slicer <--> MRI collapsible button
    self.RobotCommunicationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.RobotCommunicationCollapsibleButton.text = "Slicer <--> Robot"
    self.RobotCommunicationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.RobotCommunicationCollapsibleButton)

    # Overall layout within the path collapsible button
    RobotCommunicationLayout = qt.QVBoxLayout(self.RobotCommunicationCollapsibleButton)

    # Outbound layout within the path collapsible button
    RobotOutboundCommunicationLayout = qt.QGridLayout()
    RobotCommunicationLayout.addLayout(RobotOutboundCommunicationLayout)

    nameLabelphase = qt.QLabel('Current phase:')
    self.phaseTextbox = qt.QLineEdit("")
    self.phaseTextbox.setReadOnly(True)
    self.phaseTextbox.setFixedWidth(250)
    self.phaseTextbox.toolTip = "Show current phase: in Blue if in the phase, green if phase successfully achieved"
    RobotOutboundCommunicationLayout.addWidget(nameLabelphase, 0, 0)
    RobotOutboundCommunicationLayout.addWidget(self.phaseTextbox, 0, 1)

    # startupButton Button
    self.startupButton = qt.QPushButton("START UP")
    self.startupButton.toolTip = "Send the startup command to the WPI robot."
    self.startupButton.enabled = True
    self.startupButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.startupButton, 2, 0)
    self.startupButton.connect('clicked()', self.onStartupButtonClicked)

    # calibrationButton Button
    self.calibrationButton = qt.QPushButton("CALIBRATION")
    self.calibrationButton.toolTip = "Send the calibration command to the WPI robot."
    self.calibrationButton.enabled = False
    self.calibrationButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.calibrationButton, 3, 0)
    self.calibrationButton.connect('clicked()', self.onCalibrationButtonClicked)

    # planningButton Button # TODO Check protocol: should it print sucess after CURRENT_STATUS is sent?
    self.planningButton = qt.QPushButton("PLANNING")
    self.planningButton.toolTip = "Send the planning command to the WPI robot."
    self.planningButton.enabled = False
    self.planningButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.planningButton, 3, 1)
    self.planningButton.connect('clicked()', self.onPlanningButtonClicked)

    # targetingButton Button
    self.targetingButton = qt.QPushButton("TARGETING")
    self.targetingButton.toolTip = "Send the targeting command to the WPI robot."
    self.targetingButton.enabled = False
    self.targetingButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.targetingButton, 4 , 0)
    self.targetingButton.connect('clicked()', self.onTargetingButtonClicked)

    # moveButton Button
    self.moveButton = qt.QPushButton("MOVE")
    self.moveButton.toolTip = "Send the move to target command to the WPI robot."
    self.moveButton.enabled = False
    self.moveButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.moveButton, 4, 1)
    self.moveButton.connect('clicked()', self.onMoveButtonClicked)

    # Lock Button to ask WPI to lock robot
    self.LockButton = qt.QPushButton("LOCK")
    self.LockButton.toolTip = "Send the command to ask the operator to lock the WPI robot."
    self.LockButton.enabled = False
    self.LockButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.LockButton, 5, 0)
    self.LockButton.connect('clicked()', self.onLockButtonClicked)

    # Unlock Button to ask WPI to unlock robot
    self.UnlockButton = qt.QPushButton("UNLOCK")
    self.UnlockButton.toolTip = "Send the command to ask the operator to unlock the WPI robot."
    self.UnlockButton.enabled = False
    self.UnlockButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.UnlockButton, 5, 1)
    self.UnlockButton.connect('clicked()', self.onUnlockButtonClicked)

    # Get robot pose Button to ask WPI to send the current robot position
    self.GetPoseButton = qt.QPushButton("GET POSE")
    self.GetPoseButton.toolTip = "Send the command to ask WPI to send the current robot position."
    self.GetPoseButton.enabled = False
    self.GetPoseButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.GetPoseButton, 6, 0)
    self.GetPoseButton.connect('clicked()', self.onGetPoseButtonClicked)

    # Get robot status Button to ask WPI to send the current status position
    self.GetStatusButton = qt.QPushButton("GET STATUS")
    self.GetStatusButton.toolTip = "Send the command to ask WPI to send the current robot status."
    self.GetStatusButton.enabled = False
    self.GetStatusButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.GetStatusButton, 6, 1)
    self.GetStatusButton.connect('clicked()', self.onGetStatusButtonClicked)

    # STOP Button 
    self.StopButton = qt.QPushButton("STOP")
    self.StopButton.toolTip = "Send the command to ask the operator to stop the WPI robot."
    self.StopButton.enabled = False
    self.StopButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.StopButton, 7, 0)
    self.StopButton.connect('clicked()', self.onStopButtonClicked)

    # EMERGENCY Button 
    self.EmergencyButton = qt.QPushButton("EMERGENCY")
    self.EmergencyButton.toolTip = "Send emergency command to WPI robot."
    self.EmergencyButton.enabled = False
    self.EmergencyButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.EmergencyButton, 7, 1)
    self.EmergencyButton.connect('clicked()', self.onEmergencyButtonClicked)

    # Inbound layout within the path collapsible button
    RobotInboundCommunicationLayout = qt.QGridLayout()
    RobotCommunicationLayout.addLayout(RobotInboundCommunicationLayout)
   
    # Add 1 line of spacing
    RobotInboundCommunicationLayout.addWidget(qt.QLabel(" "), 0, 0)

    self.robotMessageTextbox = qt.QLineEdit("No message received")
    self.robotMessageTextbox.setReadOnly(True)
    self.robotMessageTextbox.setFixedWidth(200)
    robotMessageTextboxLabel = qt.QLabel("   Message received:")
    RobotInboundCommunicationLayout.addWidget(robotMessageTextboxLabel, 1, 0)
    RobotInboundCommunicationLayout.addWidget(self.robotMessageTextbox, 1, 1)

    self.robotStatusCodeTextbox = qt.QLineEdit("No status code received")
    self.robotStatusCodeTextbox.setReadOnly(True)
    self.robotStatusCodeTextbox.setFixedWidth(200)
    robotStatusCodeTextboxLabel = qt.QLabel("   Status received:")
    RobotInboundCommunicationLayout.addWidget(robotStatusCodeTextboxLabel, 2, 0)
    RobotInboundCommunicationLayout.addWidget(self.robotStatusCodeTextbox, 2, 1)

    row = 4
    column = 4
    self.robotTableWidget = qt.QTableWidget(row, column)
    #self.robotTableWidget.setMaximumWidth(400)
    self.robotTableWidget.setMinimumHeight(95)
    self.robotTableWidget.verticalHeader().hide() # Remove line numbers
    self.robotTableWidget.horizontalHeader().hide() # Remove column numbers
    self.robotTableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.robotTableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)

    verticalheader = self.robotTableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    robotTableWidgetLabel = qt.QLabel("   Transform received:")
    RobotInboundCommunicationLayout.addWidget(robotTableWidgetLabel, 3, 0)
    RobotInboundCommunicationLayout.addWidget(self.robotTableWidget, 3, 1)

    # # Visibility icon
    # self.VisibleButton = qt.QPushButton()
    # eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png");
    # self.VisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
    # self.VisibleButton.setFixedWidth(25)
    # self.VisibleButton.setCheckable(True)
    # RobotInboundCommunicationLayout.addWidget(self.VisibleButton, 4, 1)
    # self.VisibleButton.connect('clicked()', self.onVisibleButtonClicked)

    # -------  Calibration GUI ---------

    # Outbound tranform collapsible button
    self.outboundTransformCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outboundTransformCollapsibleButton.text = "Calibration"
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
    outboundTransformsFormLayout.addRow('   ZFrame image:', self.zFrameVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.zFrameVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # # Start and end slices for calibration step
    # self.startSliceSliderWidget = qt.QSpinBox()
    # self.endSliceSliderWidget = qt.QSpinBox()
    # self.startSliceSliderWidget.setValue(5)
    # self.endSliceSliderWidget.setValue(16)
    # self.startSliceSliderWidget.setMaximumWidth(40)
    # self.endSliceSliderWidget.setMaximumWidth(40)
    # outboundTransformsFormLayout.addRow('Minimum slice:', self.startSliceSliderWidget)
    # outboundTransformsFormLayout.addRow('Maximum slice:', self.endSliceSliderWidget)

    # Calibration matrix display
    row = 4
    column = 4
    self.calibrationTableWidget = qt.QTableWidget(row, column)
    self.calibrationTableWidget.setMinimumHeight(95)
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
    outboundTransformsFormLayout.addRow("   Calibration matrix: ", self.calibrationTableWidget)

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

    # # TO SELECT AN EXISTING CALIBRATION MATRIX CALUCLATED BY HARMONUS (outside of the module):
    # # Delete once Calibration step is testing and working
    # self.calibrationMatrixSelector = slicer.qMRMLNodeComboBox()
    # self.calibrationMatrixSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    # self.calibrationMatrixSelector.selectNodeUponCreation = True
    # self.calibrationMatrixSelector.addEnabled = False
    # self.calibrationMatrixSelector.removeEnabled = False
    # self.calibrationMatrixSelector.noneEnabled = False
    # self.calibrationMatrixSelector.showHidden = False
    # self.calibrationMatrixSelector.showChildNodeTypes = False
    # self.calibrationMatrixSelector.setMRMLScene( slicer.mrmlScene )
    # self.calibrationMatrixSelector.setToolTip( "Select the calibration matrix." )
    # outboundTransformsFormLayout.addRow("   Calibration matrix:  ", self.calibrationMatrixSelector)

    # # Send pre-calculated calibration matrix button
    # self.sendCalibrationMatrixButton = qt.QPushButton("Send pre-existing calibration matrix")
    # self.sendCalibrationMatrixButton.enabled = True
    # # self.createCalibrationMatrixButton.setMaximumWidth(250)
    # outboundTransformsFormLayout.addWidget(self.sendCalibrationMatrixButton)
    # self.sendCalibrationMatrixButton.connect('clicked()', self.onSendCalibrationMatrixButtonClicked)

    # Planning phase collapsible button
    self.planningCollapsibleButton = ctk.ctkCollapsibleButton()
    self.planningCollapsibleButton.text = "Planning"
    self.planningCollapsibleButton.collapsed = True
    self.layout.addWidget(self.planningCollapsibleButton)

    # Overall layout within the planning collapsible button
    # planningLayout = qt.QGridLayout(self.planningCollapsibleButton)
    planningLayout = qt.QVBoxLayout(self.planningCollapsibleButton)

    # Top layout within the planning collapsible button
    # planningLayoutTop = qt.QGridLayout()
    planningLayoutTop = qt.QFormLayout()
    planningLayout.addLayout(planningLayoutTop)

    self.targetPointNodeSelector = slicer.qSlicerSimpleMarkupsWidget()
    self.targetPointNodeSelector.objectName = 'targetPointNodeSelector'
    self.targetPointNodeSelector.toolTip = "Select a fiducial to use as the needle insertion target point."
    self.targetPointNodeSelector.setNodeBaseName("TARGET_POINT")
    self.targetPointNodeSelector.defaultNodeColor = qt.QColor(170,0,0)
    self.targetPointNodeSelector.tableWidget().hide()
    self.targetPointNodeSelector.markupsSelectorComboBox().noneEnabled = False
    self.targetPointNodeSelector.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup
    # targetPointSelectorLabel = qt.QLabel("   Target point: ")
    # planningLayoutTop.addWidget(targetPointSelectorLabel, 0, 0)
    # planningLayoutTop.addWidget(self.targetPointNodeSelector, 0, 1, 1, 3)
    planningLayoutTop.addRow("   Target point: ", self.targetPointNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.targetPointNodeSelector, 'setMRMLScene(vtkMRMLScene*)')
    self.targetPointNodeSelector.connect('updateFinished()', self.onTargetPointFiducialChanged)

    # Transform matrix display table
    row = 4
    column = 4
    self.targetTableWidget = qt.QTableWidget(row, column)
    # self.targetTableWidget.setMaximumWidth(400)
    self.targetTableWidget.setMinimumHeight(95)
    self.targetTableWidget.verticalHeader().hide() # Remove line numbers
    self.targetTableWidget.horizontalHeader().hide() # Remove column numbers
    self.targetTableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.targetTableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)

    verticalheader = self.targetTableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    # targetTableWidgetLabel = qt.QLabel("   Target transform:  ")
    # planningLayoutTop.addWidget(targetTableWidgetLabel, 2, 0)
    # planningLayoutTop.addWidget(self.targetTableWidget, 2, 1, 1, 3)
    planningLayoutTop.addRow("   Target transform:   ", self.targetTableWidget)

    # Visibility icon
    self.targetNeedleVisibleButton = qt.QPushButton()
    eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png")
    self.targetNeedleVisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
    self.targetNeedleVisibleButton.setFixedWidth(25)
    self.targetNeedleVisibleButton.setCheckable(True)
    # planningLayoutTop.addWidget(self.targetNeedleVisibleButton, 3, 1)
    planningLayoutTop.addRow(" ", self.targetNeedleVisibleButton)
    self.targetNeedleVisibleButton.connect('clicked()', self.onPlannedTargetNeedleVisibleButtonClicked)
    
    # Translation sliders
    self.translationSliderWidget = slicer.qMRMLTransformSliders()
    self.translationSliderWidget.Title = 'Translation'
    self.translationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.TRANSLATION
    self.translationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL
    self.translationSliderWidget.setMRMLScene(slicer.mrmlScene)
    self.translationSliderWidget.minMaxVisible = False
    # planningLayoutTop.addWidget(self.translationSliderWidget, 4, 0, 1, 4)
    planningLayoutTop.addRow(self.translationSliderWidget)    

    # LR and PA rotation sliders
    self.orientationSliderWidget = slicer.qMRMLTransformSliders()
    self.orientationSliderWidget.Title = 'Rotation'
    self.orientationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.ROTATION
    self.orientationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL
    self.orientationSliderWidget.setMRMLScene(slicer.mrmlScene)
    self.orientationSliderWidget.minMaxVisible = False
    # planningLayoutTop.addWidget(self.orientationSliderWidget, 5, 0, 1, 4)
    planningLayoutTop.addRow(self.orientationSliderWidget)    

    # Bottom layout within the planning collapsible button 
    # (includes the reference frame toggle button and the reset button)
    #planningLayoutBottom = qt.QGridLayout()
    planningLayoutBottom = qt.QHBoxLayout()
    planningLayout.addLayout(planningLayoutBottom)

    # Button to toggle translation in local reference frame
    self.referenceFrameToggleButton = qt.QPushButton()
    globalReferenceIcon = qt.QIcon(":Icons/RotateFirst.png")
    self.referenceFrameToggleButton.setIcon(globalReferenceIcon)
    self.referenceFrameToggleButton.setMaximumWidth(50)
    self.referenceFrameToggleButton.setMaximumHeight(25)
    self.referenceFrameToggleButton.toolTip = "Translation in global or local (rotated) reference frame"
    self.referenceFrameToggleButton.setCheckable(True)
    planningLayoutBottom.addWidget(self.referenceFrameToggleButton, 0, 0)
    self.referenceFrameToggleButton.connect('clicked()', self.onTargetReferenceFrameButtonToggled)

    # Button to reset needle to original target point & upright position
    self.resetNeedlePositionButton = qt.QPushButton("Reset")
    self.resetNeedlePositionButton.enabled = True
    self.resetNeedlePositionButton.toolTip = "Reset the needle model back to the target fiducial"
    self.resetNeedlePositionButton.setMaximumWidth(50)
    self.resetNeedlePositionButton.setMaximumHeight(25)
    planningLayoutBottom.addWidget(self.resetNeedlePositionButton, 0, 1)
    self.resetNeedlePositionButton.connect('clicked()', self.onTargetPointFiducialChanged)

    # Add spacer to left align the reference frame toggle button and reset button
    spacer = qt.QSpacerItem(150, 10, qt.QSizePolicy.Expanding)
    planningLayoutBottom.addSpacerItem(spacer)

    # Needle view panel collapsible button
    self.modelViewPanelCollapsibleButton = ctk.ctkCollapsibleButton()
    self.modelViewPanelCollapsibleButton.text = "Model View Panel"
    self.modelViewPanelCollapsibleButton.collapsed = True
    self.layout.addWidget(self.modelViewPanelCollapsibleButton)

    # Layout within the needle view panel collapsible button
    modelViewPanelLayout = qt.QGridLayout(self.modelViewPanelCollapsibleButton)

    # Model view panel GUI and functionality
      # Planned target transform (PointerModel = plannedTarget)    
      # Reachable target transform (PointerModel = reachableTarget)
      # Current location transform (PointerModel = currentLocation)
    self.treeView = slicer.qMRMLSubjectHierarchyTreeView()
    self.treeView.nodeTypes = ["vtkMRMLModelNode"]
    # self.treeView.setMRMLScene(slicer.mrmlScene)
    # if just needle models are desired in the model view panel -- use setNameFilter()
    modelViewPanelLayout.addWidget(self.treeView, 0, 0)

    # Info messages collapsible button
    self.infoCollapsibleButton = ctk.ctkCollapsibleButton()
    self.infoCollapsibleButton.text = "Command Log"
    self.infoCollapsibleButton.collapsed = True
    self.layout.addWidget(self.infoCollapsibleButton)

    # Layout within the path collapsible button
    infoFormLayout = qt.QFormLayout(self.infoCollapsibleButton)

    self.infoTextbox = qt.QTextEdit("")
    self.infoTextbox.setReadOnly(True)
    self.infoTextbox.setFixedHeight(180)
    #self.infoTextbox.setAlignment(Qt.AlignTop)
    infoFormLayout.addRow("", self.infoTextbox)

    # Add vertical spacer
    self.layout.addStretch(1)

    self.textNode = slicer.vtkMRMLTextNode()
    self.textNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(self.textNode)
    self.firstServer = True # Set to false the first time CreateServerButton is clicked so that nodes are not re-created

    # Empty nodes for planning and calibration steps
    self.zFrameROI = None
    self.zFrameROIAddedObserverTag = None
    self.outputTransform = None
    self.plannedTargetTransform = None
    self.reachableTargetTransform = None
    self.currentPositionTransform = None
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
    self.RobotCommunicationCollapsibleButton.collapsed = False
    # self.MRICommunicationCollapsibleButton.collapsed = False
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

    # Create a .txt document for the command log
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    self.commandLogFilePath = os.path.join(currentFilePath, "commandLogs.txt")
    with open(self.commandLogFilePath,"a") as f:
      f.write('\n----------------- New session started on ' + datetime.datetime.now().strftime("%d/%m/%Y at %H:%M:%S:%f") + ' -----------------\n')

    # Make a node for each message type 
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

    # Initialize variables 
    self.last_string_sent = "nostring"
    self.start = 0
    self.ack = 0
    self.last_prefix_sent = ""
    self.to_compare = 0
    self.last_randomIDname_transform = "SendTransform"
    self.loading_phase = 'STATUS_OK'

  def onDisconnectFromSocketButtonClicked(self):
    # GUI changes to enable/disable button functionality
    self.disconnectFromSocketButton.enabled = False
    self.createServerButton.enabled = True
    self.snrPortTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setReadOnly(False)
    self.RobotCommunicationCollapsibleButton.collapsed = True
    self.MRICommunicationCollapsibleButton.collapsed = True
    self.infoCollapsibleButton.collapsed = True
    self.outboundTransformCollapsibleButton.collapsed = True
    #self.outboundTargetCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True
    #self.outboundEntryCollapsibleButton.collapsed = True

    # Close socket
    self.openIGTNode.Stop()
    self.snrPortTextboxLabel.setStyleSheet('color: black')
    self.snrHostnameTextboxLabel.setStyleSheet('color: black')
    self.snrPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")
    self.snrHostnameTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")

    # Clear textboxes
    self.MRIphaseTextbox.setText("")
    self.MRImessageTextbox.setText("No message received")
    self.MRIstatusCodeTextbox.setText("No status code received")
    self.robotMessageTextbox.setText("No message received")
    self.robotStatusCodeTextbox.setText("No status code received")
    self.phaseTextbox.setText("")
    self.infoTextbox.setText("")
   
    # Clear tables
    for i in range(4):
      for j in range(4):
        self.calibrationTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
        self.robotTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
        self.MRItableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
        self.targetTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
   
    # Delete all nodes from the scene
    slicer.mrmlScene.RemoveNode(self.openIGTNode)
    slicer.mrmlScene.Clear(0) 

  def generateTimestampNameID(self, last_prefix_sent):
    timestampID = [last_prefix_sent, "_"]
    currentTime = datetime.datetime.now()
    timestampID.append(currentTime.strftime("%H%M%S%f"))
    timestampIDname = ''.join(timestampID)
    return timestampIDname

  # Command logging
  def appendSentMessageToCommandLog(self, timestampIDname, infoMsg):
    if timestampIDname.split("_")[0] == "TARGET":
      tempTimestamp  = datetime.datetime.strptime(timestampIDname.split("_")[2], "%H%M%S%f")
    else: 
      tempTimestamp = datetime.datetime.strptime(timestampIDname.split("_")[1], "%H%M%S%f")
    timestamp = tempTimestamp.strftime("%H:%M:%S:%f")
    # Append to commandLogs.txt
    with open(self.commandLogFilePath,"a") as f:
      f.write(timestamp + " -- " + infoMsg + '\n')

    # Append to Slicer module GUI command logging box
    currentInfoText = self.infoTextbox.toPlainText()
    self.infoTextbox.setText(currentInfoText + '\n' + timestamp + " -- " + infoMsg + '\n')

  def appendReceivedMessageToCommandLog(self, last_string_sent, elapsed_time):
    currentInfoText = self.infoTextbox.toPlainText()
    with open(self.commandLogFilePath,"a") as f:
      if last_string_sent.split("_")[0] == "ACK": # NO- CHANGE
        f.write("   -- Acknowledgment received for command: " + last_string_sent + " after " + elapsed_time +  "ms\n")
        self.infoTextbox.setText(currentInfoText + "\n   -- Acknowledgment received for command: " + last_string_sent + " after " + elapsed_time +  "ms\n")
      elif last_string_sent.split(' ')[0] == "Received" or last_string_sent.split(' ')[0] == "TRANSFORM":
        f.write("   -- " + last_string_sent + '\n')
        self.infoTextbox.setText(currentInfoText + "\n   -- " + last_string_sent + "\n")
      else:
        # TODO
        f.write("A message other than an acknowledgement or a status was received. Modify appendReceivedMessageToCommandLog function for last_string_sent: " + last_string_sent + "\n")

  def appendTransformToCommandLog(self, outputMatrix):
    with open(self.commandLogFilePath,"a") as f:
      f.write ("[" + str(round(outputMatrix.GetElement(0,0),2)) + ", " + str(round(outputMatrix.GetElement(0,1),2)) + ", " + str(round(outputMatrix.GetElement(0,2),2)) + ", " + str(round(outputMatrix.GetElement(0,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(1,0),2)) + ", " + str(round(outputMatrix.GetElement(1,1),2)) + ", " + str(round(outputMatrix.GetElement(1,2),2)) + ", " + str(round(outputMatrix.GetElement(1,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(2,0),2)) + ", " + str(round(outputMatrix.GetElement(2,1),2)) + ", " + str(round(outputMatrix.GetElement(2,2),2)) + ", " + str(round(outputMatrix.GetElement(2,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(3,0),2)) + ", " + str(round(outputMatrix.GetElement(3,1),2)) + ", " + str(round(outputMatrix.GetElement(3,2),2)) + ", " + str(round(outputMatrix.GetElement(3,3),2)) + "]\n")

    # Append to Slicer module GUI command logging box
    currentInfoText = self.infoTextbox.toPlainText()
    self.infoTextbox.setText(currentInfoText + "\n[" + str(round(outputMatrix.GetElement(0,0),2)) + ", " + str(round(outputMatrix.GetElement(0,1),2)) + ", " + str(round(outputMatrix.GetElement(0,2),2)) + ", " + str(round(outputMatrix.GetElement(0,3),2)) + "]\n[" 
                                 + str(round(outputMatrix.GetElement(1,0),2)) + ", " + str(round(outputMatrix.GetElement(1,1),2)) + ", " + str(round(outputMatrix.GetElement(1,2),2)) + ", " + str(round(outputMatrix.GetElement(1,3),2)) + "]\n["
                                 + str(round(outputMatrix.GetElement(2,0),2)) + ", " + str(round(outputMatrix.GetElement(2,1),2)) + ", " + str(round(outputMatrix.GetElement(2,2),2)) + ", " + str(round(outputMatrix.GetElement(2,3),2)) + "]\n["
                                 + str(round(outputMatrix.GetElement(3,0),2)) + ", " + str(round(outputMatrix.GetElement(3,1),2)) + ", " + str(round(outputMatrix.GetElement(3,2),2)) + ", " + str(round(outputMatrix.GetElement(3,3),2)) + "]\n")

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
   
  def onGetStatusButtonClicked(self):
    # Send stringMessage containing the command "GET STATUS" to the script via IGTLink
    print("Send command to get current status of the robot")
    getstatusNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)  
    self.last_name_sent = timestampIDname
    getstatusNode.SetName(timestampIDname)
    getstatusNode.SetText("GET_STATUS")
    getstatusNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(getstatusNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getstatusNode)
    self.openIGTNode.PushNode(getstatusNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  GET_STATUS )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onGetPoseButtonClicked(self):
    # Send stringMessage containing the command "GET POSE" to the script via IGTLink
    print("Send command to get current position of the robot")
    getposeNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    getposeNode.SetName(timestampIDname)
    getposeNode.SetText("GET_POSE")
    getposeNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(getposeNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getposeNode)
    self.openIGTNode.PushNode(getposeNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  GET_POSE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onTargetingButtonClicked(self):
    # Send stringMessage containing the command "TARGETING" to the script via IGTLink
    targetingNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    targetingNode.SetName(timestampIDname)
    targetingNode.SetText("TARGETING")
    targetingNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(targetingNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(targetingNode)
    self.openIGTNode.PushNode(targetingNode)
    self.start = time.time()
    self.last_string_sent = targetingNode.GetText()
    self.last_prefix_sent = "TGT"
    infoMsg =  "Sending STRING( " + timestampIDname + ",  TARGETING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

    # Show Target point GUI in the module
    self.outboundTransformCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True

  def onMoveButtonClicked(self):
    # Send stringMessage containing the command "MOVE" to the script via IGTLink
    print("Send command to ask robot to move to target")
    moveNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    moveNode.SetName(timestampIDname)
    moveNode.SetText("MOVE_TO_TARGET")
    moveNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(moveNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(moveNode)
    self.openIGTNode.PushNode(moveNode)
    self.start = time.time()
    self.last_string_sent = moveNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  MOVE_TO_TARGET )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

    # TODO - DELETE THIS LINE - FOR DEBUGGING ONLY 
    # (function call to getRobotPoseUntilTargetIsReached should be executed once the MOVE_TO_TARGET acknowledgement is received)
    # self.getRobotPoseUntilTargetIsReached()

    # Hide Calibration, Planning, and Targetting GUIs
    # self.outboundEntryCollapsibleButton.collapsed = True
    # self.outboundTargetCollapsibleButton.collapsed = True
    self.outboundTransformCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True
  
  def onCalibrationButtonClicked(self):
    # Send stringMessage containing the command "CALIBRATION" to the script via IGTLink
    print("Sending calibration command to WPI robot")
    calibrationNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    calibrationNode.SetName(timestampIDname)
    calibrationNode.SetText("CALIBRATION")
    calibrationNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(calibrationNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(calibrationNode)
    self.openIGTNode.PushNode(calibrationNode)
    self.start = time.time()
    self.last_string_sent = calibrationNode.GetText()
    self.last_prefix_sent = "CLB"
    infoMsg =  "Sending STRING( " + timestampIDname + ",  CALIBRATION )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

    # Show Calibration matrix GUI in the module
    # self.outboundEntryCollapsibleButton.collapsed = True
    # self.outboundTargetCollapsibleButton.collapsed = True
    self.outboundTransformCollapsibleButton.collapsed = False

  def onPlanningButtonClicked(self):
    # Send stringMessage containing the command "PLANNING" to the script via IGTLink
    print("Sending planning command to WPI robot")
    planningNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    planningNode.SetName(timestampIDname)
    planningNode.SetText("PLANNING")
    planningNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(planningNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(planningNode)
    self.openIGTNode.PushNode(planningNode)
    self.start = time.time()
    self.last_string_sent = planningNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  PLANNING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

    # Show planning GUI, hide calibration GUI and target point GUI
    self.planningCollapsibleButton.collapsed = False
    # self.outboundTargetCollapsibleButton.collapsed = True
    self.outboundTransformCollapsibleButton.collapsed = True

  def onUnlockButtonClicked(self):
    print("Asking to Unlock the robot")
    # Send stringMessage containing the command "UNLOCK" to the script via IGTLink
    unlockNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    unlockNode.SetName(timestampIDname)
    unlockNode.SetText("UNLOCK")
    unlockNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(unlockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(unlockNode)
    self.openIGTNode.PushNode(unlockNode)
    self.start = time.time()
    self.last_string_sent = unlockNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  UNLOCK )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onLockButtonClicked(self):
    print("Asking to Lock the robot")
    # Send stringMessage containing the command "LOCK" to the script via IGTLink
    lockNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    lockNode.SetName(timestampIDname)
    lockNode.SetText("LOCK")
    lockNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(lockNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(lockNode)
    self.openIGTNode.PushNode(lockNode)
    self.start = time.time()
    self.last_string_sent = lockNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  LOCK )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onStopButtonClicked(self):
    print("Sending Stop command")
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    stopNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    stopNode.SetName(timestampIDname)
    stopNode.SetText("STOP")
    stopNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(stopNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(stopNode)
    self.openIGTNode.PushNode(stopNode);
    self.start = time.time()
    self.last_string_sent = stopNode.GetText()
    self.deactivateButtons()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  STOP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onEmergencyButtonClicked(self):
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    print("Sending Emergency command")
    emergencyNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    emergencyNode.SetName(timestampIDname)
    emergencyNode.SetText("EMERGENCY")
    emergencyNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(emergencyNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(emergencyNode)
    self.openIGTNode.PushNode(emergencyNode)
    self.start = time.time()
    self.last_string_sent = emergencyNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  EMERGENCY )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  def onStartupButtonClicked(self):
    # Send stringMessage containing the command "START_UP" to the script via IGTLink
    print("Sending Start up command")
    startupNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = timestampIDname
    startupNode.SetName(timestampIDname)
    startupNode.SetText("START_UP")
    startupNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(startupNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(startupNode)
    self.openIGTNode.PushNode(startupNode)
    self.start = time.time()
    self.last_string_sent = startupNode.GetText()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  START_UP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

  # def onVisibleButtonClicked(self):
  #   # If button is checked
  #   if (self.VisibleButton.isChecked()):
  #     eyeIconVisible = qt.QPixmap(":/Icons/Small/SlicerVisible.png")
  #     self.VisibleButton.setIcon(qt.QIcon(eyeIconVisible))
  #     self.AddPointerModel("PointerNode")
  #     TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
  #     locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("PointerNode")
  #     locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())
  #   # If it is unchecked
  #   else:
  #     eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png")
  #     self.VisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
  #     PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PointerNode")
  #     slicer.mrmlScene.RemoveNode(PointerNodeToRemove)

  def onPlannedTargetNeedleVisibleButtonClicked(self):
    # If button is checked
    if (self.targetNeedleVisibleButton.isChecked()):
      if slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedle") is not None:
        PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedle")
        slicer.mrmlScene.RemoveNode(PointerNodeToRemove)
      eyeIconVisible = qt.QPixmap(":/Icons/Small/SlicerVisible.png")
      self.targetNeedleVisibleButton.setIcon(qt.QIcon(eyeIconVisible))
      self.AddPointerModel("PlannedTargetNeedle")
      TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetTransform")
      locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedle")
      locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())
    # If it is unchecked
    else:
      eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png")
      self.targetNeedleVisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedle")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)

  def onReachableTargetTransformReceived(self):
    # Update self.reachableTargetTransform s.t. it contains the REACHABLE_TARGET message sent by WPI
    if self.reachableTargetTransform:
      slicer.mrmlScene.RemoveNode(self.reachableTargetTransform)
      self.reachableTargetTransform = None
    self.reachableTargetTransform = slicer.vtkMRMLLinearTransformNode()
    self.reachableTargetTransform.SetName("ReachableTargetTransform")
    # TODO - update reachableTargetTransform s.t. it contains the REACHABLE_TARGET message sent by WPI
    slicer.mrmlScene.AddNode(self.reachableTargetTransform)

    # Add reachable target model to Slicer GUI
    if slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle") is not None:
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)
    self.AddPointerModel("ReachableTargetNeedle")
    TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetTransform")
    locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle")
    locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())
    # TODO - determine when to call this function 

  # def onCurrentPositionTransformReceived_v2(self, currentPositionTransform):
    # TODO?

  def onCurrentPositionTransformReceived(self):
    # Update self.currentPositionTransform s.t. it contains the CURRENT_POSITION message sent by WPI
    if self.currentPositionTransform:
      slicer.mrmlScene.RemoveNode(self.currentPositionTransform)
      self.currentPositionTransform = None
    self.currentPositionTransform = slicer.vtkMRMLLinearTransformNode()
    self.currentPositionTransform.SetName("ReachableTargetTransform")
    # TODO - update currentPositionTransform s.t. it contains the CURRENT_POSITION message sent by WPI
    slicer.mrmlScene.AddNode(self.currentPositionTransform)

    # Add current position needle model to Slicer GUI
    if slicer.mrmlScene.GetFirstNodeByName("CurrentPositionNeedle") is not None:
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionNeedle")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)
    self.AddPointerModel("CurrentPositionNeedle")
    TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionTransform")
    locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionNeedle")
    locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())
    # TODO - determine when to call this function

  def onTargetReferenceFrameButtonToggled(self):
    # If button is checked
    if self.referenceFrameToggleButton.isChecked():
      globalReferenceIcon = qt.QIcon(":Icons/RotateFirst.png")
      self.referenceFrameToggleButton.setIcon(globalReferenceIcon)
      self.orientationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.GLOBAL
      self.translationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.GLOBAL
    # If it is unchecked
    else:
      globalReferenceIcon = qt.QIcon(":Icons/TranslateFirst.png")
      self.referenceFrameToggleButton.setIcon(globalReferenceIcon)
      self.orientationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL
      self.translationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL

  def onMRIStartupButtonClicked(self):
    self.MRIdisconnectButton.enabled = True
    self.MRIstartupButton.enabled = False

    self.MRIstartScanButton.enabled = True
    self.MRIstopScanButton.enabled = True
    self.MRIupdateTargetButton.enabled = True
    self.MRIgetTargetButton.enabled = True
    
  def onMRIDisconnectButtonClicked(self):
    self.MRIstartupButton.enabled = True
    self.MRIdisconnectButton.enabled = False

    self.MRIstartScanButton.enabled = False
    self.MRIstopScanButton.enabled = False
    self.MRIupdateTargetButton.enabled = False
    self.MRIgetTargetButton.enabled = False

  def onMRIStartScanButtonClicked(self):
    print("Start MRI scan.")

  def onMRIStopScanButtonClicked(self):
    print("Stop MRI scan.")

  def onMRIUpdateTargetButtonClicked(self):
    print("Update MRI scanning target.")

  def onMRIGetTargetButtonClicked(self):
    print("Request current MRI scanning target.")

  def onTextNodeModified(textNode, unusedArg2=None, unusedArg3=None):
    print("New string received")
    ReceivedStringMsg = slicer.mrmlScene.GetFirstNodeByName("StringMessage")
    end = time.time()
    elapsed_time = (end - textNode.start)*100
    concatenateMsg = ReceivedStringMsg.GetText()
    delimit = ":"
    isVis = ReceivedStringMsg.GetAttribute("IGTLVisible")
    if(concatenateMsg.find(delimit)!=-1): # found Delimiter is in the string
      nameonly = concatenateMsg[0: concatenateMsg.index(delimit)]
      msgonly = concatenateMsg[concatenateMsg.index(delimit) + 2: len(concatenateMsg)]
      textNode.robotMessageTextbox.setText(msgonly)
      delimit2 = "_"
      if(nameonly.find(delimit2)!=-1):
        nameonlyType = nameonly[0: nameonly.index(delimit2)]
        nameonlyID = nameonly[nameonly.index(delimit2) + 1: len(nameonly)]
        if(textNode.last_name_sent.find(delimit2)!=-1):
          # last_name_sentType = textNode.last_name_sent[0: textNode.last_name_sent.index(delimit2)]
          last_name_sentID = textNode.last_name_sent[textNode.last_name_sent.index(delimit2) + 1: len(textNode.last_name_sent)]
          if((last_name_sentID == nameonlyID) and (nameonlyType == 'ACK') and(textNode.last_string_sent == msgonly)):  # if(elapsed_time > 100) print("Received knowledgment too late, after", elapsed_time, "ms")
            print("Acknowledgment received for command:", textNode.last_string_sent, "after", elapsed_time, "ms")
            # textNode.appendReceivedMessageToCommandLog(textNode.last_string_sent, elapsed_time)
            textNode.ack = 1
            infoMsg =  "Received STRING from WPI: ( " + nameonly + ", " + msgonly + " )"
            textNode.appendReceivedMessageToCommandLog(infoMsg, 0)
            re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    else:
      textNode.robotMessageTextbox.setText(concatenateMsg)
      print("Received something different than expected, received: ", ReceivedStringMsg.GetText())      
      
  def onStatusNodeModified(statusNode, unusedArg2=None, unusedArg3=None):
    print("New status received")
    ReceivedStatusMsg = slicer.mrmlScene.GetFirstNodeByName("StatusMessage")
    s1 = str(ReceivedStatusMsg.GetCode())
    s2 = str(ReceivedStatusMsg.GetSubCode())
    s3 = ReceivedStatusMsg.GetErrorName()
    concatenateMsg = ReceivedStatusMsg.GetStatusString()
    if(concatenateMsg.find(":")!=-1): # found delimiter is in the string
      nameonly = concatenateMsg[0: concatenateMsg.index(":")]
      # msgonly = concatenateMsg[concatenateMsg.index(":") + 2: len(concatenateMsg)]
    else:
      # msgonly = concatenateMsg
      nameonly = concatenateMsg
    # s = s1 + ':' + s2 + ':' + s3 + ':' + msgonly
    # statusNode.statusTextbox.setText(s)

    # Status codes -- see igtl_status.h
    statusNode.status_codes = ['STATUS_INVALID', 'STATUS_OK', 'STATUS_UNKNOWN_ERROR', 'STATUS_PANICK_MODE', 'STATUS_NOT_FOUND', 'STATUS_ACCESS_DENIED', 'STATUS_BUSY', 'STATUS_TIME_OUT', 'STATUS_OVERFLOW','STATUS_CHECKSUM_ERROR','STATUS_CONFIG_ERROR','STATUS_RESOURCE_ERROR','STATUS_UNKNOWN_INSTRUCTION','STATUS_NOT_READY','STATUS_MANUAL_MODE','STATUS_DISABLED','STATUS_NOT_PRESENT','STATUS_UNKNOWN_VERSION','STATUS_HARDWARE_FAILURE','STATUS_SHUT_DOWN','STATUS_NUM_TYPES']
    statusNode.robotStatusCodeTextbox.setText(statusNode.status_codes[ReceivedStatusMsg.GetCode()])
    end = time.time()
    elapsed_time = end - statusNode.start
    infoMsg =  "Received STATUS from WPI: ( " + nameonly + ", " + statusNode.status_codes[ReceivedStatusMsg.GetCode()] + " )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    statusNode.appendReceivedMessageToCommandLog(infoMsg, elapsed_time)

    if((statusNode.status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (statusNode.ack == 1) and (nameonly == 'CURRENT_STATUS')): 
      print("Robot is in phase: ", s3, "after", elapsed_time*100, "ms")
      statusNode.phaseTextbox.setText(s3)
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 0, 255);") # Sets phase name in blue
      statusNode.loading_phase = s3
    elif((statusNode.status_codes[ReceivedStatusMsg.GetCode()] == 'STATUS_OK') and (statusNode.ack == 1) and (statusNode.loading_phase == nameonly)): 
      print("Robot sucessfully achieved : ", statusNode.loading_phase, "after", elapsed_time, "s")
      statusNode.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green
      # Activate command buttons on Start up
      if(statusNode.loading_phase == "START_UP"):
        statusNode.activateButtons()
      # Call function to send targeting transform 
      elif(statusNode.loading_phase == "TARGETING"):
        statusNode.sendTargetTransform()
      # Call function to receive pose repeatedly from robot if the current phase is MOVE_TO_TARGET
      elif(statusNode.loading_phase == "MOVE_TO_TARGET"):
        statusNode.getRobotPoseUntilTargetIsReached()
      statusNode.ack = 0
    else:
      print("Error in changing phase")
      # print("statusNode.status_codes[ReceivedStatusMsg.GetCode()]: ", statusNode.status_codes[ReceivedStatusMsg.GetCode()])
      # print("statusNode.ack: ", statusNode.ack)
      # print("statusNode.loading_phase: ", statusNode.loading_phase)
      # print("nameonly: ", nameonly)

  def onTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    print("New transform received")
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)

    refMatrix = vtk.vtkMatrix4x4()
    LastTransformNode = slicer.mrmlScene.GetFirstNodeByName(transformNode.last_randomIDname_transform)
    LastTransformNode.GetMatrixTransformToParent(refMatrix)
    nbRows = transformNode.robotTableWidget.rowCount
    nbColumns = transformNode.robotTableWidget.columnCount
    same_transforms = 1
    for i in range(nbRows):
      for j in range(nbColumns):
        val = transformMatrix.GetElement(i,j)
        val = round(val,2)
        ref = refMatrix.GetElement(i,j)
        ref = round(val,2)
        if(transformNode.to_compare == 1):
          if(val != ref):
            same_transforms = 0
        transformNode.robotTableWidget.setItem(i , j, qt.QTableWidgetItem(str(val)))
    infoMsg = ""
    if ((transformNode.to_compare == 1) and (same_transforms == 0)):
      infoMsg =  "TRANSFORM received from WPI doesn't match transform sent"
    elif((transformNode.to_compare == 1) and (same_transforms == 1)):
      infoMsg =  "TRANSFORM received from WPI matches transform sent"
    transformNode.appendReceivedMessageToCommandLog(infoMsg, 0)

  def onTransformInfoNodeModified(infoNode, unusedArg2=None, unusedArg3=None):
    print("New transform info received")
    ReceivedTransformInfo = slicer.mrmlScene.GetFirstNodeByName("TransformInfo")
    info = ReceivedTransformInfo.GetText()
    print("transform info: ", info)
    # if (info == "CURRENT_POSITION") or (info == "TARGET"):
    if info == "TARGET":
      print("Transform received")
    elif info == "REACHABLE_TARGET":
      print("TODO - REACHABLE_TARGET RECEIVED - call onReachableTargetTransformReceived")
      infoNode.onReachableTargetTransformReceived()
      # TODO
    elif info == "CURRENT_POSITION":
      print("TODO - CURRENT_POSTION RECEIVED - call onCurrentPositionTransformReceived")
      infoNode.onCurrentPositionTransformReceived()
      # TODO
    elif(info.find("_")!=-1): # Check for delimiter "_"
      infoType = info[0: info.index("_")]
      infoID = info[info.index("_") + 1: len(info)]
      if(infoNode.last_name_sent.find("_")!=-1):
        last_name_sentID = infoNode.last_name_sent[infoNode.last_name_sent.index("_") + 1: len(infoNode.last_name_sent)]
        infoMsg =  "Received TRANSFORM from WPI: ( " + info + " )"
        re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
        infoNode.appendReceivedMessageToCommandLog(infoMsg, 0)
      
        if((last_name_sentID == infoID) and (infoType == 'ACK')):
          print("Acknowledgment received for transform:", infoNode.last_name_sent)
        infoNode.to_compare = 1

  def AddPointerModel(self, pointerNodeName):   
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
    locatorModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", pointerNodeName)
    locatorModelNode.SetAndObservePolyData(node)
    locatorModelNode.CreateDefaultDisplayNodes()
    locatorModelNode.SetDisplayVisibility(True)
    # Set needle model color based on the type of needle (planned target, reachable target, or current position)
    if pointerNodeName == "PlannedTargetNeedle": 
      locatorModelNode.GetDisplayNode().SetColor(0.80,0.80,0.80) # grey
    elif pointerNodeName == "ReachableTargetNeedle":
      locatorModelNode.GetDisplayNode().SetColor(0.48,0.75,0.40) # green
    else: #pointerNodeName == "CurrentPositionNeedle"
      locatorModelNode.GetDisplayNode().SetColor(0.40,0.48,0.75) # blue
    self.cyl.Update()

    #Rotate cylinder
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transform = vtk.vtkTransform()
    transform.RotateX(90.0)
    transform.Translate(0.0, -50.0, 0.0)
    transform.Update()
    transformFilter.SetInputConnection(self.cyl.GetOutputPort())
    transformFilter.SetTransform(transform)

    self.sphere = vtk.vtkSphereSource()
    self.sphere.SetRadius(3.0)
    self.sphere.SetCenter(0, 0, 0)

    self.append = vtk.vtkAppendPolyData()
    self.append.AddInputConnection(self.sphere.GetOutputPort())
    self.append.AddInputConnection(transformFilter.GetOutputPort())
    self.append.Update()

    locatorModelNode.SetAndObservePolyData(self.append.GetOutput())
    self.treeView.setMRMLScene(slicer.mrmlScene)

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
      
      # Get start and end slices from the StartSliceSliderWidget
      # self.startSlice = int(self.startSliceSliderWidget.value)
      # self.endSlice = int(self.endSliceSliderWidget.value)
      # maxSlice = self.inputVolume.GetImageData().GetDimensions()[2]
      # if self.endSlice == 0 or self.endSlice > maxSlice:
      #   # Use the image end slice
      #   self.endSlice = maxSlice
      #   self.endSliceSliderWidget.value = float(self.endSlice)
      self.startSlice = 5
      self.endSlice = 16

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
        # self.startSliceSliderWidget.value = float(self.startSlice)
        # self.endSliceSliderWidget.value = float(self.endSlice)

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

        # Send the calculated calibration matrix to WPI as the CLB matrix
        outputMatrix = vtk.vtkMatrix4x4()
        self.outputTransform.GetMatrixTransformToParent(outputMatrix)
        SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
        timestampIDname = self.generateTimestampNameID("CLB")
        SendTransformNodeTemp.SetName(timestampIDname)
        SendTransformNodeTemp.SetMatrixTransformToParent(outputMatrix)
        slicer.mrmlScene.AddNode(SendTransformNodeTemp)
        self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
        self.openIGTNode.PushNode(SendTransformNodeTemp)
        infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
        re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
        self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

        # Update the calibration matrix table with the calculated matrix (currently just dummy code)
        for i in range(4):
          for j in range(4):
            self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(outputMatrix.GetElement(i, j),2))))
        self.appendTransformToCommandLog(outputMatrix)

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
      timestampIDname = self.generateTimestampNameID("CLB")
      SendTransformNodeTemp.SetName(timestampIDname)
      SendTransformNodeTemp.SetMatrixTransformToParent(calibrationMatrix)
      slicer.mrmlScene.AddNode(SendTransformNodeTemp)
      self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
      self.openIGTNode.PushNode(SendTransformNodeTemp)
      infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.appendSentMessageToCommandLog(timestampIDname, infoMsg)
    
      # Update the calibration matrix table with the calculated matrix (currently just dummy code)
      for i in range(4):
        for j in range(4):
          self.calibrationTableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(calibrationMatrix.GetElement(i, j),2))))
      self.appendTransformToCommandLog(calibrationMatrix)

    elif inputVolume is not None:
      self.initiateZFrameCalibration()

    else:
      print("No zFrame image or pre-defined calibration matrix found. Cannot calculate the calibration matrix.")

  # Function to reset the 4x4 target transform to an identity matrix at the position of the new fiducial when the target point fiducial is updated
  def onTargetPointFiducialChanged(self):
    targetPointNode = self.targetPointNodeSelector.currentNode()
    if targetPointNode is not None:
      # if not self.phaseTextbox.text == 'PLANNING':
      #   print ("Robot is not yet in PLANNING workphase. Please enter PLANNING workphase before selecting the target point.")
      # else: 
      if not targetPointNode.GetNumberOfControlPoints() == 0:
        print("debug point 1")
        if self.plannedTargetTransform:
          slicer.mrmlScene.RemoveNode(self.plannedTargetTransform)
          self.plannedTargetTransform = None
        self.plannedTargetTransform = slicer.vtkMRMLLinearTransformNode()
        self.plannedTargetTransform.SetName("PlannedTargetTransform")
        slicer.mrmlScene.AddNode(self.plannedTargetTransform)
        self.plannedTargetTransform.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTargetTransformNodeModified)

        # Add display node to targetTransform
        # self.plannedTargetTransformDisplayNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLTransformDisplayNode())
        # self.plannedTargetTransformDisplayNode.SetVisibility(True)
        # self.plannedTargetTransform.SetAndObserveDisplayNodeID(self.plannedTargetTransformDisplayNode.GetID())

        # Add position element to target transform from the position of the target fiducial
        targetCoordinatesRAS = targetPointNode.GetNthControlPointPositionVector(0)
        targetPointMatrix = vtk.vtkMatrix4x4()
        targetPointMatrix.Identity()
        targetPointMatrix.SetElement(0,3,targetCoordinatesRAS[0])
        targetPointMatrix.SetElement(1,3,targetCoordinatesRAS[1])
        targetPointMatrix.SetElement(2,3,targetCoordinatesRAS[2])
        self.plannedTargetTransform.SetMatrixTransformToParent(targetPointMatrix)
        
        # Connect this transform node to the rotation sliders
        self.orientationSliderWidget.setMRMLTransformNode(self.plannedTargetTransform)
        self.translationSliderWidget.setMRMLTransformNode(self.plannedTargetTransform)

        # Set 3D visualization of needle to "On" when the target transform resets
        self.targetNeedleVisibleButton.setChecked(True)
        self.onPlannedTargetNeedleVisibleButtonClicked()

  def onTargetTransformNodeModified(self, unusedArg2=None, unusedArg3=None):
    # Update targetTableWidget when the targetTransform is modified
    targetTransformMatrix = vtk.vtkMatrix4x4()
    self.plannedTargetTransform.GetMatrixTransformToParent(targetTransformMatrix)
    nbRows = self.targetTableWidget.rowCount
    nbColumns = self.targetTableWidget.columnCount
    for i in range(nbRows):
      for j in range(nbColumns):
        self.targetTableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(targetTransformMatrix.GetElement(i,j),2))))

  def sendTargetTransform(self):
    # Send the 4x4 targeting matrix to WPI as the TGT matrix
    targetMatrix = vtk.vtkMatrix4x4()
    self.plannedTargetTransform.GetMatrixTransformToParent(targetMatrix)
    SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
    timestampIDname = self.generateTimestampNameID("TGT")
    SendTransformNodeTemp.SetName(timestampIDname)
    SendTransformNodeTemp.SetMatrixTransformToParent(targetMatrix)
    slicer.mrmlScene.AddNode(SendTransformNodeTemp)
    self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
    self.openIGTNode.PushNode(SendTransformNodeTemp)
    infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)
  
  # def onSendTargetPointButtonClicked(self):
  #   targetPointNode = self.targetPointNodeSelector.currentNode()
  #   if not targetPointNode:
  #     print ("No TARGET_POINT fiducial selected.")
  #   elif not self.phaseTextbox.text == 'TARGETING':
  #     print ("Robot is not yet in TARGETING workphase. Please enter TARGETING workphase before sending target or entry points.")
  #   else:
  #     # Print RAS coordinates of the target point fiducial into the Target point GUI
  #     targetCoordinatesRAS = [0, 0, 0]
  #     targetPointNode.GetNthFiducialPosition(0, targetCoordinatesRAS)

  #     self.targetCoordinate_R = round(targetCoordinatesRAS[0],2)
  #     self.targetCoordinate_A = round(targetCoordinatesRAS[1],2)
  #     self.targetCoordinate_S = round(targetCoordinatesRAS[2],2)

  #     self.targetPointTextbox_R.setText(str(self.targetCoordinate_R))
  #     self.targetPointTextbox_A.setText(str(self.targetCoordinate_A))
  #     self.targetPointTextbox_S.setText(str(self.targetCoordinate_S))

  #     # Send target point via IGTLink as a 4x4 matrix transform called TGT_XXX
  #     targetPointMatrix = vtk.vtkMatrix4x4()
  #     targetPointMatrix.Identity()
  #     targetPointMatrix.SetElement(0,3,self.targetCoordinate_R)
  #     targetPointMatrix.SetElement(1,3,self.targetCoordinate_A)
  #     targetPointMatrix.SetElement(2,3,self.targetCoordinate_S)
  #     SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
  #     timestampIDname = self.generateTimestampNameID("TGT")
  #     SendTransformNodeTemp.SetName(timestampIDname)
  #     SendTransformNodeTemp.SetMatrixTransformToParent(targetPointMatrix)
  #     slicer.mrmlScene.AddNode(SendTransformNodeTemp)
  #     self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
  #     self.openIGTNode.PushNode(SendTransformNodeTemp)
  #     infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
  #     re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
  #     self.appendSentMessageToCommandLog(timestampIDname, infoMsg)
  #     self.appendTransformToCommandLog(targetPointMatrix)

  # def onSendEntryPointButtonClicked(self):
  #   entryPointNode = self.entryPointNodeSelector.currentNode()
  #   if not entryPointNode:
  #     print ("No ENTRY_POINT fiducial selected.")
  #   elif not self.phaseTextbox.text == 'TARGETING':
  #     print ("Robot is not yet in TARGETING workphase. Please enter TARGETING workphase before sending target or entry points.")
  #   else:
  #     if self.entryPointCheckbox.isChecked():
      
  #       # Print RAS coordinates of the RESTRICTED entry point fiducial
  #       entryCoordinatesRAS = [0, 0, 0]
  #       entryPointNode.GetNthFiducialPosition(0, entryCoordinatesRAS)

  #       self.entryCoordinate_R = round(self.targetCoordinate_R,2)
  #       self.entryCoordinate_A = round(entryCoordinatesRAS[1],2)
  #       self.entryCoordinate_S = round(self.targetCoordinate_S,2)

  #       self.entryPointTextbox_R.setText(str(self.entryCoordinate_R))
  #       self.entryPointTextbox_A.setText(str(self.entryCoordinate_A))
  #       self.entryPointTextbox_S.setText(str(self.entryCoordinate_S))

  #       # Move the fiducial to the new point, on the same horizontal line as the Target Point
  #       entryPointNode.SetNthFiducialPosition(0, self.entryCoordinate_R, self.entryCoordinate_A, self.entryCoordinate_S)

  #     else: 
  #       # Print RAS coordinates of the entry point fiducial into the Entry point GUI
  #       entryCoordinatesRAS = [0, 0, 0]
  #       entryPointNode.GetNthFiducialPosition(0, entryCoordinatesRAS)

  #       self.entryCoordinate_R = round(entryCoordinatesRAS[0],2)
  #       self.entryCoordinate_A = round(entryCoordinatesRAS[1],2)
  #       self.entryCoordinate_S = round(entryCoordinatesRAS[2],2)

  #       self.entryPointTextbox_R.setText(str(self.entryCoordinate_R))
  #       self.entryPointTextbox_A.setText(str(self.entryCoordinate_A))
  #       self.entryPointTextbox_S.setText(str(self.entryCoordinate_S))

  #     # Send entry point via IGTLink as a 4x4 matrix transform called ENT_XXX
  #     entryPointMatrix = vtk.vtkMatrix4x4()
  #     entryPointMatrix.Identity()
  #     entryPointMatrix.SetElement(0,3,self.entryCoordinate_R)
  #     entryPointMatrix.SetElement(1,3,self.entryCoordinate_A)
  #     entryPointMatrix.SetElement(2,3,self.entryCoordinate_S)
  #     SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
  #     timestampIDname = self.generateTimestampNameID("ENT")
  #     SendTransformNodeTemp.SetName(timestampIDname)
  #     SendTransformNodeTemp.SetMatrixTransformToParent(entryPointMatrix)
  #     slicer.mrmlScene.AddNode(SendTransformNodeTemp)
  #     self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
  #     self.openIGTNode.PushNode(SendTransformNodeTemp)
  #     infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
  #     re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
  #     self.appendSentMessageToCommandLog(timestampIDname, infoMsg)
  #     self.appendTransformToCommandLog(entryPointMatrix) 

  #     # Create a 3D model of the needle between the target and entry points
  #     self.createInitialNeedleModel()

  def getRobotPoseUntilTargetIsReached(self):
    # When Move button is clicked, request current pose from WPI every second
    print ("TODO - getRobotPoseUntilTargetIsReached()")

    # TODO !

    # Get the REACHABLE_TARGET transform
    reachableTargetPositionNode = slicer.vtkMRMLLinearTransformNode()
    transformNodes = slicer.util.getNodesByClass("vtkMRMLLinearTransformNode")
    reachableTargetFound = False
    for transformNode in transformNodes:
      if transformNode.GetName().split("_")[0] == "REACHABLE":
        reachableTargetPositionNode = transformNode
        reachableTargetFound = True
    
    if not reachableTargetFound:
      print ("No transform found that is named REACHABLE_TARGET.")
      # FOR DEBUGGING PURPOSES ONLY - get matrix named TGT_XXX instead: TODO (delete)
      for transformNode in transformNodes:
        if transformNode.GetName().split("_")[0] == "TGT":
          reachableTargetPositionNode = transformNode

    targetPositionMatrix = vtk.vtkMatrix4x4()
    reachableTargetPositionNode.GetMatrixTransformToParent(targetPositionMatrix)
    print("REACHABLE TARGET POSITION NODE: ", targetPositionMatrix)

    # Request the current position from the robot
    # Robot will respond with a transform with the name CURRENT_POSITION
    # self.onGetPoseButtonClicked()
    # print("Send command to get current position of the robot")
    getposeNode = slicer.vtkMRMLTextNode()
    self.last_prefix_sent = "CMD"
    timestampIDname = self.generateTimestampNameID(self.last_prefix_sent)
    self.last_name_sent = self.generateTimestampNameID(self.last_prefix_sent)
    getposeNode.SetName(timestampIDname)
    getposeNode.SetText("GET_POSE")
    getposeNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(getposeNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(getposeNode)
    self.openIGTNode.PushNode(getposeNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  GET_POSE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg)

    time.sleep(0.1)

    # Get transform CURRENT_POSITION
    self.currentPositionNode = slicer.mrmlScene.GetFirstNodeByName("TransformMessage")
    self.currentPositionMatrix = vtk.vtkMatrix4x4()
    self.currentPositionNode.GetMatrixTransformToParent(self.currentPositionMatrix)
    print("CURRENT POSITION NODE: ", self.currentPositionNode)
    #self.onCurrentPositionTransformReceived_v2(self.currentPositionNode)

    # Update needle model in 3D Slicer pane via updateNeedleModelPosition:
    # self.updateNeedleModelPosition(currentPositionMatrix)
    # TODO

    positionsAreEqual = True
    for i in range(4):
      for j in range(4):
        if not round(targetPositionMatrix.GetElement(i, j),1) == round(self.currentPositionMatrix.GetElement(i, j),1):
          positionsAreEqual = False
          break

    if positionsAreEqual:
      print("--------------- Robot has reached the target")
    else:
      print("--------------- Robot has NOT yet reached the target")
      time.sleep(1)
      self.getRobotPoseUntilTargetIsReached()


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
    zFrameModelPath = os.path.join(currentFilePath, "Resources", "zframe", self.ZFRAME_MODEL_PATH)
    _, self.zFrameModelNode = slicer.util.loadModel(zFrameModelPath, returnNode=True)
    self.zFrameModelNode.SetName(self.ZFRAME_MODEL_NAME)
    modelDisplayNode = self.zFrameModelNode.GetDisplayNode()
    #modelDisplayNode.SetColor(1, 1, 0)
    modelDisplayNode.SetColor(0.9,0.9,0.4)
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