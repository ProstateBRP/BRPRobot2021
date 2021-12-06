import qt, vtk, ctk, slicer
import numpy
import os
# for epsilon
import sys
import datetime
import workflowFunctions as workflowFunctions
from ProstateBxLib.StyleUtils import modelColors
from slicer.util import VTKObservationMixin

class HMS_NeedleGuideTargetStep(ctk.ctkWorkflowWidgetStep, VTKObservationMixin):

    def __init__(self, stepID):
        VTKObservationMixin.__init__(self)
        self.initialize(stepID)
        self.setName('Target')
        self.setDescription('Select biopsy targets')
        
        self.logFileName = '4TARGET.txt'

        self.enableSendCoord = False

        self.targetScanDICOM = None
        self.targetScanDICOMID = workflowFunctions.getParameter('targetScanDICOMID')
        if self.targetScanDICOMID is not None:
            self.targetScanDICOM = slicer.mrmlScene.GetNodeByID(self.targetScanDICOMID)
            
        self.transformNode = None
        transformNodeID = workflowFunctions.getParameter('CalibrationTransformNodeID')
        if transformNodeID is not None:
            self.transformNode = slicer.mrmlScene.GetNodeByID(transformNodeID)
        else:
            print 'Run the calibration first!'

        self.trajectoryLabelVolume = None
        self.trajectoryDisplayNode = None

        # Read in colors to use with targeting models
        self.modelColors = modelColors()
        self.nonTargetScalar = 0
        self.targetScalar = 1

        # Set up a targets fiducial node
        self.targetFiducialsNode = None
        # observation tags for the fiducials
        self.fiducialsAddedTag = None
        self.fiducialsRemovedTag = None
        self.fiducialsPointModifiedTag = None
        self.fiducialsDisplayModifiedTag = None
        # Check to see if we have an id cached
        fiducialsNodeID = workflowFunctions.getParameter('targetFiducialsNodeID')
        if fiducialsNodeID is not None:
            self.targetFiducialsNode = slicer.mrmlScene.GetNodeByID(fiducialsNodeID)
        else:
            self.targetFiducialsNode = slicer.vtkMRMLMarkupsFiducialNode()
            self.targetFiducialsNode.SetName('Targets')
            # Adjust the label format so that the targets are labelled
            # as Target-N rather than Targets-N
            self.targetFiducialsNode.SetMarkupLabelFormat('Target-%d')
            slicer.mrmlScene.AddNode(self.targetFiducialsNode)
            fiducialsNodeID = self.targetFiducialsNode.GetID()
            workflowFunctions.setParameter('targetFiducialsNodeID', fiducialsNodeID)
            self.targetFiducialsNode = slicer.util.getNode(fiducialsNodeID)
            targetDisplayNode = self.targetFiducialsNode.GetDisplayNode()
            if targetDisplayNode:
                # adjust the fiducials
                targetDisplayNode.SetGlyphTypeFromString('StarBurst2D')
                targetDisplayNode.SetTextScale(2.5)
                targetDisplayNode.SetGlyphScale(3.5)
            # make a storage node so can save it for resume
            fiducialsDir = workflowFunctions.getParameter('targetLog')
            if fiducialsDir is not None:
                fiducialsFileName = os.path.normpath(os.path.join(fiducialsDir, self.targetFiducialsNode.GetName() + '.fcsv'))
                self.targetFiducialsNode.AddDefaultStorageNode(fiducialsFileName)
            else:
                workflowFunctions.popupWarning("W:401 Unable to save Targets for resuming, no target log directory found.")

        self.reregTargetsNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMarkupsFiducialNode')
        self.reregTargetsNode.UnRegister(None)
        self.reregTargetsNode.SetName("Rereg Targets")
        slicer.mrmlScene.AddNode(self.reregTargetsNode)
        self.reregTargetsNode = slicer.util.getNode('Rereg Targets')
        workflowFunctions.setParameter('reregtargetFiducialsNodeID', self.reregTargetsNode.GetID())

        self.targetTable = None
        self.columns = None
        self.setUpColumns()

        # some standard biopsy needle, cryo and laser ablation temperature effect ellipsoid sizes,
        # combo box text string and x, y, z radius for ellipsoid generation, last is the length
        # along Z (assuming insertion along Z axis). Biopsy super ellipsoid will be a cylinder offset
        # for throw from the target location.
        self.ellipsoidSizes = [["Biopsy Core 18G x 20 mm throw", 0.838, 0.838, 10], ["Biopsy Core 18G x 10 mm throw", 0.838, 0.838, 5], ["Cryo 10 x 10 x 10 mm", 10, 10, 10], ["Laser Radial 1min 6 x 6 x 6 mm", 6, 6, 6], ["Laser Radial 2min 8 x 8 x 9.5 mm", 8, 8, 9.5], ["Laser Diffuser 1min 7 x 7 x 11 mm", 7, 7, 11], ["Laser Diffuser 2min 9 x 9 x 14 mm", 9, 9, 14], ["Laser Diffuser 3min 11 x 11 x 15 mm", 11, 11, 15], ["Laser Diffuser 4min 12.5 x 12.5 x 17 mm", 12.5, 12.5, 17]]
        # The shape source for the target ellipsoids
        self.ellipsoidShapeSource = vtk.vtkParametricFunctionSource()
        # The current parameters of the shape source
        self.ellipsoidRadiusIndex = 0
        self.ellipsoidRadiusVector = self.ellipsoidSizes[self.ellipsoidRadiusIndex][1:]

        # will watch the parameter node for changes in the selected target scan
        self.parameterNodeModifiedTag = None

        # PIRADs window
        self.piradsBox = None
        self.mapLabel = None
        self.piradsMapPath = None
        self.piradsPixmap = None
        self.piradsStayOnTopCheckBox = None

    def setUpColumns(self):
        if not hasattr(self, 'widget'):
            return
        if self.targetTable is None:
            self.targetTable = workflowFunctions.get(self.widget, "TargetTable")
        # set up columns as name, header string pairs
        if workflowFunctions.getParameter('gfmPresentFlag') is 1:
            self.columns = [["Delete", "X"], ["Name", "Name"], ["RAS", "Position\n(RAS)"]]
        else:
            # when not fabricating, show the grid location in this table
            self.columns = [["Delete", "X"], ["Name", "Name"], ["Grid", "Grid"], ["Depth", "Depth\n(cm)"], ["RAS", "Position\n(RAS)"]]

        # adjust the table
        self.targetTable.setColumnCount(len(self.columns))
        self.targetTable.setHorizontalHeaderLabels(workflowFunctions.getColumnHeaders(self.columns))
        self.targetTable.horizontalHeader().setResizeMode(qt.QHeaderView.Stretch)
        self.targetTable.horizontalHeader().setResizeMode(workflowFunctions.getColumnIndex(self.columns, "Delete"), qt.QHeaderView.ResizeToContents)
        self.targetTable.verticalHeader().setResizeMode(qt.QHeaderView.ResizeToContents)


    def validate(self, desiredBranchId):
        validation = False
        warningString = ''
        # A target has been selected and targets can be sent
        numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
        if (numberOfTargets > 0) and (self.enableSendCoord is True):
            validation = True
            # make sure that all targets are inside target area
            outsideList = []
            for i in range(numberOfTargets):
                markerPos = [0.0, 0.0, 0.0]
                self.targetFiducialsNode.GetNthFiducialPosition(i, markerPos)
                inside = self.targetInZone(markerPos)
                if not inside:
                    outsideList.append(i)
            if len(outsideList) != 0:
                # check the checkbox to allow them outside, if checked
                # allow validation to pass
                allowOutsideFlag = False
                if workflowFunctions.getParameter('devModeFlag') == 1 and self.allowOutsideTargetsCheckBox.visible == True:
                    allowOutsideFlag = self.allowOutsideTargetsCheckBox.checked
                if not allowOutsideFlag:
                    validation = False
                    warningString = warningString + "W:402 You must have all targets within the target zone.\nTargets outside the zone:"
                    for outsideIndex in range(len(outsideList)):
                        warningString = warningString + "\n    " + self.targetFiducialsNode.GetNthFiducialLabel(outsideList[outsideIndex])
                    warningString = warningString + "\n\n"
        else:
            warningString = warningString + "W:411 You must add at least one target.\n\n"
        if not validation:
            workflowFunctions.popupWarning(warningString)
        super(HMS_NeedleGuideTargetStep, self).validate(validation, desiredBranchId)

    def createUserInterface(self):
        layout = qt.QVBoxLayout(self)

        self.widget = workflowFunctions.loadUI('HMS_NeedleGuideTarget.ui')
        if self.widget is None:
            print 'ERROR: unable to load Target step UI file'
            return
        layout.addWidget(self.widget)

        self.resourcePath = workflowFunctions.getParameter('resources')
        
        self.targetScanLabel = workflowFunctions.get(self.widget, "TargetScanLabel")

        self.createTargetZoneButton = workflowFunctions.get(self.widget, "CreateTargetZoneButton")
        self.createTargetZoneButton.connect('clicked(bool)',self.runGreenZone)
        workflowFunctions.colorPushButtonFromPalette(self.createTargetZoneButton, 'Secondary')

        # for testing, allow not deleting the targets outside the green zone
        self.allowOutsideTargetsCheckBox = workflowFunctions.get(self.widget, "AllowOutsideTargetsCheckBox")
        if workflowFunctions.getParameter('devModeFlag') == 1:
            self.allowOutsideTargetsCheckBox.visible = True
        else:
            self.allowOutsideTargetsCheckBox.visible = False

        self.addTargetButton = workflowFunctions.get(self.widget, "AddTargetButton")
        workflowFunctions.setButtonIcon(self.addTargetButton, 'Large/lg_target.png')
        self.addTargetButton.connect('clicked(bool)',self.onAddTargetButtonPressed)
        workflowFunctions.colorPushButtonFromPalette(self.addTargetButton, 'Primary')

        # Add a shortcut for adding a target
        altA = qt.QKeySequence("Alt+A")
        shortCut = qt.QShortcut(altA, self.addTargetButton)
        shortCut.connect('activated()', self.onAddTargetButtonPressed)

        self.addManualTargetButton = workflowFunctions.get(self.widget, "AddManualTargetButton")
        workflowFunctions.setButtonIcon(self.addManualTargetButton, 'Small/sm_blue1target.png')
        self.addManualTargetButton.connect('clicked(bool)',self.onAddManualTarget)
        workflowFunctions.colorPushButtonFromPalette(self.addManualTargetButton, 'Secondary')

        # Display options
        # Checkbox to show/hide the targets list
        self.showTargetsCheckBox  = workflowFunctions.get(self.widget, "showTargetsCheckBox")
        self.showTargetsCheckBox.connect('toggled(bool)', self.onShowTargets)

        #  Checkboxes to toggle displaying models/overlays
        self.showSheetCheckBox = workflowFunctions.get(self.widget, "showSheetCheckBox")
        self.showSheetCheckBox.connect('toggled(bool)', self.onShowSheet)
        self.showSheetCheckBox.checked = workflowFunctions.getParameter('SHEET_VIS_Flag')

        self.showSolidSheetCheckBox = workflowFunctions.get(self.widget, "showSolidSheetCheckBox")
        self.showSolidSheetCheckBox.connect('toggled(bool)', self.onShowSolidSheet)
        self.showSolidSheetCheckBox.checked = workflowFunctions.getParameter('SHEET_SOLID_VIS_Flag')

        # Model showing the green target zone
        self.showTargetZoneCheckBox = workflowFunctions.get(self.widget, "showTargetZoneCheckBox")
        self.showTargetZoneCheckBox.connect('toggled(bool)', self.onShowTargetZone)
        self.showTargetZoneCheckBox.checked = workflowFunctions.getParameter('TARGET_ZONE_VIS_Flag')

        # Volume showing needle paths to targets
        self.showTrajectoriesLabelCheckBox = workflowFunctions.get(self.widget, "showTargetTrajectoriesCheckBox")
        self.showTrajectoriesLabelCheckBox.connect('toggled(bool)', self.onShowTrajectoriesLabelNode)
        self.showTrajectoriesLabelCheckBox.checked = workflowFunctions.getParameter('TARGET_PATH_VIS_Flag')

        # Model showing needle paths to target
        self.showTargetTrajectoriesCheckBox = workflowFunctions.get(self.widget, "show3DTargetTrajectoriesCheckBox")
        self.showTargetTrajectoriesCheckBox.connect('toggled(bool)', self.onShowTargetTrajectories)
        self.showTargetTrajectoriesCheckBox.checked = workflowFunctions.getParameter('TARGET_PATH_3D_VIS_Flag')

        # Show slice intersections
        self.sliceIntersectionsCheckBox = workflowFunctions.get(self.widget, "showSliceIntersectionsCheckBox")
        self.sliceIntersectionsCheckBox.connect('toggled(bool)', self.onShowSliceIntersections)
        self.sliceIntersectionsCheckBox.checked = workflowFunctions.getParameter('sliceIntersectionsFlag')

        # Show ellipsoids around targets
        self.showEllipsoidsCheckBox = workflowFunctions.get(self.widget, "showTargetEllipsoidsCheckBox")
        self.showEllipsoidsCheckBox.connect('toggled(bool)', self.onShowTargetEllipsoids)
        self.showEllipsoidsCheckBox.checked = workflowFunctions.getParameter('TARGET_ELLIPSOIDS_VIS_Flag')

        # Ellipsoids shape drop down
        self.ellipsoidsComboBox = workflowFunctions.get(self.widget, "targetEllipsoidsComboBox")
        # populate with standard sizes
        for ellipsoidSize in self.ellipsoidSizes:
            # add the radius information as a vector in the item's data field
            ellipsoidRadii = qt.QVector3D()
            ellipsoidRadii.setX(ellipsoidSize[1])
            ellipsoidRadii.setY(ellipsoidSize[2])
            ellipsoidRadii.setZ(ellipsoidSize[3])
            self.ellipsoidsComboBox.addItem(ellipsoidSize[0], ellipsoidRadii)
        self.ellipsoidsComboBox.setCurrentIndex(0)
        # update when selection changes
        self.ellipsoidsComboBox.connect('currentIndexChanged(int)', self.onEllipsoidTypeChanged)

        #  PIRADS guidance
        self.showPIRADSButton = workflowFunctions.get(self.widget, "ShowPIRADSButton")
        self.showPIRADSButton.connect('clicked(bool)', self.onShowPIRADS)


        # Set up the table of target fiducials
        self.targetTable = workflowFunctions.get(self.widget, "TargetTable")
        self.targetTable.alternatingRowColors = True
        self.targetTable.horizontalHeader().setResizeMode(qt.QHeaderView.Stretch)
        self.targetTable.itemChanged.connect(self.onTargetNameChange)
        self.targetTable.cellClicked.connect(self.onTableSelect)
        self.targetTable.verticalHeader().sectionClicked.connect(self.onGotoTarget)
        self.targetTable.setContextMenuPolicy(qt.Qt.CustomContextMenu)
        self.targetTable.connect('customContextMenuRequested(QPoint)', self.onRightClickTable)
    
    def onEntry(self, comingFrom, transitionType):
        comingFromId = "None"
        if comingFrom:
            comingFromId = comingFrom.id()
        super(HMS_NeedleGuideTargetStep, self).onEntry(comingFrom, transitionType)

        layoutNode = slicer.util.getNode('Layout')

        layoutNode.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutInitialView)

        workflowFunctions.sendIGTString("TARG")

        # make sure we have the models
        self.createSheetOutlineModel()
        self.createSolidSheetModel()
        self.createGuideHolesModel()
        self.createTargetEllipsoidsModel()

        # unlock the fidicuals
        if self.targetFiducialsNode is not None:
            self.targetFiducialsNode.SetLocked(0)
            # if resumed, need to show them
            self.targetFiducialsNode.SetDisplayVisibility(True)

        # set up observers on targets and parameter nodes
        self.addObservers()

        self.targetScanDICOMID = workflowFunctions.getParameter('targetScanDICOMID')
        self.targetScanDICOM = None
        if self.targetScanDICOMID is not None:
          self.targetScanDICOM = slicer.mrmlScene.GetNodeByID(self.targetScanDICOMID)
        if self.targetScanDICOM is not None:
          workflowFunctions.setVolumeLabel(self.targetScanLabel, self.targetScanDICOM.GetName())
          # show the target volume in the slices
          workflowFunctions.setActiveVolume(self.targetScanDICOMID)
          self.runGreenZone()
        else:
          workflowFunctions.setVolumeLabel(self.targetScanLabel, '')

        # Adjust in case GFM present flag changed
        self.setUpColumns()

        # show the axial slice in 3D
        redSlice = slicer.util.getNode('vtkMRMLSliceNodeRed')
        if redSlice is not None:
            redSlice.SetSliceVisible(1)

        # set up display options after have the volume set
        workflowFunctions.reset3DCameraOnGrid()
        # Make sure slice intersections are still set as the view has changed
        self.onShowSliceIntersections()

        # Update the GUI
        self.updateTargetTable()
        # Scroll to the bottom
        if self.targetTable.rowCount > 0:
            self.targetTable.scrollToBottom()

        # Show the target green zone if it was hidden
        self.onShowTargetZone()

        # zoom in on slices after everything is set up (focuses on green zone cube)
        workflowFunctions.fitToSlices()

    def onExit(self, goingTo, transitionType):
        # save the fiducials list
        if self.targetFiducialsNode is not None:
            storageNode = self.targetFiducialsNode.GetStorageNode()
            if storageNode is not None:
                storageNode.WriteData(self.targetFiducialsNode)
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print 'TargetStep: saved ', storageNode.GetFileName()
        # hide the target cube
        self.setTargetZoneVisibility(0)
        # hide the needle paths
        workflowFunctions.setLabelVolume(None)
        self.setTargetNeedlePathVisibility(0)
        # hide the guide sheet
        self.setSheetVisibility(0)
        self.setSolidSheetVisibility(0)
        # self.setGuideHolesVisibility(0)
        # keep the guide hole tubes showing, but remove the target colouring
        self.colorGuideHolesModel()

        # remove observers on the fiducial node
        self.removeObservers()

        # lock the fiducial node so can't adjust the location of targets
        if self.targetFiducialsNode is not None:
            self.targetFiducialsNode.SetLocked(1)

        goingToId = "None"
        if goingTo:
            goingToID = goingTo.id()
        # execute the transition
        super(HMS_NeedleGuideTargetStep, self).onExit(goingTo, transitionType)

    # Check if there's a fiducial node for the targets and if it doesn't already
    # have observers on it, add them. Will remove observers on any previously
    # defined targets list.
    # Add an observer on the parameter node to track changes in the target
    # scan selection.
    def addObservers(self):
        fiducialsNodeID = workflowFunctions.getParameter('targetFiducialsNodeID')
        if fiducialsNodeID is not None:
            self.removeObservers()

            # reset the node pointer
            self.targetFiducialsNode = slicer.mrmlScene.GetNodeByID(fiducialsNodeID)

        if self.targetFiducialsNode is None:
            print 'ERROR: addObservers unable to get the targets node with id',fiducialsNodeID
            return

        # add observers for updating the GUI
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'TargetStep: adding observers to ',self.targetFiducialsNode.GetID()
        self.fiducialsAddedTag = self.targetFiducialsNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onFiducialsAdded)
        self.fiducialsRemovedTag = self.targetFiducialsNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupRemovedEvent, self.onFiducialRemoved)
        self.fiducialsPointModifiedTag =  self.targetFiducialsNode.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onFiducialPointModified)
        # for ellipsoids, hiding/showing them when fids are hidden/shown
        self.fiducialsDisplayModifiedTag = self.targetFiducialsNode.AddObserver(slicer.vtkMRMLMarkupsNode.NthMarkupModifiedEvent, self.onFiducialsDisplayModified)

        parameterNode = workflowFunctions.getParameterNode()
        if parameterNode is not None:
            if self.parameterNodeModifiedTag is not None:
                parameterNode.RemoveObserver(self.parameterNodeModifiedTag)
            self.parameterNodeModifiedTag = parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onParameterNodeModified)
        else:
            self.parameterNodeModifiedTag = None

    def removeObservers(self):
        if self.parameterNodeModifiedTag is not None:
            parameterNode = workflowFunctions.getParameterNode()
            if parameterNode is not None:
                parameterNode.RemoveObserver(self.parameterNodeModifiedTag)
            self.parameterNodeModifiedTag = None

        if self.targetFiducialsNode is not None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'TargetStep: removing observers on ',self.targetFiducialsNode.GetID()
            if self.fiducialsAddedTag is not None:
                self.targetFiducialsNode.RemoveObserver(self.fiducialsAddedTag)
                self.fiducialsAddedTag = None
            if self.fiducialsRemovedTag is not None:
                self.targetFiducialsNode.RemoveObserver(self.fiducialsRemovedTag)
                self.fiducialsRemovedTag = None
            if self.fiducialsPointModifiedTag is not None:
                self.targetFiducialsNode.RemoveObserver(self.fiducialsPointModifiedTag)
                self.fiducialsPointModifiedTag = None
            if self.fiducialsDisplayModifiedTag is not None:
                self.targetFiducialsNode.RemoveObserver(self.fiducialsDisplayModifiedTag)
                self.fiducialsDisplayModifiedTag = None

    def createTrajectoryDisplayNode(self):
        # Create a display node for the trajectory label map volume.
        # Will set self.trajectoryDisplayNode to a valid node pointing to a custom
        # color node on success, None otherwise.
        # There will be only one, each iteration of a target zone label map will
        # point to the same display node.
        if self.trajectoryDisplayNode is not None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'createTrajectoryDisplayNode: already have one, with id ',self.trajectoryDisplayNode.GetID()
            return

        self.trajectoryDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
        slicer.mrmlScene.AddNode(self.trajectoryDisplayNode)

        # Create a custom color node
        colorNode = slicer.vtkMRMLColorTableNode()
        colorNode.SetName("HMS Trajectories Color Table")
        lookup = vtk.vtkLookupTable()
        lookup.SetNumberOfColors(3)
        lookup.SetTableValue(0,[0.5647058823529412, 0.9333333333333333, 0.5647058823529412, 0.0])
        lookup.SetTableValue(1,[0.5647058823529412, 0.9333333333333333, 0.5647058823529412, 0.2])
        lookup.SetTableValue(2,[0.90, 0.4, 0.4, 0.7])
        colorNode.SetLookupTable(lookup)

        slicer.mrmlScene.AddNode(colorNode)
        self.trajectoryDisplayNode.SetAndObserveColorNodeID(colorNode.GetID())

    def createTrajectoriesLabelNode(self):
        # From the current target volume, create a label map volume that will show
        # the trajectories as drawn lines.
        # Will set the self.trajectoryLabelVolume to the new blank node on success,
        # to None if there's no target volume or other failure state.
        if self.targetScanDICOM is None:
            print 'createTrajectoriesLabelNode: select a target scan first!'
            return

        if (self.trajectoryLabelVolume is None) or (self.trajectoryLabelVolume.GetAttribute('AssociatedNodeID') != self.targetScanDICOM.GetID()):
            # remove any old version
            if self.trajectoryLabelVolume is not None:
                slicer.mrmlScene.RemoveNode(self.trajectoryLabelVolume)
                self.trajectoryLabelVolume = None
                self.trajectoryDisplayNode = None
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'Creating the trajectory label volume from the target scan'
            # this will set the AssociatedNodeID attribte, create a display node, copy
            # the image data but fill it with zeroes. Adds it to the scene as well.
            self.trajectoryLabelVolume = slicer.modules.volumes.logic().CreateAndAddLabelVolume(self.targetScanDICOM, 'HMS_Trajectories')
            # make a custom display node
            self.createTrajectoryDisplayNode()
            self.trajectoryLabelVolume.SetAndObserveDisplayNodeID(self.trajectoryDisplayNode.GetID())
            self.onShowTrajectoriesLabelNode()

            # set the direction matrix
            ijkmat = vtk.vtkMatrix4x4()
            self.targetScanDICOM.GetIJKToRASDirectionMatrix(ijkmat)
            self.trajectoryLabelVolume.SetIJKToRASDirectionMatrix(ijkmat)
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print '\tCreated trajectory label volume: ', self.trajectoryLabelVolume.GetID(), ' named ', self.trajectoryLabelVolume.GetName()

    def runGreenZone(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'runGreenZone'

        # Need to base the green zone on the current target scan
        self.targetScanDICOMID = workflowFunctions.getParameter('targetScanDICOMID')
        if self.targetScanDICOMID is None:
            print 'Error: runGreenZone unable to get the target scan DICOM id parameter'
            return
        self.targetScanDICOM = slicer.util.getNode(self.targetScanDICOMID)
        if self.targetScanDICOM is  None:
            print 'Error: runGreenZone unable to get target scan volume from id ',self.targetScanDICOMID
            return

        self.createTrajectoriesLabelNode()
        if self.trajectoryLabelVolume is None:
            print 'Error: runGreenZone: Unable to get the trajectories label volume for this target scan!'
            return

        debugFlag = (workflowFunctions.getParameter('devModeFlag') == 1)

        # corners of the green zone
        sheet = workflowFunctions.getGuideSheetCorners()
        if debugFlag:
            print 'runGreenZone: guide sheet corners:',sheet

        # follow the way the sheet outline model is made, center it around 0 so
        # transforms can be applied to it
        guideSheetCenter = numpy.array(numpy.mean(sheet, 0))
        centeredPoints = []
        for p in xrange(4):
           pos = sheet[p] - guideSheetCenter
           posArray = numpy.array(pos)
           centeredPoints.append(posArray)
        if debugFlag:
            print 'centeredPoints =\n',centeredPoints

        # now have a plane at z = 0, but need to transform the corners to
        # image space using the guide sheet transform that's inside the
        # registration transformation - use the transform to world
        transformMatrix = vtk.vtkMatrix4x4()
        transformID = workflowFunctions.getParameter('GuideSheetTransformID')
        self.transformNode = slicer.util.getNode(transformID)
        if self.transformNode is not None:
            # otherwise will use an identity transform
            self.transformNode.GetMatrixTransformToWorld(transformMatrix)

        # get sheet corners in world space
        worldSheet = numpy.zeros((4,4))
        for x in xrange(4):
            transformMatrix.MultiplyPoint(numpy.append(centeredPoints[x],1),worldSheet[x])
        if debugFlag:
            print 'Transformed sheet corners: ', worldSheet

        # Get the vectors along the transformed sheet sides
        # vector from corner 0 to corner 3
        vectorX = [0,0,0]
        for i in range(3):
            vectorX[i] =  worldSheet[0][i] - worldSheet[3][i]
        # vector from corner 0 to corner 1
        vectorY = [0,0,0]
        for i in range(3):
            vectorY[i] = worldSheet[0][i] - worldSheet[1][i]
        # cross project to get the projection along Z, pointing Superior
        vectorZ = numpy.cross(numpy.array(vectorY), numpy.array(vectorX))
        mag = numpy.sqrt(vectorZ[0]*vectorZ[0] + vectorZ[1]*vectorZ[1] + vectorZ[2]*vectorZ[2])
        if debugFlag:
            print 'Z = ', vectorZ, ', mag = ', mag
        vectorZ = vectorZ / mag
        if debugFlag:
            print 'Projection vectors:\n\tX = ', vectorX, '\n\tY = ', vectorY, '\n\tZ = ', vectorZ

        # now project that sheet onto the target volume to get end caps of a cube that are
        # positioned at it's lower and upper bounds axially


        # target volume bounds
        targetRASBounds = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.targetScanDICOM.GetRASBounds(targetRASBounds)
        if debugFlag:
            print '\ttargetBounds = ', targetRASBounds
        targetZ = [0,0]
        targetZ[0] = targetRASBounds[4]
        targetZ[1] = targetRASBounds[5]
        if debugFlag:
            print '\ttarget Z = ', targetZ

        cubeCorners = []
        # Generate the cube face closer to the guide sheet.
        # To project the sheet onto the face of the target volume, the distance in Z between
        # the volume's RAS bound and this sheet corner (the volume is more inferior thatn the sheet)
        # is projected onto the vector along the Z axis. The cube is squared off at the ends of
        # the volume, using the Z coordinate of the RAS bound.
        for p in xrange(4):
            sheetCorner = worldSheet[p]
            cubeCorner = [0.0, 0.0, 0.0]
            cubeCorner[0] = sheetCorner[0] + ((targetZ[0] - sheetCorner[2]) * vectorZ[0])
            cubeCorner[1] = sheetCorner[1] + ((targetZ[0] - sheetCorner[2]) * vectorZ[1])
            cubeCorner[2] = targetZ[0]
            if debugFlag:
                print 'z=0, p=',p,'\n\tsheetCorner = ', sheetCorner, '\n\tcubeCorner = ',cubeCorner
            cubeCorners.append(numpy.array(cubeCorner))
        # Generate the cube face further from the guide sheet
        for p in xrange(4):
            sheetCorner = worldSheet[p]
            cubeCorner = [0.0, 0.0, 0.0]
            cubeCorner[0] = sheetCorner[0] + ((targetZ[1] - sheetCorner[2]) * vectorZ[0])
            cubeCorner[1] = sheetCorner[1] + ((targetZ[1] - sheetCorner[2])* vectorZ[1])
            cubeCorner[2] = targetZ[1]
            if debugFlag:
                print 'z=1, p=',p,'\n\tsheetCorner = ', sheetCorner, '\n\tcubeCorner = ',cubeCorner
            cubeCorners.append(numpy.array(cubeCorner))
        if debugFlag:
            print '\tcubeCorners =',cubeCorners



        # Create a cube model that extends the guide sheet across the target
        # volume using the above cube corners, so can test if potential targets
        # are inside of it.
        cubeModel = slicer.util.getNode('GreenZoneCube')
        if cubeModel is None:
            cubeModel = slicer.vtkMRMLModelNode()
            cubeModel.SetName('GreenZoneCube')
            slicer.mrmlScene.AddNode(cubeModel)
            cubeModel.CreateDefaultDisplayNodes()
            disp = cubeModel.GetDisplayNode()
            disp.SetOpacity(0.5)
            disp.SetSliceIntersectionVisibility(1)
            greenColor = self.modelColors['GreenZone']
            disp.SetColor(greenColor.redF(), greenColor.greenF(), greenColor.blueF())
            # Create a polydata to use as the source for the cube model.
            greenZonePolyData = vtk.vtkPolyData()
            cubeModel.SetAndObservePolyData(greenZonePolyData)

        greenZonePolyData = cubeModel.GetPolyData()
        # Clear it out
        greenZonePolyData.Initialize()
        # Add Points
        greenZonePoints = vtk.vtkPoints()
        greenZonePolyData.SetPoints(greenZonePoints)


        # For first face of cube, it's the first four points in the
        # cube corners array, then second face is last four points in the array
        p1 = numpy.array(cubeCorners[0][:3])
        p2 = numpy.array(cubeCorners[1][:3])
        p3 = numpy.array(cubeCorners[2][:3])
        p4 = numpy.array(cubeCorners[3][:3])
        if debugFlag:
            cubeFids = slicer.util.getNode('Cube')
            if cubeFids is None:
                cubeFids = slicer.vtkMRMLMarkupsFiducialNode()
                cubeFids.SetName("Cube")
                slicer.mrmlScene.AddNode(cubeFids)
            else:
                cubeFids.RemoveAllMarkups()
            cubeFids.AddFiducialFromArray(p1, '0')
            cubeFids.AddFiducialFromArray(p2, '1')
            cubeFids.AddFiducialFromArray(p3, '2')
            cubeFids.AddFiducialFromArray(p4, '3')
            print 'greenzonepoly data near face'
            print p1
            print p2
            print p3
            print p4
        greenZonePolyData.GetPoints().InsertNextPoint(p1)
        greenZonePolyData.GetPoints().InsertNextPoint(p2)
        greenZonePolyData.GetPoints().InsertNextPoint(p3)
        greenZonePolyData.GetPoints().InsertNextPoint(p4)
        p1 = numpy.array(cubeCorners[4][:3])
        p2 = numpy.array(cubeCorners[5][:3])
        p3 = numpy.array(cubeCorners[6][:3])
        p4 = numpy.array(cubeCorners[7][:3])
        if debugFlag:
            cubeFids.AddFiducialFromArray(p1, '4')
            cubeFids.AddFiducialFromArray(p2, '5')
            cubeFids.AddFiducialFromArray(p3, '6')
            cubeFids.AddFiducialFromArray(p4, '7')
            print 'greenzonepoly data far side'
            print p1
            print p2
            print p3
            print p4
        greenZonePolyData.GetPoints().InsertNextPoint(p1)
        greenZonePolyData.GetPoints().InsertNextPoint(p2)
        greenZonePolyData.GetPoints().InsertNextPoint(p3)
        greenZonePolyData.GetPoints().InsertNextPoint(p4)

        # create a cube by joining up the points
        self.createCubeLines(cubeModel)

        # log info on target volume node
        self.writeLog("Target scan:\n"+self.targetScanDICOM.GetName())
        workflowFunctions.setStatusLabel("Waiting for user to create targets")

    def createCubeLines(self, cubeModel):
        greenZonePolyData = cubeModel.GetPolyData()
        if greenZonePolyData is None:
           print 'createCubeLines: no polydata to work from'
           return
        # The input green zone cube has it's points set, define polygons between
        # them so that the inside check on the polydata will work as expected

        # Allocate space for the 12 triangles that define the 6 faces of a cube
        greenZonePolyData.Allocate(12)
        # Create triangulated surfaces connecting the corners of the square
        # Connect the front face points (0-3) in two triangles, the back face
        # points (4-7) in another pair of triangles, then add the ones filling
        # in around them.

        # An array holding the point ids of the corners of all the triangles.
        # Triangles need to be defined counter clockwise when looking at them
        # from the outside.
        # Note: the current calibrator registration has a 180 degree rotation from
        # original, so the face names are not quite lined up
        trianglePointIds = []
        # front face
        trianglePointIds.append((0,3,2))
        trianglePointIds.append((0,2,1))
        #  back face
        trianglePointIds.append((7,5,6))
        trianglePointIds.append((7,4,5))
        #  top face
        trianglePointIds.append((5,2,6))
        trianglePointIds.append((5,1,2))
        #  side face
        trianglePointIds.append((4,1,5))
        trianglePointIds.append((4,0,1))
        # bottom face
        trianglePointIds.append((7,0,4))
        trianglePointIds.append((7,3,0))
        # side face
        trianglePointIds.append((6,3,7))
        trianglePointIds.append((6,2,3))

        # then create and add the triangles
        numTriangles = len(trianglePointIds)
        for i in xrange(numTriangles):
            triangle = vtk.vtkTriangle()
            triPoints = trianglePointIds[i]
            triangle.GetPointIds().SetId(0, triPoints[0])
            triangle.GetPointIds().SetId(1, triPoints[1])
            triangle.GetPointIds().SetId(2, triPoints[2])

            ret = greenZonePolyData.InsertNextCell(triangle.GetCellType(), triangle.GetPointIds())
            if ret == -1:
                print 'ERROR adding triangle ', i, ' to target boundary cube!'

    def drawTrajectories(self):
        # clear out the label volume, redraw trajectories for all fiducials in the
        # targets list
        if self.trajectoryLabelVolume is None or self.trajectoryLabelVolume.GetImageData() is None:
            return
        slicer.modules.volumes.logic().ClearVolumeImageData(self.trajectoryLabelVolume)
        numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
        for i in range(numberOfTargets):
            markerPos = [0.0, 0.0, 0.0]
            self.targetFiducialsNode.GetNthFiducialPosition(i, markerPos)
            self.drawTrajectory(markerPos, self.trajectoryLabelVolume,self.transformNode)

    def drawTrajectory(self, markerPos, inImageLabel, trans):

        if inImageLabel is None:
            print 'drawTrajectory: no green zone label image upon which to draw'
            return

        inImage = inImageLabel.GetImageData()
        if inImage is None:
            print 'Warning: drawTrajectory has no input image on which to draw'

        sheet = workflowFunctions.getGuideSheetCorners()
        # print 'drawTrajectory: guide sheet corners = ',sheet
        worldSheet = numpy.zeros((4,4))
        transformMatrix = vtk.vtkMatrix4x4()
        trans.GetMatrixTransformToParent(transformMatrix)
        for x in xrange(4):
            transformMatrix.MultiplyPoint(numpy.append(sheet[x],1),worldSheet[x])
        # print worldSheet

        labelVolumeRASBounds = [0.0,0.0,0.0,0.0,0.0,0.0]


        inImageLabel.GetRASBounds(labelVolumeRASBounds)

        imageBounds = [0.0,0.0,0.0,0.0,0.0,0.0]
        imageExtent = [0,0,0,0,0,0]
        if inImage is not None:
            inImage.GetBounds(imageBounds)
            imageExtent = inImage.GetExtent()

        # print imageBounds
        # print labelVolumeRASBounds
        # print markerPos

        v1 = numpy.array([worldSheet[0][0]-worldSheet[1][0],worldSheet[0][1]-worldSheet[1][1],worldSheet[0][2]-worldSheet[1][2]])
        v2 = numpy.array([worldSheet[0][0]-worldSheet[2][0],worldSheet[0][1]-worldSheet[2][1],worldSheet[0][2]-worldSheet[2][2]])
        proj = numpy.cross(v1,v2)
        mag = numpy.sqrt(proj[0]*proj[0] + proj[1]*proj[1] + proj[2]*proj[2])
        proj = proj/mag
        # print proj

        spacings = inImageLabel.GetSpacing()

        checkZ = markerPos[2]
        while (checkZ  >= labelVolumeRASBounds[4]):
            trajPoint = [0.0, 0.0, 0.0]
            trajPoint[0] = (checkZ - labelVolumeRASBounds[4]) * proj[0] + markerPos[0]
            trajPoint[1] = (checkZ - labelVolumeRASBounds[4]) * proj[1] + markerPos[1]
            trajPoint[2] = checkZ
            trajImPoint = [0, 0, 0]
            trajImPoint[0] = int((labelVolumeRASBounds[1]-trajPoint[0])/spacings[0])
            trajImPoint[1] = int((labelVolumeRASBounds[3]-trajPoint[1])/spacings[1])
            trajImPoint[2] = int((trajPoint[2]-labelVolumeRASBounds[4])/spacings[2])-1
            if inImage is not None:
                # double check Z due to off by one error
                if (trajImPoint[2] >= imageExtent[4]) and (trajImPoint[2] <= imageExtent[5]):
                    inImage.SetScalarComponentFromDouble(trajImPoint[0],trajImPoint[1],trajImPoint[2],0,2)
            checkZ = checkZ - spacings[2]

        # print "****FINISHED LINE*******"

        if inImage is not None:
            inImageLabel.SetAndObserveImageData(inImage)
        # print '\tdone drawTraj'

    def delClick(self, num):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print "DEL BUTTON CLICK, row ", num
        targetPos = [0,0,0]
        self.targetFiducialsNode.GetNthFiducialPosition(num,targetPos)
        targetPosStr = workflowFunctions.formatPositionString(targetPos)
        # confirm delete
        targetLabel = self.targetFiducialsNode.GetNthFiducialLabel(num)
        msg = 'Delete target ' + targetLabel + ' at ' + targetPosStr + '?'
        if workflowFunctions.popupQuestion('Delete Target', msg, 'HMS/Target/AlwaysDeleteTarget'):
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'Deleting target ',num
            self.writeLog("Target deleted: " + self.targetFiducialsNode.GetNthFiducialLabel(num) + "\n" + str(targetPos))
            self.targetFiducialsNode.RemoveMarkup(num)
            numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
            if (numberOfTargets == 0):
                self.enableSendCoords = False
            self.enableTargetButton(True)

    def onAddTargetButtonPressed(self):
        interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        mouseMode = slicer.qSlicerMouseModeToolBar()
        # check if already in place mode
        if interactionNode.GetInteractionModeAsString() == 'Place':
            if selectionNode.GetActivePlaceNodeClassName() == 'vtkMRMLMarkupsFiducialNode':
                # already in single place target mode, cancel
                interactionNode.SwitchToViewTransformMode()
                # cursor and button back to normal
                mouseMode.changeCursorTo(qt.QCursor(0))
                self.enableTargetButton(True)
            else:
                # might be placing a ruler, inform and ignore
                workflowFunctions.popupInfo("Already placing another marker, finish or cancel that task first.")
        else:
            # place a target
            slicer.modules.markups.logic().SetActiveListID(self.targetFiducialsNode)
            interactionNode.SwitchToSinglePlaceMode()
            mouseMode.changeCursorTo(qt.QCursor(2))
            self.enableTargetButton(False)

    def onAddManualTarget(self):
        # add a target at center of green zone if it exists then pop up an edit window
        pos = [0,0,0]
        cubeModel = slicer.util.getNode('GreenZoneCube')
        if cubeModel is not None and cubeModel.GetPolyData() is not None:
            pd = cubeModel.GetPolyData()
            # calculate center of mass
            centerOfMass = vtk.vtkCenterOfMass()
            centerOfMass.SetInputData(pd)
            centerOfMass.Update()
            pos = centerOfMass.GetCenter()
        n = self.targetFiducialsNode.AddFiducialFromArray(pos)
        # trigger the edit box
        self.targetTable.selectRow(n)
        self.onAdjustTargetTriggered()

    def onFiducialsAdded(self,caller,event):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onFiducialsAdded: event = ', event, ', markup added = ',slicer.vtkMRMLMarkupsNode.MarkupAddedEvent
        if caller.IsA('vtkMRMLMarkupsFiducialNode'):
            #if (self.targetFiducialsNode.GetNumberOfFiducials() != self.numberOfTargets):
            tempPos = [0.0,0.0,0.0]
            fidNumber = self.targetFiducialsNode.GetNumberOfFiducials()-1
            self.targetFiducialsNode.GetNthFiducialPosition(fidNumber, tempPos)
            allowOutsideFlag = False
            if workflowFunctions.getParameter('devModeFlag') == 1 and self.allowOutsideTargetsCheckBox.visible == True:
                allowOutsideFlag = self.allowOutsideTargetsCheckBox.checked
            inside = self.targetInZone(tempPos)
            if inside or allowOutsideFlag:
                self.writeLog("Target Added: " + self.targetFiducialsNode.GetNthFiducialLabel(fidNumber) + "\n" + str(tempPos))
                self.updateTargetTable()
                # update inter target distances
                slicer.modules.HMS_NeedleGuideWidget.updateFiducialDistances()
                # add slice change
                self.changeFiducialSlice()
                if not inside:
                    # for testing, warning that it failed the inside test
                    workflowFunctions.popupError("Outside Target Zone", "E:405 Target outside the area covered by the needle guide,\nplease move it inside the green cube.")
            else:
                targetPosStr = workflowFunctions.formatPositionString(tempPos)
                workflowFunctions.popupError("Outside Target Zone", "E:406 Unable to add a target at this location: " + targetPosStr + "\n\nThis target falls outside the area covered by the needle guide.\n\nPlease pick a new target inside the green zone, this one will be removed.")
                self.targetFiducialsNode.RemoveMarkup(fidNumber)

    def onFiducialRemoved(self, caller, event):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onFiducialRemoved: event = ',event
        if caller.IsA('vtkMRMLMarkupsFiducialNode'):
            self.updateTargetTable()
            # also update the fiducial distances since one was removed
            slicer.modules.HMS_NeedleGuideWidget.updateFiducialDistances()

    # Slot for PointModifiedEvent that's only triggered when a fiducial
    # location changes.
    # Update the target table then the inter fiducial distances.
    @vtk.calldata_type(vtk.VTK_INT)
    def onFiducialPointModified(self, caller, event, callData):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onFiducialPointModified: event = ',event, ', callData = ', callData
        if not caller.IsA('vtkMRMLMarkupsFiducialNode'):
            return
        self.updateTargetTable()
        # also update the measurements widget
        slicer.modules.HMS_NeedleGuideWidget.updateFiducialDistances()

    # Slot for NthMarkupModifiedEvent which is watched for changes to the
    # markup individual visibility (it's also thrown from SwapMarkups, and
    # set nth markup: associated node id, selected, locked, label, description.
    # Only label changes need to update the table, check for that.
    # Be careful of selected changes, if a restored Targets list is used,
    # the selection flags may be toggled.
    @vtk.calldata_type(vtk.VTK_INT)
    def onFiducialsDisplayModified(self, caller, event, callData):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onFiducialsDisplayModified: event = ',event, ', callData = ', callData
        # used for changes that don't need to be reported
        if not caller.IsA('vtkMRMLMarkupsFiducialNode'):
            return

        # check if it was from a label change
        thisLabel = caller.GetNthMarkupLabel(callData)
        nameColumn = workflowFunctions.getColumnIndex(self.columns, "Name")
        tableLabelItem = self.targetTable.item(callData, nameColumn)
        tableLabel = None
        if tableLabelItem is not None:
            tableLabel = tableLabelItem.text()
        if tableLabel is None or thisLabel == tableLabel:
            # just update the display of the ellipsoids
            self.updateTargetEllipsoidsModel()
        else:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print '\tlist and table labels do not match, just updating target table'
            self.updateTargetTable()
            # also update the fiducial distances since there was a name change
            slicer.modules.HMS_NeedleGuideWidget.updateFiducialDistances()

    def targetInZone(self, targetLocation):
        # Compare the input target location to the valid target area defined
        # by the guide sheet configuration.
        # Return True if it's inside the zone, False otherwise.
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'targetInZone:\n\tlocation = ' + str(targetLocation)

        # check against the full bounding box using an implicit function. If the function
        # value is <= 0 the tested point is inside, otherwise it's outside the cube.
        cubeModel = slicer.util.getNode('GreenZoneCube')
        if cubeModel is None:
            # no model against which to check, so everything's inside
            return True

        implicitFunction = vtk.vtkImplicitPolyDataDistance()
        # setting the input on vtkImplicitPolyDataDistance:
        # Use a vtkTriangleFilter on the polydata input.
        # This is done to filter out lines and vertices to leave only
        # polygons which are required by this algorithm for cell normals.
        implicitFunction.SetInput(cubeModel.GetPolyData())
        insideCheck = implicitFunction.FunctionValue(targetLocation)
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'insideCheck = ', insideCheck
        if insideCheck <= 0.0:
            return True
        else:
            return False


    def updateTargetTable(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'updateTargetTable'

        # this may get triggered if the target fiducial list is updated before the UI is created
        if not hasattr(self, 'widget'):
            return
        self.targetTable = workflowFunctions.get(self.widget, "TargetTable")
        if self.targetTable is None:
            return
        scrollFlag = False

        if workflowFunctions.getParameter('devModeFlag') == 1:
            print '\tTarget table signals blocked = ', self.targetTable.signalsBlocked()
        # Get the calibration transform node to apply to the points
        if self.transformNode is None:
            transformNodeID = workflowFunctions.getParameter('CalibrationTransformNodeID')
            if transformNodeID is not None:
                self.transformNode = slicer.mrmlScene.GetNodeByID(transformNodeID)

        # If there are no target fiducials, or transformNode, clear the table and return
        if (not self.targetFiducialsNode) or (not self.transformNode):
            self.targetTable.clear()
            self.targetTable.setHorizontalHeaderLabels(self.headers)
            self.enableSendCoord = False
            return

        deleteColumn = workflowFunctions.getColumnIndex(self.columns, "Delete")
        nameColumn = workflowFunctions.getColumnIndex(self.columns, "Name")
        rasColumn = workflowFunctions.getColumnIndex(self.columns, "RAS")
        gridColumn = workflowFunctions.getColumnIndex(self.columns, "Grid")
        depthColumn = workflowFunctions.getColumnIndex(self.columns, "Depth")
        if deleteColumn == -1 or nameColumn == -1 or rasColumn == -1 or gridColumn == -1 or depthColumn == -1:
            # step hasn't been fully initialised yet
            return

        self.targetTable.blockSignals(True)

        # Set the cursor shape
        mouseMode = slicer.qSlicerMouseModeToolBar()
        mouseMode.changeCursorTo(qt.Qt.ArrowCursor)
        
        
        numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
        # Don't limit number of targets
        self.enableTargetButton(True)
        self.addManualTargetButton.setEnabled(True)

        # Adjust the table to fit the number of targets
        if self.targetTable.rowCount != numberOfTargets:
            self.targetTable.setRowCount(numberOfTargets)
            scrollFlag = True

        if numberOfTargets > 0:
            self.enableSendCoord = True
        sheetHoles = []
        targetsList = []
        if workflowFunctions.getParameter('gfmPresentFlag') is 0:
            # calculate the depth and grid positions
            sheetHoles = workflowFunctions.calcGuideSheetHoles(self.targetFiducialsNode)

        cellDeleteIcon = qt.QIcon(os.path.join(self.resourcePath, "Icons/Small/sm_bkdelete-target"))
        for i in range(numberOfTargets):
            # add a delete option in the first column
            cellDelete = qt.QTableWidgetItem()
            cellDelete.setTextAlignment(qt.Qt.AlignCenter)
            cellDelete.setIcon(cellDeleteIcon)
            self.targetTable.setItem(i, deleteColumn, cellDelete)
            
            label = self.targetFiducialsNode.GetNthFiducialLabel(i)
            markerPos = [0.0, 0.0, 0.0]
            self.targetFiducialsNode.GetNthFiducialPosition(i, markerPos)
            markerPosStr = workflowFunctions.formatPositionString(markerPos)
            inside = self.targetInZone(markerPos)
            if not inside:
                # don't use a pop up here, if the user is moving the target with the
                # mouse it will interfere
                warningString = "Unable to set this target at this location: " + markerPosStr + "\n\nThis target falls outside the area covered by the needle guide.\n\nPlease place the target inside the green zone.\n"
                print warningString
                self.writeLog(warningString)
                self.targetFiducialsNode.SetNthFiducialSelected(i, 0)
            else:
                self.targetFiducialsNode.SetNthFiducialSelected(i, 1)


            # create cells for the table
            cellLabel = qt.QTableWidgetItem(label)
            cellLabel.setTextAlignment(qt.Qt.AlignCenter)

            cellMarkerPos = qt.QTableWidgetItem(markerPosStr)
            cellMarkerPos.setTextAlignment(qt.Qt.AlignCenter)
            cellFlags = qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable
            cellMarkerPos.setFlags(cellFlags)

            # set them into the table
            self.targetTable.setItem(i, nameColumn, cellLabel)
            self.targetTable.setItem(i, rasColumn, cellMarkerPos)

            # if no GFM is present, fill in the grid and depth columns
            if workflowFunctions.getParameter('gfmPresentFlag') is 0:
                sheetPosition = sheetHoles[i]

                gridLocation = workflowFunctions.calculateGridLocation(sheetPosition)
                gridPosStr = gridLocation[0] + ", " + gridLocation[1]
                targetsList.append(gridLocation)
                cellGridPosition = qt.QTableWidgetItem(gridPosStr)
                cellGridPosition.setTextAlignment(qt.Qt.AlignCenter)
                cellGridPosition.setFlags(cellFlags)
                self.targetTable.setItem(i, gridColumn, cellGridPosition)

                # Depth is negative when it's more Superior than the guide sheet, but
                # present it to the user as a positive number for the insertion depth
                if sheetPosition.depth > 0.0:
                    depthWarning = "WARNING: Target " + label + " is not on patient side of guide sheet!"
                    self.writeLog(depthWarning)
                    if workflowFunctions.getParameter('devModeFlag') == 1:
                        print depthWarning
                # sheetPosition is in mm, convert to cm
                depthStr = "%.1f" % (-0.1 * sheetPosition.depth)
                cellDepth = qt.QTableWidgetItem(depthStr)
                cellDepth.setTextAlignment(qt.Qt.AlignCenter)
                cellDepth.setFlags(cellFlags)
                self.targetTable.setItem(i, depthColumn, cellDepth)

        if scrollFlag:
            self.targetTable.scrollToBottom()

        self.targetTable.blockSignals(False)

        # draw all the trajectories
        self.drawTrajectories()

        # show the trajectory volume
        self.onShowTrajectoriesLabelNode()

        # update the needle models
        self.updateTargetPathsModel()

        # color the guide hole model tubes
        self.colorGuideHolesModel(targetsList)

        # update ellipsoids around targets
        self.updateTargetEllipsoidsModel()

    def changeFiducialSlice(self):
        #when new target is chosen, all slices move to this target
        nOfControlPoints = self.targetFiducialsNode.GetNumberOfFiducials()
    
        markerPos = [0.0, 0.0, 0.0]
        self.targetFiducialsNode.GetNthFiducialPosition(nOfControlPoints-1, markerPos)
        workflowFunctions.jumpSlices(markerPos)

    def onTargetNameChange(self, item):
        # is the table blocking signals right now?
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onTargetNameChange: index: ', item.row(), item.column(), ', table blocking signals = ',self.targetTable.signalsBlocked()
        if self.targetTable.signalsBlocked():
            return
        try:
            nameColumn = workflowFunctions.getColumnIndex(self.columns, "Name")
            if item.column() != nameColumn:
                return
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'onTargetNameChange: ', item.row(), item.column(), item.text()
            oldName = self.targetFiducialsNode.GetNthFiducialLabel(item.row())
            if oldName != item.text():
                self.targetFiducialsNode.SetNthFiducialLabel(item.row(),item.text())
                self.writeLog('Target name changed from ' + oldName + ' to ' + item.text())
        except ValueError:
            print 'onTargetNameChanged: unable to change name'

    def onTableSelect(self, row, col):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onTableSelect: ', row, col
        if col == workflowFunctions.getColumnIndex(self.columns, "Delete"):
            # Delete the target
            self.delClick(row)
        else:
            self.onGotoTarget(row)
  
    def onGotoTarget(self, target):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onGotoTarget'
        #CHANGE SLICES TO TARGET
        tempPos = [0,0,0]
        self.targetFiducialsNode.GetNthFiducialPosition(target,tempPos)
        workflowFunctions.jumpSlices(tempPos)

    def onRightClickTable(self, point):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onRightClickTable: ', point

        # set up a context menu
        menu = qt.QMenu()

        # add an action to reset the name and position
        adjustTargetAction = qt.QAction("Adjust target name, position", menu)
        menu.addAction(adjustTargetAction)
        adjustTargetAction.connect('triggered()', self.onAdjustTargetTriggered)

        # show the menu
        menu.exec_(qt.QCursor().pos())

    def onAdjustTargetTriggered(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onAdjustTargetTriggered'
        # get the selected row
        selectedItems = self.targetTable.selectedItems()
        if len(selectedItems) == 0:
            workflowFunctions.popupError("Select a target", "E:407 No targets selected for adjustment.")
            return
        row = selectedItems[0].row()

        # get the current position
        currentPos = [0,0,0]
        self.targetFiducialsNode.GetNthFiducialPosition(row, currentPos)
        # get the current name
        currentName = self.targetFiducialsNode.GetNthFiducialLabel(row)

        # pop up a widget to change name and position
        adjustTargetDialog = qt.QDialog()
        adjustTargetDialog.setWindowFlags(adjustTargetDialog.windowFlags() | qt.Qt.WindowStaysOnTopHint)
        adjustTargetDialog.setWindowTitle("Adjust target")
        layout = qt.QFormLayout()
        adjustTargetDialog.setLayout(layout)

        # Name
        nameEntry = qt.QLineEdit()
        nameEntry.text = currentName
        adjustTargetDialog.layout().addRow("Target Name:", nameEntry)

        # Position
        positionWidget = ctk.ctkCoordinatesWidget()
        positionWidget.coordinates = str(currentPos[0]) + ',' + str(currentPos[1]) + ',' + str(currentPos[2])
        adjustTargetDialog.layout().addRow("Target Position:", positionWidget)

        buttonBox = qt.QDialogButtonBox()
        okButton = qt.QPushButton("Ok")
        workflowFunctions.colorPushButtonFromPalette(okButton, 'Primary')
        buttonBox.addButton(okButton, qt.QDialogButtonBox.AcceptRole)
        cancelButton = qt.QPushButton("Cancel")
        workflowFunctions.colorPushButtonFromPalette(cancelButton, 'Secondary')
        cancelButton.setDefault(True)
        buttonBox.addButton(cancelButton, qt.QDialogButtonBox.RejectRole)
        buttonBox.connect('accepted()', adjustTargetDialog, 'accept()')
        buttonBox.connect('rejected()', adjustTargetDialog, 'reject()')
        adjustTargetDialog.layout().addRow('', buttonBox)

        ret = adjustTargetDialog.exec_()
        if ret == qt.QDialog.Accepted:
            newName = nameEntry.text
            newPosStrArray = positionWidget.coordinates.split(',')
            logString = 'Target modified:\n\tName updated from '
            logString = logString + self.targetFiducialsNode.GetNthFiducialLabel(row)
            logString = logString + ' to ' + newName + '\n\tOriginal position = '
            logString = logString + str(currentPos[0]) + ',' + str(currentPos[1]) + ',' + str(currentPos[2])
            logString = logString + '\n\tUpdated position: '
            logString = logString + newPosStrArray[0] + ',' + newPosStrArray[1] + ',' + newPosStrArray[2]
            self.writeLog(logString)

            self.targetFiducialsNode.SetNthFiducialLabel(row, newName)
            newPosArray = [float(newPosStrArray[0]), float(newPosStrArray[1]), float(newPosStrArray[2])]
            self.targetFiducialsNode.SetNthFiducialPosition(row, newPosArray[0], newPosArray[1], newPosArray[2])
            workflowFunctions.jumpSlices(newPosArray)

    def writeLog(self, message):
        workflowFunctions.writeLog(self.logFileName, message)
        
    def onParameterNodeModified(self, caller, event):
        # compare the step's target label to the parameter node's target scan id and
        # update if necessary
        parameterID = workflowFunctions.getParameter('targetScanDICOMID')
        if parameterID is None:
            # unset the selected target scan
            workflowFunctions.setVolumeLabel(self.targetScanLabel, '')
            self.targetScanDICOM = None
            self.targetScanDICOMID = None
            return
        node = None
        nodeID = None
        labelText = self.targetScanLabel.text
        if labelText is not None and labelText != '':
             node = slicer.util.getFirstNodeByName(labelText)
        if node is not None:
             nodeID = node.GetID()
        if nodeID is None or nodeID != parameterID:
             self.targetScanDICOM = slicer.util.getNode(parameterID)
             if self.targetScanDICOM != None:
                 workflowFunctions.setVolumeLabel(self.targetScanLabel, self.targetScanDICOM.GetName())
                 self.targetScanDICOMID = self.targetScanDICOM.GetID()
                 workflowFunctions.setActiveVolume(self.targetScanDICOM.GetID())
                 self.runGreenZone()
             else:
                 workflowFunctions.setVolumeLabel(self.targetScanLabel, '')
                 self.targetScanDICOMID = None
                 workflowFunctions.setActiveVolume(None)

    def onShowTargets(self):
        if self.targetFiducialsNode is None:
            return
        if self.showTargetsCheckBox is None:
            return
        self.targetFiducialsNode.SetDisplayVisibility(self.showTargetsCheckBox.checked)

    def onShowTrajectoriesLabelNode(self):
        visible = self.showTrajectoriesLabelCheckBox.checked
        if (self.trajectoryLabelVolume is None) or (not visible):
            workflowFunctions.setLabelVolume(None)
        if (self.trajectoryLabelVolume is not None) and visible:
            workflowFunctions.setLabelVolume(self.trajectoryLabelVolume.GetID())
        # update parameter if necessary
        workflowFunctions.updateParameterFlagFromChecked('TARGET_PATH_VIS_Flag', visible)

    def onShowTargetTrajectories(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onShowTargetTrajectories'
        checked = self.showTargetTrajectoriesCheckBox.checked
        self.setTargetNeedlePathVisibility(checked)
        # update parameter if necessary
        workflowFunctions.updateParameterFlagFromChecked('TARGET_PATH_3D_VIS_Flag', checked)

    def updateTargetPathsModel(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'updateTargetPathsModel'
        regTrans = numpy.identity(4)
        newModel = False
        targetPathModelNode = None
        targetNeedlePathModelNodeID = workflowFunctions.getParameter('targetNeedlePathModelNodeID')
        if targetNeedlePathModelNodeID is not None:
            targetPathModelNode = slicer.mrmlScene.GetNodeByID(targetNeedlePathModelNodeID)
        if targetPathModelNode == None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print '\tcreating new 3d needle tracks model'
            targetPathModelNode = slicer.vtkMRMLModelNode()
            newModel = True
            targetPathModelNode.SetName('TargetNeedlePath')
            slicer.mrmlScene.AddNode(targetPathModelNode)
            targetNeedlePathModelNodeID = targetPathModelNode.GetID()
            workflowFunctions.setParameter('targetNeedlePathModelNodeID',targetNeedlePathModelNodeID)
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print("Created target path model ID=%s"%(targetNeedlePathModelNodeID))

            dnode = slicer.vtkMRMLModelDisplayNode()
            slicer.mrmlScene.AddNode(dnode)
            targetPathModelNode.SetAndObserveDisplayNodeID(dnode.GetID())
            dnode.SetSliceIntersectionVisibility(1)

            if workflowFunctions.getParameter('devModeFlag') == 1:
                print("target path display node ID=%s"%(dnode.GetID()))

        if targetPathModelNode is None:
            workflowFunctions.popupError("Target paths", "E:408 Unable to create a model showing the needle paths to targets!")
            return

        # set the color to match the label volume
        if self.trajectoryLabelVolume is not None:
            labelColorNode = self.trajectoryLabelVolume.GetDisplayNode().GetColorNode()
            if labelColorNode is not None:
                pathColor = [0,0,0,0]
                labelColorNode.GetColor(2, pathColor)
                dnode = targetPathModelNode.GetDisplayNode()
                if dnode is not None:
                    dnode.SetColor(pathColor[0], pathColor[1], pathColor[2])
                    dnode.SetOpacity(pathColor[3])

        # clear it out
        targetPathModelNode.SetAndObservePolyData(None)

        # create new paths
        targetPathModelAppend = vtk.vtkAppendPolyData()
        numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
        sheetHoles = []

        if numberOfTargets > 0:
                sheetHoles = workflowFunctions.calcGuideSheetHoles(self.targetFiducialsNode)
        for targetNum in range(numberOfTargets):
            targetPos = [0,0,0]
            self.targetFiducialsNode.GetNthFiducialPosition(targetNum, targetPos)
            sheetPosition = sheetHoles[targetNum]
            targetPt = numpy.array(targetPos)
            targetPt = numpy.hstack((targetPt,numpy.array([1])))
            targetPtT = numpy.dot(regTrans,numpy.transpose(targetPt))
            targetPtT = targetPtT[0:3]
            targetDepth = sheetPosition.depth
            targetNormal = sheetPosition.normal
            sourcePt = numpy.array(targetPtT) - targetDepth*targetNormal
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print("target=%s, targetPt=%s, normal=%s, sourcePt=%s" % (targetNum, targetPtT, targetNormal, sourcePt))
            targetLineSource = vtk.vtkLineSource()
            targetLineSource.SetPoint1(sourcePt)
            targetLineSource.SetPoint2(targetPtT)
            targetTubeFilter = vtk.vtkTubeFilter()
            targetTubeFilter.SetInputConnection(targetLineSource.GetOutputPort())
            targetTubeFilter.SetRadius(0.8)
            targetTubeFilter.SetNumberOfSides(18)
            targetTubeFilter.CappingOn()
            targetTubeFilter.Update()
            targetPathModelAppend.AddInputData(targetTubeFilter.GetOutput())
        targetPathModelAppend.Update()
        targetPathModelNode.SetAndObservePolyData(targetPathModelAppend.GetOutput())

        self.onShowTargetTrajectories()

    # Set the scalars on the guide holes model to show the target tube(s)
    # in a different colour.
    # Uses self.targetScalar and self.nonTargetScalar
    # targets: a list of grid coordinates, eg [[['A', '1'], ['H', '17']]
    def colorGuideHolesModel(self, targets = None):
        modelNodeID = workflowFunctions.getParameter('guideHolesModelNodeID')
        if modelNodeID is None:
            return
        modelNode = slicer.mrmlScene.GetNodeByID(modelNodeID)
        if modelNode is None:
            return
        if not modelNode.GetDisplayVisibility():
            return
        numPointsInModel = modelNode.GetPolyData().GetNumberOfPoints()
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'colorGuideHolesModel: total points: ', numPointsInModel, ', points per tube:', self.numPointsOneGridTube

        # are the scalars defined already?
        pointData = modelNode.GetPolyData().GetPointData()
        tubeScalars = pointData.GetArray('TubeScalars')
        if tubeScalars is None:
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print 'TubeScalars not found on', modelNode.GetID(), ', creating.'
            # create
            tubeScalars = vtk.vtkDoubleArray()
            tubeScalars.SetNumberOfTuples(numPointsInModel)
            tubeScalars.SetName('TubeScalars')
            modelNode.AddPointScalars(tubeScalars)
            modelNode.GetDisplayNode().SetActiveScalarName('TubeScalars')
            modelNode.GetDisplayNode().SetScalarVisibility(1)
            # explicitly set the LUT for the point scalars
            lut = modelNode.GetDisplayNode().GetColorNode().GetLookupTable()
            modelNode.GetPolyData().GetPointData().GetScalars().SetLookupTable(lut)
        # fill it with non target scalars
        for i in xrange(numPointsInModel):
            tubeScalars.SetTuple1(i, self.nonTargetScalar)
        if targets is not None:
            for target in targets:
                if target is None:
                    continue
                if target[0] == '?' or target[1] == '?':
                    continue
                # set the scalars in the target tube
                # Convert grid coords ['A', '1'] to i,j
                i = workflowFunctions.getColumnNumber(target[0])
                rowsFromBottom = int(target[1])
                numberOfHolesY = workflowFunctions.getGridParameter('NumberOfHolesPerColumn')
                j = numberOfHolesY - rowsFromBottom
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\n\n\n\n*****************\nTarget: ', target, ': i = ', i, ', j = ', j
                targetTube = self.gridCoordinatesToTubeNumber[i, j]
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\ttargetTube = ', targetTube
                targetPointStart = targetTube * self.numPointsOneGridTube
                targetPointEnd = targetPointStart + self.numPointsOneGridTube
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\tpointStart = ', targetPointStart, ', end = ', targetPointEnd
                for p in xrange(targetPointStart, targetPointEnd):
                    tubeScalars.SetTuple1(p, self.targetScalar)
        # trigger an update to ensure that the slice intersections are updated
        modelNode.GetPolyData().Modified()
        modelNode.GetDisplayNode().Modified()

    def setGuideHolesVisibility(self, visibility):
        for id in ['guideHolesModelNodeID', 'guideHolesLettersTopModelNodeID', 'guideHolesLettersBottomModelNodeID', 'guideHolesNumbersRightModelNodeID', 'guideHolesNumbersLeftModelNodeID']:
            modelNodeID = workflowFunctions.getParameter(id)
            if workflowFunctions.getParameter('devModeFlag') == 1:
                print("setGuideHolesVisibility=%d NodeID=%s"%(visibility, modelNodeID))
            if modelNodeID is not None and visibility is not None:
                modelNode = slicer.mrmlScene.GetNodeByID(modelNodeID)
                if modelNode != None:
                    dnode = modelNode.GetDisplayNode()
                    if dnode != None:
                        dnode.SetVisibility(visibility)
                        if visibility:
                            # only show in 3d and on red slice
                            dnode.RemoveAllViewNodeIDs()
                            dnode.AddViewNodeID('vtkMRMLViewNode1')
                            dnode.AddViewNodeID('vtkMRMLSliceNodeRed')

        # if on, update the coloring as updating is turned off when not visible
        if visibility:
            # the target table update calculates the target tubes and then
            # updates the colouring, so to avoid unsetting all the target tube
            # colors, trigger it via a table update
            self.updateTargetTable()
        # update the target zone to show it in 3d if the guide holes
        # aren't visible
        self.onShowTargetZone()

    def setTargetNeedlePathVisibility(self, visibility):
        targetNeedlePathModelNodeID = workflowFunctions.getParameter('targetNeedlePathModelNodeID')
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print("setTargetNeedlePathVisibility=%d NodeID=%s"%(visibility, targetNeedlePathModelNodeID))
        if targetNeedlePathModelNodeID is not None and visibility is not None:
            workflowFunctions.setModelVisibilityByID(targetNeedlePathModelNodeID, visibility)

    def onShowTargetZone(self):
        # this may be called to update the target zone when the needle
        # guide tubes are toggled from tests or other steps, so check that the
        # workflow is running and in the target step
        if (self.workflow().currentStep() is None) or (self.workflow().currentStep().id() != self.id()):
            return
        if not hasattr(self, 'showTargetZoneCheckBox'):
            return
        checked = self.showTargetZoneCheckBox.checked
        self.setTargetZoneVisibility(checked)
        workflowFunctions.updateParameterFlagFromChecked('TARGET_ZONE_VIS_Flag', checked)

    def onShowSheet(self):
        checked = self.showSheetCheckBox.checked
        self.setSheetVisibility(checked)
        workflowFunctions.updateParameterFlagFromChecked('SHEET_VIS_Flag', checked)

    def onShowSolidSheet(self):
        checked = self.showSolidSheetCheckBox.checked
        self.setSolidSheetVisibility(checked)
        workflowFunctions.updateParameterFlagFromChecked('SHEET_SOLID_VIS_Flag', checked)

    def onShowSliceIntersections(self):
        checked = self.sliceIntersectionsCheckBox.checked
        self.setSliceIntersectionsVisibility(checked)

    def onShowTargetEllipsoids(self):
        checked = self.showEllipsoidsCheckBox.checked
        self.setEllipsoidsVisibility(checked)
        workflowFunctions.updateParameterFlagFromChecked('TARGET_ELLIPSOIDS_VIS_Flag', checked)

    def setTargetZoneVisibility(self, visibility):
        cubeModel = slicer.util.getNode('GreenZoneCube')
        if cubeModel is not None:
            cubeModel.SetDisplayVisibility(visibility)
            # If the guide hole tubes are showing,
            # don't show in 3D, just in slice views.
            # Otherwise show in all views.
            # Have to remove the view node ids in order to
            # reset the target zone visibility in 3D.
            tubesVisible = False
            tubesModelNodeID = workflowFunctions.getParameter('guideHolesModelNodeID')
            if tubesModelNodeID is not None:
                tubesModelNode = slicer.mrmlScene.GetNodeByID(tubesModelNodeID)
                if tubesModelNode is not None:
                    # display visibility of 2 means visible in some views
                    tubesVisible = (tubesModelNode.GetDisplayVisibility() != 0)
            dnode = cubeModel.GetDisplayNode()
            dnode.RemoveAllViewNodeIDs()
            if not tubesVisible:
                return
            layoutManager = slicer.app.layoutManager()
            if not layoutManager:
                return
            viewNames = layoutManager.sliceViewNames()
            for viewName in viewNames:
                viewNode = slicer.mrmlScene.GetFirstNodeByName(viewName)
                if viewNode is not None:
                    dnode.AddViewNodeID(viewNode.GetID())


    def setSheetVisibility(self, visibility):
        sheetModelNodeID = workflowFunctions.getParameter('sheetModelNodeID')
        if sheetModelNodeID is not None and visibility is not None:
            workflowFunctions.setModelVisibilityByID(sheetModelNodeID, visibility)

    def setSolidSheetVisibility(self, visibility):
        solidSheetModelNodeID = workflowFunctions.getParameter('solidSheetModelNodeID')
        if solidSheetModelNodeID is not None and visibility is not None:
            workflowFunctions.setModelVisibilityByID(solidSheetModelNodeID, visibility)

    def setSliceIntersectionsVisibility(self, checked):
        workflowFunctions.setSliceIntersections(checked)
        workflowFunctions.updateParameterFlagFromChecked('sliceIntersectionsFlag', checked)

    def setEllipsoidsVisibility(self, visibility):
        ellipsoidsModeNodeID = workflowFunctions.getParameter('targetEllipsoidsNodeID')
        if ellipsoidsModeNodeID is not None and visibility is not None:
            workflowFunctions.setModelVisibilityByID(ellipsoidsModeNodeID, visibility)

    def filterSheetLine(self, lineSource, append, node):
        tubeFilter = vtk.vtkTubeFilter()
        tubeFilter.SetInputConnection(lineSource.GetOutputPort())
        tubeFilter.SetRadius(0.8)
        tubeFilter.SetNumberOfSides(18)
        tubeFilter.CappingOn()
        tubeFilter.Update()
        append.AddInputData(tubeFilter.GetOutput())

    def createSolidSheetModel(self):
        'display guide sheet as a solid cube'
        points = workflowFunctions.getGuideSheetCorners()
        if points is None:
            workflowFunctions.popupWarning("W:403 Unable to create guide sheet solid model")
            return
        solidSheetModelNodeID = workflowFunctions.getParameter('solidSheetModelNodeID')
        solidSheetModelNode = None
        if solidSheetModelNodeID is not None:
            solidSheetModelNode = slicer.mrmlScene.GetNodeByID(solidSheetModelNodeID)
        newModel = False
        if solidSheetModelNode == None:
          solidSheetModelNode = slicer.vtkMRMLModelNode()
          solidSheetModelNode.SetName('GuideSheetSolidModel')
          slicer.mrmlScene.AddNode(solidSheetModelNode)
          solidSheetModelNodeID = solidSheetModelNode.GetID()
          workflowFunctions.setParameter('solidSheetModelNodeID', solidSheetModelNodeID)

          dnode = slicer.vtkMRMLModelDisplayNode()
          slicer.mrmlScene.AddNode(dnode)
          solidSheetModelNode.SetAndObserveDisplayNodeID(dnode.GetID())
          # set it not displayed to start
          solidSheetModelNode.SetDisplayVisibility(0)
          # print("Created solid sheet model ID=%s  display node ID=%s" %(self.solidSheetModelNodeID, dnode.GetID()))
          newModel = True
        solidSheetModelAppend = vtk.vtkAppendPolyData()
        cubeSource = vtk.vtkCubeSource()
        minX = sys.float_info.max
        minY = sys.float_info.max
        minZ = sys.float_info.max
        negMin = float(workflowFunctions.getParameter('NEGATIVE_MIN'))
        maxX = negMin
        maxY = negMin
        maxZ = negMin

        guideSheetCenter = numpy.array(numpy.mean(points, 0))
        # create array of points that are centered around 0 so that when the model is
        # transformed it will move correctly
        centeredPoints = []
        for p in xrange(4):
           pos = points[p] - guideSheetCenter
           posArray = numpy.array(pos)
           centeredPoints.append(posArray)

        cornerZ = centeredPoints[0][2]
        # find lower left point
        for spt in centeredPoints:
          if spt[0] < minX:
            minX = spt[0]
          if spt[1] < minY:
            minY = spt[1]
          if spt[2] < minZ:
            minZ = spt[2]
          if spt[0] > maxX:
            maxX = spt[0]
          if spt[1] > maxY:
            maxY = spt[1]
          if spt[2] > maxZ:
            maxZ = spt[2]
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print("Solid guide sheet model %f %f %f %f %f %f" %(minX, maxX, minY, maxY, minZ-0.6, maxZ+0.6))
        cubeSource.SetBounds(minX, maxX, minY, maxY, minZ-0.6, maxZ+0.6)

        solidSheetModelAppend.AddInputData(cubeSource.GetOutput())
        cubeSource.Update()
        solidSheetModelAppend.Update()
        mark00 = vtk.vtkLineSource()
        cornerMarkLength = float(workflowFunctions.getParameter('CORNER_MARK_LENGTH'))
        mark00.SetPoint1((minX, minY, cornerZ-cornerMarkLength))
        mark00.SetPoint2((minX, minY, cornerZ+cornerMarkLength))
        tubeFilter = vtk.vtkTubeFilter()
        tubeFilter.SetInputConnection(mark00.GetOutputPort())
        tubeFilter.SetRadius(0.4)
        tubeFilter.SetNumberOfSides(9)
        tubeFilter.CappingOn()
        tubeFilter.Update()
        solidSheetModelAppend.AddInputData(tubeFilter.GetOutput())
        solidSheetModelAppend.Update()
        solidSheetModelNode.SetAndObservePolyData(solidSheetModelAppend.GetOutput())
        if newModel:
          guideSheetTransformNodeID = workflowFunctions.getParameter('GuideSheetTransformID')
          solidSheetModelNode.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        self.setSolidSheetVisibility(workflowFunctions.getParameter('SHEET_SOLID_VIS_Flag'))

    def createSheetOutlineModel(self):
        '''Create 3D model of guide sheet
        '''
        points = workflowFunctions.getGuideSheetCorners()
        if points is None:
            workflowFunctions.popupWarning("W:412 Unable to create guide sheet outline model")
            return

        sheetModelNodeID = workflowFunctions.getParameter('sheetModelNodeID')
        sheetModelNode = None
        if sheetModelNodeID is not None:
            sheetModelNode = slicer.mrmlScene.GetNodeByID(sheetModelNodeID)
        newModel = False
        if sheetModelNode == None:
          sheetModelNode = slicer.vtkMRMLModelNode()
          sheetModelNode.SetName('GuideSheetOutlineModel')
          slicer.mrmlScene.AddNode(sheetModelNode)
          sheetModelNodeID = sheetModelNode.GetID()
          workflowFunctions.setParameter('sheetModelNodeID', sheetModelNodeID)

          dnode = slicer.vtkMRMLModelDisplayNode()
          slicer.mrmlScene.AddNode(dnode)
          sheetModelNode.SetAndObserveDisplayNodeID(dnode.GetID())
          # set it not displayed to start
          sheetModelNode.SetDisplayVisibility(0)
          # print("Created sheet model ID=%s  display node ID=%s" %(self.sheetModelNodeID, dnode.GetID()))
          newModel = True
        sheetModelAppend = vtk.vtkAppendPolyData()

        # create array of points that are centered around 0 so that when the model is
        # transformed it will move correctly
        guideSheetCenter = numpy.array(numpy.mean(points, 0))
        centeredPoints = []
        for p in xrange(4):
           pos = points[p] - guideSheetCenter
           posArray = numpy.array(pos)
           centeredPoints.append(posArray)

        line1 = vtk.vtkLineSource()
        line1.SetPoint1(centeredPoints[0])
        line1.SetPoint2(centeredPoints[1])
        line2 = vtk.vtkLineSource()
        line2.SetPoint1(centeredPoints[1])
        line2.SetPoint2(centeredPoints[2])
        line3 = vtk.vtkLineSource()
        line3.SetPoint1(centeredPoints[2])
        line3.SetPoint2(centeredPoints[3])
        line4 = vtk.vtkLineSource()
        line4.SetPoint1(centeredPoints[3])
        line4.SetPoint2(centeredPoints[0])

        self.filterSheetLine(line1, sheetModelAppend, sheetModelNode)
        self.filterSheetLine(line2, sheetModelAppend, sheetModelNode)
        self.filterSheetLine(line3, sheetModelAppend, sheetModelNode)
        self.filterSheetLine(line4, sheetModelAppend, sheetModelNode)

        sheetModelAppend.Update()
        sheetModelNode.SetAndObservePolyData(sheetModelAppend.GetOutput())
        if newModel:
          guideSheetTransformNodeID = workflowFunctions.getParameter('GuideSheetTransformID')
          sheetModelNode.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        self.setSheetVisibility(workflowFunctions.getParameter('SHEET_VIS_Flag'))


    def createGuideHolesModel(self):
        points = workflowFunctions.getGuideSheetCorners()
        if points is None:
            workflowFunctions.popupWarning("W:413 Unable to create guide sheet holes model")
            return

        guideHolesModelNodeID = workflowFunctions.getParameter('guideHolesModelNodeID')
        guideHolesModelNode = None
        if guideHolesModelNodeID is not None:
            guideHolesModelNode = slicer.mrmlScene.GetNodeByID(guideHolesModelNodeID)
        newModel = False
        if guideHolesModelNode == None:
          guideHolesModelNode = slicer.vtkMRMLModelNode()
          guideHolesModelNode.SetName('GuideSheetHolesModel')
          slicer.mrmlScene.AddNode(guideHolesModelNode)
          guideHolesModelNodeID = guideHolesModelNode.GetID()
          workflowFunctions.setParameter('guideHolesModelNodeID', guideHolesModelNodeID)

          dnode = slicer.vtkMRMLModelDisplayNode()
          # set it the same color as the green target zone
          dnode.SetOpacity(0.75)
          dnode.SetSliceIntersectionVisibility(1)
          # only show on Red and 3D View
          dnode.RemoveAllViewNodeIDs()
          dnode.AddViewNodeID('vtkMRMLViewNode1')
          dnode.AddViewNodeID('vtkMRMLSliceNodeRed')
          greenColor = self.modelColors['GreenZone']
          dnode.SetColor(greenColor.redF(), greenColor.greenF(), greenColor.blueF())
          slicer.mrmlScene.AddNode(dnode)
          guideHolesModelNode.SetAndObserveDisplayNodeID(dnode.GetID())
          # set the color information
          gridHolesColorNode = slicer.vtkMRMLColorTableNode()
          gridHolesColorNode.SetName("HMS Grid Holes Color Table")
          lookup = vtk.vtkLookupTable()
          lookup.SetNumberOfColors(2)
          # lookup.SetTableValue(0,[0.0, 0.0, 0.0, 0.0])
          lookup.SetTableValue(0,[greenColor.redF(), greenColor.greenF(), greenColor.blueF(), 1.0])
          targetColor = self.modelColors['TargetTube']
          lookup.SetTableValue(1,[targetColor.redF(), targetColor.greenF(), targetColor.blueF(), 1.0])
          gridHolesColorNode.SetLookupTable(lookup)
          # init the names then set them
          gridHolesColorNode.SetNamesFromColors()
          gridHolesColorNode.SetColorName(0, 'Hole')
          gridHolesColorNode.SetColorName(1, 'Target')

          slicer.mrmlScene.AddNode(gridHolesColorNode)
          guideHolesModelNode.GetDisplayNode().SetAndObserveColorNodeID(gridHolesColorNode.GetID())

          # set it not displayed to start
          guideHolesModelNode.SetDisplayVisibility(0)
          # enable the GUI button to toggle visibility
          ngw = slicer.modules.HMS_NeedleGuideWidget
          ngw.sheetHolesButton.enabled = True
          # mark it as a new model
          newModel = True

        if not newModel:
            # just update the visibility, don't need to regenerate
            self.setGuideHolesVisibility(workflowFunctions.getParameter('sheetHolesFlag'))
            return

        modelAppend = vtk.vtkAppendPolyData()
        # create unit length tubes the size of the grid holes, centered at the origin
        # so it can be transformed

        guideSheetCenter = numpy.array(numpy.mean(points, 0))
        cornerPoints = []
        for p in xrange(4):
           pos = points[p] - guideSheetCenter
           posArray = numpy.array(pos)
           cornerPoints.append(posArray)
           if workflowFunctions.getParameter('devModeFlag') == 1:
               print 'createGuideHolesModel: Corner point ', p, ' = ', posArray

        # get the vectors along the sides
        # vector from corner 0 to corner 3
        vectorX = [0,0,0]
        for i in range(3):
            vectorX[i] =  cornerPoints[0][i] - cornerPoints[3][i]
        mag = numpy.sqrt(vectorX[0]*vectorX[0] + vectorX[1]*vectorX[1] + vectorX[2]*vectorX[2])
        if mag != 0.0:
            vectorX = numpy.array(vectorX) / mag
        # vector from corner 0 to corner 1
        vectorY = [0,0,0]
        for i in range(3):
            vectorY[i] = cornerPoints[0][i] - cornerPoints[1][i]
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Projection vectors:\n\tX = ', vectorX, '\n\tY = ', vectorY

        # get the guide sheet parameters
        holesPerRow = workflowFunctions.getGridParameter('NumberOfHolesPerRow')
        holesPerColumn = workflowFunctions.getGridParameter('NumberOfHolesPerColumn')
        offsetX = workflowFunctions.getGridParameter('OriginOffsetX')
        offsetY = workflowFunctions.getGridParameter('OriginOffsetY')
        spacingBetweenCols = workflowFunctions.getGridParameter('SpacingBetweenColumns')
        spacingBetweenRows = workflowFunctions.getGridParameter('SpacingBetweenRows')
        holeDiameter = workflowFunctions.getGridParameter('HoleDiameter')
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'Grid parameters:'
            print '\tholesPerRow = ', holesPerRow
            print '\tholesPerCol = ', holesPerColumn
            print '\toffsetX = ', offsetX
            print '\toffsetY = ', offsetY
            print '\tspacingBetweenRows = ', spacingBetweenRows
            print '\tspacingBetweenCols = ', spacingBetweenCols
            print '\tholeDiameter = ', holeDiameter
            print 'Creating tubes:'
        # create line sources
        self.numPointsOneGridTube = 0
        self.gridCoordinatesToTubeNumber = {}
        tubeNumber = 0
        for i in xrange(holesPerRow):
            for j in xrange(holesPerColumn):
                # Center of grid hole
                holeCenterX = cornerPoints[0][0] - offsetX - i*spacingBetweenCols
                holeCenterY = cornerPoints[0][1] + offsetY + j*spacingBetweenRows
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\ti', i, ', j', j, ', centerX ', holeCenterX, ', centerY', holeCenterY
                # create line offset by 0.5 along Z
                line = vtk.vtkLineSource()
                line.SetPoint1([holeCenterX, holeCenterY, -0.5])
                line.SetPoint2([holeCenterX, holeCenterY, 0.5])
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\t\tline ends = ', line.GetPoint1(), line.GetPoint2()
                # create a tube
                tubeFilter = vtk.vtkTubeFilter()
                tubeFilter.SetInputConnection(line.GetOutputPort())
                tubeFilter.SetRadius(holeDiameter)
                tubeFilter.SetNumberOfSides(18)
                tubeFilter.CappingOn()
                tubeFilter.Update()
                self.numPointsOneGridTube = tubeFilter.GetOutput().GetPointData().GetNumberOfTuples()
                if workflowFunctions.getParameter('devModeFlag') == 1:
                    print '\t\ttube num points = ', self.numPointsOneGridTube
                modelAppend.AddInputData(tubeFilter.GetOutput())
                self.gridCoordinatesToTubeNumber[i, j] = tubeNumber
                tubeNumber = tubeNumber + 1

        modelAppend.Update()
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print '\tPoints per tube: ', self.numPointsOneGridTube, ', tube coords:\n', self.gridCoordinatesToTubeNumber
        guideHolesModelNode.SetAndObservePolyData(modelAppend.GetOutput())
        self.colorGuideHolesModel()

        if newModel:
          guideSheetHolesTransformNodeID = workflowFunctions.getParameter('GuideSheetHolesTransformID')
          guideHolesModelNode.SetAndObserveTransformNodeID(guideSheetHolesTransformNodeID)

        # add the grid letters and numbers
        if newModel:
            self.createGuideHolesLetters()

        self.setGuideHolesVisibility(workflowFunctions.getParameter('sheetHolesFlag'))

    # Create models that contain the letters and numbers that mark the grid columns and rows.
    # Positioned with relative transforms and then placed under the guide sheet transform
    def createGuideHolesLetters(self):
        # Get the grid parameters needed to geneate and position markings
        numCols = workflowFunctions.getGridParameter('NumberOfHolesPerRow')
        numRows = workflowFunctions.getGridParameter('NumberOfHolesPerColumn')
        offsetX = workflowFunctions.getGridParameter('OriginOffsetX')
        offsetY = workflowFunctions.getGridParameter('OriginOffsetY')
        spacingBetweenCols = workflowFunctions.getGridParameter('SpacingBetweenColumns')
        spacingBetweenRows = workflowFunctions.getGridParameter('SpacingBetweenRows')

        # Column letters
        gridLetters = vtk.vtkVectorText()
        lettersString = ''
        letterStart = ord('A')
        letterEnd = ord('A') + numCols
        columnLetters = list(map(chr, range(letterStart, letterEnd)))
        for i in xrange(len(columnLetters)):
            if i == 0:
                lettersString = lettersString + columnLetters[i]
            else:
                if columnLetters[i] == 'J':
                    # add some padding for the J after the I
                    spaces = '  '
                else:
                    spaces = ' '
                lettersString = lettersString + spaces + columnLetters[i]
        gridLetters.SetText(lettersString)
        gridLetters.Update()

        # Put the letters along the top
        gridLettersTopModel = slicer.vtkMRMLModelNode()
        gridLettersTopModel.SetName("Grid Letters Top")
        gridLettersTopModel.SetAndObservePolyData(gridLetters.GetOutput())

        gridLettersTopDisplay = slicer.vtkMRMLModelDisplayNode()
        gridLettersTopDisplay.SetName("Grid Letters Display")
        greenColor = self.modelColors['GreenZone']
        gridLettersTopDisplay.SetColor(greenColor.redF(), greenColor.greenF(), greenColor.blueF())
        gridLettersTopDisplay.SetBackfaceCulling(0)
        slicer.mrmlScene.AddNode(gridLettersTopDisplay)

        slicer.mrmlScene.AddNode(gridLettersTopModel)
        workflowFunctions.setParameter('guideHolesLettersTopModelNodeID', gridLettersTopModel.GetID())
        gridLettersTopModel.SetAndObserveDisplayNodeID(gridLettersTopDisplay.GetID())

        # transform in guide sheet coordinates to line the grid
        lettersTopTransform = slicer.vtkMRMLLinearTransformNode()
        lettersTopTransform.SetName("Grid Letters Top xform")
        lettersTopMatrix = vtk.vtkMatrix4x4()
        # scale the text, and flip so can be read from inferior
        lettersTopMatrix.SetElement(0,0,-3.4)
        lettersTopMatrix.SetElement(1,1,3.4)
        lettersTopMatrix.SetElement(2,2,-3.4)
        # position it
        lettersX = (numCols * spacingBetweenCols) / 2.0
        lettersY = ((numRows * spacingBetweenRows) / 2.0) + offsetY
        lettersTopMatrix.SetElement(0,3,lettersX)
        lettersTopMatrix.SetElement(1,3,lettersY)
        lettersTopTransform.SetMatrixTransformToParent(lettersTopMatrix)
        slicer.mrmlScene.AddNode(lettersTopTransform)

        # put into patient space
        guideSheetTransformNodeID = workflowFunctions.getParameter('GuideSheetTransformID')
        if guideSheetTransformNodeID is not None:
            lettersTopTransform.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        gridLettersTopModel.SetAndObserveTransformNodeID(lettersTopTransform.GetID())

        # Put the letters along the bottom
        gridLettersBottomModel = slicer.vtkMRMLModelNode()
        gridLettersBottomModel.SetName("Grid Letters Bottom")
        gridLettersBottomModel.SetAndObservePolyData(gridLetters.GetOutput())

        gridLettersBottomDisplay = slicer.vtkMRMLModelDisplayNode()
        gridLettersBottomDisplay.Copy(gridLettersTopDisplay)
        slicer.mrmlScene.AddNode(gridLettersBottomDisplay)

        slicer.mrmlScene.AddNode(gridLettersBottomModel)
        workflowFunctions.setParameter('guideHolesLettersBottomModelNodeID', gridLettersBottomModel.GetID())
        gridLettersBottomModel.SetAndObserveDisplayNodeID(gridLettersBottomDisplay.GetID())

        # transform in guide sheet coordinates to line the grid
        lettersBottomTransform = slicer.vtkMRMLLinearTransformNode()
        lettersBottomTransform.SetName("Grid Letters Bottom xform")
        lettersBottomMatrix = vtk.vtkMatrix4x4()
        # scale the text, and flip so can be read from inferior
        lettersBottomMatrix.SetElement(0,0,-3.4)
        lettersBottomMatrix.SetElement(1,1,3.4)
        lettersBottomMatrix.SetElement(2,2,-3.4)
        # position it
        lettersX = (numCols * spacingBetweenCols) / 2.0
        lettersY = -(((numRows * spacingBetweenRows) / 2.0) + 2.0*offsetY)
        lettersBottomMatrix.SetElement(0,3,lettersX)
        lettersBottomMatrix.SetElement(1,3,lettersY)
        lettersBottomTransform.SetMatrixTransformToParent(lettersBottomMatrix)
        slicer.mrmlScene.AddNode(lettersBottomTransform)

        # put into patient space
        guideSheetTransformNodeID = workflowFunctions.getParameter('GuideSheetTransformID')
        if guideSheetTransformNodeID is not None:
            lettersBottomTransform.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        gridLettersBottomModel.SetAndObserveTransformNodeID(lettersBottomTransform.GetID())

        # Row numbers
        gridNumbers = vtk.vtkVectorText()
        numbersString = '' # ' 1\n 2\n 3\n 4\n 5\n 6\n 7\n 8\n 9\n10\n11\n12\n13\n14\n15\n16\n17'
        for i in xrange(numRows):
            if i == 0:
                numbersString = numbersString + '{0: >2}'.format(i+1)
            else:
                numbersString = numbersString + '\n{0: >2}'.format(i+1)
        gridNumbers.SetText(numbersString)
        gridNumbers.Update()

        # Place along patient right of the grid
        gridNumbersRightModel = slicer.vtkMRMLModelNode()
        gridNumbersRightModel.SetName("Grid Numbers Right")
        gridNumbersRightModel.SetAndObservePolyData(gridNumbers.GetOutput())

        gridNumbersRightDisplay = slicer.vtkMRMLModelDisplayNode()
        gridNumbersRightDisplay.Copy(gridLettersTopDisplay)
        slicer.mrmlScene.AddNode(gridNumbersRightDisplay)

        slicer.mrmlScene.AddNode(gridNumbersRightModel)
        workflowFunctions.setParameter('guideHolesNumbersRightModelNodeID', gridNumbersRightModel.GetID())
        gridNumbersRightModel.SetAndObserveDisplayNodeID(gridNumbersRightDisplay.GetID())

        # transform in guide sheet coordinates to line the grid
        numbersRightTransform = slicer.vtkMRMLLinearTransformNode()
        numbersRightTransform.SetName("Grid Numbers Right xform")
        numbersRightMatrix = vtk.vtkMatrix4x4()
        # scale the text, and flip so can be read from inferior
        numbersRightMatrix.SetElement(0,0,-3.5)
        numbersRightMatrix.SetElement(1,1,3.5)
        numbersRightMatrix.SetElement(2,2,-3.5)
        # position it
        numbersX = ((numCols * spacingBetweenCols) / 2.0) + (3.0 * offsetX)
        numbersY = ((numRows * spacingBetweenRows) / 2.0) - (2.0 * offsetY)
        numbersRightMatrix.SetElement(0,3,numbersX)
        numbersRightMatrix.SetElement(1,3,numbersY)

        numbersRightTransform.SetMatrixTransformToParent(numbersRightMatrix)
        slicer.mrmlScene.AddNode(numbersRightTransform)

        # put into patient space
        if guideSheetTransformNodeID is not None:
            numbersRightTransform.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        gridNumbersRightModel.SetAndObserveTransformNodeID(numbersRightTransform.GetID())

        # Place along patient left of the grid
        gridNumbersLeftModel = slicer.vtkMRMLModelNode()
        gridNumbersLeftModel.SetName("Grid Numbers Left")
        gridNumbersLeftModel.SetAndObservePolyData(gridNumbers.GetOutput())

        gridNumbersLeftDisplay = slicer.vtkMRMLModelDisplayNode()
        gridNumbersLeftDisplay.Copy(gridLettersTopDisplay)
        slicer.mrmlScene.AddNode(gridNumbersLeftDisplay)

        slicer.mrmlScene.AddNode(gridNumbersLeftModel)
        workflowFunctions.setParameter('guideHolesNumbersLeftModelNodeID', gridNumbersLeftModel.GetID())
        gridNumbersLeftModel.SetAndObserveDisplayNodeID(gridNumbersLeftDisplay.GetID())

        # transform in guide sheet coordinates to line the grid
        numbersLeftTransform = slicer.vtkMRMLLinearTransformNode()
        numbersLeftTransform.SetName("Grid Numbers Left xform")
        numbersLeftMatrix = vtk.vtkMatrix4x4()
        # scale the text, and flip so can be read from inferior
        numbersLeftMatrix.SetElement(0,0,-3.5)
        numbersLeftMatrix.SetElement(1,1,3.5)
        numbersLeftMatrix.SetElement(2,2,-3.5)
        # position it
        numbersX = -((numCols * spacingBetweenCols) / 2.0)
        numbersY = ((numRows * spacingBetweenRows) / 2.0) - (2.0 * offsetY)
        numbersLeftMatrix.SetElement(0,3,numbersX)
        numbersLeftMatrix.SetElement(1,3,numbersY)

        numbersLeftTransform.SetMatrixTransformToParent(numbersLeftMatrix)
        slicer.mrmlScene.AddNode(numbersLeftTransform)

        # put into patient space
        if guideSheetTransformNodeID is not None:
            numbersLeftTransform.SetAndObserveTransformNodeID(guideSheetTransformNodeID)
        gridNumbersLeftModel.SetAndObserveTransformNodeID(numbersLeftTransform.GetID())


    # Create a model that has multiple ellipsoids in it's poly data, each at
    # a target location.
    def createTargetEllipsoidsModel(self):
        fiducials = self.targetFiducialsNode
        if fiducials is None:
            workflowFunctions.popupWarning("Unable to create target ellipsoids model")
            return
        modelID = workflowFunctions.getParameter('targetEllipsoidsNodeID')
        modelNode = None
        if modelID is not None:
            modelNode = slicer.mrmlScene.GetNodeByID(modelID)
        if modelNode is None:
            # create a new one
            modelNode = slicer.vtkMRMLModelNode()
            modelNode.SetName("Target Ellipsoids")
            slicer.mrmlScene.AddNode(modelNode)
            modelID = modelNode.GetID()
            workflowFunctions.setParameter('targetEllipsoidsNodeID', modelID)

            # set up a display node
            displayNode = slicer.vtkMRMLModelDisplayNode()
            displayNode.SetBackfaceCulling(0)
            displayNode.SetOpacity(0.5)
            displayNode.SetSliceIntersectionVisibility(1)
            # use flat interpolation as the super ellipsoid has a seam otherwise
            displayNode.SetInterpolation(displayNode.FlatInterpolation)
            slicer.mrmlScene.AddNode(displayNode)
            modelNode.SetAndObserveDisplayNodeID(displayNode.GetID())

            # don't display to start
            modelNode.SetDisplayVisibility(0)

        # generate ellipsoids at the selected size at each target location
        self.updateTargetEllipsoidGeometry()
        # set the point locations and visibility
        self.updateTargetEllipsoidsModel()

    # update the ellipsoid shape source
    def updateTargetEllipsoidGeometry(self):
        radiusIndex = self.ellipsoidsComboBox.currentIndex
        radiusVector = self.ellipsoidsComboBox.itemData(radiusIndex)
        if radiusIndex == self.ellipsoidRadiusIndex and radiusVector == self.ellipsoidRadiusVector:
            return
        self.ellipsoidRadiusIndex = radiusIndex
        self.ellipsoidRadiusVector = radiusVector

        isBiopsy = False
        comboText = self.ellipsoidsComboBox.currentText
        if comboText.find("Biopsy") != -1:
            isBiopsy = True
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'radiusIndex: ', radiusIndex
            print 'radiusVector: ', self.ellipsoidRadiusVector
            print '\t', self.ellipsoidRadiusVector.x(), self.ellipsoidRadiusVector.y(), self.ellipsoidRadiusVector.z()
            print '\tis biopsy = ', isBiopsy

        # regenerate the ellipsoid geometry
        # build the ellipsoid
        if isBiopsy:
            # use this to get a cylinder along Z
            shapePower = 0.25
        else:
            # use this to get an ellipsoid
            shapePower = 1
        ellipsoid = vtk.vtkParametricSuperEllipsoid()
        ellipsoid.SetXRadius(self.ellipsoidRadiusVector.x())
        ellipsoid.SetYRadius(self.ellipsoidRadiusVector.y())
        ellipsoid.SetZRadius(self.ellipsoidRadiusVector.z())
        # squareness of Z axis
        ellipsoid.SetN1(shapePower)
        # squareness of XY plane
        ellipsoid.SetN2(1)
        self.ellipsoidShapeSource.SetParametricFunction(ellipsoid)


    # Called when the target list is updated to update the model.
    # Sets location, visibility. Call create to set the glyph type.
    def updateTargetEllipsoidsModel(self):
        if self.targetFiducialsNode is None:
            print 'updateTargetEllipsoidsModel: no targets fid node'
            return
        modelID = workflowFunctions.getParameter('targetEllipsoidsNodeID')
        if modelID is None:
            print 'updateTargetEllipsoidsModel: no model id, create first!'
            return
        modelNode = slicer.mrmlScene.GetNodeByID(modelID)
        if modelNode is None:
            print 'updateTargetEllipsoidsModel: model node with id', modelID, 'not found!'

        # set the color
        comboText = self.ellipsoidsComboBox.currentText
        isBiopsy = False
        isLaserDiffuser = False
        if comboText.find("Biopsy") != -1:
            modelColor = self.modelColors['Biopsy']
            # for the biopsy throw, will need an offset cylinder
            isBiopsy = True
        elif comboText.find("Cryo") != -1:
            modelColor = self.modelColors['CryoBlue']
        elif comboText.find("Laser") != -1:
            modelColor = self.modelColors['LaserRed']
            if comboText.find("Diffuser") != -1:
                isLaserDiffuser = True
        else:
            # default
            modelColor = self.modelColors['Biopsy']
        modelNode.GetDisplayNode().SetColor(modelColor.redF(), modelColor.greenF(), modelColor.blueF())

        # clear out the model
        modelNode.SetAndObservePolyData(None)

        numberOfFids = self.targetFiducialsNode.GetNumberOfFiducials()
        if (numberOfFids == 0):
            return

        # build locations
        points = vtk.vtkPoints()

        pointNumber = 0
        for fidNum in range(numberOfFids):
            # only show the ellipsoid if fiducial is visible
            if self.targetFiducialsNode.GetNthFiducialVisibility(fidNum):
                pos = [0,0,0]
                self.targetFiducialsNode.GetNthFiducialPosition(fidNum, pos)
                if isBiopsy:
                    # adjust point along the throw
                    pos[2] = pos[2] + self.ellipsoidRadiusVector.z()
                elif isLaserDiffuser:
                    # the ablation zone is back along the probe 12mm
                    pos[2] = pos[2] - 12.0
                points.InsertPoint(pointNumber, pos[0], pos[1], pos[2])
                pointNumber = pointNumber + 1

        # if no targets are present or showing, don't proceed since otherwise may
        # get a shape at the origin even with an empty points array
        if points.GetNumberOfPoints() == 0:
            return

        # add to glyph as points in a poly data
        polyData = vtk.vtkPolyData()
        polyData.SetPoints(points)

        # use a glyph that takes in a shape source and locations
        glyph = vtk.vtkGlyph3D()

        glyph.SetInputDataObject(polyData)
        glyph.SetSourceConnection(self.ellipsoidShapeSource.GetOutputPort())
        # TBD: orientation
        glyph.Update()

        modelNode.SetAndObservePolyData(glyph.GetOutput())

        # set visibility
        self.setEllipsoidsVisibility(workflowFunctions.getParameter('TARGET_ELLIPSOIDS_VIS_Flag'))

    def onEllipsoidTypeChanged(self, int):
        self.updateTargetEllipsoidGeometry()
        self.updateTargetEllipsoidsModel()

    #
    #
    # Methods to give anatomical guidance by showing the PI-RADS v2 zone maps
    #
    #
    def onShowPIRADS(self):
        self.piradsMapPath = os.path.join(self.resourcePath, "Images", "Prostate_Template.png")
        if os.path.exists(self.piradsMapPath) is False:
            workflowFunctions.popupError("Can't show PI-RADS map", "E:409 Unable to find PI-RADS anatomical map.\n\nFile does not exist:\n" + self.piradsMapPath)
            return

        # pop up a window showing the PIRADS guidance
        if self.piradsBox is None:
            self.piradsBox = qt.QDialog()
            self.piradsBox.setModal(False)
            self.piradsBox.setWindowTitle('PI-RADS Anatomical Map')
            # stay on top by default
            self.piradsBox.setWindowFlags(self.piradsBox.windowFlags() | qt.Qt.WindowStaysOnTopHint)
            layout = qt.QVBoxLayout()
            self.piradsBox.setLayout(layout)

            # set up a label to show the image
            self.piradsMapLabel = qt.QLabel()
            # allow scaling to the loaded image
            self.piradsMapLabel.scaledContents = True
            self.piradsPixmap = qt.QPixmap(self.piradsMapPath)
            self.piradsMapLabel.setPixmap(self.piradsPixmap)
            self.piradsMapLabel.setMask(self.piradsPixmap.mask())
            layout.addWidget(self.piradsMapLabel)

            # toggle stay on top
            self.piradsStayOnTopCheckBox = qt.QCheckBox('Stay on Top')
            self.piradsStayOnTopCheckBox.checked = True
            self.piradsStayOnTopCheckBox.connect('toggled(bool)', self.onCheckStayOnTop)
            layout.addWidget(self.piradsStayOnTopCheckBox)

            # add buttons for zone overlays
            zonesFrame = qt.QFrame()
            zonesLayout = qt.QHBoxLayout()
            zonesFrame.setLayout(zonesLayout)

            clearZones = qt.QPushButton('Clear Zones')
            clearZones.connect('clicked(bool)', self.onClearPIRADS)
            zonesLayout.addWidget(clearZones)

            showPZ = qt.QPushButton('Show PZ')
            showPZ.toolTip = 'Highlight Peripheral Zone'
            showPZ.connect('clicked(bool)', self.onShowPIRADSPZ)
            zonesLayout.addWidget(showPZ)

            showCZ = qt.QPushButton('Show CZ')
            showCZ.toolTip = 'Highlight Central Zone'
            showCZ.connect('clicked(bool)', self.onShowPIRADSCZ)
            zonesLayout.addWidget(showCZ)

            showTZ = qt.QPushButton('Show TZ')
            showTZ.toolTip = 'Highlight Transition Zone'
            showTZ.connect('clicked(bool)', self.onShowPIRADSTZ)
            zonesLayout.addWidget(showTZ)

            showAFS = qt.QPushButton('Show AFS')
            showAFS.toolTip = 'Highlight Anterior Fibromuscular Stroma Zone'
            showAFS.connect('clicked(bool)', self.onShowPIRADSAFS)
            zonesLayout.addWidget(showAFS)

            showUS = qt.QPushButton('Show US')
            showUS.toolTip = 'Highlight Urethral Sphincter Zone'
            showUS.connect('clicked(bool)', self.onShowPIRADSUS)
            zonesLayout.addWidget(showUS)

            layout.addWidget(zonesFrame)

            # ok button
            buttonBox = qt.QDialogButtonBox(qt.QDialogButtonBox.Ok)
            buttonBox.connect('accepted()', self.piradsBox, 'accept()')
            self.piradsBox.layout().addWidget(buttonBox)



        # show it in an informational pop up
        self.piradsBox.show()

    def onCheckStayOnTop(self):
        if workflowFunctions.getParameter('devModeFlag') == 1:
            print 'onCheckStayOnTop: stay on top is checked = ',self.piradsStayOnTopCheckBox.checked
            print '\twindow flags = ',  self.piradsBox.windowFlags()
        if self.piradsStayOnTopCheckBox.checked:
            self.piradsBox.setWindowFlags(self.piradsBox.windowFlags() | qt.Qt.WindowStaysOnTopHint)
        else:
            self.piradsBox.setWindowFlags(self.piradsBox.windowFlags() ^ qt.Qt.WindowStaysOnTopHint)
        # have to re-show it
        self.piradsBox.show()

    def onClearPIRADS(self):
        # clear the highlights on the map
        self.piradsMapLabel.setPixmap(self.piradsPixmap)
        self.piradsMapLabel.setMask(self.piradsPixmap.mask())

    def addOverlay(self, overlay):
        baseImage = qt.QImage(self.piradsMapPath)
        # combinedImage = qt.QImage(baseImage.size(), baseImage.Format()))
        combined = qt.QPixmap(baseImage.size())
        painter = qt.QPainter(combined)
        # draw the image as is
        painter.drawImage(qt.QPoint(0,0), baseImage)
        # draw overlay at 100% opacity
        painter.setOpacity(1.0)
        painter.drawImage(qt.QPoint(0,0), overlay)
        painter.end()
        return combined

    def onShowPIRADSPZ(self):
        # show the peripheral zone highlight
        imagePath = os.path.join(self.resourcePath, "Images", "Prostate_PZ_Area.png")
        if os.path.exists(imagePath) is False:
            workflowFunctions.popupError("Can't show PI-RADS highlight", "E:410 Unable to find PI-RADS PZ mask.\n\nFile does not exist:\n" + imagePath)
            return
        overlayImage = qt.QImage(imagePath)
        # overlay on the full pixmap
        comboPixmap = self.addOverlay(overlayImage)
        self.piradsMapLabel.setPixmap(comboPixmap)
        self.piradsMapLabel.setMask(comboPixmap.mask())

    def onShowPIRADSCZ(self):
        # show the central zone highlight
        imagePath = os.path.join(self.resourcePath, "Images", "Prostate_CZ_Area.png")
        if os.path.exists(imagePath) is False:
            workflowFunctions.popupError("Can't show PI-RADS highlight", "E:410 Unable to find PI-RADS CZ mask.\n\nFile does not exist:\n" + imagePath)
            return
        overlayImage = qt.QImage(imagePath)
        # overlay on the full pixmap
        comboPixmap = self.addOverlay(overlayImage)
        self.piradsMapLabel.setPixmap(comboPixmap)
        self.piradsMapLabel.setMask(comboPixmap.mask())

    def onShowPIRADSTZ(self):
        # show the transition zone highlight
        imagePath = os.path.join(self.resourcePath, "Images", "Prostate_TZ_Area.png")
        if os.path.exists(imagePath) is False:
            workflowFunctions.popupError("Can't show PI-RADS highlight", "E:410 Unable to find PI-RADS TZ mask.\n\nFile does not exist:\n" + imagePath)
            return
        overlayImage = qt.QImage(imagePath)
        # overlay on the full pixmap
        comboPixmap = self.addOverlay(overlayImage)
        self.piradsMapLabel.setPixmap(comboPixmap)
        self.piradsMapLabel.setMask(comboPixmap.mask())

    def onShowPIRADSAFS(self):
        # show the Anterior Fibromuscular Stroma zone highlight
        imagePath = os.path.join(self.resourcePath, "Images", "Prostate_AFS_Area.png")
        if os.path.exists(imagePath) is False:
            workflowFunctions.popupError("Can't show PI-RADS highlight", "E:410 Unable to find PI-RADS AFS mask.\n\nFile does not exist:\n" + imagePath)
            return
        overlayImage = qt.QImage(imagePath)
        # overlay on the full pixmap
        comboPixmap = self.addOverlay(overlayImage)
        self.piradsMapLabel.setPixmap(comboPixmap)
        self.piradsMapLabel.setMask(comboPixmap.mask())

    def onShowPIRADSUS(self):
        # show the Urethral Sphincter zone highlight
        imagePath = os.path.join(self.resourcePath, "Images", "Prostate_US_Area.png")
        if os.path.exists(imagePath) is False:
            workflowFunctions.popupError("Can't show PI-RADS highlight", "E:410 Unable to find PI-RADS US mask.\n\nFile does not exist:\n" + imagePath)
            return
        overlayImage = qt.QImage(imagePath)
        # overlay on the full pixmap
        comboPixmap = self.addOverlay(overlayImage)
        self.piradsMapLabel.setPixmap(comboPixmap)
        self.piradsMapLabel.setMask(comboPixmap.mask())


    # Change the add button to give feedback that we're in target adding mode.
    # Button is reset once target has been added or cancelled.
    def enableTargetButton(self, enabled):
        if enabled:
            self.addTargetButton.setText("Add Target")
            workflowFunctions.setButtonIcon(self.addTargetButton, 'Large/lg_target.png')
            workflowFunctions.colorPushButtonFromPalette(self.addTargetButton, 'Primary')
            numberOfTargets = self.targetFiducialsNode.GetNumberOfFiducials()
            if numberOfTargets > 0:
                if workflowFunctions.getParameter('gfmPresentFlag') is 1:
                    workflowFunctions.setStatusLabel("Waiting for user to print guide")
                else:
                    workflowFunctions.setStatusLabel("Waiting for confirmation scan")
            else:
                workflowFunctions.setStatusLabel("Waiting for user to create targets")
        else:
            self.addTargetButton.setText("Adding new target...")
            workflowFunctions.setButtonIcon(self.addTargetButton, 'Large/lg_gry2target.png')
            workflowFunctions.colorPushButtonFromPalette(self.addTargetButton, 'Secondary')
            workflowFunctions.setStatusLabel("Waiting for user to add new target.")
