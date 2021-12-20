/*==========================================================================

  Portions (c) Copyright 2008 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See Doc/copyright/copyright.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   ZFrame Calibration
  Module:    $HeadURL: http://svn.slicer.org/Slicer3/trunk/Modules/OpenIGTLinkIF/vtkIGTLToMRMLBase.h $
  Date:      $Date: 2009-01-05 13:28:20 -0500 (Mon, 05 Jan 2009) $
  Version:   $Revision: 8267 $

==========================================================================*/

#ifndef __Calibration_h
#define __Calibration_h

#include "ZLinAlg.h"
#include "newmatap.h"
#include "newmat.h"

namespace zf {

typedef float  Matrix4x4[4][4];

void PrintMatrix(Matrix4x4 &matrix);
void QuaternionToMatrix(float* q, Matrix4x4& m);
void MatrixToQuaternion(Matrix4x4& m, float* q);
void Cross(float *a, float *b, float *c);
void IdentityMatrix(Matrix4x4 &matrix);

class Calibration
{

public:

  // Methods related to finding the fiducial artifacts in the MR images.
  Calibration();
  ~Calibration();

public:
  int SetInputImage(short* inputImage, int dimensions[3], Matrix4x4& transform);
  int SetOrientationBase(float orentation[4]);


  // Set the verbose debugging flag and define or undefine the macro
  void SetVerbose(bool flag);
  // Get the value of the verbose debugging flag
  bool GetVerbose();

  // Burn algorithm parameters
  void SetBurnFlag(bool flag);
  int SetVoxelSize(double voxSize[3]);
  void SetHistogramMaximumBin(int maxBin);
  void SetHistogramNumberOfBins(int numBins);
  void SetBurnThresholdPercent(double percent);
  void SetSurroundPercent(double percent);
  void SetRecursionLimit(int limit);

  void SetMinFrameLocks(int min);
  void SetPeakRadius(float radius);
  void SetMaxBadPeaks(int max);
  void SetOffPeakPercent(double percent);
  void SetMinMarkerSize(double min);
  void SetMaxMarkerSize(double max);

  void GetPositionStdDev(double stdev[3]);
  void GetQuaternionStdDev(double stdev[4]);
  void SetMaxStandardDeviationPosition(double max);

  int Register(int range[2],float Zposition[3], float Zorientation[4]);

  enum RegisterReturnCodes
  {
    RegisterError = 0,
    RegisterSuccess = 1,
    RegisterSliceOutOfBounds,
    RegisterQuaternionError,
    RegisterQuaternionException,
    RegisterQuaternionBadGeometry,
    RegisterQuaternionLocateFiducials,
    RegisterNotEnoughFrameLocks,
    RegisterStandardDeviationError,
    LocateFiducialsNotSquare,
    LocateFiducialsBadPeaks,
    LocalizeFrameError,
    LocalizeFrameComputeFromRotation,
    LocalizeFrameComputeImageCrossSection,
    LocalizeFrameAngle,
    LocalizeFrameDisplacement,
  };

  /// Return strings explaining the code
  const char *RegisterReturnCodeString(int code);

protected:
  void Init(int xsize, int ysize, float xspacing, float yspacing);
  int  RegisterQuaternion(float position[3], float quaternion[4],
                          float ZquaternionBase[4],
                          Matrix& srcImage, int dimension[3], float spacing[3]);
  int LocateFiducials(Matrix &image, int xsize, int ysize,
                       int Zcoordinates[7][2], float tZcoordinates[7][2]);
  void FindSubPixelPeak(int Zcoordinate[2], float tZcoordinate[2],
                        Real Y0, Real Yx1, Real Yx2, Real Yy1, Real Yy2);
  bool CheckFiducialGeometry(int Zcoordinates[7][2], int xsize, int ysize);
  void FindFidCentre(float points[7][2], float &rmid, float &cmid);
  void FindFidCorners(float points[7][2], float *pmid);
  void OrderFidPoints(float points[7][2], float rmid, float cmid);

  // Methods related to solving for the frame pose w.r.t. the imaging plane.
 public:
  int LocalizeFrame(float Zcoordinates[7][2], Column3Vector &Zposition,
                     Quaternion &Zorientation);
 protected:

  void SolveZ(Column3Vector P1, Column3Vector P2, Column3Vector P3,
              Column3Vector Oz, Column3Vector Vz, Column3Vector &P2f);

  // Methods for finding matrix maxima.
  Real ComplexMax(Matrix &realmat, Matrix &imagmat);
  Real RealMax(Matrix &realmat);
  Real FindMax(Matrix &inmatrix, int &row, int &col);
  float CoordDistance(float *p1, float *p2);
  //ETX

  void Burn3D(short* inImage, float threshold);
  // Count the number of voxels with each label, multiply by the voxel volume, and
  // then check that the volumes of continuous labels fall within the marker size
  // range. Any volumes that fall outside these limits are labelled 0.
  // This labelmap is then used as a mask for the original image, setting voxels
  // labelled 0 in the output of the burn to 0 in the original image. This masked
  // image is passed back into the original algorithm.
  void ConvertBurn();
  // Apply a threshold filter, ThresholdPercent of the image max value.
  // Apply a surround filter on the output of the threshold, SurroundPercent
  // Do a volume burn on the binary image output of the surround filter.
  int RunBurn(float surround);
  short GetPixel(short* inImage, int i, int j, int k);
  int GetPixel(int* inImage, int i, int j, int k);
  void DoBurn(int i, int j, int k, int n, int deep);
  float GetMax(short* inImage);
  float GetMin(short* inImage);

protected:

  short *   InputImage;
  int       InputImageDim[3];
  Matrix4x4 InputImageTrans;
  float     ZOrientationBase[4];

  // Standard deviation of position calculation for each axis
  double PositionStdDev[3];
  // Standard deviation of quaternion elements
  double QuaternionStdDev[4];
  // The minimum number of slices on which to obtain a frame lock to determine that the
  // registraiton was successfull
  int       MinFrameLocks;
  // Define a block neighbourhood around the peak value, in mm, will be divided by the voxel size along x, y axes.
  float       PeakRadius;
  // Skip this slice if find too many bad peaks (peak is bad if off peak percentage check fails).
  int       MaxBadPeaks;
  // Ignore a coordinate if the off peak value, at PeakRadius, is within this percentage of the peak. 0-1
  double    OffPeakPercent;
  // Fail registration if the standard deviation of the position over the frame locked slices is larger than this value along any axis, default 10.0
  double    MaxStandardDeviationPosition;

  // Marker size range in mm^3.
  // Beekly markers are max size 1250mm^3, but should always be smaller than that.
  // Use a minimum of ~25% of that size. Max may be set higher for testing purposes.
  double MinMarkerSize;
  double MaxMarkerSize;

  //BTX
  Matrix SourceImage, MaskImage;
  Matrix IFreal, IFimag, MFreal, MFimag, zeroimag;
  Matrix PFreal, PFimag;
  Matrix PIreal, PIimag;
  //ETX

  // Flag to check if to use the burn algorithm to mask the input image or
  // not. True by default.
  bool BurnFlag;
  // The burn algorithm applies a threshold filter of this percent
  // of the image's max value, 0-1, default 0.2
  double BurnThresholdPercent;
  // The burn algorithmm applies a "surround" filter on the output of the
  // threshold filter. i.e. if voxel is at least SurroundPercent surrounded by
  // non-zero voxels in the 26 surrounding voxels (the 3x3x3 matrix centered on
  // the voxel), then keep it's value, otherwise set voxel value to 0.
  // Valid range 0.0 - 1.0, default 0.5
  double SurroundPercent;
  // To stop an overflow error occurring with the recursive nature of the burn
  // algorithm, the recursions are limited
  int RecursionLimit;
  int* BurnLabelMap;
  short* BurnedImage;
  int* LabelCount;
  int LabelCountNum;
  double VoxelSize[3];
  int HistogramMaximumBin;
  int HistogramNumberOfBins;

  // Verbose debugging on or off
  bool VerboseFlag;
};

}


#endif // __Calibration_h
