Sequence Diagram
================

Initialization
--------------

```mermaid
sequenceDiagram

title System Sequence Diagram

participant R as Robot
participant SGUI as 3D Slicer
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

alt Until status code is OK
activate SGUI
activate R
SGUI->>R:Command IGTL(STRING, START_UP)
R->>SGUI:Acknowledgement IGTL(STRING, START_UP)
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)

note left of R:⠀⠀⠀STATUS:OK or STATUS:DNR⠀⠀⠀
R->>SGUI:Status IGTL(STRING, START_UP)
deactivate R
deactivate SGUI
end

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```

Patient set up in bore
----------------------


Calibration
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant SGUI as 3D Slicer
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner


loop until status code is OK
activate SGUI
activate R
SGUI->>R:Command IGTL(STRING, CALIBRATION)
note left of R:CALIBRATION
note left of R:⠀⠀⠀STATUS:OK or STATUS:DNR⠀⠀⠀
R->>SGUI:Acknowledgement IGTL(STRING)
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate R
deactivate SGUI
end
note right of SGUI:⠀⠀⠀⠀⠀⠀Show that robot has entered Calibration phase⠀⠀⠀⠀⠀⠀
note over MRS:⠀⠀⠀Zframe scan for registration⠀⠀⠀
MRS->>SGUI:Zframe DICOM image
note right of SGUI:⠀⠀⠀Select target in the Slicer GUI⠀⠀⠀
loop until status code is OK
activate SGUI
activate R
SGUI->>R:Transform IGTL(TRANSFORM)
note left of R:CALIBRATION
R->>SGUI:Acknowledgement IGTL(TRANSFORM)
note left of R:⠀⠀⠀STATUS:OK or STATUS:CE⠀⠀⠀
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate R
deactivate SGUI

end

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```


Planning
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant SGUI as 3D Slicer
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner


loop until status code is OK
SGUI->>R:Command IGTL(STRING, PLANNING)
activate SGUI
activate R

note left of R:PLANNING
note left of R:⠀⠀⠀STATUS:OK or STATUS:DNR⠀⠀⠀
R->>SGUI:Acknowledgement IGTL(STRING)
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate R
deactivate SGUI
end
note right of SGUI:⠀⠀⠀⠀⠀⠀Show that robot has entered Planning phase⠀⠀⠀⠀⠀⠀
note over MRS:⠀⠀⠀⠀Anatomical T2 scan for planning⠀⠀⠀⠀
MRS->>SGUI:T2 DICOM image
note over SGUI:⠀⠀⠀⠀⠀⠀Select target point and needle position in GUI⠀⠀⠀⠀⠀⠀
loop until status code is OK
SGUI->>R:Transform IGTL(TRANSFORM, TARGET)
activate SGUI
activate R
note left of R:PLANNING
R->>SGUI:Acknowledgement IGTL(TRANSFORM)
note left of R:⠀⠀⠀STATUS:OK or STATUS:CE⠀⠀⠀
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate R
deactivate SGUI

end

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```

Targeting
---------------
```mermaid
sequenceDiagram

participant R as Robot
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

loop until status code is OK
SGUI->>R:Command IGTL(STRING, TARGETING)
activate SGUI
activate R
note left of R:TARGETING
R->>SGUI:Acknowledgement IGTL(STRING)
note over R:⠀⠀⠀⠀⠀⠀⠀⠀⠀Confirm if robot is ready for targeting and Check if calibration was received⠀⠀⠀⠀⠀⠀⠀⠀⠀
note left of R:⠀⠀⠀⠀STATUS:OK or STATUS:DNR⠀⠀⠀⠀
R->>SGUI:Status IGTL(STRING, CURRENT_STATUS)
deactivate SGUI
deactivate R
end

activate SGUI
deactivate SGUI
loop until status code is OK
SGUI->>R:Transform IGTL(TRANSFORM)
activate SGUI
activate R
note left of R:TARGETING

R->>SGUI:Acknowledgement IGTL(TRANSFORM)

note over R:⠀⠀⠀⠀⠀⠀Calculate if planned target is reachable⠀⠀⠀⠀⠀⠀
alt if the target point is reachable within some maximum error
note left of R:STATUS:OK
R->>SGUI:Transform IGTL(TRANSFORM)
R->>SGUI:Status IGTL(STRING, STATUS)
note over SGUI:⠀⠀⠀REACHABLE_TARGET accepted⠀⠀⠀

else if the target point is NOT reachable within some maximum error
note left of R:⠀⠀⠀⠀⠀⠀STATUS: CE or Not a valid target⠀⠀⠀⠀⠀⠀
R->>SGUI:Status IGTL(STRING, STATUS)
note over SGUI:⠀⠀⠀Target point NOT reachable⠀⠀⠀

else
note left of R:⠀⠀⠀⠀⠀⠀STATUS code: DNR or Not in targeting mode⠀⠀⠀⠀⠀⠀
R->>SGUI:Status IGTL(STRING, STATUS)
deactivate R

deactivate SGUI
note over SGUI:⠀⠀⠀R not in valid mode⠀⠀⠀
end
end

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```


Idle
----

```mermaid
sequenceDiagram

participant R as Robot
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

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```

Scan & Move (Revised on Feb 23, 2023)
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

SGUI->>R:Command IGTL(STRING, MOVE_TO_TARGET)
R->>SGUI:Acknowledgement IGTL(STRING, ACK_XXXXX)
R->>SGUI:Status IGTL(STATUS)
R->>SGUI:Transform IGTL(TRANSFORM, CURR_POS)

loop Image feedback
SGUI->>MRIGTL:Transform IGTL(TRANSFORM, PLANE_0)
MRIGTL->>MRS:Transform
note over MRS:⠀⠀⠀Updates the scan plane⠀⠀⠀
note over MRS:⠀⠀⠀Acquires an image⠀⠀⠀
MRS->>MRIGTL:Image
MRIGTL->>SGUI:Image IGTL(IMAGE)
MRIGTL->>SGUI:Timestamp IGTL(STRING, TIMESTAMP)
note over SGUI: Needle detection

SGUI->>R: Transform IGTL(TRANSFORM, NPOSE_XXXX)
R->>SGUI: Acknowledgement IGTL(STATUS, ACK_XXXX)
note over R: Check if the target is still reachable)
R->>SGUI: Status IGTL(STATUS, )

SGUI->>R: Command IGTL(STRING, CMD_XXXX, CURRENT_POSITION)
R->>SGUI: Transform IGTL(TRANSFORM, CURR_POS)
end
```

Scan & Move (Obsolete)
-----------

```mermaid
sequenceDiagram

participant R as Robot
participant SGUI as 3D Slicer GUI
participant MRIGTL  as MR IGTL Bridge
participant MRS as MR Scanner

loop Imaging loop
alt if the user subscribes parameters case
SGUI->>MRIGTL:Transform IGTL(TRANSFORM)
MRIGTL->>MRS:Transform
note over MRS:⠀⠀⠀Updates the scan plane⠀⠀⠀
end
note over MRS:⠀⠀⠀Acquires an image⠀⠀⠀
MRS->>MRIGTL:Image
MRIGTL->>SGUI:Image IGTL(IMAGE)
end

SGUI->>R:Command IGTL(STRING, MOVE_TO_TARGET)

note left of R:MOVE_TO_TARGET
R->>SGUI:Acknowledgement IGTL(STRING)

R->>SGUI:Status IGTL(STRING, STATUS)

loop Current Position loop
SGUI->>R:Command IGTL(STRING, GET_TRANSFORM)
R->>SGUI:Transform IGTL(TRANSFORM)
note over SGUI:⠀⠀⠀CURRENT_POSITION received⠀⠀⠀
end
```


                                                                        
