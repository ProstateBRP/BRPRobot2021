CommunicationTest
=================

Command line simulator software to perform communication test between navigation software and robot control software.

For the detail of the testing protocol, please see:

http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013


Overview
--------

The testing software consists of two console programs:

### NavigationTestSimulator
NavigationTestSimulator simulates the behaviour of navigation software e.g. 3D Slicer
to test the robot control software. Once it starts, it starts sending a series of messages defined in
[the testing protocol](http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013).

### RobotTestSimulator
RobotTestSimulator simulates the behaviour of robot control software. It responses to 
message sent from navigation software, and is usesful to test navigation software.

Tutorial
--------

Although NavigationTestSimulator and RobotTestSimulator are designed to be used with actual robot control software
and navigation software respectively, they can be used together. The following tutorial demonstrate
how to run those programs. We assume that those programs are running on the same machine and use port 18944.

First, open a terminal, go to the directory that contains the simulator programs, and start the RobotTestSimulator:

    $ ./RobotTestSimulator 18944

Now the RobotTestSimulator is waiting for a connection from the NavigationTestSimulator.
Then open another terminal, go to the directory that contains the simulator programs, and
start the NavigationTestSimulator:

    $ ./NavigationTestSimulator localhost 18944 1

The last argument '1' is the test number (1-10). Currently, only tests #1-4 are supported (July 7, 2013).
If the program has connected to the RobotTestSimulator successfully, you will see the following
messages on the terminal, where you launched the RobotTestSimulator:

    MESSAGE: Defect status:
    MESSAGE:    START_UP:DNR  :  OFF
    MESSAGE: Client connected. Starting a session...
    MESSAGE: Sending STRING( ACK_0001, START_UP )
    MESSAGE: Sending STATUS( START_UP )
    MESSAGE: Sending STRING( ACK_0002, PLANNING )
    MESSAGE: Sending STRING( ACK_0003, CALIBRATION )
    MESSAGE: Receiving TRANSFORM data type.
    
    MESSAGE: Sending TRANSFORM( ACK_0004 )
    MESSAGE: Sending STATUS( CALIBRATION )
    MESSAGE: Sending STRING( ACK_0005, TARGETING )
    MESSAGE: Sending STATUS( TARGETING )
    MESSAGE: Receiving TRANSFORM data type.
    
    MESSAGE: Sending TRANSFORM( ACK_0006 )
    MESSAGE: Sending STATUS( TARGET )
    MESSAGE: Sending TRANSFORM( TARGET )
    MESSAGE: Sending STRING( ACK_0007, MOVE_TO_TARGET )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending STATUS( MOVE_TO_TARGET )
    MESSAGE: Sending TRANSFORM( CURRENT_POSITION )
    MESSAGE: Sending STRING( ACK_0008, MANUAL )
    MESSAGE: Sending STATUS( MANUAL )
    MESSAGE: Sending STRING( ACK_0009, STOP )
    MESSAGE: Sending STATUS( STOP )
    MESSAGE: Sending STRING( ACK_0010, EMERGENCY )
    MESSAGE: Sending STATUS( EMERGENCY )
    MESSAGE: Socket closed.

At the same time, you will see messages on the terminal for the NavigationTestSimulator, too.

    MESSAGE: ===== Step 1: START_UP =====
    MESSAGE: Sending STRING( CMD_0001, START_UP )
    MESSAGE: ===== Step 2: PLANNING =====
    MESSAGE: Sending STRING( CMD_0002, PLANNING )
    MESSAGE: ===== Step 3: CALIBRATION =====
    MESSAGE: Sending STRING( CMD_0003, CALIBRATION )
    MESSAGE: Sending TRANSFORM( CLB_0004 )
    MESSAGE: ===== Step 4: TARGETING =====
    MESSAGE: Sending STRING( CMD_0005, TARGETING )
    MESSAGE: Sending TRANSFORM( TGT_0006 )
    MESSAGE: ===== Step 5: MOVE_TO_TARGET =====
    MESSAGE: Sending STRING( CMD_0007, MOVE_TO_TARGET )
    MESSAGE: ===== Step 6: MANUAL =====
    MESSAGE: Sending STRING( CMD_0008, MANUAL )
    MESSAGE: ===== Step 9: STOP =====
    MESSAGE: Sending STRING( CMD_0009, STOP )
    MESSAGE: ===== Step 10: EMERGENCY =====
    MESSAGE: Sending STRING( CMD_0010, EMERGENCY )
    MESSAGE: The test has been completed successfully.


To simulate hardware (e.g. test 2 -- start-up witout connecting the device to the robot control computer), the RobotTestSimulator can activate 'defects'. For example, you can simulate device-not-ready error in START_UP phase by the following command:

    $ ./RobotTestSimulator 18944 START_UP:DNR

When the program starts, it will show the following message

    MESSAGE: Defect status:
    MESSAGE:    START_UP:DNR  :  ON
                                ^^^^


