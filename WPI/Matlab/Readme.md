New State machine for BRP project. Server class is for connecting to slicer IGT interface, and Robot class is for connecting to lower level controllers.

Upon download, open matlab project first to register all folders under your local path. Open Main for testing.
Without robot hardware, you can try simulation mode. You can add host and port parameters in the contructor function for server class to change the hostname and port for IGT interface. 

Currently the IGT-Matlab are only working as client. So the auto-test function in the interface would not working properly.

To run this project, start the IGT server first. Then run the main.m scripy. The following testing steps are the same as the following video:
https://youtu.be/Ad3AOeqrEuQ

We also enabled needle retraction and stop/estop in this project.

