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
from pyexpat import model
import unittest
# from matplotlib.pyplot import get
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
from slicer.util import NodeModify
import sitkUtils
import numpy as np
import time
import datetime
import random
import string
import math
import re
import csv
import configparser
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
    self.parent.contributors = ["Rebecca Lisk (SNR), Franklin King (SNR)"]
    self.parent.helpText = """
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
"""
    # Set module icon from Resources/Icons/<ModuleName>.png
    moduleDir = os.path.dirname(self.parent.path)
    for iconExtension in ['.svg', '.png']:
      iconPath = os.path.join(moduleDir, 'Resources/Icons', self.__class__.__name__ + iconExtension)
      if os.path.isfile(iconPath):
        parent.icon = qt.QIcon(iconPath)
        break

class ProstateBRPInterfaceWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.nodeAddedObserver = None
    self.onACKTransformNodeModifiedObserver = None
    self.onTargetTransformNodeModifiedObserver = None
    self.onPositionTransformNodeModifiedObserver = None
    self.needleTipTransformObserver = None
    self.plannedTargetTransformObserver = None
    self.status_codes = ['STATUS_INVALID', 'STATUS_OK', 'STATUS_UNKNOWN_ERROR', 'STATUS_PANIC_MODE', 'STATUS_NOT_FOUND', 'STATUS_ACCESS_DENIED', 'STATUS_BUSY', 'STATUS_TIME_OUT', 'STATUS_OVERFLOW','STATUS_CHECKSUM_ERROR','STATUS_CONFIG_ERROR','STATUS_RESOURCE_ERROR','STATUS_UNKNOWN_INSTRUCTION','STATUS_NOT_READY','STATUS_MANUAL_MODE','STATUS_DISABLED','STATUS_NOT_PRESENT','STATUS_UNKNOWN_VERSION','STATUS_HARDWARE_FAILURE','STATUS_SHUT_DOWN','STATUS_NUM_TYPES']
    #self.robot_phases = ['START_UP', 'EMERGENCY', 'TARGETING', 'MOVE_TO_TARGET', 'CALIBRATION', 'PLANNING']
    self.robot_phase = "NONE"
    self.firstServer = True # Set to false the first time CreateServerButton is clicked so that nodes are not re-created

  def cleanup(self):
    self.getTransformTimer.stop()
    if self.nodeAddedObserver: slicer.mrmlScene.RemoveObserver(self.nodeAddedObserver)
    if self.onACKTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onACKTransformNodeModifiedObserver)
    if self.onTargetTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onTargetTransformNodeModifiedObserver)
    if self.onPositionTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onPositionTransformNodeModifiedObserver)
    if self.needleTipTransformObserver: slicer.mrmlScene.RemoveObserver(self.needleTipTransformObserver)
    if self.plannedTargetTransformObserver: slicer.mrmlScene.RemoveObserver(self.plannedTargetTransformObserver)
    self.registrationTranslationSliderWidget.setMRMLTransformNode(None)
    self.registrationTranslationSliderWidget.reset()
    self.registrationOrientationSliderWidget.setMRMLTransformNode(None)
    self.registrationOrientationSliderWidget.reset()
    self.robot_phase = "NONE"
    self.firstServer = True # Set to false the first time CreateServerButton is clicked so that nodes are not re-created

  def onReload(self,moduleName="ProstateBRPInterface"):
    self.getTransformTimer.stop()
    if self.nodeAddedObserver: slicer.mrmlScene.RemoveObserver(self.nodeAddedObserver)
    if self.onACKTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onACKTransformNodeModifiedObserver)
    if self.onTargetTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onTargetTransformNodeModifiedObserver)
    if self.onPositionTransformNodeModifiedObserver: slicer.mrmlScene.RemoveObserver(self.onPositionTransformNodeModifiedObserver)
    if self.needleTipTransformObserver: slicer.mrmlScene.RemoveObserver(self.needleTipTransformObserver)
    if self.plannedTargetTransformObserver: slicer.mrmlScene.RemoveObserver(self.plannedTargetTransformObserver)
    self.registrationTranslationSliderWidget.setMRMLTransformNode(None)
    self.registrationTranslationSliderWidget.reset()
    self.registrationOrientationSliderWidget.setMRMLTransformNode(None)
    self.registrationOrientationSliderWidget.reset()
    self.robot_phase = "NONE"
    self.firstServer = True # Set to false the first time CreateServerButton is clicked so that nodes are not re-created
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    moduleDir = os.path.dirname(slicer.util.modulePath(self.__module__))
    print(moduleDir)
    defaultsFilePath = os.path.join(moduleDir, "Resources/Defaults.ini")
    config = configparser.ConfigParser()
    config.read(defaultsFilePath)

    # ------------------------------------ Initialization UI ---------------------------------------
    # Server collapsible button
    serverCollapsibleButton = ctk.ctkCollapsibleButton()
    serverCollapsibleButton.text = "Robot Connection"
    self.layout.addWidget(serverCollapsibleButton)

    # Layout within the path collapsible button
    serverFormLayout = qt.QGridLayout(serverCollapsibleButton)

    # Slicer<->Robot IGTLink connection interface
    # Create server button
    initializeFont = qt.QFont()
    initializeFont.setPointSize(16)
    initializeFont.setBold(False)
    self.createServerButton = qt.QPushButton("Start robot client")
    self.createServerButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.createServerButton.setFont(initializeFont)
    self.createServerButton.toolTip = "Create the IGTLink client connection with robot."
    self.createServerButton.enabled = True
    self.createServerButton.setFixedWidth(250)
    serverFormLayout.addWidget(self.createServerButton, 0, 0)
    self.createServerButton.connect('clicked()', self.onCreateRobotClientButtonClicked)

    self.disconnectFromSocketButton = qt.QPushButton("Disconnect from robot")
    self.disconnectFromSocketButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.disconnectFromSocketButton.setFont(initializeFont)
    self.disconnectFromSocketButton.toolTip = "Disconnect from the socket."
    self.disconnectFromSocketButton.enabled = False
    self.disconnectFromSocketButton.setFixedWidth(250)
    serverFormLayout.addWidget(self.disconnectFromSocketButton, 0, 1)
    self.disconnectFromSocketButton.connect('clicked()', self.onDisconnectFromSocketButtonClicked)

    hostname = config['GENERAL']['hostname']
    self.snrHostnameTextboxLabel = qt.QLabel('Robot server hostname:')
    self.snrHostnameTextbox = qt.QLineEdit(hostname)
    self.snrHostnameTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setMaximumWidth(250)
    serverFormLayout.addWidget(self.snrHostnameTextboxLabel, 1, 0)
    serverFormLayout.addWidget(self.snrHostnameTextbox, 1, 1)

    port = config['GENERAL']['port']
    self.snrPortTextboxLabel = qt.QLabel('Robot server port:')
    self.snrPortTextbox = qt.QLineEdit(port)
    self.snrPortTextbox.setReadOnly(False)
    self.snrPortTextbox.setMaximumWidth(75)
    serverFormLayout.addWidget(self.snrPortTextboxLabel, 2, 0)
    serverFormLayout.addWidget(self.snrPortTextbox, 2, 1)

    # -------- Slicer <--> WPI connection GUI ---------

    # Slicer <--> MRI collapsible button
    self.RobotCommunicationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.RobotCommunicationCollapsibleButton.text = "Robot Control"
    self.RobotCommunicationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.RobotCommunicationCollapsibleButton)

    # Overall layout within the path collapsible button
    RobotCommunicationLayout = qt.QVBoxLayout(self.RobotCommunicationCollapsibleButton)

    # Outbound layout within the path collapsible button
    RobotOutboundCommunicationLayout = qt.QGridLayout()
    RobotCommunicationLayout.addLayout(RobotOutboundCommunicationLayout)

    # Current Phase button
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

    # currentPosition Button
    self.currentPositionButton = qt.QPushButton("QUERY POSITION")
    self.currentPositionButton.toolTip = "Continuously query robot for position."
    self.currentPositionButton.setCheckable(True)
    self.currentPositionButton.enabled = False
    self.currentPositionButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.currentPositionButton, 2, 1)
    self.currentPositionButton.connect('clicked()', self.onCurrentPositionClicked)

    self.currentPositionTransform = None
    self.currentPositionBaseTransform = None

    # calibrationButton Button
    self.calibrationButton = qt.QPushButton("CALIBRATION")
    self.calibrationButton.toolTip = "Send the calibration command to the WPI robot."
    self.calibrationButton.enabled = False
    self.calibrationButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.calibrationButton, 4, 0)
    self.calibrationButton.connect('clicked()', self.onCalibrationButtonClicked)

    # planningButton Button # TODO Check protocol: should it print sucess after CURRENT_STATUS is sent?
    self.planningButton = qt.QPushButton("PLANNING")
    self.planningButton.toolTip = "Send the planning command to the WPI robot."
    self.planningButton.enabled = False
    self.planningButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.planningButton, 4, 1)
    self.planningButton.connect('clicked()', self.onPlanningButtonClicked)

    # targetingButton Button
    self.targetingButton = qt.QPushButton("TARGETING")
    self.targetingButton.toolTip = "Send the targeting command to the WPI robot."
    self.targetingButton.enabled = False
    self.targetingButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.targetingButton, 5 , 0)
    self.targetingButton.connect('clicked()', self.onTargetingButtonClicked)

    # moveButton Button
    self.moveButton = qt.QPushButton("MOVE")
    self.moveButton.toolTip = "Send the move to target command to the WPI robot."
    self.moveButton.enabled = False
    self.moveButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.moveButton, 5, 1)
    self.moveButton.connect('clicked()', self.onMoveButtonClicked)

    # # Get robot status Button to ask WPI to send the current status position
    # self.GetStatusButton = qt.QPushButton("GET STATUS")
    # self.GetStatusButton.toolTip = "Send the command to ask WPI to send the current robot status."
    # self.GetStatusButton.enabled = True
    # self.GetStatusButton.setMaximumWidth(250)
    # RobotOutboundCommunicationLayout.addWidget(self.GetStatusButton, 6, 0)
    # self.GetStatusButton.connect('clicked()', self.onGetStatusButtonClicked)

    # Retract needle button
    self.RetractNeedleButton = qt.QPushButton("RETRACT NEEDLE")
    self.RetractNeedleButton.toolTip = "Send the command to ask WPI to retract the needle."
    self.RetractNeedleButton.enabled = False
    self.RetractNeedleButton.setMaximumWidth(250)
    RobotOutboundCommunicationLayout.addWidget(self.RetractNeedleButton, 6, 1)
    self.RetractNeedleButton.connect('clicked()', self.onRetractNeedleButtonClicked)    

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

    self.getTransformFPSBox = qt.QSpinBox()
    self.getTransformFPSBox.setSingleStep(1)
    self.getTransformFPSBox.setMaximum(144)
    self.getTransformFPSBox.setMinimum(1)
    self.getTransformFPSBox.setSuffix(" FPS")
    self.getTransformFPSBox.value = 5
    getTransformFPSLabel = qt.QLabel('Query position rate:')
    RobotOutboundCommunicationLayout.addWidget(getTransformFPSLabel, 8, 0)
    RobotOutboundCommunicationLayout.addWidget(self.getTransformFPSBox, 8, 1)

    self.getTransformNode = None
    self.getTransformTimer = qt.QTimer()
    self.getTransformTimer.timeout.connect(self.updateGetTransform)
    self.retractNeedleNode = None

    self.robotMessageTextbox = qt.QLineEdit("No message received")
    self.robotMessageTextbox.setReadOnly(True)
    self.robotMessageTextbox.setFixedWidth(200)
    robotMessageTextboxLabel = qt.QLabel("Message received:")
    RobotOutboundCommunicationLayout.addWidget(robotMessageTextboxLabel, 10, 0, 1, 1)
    RobotOutboundCommunicationLayout.addWidget(self.robotMessageTextbox, 10, 1, 1, 1)

    self.robotStatusCodeTextbox = qt.QLineEdit("No status code received")
    self.robotStatusCodeTextbox.setReadOnly(True)
    self.robotStatusCodeTextbox.setFixedWidth(200)
    robotStatusCodeTextboxLabel = qt.QLabel("Status received:")
    RobotOutboundCommunicationLayout.addWidget(robotStatusCodeTextboxLabel, 11, 0, 1, 1)
    RobotOutboundCommunicationLayout.addWidget(self.robotStatusCodeTextbox, 11, 1, 1, 1)

    RobotInboundCommunicationMatrixGroupBox = ctk.ctkCollapsibleGroupBox()
    RobotInboundCommunicationMatrixGroupBox.title = "Transforms Received"
    RobotInboundCommunicationMatrixGroupBox.collapsed = True
    RobotInboundCommunicationMatrixLayout = qt.QFormLayout(RobotInboundCommunicationMatrixGroupBox)
    RobotOutboundCommunicationLayout.addWidget(RobotInboundCommunicationMatrixGroupBox, 12, 0, 1, 2)

    row = 4
    column = 4
    self.robotTableWidget = qt.QTableWidget(row, column)
    self.robotTableWidget.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Minimum)
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
    RobotInboundCommunicationMatrixLayout.addRow("Target received:", self.robotTableWidget)

    self.robotPositionTableWidget = qt.QTableWidget(row, column)
    self.robotPositionTableWidget.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Minimum)
    #self.robotPositionTableWidget.setMaximumWidth(400)
    self.robotPositionTableWidget.setMinimumHeight(95)
    self.robotPositionTableWidget.verticalHeader().hide() # Remove line numbers
    self.robotPositionTableWidget.horizontalHeader().hide() # Remove column numbers
    self.robotPositionTableWidget.setEditTriggers(qt.QTableWidget.NoEditTriggers) # Make table read-only
    horizontalheader = self.robotPositionTableWidget.horizontalHeader()
    horizontalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    horizontalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    verticalheader = self.robotPositionTableWidget.verticalHeader()
    verticalheader.setSectionResizeMode(0, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(1, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(2, qt.QHeaderView.Stretch)
    verticalheader.setSectionResizeMode(3, qt.QHeaderView.Stretch)
    RobotInboundCommunicationMatrixLayout.addRow("Position received:", self.robotPositionTableWidget)

    # -------  Calibration GUI ---------

    # Outbound tranform collapsible button
    self.calibrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.calibrationCollapsibleButton.text = "Registration"
    self.calibrationCollapsibleButton.collapsed = True
    self.layout.addWidget(self.calibrationCollapsibleButton)

    # Layout within the collapsible button
    calibrationLayout = qt.QVBoxLayout(self.calibrationCollapsibleButton)

    # Top layout within the calibration collapsible button (CalibrationLayout)
    calibrationLayoutTop = qt.QFormLayout()
    calibrationLayout.addLayout(calibrationLayoutTop)

    registerFont = qt.QFont()
    registerFont.setPointSize(18)
    registerFont.setBold(False)
    self.registrationButton = qt.QPushButton("Register")
    self.registrationButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.registrationButton.setFont(registerFont)
    self.registrationButton.toolTip = "Start registration process for Z-Frame"
    self.registrationButton.enabled = True
    self.registrationButton.connect('clicked()', self.onRegister)
    calibrationLayoutTop.addRow(self.registrationButton)

    # Create and send new calibration matrix button
    sendToRobotFont = qt.QFont()
    sendToRobotFont.setPointSize(14)
    self.sendCalibrationMatrixButton = qt.QPushButton("Send Transform To Robot")
    #self.sendCalibrationMatrixButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.sendCalibrationMatrixButton.setFont(sendToRobotFont)
    self.sendCalibrationMatrixButton.enabled = False
    calibrationLayoutTop.addRow(self.sendCalibrationMatrixButton)
    self.sendCalibrationMatrixButton.connect('clicked()', self.onSendCalibrationMatrixButtonClicked)

    validRegistrationFont = qt.QFont()
    validRegistrationFont.setPointSize(18)
    validRegistrationFont.setBold(False)
    self.validRegistrationLabel = qt.QLabel()
    self.validRegistrationLabel.text = ""
    self.validRegistrationLabel.setAlignment(qt.Qt.AlignCenter)
    calibrationLayoutTop.addRow(self.validRegistrationLabel)

    # Z-frame configuration file selection box
    self.configFileSelectionBox = qt.QComboBox()
    self.configFileSelectionBox.addItems(['Template 001 - Seven Fiducials', 'Template 002 - Nine Fiducials', 'Template 003 - BRP Robot - Nine Fiducials', 'Template 004 - Wide Z-frame - Seven Fiducials'])
    self.configFileSelectionBox.setCurrentIndex(config['REGISTRATION'].getint('template_index'))
    calibrationLayoutTop.addRow('Template Configuration:', self.configFileSelectionBox)

    # Input volume selector for zFrame calibration
    self.zFrameVolumeSelector = slicer.qMRMLNodeComboBox()
    self.zFrameVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.zFrameVolumeSelector.objectName = 'zFrameVolumeSelector'
    self.zFrameVolumeSelector.toolTip = "Select the ZFrame image."
    self.zFrameVolumeSelector.nodeTypes = ['vtkMRMLVolumeNode']
    self.zFrameVolumeSelector.hideChildNodeTypes = ['vtkMRMLAnnotationNode']  # hide all annotation nodes
    self.zFrameVolumeSelector.noneEnabled = False
    self.zFrameVolumeSelector.addEnabled = False
    self.zFrameVolumeSelector.removeEnabled = False
    #self.zFrameVolumeSelector.setFixedWidth(250)
    calibrationLayoutTop.addRow('Registration image:', self.zFrameVolumeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.zFrameVolumeSelector, 'setMRMLScene(vtkMRMLScene*)')

    # Add spacer to left align the reference frame toggle button and reset button
    spacer = qt.QSpacerItem(150, 10, qt.QSizePolicy.Expanding)
    calibrationLayout.addSpacerItem(spacer)

    registrationParametersGroupBox = ctk.ctkCollapsibleGroupBox()
    registrationParametersGroupBox.title = "Automatic Registration Parameters"
    registrationParametersGroupBox.collapsed = True
    registrationParametersLayout = qt.QFormLayout(registrationParametersGroupBox)
    calibrationLayout.addWidget(registrationParametersGroupBox)

    self.defaultThresholdPercentage = config['REGISTRATION'].getfloat('threshold_percentage')
    self.thresholdSliderWidget = ctk.ctkSliderWidget()
    self.thresholdSliderWidget.setToolTip("Set range for threshold percentage for isolating registration fiducial markers")
    self.thresholdSliderWidget.setDecimals(2)
    self.thresholdSliderWidget.minimum = 0.00
    self.thresholdSliderWidget.maximum = 1.00
    self.thresholdSliderWidget.singleStep = 0.01
    self.thresholdSliderWidget.value = self.defaultThresholdPercentage
    registrationParametersLayout.addRow("Threshold Percentage:", self.thresholdSliderWidget)

    self.fiducialSizeSliderWidget = ctk.ctkRangeWidget()
    self.fiducialSizeSliderWidget.setToolTip("Set range for fiducial size for isolating registration fiducial markers")
    self.fiducialSizeSliderWidget.setDecimals(0)
    self.fiducialSizeSliderWidget.maximum = 5000
    self.fiducialSizeSliderWidget.minimum = 0
    self.fiducialSizeSliderWidget.singleStep = 1
    self.fiducialSizeSliderWidget.maximumValue = config['REGISTRATION'].getint('fiducial_size_maxValue')
    self.fiducialSizeSliderWidget.minimumValue = config['REGISTRATION'].getint('fiducial_size_minValue')
    registrationParametersLayout.addRow("Fiducial Size Range:", self.fiducialSizeSliderWidget)

    self.borderMarginSliderWidget = ctk.ctkSliderWidget()
    self.borderMarginSliderWidget.setToolTip("Set range for threshold percentage for isolating registration fiducial markers")
    self.borderMarginSliderWidget.setDecimals(0)
    self.borderMarginSliderWidget.minimum = 0
    self.borderMarginSliderWidget.maximum = 50
    self.borderMarginSliderWidget.singleStep = 1
    self.borderMarginSliderWidget.value = config['REGISTRATION'].getint('border_margin')
    registrationParametersLayout.addRow("Border Removal Margin:", self.borderMarginSliderWidget)

    self.removeOrientationCheckBox = qt.QCheckBox("Remove orientation from registration transform")
    self.removeOrientationCheckBox.setChecked(config['REGISTRATION'].getboolean('remove_orientation'))
    registrationParametersLayout.addRow(self.removeOrientationCheckBox)

    self.removeBorderIslandsCheckBox = qt.QCheckBox("Remove segment islands on border of volume")
    self.removeBorderIslandsCheckBox.setChecked(config['REGISTRATION'].getboolean('remove_border_islands'))
    registrationParametersLayout.addRow(self.removeBorderIslandsCheckBox)

    # self.repairFiducialImageCheckBox = qt.QCheckBox("Attempt repair of fiducial image")
    # self.repairFiducialImageCheckBox.setChecked(config['REGISTRATION'].getboolean('repair_fiducials'))
    # registrationParametersLayout.addRow(self.repairFiducialImageCheckBox)

    self.retryFailedRegistrationCheckBox = qt.QCheckBox("Re-attempt registration with different settings upon failure")
    self.retryFailedRegistrationCheckBox.setChecked(config['REGISTRATION'].getboolean('retry_failed'))
    registrationParametersLayout.addRow(self.retryFailedRegistrationCheckBox)

    self.manualRegistrationGroupBox = ctk.ctkCollapsibleGroupBox()
    self.manualRegistrationGroupBox.title = "Manual Registration"
    self.manualRegistrationGroupBox.collapsed = True
    manualRegistrationLayout = qt.QFormLayout(self.manualRegistrationGroupBox)
    calibrationLayout.addWidget(self.manualRegistrationGroupBox)

    # Define dummy registration transform to link to transform sliders below
    self.outputTransform = slicer.vtkMRMLLinearTransformNode()
    self.outputTransform.SetName('outputTransform')
    slicer.mrmlScene.AddNode(self.outputTransform)

    self.registrationTranslationSliderWidget = slicer.qMRMLTransformSliders()
    self.registrationTranslationSliderWidget.setWindowTitle("Translation")
    self.registrationTranslationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.TRANSLATION
    self.registrationTranslationSliderWidget.setDecimals(3)
    manualRegistrationLayout.addWidget(self.registrationTranslationSliderWidget)

    self.registrationOrientationSliderWidget = slicer.qMRMLTransformSliders()
    self.registrationOrientationSliderWidget.setWindowTitle("Rotation")
    self.registrationOrientationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.ROTATION
    self.registrationOrientationSliderWidget.setDecimals(3)
    manualRegistrationLayout.addWidget(self.registrationOrientationSliderWidget)

    manualRegistrationFooterWidget = qt.QWidget()
    manualRegistrationLayout.addWidget(manualRegistrationFooterWidget)
    manualRegistrationFooterLayout = qt.QHBoxLayout(manualRegistrationFooterWidget)

    self.identityButton = qt.QPushButton("Identity")
    self.identityButton.toolTip = "Set Z-Frame calibration matrix to be Identity"
    self.identityButton.setMaximumWidth(100)
    self.identityButton.connect('clicked()', self.onIdentity)
    manualRegistrationFooterLayout.addWidget(self.identityButton)

    manualRegisterFont = qt.QFont()
    manualRegisterFont.setPointSize(12)
    manualRegisterFont.setBold(False)
    useManualRegistrationButton = qt.QPushButton("Accept Manual Registration")
    useManualRegistrationButton.setStyleSheet("QPushButton {background-color: #16417C}")
    useManualRegistrationButton.setFont(manualRegisterFont)
    useManualRegistrationButton.toolTip = "Flag module to accept manual registration"
    useManualRegistrationButton.connect('clicked()', self.onUseManualRegistration)
    manualRegistrationFooterLayout.addWidget(useManualRegistrationButton)

    self.registrationTranslationSliderWidget.setMRMLTransformNode(self.outputTransform)
    self.registrationOrientationSliderWidget.setMRMLTransformNode(self.outputTransform)

    # Planning phase GUI ---------------------------------------

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

    addTargetFont = qt.QFont()
    addTargetFont.setPointSize(18)
    addTargetFont.setBold(False)
    self.addTargetButton = qt.QPushButton("Add Target")
    self.addTargetButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.addTargetButton.setFont(registerFont)
    self.addTargetButton.toolTip = "Add a target for biopsy"
    self.addTargetButton.enabled = True
    self.addTargetButton.connect('clicked()', self.onAddTarget)
    planningLayoutTop.addRow(self.addTargetButton)

    self.targetPointNodeSelector = slicer.qSlicerSimpleMarkupsWidget()
    self.targetPointNodeSelector.objectName = 'targetPointNodeSelector'
    self.targetPointNodeSelector.toolTip = "Select a fiducial to use as the needle insertion target point."
    self.targetPointNodeSelector.setNodeBaseName("TARGET_POINT")
    self.targetPointNodeSelector.defaultNodeColor = qt.QColor(170,0,0)
    self.targetPointNodeSelector.tableWidget().hide()
    self.targetPointNodeSelector.markupsSelectorComboBox().noneEnabled = False
    self.targetPointNodeSelector.markupsPlaceWidget().placeMultipleMarkups = slicer.qSlicerMarkupsPlaceWidget.ForcePlaceSingleMarkup
    planningLayoutTop.addRow("   Target point: ", self.targetPointNodeSelector)
    self.targetPointNodeSelector.setMRMLScene(slicer.mrmlScene)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)', self.targetPointNodeSelector, 'setMRMLScene(vtkMRMLScene*)')
    self.targetPointNodeSelector.connect('updateFinished()', self.onTargetPointFiducialChanged)

    # Transform matrix display table
    row = 4
    column = 4
    self.targetTableWidget = qt.QTableWidget(row, column)
    self.targetTableWidget.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Minimum)
    self.targetTableWidget.setMaximumWidth(400)
    self.targetTableWidget.setMinimumHeight(95)
    self.targetTableWidget.setMaximumHeight(100)
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
    planningLayoutTop.addRow("   Target transform:   ", self.targetTableWidget)

    # Create a new QHBoxLayout() within planningLayout to place 2 visibility buttons next to one another
    planningLayoutMiddle = qt.QHBoxLayout()
    planningLayout.addLayout(planningLayoutMiddle)
    
    # Add spacer to right align the two visibility buttons
    spacer = qt.QSpacerItem(132, 10, qt.QSizePolicy.Maximum)
    planningLayoutMiddle.addSpacerItem(spacer)

    # Needle model visibility icon
    self.targetNeedleVisibleButton = qt.QPushButton()
    eyeIconInvisible = qt.QPixmap(":/Icons/Small/SlicerInvisible.png")
    self.targetNeedleVisibleButton.setIcon(qt.QIcon(eyeIconInvisible))
    self.targetNeedleVisibleButton.setFixedWidth(25)
    self.targetNeedleVisibleButton.setFixedHeight(25)
    self.targetNeedleVisibleButton.setCheckable(True)
    planningLayoutMiddle.addWidget(self.targetNeedleVisibleButton)
    self.targetNeedleVisibleButton.connect('clicked()', self.onPlannedTargetNeedleVisibleButtonClicked)

    # Needle trajectory visibility icon
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    self.targetNeedleTrajectoryVisibleButton = qt.QPushButton()
    trajectoryIcon = qt.QIcon(os.path.join(currentFilePath, "Resources/UI/Icons/trajectoryIcon.png"))
    self.targetNeedleTrajectoryVisibleButton.setIconSize(qt.QSize(20, 20))
    self.targetNeedleTrajectoryVisibleButton.setIcon(trajectoryIcon)
    self.targetNeedleTrajectoryVisibleButton.setFixedWidth(25)
    self.targetNeedleTrajectoryVisibleButton.setFixedHeight(25)
    self.targetNeedleTrajectoryVisibleButton.setCheckable(True)
    planningLayoutMiddle.addWidget(self.targetNeedleTrajectoryVisibleButton)
    self.targetNeedleTrajectoryVisibleButton.connect('clicked()', self.onPlannedTrajectoryVisibleButtonClicked)

    # Add spacer to right align the visibility buttons
    spacer = qt.QSpacerItem(150, 10, qt.QSizePolicy.Expanding)
    planningLayoutMiddle.addSpacerItem(spacer)

    # Add spacer to right align the visibility buttons
    spacer = qt.QSpacerItem(150, 10, qt.QSizePolicy.Expanding)
    planningLayoutMiddle.addSpacerItem(spacer)

    # Add planningLayoutSLiders to contain the translation sliders
    planningLayoutSliders = qt.QFormLayout()
    planningLayout.addLayout(planningLayoutSliders)

    # self.plannedTargetTransform = None
    self.plannedTargetTransform = slicer.vtkMRMLTransformNode()
    self.plannedTargetTransform.SetName("PlannedTargetTransform")
    self.plannedTargetTransformObserver = self.plannedTargetTransform.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTargetTransformNodeModified)
    slicer.mrmlScene.AddNode(self.plannedTargetTransform)

    # Translation sliders
    self.translationSliderWidget = slicer.qMRMLTransformSliders()
    self.translationSliderWidget.Title = 'Translation'
    self.translationSliderWidget.setMRMLTransformNode(slicer.util.getNode("PlannedTargetTransform"))
    self.translationSliderWidget.setMRMLScene(slicer.mrmlScene)
    # Setting of qMRMLTransformSliders.TypeOfTransform is not robust: it has to be set after setMRMLScene and
    # has to be set twice (with setting the type to something else in between).
    # Therefore the following 3 lines are needed, and they are needed here:
    self.translationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.TRANSLATION
    self.translationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.ROTATION
    self.translationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.TRANSLATION
    self.translationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL
    self.translationSliderWidget.minMaxVisible = False
    planningLayoutSliders.addRow(self.translationSliderWidget)    

    # Rotation sliders
    self.orientationSliderWidget = slicer.qMRMLTransformSliders()
    self.orientationSliderWidget.Title = 'Rotation'
    self.orientationSliderWidget.setMRMLTransformNode(slicer.util.getNode("PlannedTargetTransform"))
    self.orientationSliderWidget.setMRMLScene(slicer.mrmlScene)
    self.orientationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.ROTATION
    self.orientationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.TRANSLATION
    self.orientationSliderWidget.TypeOfTransform = slicer.qMRMLTransformSliders.ROTATION
    self.orientationSliderWidget.CoordinateReference = slicer.qMRMLTransformSliders.LOCAL
    self.orientationSliderWidget.minMaxVisible = False
    planningLayoutSliders.addRow(self.orientationSliderWidget)

    # Needle Tracking panel collapsible button
    self.needleTrackingPanelCollapsibleButton = ctk.ctkCollapsibleButton()
    self.needleTrackingPanelCollapsibleButton.text = "Needle Tracking"
    self.needleTrackingPanelCollapsibleButton.collapsed = True
    self.layout.addWidget(self.needleTrackingPanelCollapsibleButton)

    # Layout within the needle view panel collapsible button
    needleTrackingPanelLayout = qt.QFormLayout(self.needleTrackingPanelCollapsibleButton)

    self.needleTipTransformComboBox = slicer.qMRMLNodeComboBox()
    self.needleTipTransformComboBox.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.needleTipTransformComboBox.selectNodeUponCreation = False
    self.needleTipTransformComboBox.noneEnabled = False
    self.needleTipTransformComboBox.addEnabled = True
    self.needleTipTransformComboBox.showHidden = False
    self.needleTipTransformComboBox.setMRMLScene( slicer.mrmlScene )
    self.needleTipTransformComboBox.setToolTip( "Tracked Needle Tip Transform" )
    needleTrackingPanelLayout.addRow("Tracked Needle Tip Transform:", self.needleTipTransformComboBox)

    self.previousTrackedTipMatrix = vtk.vtkMatrix4x4()
    self.previousTrackedTipMatrix.Zero()
    self.sendTrackedTipTransformCheckbox = qt.QCheckBox("Send tracked tip position to Robot")
    self.sendTrackedTipTransformCheckbox.setChecked(False)
    needleTrackingPanelLayout.addWidget(self.sendTrackedTipTransformCheckbox)
   
    # ------------------------------------ Scanner UI ---------------------------------------
    # Server collapsible button
    scannerServerCollapsibleButton = ctk.ctkCollapsibleButton()
    scannerServerCollapsibleButton.text = "MRI Scanner"
    scannerServerCollapsibleButton.collapsed = True
    self.layout.addWidget(scannerServerCollapsibleButton)

    # Layout within the path collapsible button
    scannerServerFormLayout = qt.QGridLayout(scannerServerCollapsibleButton)

    # Slicer<->Scanner OpenIGTLink connection interface
    # Create server button
    self.createScannerServerButton = qt.QPushButton("Start MRI scanner server")
    self.createScannerServerButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.createScannerServerButton.setFont(initializeFont)
    self.createScannerServerButton.toolTip = "Create the IGTLink server connection with scanner."
    self.createScannerServerButton.enabled = True
    self.createScannerServerButton.setFixedWidth(250)
    scannerServerFormLayout.addWidget(self.createScannerServerButton, 0, 0)
    self.createScannerServerButton.connect('clicked()', self.onCreateScannerServerButtonClicked)

    self.disconnectFromScannerSocketButton = qt.QPushButton("Disconnect from socket")
    self.disconnectFromScannerSocketButton.setStyleSheet("QPushButton {background-color: #16417C}")
    self.disconnectFromScannerSocketButton.setFont(initializeFont)
    self.disconnectFromScannerSocketButton.toolTip = "Disconnect from the socket."
    self.disconnectFromScannerSocketButton.enabled = False
    self.disconnectFromScannerSocketButton.setFixedWidth(250)
    scannerServerFormLayout.addWidget(self.disconnectFromScannerSocketButton, 0, 1)
    self.disconnectFromScannerSocketButton.connect('clicked()', self.onDisconnectFromScannerSocketButtonClicked)    
    
    self.scannerPortTextboxLabel = qt.QLabel('Scanner server port:')
    self.scannerPortTextbox = qt.QLineEdit("18940")
    self.scannerPortTextbox.setReadOnly(False)
    self.scannerPortTextbox.setMaximumWidth(75)

    scannerServerFormLayout.addWidget(self.scannerPortTextboxLabel, 1, 0)
    scannerServerFormLayout.addWidget(self.scannerPortTextbox, 1, 1)
    
    MRIphaseTextboxLabel = qt.QLabel('Current phase:')
    self.MRIphaseTextbox = qt.QLineEdit("")
    self.MRIphaseTextbox.setReadOnly(True)
    self.MRIphaseTextbox.setFixedWidth(250)
    self.MRIphaseTextbox.toolTip = "Show current phase: in Blue if in the phase, green if phase successfully achieved"
    scannerServerFormLayout.addWidget(MRIphaseTextboxLabel, 2, 0)
    scannerServerFormLayout.addWidget(self.MRIphaseTextbox, 2, 1)

    # MRI Start scan button
    self.MRIstartScanButton = qt.QPushButton("START SEQUENCE")
    self.MRIstartScanButton.toolTip = "Begin scanning."
    self.MRIstartScanButton.enabled = True
    self.MRIstartScanButton.setMaximumWidth(250)
    scannerServerFormLayout.addWidget(self.MRIstartScanButton, 3, 0)
    self.MRIstartScanButton.connect('clicked()', self.onMRIStartScanButtonClicked)

    # MRI Stop scan button
    self.MRIstopScanButton = qt.QPushButton("STOP SEQUENCE")
    self.MRIstopScanButton.toolTip = "Stop scanning."
    self.MRIstopScanButton.enabled = True
    self.MRIstopScanButton.setMaximumWidth(250)
    scannerServerFormLayout.addWidget(self.MRIstopScanButton, 3, 1)
    self.MRIstopScanButton.connect('clicked()', self.onMRIStopScanButtonClicked)

    # Add 1 line of spacing
    scannerServerFormLayout.addWidget(qt.QLabel(" "), 4, 0)

    # Dropdown section for scan plane selection
    self.updateScanPlaneCollapsibleButton = ctk.ctkCollapsibleButton()
    self.updateScanPlaneCollapsibleButton.text = "Update Scan Plane"
    self.updateScanPlaneCollapsibleButton.collapsed = True
    scannerServerFormLayout.addWidget(self.updateScanPlaneCollapsibleButton, 5, 0, 1, 2)

    # Layout within the path collapsible button
    updateScanPlaneLayout = qt.QVBoxLayout(self.updateScanPlaneCollapsibleButton)

    # Create a new QHBoxLayout() within updateScanPlaneLayout to format the file selection dropdown
    updateScanPlaneLayoutMiddle1 = qt.QFormLayout()
    updateScanPlaneLayout.addLayout(updateScanPlaneLayoutMiddle1)

    # Input scan plane transform
    self.scanPlaneTransformSelector = slicer.qMRMLNodeComboBox()
    self.scanPlaneTransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.scanPlaneTransformSelector.selectNodeUponCreation = False
    self.scanPlaneTransformSelector.noneEnabled = False
    self.scanPlaneTransformSelector.addEnabled = True
    self.scanPlaneTransformSelector.removeEnabled = True
    self.scanPlaneTransformSelector.setMRMLScene(slicer.mrmlScene)
    updateScanPlaneLayoutMiddle1.addRow("Scan Plane Transform: ", self.scanPlaneTransformSelector)

    # Create a new QHBoxLayout() within updateScanPlaneLayout to format the dropdown & Update Scan Plane button
    updateScanPlaneLayoutMiddle2 = qt.QFormLayout()
    updateScanPlaneLayout.addLayout(updateScanPlaneLayoutMiddle2)

    self.scanPlaneTransform = slicer.vtkMRMLLinearTransformNode()
    self.scanPlaneTransform.SetName("PLANE_0")
    slicer.mrmlScene.AddNode(self.scanPlaneTransform)
    self.scanPlaneTransformSelector.setCurrentNode(self.scanPlaneTransform)

    # self.scanPlaneTransformOrientation = slicer.vtkMRMLLinearTransformNode()
    # self.scanPlaneTransformOrientation.SetName("PLANE_0_Orientation")
    # slicer.mrmlScene.AddNode(self.scanPlaneTransformOrientation)

    self.scanPlaneRobotPositionCheckbox = qt.QCheckBox("Follow current robot position with scan plane")
    self.scanPlaneRobotPositionCheckbox.setChecked(False)
    updateScanPlaneLayout.addWidget(self.scanPlaneRobotPositionCheckbox)

    # MRI Start Updating scan target button
    self.MRIupdateTargetButton = qt.QPushButton("Start Observing Transform")
    self.MRIupdateTargetButton.toolTip = "Start sending transform to scanner"
    self.MRIupdateTargetButton.enabled = True
    updateScanPlaneLayoutMiddle2.addWidget(self.MRIupdateTargetButton)
    self.MRIupdateTargetButton.connect('clicked()', self.onMRIUpdateTargetButtonClicked)

    # MRI Stop Updating scan target button
    self.MRIStopupdateTargetButton = qt.QPushButton("Stop Observing Transform")
    self.MRIStopupdateTargetButton.toolTip = "Stop sending transform to scanner"
    self.MRIStopupdateTargetButton.enabled = True
    updateScanPlaneLayoutMiddle2.addWidget(self.MRIStopupdateTargetButton)
    self.MRIStopupdateTargetButton.connect('clicked()', self.onMRIStopUpdateTargetButtonClicked)

    self.MRIfpsBox = qt.QSpinBox()
    self.MRIfpsBox.setSingleStep(1)
    self.MRIfpsBox.setMaximum(144)
    self.MRIfpsBox.setMinimum(1)
    self.MRIfpsBox.setSuffix(" FPS")
    self.MRIfpsBox.value = 2
    updateScanPlaneLayoutMiddle2.addRow("Update Transform Rate:", self.MRIfpsBox)

    self.lastTransformMatrix = vtk.vtkMatrix4x4()
    self.lastTransformMatrix.SetElement(0,0,0)
    self.lastTransformMatrix.SetElement(1,1,0)
    self.lastTransformMatrix.SetElement(2,2,0)    

    self.MRIUpdateTimer = qt.QTimer()
    self.MRIUpdateTimer.timeout.connect(self.updateMRITransformToScanner)

    updateScanPlaneLayoutOrientationLayout = qt.QGridLayout()
    updateScanPlaneLayout.addLayout(updateScanPlaneLayoutOrientationLayout)

    self.axialScanPlaneButton = qt.QPushButton("AXIAL")
    self.axialScanPlaneButton.toolTip = "Update scan plane for Axial orientation."
    self.axialScanPlaneButton.enabled = True
    self.axialScanPlaneButton.setMaximumWidth(250)
    updateScanPlaneLayoutOrientationLayout.addWidget(self.axialScanPlaneButton, 0, 0)
    self.axialScanPlaneButton.connect('clicked()', self.onAxialScanPlaneButtonClicked)

    self.coronalScanPlaneButton = qt.QPushButton("CORONAL")
    self.coronalScanPlaneButton.toolTip = "Update scan plane for Coronal orientation."
    self.coronalScanPlaneButton.enabled = True
    self.coronalScanPlaneButton.setMaximumWidth(250)
    updateScanPlaneLayoutOrientationLayout.addWidget(self.coronalScanPlaneButton, 0, 1)
    self.coronalScanPlaneButton.connect('clicked()', self.onCoronalScanPlaneButtonClicked)

    self.sagittalScanPlaneButton = qt.QPushButton("SAGITTAL")
    self.sagittalScanPlaneButton.toolTip = "Update scan plane for Sagittal orientation."
    self.sagittalScanPlaneButton.enabled = True
    self.sagittalScanPlaneButton.setMaximumWidth(250)
    updateScanPlaneLayoutOrientationLayout.addWidget(self.sagittalScanPlaneButton, 0, 2)
    self.sagittalScanPlaneButton.connect('clicked()', self.onSagittalScanPlaneButtonClicked)

    # ------------------------------------ Log UI ---------------------------------------
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

    # Empty nodes for planning and calibration steps
    # self.outputTransform = None
    # self.plannedTargetTransform = None
    self.reachableTargetTransform = None
    self.currentPositionTransform = None
    self.otsuFilter = sitk.OtsuThresholdImageFilter()
    self.zFrameFidsString = '' # For manual selection of zframe fiducial locations
    self.templateVolume = None
    self.zFrameCroppedVolume = None
    self.zFrameLabelVolume = None
    self.zFrameMaskedVolume = None
    self.otsuOutputVolume = None
    self.startIndex = None
    self.endIndex = None
    self.zFrameModelNode = None
    self.robotModelNode = None

  def removeNodeByName(self, nodeName):
    nodes = slicer.util.getNodes(nodeName)
    for node in nodes.values():
      slicer.mrmlScene.RemoveNode(node)

  def createServerInitializationStep(self):
    # Prevent re-initialization
    self.firstServer = False

    # Create a .txt document for the command log
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    self.commandLogFilePath = os.path.join(currentFilePath, "commandLogs.txt")
    with open(self.commandLogFilePath,"a") as f:
      f.write('\n----------------- New session started on ' + datetime.datetime.now().strftime("%d/%m/%Y at %H:%M:%S:%f") + ' -----------------\n')

    # Make a node for each message type 
    # Create nodes to receive string, status, and transform messages
    # ReceivedStringMsg = slicer.vtkMRMLTextNode()
    # ReceivedStringMsg.SetName("StringMessage")
    # slicer.mrmlScene.AddNode(ReceivedStringMsg)

    # ReceivedStatusMsg = slicer.vtkMRMLIGTLStatusNode()
    # ReceivedStatusMsg.SetName("StatusMessage")
    # slicer.mrmlScene.AddNode(ReceivedStatusMsg)

    ReceivedACKTransformMsg = slicer.vtkMRMLLinearTransformNode()
    ReceivedACKTransformMsg.SetName("ACK_Transform")
    slicer.mrmlScene.AddNode(ReceivedACKTransformMsg)

    ReceivedTargetTransformMsg = slicer.vtkMRMLLinearTransformNode()
    ReceivedTargetTransformMsg.SetName("REACHABLE_TARGET")
    slicer.mrmlScene.AddNode(ReceivedTargetTransformMsg)

    ReceivedPositionTransformMsg = slicer.vtkMRMLLinearTransformNode()
    ReceivedPositionTransformMsg.SetName("CURRENT_POSITION")
    slicer.mrmlScene.AddNode(ReceivedPositionTransformMsg)    

    # Add observers on the message type nodes
    self.nodeAddedObserver = slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.onMRMLNodeAdded) # Check newly added MRML nodes from OpenIGTLink to modify StringMsg
    self.onACKTransformNodeModifiedObserver = ReceivedACKTransformMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onACKTransformNodeModified)
    self.onTargetTransformNodeModifiedObserver = ReceivedTargetTransformMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTargetTransformMessageNodeModified)
    self.onPositionTransformNodeModifiedObserver = ReceivedPositionTransformMsg.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onPositionTransformNodeModified)

    # Create a node for sending transforms
    SendTransformNode = slicer.vtkMRMLLinearTransformNode()
    SendTransformNode.SetName("SendTransform")
    slicer.mrmlScene.AddNode(SendTransformNode)

    # Initialize variables 
    self.start = 0
    self.transformType = ""
    self.last_randomIDname_transform = "SendTransform"

  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onMRMLNodeAdded(self, caller, event, calldata):
    calledNode = calldata
    if isinstance(calledNode, slicer.vtkMRMLTextNode):
      if calledNode.GetName()[:4] == "ACK_":
        qt.QTimer.singleShot(10, lambda: self.onACKMessage(calledNode)) # Allow node to fully load
    elif isinstance(calledNode, slicer.vtkMRMLIGTLStatusNode):
      qt.QTimer.singleShot(100, lambda: self.onStatusMessage(calledNode)) # Allow node to fully load
    elif isinstance(calledNode, slicer.vtkMRMLLinearTransformNode) and calledNode.GetName().startswith("ACK"):
      qt.QTimer.singleShot(100, lambda: self.updateACKTransformMessage(calledNode))        
        
  def onACKMessage(self, calledNode):
    stringMessageName = calledNode.GetName() # example: ACK_###########
    stringMessageText = calledNode.GetText() # example: START_UP
    infoMsg = "Received ACK message from Robot: ( " + stringMessageName + ", " + stringMessageText + " )"
    self.appendReceivedMessageToCommandLog(infoMsg)
    self.robotMessageTextbox.setText(stringMessageText)
    #re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    timestampID = stringMessageName[4:]
    cmdNode = slicer.util.getNode(f'CMD_{timestampID}')
    cmdNode.SetAttribute("ACK", "1")
    self.phaseTextbox.setText(stringMessageText)
    self.phaseTextbox.setStyleSheet("color: rgb(0, 0, 255);") # Sets phase name in blue

  def onStatusMessage(self, calledNode):
    print(calledNode.GetCode(), calledNode.GetSubCode())
    statusMessageStatusString = calledNode.GetName()
    statusMessageError = calledNode.GetErrorName()
    statusMessageCode = calledNode.GetCode()
    self.robotStatusCodeTextbox.setText(self.status_codes[statusMessageCode])
    infoMsg =  "Received STATUS from Robot: ( " + statusMessageStatusString + ", " + self.status_codes[statusMessageCode] + " )"
    self.appendReceivedMessageToCommandLog(infoMsg)
    cmdNodes = slicer.util.getNodes("CMD_*")
    if statusMessageStatusString == "CURRENT_STATUS":
      print(f'CURRENT_STATUS: {self.status_codes[statusMessageCode]}')
    elif statusMessageStatusString == "START_UP":
      if statusMessageCode == 1:
        for name, node in cmdNodes.items():
          print(node.GetText() == "START_UP", node.GetAttribute("ACK"))
          if node.GetText() == "START_UP":
            if node.GetAttribute("ACK") == "1":
              print("Robot sucessfully achieved: ", statusMessageStatusString)
              self.phaseTextbox.setText(statusMessageStatusString)
              self.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green

              # Perform phase actions
              self.activateButtons()
              self.RetractNeedleButton.enabled = False

              # Remove nodes now that phase change achieved
              timestampID = name[4:]
              ackNode = slicer.util.getNode(f'ACK_{timestampID}')
              slicer.mrmlScene.RemoveNode(ackNode)
              slicer.mrmlScene.RemoveNode(node)

              self.robot_phase = "START_UP"
              break
            else:
              print(f'Acknowdgement for {name} not received. Unable to change phase.')
      else:
        print(f'Error: {self.status_codes[statusMessageCode]}')
    elif statusMessageStatusString == "CALIBRATION":
      if statusMessageCode == 1:
        for name, node in cmdNodes.items():
          if node.GetText() == "CALIBRATION":
            if node.GetAttribute("ACK") == "1":
              print("Robot sucessfully achieved: ", statusMessageStatusString)
              self.phaseTextbox.setText(statusMessageStatusString)
              self.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green

              # Perform phase actions
              # Show Calibration matrix GUI in the module
              self.calibrationCollapsibleButton.collapsed = False
              self.RetractNeedleButton.enabled = False

              # Remove nodes now that phase change achieved
              timestampID = name[4:]
              ackNode = slicer.util.getNode(f'ACK_{timestampID}')
              slicer.mrmlScene.RemoveNode(ackNode)
              slicer.mrmlScene.RemoveNode(node)

              self.robot_phase = "CALIBRATION"
              break
            else:
              print(f'Acknowdgement for {name} not received. Unable to change phase.')
      else:
        print(f'Error: {self.status_codes[statusMessageCode]}')
    elif statusMessageStatusString == "PLANNING":
      if statusMessageCode == 1:
        for name, node in cmdNodes.items():
          if node.GetText() == "PLANNING":
            if node.GetAttribute("ACK") == "1":
              print("Robot sucessfully achieved: ", statusMessageStatusString)
              self.phaseTextbox.setText(statusMessageStatusString)
              self.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green

              # Perform phase actions
              # Show planning GUI, hide calibration GUI and target point GUI
              self.planningCollapsibleButton.collapsed = False
              self.calibrationCollapsibleButton.collapsed = True
              self.RetractNeedleButton.enabled = False

              # Remove nodes now that phase change achieved
              timestampID = name[4:]
              ackNode = slicer.util.getNode(f'ACK_{timestampID}')
              slicer.mrmlScene.RemoveNode(ackNode)
              slicer.mrmlScene.RemoveNode(node)

              self.robot_phase = "PLANNING"
              break
            else:
              print(f'Acknowdgement for {name} not received. Unable to change phase.')
      else:
        print(f'Error: {self.status_codes[statusMessageCode]}')
    elif statusMessageStatusString == "TARGETING":
      if statusMessageCode == 1:
        for name, node in cmdNodes.items():
          if node.GetText() == "TARGETING":
            if node.GetAttribute("ACK") == "1":
              print("Robot sucessfully achieved: ", statusMessageStatusString)
              self.phaseTextbox.setText(statusMessageStatusString)
              self.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green

              # Perform phase actions
              self.sendTargetTransform()

              # Remove nodes now that phase change achieved
              timestampID = name[4:]
              ackNode = slicer.util.getNode(f'ACK_{timestampID}')
              slicer.mrmlScene.RemoveNode(ackNode)
              slicer.mrmlScene.RemoveNode(node)

              self.robot_phase = "TARGETING"
              break
            else:
              print(f'Acknowdgement for {name} not received. Unable to change phase.')
      else:
        print(f'Error: {self.status_codes[statusMessageCode]}')
    elif statusMessageStatusString == "MOVE_TO_TARGET":
      if statusMessageCode == 1:
        for name, node in cmdNodes.items():
          if node.GetText() == "MOVE_TO_TARGET":
            if node.GetAttribute("ACK") == "1":
              print("Robot sucessfully achieved: ", statusMessageStatusString)
              self.phaseTextbox.setText(statusMessageStatusString)
              self.phaseTextbox.setStyleSheet("color: rgb(0, 255, 0);") # Sets phase name in green

              # Perform phase actions
              # Hide Calibration, Planning, and Targetting GUIs
              self.calibrationCollapsibleButton.collapsed = True
              self.planningCollapsibleButton.collapsed = True
              self.RetractNeedleButton.enabled = True

              # Start Needle Tip Tracking Function
              #self.startTrackedTipTimer()
              self.needleTipTransformObserver = self.needleTipTransformComboBox.currentNode().AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onSendTrackedTipTransform)

              # Remove nodes now that phase change achieved
              timestampID = name[4:]
              ackNode = slicer.util.getNode(f'ACK_{timestampID}')
              slicer.mrmlScene.RemoveNode(ackNode)
              slicer.mrmlScene.RemoveNode(node)
              
              self.robot_phase = "MOVE_TO_TARGET"
              break
            else:
              print(f'Acknowdgement for {name} not received. Unable to change phase.')  
      else:
        print(f'Error: {self.status_codes[statusMessageCode]}')
    # Remove status node to allow a new status node to be loaded
    slicer.mrmlScene.RemoveNode(calledNode)                

  def updateACKTransformMessage(self, calledNode):
    print(calledNode)
    ReceivedACKTransformMsg = slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")
    matrix = vtk.vtkMatrix4x4()
    calledNode.GetMatrixTransformToParent(matrix)
    ReceivedACKTransformMsg.SetAndObserveMatrixTransformToParent(matrix)
    slicer.mrmlScene.RemoveNode(calledNode)

  def onCreateRobotClientButtonClicked(self):
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
    #VisualFeedback: color in gray when server is created
    self.snrPortTextboxLabel.setStyleSheet('color: rgb(195,195,195)')
    self.snrHostnameTextboxLabel.setStyleSheet('color: rgb(195,195,195)')
    self.snrPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: rgb(195,195,195) }""")
    self.snrHostnameTextbox.setStyleSheet("""QLineEdit { background-color: white; color: rgb(195,195,195) }""")

    # Initialize the IGTLink Slicer-side server component
    self.openIGTNode = slicer.vtkMRMLIGTLConnectorNode()
    slicer.mrmlScene.AddNode(self.openIGTNode)
    self.openIGTNode.SetTypeServer(int(snrPort)) #snrHostname,
    self.openIGTNode.Start()

    if self.firstServer:
      self.createServerInitializationStep()

  def onDisconnectFromSocketButtonClicked(self):
    # GUI changes to enable/disable button functionality
    self.disconnectFromSocketButton.enabled = False
    self.createServerButton.enabled = True
    self.snrPortTextbox.setReadOnly(False)
    self.snrHostnameTextbox.setReadOnly(False)
    self.RobotCommunicationCollapsibleButton.collapsed = True
    self.infoCollapsibleButton.collapsed = True
    self.calibrationCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True

    # Stop querying robot position
    self.getTransformTimer.stop()
    self.getTransformFPSBox.enabled = True
    self.currentPositionButton.setChecked(False)
    
    # Close socket
    if self.openIGTNode:
      self.openIGTNode.Stop()

    self.snrPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")
    self.snrHostnameTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")

    if self.getTransformNode:
      slicer.mrmlScene.RemoveNode(self.getTransformNode)
      self.getTransformNode = None

    # Clear textboxes
    self.robotMessageTextbox.setText("No message received")
    self.robotStatusCodeTextbox.setText("No status code received")
    self.phaseTextbox.setText("")
   
    # Clear tables
    for i in range(4):
      for j in range(4):
        self.robotTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
        self.robotPositionTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
        self.targetTableWidget.setItem(i,j,qt.QTableWidgetItem(" "))
   
    slicer.mrmlScene.RemoveNode(self.openIGTNode)

  def onCreateScannerServerButtonClicked(self):
    self.createScannerServerButton.enabled = False
    self.disconnectFromScannerSocketButton.enabled = True
    self.scannerPortTextbox.setReadOnly(True)
    self.MRICommunicationCollapsibleButton.collapsed = False
    self.infoCollapsibleButton.collapsed = False

    scannerPort = self.scannerPortTextbox.text
    #VisualFeedback: color in gray when server is created
    self.scannerPortTextboxLabel.setStyleSheet('color: rgb(195,195,195)')
    self.scannerPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: rgb(195,195,195) }""")

    # Initialize the IGTLink Slicer-side server component
    self.openIGTNode_Scanner = slicer.vtkMRMLIGTLConnectorNode()
    slicer.mrmlScene.AddNode(self.openIGTNode_Scanner)
    self.openIGTNode_Scanner.SetTypeServer(int(scannerPort))
    self.openIGTNode_Scanner.Start()
    print("Scanner OpenIGT node: ", self.openIGTNode_Scanner)

    if self.firstServer:
      self.createServerInitializationStep()
  
  def onDisconnectFromScannerSocketButtonClicked(self):
    self.createScannerServerButton.enabled = True
    self.disconnectFromScannerSocketButton.enabled = False
    self.scannerPortTextbox.setReadOnly(False)
    self.scannerPortTextboxLabel.setStyleSheet('color: black')
    self.scannerPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")

    # GUI changes to enable/disable button functionality
    self.disconnectFromScannerSocketButton.enabled = False
    self.createScannerServerButton.enabled = True
    self.scannerPortTextbox.setReadOnly(False)
    # self.RobotCommunicationCollapsibleButton.collapsed = True
    self.MRICommunicationCollapsibleButton.collapsed = True
    self.infoCollapsibleButton.collapsed = True
    self.calibrationCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True

    # Stop MRI Update timer if running
    self.onMRIStopUpdateTargetButtonClicked()

    # Close socket
    self.openIGTNode_Scanner.Stop()
    self.scannerPortTextboxLabel.setStyleSheet('color: black')
    self.scannerPortTextbox.setStyleSheet("""QLineEdit { background-color: white; color: black }""")

    # Delete all nodes from the scene
    slicer.mrmlScene.RemoveNode(self.openIGTNode_Scanner)
    #slicer.mrmlScene.Clear(0) 
  
  def generateTimestampNameID(self, last_prefix_sent):
    timestampID = [last_prefix_sent, "_"]
    currentTime = datetime.datetime.now()
    timestampID.append(currentTime.strftime("%H%M%S%f"))
    timestampIDname = ''.join(timestampID)
    return timestampIDname

  # Command logging
  def appendSentMessageToCommandLog(self, timestampIDname, infoMsg, receiver):
    if timestampIDname.split("_")[0] == "TARGET":
      tempTimestamp  = datetime.datetime.strptime(timestampIDname.split("_")[2], "%H%M%S%f")
    else: 
      tempTimestamp = datetime.datetime.strptime(timestampIDname.split("_")[1], "%H%M%S%f")
    timestamp = tempTimestamp.strftime("%H:%M:%S:%f")
    # Append to commandLogs.txt
    with open(self.commandLogFilePath,"a") as f:
      f.write(timestamp + " -- " + infoMsg + " to " + receiver + '\n')

    # Append to Slicer module GUI command logging box
    currentInfoText = self.infoTextbox.toPlainText()
    if "CURRENT_POSITION" not in infoMsg:
      self.infoTextbox.append(f"{timestamp} -- {infoMsg} to {receiver} \n")
      self.infoTextbox.verticalScrollBar().setValue(self.infoTextbox.verticalScrollBar().maximum)

  def appendReceivedMessageToCommandLog(self, rcvdMsg):
    currentInfoText = self.infoTextbox.toPlainText()
    with open(self.commandLogFilePath,"a") as f:
      if rcvdMsg.split("_")[0] == "ACK": # NO- CHANGE
        f.write("   -- Acknowledgment received for command: " + rcvdMsg)
        self.infoTextbox.append(f"   -- Acknowledgment received for command: {rcvdMsg}\n")
        self.infoTextbox.verticalScrollBar().setValue(self.infoTextbox.verticalScrollBar().maximum)
      elif rcvdMsg.split(' ')[0] == "Received" or rcvdMsg.split(' ')[0] == "TRANSFORM":
        f.write("   -- " + rcvdMsg + '\n')
        self.infoTextbox.append(f"   --  {rcvdMsg} \n")
        self.infoTextbox.verticalScrollBar().setValue(self.infoTextbox.verticalScrollBar().maximum)
      elif rcvdMsg == "REACHABLE_TARGET":
        f.write("   -- Received TRANSFORM from WPI: ( REACHABLE_TARGET )\n")
        self.infoTextbox.append(f"   -- Received TRANSFORM from WPI: ( REACHABLE_TARGET )\n")
        self.infoTextbox.verticalScrollBar().setValue(self.infoTextbox.verticalScrollBar().maximum)
      elif rcvdMsg == "CURRENT_POSITION":
        f.write("   -- Received TRANSFORM from WPI: ( CURRENT_POSTION )\n")
        self.infoTextbox.append(f"   -- Received TRANSFORM from WPI: ( CURRENT_POSITION )\n")
        self.infoTextbox.verticalScrollBar().setValue(self.infoTextbox.verticalScrollBar().maximum)
      else:
        f.write("Unsupported message. Modify appendReceivedMessageToCommandLog accordingly.\n")

  def appendTransformToCommandLog(self, outputMatrix):
    with open(self.commandLogFilePath,"a") as f:
      f.write ("[" + str(round(outputMatrix.GetElement(0,0),2)) + ", " + str(round(outputMatrix.GetElement(0,1),2)) + ", " + str(round(outputMatrix.GetElement(0,2),2)) + ", " + str(round(outputMatrix.GetElement(0,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(1,0),2)) + ", " + str(round(outputMatrix.GetElement(1,1),2)) + ", " + str(round(outputMatrix.GetElement(1,2),2)) + ", " + str(round(outputMatrix.GetElement(1,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(2,0),2)) + ", " + str(round(outputMatrix.GetElement(2,1),2)) + ", " + str(round(outputMatrix.GetElement(2,2),2)) + ", " + str(round(outputMatrix.GetElement(2,3),2)) + "]\n")
      f.write ("[" + str(round(outputMatrix.GetElement(3,0),2)) + ", " + str(round(outputMatrix.GetElement(3,1),2)) + ", " + str(round(outputMatrix.GetElement(3,2),2)) + ", " + str(round(outputMatrix.GetElement(3,3),2)) + "]\n")

    # Append to Slicer module GUI command logging box
    currentInfoText = self.infoTextbox.toPlainText()

  def activateButtons(self):
    self.planningButton.enabled = True
    self.EmergencyButton.enabled = True
    self.StopButton.enabled = True
    self.moveButton.enabled = True
    self.targetingButton.enabled = True
    self.calibrationButton.enabled = True
    #self.GetStatusButton.enabled = True
    self.RetractNeedleButton.enabled = False
    self.currentPositionButton.enabled = True
    self.currentPositionButton.setChecked(False)

  def deactivateButtons(self):
    self.planningButton.enabled = False
    self.EmergencyButton.enabled = False
    self.StopButton.enabled = False
    self.moveButton.enabled = False
    self.targetingButton.enabled = False
    self.calibrationButton.enabled = False
    #self.GetStatusButton.enabled = False
    self.RetractNeedleButton.enabled = False
    self.currentPositionButton.enabled = False
    self.currentPositionButton.setChecked(False)
   
  # def onGetStatusButtonClicked(self):
  #   # Send stringMessage containing the command "GET STATUS" to the script via IGTLink
  #   print("Send command to get current status of the robot")
  #   getStatusNode = slicer.vtkMRMLIGTLQueryNode()
  #   getStatusNode.SetIGTLDeviceName("STATUS")
  #   getStatusNode.SetQueryType(1) # Query type "1" corresponds with "GET"; Query type "2" corresponds with "START"; Query type 3 corresponds with "STOP"
  #   getStatusNode.SetIGTLName("GET")
  #   slicer.mrmlScene.AddNode(getStatusNode)
  #   self.openIGTNode.RegisterOutgoingMRMLNode(getStatusNode)
  #   self.openIGTNode.PushNode(getStatusNode)

  def updateGetTransform(self):
    # Send stringMessage containing the command "GET POSE" to the script via IGTLink
    if self.getTransformNode is None:
      self.getTransformNode = slicer.vtkMRMLTextNode()
      self.getTransformNode.SetName("CURRENT_POSITION")
      self.getTransformNode.SetText("CURRENT_POSITION")
      self.getTransformNode.SetEncoding(3)
      slicer.mrmlScene.AddNode(self.getTransformNode)
      self.openIGTNode.RegisterOutgoingMRMLNode(self.getTransformNode)
    # print("Send command to get current position of the robot")
    timestampIDname = self.generateTimestampNameID("CMD")
    self.openIGTNode.PushNode(self.getTransformNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  CURRENT_POSITION )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onTargetingButtonClicked(self):
    # Send stringMessage containing the command "TARGETING" to the script via IGTLink
    print("Sending targeting command to WPI robot")
    targetingNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    targetingNode.SetName(timestampIDname)
    targetingNode.SetText("TARGETING")
    targetingNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(targetingNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(targetingNode)
    self.openIGTNode.PushNode(targetingNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  TARGETING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")
    
    # Hide calibration and planning GUIs
    self.calibrationCollapsibleButton.collapsed = True
    self.planningCollapsibleButton.collapsed = True
    self.RetractNeedleButton.enabled = False

  def onMoveButtonClicked(self):
    # Send stringMessage containing the command "MOVE" to the script via IGTLink
    print("Send command to ask robot to move to target")
    moveNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    moveNode.SetName(timestampIDname)
    moveNode.SetText("MOVE_TO_TARGET")
    moveNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(moveNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(moveNode)
    self.openIGTNode.PushNode(moveNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  MOVE_TO_TARGET )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")
  
  def onCalibrationButtonClicked(self):
    # Send stringMessage containing the command "CALIBRATION" to the script via IGTLink
    print("Sending calibration command to WPI robot")
    calibrationNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    calibrationNode.SetName(timestampIDname)
    calibrationNode.SetText("CALIBRATION")
    calibrationNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(calibrationNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(calibrationNode)
    self.openIGTNode.PushNode(calibrationNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  CALIBRATION )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onPlanningButtonClicked(self):
    # Send stringMessage containing the command "PLANNING" to the script via IGTLink
    print("Sending planning command to WPI robot")
    planningNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    planningNode.SetName(timestampIDname)
    planningNode.SetText("PLANNING")
    planningNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(planningNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(planningNode)
    self.openIGTNode.PushNode(planningNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  PLANNING )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onRetractNeedleButtonClicked(self):
    # Send stringMessage containing the command "GET POSE" to the script via IGTLink
    if self.retractNeedleNode is None:
      self.retractNeedleNode = slicer.vtkMRMLTextNode()
      self.retractNeedleNode.SetName("RETRACT_NEEDLE")
      self.retractNeedleNode.SetText("RETRACT_NEEDLE")
      self.retractNeedleNode.SetEncoding(3)
      slicer.mrmlScene.AddNode(self.retractNeedleNode)
      self.openIGTNode.RegisterOutgoingMRMLNode(self.retractNeedleNode)
    # print("Send command to get current position of the robot")
    timestampIDname = self.generateTimestampNameID("CMD")
    self.openIGTNode.PushNode(self.retractNeedleNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  RETRACT_NEEDLE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onStopButtonClicked(self):
    print("Sending Stop command")
    # Send stringMessage containing the command "STOP" to the script via IGTLink
    stopNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    stopNode.SetName(timestampIDname)
    stopNode.SetText("STOP")
    stopNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(stopNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(stopNode)
    self.openIGTNode.PushNode(stopNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  STOP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onEmergencyButtonClicked(self):
    # Stop querying robot position
    self.getTransformTimer.stop()
    self.getTransformFPSBox.enabled = True
    self.currentPositionButton.setChecked(False)

    # Send stringMessage containing the command "STOP" to the script via IGTLink
    print("Sending Emergency command")
    emergencyNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    emergencyNode.SetName(timestampIDname)
    emergencyNode.SetText("EMERGENCY")
    emergencyNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(emergencyNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(emergencyNode)
    self.openIGTNode.PushNode(emergencyNode)
    self.start = time.time()
    self.deactivateButtons()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  EMERGENCY )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onStartupButtonClicked(self):
    # Stop querying robot position
    self.getTransformTimer.stop()
    self.getTransformFPSBox.enabled = True
    self.currentPositionButton.setChecked(False)

    # Send stringMessage containing the command "START_UP" via IGTLink
    # Create a text node representing a pending request to change phase
    startupNode = slicer.vtkMRMLTextNode()
    timestampIDname = self.generateTimestampNameID("CMD")
    startupNode.SetName(timestampIDname)
    startupNode.SetText("START_UP")
    startupNode.SetAttribute("ACK", "0")
    startupNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(startupNode)
    self.openIGTNode.RegisterOutgoingMRMLNode(startupNode)
    self.openIGTNode.PushNode(startupNode)
    self.start = time.time()
    infoMsg =  "Sending STRING( " + timestampIDname + ",  START_UP )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")

  def onCurrentPositionClicked(self):
    if self.currentPositionButton.isChecked():
      # Start querying robot position
      self.getTransformTimer.start(int(1000/int(self.getTransformFPSBox.value)))
      self.getTransformFPSBox.enabled = False
    else:
      # Stop querying robot position
      self.getTransformTimer.stop()
      self.getTransformFPSBox.enabled = True

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
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedleTrajectory")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)

  def onPlannedTrajectoryVisibleButtonClicked(self):
    # If button is checked
    if (self.targetNeedleTrajectoryVisibleButton.isChecked()):
      # Add dashed line for needle trajectory
      if slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedleTrajectory") is not None:
        PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedleTrajectory")
        slicer.mrmlScene.RemoveNode(PointerNodeToRemove)
      self.AddNeedleTrajectoryLine("PlannedTargetNeedleTrajectory")
      TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetTransform")
      locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedleTrajectory")
      locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())

    # If it is unchecked
    else:
      # Remove line for needle trajectory
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("PlannedTargetNeedleTrajectory")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)

  def onReachableTargetTransformReceived(self, reachableTargetMatrix):
    self.appendTransformToCommandLog(reachableTargetMatrix)
    # Update self.reachableTargetTransform s.t. it contains the REACHABLE_TARGET message sent by WPI
    if self.reachableTargetTransform:
      slicer.mrmlScene.RemoveNode(self.reachableTargetTransform)
      self.reachableTargetTransform = None
    self.reachableTargetTransform = slicer.vtkMRMLLinearTransformNode()
    self.reachableTargetTransform.SetName("ReachableTargetTransform")
    self.reachableTargetTransform.SetMatrixTransformToParent(reachableTargetMatrix)
    slicer.mrmlScene.AddNode(self.reachableTargetTransform)

    # Add reachable target model to Slicer GUI
    if slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle") is not None:
      PointerNodeToRemove = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle")
      slicer.mrmlScene.RemoveNode(PointerNodeToRemove)
    self.AddPointerModel("ReachableTargetNeedle")
    TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetTransform")
    locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("ReachableTargetNeedle")
    locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())

  # TODO: Can be done without removing and adding again
  def onCurrentPositionTransformReceived(self, currentPositionMatrix):
    self.appendTransformToCommandLog(currentPositionMatrix)

    # Update self.currentPositionTransform s.t. it contains the CURRENT_POSITION message sent by WPI
    if self.currentPositionTransform is None:
      self.currentPositionTransform = slicer.vtkMRMLLinearTransformNode()
      self.currentPositionTransform.SetName("CurrentPositionTransform")
      slicer.mrmlScene.AddNode(self.currentPositionTransform)
    
    #Remove roll component
    R = np.array([[currentPositionMatrix.GetElement(0,0), currentPositionMatrix.GetElement(0,1), currentPositionMatrix.GetElement(0,2)],
    [currentPositionMatrix.GetElement(1,0), currentPositionMatrix.GetElement(1,1), currentPositionMatrix.GetElement(1,2)],
    [currentPositionMatrix.GetElement(2,0), currentPositionMatrix.GetElement(2,1), currentPositionMatrix.GetElement(2,2)]])
    
    roll = math.atan2(currentPositionMatrix.GetElement(1,0), currentPositionMatrix.GetElement(0,0))
    #print(np.rad2deg(roll))
    
    Rz = np.array([[math.cos(-roll), -math.sin(-roll), 0],[math.sin(-roll), math.cos(-roll), 0],[0, 0, 1]])

    # Multiply the orientation matrix by the rotation matrix to remove the roll component
    R_no_roll = np.dot(R, Rz)
    
    currentPositionMatrix.SetElement(0,0,R_no_roll[0][0]); currentPositionMatrix.SetElement(0,1,R_no_roll[0][1]); currentPositionMatrix.SetElement(0,2,R_no_roll[0][2])
    currentPositionMatrix.SetElement(1,0,R_no_roll[1][0]); currentPositionMatrix.SetElement(1,1,R_no_roll[1][1]); currentPositionMatrix.SetElement(1,2,R_no_roll[1][2])
    currentPositionMatrix.SetElement(2,0,R_no_roll[2][0]); currentPositionMatrix.SetElement(2,1,R_no_roll[2][1]); currentPositionMatrix.SetElement(2,2,R_no_roll[2][2])
    
    self.currentPositionTransform.SetMatrixTransformToParent(currentPositionMatrix)

    if self.currentPositionBaseTransform is None:
      self.currentPositionBaseTransform = slicer.vtkMRMLLinearTransformNode()
      self.currentPositionBaseTransform.SetName("CurrentPositionBaseTransform")
      slicer.mrmlScene.AddNode(self.currentPositionBaseTransform)
    currentPositionBaseMatrix = vtk.vtkMatrix4x4()
    currentPositionBaseMatrix.DeepCopy(currentPositionMatrix)
    if self.outputTransform:
      registrationMatrix = vtk.vtkMatrix4x4()
      self.outputTransform.GetMatrixTransformToParent(registrationMatrix)
      currentPositionBaseMatrix.SetElement(2,3,registrationMatrix.GetElement(2,3))
    self.currentPositionBaseTransform.SetMatrixTransformToParent(currentPositionBaseMatrix)

    # Add current position needle model to Slicer GUI
    if slicer.mrmlScene.GetFirstNodeByName("CurrentPositionNeedle") is None:
      self.LoadCurrentPositionModel("CurrentPositionNeedle", "CurrentPositionBase")
    TransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionTransform")
    BaseTransformNodeToDisplay = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionBaseTransform")
    locatorModelNode = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionNeedle")
    locatorModelNode.SetAndObserveTransformNodeID(TransformNodeToDisplay.GetID())
    locatorBaseModelNode = slicer.mrmlScene.GetFirstNodeByName("CurrentPositionBase")
    locatorBaseModelNode.SetAndObserveTransformNodeID(BaseTransformNodeToDisplay.GetID())

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

  def onMRIStartScanButtonClicked(self):
    # Send stringMessage containing the command "START_SCAN" to the MR Scanner via IGTLink
    print("Sending start_scan command to MR Scanner")
    timestampIDname = self.generateTimestampNameID("CMD")
    startScanNode = slicer.vtkMRMLTextNode()
    startScanNode.SetName(timestampIDname)
    startScanNode.SetText("START_SEQUENCE")
    startScanNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(startScanNode)
    self.openIGTNode_Scanner.RegisterOutgoingMRMLNode(startScanNode)
    self.openIGTNode_Scanner.PushNode(startScanNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  START_SEQUENCE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "SCANNER")
    
  def onMRIStopScanButtonClicked(self):
    # Send stringMessage containing the command "STOP_SCAN" to the MR Scanner via IGTLink
    print("Sending stop_scan command to MR Scanner")
    timestampIDname = self.generateTimestampNameID("CMD")
    stopScanNode = slicer.vtkMRMLTextNode()
    stopScanNode.SetName(timestampIDname)
    stopScanNode.SetText("STOP_SEQUENCE")
    stopScanNode.SetEncoding(3)
    slicer.mrmlScene.AddNode(stopScanNode)
    self.openIGTNode_Scanner.RegisterOutgoingMRMLNode(stopScanNode)
    self.openIGTNode_Scanner.PushNode(stopScanNode)
    infoMsg =  "Sending STRING( " + timestampIDname + ",  STOP_SEQUENCE )"
    re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
    self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "SCANNER")

  def onMRIUpdateTargetButtonClicked(self, unusedArg2=None, unusedArg3=None):
    #self.scanPlaneTransformSelector.currentNode().DisableModifiedEventOn()
    #self.openIGTNode_Scanner.RegisterOutgoingMRMLNode(self.scanPlaneTransformSelector.currentNode())
    self.MRIUpdateTimer.start(int(1000/int(self.MRIfpsBox.value)))

  def onMRIStopUpdateTargetButtonClicked(self, unusedArg2=None, unusedArg3=None):
    self.MRIUpdateTimer.stop()
    self.lastTransformMatrix = vtk.vtkMatrix4x4()
    self.lastTransformMatrix.SetElement(0,0,0)
    self.lastTransformMatrix.SetElement(1,1,0)
    self.lastTransformMatrix.SetElement(2,2,0)
  
  def updateMRITransformToScanner(self, unusedArg2=None, unusedArg3=None):
    if self.lastTransformMatrix is None:
      self.lastTransformMatrix = vtk.vtkMatrix4x4()
      self.lastTransformMatrix.SetElement(0,0,0)
      self.lastTransformMatrix.SetElement(1,1,0)
      self.lastTransformMatrix.SetElement(2,2,0)

    m = vtk.vtkMatrix4x4()
    self.scanPlaneTransformSelector.currentNode().GetMatrixTransformToParent(m)
    
    if self.scanPlaneRobotPositionCheckbox.isChecked() and self.currentPositionTransform:
      currentPositionMatrix = vtk.vtkMatrix4x4()
      # or to world? Is current position under registration?
      self.currentPositionTransform.GetMatrixTransformToParent(currentPositionMatrix)
      m.SetElement(0, 3, currentPositionMatrix.GetElement(0, 3))
      m.SetElement(1, 3, currentPositionMatrix.GetElement(1, 3))
      m.SetElement(2, 3, currentPositionMatrix.GetElement(2, 3))
      self.scanPlaneTransformSelector.currentNode().SetMatrixTransformToParent(m)
    if not self.CompareMatrices(self.lastTransformMatrix, m):
      # Send transform message containing new MRI scanning target with prefix "PLANE"
      timestampIDname = self.generateTimestampNameID("PLANE")
      self.openIGTNode_Scanner.RegisterOutgoingMRMLNode(self.scanPlaneTransformSelector.currentNode())
      self.openIGTNode_Scanner.PushNode(self.scanPlaneTransformSelector.currentNode())
      self.openIGTNode_Scanner.UnregisterOutgoingMRMLNode(self.scanPlaneTransformSelector.currentNode())
      infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "SCANNER")
      self.lastTransformMatrix.DeepCopy(m)
    # # Input the current scan plane transform into the MRItableWidget
    # for i in range(4):
    #   for j in range(4):
    #     self.MRItableWidget.setItem(i , j, qt.QTableWidgetItem(str(round(self.scanPlaneTransform.GetMatrix.GetElement(i, j),2))))

  def onAxialScanPlaneButtonClicked(self):
    m = vtk.vtkMatrix4x4()
    self.scanPlaneTransformSelector.currentNode().GetMatrixTransformToParent(m)
    m.SetElement(0, 0, 1); m.SetElement(0, 1, 0); m.SetElement(0, 2, 0)
    m.SetElement(1, 0, 0); m.SetElement(1, 1, 1); m.SetElement(1, 2, 0)
    m.SetElement(2, 0, 0); m.SetElement(2, 1, 0); m.SetElement(2, 2, 1)
    self.scanPlaneTransformSelector.currentNode().SetMatrixTransformToParent(m)

  def onCoronalScanPlaneButtonClicked(self):
    m = vtk.vtkMatrix4x4()
    self.scanPlaneTransformSelector.currentNode().GetMatrixTransformToParent(m)
    m.SetElement(0, 0, 1); m.SetElement(0, 1, 0); m.SetElement(0, 2, 0)
    m.SetElement(1, 0, 0); m.SetElement(1, 1, 0); m.SetElement(1, 2, -1)
    m.SetElement(2, 0, 0); m.SetElement(2, 1, 1); m.SetElement(2, 2, 0)
    self.scanPlaneTransformSelector.currentNode().SetMatrixTransformToParent(m)

  def onSagittalScanPlaneButtonClicked(self):
    m = vtk.vtkMatrix4x4()
    self.scanPlaneTransformSelector.currentNode().GetMatrixTransformToParent(m)
    m.SetElement(0, 0, 0); m.SetElement(0, 1, 0); m.SetElement(0, 2, 1)
    m.SetElement(1, 0, 0); m.SetElement(1, 1, 1); m.SetElement(1, 2, 0)
    m.SetElement(2, 0, -1); m.SetElement(2, 1, 0); m.SetElement(2, 2, 0)
    self.scanPlaneTransformSelector.currentNode().SetMatrixTransformToParent(m)        

  def CompareMatrices(self, m, n):
    for i in range(0,4):
      for j in range(0,4):
        if m.GetElement(i,j) != n.GetElement(i,j):
          return False
    return True

  def onACKTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    print("New transform received")
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)

    # If the received transform is of type ACK_XXX, check if it matches the original transform sent to WPI
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
        if(transformNode.transformType == "ACK"):
          if(val != ref):
            same_transforms = 0
        transformNode.robotTableWidget.setItem(i , j, qt.QTableWidgetItem(str(val)))
    if not same_transforms:
      infoMsg =  "TRANSFORM received from WPI does NOT match transform sent"
      transformNode.appendReceivedMessageToCommandLog(infoMsg)
    else:
      infoMsg =  "TRANSFORM received from WPI matches transform sent"
      transformNode.appendReceivedMessageToCommandLog(infoMsg)

  def onTargetTransformMessageNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("REACHABLE_TARGET")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)

    nbRows = transformNode.robotTableWidget.rowCount
    nbColumns = transformNode.robotTableWidget.columnCount
    for i in range(nbRows):
      for j in range(nbColumns):
        transformNode.robotTableWidget.setItem(i , j, qt.QTableWidgetItem(str(transformMatrix.GetElement(i,j))))      
    transformNode.onReachableTargetTransformReceived(transformMatrix)

  def onPositionTransformNodeModified(transformNode, unusedArg2=None, unusedArg3=None):
    ReceivedTransformMsg = slicer.mrmlScene.GetFirstNodeByName("CURRENT_POSITION")
    transformMatrix = vtk.vtkMatrix4x4()
    ReceivedTransformMsg.GetMatrixTransformToParent(transformMatrix)

    nbRows = transformNode.robotPositionTableWidget.rowCount
    nbColumns = transformNode.robotPositionTableWidget.columnCount
    for i in range(nbRows):
      for j in range(nbColumns):
        transformNode.robotPositionTableWidget.setItem(i , j, qt.QTableWidgetItem(str(transformMatrix.GetElement(i,j))))           
    transformNode.onCurrentPositionTransformReceived(transformMatrix)       

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

  def LoadCurrentPositionModel(self, pointerModelName, pointerModelBaseName):
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    currentPositionPath = os.path.join(currentFilePath, "Resources", "robot", "needle.vtk")
    currentPositionModelNode = slicer.util.loadModel(currentPositionPath)
    currentPositionBasePath = os.path.join(currentFilePath, "Resources", "robot", "needleBase.vtk")
    currentPositionBaseModelNode = slicer.util.loadModel(currentPositionBasePath)    
    currentPositionModelNode.SetName(pointerModelName)
    currentPositionBaseModelNode.SetName(pointerModelBaseName)
    modelDisplayNode = currentPositionModelNode.GetDisplayNode()
    modelDisplayNode.SetOpacity(1.0)
    modelDisplayNode.SetColor(0.0, 1.0, 1.0)
    modelDisplayNode.SliceIntersectionVisibilityOn()
    baseModelDisplayNode = currentPositionBaseModelNode.GetDisplayNode()
    baseModelDisplayNode.SetOpacity(0.6)
    baseModelDisplayNode.SetColor(0.0, 0.5, 0.5)

  def removeOrientationComponent(self, transformNode):
    # Get the transformation matrix
    matrix = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToParent(matrix)

    # Set the orientation part of the matrix to identity
    for i in range(3):
        for j in range(3):
            if i == j:
                matrix.SetElement(i, j, 1)
            else:
                matrix.SetElement(i, j, 0)

    # Update the transform node
    transformNode.SetMatrixTransformToParent(matrix)

  def AddNeedleTrajectoryLine(self, modelNodeName):
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(2)
    points.SetPoint(0,   0, 0, 0)
    if modelNodeName == "PlannedTargetNeedleTrajectory":
      points.SetPoint(1,   0, 0, -200)
    else: #Needle is current position or reachable target
      points.SetPoint(1,   0, 0, 100)
    line = vtk.vtkLineSource()
    line.SetPoints(points)
    lineNode = slicer.modules.models.logic().AddModel(line.GetOutputPort())
    lineNode.SetName(modelNodeName)
    modelDisplay = lineNode.GetDisplayNode()
    modelDisplay.SetColor(1,0,0)
    modelDisplay.SetLineWidth(1)
    modelDisplay.SetOpacity(1)
    modelDisplay.SetVisibility2D(1)

  def createMaskedVolumeBySize(self, inputVolume, repair):
    loopRegistration = True
    while loopRegistration:
      thresholdPercent = self.thresholdSliderWidget.value 
      minimumSize = self.fiducialSizeSliderWidget.minimumValue
      maximumSize = self.fiducialSizeSliderWidget.maximumValue
      zframeConfig = self.zframeConfig

      # Create segmentation node
      segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
      segmentationNode.CreateDefaultDisplayNodes()
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)

      # Create segment
      segmentId = segmentationNode.GetSegmentation().AddEmptySegment("base")

      # Get access to the segment editor effect
      segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
      segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
      segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
      segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteNone)
      segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
      segmentEditorWidget.setSegmentationNode(segmentationNode)
      segmentEditorWidget.setMasterVolumeNode(inputVolume)
      segmentEditorWidget.setCurrentSegmentID(segmentId)

      # Thresholding
      inputVolume.GetImageData().GetScalarTypeMax()
      segmentEditorWidget.setActiveEffectByName("Threshold")
      effect = segmentEditorWidget.activeEffect()
      segmentEditorWidget.setCurrentSegmentID(segmentId)
      effect.setParameter("MinimumThreshold", int((inputVolume.GetImageData().GetScalarRange()[1]-inputVolume.GetImageData().GetScalarRange()[0]) * thresholdPercent + inputVolume.GetImageData().GetScalarRange()[0]))
      effect.setParameter("MaximumThreshold", int(inputVolume.GetImageData().GetScalarRange()[1]))
      effect.self().onApply()

      # Islands removal
      segmentEditorWidget.setActiveEffectByName("Islands")
      effect = segmentEditorWidget.activeEffect()
      effect.setParameter("Operation", "REMOVE_SMALL_ISLANDS")
      effect.setParameter("MinimumSize", minimumSize)
      effect.self().onApply()

      # Copy
      clonedSegmentId = segmentationNode.GetSegmentation().AddEmptySegment("cloned")
      segmentEditorWidget.setActiveEffectByName("Logical operators")
      effect = segmentEditorWidget.activeEffect()
      segmentEditorWidget.setCurrentSegmentID(clonedSegmentId)
      effect.setParameter("Operation", "COPY")
      effect.setParameter("ModifierSegmentID", segmentId)
      effect.self().onApply()

      # Isolate largest islands
      segmentEditorWidget.setActiveEffectByName("Islands")
      effect = segmentEditorWidget.activeEffect()
      effect.setParameter("MinimumSize", maximumSize)
      effect.self().onApply()

      # Subtract from base segment to leave only islands in size range
      segmentEditorWidget.setActiveEffectByName("Logical operators")
      effect = segmentEditorWidget.activeEffect()
      segmentEditorWidget.setCurrentSegmentID(segmentId)
      effect.setParameter("Operation", "SUBTRACT")
      effect.setParameter("ModifierSegmentID", clonedSegmentId)
      effect.self().onApply()

      segmentationNode.GetSegmentation().RemoveSegment(clonedSegmentId)
      
      # Remove all islands on the edges of the image
      if self.removeBorderIslandsCheckBox.isChecked():
        borderVoxels = True
        while borderVoxels:
          tempLabelmapVolume = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode', 'TempLabelMapVolume')
          slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, tempLabelmapVolume, inputVolume)
          tempLabelMapArray = slicer.util.arrayFromVolume(tempLabelmapVolume)
          slicer.mrmlScene.RemoveNode(tempLabelmapVolume)

          mask = np.zeros_like(tempLabelMapArray, dtype=bool)
          margin = int(self.borderMarginSliderWidget.value)
          # mask[0, :, :] = True # Front
          # mask[-1, :, :] = True # Back
          mask[:, 0:margin, :] = True
          mask[:, (-margin-1):-1, :] = True
          mask[:, :, 0:margin] = True
          mask[:, :, (-margin-1):-1] = True

          tempLabelMapArray[~mask] = 0
          indices = np.argwhere(tempLabelMapArray == 1)
          if len(indices) <= 0:
            borderVoxels = False
          else:
            segmentEditorWidget.setActiveEffectByName("Islands")
            effect = segmentEditorWidget.activeEffect()
            effect.setParameter("Operation", "REMOVE_SELECTED_ISLAND")
            self.removeSelectedIsland(effect, [indices[0][2], indices[0][1], indices[0][0]])

      # Export segmentation to label map
      self.removeNodeByName('MaskedCalibrationLabelMapVolume')
      labelMapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "MaskedCalibrationLabelMapVolume")
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelMapVolumeNode, inputVolume)

       # Clean up
      segmentEditorWidget.setActiveEffectByName("No editing")
      segmentEditorWidget.deleteLater()
      segmentEditorWidget = None
      slicer.mrmlScene.RemoveNode(segmentationNode)
      slicer.mrmlScene.RemoveNode(segmentEditorNode)

      # Count number of Islands and attempt repair if one is missing
      # Does not support 9 fiducial frame
      # if repair:
      #   if not zframeConfig == 'z003':
      #     loopRegistration = self.countAndRepairFiducials(labelMapVolumeNode)
      #   else: 
      #     loopRegistration = False
      # else:
      #   loopRegistration = False
      loopRegistration = False

    # Convert label map to scalar volume
    scalarVolumeNode = None
    self.removeNodeByName('MaskedCalibrationVolume')
    scalarVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "MaskedCalibrationVolume")
    slicer.modules.volumes.logic().CreateScalarVolumeFromVolume(slicer.mrmlScene, scalarVolumeNode, labelMapVolumeNode)
    self.increaseThresholdForRepair = False
    slicer.mrmlScene.RemoveNode(labelMapVolumeNode)

    return scalarVolumeNode
  
  def cropVolume(self, volumeNode, xSize, ySize):
    imageData = volumeNode.GetImageData()
    dims = imageData.GetDimensions()

    xMargin = (dims[0] - xSize, dims[0] - xSize)
    if xMargin[0] % 2 == 1:
      xMargin = (xMargin[0]//2+1, xMargin[1]//2)
    else:
      xMargin = (xMargin[0]//2, xMargin[1]//2)
    yMargin = (dims[1] - ySize, dims[1] - ySize)
    if yMargin[0] % 2 == 1:
      yMargin = (yMargin[0]//2+1, yMargin[1]//2)
    else:
      yMargin = (yMargin[0]//2, yMargin[1]//2)

    # Create a vtkExtractVOI filter to crop the image data
    extractVoi = vtk.vtkExtractVOI()
    extractVoi.SetInputData(imageData)
    extractVoi.SetVOI(xMargin[0], dims[0] - xMargin[1] - 1, yMargin[0], dims[1] - yMargin[1] - 1, 0, dims[2] - 1)
    extractVoi.Update()
    volumeNode.SetAndObserveImageData(extractVoi.GetOutput())

  def removeSelectedIsland(self, scriptedEffect, ijk):
    # Generate merged labelmap of all visible segments
    segmentationNode = scriptedEffect.parameterSetNode().GetSegmentationNode()

    selectedSegmentLabelmap = scriptedEffect.selectedSegmentLabelmap()
    # We need to know exactly the value of the segment voxels, apply threshold to make force the selected label value
    labelValue = 1
    backgroundValue = 0
    thresh = vtk.vtkImageThreshold()
    thresh.SetInputData(selectedSegmentLabelmap)
    thresh.ThresholdByLower(0)
    thresh.SetInValue(backgroundValue)
    thresh.SetOutValue(labelValue)
    thresh.SetOutputScalarType(selectedSegmentLabelmap.GetScalarType())
    thresh.Update()

    # Create oriented image data from output
    inputLabelImage = slicer.vtkOrientedImageData()
    inputLabelImage.ShallowCopy(thresh.GetOutput())
    selectedSegmentLabelmapImageToWorldMatrix = vtk.vtkMatrix4x4()
    selectedSegmentLabelmap.GetImageToWorldMatrix(selectedSegmentLabelmapImageToWorldMatrix)
    inputLabelImage.SetImageToWorldMatrix(selectedSegmentLabelmapImageToWorldMatrix)

    pixelValue = inputLabelImage.GetScalarComponentAsFloat(ijk[0], ijk[1], ijk[2], 0)

    try:
      floodFillingFilter = vtk.vtkImageThresholdConnectivity()
      floodFillingFilter.SetInputData(inputLabelImage)
      seedPoints = vtk.vtkPoints()
      origin = inputLabelImage.GetOrigin()
      spacing = inputLabelImage.GetSpacing()
      seedPoints.InsertNextPoint(origin[0] + ijk[0] * spacing[0], origin[1] + ijk[1] * spacing[1], origin[2] + ijk[2] * spacing[2])
      floodFillingFilter.SetSeedPoints(seedPoints)
      floodFillingFilter.ThresholdBetween(pixelValue, pixelValue)

      if pixelValue != 0:  # if clicked on empty part then there is nothing to remove or keep
        floodFillingFilter.SetInValue(1)
        floodFillingFilter.SetOutValue(0)

        floodFillingFilter.Update()
        modifierLabelmap = scriptedEffect.defaultModifierLabelmap()
        modifierLabelmap.DeepCopy(floodFillingFilter.GetOutput())

        scriptedEffect.modifySelectedSegmentByLabelmap(modifierLabelmap, slicer.qSlicerSegmentEditorAbstractEffect.ModificationModeRemove)
    except IndexError:
      print("Island processing failed")

  # def countAndRepairFiducials(self, labelMapVolumeNode):
  #   # Returns False if redoing registration with different parameters
  #   if labelMapVolumeNode.GetImageData().GetScalarRange()[1] == 0:
  #     numberOfSegments = 0
  #   else:
  #     segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
  #     segmentationNode.CreateDefaultDisplayNodes()
  #     slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelMapVolumeNode, segmentationNode)

  #     segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
  #     segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
  #     segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
  #     segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteNone)
  #     segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
  #     segmentEditorWidget.setSegmentationNode(segmentationNode)
  #     segmentEditorWidget.setMasterVolumeNode(labelMapVolumeNode)

  #     segmentEditorWidget.setActiveEffectByName("Islands")
  #     effect = segmentEditorWidget.activeEffect()
  #     effect.setParameter("Operation", "SPLIT_ISLANDS_TO_SEGMENTS")
  #     effect.setParameter("MinimumSize", 0)
  #     effect.self().onApply()

  #     numberOfSegments = segmentationNode.GetSegmentation().GetNumberOfSegments()

  #     # Cleanup
  #     segmentEditorWidget.setActiveEffectByName("No editing")
  #     slicer.mrmlScene.RemoveNode(segmentationNode)
  #     slicer.mrmlScene.RemoveNode(segmentEditorNode)
  #     segmentEditorWidget.deleteLater()
  #     segmentEditorWidget = None

  #   # Attempt repair
  #   result = ""
  #   print(f'Segments detected: {numberOfSegments}')

  #   if numberOfSegments > 0:
  #     # Determine if the image is salvageable
  #     # Isolate middle slice
  #     imageData = labelMapVolumeNode.GetImageData()
  #     centroid = self.findCentroidOfVolume(labelMapVolumeNode)
  #     middleSlice = int(centroid[2])
  #     dims = imageData.GetDimensions()
  #     numpy_array = vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars())
  #     numpy_array = numpy_array.reshape(dims[2], dims[1], dims[0])
  #     numpy_array = numpy_array.transpose(2,1,0)
  #     slice_array = numpy_array[:, :, middleSlice]

  #     # Calculate bounding box to see if the dimensions are about right and that there are only 1-2 missing fiducials
  #     rangeNumber = 15 # how much wiggle room to allow for bounding box
  #     leftColumn, rightColumn, topRow, bottomRow = self.calculateBoundingBox(slice_array)
  #     width = (rightColumn - leftColumn) * labelMapVolumeNode.GetSpacing()[0]
  #     height = (bottomRow - topRow) * labelMapVolumeNode.GetSpacing()[1]
  #     # print(f'leftColumn {leftColumn}')
  #     # print(f'rightColumn {rightColumn}')
  #     # print(f'topRow {topRow}')
  #     # print(f'bottomRow {bottomRow}')
  #     expectedWidth = abs(self.frameTopology[0][0] - self.frameTopology[2][0])
  #     expectedHeight = abs(self.frameTopology[0][1] - self.frameTopology[2][1])
  #     widthCorrect = (expectedWidth - rangeNumber) <= width <= (expectedWidth + rangeNumber)
  #     heightCorrect = (expectedWidth - rangeNumber) <= width <= (expectedWidth + rangeNumber)

  #     if numberOfSegments == 7:
  #       if widthCorrect and heightCorrect:
  #         print("7 fiducials detected; bounding box dimensions correct")
  #         return False
  #       else:
  #         print("7 fiducials detected; however, bounding box dimensions are wrong")
  #     if (numberOfSegments == 6 or numberOfSegments == 5) and widthCorrect and heightCorrect:
  #       print("5-6 fiducials detected; bounding box dimensions correct; trying to repair")
  #       result = self.repairMissingFiducial(slice_array, numpy_array, leftColumn, rightColumn, topRow, bottomRow, middleSlice, labelMapVolumeNode)
  #       if result == "success":
  #         return False
  #   if not self.increaseThresholdForRepair:
  #     if not (self.thresholdSliderWidget.value <= self.thresholdSliderWidget.minimum):
  #       self.thresholdSliderWidget.value = self.thresholdSliderWidget.value - 0.01
  #       print(f'Less than 6 or more than 7 fiducials detected; decreasing threshold percentage to {self.thresholdSliderWidget.value}')
  #       return True
  #     else:
  #       self.increaseThresholdForRepair = True
  #       self.thresholdSliderWidget.value = self.defaultThresholdPercentage + 0.02
  #       print(f'Switching to increasing to {self.thresholdSliderWidget.value}')
  #       return True
  #   else:
  #     # Try again with the assumption that the thresholding was too lenient
  #     if not (self.thresholdSliderWidget.value >= (self.thresholdSliderWidget.maximum/5)):
  #       self.thresholdSliderWidget.value = self.thresholdSliderWidget.value + 0.02
  #       print(f'Less than 6 or more than 7 fiducials detected; increasing threshold percentage to {self.thresholdSliderWidget.value}')
  #       return True
  #     else:
  #       print("Fiducial repair failed")
  #       self.thresholdSliderWidget.value = self.defaultThresholdPercentage
  #       return False

  def calculateBoundingBox(self, slice_array):
    leftColumn = 0
    rightColumn = slice_array.shape[0]
    topRow = 0
    bottomRow = slice_array.shape[1]
    for row in range(0, slice_array.shape[0]):
      if np.any(slice_array[row,:] > 0):
        leftColumn = row
        break
    for row in range(slice_array.shape[0]-1, -1, -1):
      if np.any(slice_array[row,:] > 0):
        rightColumn = row
        break
    for column in range(0, slice_array.shape[1]):
      if np.any(slice_array[:,column] > 0):
        topRow = column
        break
    for column in range(slice_array.shape[1]-1, -1, -1):
      if np.any(slice_array[:,column] > 0):
        bottomRow = column
        break
    return leftColumn, rightColumn, topRow, bottomRow

  # def repairMissingFiducial(self, slice_array, numpy_array, leftColumn, rightColumn, topRow, bottomRow, middleSlice, labelMapVolumeNode):
  #   # Identify missing fiducial
  #   # Shrink margins of image
  #   cropped = slice_array[leftColumn:rightColumn, topRow:bottomRow]

  #   # Probe array for values to look for missing value
  #   missingFiducial = 0
  #   r = 10
  #   thickness = 8
  #   adjust = 4
  #   length = 4
  #   diagLength = int(math.sqrt(length**2 + length**2))
  #   # Corners
  #   # Top Left
  #   if not np.any(cropped[0:r, 0:r] > 0):
  #     print("Attempting repair of top left fiducial")
  #     startLine = (leftColumn + adjust, topRow + adjust, middleSlice - (length//2))
  #     endLine = (leftColumn + adjust, topRow + adjust, middleSlice + (length//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1
  #   # Top Right
  #   if not np.any(cropped[cropped.shape[0]-r:cropped.shape[0],0:r] > 0):
  #     print("Attempting repair of top right fiducial")
  #     startLine = (leftColumn + cropped.shape[0] - adjust, topRow + adjust, middleSlice - (length//2))
  #     endLine = (leftColumn + cropped.shape[0] - adjust, topRow + adjust, middleSlice + (length//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1
  #   # Bottom Left
  #   if not np.any(cropped[0:r,cropped.shape[1]-r:cropped.shape[1]] > 0):
  #     print("Attempting repair of bottom left fiducial")
  #     startLine = (leftColumn + adjust, topRow + cropped.shape[1] - adjust, middleSlice - (length//2))
  #     endLine = (leftColumn + adjust, topRow + cropped.shape[1] - adjust, middleSlice + (length//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1
  #   # Bottom Right
  #   if not np.any(cropped[cropped.shape[0]-r:cropped.shape[0],cropped.shape[1]-r:cropped.shape[1]] > 0):
  #     print("Attempting repair of bottom right fiducial")
  #     startLine = (leftColumn + cropped.shape[0] - adjust, topRow + cropped.shape[1] - adjust, middleSlice - (length//2))
  #     endLine = (leftColumn + cropped.shape[0] - adjust, topRow + cropped.shape[1] - adjust, middleSlice + (length//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1

  #   # Sides
  #   # Middle Left
  #   if not np.any(cropped[0:r, cropped.shape[1]//2-r//2:cropped.shape[1]//2+r//2] > 0):
  #     print("Attempting repair of middle left fiducial")
  #     startLine = (leftColumn + adjust, topRow + cropped.shape[1]//2 - (diagLength//2), middleSlice - (diagLength//2))
  #     endLine = (leftColumn + adjust, topRow + cropped.shape[1]//2 + (diagLength//2), middleSlice + (diagLength//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1
  #   # Middle Top  
  #   if not np.any(cropped[cropped.shape[0]//2-r//2:cropped.shape[0]//2+r//2, 0:r] > 0):
  #     print("Attempting repair of middle top fiducial")
  #     startLine = (leftColumn + cropped.shape[0]//2 + (diagLength//2), topRow + adjust, middleSlice - (diagLength//2))
  #     endLine = (leftColumn + cropped.shape[0]//2 - (diagLength//2), topRow + adjust, middleSlice + (diagLength//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1
  #   # Middle Right  
  #   if not np.any(cropped[cropped.shape[0]-r:cropped.shape[0], cropped.shape[1]//2-r//2:cropped.shape[1]//2+r//2] > 0):
  #     print("Attempting repair of middle right fiducial")
  #     startLine = (leftColumn + cropped.shape[0] - adjust, topRow + cropped.shape[1]//2 + (diagLength//2), middleSlice - (diagLength//2))
  #     endLine = (leftColumn + cropped.shape[0] - adjust, topRow +  cropped.shape[1]//2 - (diagLength//2), middleSlice + (diagLength//2))
  #     numpy_array = self.drawThickLine(startLine, endLine, thickness, numpy_array)
  #     missingFiducial += 1

  #   if 2 >= missingFiducial >= 1:
  #     imageData = self.numpy_to_vtk_image_data(numpy_array)
  #     labelMapVolumeNode.SetAndObserveImageData(imageData)
  #     return "success"
  #   else:
  #     return "anomaly"

  # def drawThickLine(self, start, end, thickness, numpy_array):
  #   for dx in range(-thickness//2, thickness//2+1):
  #     for dy in range(-thickness//2, thickness//2+1):
  #         for dz in range(-thickness//2, thickness//2+1):
  #           rr, cc, zz = line_nd([start[0]+dx, start[1]+dy, start[2]+dz], [end[0]+dx, end[1]+dy, end[2]+dz], endpoint=True)
  #           numpy_array[rr, cc, zz] = 1
  #   return numpy_array

  def findCentroidOfVolume(self, inputVolume):
    imageData = inputVolume.GetImageData()
    dimensions = imageData.GetDimensions()
    spacing = imageData.GetSpacing()
    origin = imageData.GetOrigin()
    # Convert vtkImageData to numpy array
    voxels = vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars())
    voxels = voxels.reshape(dimensions, order='F')
    # Calculate the center of mass
    indices = np.indices(dimensions).reshape(3, -1)
    center_of_mass = np.average(indices, axis=1, weights=voxels.ravel())
    return center_of_mass

  def onIdentity(self):
    if self.outputTransform:
      identityMatrix = vtk.vtkMatrix4x4()
      identityMatrix.Identity()
      self.outputTransform.SetMatrixTransformToParent(identityMatrix)
      self.manualRegistrationTransformSliders.setMRMLTransformNode(None)
      self.manualRegistrationRotationSliders.setMRMLTransformNode(None)
      self.manualRegistrationTransformSliders.reset()
      self.manualRegistrationRotationSliders.reset()
      self.manualRegistrationTransformSliders.setMRMLTransformNode(self.outputTransform)
      self.manualRegistrationRotationSliders.setMRMLTransformNode(self.outputTransform)

  def loadTemplateConfiguration(self):
    currentFilePath = os.path.dirname(slicer.util.modulePath(self.__module__))
    self.zframeConfig = ""
    if self.configFileSelectionBox.currentIndex == 0:
      self.ZFRAME_MODEL_PATH = 'template001/zframe001-model.vtk'
      self.zframeConfig = 'z001'
      zframeConfigFilePath = os.path.join(currentFilePath, "Resources/Templates/template001/zframe001.txt")
    elif self.configFileSelectionBox.currentIndex == 1:
      self.ZFRAME_MODEL_PATH = 'template002/zframe002-model.vtk'
      self.zframeConfig = 'z002'
      zframeConfigFilePath = os.path.join(currentFilePath, "Resources/Templates/template002/zframe002.txt")
    elif self.configFileSelectionBox.currentIndex == 2:
      self.ZFRAME_MODEL_PATH = 'template003/zframe003-model.vtk'
      self.zframeConfig = 'z003'
      zframeConfigFilePath = os.path.join(currentFilePath, "Resources/Templates/template003/zframe003.txt")
    else: #self.configFileSelectionBox.currentIndex == 3:
      self.ZFRAME_MODEL_PATH = 'template004/zframe004-model.vtk'
      self.zframeConfig = 'z004'
      zframeConfigFilePath = os.path.join(currentFilePath, "Resources/Templates/template004/zframe004.txt")
    
    with open(zframeConfigFilePath,"r") as f:
      configFileLines = f.readlines()

    # Parse zFrame configuration file here to identify the dimensions and topology of the zframe
    # Save the origins and diagonal vectors of each of the 3 sides of the zframe in an array
    self.frameTopology = []
    self.zFrameFiducials = []
    for line in configFileLines:
      if line.startswith('Side 1') or line.startswith('Side 2'): 
        vec = [float(s) for s in re.findall(r'-?\d+\.?\d*', line)]
        vec.pop(0)
        self.frameTopology.append(vec)
      elif line.startswith('Base'):
        vec = [float(s) for s in re.findall(r'-?\d+\.?\d*', line)]
        self.frameTopology.append(vec)
      elif line.startswith('Fiducial'):
        vec = [float(s) for s in re.findall(r'(-?\d+)(?!:)', line)]
        self.zFrameFiducials.append(vec)

    # Convert frameTopology points to a string, for the sake of passing it as a string argument to the ZframeRegistration CLI 
    self.frameTopologyString = ' '.join([str(elem) for elem in self.frameTopology])

  def onRegister(self):
    self.loadTemplateConfiguration()

    # If there is a zFrame image selected, perform the calibration step to calculate the CLB matrix
    if not self.zFrameVolumeSelector.currentNode():
      print("No zFrame image found. Cannot calculate the calibration matrix.")
      return
    
    print ("Initating calibration matrix calculation with zFrame image.")

    result = False
    result = self.registerZFrame()
    self.increaseThresholdForRetry = False

    self.loadZFrameModel()
    self.loadRobotModel()

    self.zFrameModelNode.SetAndObserveTransformNodeID(self.outputTransform.GetID())
    self.robotModelNode.SetAndObserveTransformNodeID(self.outputTransform.GetID())
    self.zFrameModelNode.GetDisplayNode().SetVisibility2D(True)
    self.zFrameModelNode.SetDisplayVisibility(True)
    self.robotModelNode.SetDisplayVisibility(True)

    if result:
      self.onRegistrationSuccess()
    else:
      self.onRegistrationFailure()

  def registerZFrame(self):
    inputVolume = self.zFrameVolumeSelector.currentNode()
    seriesNumber = inputVolume.GetName().split(":")[0]
    name = seriesNumber + "-ZFrameTransform"

    # Create an empty transform for the calibration matrix output
    if self.outputTransform:
      slicer.mrmlScene.RemoveNode(self.outputTransform)
      self.outputTransform = None
    self.outputTransform = slicer.vtkMRMLLinearTransformNode()
    self.outputTransform.SetName(name)
    slicer.mrmlScene.AddNode(self.outputTransform)
    self.registrationTranslationSliderWidget.setMRMLTransformNode(slicer.util.getNode(name))
    self.registrationOrientationSliderWidget.setMRMLTransformNode(slicer.util.getNode(name))

    if not inputVolume:
      return False
    
    # First try without repair methods
    loopRegistration = True
    while loopRegistration:
      zFrameMaskedVolume = self.createMaskedVolumeBySize(inputVolume, False)
      if zFrameMaskedVolume.GetImageData().GetScalarRange()[1] > 0:
        # Crop if not 256x256
        zFrameMaskedVolumeDims = zFrameMaskedVolume.GetImageData().GetDimensions()
        if zFrameMaskedVolumeDims[0] != 256 and zFrameMaskedVolumeDims[1] != 256:
          self.cropVolume(zFrameMaskedVolume, 256, 256)
        
        centerOfMassSlice = int(self.findCentroidOfVolume(zFrameMaskedVolume)[2])
        # Run zFrameRegistration CLI module
        params = {'inputVolume': zFrameMaskedVolume, 'startSlice': centerOfMassSlice-3, 'endSlice': centerOfMassSlice+3,
                  'outputTransform': self.outputTransform, 'zframeConfig': self.zframeConfig, 'frameTopology': self.frameTopologyString, 
                  'zFrameFids': ''}
        cliNode = slicer.cli.run(slicer.modules.zframeregistration, None, params, wait_for_completion=True)
        if cliNode.GetStatus() & cliNode.ErrorsMask:
          print(cliNode.GetErrorText())
        if self.removeOrientationCheckBox.isChecked():
          self.removeOrientationComponent(self.outputTransform)
      else:
        print("Masked volume empty")
      regResult = self.checkRegistrationResult(self.outputTransform, zFrameMaskedVolume, self.zFrameFiducials)
      if not regResult:
        # Try to process at different thresholds
        if self.retryFailedRegistrationCheckBox.isChecked():
          if not self.increaseThresholdForRetry:
            if not (self.thresholdSliderWidget.value <= self.thresholdSliderWidget.minimum):
              self.thresholdSliderWidget.value = self.thresholdSliderWidget.value - 0.02
              print(f'Retrying; decreasing threshold percentage to {self.thresholdSliderWidget.value}')
              loopRegistration = True
            else:
              self.increaseThresholdForRetry = True
              self.thresholdSliderWidget.value = self.defaultThresholdPercentage + 0.04
              print(f'Retrying; increasing threshold percentage to {self.thresholdSliderWidget.value}')
              loopRegistration = True
          else:
            if not (self.thresholdSliderWidget.value >= (self.thresholdSliderWidget.maximum/5)):
              self.thresholdSliderWidget.value = self.thresholdSliderWidget.value + 0.04
              print(f'Retrying; increasing threshold percentage to {self.thresholdSliderWidget.value}')
              loopRegistration = True
            else:
              print("Retries failed; Moving on to repair attempt")
              self.thresholdSliderWidget.value = self.defaultThresholdPercentage
              loopRegistration = False
        else:
          loopRegistration = False
      else:
        loopRegistration = False
        return True
      
    # if self.repairFiducialImageCheckBox.isChecked():
    #   zFrameMaskedVolume = self.createMaskedVolumeBySize(inputVolume, True)
    #   if zFrameMaskedVolume.GetImageData().GetScalarRange()[1] > 0:
    #     # Crop if not 256x256
    #     zFrameMaskedVolumeDims = zFrameMaskedVolume.GetImageData().GetDimensions()
    #     # TODO: Pad images smaller than 256 by 256
    #     if zFrameMaskedVolumeDims[0] != 256 and zFrameMaskedVolumeDims[1] != 256:
    #       self.cropVolume(zFrameMaskedVolume, 256, 256)
        
    #     centerOfMassSlice = int(self.findCentroidOfVolume(zFrameMaskedVolume)[2])
    #     # Run zFrameRegistration CLI module
    #     params = {'inputVolume': zFrameMaskedVolume, 'startSlice': centerOfMassSlice-3, 'endSlice': centerOfMassSlice+3,
    #               'outputTransform': outputTransform, 'zframeConfig': self.zframeConfig, 'frameTopology': self.frameTopologyString, 
    #               'zFrameFids': ''}
    #     cliNode = slicer.cli.run(slicer.modules.zframeregistration, None, params, wait_for_completion=True)
    #     if cliNode.GetStatus() & cliNode.ErrorsMask:
    #       print(cliNode.GetErrorText())
    #     if self.removeOrientationCheckBox.isChecked():
    #       self.removeOrientationComponent(outputTransform)
    #   else:
    #     print("Masked volume empty")

    #   regResult = self.checkRegistrationResult(outputTransform, zFrameMaskedVolume, self.zFrameFiducials)
    #   return regResult, outputTransform
    
    return False

  def checkRegistrationResult(self, outputTransform, fiducialVolume, zFrameFiducials):
    # Check the midpoint of each ZFrame fiducial and some points around it for a detected fiducial
    zFrameMidpoints = []
    for zFrameFiducial in zFrameFiducials:
      zFrameMidpoints.append([(zFrameFiducial[0] + zFrameFiducial[3]) / 2, (zFrameFiducial[1] + zFrameFiducial[4]) / 2, (zFrameFiducial[2] + zFrameFiducial[5]) / 2])
    for zFrameMidpoint in zFrameMidpoints:
      zFrameMidpoint = zFrameMidpoint + [1]

      outputMatrix = vtk.vtkMatrix4x4()
      outputTransform.GetMatrixTransformToParent(outputMatrix)
      transformedMidpoint = [0, 0, 0, 1]
      outputMatrix.MultiplyPoint(zFrameMidpoint, transformedMidpoint)

      rasToIjkMatrix = vtk.vtkMatrix4x4()
      fiducialVolume.GetRASToIJKMatrix(rasToIjkMatrix)
      ijkMidpoint = [0, 0, 0, 1]
      rasToIjkMatrix.MultiplyPoint(transformedMidpoint, ijkMidpoint)

      fiducialImageData = fiducialVolume.GetImageData()
      # Check if point is in extent of volume
      extent = fiducialImageData.GetExtent()
      if not (extent[0] <= ijkMidpoint[0] <= extent[1] and extent[2] <= ijkMidpoint[1] <= extent[3] and extent[4] <= ijkMidpoint[2] <= extent[5]):
        return False
      # Check point and surrounding points
      fiducialFound = False
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0]), int(ijkMidpoint[1]), int(ijkMidpoint[2]), 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0])-2, int(ijkMidpoint[1]), int(ijkMidpoint[2]), 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0])+2, int(ijkMidpoint[1]), int(ijkMidpoint[2]), 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0]), int(ijkMidpoint[1])-2, int(ijkMidpoint[2]), 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0]), int(ijkMidpoint[1])+2, int(ijkMidpoint[2]), 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0]), int(ijkMidpoint[1]), int(ijkMidpoint[2])-2, 0) > 0: fiducialFound = True
      if fiducialImageData.GetScalarComponentAsDouble(int(ijkMidpoint[0]), int(ijkMidpoint[1]), int(ijkMidpoint[2])+2, 0) > 0: fiducialFound = True
      if not fiducialFound:
        return False
    return True    

  def onUseManualRegistration(self):
    self.sendCalibrationMatrixButton.enabled = True

  # def initiateZFrameCalibration(self):
  #   # Begin by identifying the zframe dropdown selection & parsing the config file to package topological dimensions into a ZframeRegistration argument
  #   self.onConfigFileSelectionChanged()

  #   # If there is a zFrame image selected, perform the calibration step to calculate the CLB matrix
  #   self.inputVolume = self.zFrameVolumeSelector.currentNode()

  #   if self.inputVolume is not None:
  #     seriesNumber = self.inputVolume.GetName().split(":")[0]
  #     name = seriesNumber + "-ZFrameTransform"
      
  #     # Create an empty transform for the calibration matrix output
  #     if self.outputTransform:
  #       slicer.mrmlScene.RemoveNode(self.outputTransform)
  #       self.outputTransform = None
  #     self.outputTransform = slicer.vtkMRMLLinearTransformNode()
  #     self.outputTransform.SetName(name)
  #     slicer.mrmlScene.AddNode(self.outputTransform)
  #     self.registrationTranslationSliderWidget.setMRMLTransformNode(slicer.util.getNode(name))
  #     self.registrationOrientationSliderWidget.setMRMLTransformNode(slicer.util.getNode(name))
  #     self.outputTransform.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onRegistrationTransformManuallyModified)

  #     print ("Initating calibration matrix calculation with zFrame image.")
      
  #     # Get start and end slices from the StartSliceSliderWidget
  #     self.startSlice = int(self.startSliceSliderWidget.value)
  #     self.endSlice = int(self.endSliceSliderWidget.value)
  #     maxSlice = self.inputVolume.GetImageData().GetDimensions()[2]
  #     if self.endSlice == 0 or self.endSlice > maxSlice:
  #       # Use the image end slice
  #       self.endSlice = maxSlice
  #       self.endSliceSliderWidget.value = float(self.endSlice)

  #     if self.manuallySelectSlices:
  #       self.startSlice = int(self.startSliceSliderWidget.text)
  #       self.endSlice = int(self.endSliceSliderWidget.text)
        
  #     # If the user manually selected a list of fiducials to use in registration (zFrameFids), set the start and end slices s.t. 
  #     # only the image frame with the fiducials on it is used in the calculation
  #     if self.manualRegistration:
  #       # Get volume voxel coordinates from markup control point RAS coordinates
  #       # to determine slice index for registration with manual fiducial selection
  #       # Get point coordinate in RAS
  #       pointListNode= self.manualZframeFiducialsSelector.currentNode()
  #       markupsIndex = 0
  #       point_Ras = [0, 0, 0, 1]
  #       pointListNode.GetNthFiducialWorldCoordinates(markupsIndex, point_Ras)

  #       # If volume node is transformed, apply that transform to get volume's RAS coordinates
  #       transformRasToVolumeRas = vtk.vtkGeneralTransform()
  #       slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(None, self.inputVolume .GetParentTransformNode(), transformRasToVolumeRas)
  #       point_VolumeRas = transformRasToVolumeRas.TransformPoint(point_Ras[0:3])

  #       # Get voxel coordinates from physical coordinates
  #       volumeRasToIjk = vtk.vtkMatrix4x4()
  #       self.inputVolume.GetRASToIJKMatrix(volumeRasToIjk)
  #       point_Ijk = [0, 0, 0, 1]
  #       volumeRasToIjk.MultiplyPoint(np.append(point_VolumeRas,1.0), point_Ijk)
  #       point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]
  #       voxelCoordinate = point_Ijk[2]

  #       self.startSlice = voxelCoordinate
  #       self.endSlice = voxelCoordinate + 1

  #     # Check for the ZFrame ROI node and if it exists, use it for the start and end slices
  #     if self.zFrameROI is not None:
  #       print ("Found zFrame ROI: ", self.zFrameROI.GetID())
  #       self.zFrameROI.SetDisplayVisibility(1)
  #       center = [0.0, 0.0, 0.0]
  #       self.zFrameROI.GetXYZ(center)
  #       bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  #       self.zFrameROI.GetRASBounds(bounds)
  #       pMin = [bounds[0], bounds[2], bounds[4], 1]
  #       pMax = [bounds[1], bounds[3], bounds[5], 1]
  #       rasToIJKMatrix = vtk.vtkMatrix4x4()
  #       self.inputVolume.GetRASToIJKMatrix(rasToIJKMatrix)
  #       pos = [0,0,0,1]
  #       rasToIJKMatrix.MultiplyPoint(pMin, pos)

  #       # Only use the ZFrame ROI node to define the start and end slices if the user did NOT 
  #       # manually select zframe fiducials in Advanced Registration Options
  #       if not self.manualRegistration and not self.manuallySelectSlices:
  #         self.startSlice = int(pos[2])
  #         rasToIJKMatrix.MultiplyPoint(pMax, pos)
  #         self.endSlice = int(pos[2])
  #         # Check if slices are in bounds
  #         if self.startSlice < 0:
  #           self.startSlice = 0
  #         if self.endSlice < 0:
  #           self.endSlice = 0
  #         endZ = self.inputVolume.GetImageData().GetDimensions()[2]
  #         endZ = endZ - 1
  #         if self.startSlice > endZ:
  #           self.startSlice = endZ
  #         if self.endSlice > endZ:
  #           self.endSlice = endZ

  #       self.startSliceSliderWidget.value = float(self.startSlice)
  #       self.endSliceSliderWidget.value = float(self.endSlice)

  #       if self.configFileSelectionBox.currentText == "Z-frame z001":
  #         self.ZFRAME_MODEL_PATH = 'zframe001-model.vtk'
  #         zframeConfig = 'z001'
  #       elif self.configFileSelectionBox.currentText == "Z-frame z002":
  #         self.ZFRAME_MODEL_PATH = 'zframe002-model.vtk'
  #         zframeConfig = 'z002'
  #       else: # if self.configFileSelectionBox.currentText == "Z-frame z003":
  #         self.ZFRAME_MODEL_PATH = 'zframe003-model.vtk'
  #         zframeConfig = 'z003'

  #       self.ZFRAME_MODEL_NAME = 'ZFrameModel'
        
  #       # Run ZFrame Open Source Registration
  #       self.loadZFrameModel()
  #       self.loadRobotModel()

  #       # Begin zFrameRegistrationWithROI logic
  #       zFrameTemplateVolume = self.inputVolume
  #       coverTemplateROI = self.zFrameROI

  #       self.zFrameCroppedVolume = self.createCroppedVolume(zFrameTemplateVolume, coverTemplateROI)
  #       self.zFrameLabelVolume = self.createLabelMapFromCroppedVolume(self.zFrameCroppedVolume, "labelmap")
  #       self.zFrameMaskedVolume = self.createMaskedVolume(zFrameTemplateVolume, self.zFrameLabelVolume)
  #       self.zFrameMaskedVolume.SetName(zFrameTemplateVolume.GetName() + "-label")
  #       if self.startSlice is None or self.endSlice is None:
  #         self.startSlice, center, self.endSlice = self.getROIMinCenterMaxSliceNumbers(coverTemplateROI)
  #         self.otsuOutputVolume = self.applyITKOtsuFilter(self.zFrameMaskedVolume)
  #         self.dilateMask(self.otsuOutputVolume)
  #         self.startSlice, self.endSlice = self.getStartEndWithConnectedComponents(self.otsuOutputVolume, center)

  #       # Run zFrameRegistration CLI module
  #       # params = {'inputVolume': self.zFrameMaskedVolume, 'startSlice': self.startSlice, 'endSlice': self.endSlice,
  #       #            'outputTransform': self.outputTransform}
  #       params = {'inputVolume': self.zFrameMaskedVolume, 'startSlice': self.startSlice, 'endSlice': self.endSlice,
  #                 'outputTransform': self.outputTransform, 'zframeConfig': zframeConfig, 'frameTopology': self.frameTopologyString, 
  #                 'zFrameFids': self.zFrameFidsString}
  #       slicer.cli.run(slicer.modules.zframeregistration, None, params, wait_for_completion=True)

  #       self.zFrameModelNode.SetAndObserveTransformNodeID(self.outputTransform.GetID())
  #       self.robotModelNode.SetAndObserveTransformNodeID(self.outputTransform.GetID())
  #       self.zFrameModelNode.GetDisplayNode().SetVisibility2D(True)
  #       self.zFrameModelNode.SetDisplayVisibility(True)
  #       self.robotModelNode.SetDisplayVisibility(True)

  #       # Remove unnecessary nodes from the Slicer scene
  #       self.clearVolumeNodes()

  #       # Reset registration to automatic
  #       self.manualRegistration = False
      
  #       # Enable the sendCalibrationMatrixButton
  #       self.sendCalibrationMatrixButton.enabled = True
      
  #     else:
  #       print("No ROI found. Please indicate the region of interest using the 'Add ROI' button.")
        
  #   else:
  #     print("No zFrame image found. Cannot calculate the calibration matrix.")

  def modified_gram_schmidt(self, A):
    m, n = A.shape
    Q = np.zeros((m, n))
    R = np.zeros((n, n))
    for j in range(n):
      v = A[:, j]
      for i in range(j):
        R[i, j] = np.dot(Q[:, i], A[:, j])
        v = v - R[i, j] * Q[:, i]
      R[j, j] = np.linalg.norm(v)
      Q[:, j] = v / R[j, j]
    return Q, R
  
  def onRegistrationSuccess(self):
    print("Registration Successful")
    self.increaseThresholdForRepair = False

    self.validRegistrationLabel.text= "Registration Successful"
    self.validRegistrationLabel.setStyleSheet("QLabel {background-color: #1A9A30}")

    # Enable the sendCalibrationMatrixButton
    self.sendCalibrationMatrixButton.enabled = True

  def onRegistrationFailure(self):
    print("Registration Failure")
    self.increaseThresholdForRepair = False
    self.manualRegistrationGroupBox.collapsed = False

    self.validRegistrationLabel.text= "Registration Failed"
    self.validRegistrationLabel.setStyleSheet("QLabel {background-color: #660000}")

    # Disable the sendCalibrationMatrixButton
    self.sendCalibrationMatrixButton.enabled = False

  def onSendCalibrationMatrixButtonClicked(self):
    # Package the contents of the Calibration Matrix into a 4x4 matrix
    outputMatrix = vtk.vtkMatrix4x4()
    
    self.outputTransform.GetMatrixTransformToParent(outputMatrix)
    
    # Make rotational component orthonormal
    nonorthonormalArray = np.array([[outputMatrix.GetElement(0,0), outputMatrix.GetElement(0,1), outputMatrix.GetElement(0,2)], [outputMatrix.GetElement(1,0), outputMatrix.GetElement(1,1), outputMatrix.GetElement(1,2)], [outputMatrix.GetElement(2,0), outputMatrix.GetElement(2,1), outputMatrix.GetElement(2,2)]])
    orthonormalArray, R = self.modified_gram_schmidt(nonorthonormalArray)
    outputMatrix.SetElement(0,0,orthonormalArray[0,0]); outputMatrix.SetElement(0,1,orthonormalArray[0,1]); outputMatrix.SetElement(0,2,orthonormalArray[0,2])
    outputMatrix.SetElement(1,0,orthonormalArray[1,0]); outputMatrix.SetElement(1,1,orthonormalArray[1,1]); outputMatrix.SetElement(1,2,orthonormalArray[1,2])
    outputMatrix.SetElement(2,0,orthonormalArray[2,0]); outputMatrix.SetElement(2,1,orthonormalArray[2,1]); outputMatrix.SetElement(2,2,orthonormalArray[2,2])

    # Send the calculated calibration matrix to WPI as the CLB matrix
    if (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLIGTLConnectorNode') > 0): # AKA, if the IGTL connector is active
      SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
      timestampIDname = self.generateTimestampNameID("CLB")
      SendTransformNodeTemp.SetName(timestampIDname)
      SendTransformNodeTemp.SetMatrixTransformToParent(outputMatrix)
      slicer.mrmlScene.AddNode(SendTransformNodeTemp)
      self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
      self.openIGTNode.PushNode(SendTransformNodeTemp)
      infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
      re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
      self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")
      self.appendTransformToCommandLog(outputMatrix)
    else:
      print("OpenIGTLink connector is not active. Cannot send the registration transform.")

  def onAddTarget(self):
    nodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLMarkupsFiducialNode')
    count = 0
    for i in range(nodes.GetNumberOfItems()):
      node = nodes.GetItemAsObject(i)
      if node.GetName().startswith("TARGET_POINT"):
        count += 1

    biopsyFiducialListNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", f'TARGET_POINT_{count+1}')
    slicer.modules.markups.logic().StartPlaceMode(False)

    # Set the current node in the selection node
    selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
    selectionNode.SetReferenceActivePlaceNodeClassName(biopsyFiducialListNode.GetClassName())
    selectionNode.SetActivePlaceNodeID(biopsyFiducialListNode.GetID())

    self.targetPointNodeSelector.setCurrentNode(biopsyFiducialListNode)

  # Function to reset the 4x4 target transform to an identity matrix at the position of the new fiducial when the target point fiducial is updated
  def onTargetPointFiducialChanged(self):
    targetPointNode = self.targetPointNodeSelector.currentNode()
    if targetPointNode is not None:
      # if not self.phaseTextbox.text == 'PLANNING':
      #   print ("Robot is not yet in PLANNING workphase. Please enter PLANNING workphase before selecting the target point.")
      # else: 
      if not targetPointNode.GetNumberOfControlPoints() == 0:
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
    if self.plannedTargetTransform:
      # Package the planned target transform generated by the planning GUI into a 4x4 matrix
      plannedTargetMatrix = vtk.vtkMatrix4x4()
      self.plannedTargetTransform.GetMatrixTransformToParent(plannedTargetMatrix)

      # Send the calculated target matrix to WPI as the TGT matrix
      if (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLIGTLConnectorNode') > 0): # AKA, if the IGTL connector is active
        SendTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
        timestampIDname = self.generateTimestampNameID("TGT")
        SendTransformNodeTemp.SetName(timestampIDname)
        SendTransformNodeTemp.SetMatrixTransformToParent(plannedTargetMatrix)
        slicer.mrmlScene.AddNode(SendTransformNodeTemp)
        self.openIGTNode.RegisterOutgoingMRMLNode(SendTransformNodeTemp)
        self.openIGTNode.PushNode(SendTransformNodeTemp)
        infoMsg =  "Sending TRANSFORM( " + timestampIDname + " )"
        re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
        self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")
        self.appendTransformToCommandLog(plannedTargetMatrix)

      else:
        print("OpenIGTLink connector is not active. Cannot send the registration transform.")
    else:
      print("plannedTargetTransform has not been generated yet. Use the Planning GUI to plan the target location.")

# # ------------------------- FUNCTIONS FOR CALIBRATION STEP ---------------------------

  def loadZFrameModel(self):
    if self.zFrameModelNode:
      slicer.mrmlScene.RemoveNode(self.zFrameModelNode)
      self.zFrameModelNode = None
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    zFrameModelPath = os.path.join(currentFilePath, "Resources", "Templates", self.ZFRAME_MODEL_PATH)
    print(zFrameModelPath)
    self.zFrameModelNode = slicer.util.loadModel(zFrameModelPath)
    # _, self.zFrameModelNode = slicer.util.loadModel(zFrameModelPath)
    self.zFrameModelNode.SetName('ZFrameModel')
    modelDisplayNode = self.zFrameModelNode.GetDisplayNode()
    modelDisplayNode.SetColor(0.9,0.9,0.4)
    self.zFrameModelNode.SetDisplayVisibility(False)

  def loadRobotModel(self):
    if self.robotModelNode:
      slicer.mrmlScene.RemoveNode(self.robotModelNode)
      self.robotModelNode = None
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    robotModelPath = os.path.join(currentFilePath, "Resources", "robot", "robot.vtk")
    self.robotModelNode = slicer.util.loadModel(robotModelPath)
    self.robotModelNode.SetName("RobotModel")
    modelDisplayNode = self.robotModelNode.GetDisplayNode()
    modelDisplayNode.SetColor(0.7, 0.7, 0.85)
    modelDisplayNode.SetOpacity(0.4)
    self.robotModelNode.SetDisplayVisibility(False)    

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

  def onSendTrackedTipTransform(self, caller, event):
    if (self.sendTrackedTipTransformCheckbox.isChecked()):
      trackedTipMatrix = vtk.vtkMatrix4x4()
      self.needleTipTransformComboBox.currentNode().GetMatrixTransformToWorld(trackedTipMatrix)
      reachedTargetString = (slicer.mrmlScene.GetFirstNodeByName("HAS_REACHED_TARGET")).GetText()
      if (reachedTargetString == "0") and (not ((trackedTipMatrix.GetElement(0,3) == self.previousTrackedTipMatrix.GetElement(0,3)) and (trackedTipMatrix.GetElement(1,3) == self.previousTrackedTipMatrix.GetElement(1,3)) and (trackedTipMatrix.GetElement(2,3) == self.previousTrackedTipMatrix.GetElement(2,3)))):
        #Remove orientation component of matrix
        trackedTipMatrix.SetElement(0,0,1); trackedTipMatrix.SetElement(0,1,0); trackedTipMatrix.SetElement(0,2,0)
        trackedTipMatrix.SetElement(1,0,0); trackedTipMatrix.SetElement(1,1,1); trackedTipMatrix.SetElement(1,2,0)
        trackedTipMatrix.SetElement(2,0,0); trackedTipMatrix.SetElement(2,1,0); trackedTipMatrix.SetElement(2,2,1)

        if (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLIGTLConnectorNode') > 0): # AKA, if the IGTL connector is active
          TrackedTipTransformNodeTemp = slicer.vtkMRMLLinearTransformNode()
          timestampIDname = self.generateTimestampNameID("NPOS")
          TrackedTipTransformNodeTemp.SetName(timestampIDname)
          TrackedTipTransformNodeTemp.SetMatrixTransformToParent(trackedTipMatrix)
          slicer.mrmlScene.AddNode(TrackedTipTransformNodeTemp)
          self.openIGTNode.RegisterOutgoingMRMLNode(TrackedTipTransformNodeTemp)
          self.openIGTNode.PushNode(TrackedTipTransformNodeTemp)
          infoMsg =  "Sending TRACKED TIP TRANSFORM( " + timestampIDname + " )"
          re.sub(r'(?<=[,])(?=[^\s])', r' ', infoMsg)
          self.appendSentMessageToCommandLog(timestampIDname, infoMsg, "ROBOT")
          #slicer.mrmlScene.RemoveNode(TrackedTipTransformNodeTemp)
          self.previousTrackedTipMatrix.DeepCopy(trackedTipMatrix)
      elif (reachedTargetString == "1"):
        caller.RemoveObserver(caller.observerTag)

class ProstateBRPInterfaceTest(ScriptedLoadableModuleTest):

  def setUp(self):
    slicer.mrmlScene.Clear()
    widget = ProstateBRPInterfaceWidget()
    print(dir(widget))
    hostname = slicer.modules.prostatebrpinterface.widgetRepresentation().self().snrHostnameTextbox.text
    port = slicer.modules.prostatebrpinterface.widgetRepresentation().self().snrPortTextbox.text
    widget.snrHostnameTextbox.setText(hostname)
    widget.snrPortTextbox.setText(port)
    return widget
  
  def getMostRecentMessage(self, type, prefix):
    nodes = slicer.mrmlScene.GetNodes()
    node_of_interest = None
    highestTimestamp = 0
    for i in range(nodes.GetNumberOfItems()):
      node = nodes.GetItemAsObject(i)
      if node.GetClassName() == type and node.GetName().startswith(prefix):
        timestamp = int(node.GetName()[4:])
        if timestamp > highestTimestamp:
          node_of_interest = node
    return node_of_interest
  
  def compareTransformNodes(self, node1, node2, precision=0.01):
    # Get the transformation matrices
    matrix1 = vtk.vtkMatrix4x4()
    node1.GetMatrixTransformToParent(matrix1)
    matrix2 = vtk.vtkMatrix4x4()
    node2.GetMatrixTransformToParent(matrix2)
    # Compare the matrices element by element
    for i in range(4):
      for j in range(4):
        if abs(matrix1.GetElement(i, j) - matrix2.GetElement(i, j)) > precision:
          return False
    return True

  def runTest(self):
    # Unit testing
    self.delayDisplay("<h1>Starting Unit Tests</h1>")
    self.test_RegistrationTest()
    self.test_PlanningTest()

    # Integration testing
    self.delayDisplay("<h1>Starting Integrated Tests</h1>")
    self.test_NormalOperation()
    self.test_NormalOperationWithPositionQuery()
    self.test_ImproperCalibration()
    self.test_OutOfBounds()
    self.test_EmergencyStop()

  # Unit testing

  def test_RegistrationTest(self):
    widget = self.setUp()
    try:
      self.delayDisplay("<h2>Starting Registration Test</h2>")

      volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
      templateImageNode = slicer.util.loadVolume(volumePathTemplate)

      slicer.util.delayDisplay("Performing Registration", 1000)
      widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
      widget.onRegister()

      correctTransform = slicer.vtkMRMLLinearTransformNode()
      correctMatrix = vtk.vtkMatrix4x4()
      correctMatrix.SetElement(0,0,1); correctMatrix.SetElement(0,1,0); correctMatrix.SetElement(0,2,0); correctMatrix.SetElement(0,3,-6.67969)
      correctMatrix.SetElement(1,0,0); correctMatrix.SetElement(1,1,1); correctMatrix.SetElement(1,2,0); correctMatrix.SetElement(1,3,68.0608)
      correctMatrix.SetElement(2,0,0); correctMatrix.SetElement(2,1,0); correctMatrix.SetElement(2,2,1); correctMatrix.SetElement(2,3,-106.241)
      correctMatrix.SetElement(3,0,0); correctMatrix.SetElement(3,1,0); correctMatrix.SetElement(3,2,0); correctMatrix.SetElement(3,3,1)
      correctTransform.SetAndObserveMatrixTransformToParent(correctMatrix)
      self.assertTrue(self.compareTransformNodes(widget.outputTransform, correctTransform))
      self.delayDisplay(f'<font color="#72ff6b">Calibration Matrix matches known correct values</font>')

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
      raise Exception("Exception occurred during testing")
    
    widget.cleanup()
    widget.parent.deleteLater()

  def test_PlanningTest(self):
    widget = self.setUp()
    try:
      self.delayDisplay("<h2>Starting Planning Test</h2>")

      volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
      anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

      slicer.util.delayDisplay("Selecting Target", 1000)
      widget.onAddTarget()
      widget.targetPointNodeSelector.currentNode().AddFiducial(-20, 59, 18.2)
      interactionNode = slicer.app.applicationLogic().GetInteractionNode()
      interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)

      correctTransform = slicer.vtkMRMLLinearTransformNode()
      correctMatrix = vtk.vtkMatrix4x4()
      correctMatrix.SetElement(0,0,1); correctMatrix.SetElement(0,1,0); correctMatrix.SetElement(0,2,0); correctMatrix.SetElement(0,3,-20)
      correctMatrix.SetElement(1,0,0); correctMatrix.SetElement(1,1,1); correctMatrix.SetElement(1,2,0); correctMatrix.SetElement(1,3,59)
      correctMatrix.SetElement(2,0,0); correctMatrix.SetElement(2,1,0); correctMatrix.SetElement(2,2,1); correctMatrix.SetElement(2,3,18.2)
      correctMatrix.SetElement(3,0,0); correctMatrix.SetElement(3,1,0); correctMatrix.SetElement(3,2,0); correctMatrix.SetElement(3,3,1)
      correctTransform.SetAndObserveMatrixTransformToParent(correctMatrix)
      self.assertTrue(self.compareTransformNodes(widget.plannedTargetTransform, correctTransform))
      self.delayDisplay(f'<font color="#72ff6b">Target Matrix matches known correct values</font>')      

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
      raise Exception("Exception occurred during testing")
    
    widget.cleanup()
    widget.parent.deleteLater()
  
  # Integrated Testing

  def test_NormalOperation(self):
    widget = self.setUp()
    try:
      self.delayDisplay("<h2>Starting Normal Operation Test</h2>")

      volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
      templateImageNode = slicer.util.loadVolume(volumePathTemplate)
      volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
      anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

      widget.onCreateRobotClientButtonClicked()
      slicer.util.delayDisplay("Starting connection with robot", 3000)

      widget.onStartupButtonClicked()
      slicer.util.delayDisplay("Sent START_UP request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "START_UP")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      widget.onCalibrationButtonClicked()
      slicer.util.delayDisplay("Sent CALIBRATION request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "CALIBRATION")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      slicer.util.delayDisplay("Performing Registration", 1000)
      widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
      widget.onRegister()
      
      widget.onSendCalibrationMatrixButtonClicked()
      slicer.util.delayDisplay("Sent Calibration Matrix", 3000)
      self.assertTrue(self.compareTransformNodes(widget.outputTransform, slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")))
      self.delayDisplay(f'<font color="#72ff6b">Calibration Matrix matches ACK</font>')
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      slicer.util.delayDisplay("Selecting Target", 1000)
      widget.onAddTarget()
      widget.targetPointNodeSelector.currentNode().AddFiducial(-20, 59, 18.2)
      interactionNode = slicer.app.applicationLogic().GetInteractionNode()
      interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)

      widget.onPlanningButtonClicked()
      slicer.util.delayDisplay("Sent PLANNING request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "PLANNING")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      widget.onTargetingButtonClicked()
      slicer.util.delayDisplay("Sending TARGETING request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "TARGETING")
      self.assertTrue(self.compareTransformNodes(widget.plannedTargetTransform, slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")))
      self.delayDisplay(f'<font color="#72ff6b">Target Matrix matches ACK</font>')
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
      raise Exception("Exception occurred during testing")
    
    widget.onDisconnectFromSocketButtonClicked()
    slicer.util.delayDisplay("Disconnected from robot", 1000)
    widget.cleanup()
    widget.parent.deleteLater()

  def test_NormalOperationWithPositionQuery(self):
    widget = self.setUp()
    try:
      self.delayDisplay("<h2>Starting Normal Operation with Position Query Test</h2>")

      volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
      templateImageNode = slicer.util.loadVolume(volumePathTemplate)
      volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
      anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

      widget.onCreateRobotClientButtonClicked()
      slicer.util.delayDisplay("Starting connection with robot", 3000)

      widget.onStartupButtonClicked()
      slicer.util.delayDisplay("Sent START_UP request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "START_UP")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      widget.currentPositionButton.setChecked(True)
      widget.onCurrentPositionClicked()
      slicer.util.delayDisplay("Sent CURRENT_POSITION request", 2000)

      widget.onCalibrationButtonClicked()
      slicer.util.delayDisplay("Sent CALIBRATION request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "CALIBRATION")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      slicer.util.delayDisplay("Performing Registration", 1000)
      widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
      widget.onRegister()
      
      widget.onSendCalibrationMatrixButtonClicked()
      slicer.util.delayDisplay("Sent Calibration Matrix", 3000)
      self.assertTrue(self.compareTransformNodes(widget.outputTransform, slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")))
      self.delayDisplay(f'<font color="#72ff6b">Calibration Matrix matches ACK</font>')
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      slicer.util.delayDisplay("Selecting Target", 1000)
      widget.onAddTarget()
      widget.targetPointNodeSelector.currentNode().AddFiducial(-20, 59, 18.2)
      interactionNode = slicer.app.applicationLogic().GetInteractionNode()
      interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)

      widget.onPlanningButtonClicked()
      slicer.util.delayDisplay("Sent PLANNING request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "PLANNING")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      widget.onTargetingButtonClicked()
      slicer.util.delayDisplay("Sending TARGETING request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "TARGETING")
      self.assertTrue(self.compareTransformNodes(widget.plannedTargetTransform, slicer.mrmlScene.GetFirstNodeByName("ACK_Transform")))
      self.delayDisplay(f'<font color="#72ff6b">Target Matrix matches ACK</font>')
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
      raise Exception("Exception occurred during testing")
    
    widget.onDisconnectFromSocketButtonClicked()
    slicer.util.delayDisplay("Disconnected from robot", 1000)
    widget.cleanup()
    widget.parent.deleteLater()
    

  def test_ImproperCalibration(self):
    widget = self.setUp()
    try:
      self.delayDisplay("<h2>Starting Improper Calibration Test</h2>")

      volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
      templateImageNode = slicer.util.loadVolume(volumePathTemplate)
      volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
      anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

      widget.onCreateRobotClientButtonClicked()
      slicer.util.delayDisplay("Starting connection with robot", 3000)

      widget.onStartupButtonClicked()
      slicer.util.delayDisplay("Sent START_UP request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "START_UP")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      widget.onCalibrationButtonClicked()
      slicer.util.delayDisplay("Sent CALIBRATION request", 3000)
      self.delayDisplay(f'Robot in phase {widget.robot_phase}')
      self.assertEqual(widget.robot_phase, "CALIBRATION")
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

      slicer.util.delayDisplay("Performing Registration", 1000)
      widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
      widget.onRegister()

      slicer.util.delayDisplay("Adjusting Calibration matrix to be incorrect", 1000)
      registrationMatrix = vtk.vtkMatrix4x4()
      widget.outputTransform.GetMatrixTransformToParent(registrationMatrix)
      registrationMatrix.SetElement(0,0,-1); registrationMatrix.SetElement(0,1,-1); registrationMatrix.SetElement(0,2,-1)
      registrationMatrix.SetElement(1,0,-1); registrationMatrix.SetElement(1,1,-1); registrationMatrix.SetElement(1,2,-1)
      registrationMatrix.SetElement(2,0,-1); registrationMatrix.SetElement(2,1,-1); registrationMatrix.SetElement(2,2,-1)
      widget.outputTransform.SetAndObserveMatrixTransformToParent(registrationMatrix)
      
      widget.onSendCalibrationMatrixButtonClicked()
      slicer.util.delayDisplay("Sent Incorrect Calibration Matrix", 3000)
      self.assertEqual(widget.robotStatusCodeTextbox.text, "STATUS_CONFIG_ERROR")
      self.delayDisplay(f'<font color="#72ff6b">Error received from Robot</font>')
      slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
      raise Exception("Exception occurred during testing")
    
    widget.onDisconnectFromSocketButtonClicked()
    slicer.util.delayDisplay("Disconnected from robot", 1000)
    widget.cleanup()
    widget.parent.deleteLater()

  def test_OutOfBounds(self):
    pass
    # widget = self.setUp()
    # try:
    #   self.delayDisplay("<h2>Starting Out of Bounds Test</h2>")

    #   volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
    #   templateImageNode = slicer.util.loadVolume(volumePathTemplate)
    #   volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
    #   anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

    #   widget.onCreateRobotClientButtonClicked()
    #   slicer.util.delayDisplay("Starting connection with robot", 3000)

    #   widget.onStartupButtonClicked()
    #   slicer.util.delayDisplay("Sent START_UP request", 3000)
    #   self.delayDisplay(f'Robot in phase {widget.robot_phase}')
    #   self.assertEqual(widget.robot_phase, "START_UP")
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    #   widget.onCurrentPositionClicked()
    #   slicer.util.delayDisplay("Sent START_UP request", 3000)

    #   widget.onCalibrationButtonClicked()
    #   slicer.util.delayDisplay("Sent CALIBRATION request", 3000)
    #   self.delayDisplay(f'Robot in phase {widget.robot_phase}')
    #   self.assertEqual(widget.robot_phase, "CALIBRATION")
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    #   slicer.util.delayDisplay("Performing Registration", 1000)
    #   widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
    #   widget.onRegister()

    #   slicer.util.delayDisplay("Adjusting Calibration matrix to be incorrect", 1000)
    #   registrationMatrix = vtk.vtkMatrix4x4()
    #   widget.outputTransform.GetMatrixTransformToParent(registrationMatrix)
    #   registrationMatrix.SetElement(0,0,-1); registrationMatrix.SetElement(0,1,-1); registrationMatrix.SetElement(0,2,-1)
    #   registrationMatrix.SetElement(1,0,-1); registrationMatrix.SetElement(1,1,-1); registrationMatrix.SetElement(1,2,-1)
    #   registrationMatrix.SetElement(2,0,-1); registrationMatrix.SetElement(2,1,-1); registrationMatrix.SetElement(2,2,-1)
    #   widget.outputTransform.SetAndObserveMatrixTransformToParent(registrationMatrix)
      
    #   widget.onSendCalibrationMatrixButtonClicked()
    #   slicer.util.delayDisplay("Sent Incorrect Calibration Matrix", 3000)
    #   self.assertEqual(self.robotStatusCodeTextbox.text, "STATUS_CONFIG_ERROR")
    #   self.delayDisplay(f'Error received from Robot')
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    # except Exception as e:
    #   import traceback
    #   traceback.print_exc()
    #   self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
    #   raise Exception("Exception occurred during testing")
    
    # widget.onDisconnectFromSocketButtonClicked()
    # slicer.util.delayDisplay("Disconnected from robot", 1000)
    # widget.cleanup()
    # widget.parent.deleteLater()

  def test_EmergencyStop(self):
    pass
    # widget = self.setUp()
    # try:
    #   self.delayDisplay("<h2>Starting Emergency Stop Test</h2>")

    #   volumePathTemplate = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "2 AX TSE T2 COVER TEMPLATE.nrrd")
    #   templateImageNode = slicer.util.loadVolume(volumePathTemplate)
    #   volumePathAnatomy = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Testing", "3 AXIAL T2 COVER PROSTATE 3mm 0gap at iso.nrrd")
    #   anatomyImageNode = slicer.util.loadVolume(volumePathAnatomy)

    #   widget.onCreateRobotClientButtonClicked()
    #   slicer.util.delayDisplay("Starting connection with robot", 3000)

    #   widget.onStartupButtonClicked()
    #   slicer.util.delayDisplay("Sent START_UP request", 3000)
    #   self.delayDisplay(f'Robot in phase {widget.robot_phase}')
    #   self.assertEqual(widget.robot_phase, "START_UP")
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    #   widget.onCurrentPositionClicked()
    #   slicer.util.delayDisplay("Sent START_UP request", 3000)

    #   widget.onCalibrationButtonClicked()
    #   slicer.util.delayDisplay("Sent CALIBRATION request", 3000)
    #   self.delayDisplay(f'Robot in phase {widget.robot_phase}')
    #   self.assertEqual(widget.robot_phase, "CALIBRATION")
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    #   slicer.util.delayDisplay("Performing Registration", 1000)
    #   widget.zFrameVolumeSelector.setCurrentNode(templateImageNode)
    #   widget.onRegister()

    #   slicer.util.delayDisplay("Adjusting Calibration matrix to be incorrect", 1000)
    #   registrationMatrix = vtk.vtkMatrix4x4()
    #   widget.outputTransform.GetMatrixTransformToParent(registrationMatrix)
    #   registrationMatrix.SetElement(0,0,-1); registrationMatrix.SetElement(0,1,-1); registrationMatrix.SetElement(0,2,-1)
    #   registrationMatrix.SetElement(1,0,-1); registrationMatrix.SetElement(1,1,-1); registrationMatrix.SetElement(1,2,-1)
    #   registrationMatrix.SetElement(2,0,-1); registrationMatrix.SetElement(2,1,-1); registrationMatrix.SetElement(2,2,-1)
    #   widget.outputTransform.SetAndObserveMatrixTransformToParent(registrationMatrix)
      
    #   widget.onSendCalibrationMatrixButtonClicked()
    #   slicer.util.delayDisplay("Sent Incorrect Calibration Matrix", 3000)
    #   self.assertEqual(self.robotStatusCodeTextbox.text, "STATUS_CONFIG_ERROR")
    #   self.delayDisplay(f'Error received from Robot')
    #   slicer.util.delayDisplay(f'<font color="#72ff6b">ACK and Status received from Robot</font>', 500)

    # except Exception as e:
    #   import traceback
    #   traceback.print_exc()
    #   self.delayDisplay(f'<font color="red">Test caused exception!</font>\n {str(e)}')
    #   raise Exception("Exception occurred during testing")
    
    # widget.onDisconnectFromSocketButtonClicked()
    # slicer.util.delayDisplay("Disconnected from robot", 1000)
    # widget.cleanup()
    # widget.parent.deleteLater()