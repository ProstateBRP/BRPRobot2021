![Alt text](ZFrameRegistration.png)

### Overview

ZFrameRegistration is a [3D Slicer](http://slicer.org) extension designed to support the workflow of the in-bore MRI-guided therapies (see references below for [clinical context](http://ncigt.org/prostate-biopsy)). 
ZFrameRegistration was developed and tested to support transperineal MRgBx and CryoAblation procedures in the [Advanced Multimodality Image Guided Operating (AMIGO)](http://www.brighamandwomens.org/research/amigo/default.aspx) at the Brigham and Women's Hospital, Boston. Its applicability to other types of procedures has not been evaluated.
The registration of the intra-procedural image frame of reference with the transperineal biopsy or cryoablation templates.
![](Screenshots/Animation.gif)

### Usage:

### ZFrameRegistrationScripted

##### Method 1: Using module

Select input volume

Select frame type

Select Z-Frame configuration to set Frame Topology or adjust Frame Topology manually

Select Slice Range

Select Output Transform

Click Apply


##### Method 2: From interactor
```
import ZFrameRegistrationScripted
zFrameConfig = 'z001'
zFrameType = '7-fiducial' # Or '9-fiducial'
frameTopology = '[30.0, 30.0, -30.0], [-30.0, 30.0, -30.0], [-30.0, -30.0, -30.0], [0.0, -1.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]'
registrationLogic = ZFrameRegistrationScripted.ZFrameRegistrationScriptedLogic()
startSlice = 6
endSlice = 11
registrationLogic.run(inputVolumeNode, outputTransformNode, zFrameConfig, zFrameType, frameTopology, startSlice, endSlice)
```


### ZFrameRegistrationWithROI

#### With 3D slicer main window.
1. After install the extension, the user need to switch to the module `ZFrameRegistrationWithROI`.
2. Select the desired zFrame model from the list. The module provides two zFrame model options:
* original (vertical) version
* modified (horizontal) version
3. Load a nrrd file into 3D Slicer by clicking the Slicer `Add Data` button.
![Alt text](Screenshots/AddData.png?raw=true "Add Data")

4. Choose the volume in the `Zframe template volume` selector.
![Alt text](Screenshots/SelectVolume.png?raw=true "Select Volume")

5. The ROI definition will be automatically triggered if the volume is selected or changed, user needs to define ROI by clicking two points in the slice widget.
![Alt text](Screenshots/DefineROI.png?raw=true "Define ROI")

6. Press the run algorithm button, the registration will be performed and the zframe model will be shown both in the slice widgets and the 3D view widget.
![Alt text](Screenshots/RunAlgorithm.png?raw=true "Run Algorithm")

7. If the result is not good, click the "Reset" button or user the manual start/end indexes. If the "Reset" button is clicked, the user will be prompt to do the ROI definition as in step 3.
   Afterwards, press the run algorithm button again.
![Alt text](Screenshots/Retry.png?raw=true "Retry") ![Alt text](Screenshots/RetryManualIndexes.png?raw=true "RetryManualIndexes")

8. When the result looks good, the zframe will align very well with the fiducial artifacts on the slice widgets and the 3D view window.
![Alt text](Screenshots/Validation.png?raw=true "Validation")

#### Slicelet mode
The user have the option to run the module in a slicelet mode
Type the following command in a terminal in Linux or Mac OS system.
~~~~
$ cd ${Slicer_execution_path}
$ ./Slicer --no-main-window --python-script lib/Slicer-x.x/qt-scripted-modules/ZFrameRegistrationWithROI.py
~~~~
![Alt text](Screenshots/Slicelet.png?raw=true "Slicelet")
For Windows system, see the link for more information [Slicelet Mode](https://www.slicer.org/wiki/Documentation/Nightly/Developers/Slicelets)
### Disclaimer

ZFrameRegistration, same as 3D Slicer, is a research software. **ZFrameRegistration is NOT an FDA-approved medical device**. It is not intended for clinical use. The user assumes full responsibility to comply with the appropriate regulations.  

### Support

Please feel free to contact us for questions, feedback, suggestions, bugs, or you can create issues in the issue tracker: https://github.com/leochan2009/SlicerZframeRegistration/issues

* [Junichi Tokuda](https://github.com/tokjun) tokuda@bwh.harvard.edu

* [Longquan Chen](https://github.com/leochan2009) lchen@bwh.harvard.edu

* [Christian Herz](https://github.com/che85) cherz@bwh.harvard.edu

* [Andrey Fedorov](https://github.com/fedorov) fedorov@bwh.harvard.edu

### Acknowledgments

Development of ZFrameRegistration is supported in part by the following NIH grants: 
* R01 EB020667 OpenIGTLink: a network communication interface for closed-loop image-guided interventions
* R01 CA111288 Enabling Technologies for MRI-guided prostate interventions
* P41 EB015898 National Center for Image Guided Therapy (NCIGT), http://ncigt.org

The source code was adopted from the open source projects
as follows:
* [ProstateNav module of 3D Slicer version
  3](https://www.slicer.org/slicerWiki/index.php/Modules:ProstateNav-Documentation-3.6) (see source
  code [here](https://github.com/SlicerProstate/ProstateNav), no revision
  history); although we
  do not have the precise record of contribution to that functionality in the
  ProstateNav module, we believe main contributors were Junichi Tokuda and
  Simon Di Maio (while at BWH, now at [Intuitive
  Surgical](http://www.intuitivesurgical.com/))
* [SliceTracker](https://github.com/SlicerProstate/SliceTracker), courtesy Christian Herz
  @che85  

### References

The following publications led to the development of ZFrameRegistration.
1. Tokuda J., Tuncali K., Iordachita I., Song S-EE., Fedorov A., Oguro S., Lasso A., Fennessy FM., Tempany CM., Hata N. 2012. In-bore setup and software for 3T MRI-guided transperineal prostate biopsy. Physics in medicine and biology 57:5823–5840. DOI: [10.1088/0031-9155/57/18/5823](http://doi.org/10.1088/0031-9155/57/18/5823): **procedure technical setup**.
2. DiMaio S, Samset E, Fischer G, Iordachita I, Fichtinger G, Jolesz F, et al. Dynamic MRI scan plane control for passive tracking of instruments and devices. MICCAI. 2007;10:50–8.
