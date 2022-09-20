Sequence Diagram
================

Initialization
--------------

```mermaid
sequenceDiagram

title System Sequence Diagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

SGUI->>MRIGTL:Command IGTL(STRING, START_UP)
activate SGUI
activate MRIGTL
MRIGTL->>MRS:Command
activate MRS
note right of MRS:START UP SCANNER
MRS->>MRIGTL:Status
deactivate MRS
MRIGTL->>SGUI:Status IGTL(STRING, STATUS)
deactivate SGUI
deactivate MRIGTL

note over MRIGTL,MRS:Transition to "Idle"
alt Until status code is OK
SGUI->>RL:Command IGTL(STRING, START_UP)
activate SGUI
activate RL
RL->>R:Command
activate R
note left of Robot:START_UP
R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(STRING, START_UP)
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)


deactivate RL
deactivate SGUI
note left of R:STATUS CODE: OK\n               or\nSTATUS CODE: DNR
R->>RL:Status
RL->>SGUI:Status IGTL(STRING, START_UP)
end

```

Patient set up in bore
----------------------


Calibration
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner


loop until status code is OK
SGUI->>RL:Command IGTL(STRING, CALIBRATION)
activate SGUI
activate RL
RL->>R:Command
activate R
note left of R:CALIBRATION
R->>RL:Acknowledgement
note left of R:STATUS code: OK\n              or\nSTATUS code: DNR
RL->>SGUI:Acknowledgement IGTL(STRING)
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate RL
end
note right of SGUI:Show that robot has \nentered Calibration phase
note over MRS:Zframe scan\nfor registration
MRS->>SGUI:Zframe DICOM image
note right of SGUI:Select target in the Slicer GUI
loop until status code is OK
SGUI->>RL:Transform IGTL(TRANSFORM)
activate SGUI
activate RL
RL->>R:Transform
activate R
note left of R:CALIBRATION
R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(TRANSFORM)
note left of R:STATUS code: OK \n              or \nSTATUS code: CE
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate RL

end
```


Planning
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner


loop until status code is OK
SGUI->>RL:Command IGTL(STRING, PLANNING)
activate SGUI
activate RL
RL->>R:Command
activate R
note left of R:PLANNING
R->>RL:Acknowledgement
note left of R:STATUS code: OK\n              or\nSTATUS code: DNR
RL->>SGUI:Acknowledgement IGTL(STRING)
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate RL
end
note right of SGUI:Show that robot has \nentered Planning phase
note over MRS:Scan for planning
MRS->>SGUI:Planning DICOM image
note right of SGUI:Calculate calibration matrix\nin the Slicer GUI
loop until status code is OK
SGUI->>RL:Transform IGTL(TRANSFORM, TARGET)
activate SGUI
activate RL
RL->>R:Transform
activate R
note left of R:PLANNING
R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(TRANSFORM)
note left of R:STATUS code: OK \n              or \nSTATUS code: CE
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate RL

end
```

Targeting
---------------
```mermaid
sequenceDiagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

loop until status code is OK
SGUI->>RL:Command IGTL(STRING, TARGETING)
activate SGUI
activate RL
RL->>R:Command
activate R
note left of R:TARGETING
R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(STRING)
note over R:Confirm if robot is ready for targeting\nCheck if calibration was received
note left of R:STATUS code: OK\n              or\nSTATUS code: DNR
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate RL
end

note over MRS:Anatomical T2 scan \nfor targeting
MRS->>SGUI:T2 DICOM image
note over SGUI:Select target point and \nneedle position in GUI

activate SGUI
deactivate SGUI
loop until status code is OK
SGUI->>RL:Transform IGTL(TRANSFORM)
activate SGUI
activate RL
RL->>R:Transform
activate R
note left of R:TARGETING

R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(TRANSFORM)

note over R:Calculate if planned\ntarget is reachable
alt if the target point is reachable within some maximum error
note left of R:STATUS code: OK
R->>RL:Transform
RL->>SGUI:Transform IGTL(TRANSFORM)
R->>RL:Status
RL->>SGUI:Status IGTL(STRING, STATUS)
note over SGUI:REACHABLE_TARGET accepted

else if the target point is NOT reachable within some maximum error
note left of R:STATUS code: CE\nNot a valid target
R->>RL:Status
RL->>SGUI:Status IGTL(STRING, STATUS)
note over SGUI:Target point NOT reachable

else
note left of R:STATUS code: DNR\nNot in targeting mode
R->>RL:Status
deactivate R
RL->>SGUI:Status IGTL(STRING, STATUS)

deactivate SGUI
deactivate RL
note over SGUI:R not in valid mode
end
end
```


Idle
----

```mermaid
sequenceDiagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

alt if the user subscribes parameters case
SGUI->>MRIGTL:Command IGTL(STRING)
activate SGUI
activate MRIGTL
MRIGTL->>MRS:Command

activate MRS
MRS->>MRIGTL:Status
deactivate MRS
MRIGTL->>SGUI:Status IGTL(STRING, STATUS)
deactivate SGUI
deactivate MRIGTL
end
```

Scan & Move
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant RL as Robot Listener
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

loop Imaging loop
alt if the user subscribes parameters case
SGUI->>MRIGTL:Transform IGTL(TRANSFORM)
MRIGTL->>MRS:Transform
note over MRS:Updates the scan plane
end
note over MRS:Acquires an image
MRS->>MRIGTL:Image
MRIGTL->>SGUI:Image IGTL(IMAGE)
end

SGUI->>RL:Command IGTL(STRING, MOVE_TO_TARGET)
RL->>R:Command

note left of R:MOVE_TO_TARGET
R->>RL:Acknowledgement
RL->>SGUI:Acknowledgement IGTL(STRING)
loop Movement loop
R->>RL:Transform
RL->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:CURRENT_POSITION received
end

R->>RL:Status
RL->>SGUI:Status IGTL(STRING, STATUS)
```



                                                                        
