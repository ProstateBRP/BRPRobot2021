Sequence Diagram
================

Initialization
--------------

```mermaid
sequenceDiagram

title System Sequence Diagram

participant "Robot"
participant "Robot Listener"
participant "3D Slicer GUI"
participant "MR IGTL Bridge"
participant "MRScanner"

"3D Slicer GUI"->>"MR IGTL Bridge":Command IGTL(STRING)
activate "3D Slicer GUI"
activate "MR IGTL Bridge"
"MR IGTL Bridge"->>"MRScanner":Command
activate "MRScanner"
note right of "MRScanner":START UP SCANNER
"MRScanner"->>"MR IGTL Bridge":Status
deactivate "MRScanner"
"MR IGTL Bridge"->>"3D Slicer GUI":Status IGTL(STATUS)
deactivate "3D Slicer GUI"
deactivate "MR IGTL Bridge"

note over "MR IGTL Bridge","MRScanner":Transition to "Idle"
alt Until status code is OK
"3D Slicer GUI"->>"Robot Listener":Command IGTL(STRING)
activate "3D Slicer GUI"
activate "Robot Listener"
"Robot Listener"->>"Robot":Command
activate "Robot"
note left of Robot:START_UP
"Robot"->>"Robot Listener":Acknowledgement
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(STRING)
"Robot"->>"Robot Listener":Status
deactivate "Robot"
"Robot Listener"->>"3D Slicer GUI":Status IGTL(CURRENT_STATUS)


deactivate "Robot Listener"
deactivate "3D Slicer GUI"
note left of "Robot":STATUS CODE: OK\n               or\nSTATUS CODE: DNR
"Robot"->>"Robot Listener":Status
"Robot Listener"->>"3D Slicer GUI":Status IGTL(START_UP)
end

```

Patient set up in bore
----------------------


Calibration
-----------

```mermaid
sequenceDiagram

participant "Robot"
participant "Robot Listener"
participant "3D Slicer GUI"
participant "MR IGTL Bridge"
participant "MRScanner"

loop until status code is OK
"3D Slicer GUI"->>"Robot Listener":Command IGTL(STRING)
activate "3D Slicer GUI"
activate "Robot Listener"
"Robot Listener"->>"Robot":Command
activate "Robot"
note left of "Robot":CALIBRATION
"Robot"->>"Robot Listener":Acknowledgement
note left of "Robot":STATUS code: OK\n              or\nSTATUS code: DNR
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(STRING)
"Robot"->>"Robot Listener":Status
deactivate "Robot"
"Robot Listener"->>"3D Slicer GUI":Status IGTL(CURRENT_STATUS)
deactivate "3D Slicer GUI"
deactivate "Robot Listener"
end
note right of "3D Slicer GUI":Show that robot has \nentered Calibration phase
note over "MRScanner":Zframe scan\nfor registration
"MRScanner"->>"3D Slicer GUI":Zframe DICOM image
note right of "3D Slicer GUI":Calculate calibration matrix\nin the Slicer GUI
loop until status code is OK
"3D Slicer GUI"->>"Robot Listener":Transform IGTL(TRANSFORM)
activate "3D Slicer GUI"
activate "Robot Listener"
"Robot Listener"->>"Robot":Transform
activate "Robot"
note left of "Robot":CALIBRATION
"Robot"->>"Robot Listener":Acknowledgement
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(TRANSFORM)
note left of "Robot":STATUS code: OK \n              or \nSTATUS code: CE
"Robot"->>"Robot Listener":Status
deactivate "Robot"
"Robot Listener"->>"3D Slicer GUI":Status IGTL(CURRENT_STATUS)
deactivate "3D Slicer GUI"
deactivate "Robot Listener"

end
```

Target planning
---------------
```mermaid
sequenceDiagram

participant "Robot"
participant "Robot Listener"
participant "3D Slicer GUI"
participant "MR IGTL Bridge"
participant "MRScanner"

loop until status code is OK
"3D Slicer GUI"->>"Robot Listener":Command IGTL(STRING)
activate "3D Slicer GUI"
activate "Robot Listener"
"Robot Listener"->>"Robot":Command
activate "Robot"
note left of "Robot":TARGETING
"Robot"->>"Robot Listener":Acknowledgement
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(STRING)
note over "Robot":Confirm if robot is ready for targeting\nCheck if calibration was received
note left of "Robot":STATUS code: OK\n              or\nSTATUS code: DNR
"Robot"->>"Robot Listener":Status
deactivate "Robot"
"Robot Listener"->>"3D Slicer GUI":Status IGTL(CURRENT_STATUS)
deactivate "3D Slicer GUI"
deactivate "Robot Listener"
end

note over "MRScanner":Anatomical T2 scan \nfor targeting
"MRScanner"->>"3D Slicer GUI":T2 DICOM image
note over "3D Slicer GUI":Select target point and \nneedle position in GUI

activate "3D Slicer GUI"
deactivate "3D Slicer GUI"
loop until status code is OK
"3D Slicer GUI"->>"Robot Listener":Transform IGTL(TRANSFORM)
activate "3D Slicer GUI"
activate "Robot Listener"
"Robot Listener"->>"Robot":Transform
activate "Robot"
note left of "Robot":TARGETING

"Robot"->>"Robot Listener":Acknowledgement
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(TRANSFORM)

note over "Robot":Calculate if planned\ntarget is reachable
alt if the target point is reachable within some maximum error
note left of "Robot":STATUS code: OK
"Robot"->>"Robot Listener":Transform
"Robot Listener"->>"3D Slicer GUI":Transform IGTL(TRANSFORM)
"Robot"->>"Robot Listener":Status
"Robot Listener"->>"3D Slicer GUI":Status IGTL(STATUS)
note over "3D Slicer GUI":REACHABLE_TARGET accepted

else if the target point is NOT reachable within some maximum error
note left of "Robot":STATUS code: CE\nNot a valid target
"Robot"->>"Robot Listener":Status
"Robot Listener"->>"3D Slicer GUI":Status IGTL(STATUS)
note over "3D Slicer GUI":Target point NOT reachable

else
note left of "Robot":STATUS code: DNR\nNot in targeting mode
"Robot"->>"Robot Listener":Status
deactivate "Robot"
"Robot Listener"->>"3D Slicer GUI":Status IGTL(STATUS)

deactivate "3D Slicer GUI"
deactivate "Robot Listener"
note over "3D Slicer GUI":"Robot" not in valid mode
end
end
```


Idle
----

```mermaid
sequenceDiagram

participant "Robot"
participant "Robot Listener"
participant "3D Slicer GUI"
participant "MR IGTL Bridge"
participant "MRScanner"


alt if the user subscribes parameters case
"3D Slicer GUI"->>"MR IGTL Bridge":Command IGTL(STRING)
activate "3D Slicer GUI"
activate "MR IGTL Bridge"
"MR IGTL Bridge"->>"MRScanner":Command

activate "MRScanner"
"MRScanner"->>"MR IGTL Bridge":Status
deactivate "MRScanner"
"MR IGTL Bridge"->>"3D Slicer GUI":Status IGTL(STATUS)
deactivate "3D Slicer GUI"
deactivate "MR IGTL Bridge"
end
```

Scan & Move
-----------

```mermaid
sequenceDiagram

participant "Robot"
participant "Robot Listener"
participant "3D Slicer GUI"
participant "MR IGTL Bridge"
participant "MRScanner"

loop Imaging loop
alt if the user subscribes parameters case
"3D Slicer GUI"->>"MR IGTL Bridge":Transform IGTL(TRANSFORM)
"MR IGTL Bridge"->>"MRScanner":Transform
note over "MRScanner":Updates the scan plane
end
note over "MRScanner":Acquires an image
"MRScanner"->>"MR IGTL Bridge":Image
"MR IGTL Bridge"->>"3D Slicer GUI":Image IGTL(IMAGE)
end

"3D Slicer GUI"->>"Robot Listener":Command IGTL(STRING)
"Robot Listener"->>"Robot":Command

note left of "Robot":MOVE_TO_TARGET
"Robot"->>"Robot Listener":Acknowledgement
"Robot Listener"->>"3D Slicer GUI":Acknowledgement IGTL(STRING)
loop Movement loop
"Robot"->>"Robot Listener":Transform
"Robot Listener"->>"3D Slicer GUI":Transform IGTL(TRANSFORM)
note over "3D Slicer GUI":CURRENT_POSITION received
end

"Robot"->>"Robot Listener":Status
"Robot Listener"->>"3D Slicer GUI":Status IGTL(STATUS)
```



                                                                        
