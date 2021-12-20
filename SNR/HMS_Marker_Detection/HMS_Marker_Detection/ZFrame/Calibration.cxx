/*==========================================================================

  Portions (c) Copyright 2008 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See Doc/copyright/copyright.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   ZFrame Calibration
  Module:    $HeadURL: http://svn.slicer.org/Slicer3/trunk/Modules/OpenIGTLinkIF/vtkIGTLToMRMLBase.h $
  Date:      $Date: 2009-01-05 13:28:20 -0500 (Mon, 05 Jan 2009) $
  Version:   $Revision: 8267 $

==========================================================================*/

#include <string.h>
#include <sstream>
#include <fstream>
#include <vector>

#include "Calibration.h"

#define MEPSILON        (1e-10)
#ifndef M_PI
#define M_PI 3.14159
#endif


namespace zf {


void PrintMatrix(Matrix4x4 &matrix)
{
  std::cout << "=============" << std::endl;
  std::cout << matrix[0][0] << ", " << matrix[0][1] << ", " << matrix[0][2] << ", " << matrix[0][3] << std::endl;
  std::cout << matrix[1][0] << ", " << matrix[1][1] << ", " << matrix[1][2] << ", " << matrix[1][3] << std::endl;
  std::cout << matrix[2][0] << ", " << matrix[2][1] << ", " << matrix[2][2] << ", " << matrix[2][3] << std::endl;
  std::cout << matrix[3][0] << ", " << matrix[3][1] << ", " << matrix[3][2] << ", " << matrix[3][3] << std::endl;
  std::cout << "=============" << std::endl;
}

void QuaternionToMatrix(float* q, Matrix4x4& m)
{

  // normalize
  float mod = sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);

  // convert to the matrix
  const float x = q[0] / mod;
  const float y = q[1] / mod;
  const float z = q[2] / mod;
  const float w = q[3] / mod;

  const float xx = x * x * 2.0;
  const float xy = x * y * 2.0;
  const float xz = x * z * 2.0;
  const float xw = x * w * 2.0;
  const float yy = y * y * 2.0;
  const float yz = y * z * 2.0;
  const float yw = y * w * 2.0;
  const float zz = z * z * 2.0;
  const float zw = z * w * 2.0;

  m[0][0] = 1.0 - (yy + zz);
  m[1][0] = xy + zw;
  m[2][0] = xz - yw;

  m[0][1] = xy - zw;
  m[1][1] = 1.0 - (xx + zz);
  m[2][1] = yz + xw;

  m[0][2] = xz + yw;
  m[1][2] = yz - xw;
  m[2][2] = 1.0 - (xx + yy);

  m[3][0] = 0.0;
  m[3][1] = 0.0;
  m[3][2] = 0.0;
  m[3][3] = 1.0;

  m[0][3] = 0.0;
  m[1][3] = 0.0;
  m[2][3] = 0.0;

}


void MatrixToQuaternion(Matrix4x4& m, float* q)
{
  float trace = m[0][0] + m[1][1] + m[2][2];

  if( trace > 0.0 ) {

    float s = 0.5f / sqrt(trace + 1.0f);

    q[3] = 0.25f / s;
    q[0] = ( m[2][1] - m[1][2] ) * s;
    q[1] = ( m[0][2] - m[2][0] ) * s;
    q[2] = ( m[1][0] - m[0][1] ) * s;

  } else {

    if ( m[0][0] > m[1][1] && m[0][0] > m[2][2] ) {

      float s = 2.0f * sqrt( 1.0f + m[0][0] - m[1][1] - m[2][2]);

      q[3] = (m[2][1] - m[1][2] ) / s;
      q[0] = 0.25f * s;
      q[1] = (m[0][1] + m[1][0] ) / s;
      q[2] = (m[0][2] + m[2][0] ) / s;

    } else if (m[1][1] > m[2][2]) {

      float s = 2.0f * sqrt( 1.0f + m[1][1] - m[0][0] - m[2][2]);

      q[3] = (m[0][2] - m[2][0] ) / s;
      q[0] = (m[0][1] + m[1][0] ) / s;
      q[1] = 0.25f * s;
      q[2] = (m[1][2] + m[2][1] ) / s;

    } else {

      float s = 2.0f * sqrt( 1.0f + m[2][2] - m[0][0] - m[1][1] );

      q[3] = (m[1][0] - m[0][1] ) / s;
      q[0] = (m[0][2] + m[2][0] ) / s;
      q[1] = (m[1][2] + m[2][1] ) / s;
      q[2] = 0.25f * s;

    }
  }
}



void Cross(float *a, float *b, float *c)
{
    a[0] = b[1]*c[2] - c[1]*b[2];
    a[1] = c[0]*b[2] - b[0]*c[2];
    a[2] = b[0]*c[1] - c[0]*b[1];
}


void IdentityMatrix(Matrix4x4 &matrix)
{
  matrix[0][0] = 1.0;
  matrix[1][0] = 0.0;
  matrix[2][0] = 0.0;
  matrix[3][0] = 0.0;

  matrix[0][1] = 0.0;
  matrix[1][1] = 1.0;
  matrix[2][1] = 0.0;
  matrix[3][1] = 0.0;

  matrix[0][2] = 0.0;
  matrix[1][2] = 0.0;
  matrix[2][2] = 1.0;
  matrix[3][2] = 0.0;

  matrix[0][3] = 0.0;
  matrix[1][3] = 0.0;
  matrix[2][3] = 0.0;
  matrix[3][3] = 1.0;
}


//----------------------------------------------------------------------------
Calibration::Calibration()
{
  this->InputImage = NULL;
  IdentityMatrix(this->InputImageTrans);
  for (int i = 0; i < 3; i ++)
    {
    this->InputImageDim[i] = 0;
    this->PositionStdDev[i] = 0.0;
    this->QuaternionStdDev[i] = 0.0;
    }
  this->QuaternionStdDev[3] = 0.0;

  this->MinFrameLocks = 2;
  this->PeakRadius = 16.0;
  this->MaxBadPeaks = 5;
  this->OffPeakPercent = 0.7;
  this->MaxStandardDeviationPosition = 10.0;

  this->MinMarkerSize = 315.0;
  this->MaxMarkerSize = 3000.0;

  // Burn algorithm settings
  this->VoxelSize[0] = 1.0;
  this->VoxelSize[1] = 1.0;
  this->VoxelSize[2] = 1.0;
  this->BurnFlag = true;
  this->BurnLabelMap = NULL;
  this->BurnedImage = NULL;
  this->LabelCount = NULL;
  this->LabelCountNum = 0;
  // Set threshold value 20% between highest frequency value and max value
  this->BurnThresholdPercent = 0.2;
  // Set the percentage of non zero voxels surrounding a voxel in order to keep it
  this->SurroundPercent = 0.5;
  // Limit the recursion level
  this->RecursionLimit = 5000;

  this->VerboseFlag = false;
}


Calibration::~Calibration()
{
}


int Calibration::SetInputImage(short* inputImage, int dimensions[3], Matrix4x4& transform)
{

  this->InputImage = inputImage;
  memcpy(this->InputImageDim, dimensions, sizeof(int)*3);
  memcpy(this->InputImageTrans, transform, sizeof(Matrix4x4));

  return 1;
}

void Calibration::SetBurnFlag(bool flag)
{
  this->BurnFlag = flag;
}

int Calibration::SetVoxelSize(double inVox[3])
{
  if (this->VerboseFlag)
  {
  std::cerr << "SetVoxelSize: "
    << inVox[0] << ", " << inVox[1] << ", " << inVox[2]
    << std::endl;
  }
  for (int i = 0; i < 3; ++i)
    {
      if (inVox[i] > 0.0)
	{
	this->VoxelSize[i] = inVox[i];
	}
      else
	{
	this->VoxelSize[i] = 1.0;
	}
    }
  return 1;
}


int Calibration::SetOrientationBase(float orientation[4])
{
  memcpy (this->ZOrientationBase, orientation, sizeof (float) * 4);
  return 1;
}

void Calibration::GetPositionStdDev(double stdev[3])
{
  for (int i = 0; i < 3; ++i)
    {
      stdev[i] = this->PositionStdDev[i];
    }
}
void Calibration::GetQuaternionStdDev(double stdev[4])
{
    for (int i = 0; i < 4; ++i)
    {
      stdev[i] = this->QuaternionStdDev[i];
    }
}
void Calibration::SetMinFrameLocks(int min)
{
  if (min < 1)
    {
      this->MinFrameLocks = 1;
    }
  else
    {
      this->MinFrameLocks = min;
    }
}

void Calibration::SetPeakRadius(float radius)
{
  if (radius > 0.0)
    {
      this->PeakRadius = radius;
    }
  else
    {
      this->PeakRadius = 1;
    }
}

void Calibration::SetMaxBadPeaks(int max)
{
  if (max < 0)
    {
      this->MaxBadPeaks = 0;
    }
  else
    {
      this->MaxBadPeaks = max;
    }
}

void Calibration::SetOffPeakPercent(double percent)
{
  if (percent < 0.0)
    {
      this->OffPeakPercent = 0.0;
    }
  else if (percent > 1.0)
    {
      this->OffPeakPercent = 1.0;
    }
  else
    {
      this->OffPeakPercent = percent;
    }
}

void Calibration::SetMaxStandardDeviationPosition(double max)
{
  if (max < 0.0)
    {
      this->MaxStandardDeviationPosition = 0.0;
    }
  else
    {
      this->MaxStandardDeviationPosition = max;
    }
}


void Calibration::SetMinMarkerSize(double min)
{
  if (min < 0.0)
    {
      this->MinMarkerSize = 0.0;
    }
  else
    {
      this->MinMarkerSize = min;
    }
}

void Calibration::SetMaxMarkerSize(double max)
{
  if (max < 0.0)
    {
      this->MaxMarkerSize = 0.0;
    }
  else
    {
      this->MaxMarkerSize = max;
    }
}

void Calibration::SetBurnThresholdPercent(double percent)
{
  if (percent < 0.0)
    {
      this->BurnThresholdPercent = 0.0;
    }
  else if (percent > 1.0)
    {
      this->BurnThresholdPercent = 1.0;
    }
  else
    {
      this->BurnThresholdPercent = percent;
    }
}

void Calibration::SetSurroundPercent(double percent)
{
  if (percent < 0.0)
    {
      this->SurroundPercent = 0.0;
    }
  else if (percent > 1.0)
    {
      this->SurroundPercent = 1.0;
    }
  else
    {
      this->SurroundPercent = percent;
    }
}

void Calibration::SetRecursionLimit(int limit)
{
  if (limit < 0)
    {
      this->RecursionLimit = 0;
    }
  else
    {
      this->RecursionLimit = limit;
    }
}

int Calibration::Register(int range[2], float Zposition[3], float Zorientation[4])
{
  if (this->BurnFlag)
    {
    //find the pixel value of the highest frequency from histogram (should be the background)
    float maxIntensity = this->GetMax(InputImage);
    float minIntensity = this->GetMin(InputImage);
    float maxFreqValue = (maxIntensity - minIntensity)*this->HistogramMaximumBin / this->HistogramNumberOfBins;
    float thresh = maxFreqValue + (maxIntensity - maxFreqValue) * this->BurnThresholdPercent;
    this->Burn3D(this->InputImage, thresh);
    this->ConvertBurn();
    }

  int xsize = this->InputImageDim[0];
  int ysize = this->InputImageDim[1];
  int zsize = this->InputImageDim[2];
    
  if (this->VerboseFlag)
  {
    std::cerr << "=== Image Size (x,y,z): " << xsize << ", " << ysize << ", " << zsize << "===" << std::endl;
  }

  // Image matrix
  float tx = this->InputImageTrans[0][0];
  float ty = this->InputImageTrans[1][0];
  float tz = this->InputImageTrans[2][0];
  float sx = this->InputImageTrans[0][1];
  float sy = this->InputImageTrans[1][1];
  float sz = this->InputImageTrans[2][1];
  float nx = this->InputImageTrans[0][2];
  float ny = this->InputImageTrans[1][2];
  float nz = this->InputImageTrans[2][2];
  float px = this->InputImageTrans[0][3];
  float py = this->InputImageTrans[1][3];
  float pz = this->InputImageTrans[2][3];

  // normalize
  float psi = sqrt(tx*tx + ty*ty + tz*tz);
  float psj = sqrt(sx*sx + sy*sy + sz*sz);
  float psk = sqrt(nx*nx + ny*ny + nz*nz);
  float ntx = tx / psi;
  float nty = ty / psi;
  float ntz = tz / psi;
  float nsx = sx / psj;
  float nsy = sy / psj;
  float nsz = sz / psj;
  float nnx = nx / psk;
  float nny = ny / psk;
  float nnz = nz / psk;

  // Here we calculate 'average' quaternion from registration results from
  // multiple slices. The average quaternion here is defined as the eigenvector
  // corresponding to the largest eigenvalue of the sample moment of inertia
  // matrix given as:
  //            ____
  //         1  \   |
  //    T = ---  |     qi qi'
  //         n  /___|
  //              i

  int numFrameLocks = 0;
  SymmetricMatrix T;
  T.ReSize(4);
  float P[3]={0,0,0};
  for (int i = 0; i < 4; i ++)
    for (int j = 0; j < 4; j ++)
      T.element(i, j) = 0.0;

  float position[3];
  float quaternion[4];
  typedef std::vector<float> CoordType;
  typedef std::vector<CoordType> PointsType;
  PointsType positions;
  PointsType quaternions;

  zf::Matrix4x4 matrix;
  matrix[0][0] = ntx;
  matrix[1][0] = nty;
  matrix[2][0] = ntz;
  matrix[0][1] = nsx;
  matrix[1][1] = nsy;
  matrix[2][1] = nsz;
  matrix[0][2] = nnx;
  matrix[1][2] = nny;
  matrix[2][2] = nnz;

  int lastSliceError = RegisterSuccess;
  for (int slindex = range[0]; slindex < range[1]; slindex ++)
    {
    
    if (this->VerboseFlag)
      {
      std::cerr << "=== Current Slice Index: " << slindex << "===" << std::endl;
      std::cerr << "\tPrevious slices with frame lock: " << numFrameLocks << std::endl;
      }
        
    // Shift the center
    // NOTE: The center of the image should be shifted due to different
    // definitions of image origin between VTK (Slicer) and OpenIGTLink;
    // OpenIGTLink image has its origin at the center, while VTK image
    // has one at the corner.

    float hfovi = psi * (this->InputImageDim[0]-1) / 2.0;
    float hfovj = psj * (this->InputImageDim[1]-1) / 2.0;
    //float hfovk = psk * (this->InputIMageDim[2]-1) / 2.0;

    // For slice (k) direction, we calculate slice offset based on
    // the slice index.
    float offsetk = psk * slindex;

    float cx = ntx * hfovi + nsx * hfovj + nnx * offsetk;
    float cy = nty * hfovi + nsy * hfovj + nny * offsetk;
    float cz = ntz * hfovi + nsz * hfovj + nnz * offsetk;

    // position and quaternion will be overwritten by ZFrameRegistrationQuaternion()
    zf::MatrixToQuaternion(matrix, quaternion);

    position[0] = px + cx;
    position[1] = py + cy;
    position[2] = pz + cz;

    if (this->VerboseFlag)
      {
      std::cerr << "=== Image position ===" << std::endl;
      std::cerr << "x = " << position[0] << std::endl;
      std::cerr << "y = " << position[1] << std::endl;
      std::cerr << "z = " << position[2] << std::endl;
      }

    short * currentSlice;
    if (slindex >= 0 && slindex < zsize)
      {
      currentSlice = &(this->InputImage[xsize*ysize*slindex]);
      }
    else
      {
      return RegisterSliceOutOfBounds;
      }

    if (this->VerboseFlag)
      {
      std::cerr << "\n\n\nSlice = " << slindex << std::endl;
      }
    // Transfer image to a Matrix.
    SourceImage.ReSize(xsize,ysize);

    for(int i=0; i<xsize; i++)
      for(int j=0; j<ysize; j++)
        SourceImage.element(i,j) = currentSlice[j*xsize+i];

    // if Z-frame position is determined from the slice
    float spacing[3];
    spacing[0] = psi;
    spacing[1] = psj;
    spacing[2] = psk;
    if (this->VerboseFlag)
      {
      std::cerr << "SPACING:: " << psi << ", " << "psj" << std::endl;
      }
    Init(xsize, ysize, spacing[0], spacing[1]);

    try
      {
	int registered = RegisterQuaternion(position, quaternion, this->ZOrientationBase,
					    SourceImage, this->InputImageDim, spacing);
	if (registered == RegisterSuccess)
	  {
	    P[0] += position[0];
	    P[1] += position[1];
	    P[2] += position[2];
	    // save for further calculation
	    CoordType pos(3);
	    pos[0] = position[0];
	    pos[1] = position[1];
	    pos[2] = position[2];
	    positions.push_back(pos);
	    CoordType quat(4);
	    quat[0] = quaternion[0];
	    quat[1] = quaternion[1];
	    quat[2] = quaternion[2];
	    quat[3] = quaternion[3];
	    quaternions.push_back(quat);
	    if (this->VerboseFlag)
	      {
	      std::cerr << "position # " << positions.size()
			<< " = ("
			<< position[0] << ", "
			<< position[1] << ", "
			<< position[2] << ")" << std::endl;
	      }

	    // Note that T is defined as SymmetricMatrix class
	    // and upper triangular part is updated.
	    T.element(0, 0) = T.element(0, 0) + quaternion[0]*quaternion[0];
	    T.element(0, 1) = T.element(0, 1) + quaternion[0]*quaternion[1];
	    T.element(0, 2) = T.element(0, 2) + quaternion[0]*quaternion[2];
	    T.element(0, 3) = T.element(0, 3) + quaternion[0]*quaternion[3];
	    T.element(1, 1) = T.element(1, 1) + quaternion[1]*quaternion[1];
	    T.element(1, 2) = T.element(1, 2) + quaternion[1]*quaternion[2];
	    T.element(1, 3) = T.element(1, 3) + quaternion[1]*quaternion[3];
	    T.element(2, 2) = T.element(2, 2) + quaternion[2]*quaternion[2];
	    T.element(2, 3) = T.element(2, 3) + quaternion[2]*quaternion[3];
	    T.element(3, 3) = T.element(3, 3) + quaternion[3]*quaternion[3];
	    numFrameLocks++;

	    if (this->VerboseFlag)
	      {
	      std::cerr << "quaternion = ("
			<< quaternion[0] << ", "
			<< quaternion[1] << ", "
			<< quaternion[2] << ", "
			<< quaternion[3] << ")" << std::endl;
	      }
	  }
	else
	  {
	    // TODO: collect reasons why failed on slices
	    lastSliceError = registered;
#ifdef DEBUG_ZFRAME_REGISTRATION
	    std::cerr << "Failed to register quaternion. Returned " << registered
		      << ": "
		      << RegisterReturnCodeString(registered)
		      << std::endl;
#endif // DEBUG_ZFRAME_REGISTRATION
	  }
      }
    catch (const std::exception& err)
      {
	if (this->VerboseFlag)
	  {
	  std::cerr << "Failed to register quaternion: " << err.what() << std::endl;
	  }
	return RegisterQuaternionError;
      }
    catch (...)
      {
	if (this->VerboseFlag)
	  {
	  std::cerr << "Failed to register quaternion. Unknown exception." << std::endl;
	  }
	return RegisterQuaternionException;
      }
    }

  // require lock on a minimum number of slices
  if (numFrameLocks < this->MinFrameLocks)
    {
    if (this->VerboseFlag)
      {
        std::cerr << "Failed to detect the frame on at least "
        << this->MinFrameLocks << " slices, found it on "
        << numFrameLocks << std::endl;
      }
    if (lastSliceError != RegisterSuccess)
      {
	// not enough frame locks is too general, return a lower level error code
	return lastSliceError;
      }
    else
      {
      return RegisterNotEnoughFrameLocks;
      }
    }
  else
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Detected the frame on " << numFrameLocks << " slices." << std::endl;
      }
    }

  float fn = (float) numFrameLocks;
  for (int i = 0; i < 3; i ++)
    {
    P[i] /= fn;
    }
  // calculate standard deviation on the position
  double position_square_sum[3] = {0,0,0};
  for (int i = 0; i < positions.size(); ++i)
    {
      CoordType pos = positions[i];
      if (this->VerboseFlag)
	{
        std::cerr << i << ": " << pos[0] << ", " << pos[1] << ", " << pos[2] << std::endl;
	}
      for (int a = 0; a < 3; ++a)
	{
	position_square_sum[a] = position_square_sum[a] + (pos[a] - P[a])*(pos[a] - P[a]);
	}
    }
  for (int i = 0; i < 3; ++i)
    {
    double squared_stdev = (position_square_sum[i] / positions.size());
    this->PositionStdDev[i] = std::sqrt(squared_stdev);
    if (this->VerboseFlag)
      {
      std::cerr << i << " square sum = " << position_square_sum[i]
		<< ", positions size = " << positions.size()
		<< ", mean = " << P[i]
		<< ", squared_stdev = " << squared_stdev
		<< std::endl;
      }
    }

  // calculate standard deviation on the quaternions
  double quaternion_square_sum[4] = {0,0,0,0};
  for (int i = 0; i < quaternions.size(); ++i)
    {
      CoordType quat = quaternions[i];
      if (this->VerboseFlag)
	{
        std::cerr << i << ": " << quat[0] << ", " << quat[1] << ", " << quat[2] << ", " << quat[3] << std::endl;
	}
      for (int a = 0; a < 4; ++a)
	{
	quaternion_square_sum[a] = quaternion_square_sum[a] + (quat[a] - quaternion[a])*(quat[a] - quaternion[a]);
	}
    }
  for (int i = 0; i < 4; ++i)
    {
      double squared_stdev = (quaternion_square_sum[i] / quaternions.size());
      this->QuaternionStdDev[i] = std::sqrt(squared_stdev);
      if (this->VerboseFlag)
	{
        std::cerr << i << " square sum = " << quaternion_square_sum[i]
		  << ", quaternions size = " << quaternions.size()
		  << ", mean = " << quaternion[i]
		  << ", squared_stdev = " << squared_stdev
		  << std::endl;
	}
    }

  T.element(0, 0) = T.element(0, 0) / fn;
  T.element(0, 1) = T.element(0, 1) / fn;
  T.element(0, 2) = T.element(0, 2) / fn;
  T.element(0, 3) = T.element(0, 3) / fn;

  T.element(1, 1) = T.element(1, 1) / fn;
  T.element(1, 2) = T.element(1, 2) / fn;
  T.element(1, 3) = T.element(1, 3) / fn;

  T.element(2, 2) = T.element(2, 2) / fn;
  T.element(2, 3) = T.element(2, 3) / fn;
  T.element(3, 3) = T.element(3, 3) / fn;


  // calculate eigenvalues of T matrix
  DiagonalMatrix D;
  Matrix V;
  D.ReSize(4);
  V.ReSize(4, 4);
  eigenvalues(T, D, V);

  if (this->VerboseFlag)
    {
    for (int i = 0; i < 4; i ++)
      {
      std::cerr << "T[" << i << ", 0] = ("
		<<  T.element(i, 0) << ", "
		<<  T.element(i, 1) << ", "
		<<  T.element(i, 2) << ", "
		<<  T.element(i, 3) << ")" << std::endl;
      }

//  std::cerr << "D[" << i << ", 0] = ("
//            <<  D.element(0) << ", "
//            <<  D.element(1) << ", "
//            <<  D.element(2) << ", "
//            <<  D.element(3) << ")" << std::endl;

    for (int i = 0; i < 4; i ++)
      {
      std::cerr << "V[" << i << ", 0] = ("
		<<  V.element(i, 0) << ", "
		<<  V.element(i, 1) << ", "
		<<  V.element(i, 2) << ", "
		<<  V.element(i, 3) << ")" << std::endl;
      }
    }

  // find the maximum eigen value
  int maxi = 0;
  float maxv = D.element(0);
  for (int i = 1; i < 4; i ++)
    {
    if (D.element(i) > maxv)
      {
      maxi = i;
      }
    }

  // Substitute 'average' position and quaternion.
  Zposition[0] = P[0];
  Zposition[1] = P[1];
  Zposition[2] = P[2];
  Zorientation[0] = V.element(0, maxi);
  Zorientation[1] = V.element(1, maxi);
  Zorientation[2] = V.element(2, maxi);
  Zorientation[3] = V.element(3, maxi);

  if (this->VerboseFlag)
    {
    std::cerr << "average position = ("
	      << Zposition[0] << ", "
	      << Zposition[1] << ", "
	      << Zposition[2] << ")" << std::endl;
    std::cerr << "\tstdev = ("
	      << this->PositionStdDev[0] << ", "
	      << this->PositionStdDev[1] << ", "
	      << this->PositionStdDev[2] << ")"
	      << std::endl;

    std::cerr << "average orientation = ("
	      << Zorientation[0] << ", "
	      << Zorientation[1] << ", "
	      << Zorientation[2] << ", "
	      << Zorientation[3] << ")" << std::endl;
    std::cerr << "\tstdev = ("
	      << this->QuaternionStdDev[0] << ", "
	      << this->QuaternionStdDev[1] << ", "
	      << this->QuaternionStdDev[2] << ", "
	      << this->QuaternionStdDev[3] << ")"
	      << std::endl;
    }

  // fail if the position standard deviation is too large
  if (this->PositionStdDev[0] > this->MaxStandardDeviationPosition ||
      this->PositionStdDev[1] > this->MaxStandardDeviationPosition ||
      this->PositionStdDev[2] > this->MaxStandardDeviationPosition)
    {
      std::cerr << "Failed: standard deviation of the registered position is > "
		<< this->MaxStandardDeviationPosition << " on at least one axis: "
		<< this->PositionStdDev[0] << ", "
		<< this->PositionStdDev[1] << ", "
		<< this->PositionStdDev[2]
		<< std::endl;
      return RegisterStandardDeviationError;
    }
  return RegisterSuccess;

}


void Calibration::Init(int xsize, int ysize, float xspacing, float yspacing)
{
  int i,j,m,n;

  // Markers are ~10mm diameter
  int kernelX = int(round(10.0 / xspacing));
  int kernelY = int(round(10.0 / yspacing));
  if (kernelX % 2 == 0){ // kernelX must be odd
	  kernelX++;
  }
  if (kernelY % 2 == 0){ // kernelY must be odd
	  kernelY++;
  }
  Real kernel[11][11] = { { 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0 },
  { 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0 },
  { 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0 },
  { 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0 },
  { 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5 },
  { 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5 },
  { 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5 },
  { 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0 },
  { 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0 },
  { 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0 },
  { 0.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0 } };

  Matrix sizedKernel;
  sizedKernel.ReSize(kernelX, kernelY);
  //assuming spacing <= 1mm i.e. kernelX >= 11

  for (int i = 0; i < kernelX; i++)
  {
    for (int j = 0; j < kernelY; j++)
      {
	float istart = float(i) / float(kernelX) * 11;
	float iend = float(i + 1) / float(kernelX) * 11;
	float jstart = float(j) / float(kernelY) * 11;
	float jend = float(j + 1) / float(kernelY) * 11;
	int istart_floor = int(floor(istart));
	int iend_floor = int(floor(iend));
	int jstart_floor = int(floor(jstart));
	int jend_floor = int(floor(jend));
	if (istart_floor == iend_floor)
	  {
	  if (jstart_floor == jend_floor)
	    {
	    sizedKernel.element(i,j) = kernel[istart_floor][jstart_floor];
	    }
	  else
	    {
	      sizedKernel.element(i, j) = kernel[istart_floor][jstart_floor] * (jend_floor - jstart)/(jend-jstart);
	      sizedKernel.element(i, j) += kernel[istart_floor][jstart_floor + 1] * (jend - jend_floor) / (jend - jstart);
	    }
	  }
	else
	  {
	    if (jstart_floor == jend_floor)
	      {
		sizedKernel.element(i, j) = kernel[istart_floor][jstart_floor] * (iend_floor - istart) / (iend - istart);
		sizedKernel.element(i, j) += kernel[istart_floor + 1][jstart_floor] * (iend - iend_floor) / (iend - istart);
	      }
	    else
	      {
		sizedKernel.element(i, j) = kernel[istart_floor][jstart_floor] * (float(iend_floor) - istart)*(float(jend_floor) - jstart) / (jend - jstart) / (iend - istart);
		sizedKernel.element(i, j) += kernel[istart_floor + 1][jstart_floor] * (iend - float(iend_floor))*(float(jend_floor) - jstart) / (jend - jstart) / (iend - istart);
		sizedKernel.element(i, j) += kernel[istart_floor][jstart_floor + 1] * (float(iend_floor) - istart)*(jend - float(jend_floor)) / (jend - jstart) / (iend - istart);
		sizedKernel.element(i, j) += kernel[istart_floor + 1][jstart_floor + 1] * (iend - float(iend_floor))*(jend - float(jend_floor)) / (jend - jstart) / (iend - istart);
	      }
	  }
      }
  }


  // Create a mask image and initialize elements to zero.
  // The Matrix class is implemented in the newmat library:
  // see: http://www.robertnz.net/
  MaskImage.ReSize(xsize,ysize);
  for(i=0; i<xsize; i++)
    for(j=0; j<ysize; j++)
        MaskImage.element(i,j) = 0;

  // Copy the correlation kernel to the centre of the mask image.
  for (i = ((xsize / 2) - (kernelX - 1) / 2), m = 0; i <= ((xsize / 2) + (kernelX - 1) / 2); i++, m++)
    {
      for (j = ((ysize / 2) - (kernelY - 1) / 2), n = 0; j <= ((ysize / 2) + (kernelY - 1) / 2); j++, n++)
	{
	  MaskImage.element(i, j) = sizedKernel.element(m, n);
	}
    }

  // Correlation will be computed using spatial convolution, and hence
  // multiplication in the frequency domain. This dramatically accelerates
  // fiducial detection. Transform mask to frequency domain; this only
  // has to be done once.
  // Before transforming the mask to the spatial frequency domain, need to
  // create an empty imaginary component, since the mask is real-valued.
  zeroimag.ReSize(xsize,ysize);
  for(i=0; i<xsize; i++)
    for(j=0; j<ysize; j++)
        zeroimag.element(i,j) = 0;

  // The Radix-2 FFT algorithm is implemented in the newmat library:
  // see: http://www.robertnz.net/
  FFT2(MaskImage, zeroimag, MFreal, MFimag);

  // Conjugate and normalize the mask.
  MFimag *= -1;
  Real maxabsolute = ComplexMax(MFreal, MFimag);
  MFreal *= (1/maxabsolute);
  MFimag *= (1/maxabsolute);

  // MFreal and MFimag now contain the real and imaginary matrix elements for
  // the frequency domain representation of the correlation mask.

}


int Calibration::RegisterQuaternion(float position[3], float quaternion[4],
                                                    float ZquaternionBase[4],
                                                    Matrix& SourceImage, int dimension[3], float spacing[3])
{

  Column3Vector Zposition;
  Quaternion    Zorientation;
  Quaternion    ZorientationBase;
  static Column3Vector Iposition;
  static Quaternion Iorientation;
  int           Zcoordinates[7][2];
  float         tZcoordinates[7][2];
  bool          frame_lock;

  // Get current position and orientation of the imaging plane.
  Iposition.setX( position[0] );
  Iposition.setY( position[1] );
  Iposition.setZ( position[2] );

  Iorientation.setX( quaternion[0] );
  Iorientation.setY( quaternion[1] );
  Iorientation.setZ( quaternion[2] );
  Iorientation.setW( quaternion[3] );

  ZorientationBase.setX( ZquaternionBase[0] );
  ZorientationBase.setY( ZquaternionBase[1] );
  ZorientationBase.setZ( ZquaternionBase[2] );
  ZorientationBase.setW( ZquaternionBase[3] );

  // Find the 7 Z-frame fiducial intercept artifacts in the image.
  if (this->VerboseFlag)
    {
    std::cerr << "ZTrackerTransform - Searching fiducials..." << std::endl;
    }
  try
    {
      int located = LocateFiducials(SourceImage, dimension[0], dimension[1], Zcoordinates, tZcoordinates);
      if (located != RegisterSuccess)
	{
	  if (this->VerboseFlag)
	    {
	    std::cerr << "Calibration::RegisterQuaternion - Fiducials not detected. No frame lock on this image.\n" << std::endl;
	    }
	  frame_lock = false;
	  return located;
	}
      else frame_lock = true;

      // Check that the fiducial geometry makes sense.
      if (this->VerboseFlag)
	{
        std::cerr << "RegisterQuaternion - Checking the fiducial geometries..." << std::endl;
	}
      try
	{
        if(CheckFiducialGeometry(Zcoordinates, dimension[0], dimension[1]) == true)
          {
          frame_lock = true;
          }
        else
          {
          frame_lock = false;
          if (this->VerboseFlag)
            {
            std::cerr << "RegisterQuaternion - Bad fiducial geometry. No frame lock on this image." << std::endl;
            }
          return RegisterQuaternionBadGeometry;;
          }
        }
      catch (const std::exception& err)
	{
	if (this->VerboseFlag)
	  {
	  std::cerr << "Failed to check fiducial geometry: " << err.what() << std::endl;
	  }
        return RegisterQuaternionBadGeometry;
	}
    }
  catch (const std::exception& err)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Failed to locate fiducials: " << err.what() << std::endl;
      }
      return RegisterQuaternionLocateFiducials;
    }
  catch (...)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Failed to locate fiducials, unknown error." << std::endl;
      }
      return RegisterQuaternionLocateFiducials;
    }

  // Compute the pose of the Z-frame only if we have a lock on the fiducial points.
  if(frame_lock)
    {
    // Transform pixel coordinates into spatial coordinates.
    // 1) Put the image origin at the centre of the image,
    // 2) Scale by pixel size.
    // 3) Re-align axes according to the IJK convention,
    for(int i=0; i<7; i++)
      {
      // 1) Put the image origin at the center
      tZcoordinates[i][0] = (float)(tZcoordinates[i][0]) - (float)(dimension[0]/2);
      tZcoordinates[i][1] = (float)(tZcoordinates[i][1]) - (float)(dimension[1]/2);

      // 2) Scale coordinates by pixel size
      tZcoordinates[i][0] *= spacing[0];
      tZcoordinates[i][1] *= spacing[1];
      }

    // Compute relative pose between the Z-frame and the current image.
    try
      {
	int localized = LocalizeFrame(tZcoordinates, Zposition, Zorientation);
	if (localized != RegisterSuccess)
	  {
	  frame_lock = 0;
	  if (this->VerboseFlag)
	    {
	    std::cerr << "RegisterQuaternion - Could not localize the frame. Skipping this one." << std::endl;
	    }
	    return localized;
	  }
      }
    catch (const std::exception& err)
      {
      if (this->VerboseFlag)
	{
	std::cerr << "Failed to localize frame: " << err.what() << std::endl;
	}
	return LocalizeFrameError;
      }

    // Compute the Z-frame position in the image (RAS) coordinate system
    Zposition = Iposition + Iorientation.RotateVector(Zposition);
    Zorientation = Iorientation * Zorientation;
    }

  // Construct a new event to pass on to the child node.

  if (frame_lock)
    {
    // Calculate rotation from the base orientation
    Zorientation = Zorientation / ZorientationBase;

    position[0] = Zposition.getX();
    position[1] = Zposition.getY();
    position[2] = Zposition.getZ();
    quaternion[0] = Zorientation.getX();
    quaternion[1] = Zorientation.getY();
    quaternion[2] = Zorientation.getZ();
    quaternion[3] = Zorientation.getW();

    return RegisterSuccess;
    }
  else
    {
    return RegisterError;
    }
}


/*----------------------------------------------------------------------------*/

/**
 * The Z-frame contains seven line fiducials arranged in such a manner that
 * its position and orientation in the MRI scanner can be determined from a
 * single image. This method detects the seven line fiducial intercepts.
 * @param SourceImage An image matrix containing the latest image.
 * @param xsize The width of the image in pixels.
 * @param ysize The height of the image in pixels.
 * @param Zcoordinates[][] The resulting list of seven fiducial coordinates.

*/
int Calibration::LocateFiducials(Matrix &SourceImage, int xsize,
                  int ysize, int Zcoordinates[7][2], float tZcoordinates[7][2])
{
  int    i,j;
  Real   peakval, offpeak1, offpeak2, offpeak3, offpeak4;

  // FFT2 only works on square images, fail if x and y size don't match
  if (xsize != ysize)
    {
    std::cerr << "ERROR: LocateFiducials can only call FFT2 with square images. "
              << "Input size is " << xsize << "x" << ysize << std::endl;
    return false;
    }
  // Transform the MR image to the frequency domain (k-space).
  try
    {
    FFT2(SourceImage, zeroimag, IFreal, IFimag);
    }
  catch (...)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Failed in FFT2" << std::endl;
      }
    throw;
    }
  // Normalize the image.
  Real maxabsolute = ComplexMax(IFreal, IFimag);
  // RISK: maxabsolute may be close to zero.
  if (maxabsolute<MEPSILON)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "ZTrackerTransform::LocateFiducials - divide by zero." << std::endl;
      }
    }
  else
    {
    IFreal *= (1 / maxabsolute);
    IFimag *= (1 / maxabsolute);
    }
  
  // Pointwise multiply the Image and the Mask in k-space.
  PFreal.ReSize(xsize, ysize);
  PFimag.ReSize(xsize, ysize);
  for (i = 0; i<xsize; i++)
    {
    for (j = 0; j<ysize; j++)
      {
      PFreal.element(i, j) = IFreal.element(i, j)*MFreal.element(i, j) -
        IFimag.element(i, j)*MFimag.element(i, j);
      PFimag.element(i, j) = IFreal.element(i, j)*MFimag.element(i, j) +
        IFimag.element(i, j)*MFreal.element(i, j);
      }
    }

  // Invert the product of the two k-space images back to spatial domain.
  // Regions of high correlation between the mask the image will appear
  // as sharp peaks in the inverted image.
  PIreal.ReSize(xsize, ysize);
  PIimag.ReSize(xsize, ysize);
  FFT2I(PFreal, PFimag, PIreal, PIimag);

  // FFTSHIFT: exchange diagonally-opposite image quadrants.
  Real swaptemp;
  for (i = 0; i<(xsize / 2); i++)
    for (j = 0; j<ysize / 2; j++)
      {
      // Exchange first and fourth quadrants.
      swaptemp = PIreal.element(i, j);
      PIreal.element(i, j) = PIreal.element(i + xsize / 2, j + ysize / 2);
      PIreal.element(i + xsize / 2, j + ysize / 2) = swaptemp;
      
      // Exchange second and third quadrants.
      swaptemp = PIreal.element(i + xsize / 2, j);
      PIreal.element(i + xsize / 2, j) = PIreal.element(i, j + ysize / 2);
      PIreal.element(i, j + ysize / 2) = swaptemp;
      }
  
  // Normalize result.
  maxabsolute = RealMax(PIreal);
  // RISK: maxabsolute may be close to zero.
  if (maxabsolute<MEPSILON)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "ZTrackerTransform::LocateFiducials - divide by zero." << std::endl;
      }
    return RegisterError;
    }
  else
    {
    PIreal *= (1 / maxabsolute);
    }
  Matrix checkMatrix = PIreal;


  // Find the top 7 peak image values.
  int rstart, rstop, cstart, cstop;
  int peakcount = 0;

  // Adjust the peak radius by the volume voxel size in X and Y to convert
  // peak radius in mm to voxels, but only if using the burn algorithm.
  int peakRadiusX, peakRadiusY;
  if (!this->BurnFlag)
    {
    peakRadiusX = int(round(this->PeakRadius));
    peakRadiusY = int(round(this->PeakRadius));
    }
  else
    {
    peakRadiusX = int(round(this->PeakRadius / this->VoxelSize[0]));
    peakRadiusY = int(round(this->PeakRadius / this->VoxelSize[1]));
    }
  for (i = 0; i<7; i++)
    {
    // Find the next peak value.
    peakval = FindMax(checkMatrix, Zcoordinates[i][0], Zcoordinates[i][1]);
    if (this->VerboseFlag)
      {
      std::cerr << "Think peak is: " << Zcoordinates[i][0] << ", " << Zcoordinates[i][1] << std::endl;
      }
    // Define a block neighbourhood around the peak value.
    rstart = Zcoordinates[i][0] - peakRadiusX;
    if (rstart<0)
      {
      rstart = 0;
      }
    rstop = Zcoordinates[i][0] + peakRadiusX;
    if (rstop >= xsize)
      {
      rstop = xsize - 1;
      }
    cstart = Zcoordinates[i][1] - peakRadiusY;
    if (cstart<0)
      {
      cstart = 0;
      }
    cstop = Zcoordinates[i][1] + peakRadiusY;
    if (cstop >= ysize)
      {
      cstop = ysize - 1;
      }
    bool ignore = false;
    // Check that this is a local maximum.
    if (peakval<MEPSILON)
      {
      if (this->VerboseFlag)
        {
        std::cerr << "Calibration::LocateFiducials - peak value is zero." << std::endl;
        }
      return RegisterError;
      }
    else
      {
      offpeak1 = (peakval - PIreal.element(rstart, cstart)) / peakval;
      offpeak2 = (peakval - PIreal.element(rstart, cstop)) / peakval;
      offpeak3 = (peakval - PIreal.element(rstop, cstart)) / peakval;
      offpeak4 = (peakval - PIreal.element(rstop, cstop)) / peakval;
      if (this->VerboseFlag)
        {
        std::cerr << "LocateFiducials: offpeaks: " << offpeak1 << ", " << offpeak2 << ", " << offpeak3 << ", " << offpeak4 << std::endl;
        }
      
      if (offpeak1 < this->OffPeakPercent ||
          offpeak2 < this->OffPeakPercent ||
          offpeak3 < this->OffPeakPercent ||
          offpeak4 < this->OffPeakPercent)
        {
        if (this->VerboseFlag)
          {
          std::cerr << "\tignoring" << std::endl;
          }
        ignore = true;
        // Ignore coordinate if the offpeak value is within 30% of the peak.
        i--;
        // std::cerr << "Calibration::LocateFiducials - Bad Peak." << std::endl;
        if (++peakcount > this->MaxBadPeaks)
          {
          if (this->VerboseFlag)
            {
            std::cerr << "Calibration::LocateFiducials - too many bad peaks: " << peakcount << std::endl;
            }
          return LocateFiducialsBadPeaks;
          }
        }
      }
    
    if (i >= 0 && ignore == false)
      {
      if (this->VerboseFlag)
        {
        std::cerr << "Pre-subpixel\n";
        std::cerr << i << ": " << Zcoordinates[i][0] << ", " << Zcoordinates[i][1] << std::endl;
        }
      
      // Find the subpixel coordinates of the peak.
      FindSubPixelPeak(&(Zcoordinates[i][0]), &(tZcoordinates[i][0]),
                       PIreal.element(Zcoordinates[i][0], Zcoordinates[i][1]),
                       PIreal.element(Zcoordinates[i][0] - 1, Zcoordinates[i][1]),
                       PIreal.element(Zcoordinates[i][0] + 1, Zcoordinates[i][1]),
                       PIreal.element(Zcoordinates[i][0], Zcoordinates[i][1] - 1),
                       PIreal.element(Zcoordinates[i][0], Zcoordinates[i][1] + 1));
      if (this->VerboseFlag)
        {
        std::cerr << "post-subpixel\n";
        std::cerr << i << ": " << tZcoordinates[i][0] << ", " << tZcoordinates[i][1] << std::endl;
        }
      }
    
    // Eliminate this peak and search for the next.
    for (int m = rstart; m <= rstop; m++)
      {
      for (int n = cstart; n <= cstop; n++)
        {
        if (ignore == false)
          {
          PIreal.element(m, n) = 0.0;
          }
        checkMatrix.element(m, n) = 0.0;
        }
      }
    }
  
  //=== Determine the correct ordering of the detected fiducial points ===
  // Find the centre of the pattern
  float pmid[2];
  if (this->VerboseFlag)
    {
    std::cerr << "Pre-Center\n";
    for (i = 0; i < 7; i++)
      {
      std::cerr << i << ": " << tZcoordinates[i][0] << ", " << tZcoordinates[i][1] << std::endl;
      }
    }
  FindFidCentre(tZcoordinates, pmid[0], pmid[1]);
  
  // Find the corner points
  FindFidCorners(tZcoordinates, pmid);
  
  // Sequentially order all points
  OrderFidPoints(tZcoordinates, pmid[0], pmid[1]);
  
  // Update Zcoordinates
  for (i = 0; i<7; i++)
    {
    Zcoordinates[i][0] = (int)(tZcoordinates[i][0]);
    Zcoordinates[i][1] = (int)(tZcoordinates[i][1]);
    }
  
  return RegisterSuccess;
}

/*----------------------------------------------------------------------------*/

/**
 * Find the subpixel coordinates of the peak. This implementation approximates
 * the location of the peak by fitting a parabola in each axis. This should be
 * revised to fit a paraboloid in 3D.
 * @param Zcoordinate[] A fiducial coordinate.
 * @param tZcoordinate[] A fiducial coordinate computed to sub-pixel accuracy.
 */

void Calibration::FindSubPixelPeak(int Zcoordinate[2],
	float tZcoordinate[2],
	Real Y0, Real Yx1, Real Yx2, Real Yy1, Real Yy2)
{
	float Xshift, Yshift = 0.0;
	if (this->VerboseFlag)
	  {
	  std::cerr << "subpixvals:" << Zcoordinate[0] << "," << Zcoordinate[1] << "," << tZcoordinate[0] << "," << tZcoordinate[1] << "," << Y0 << "," << Yx1 << "," << Yx2 << "," << Yy1 << "," << Yy2 << std::endl;
	  }
	if (((float)Yx1 + (float)Yx2 - 2.0*(float)Y0) != 0)
	{
		Xshift = (0.5*((float)Yx1 - (float)Yx2)) /
			((float)Yx1 + (float)Yx2 - 2.0*(float)Y0);
	}
	if (((float)Yy1 + (float)Yy2 - 2.0*(float)Y0) != 0)
	{
		Yshift = (0.5*((float)Yy1 - (float)Yy2)) /
			((float)Yy1 + (float)Yy2 - 2.0*(float)Y0);
	}

  if(fabs(Xshift)>1.0 || fabs(Yshift)>1.0)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Calibration::FindSubPixelPeak - subpixel peak out of range." << std::endl;
      }
    tZcoordinate[0] = (float)(Zcoordinate[0]);
    tZcoordinate[1] = (float)(Zcoordinate[1]);
    }
  else
    {
    tZcoordinate[0] = (float)(Zcoordinate[0]) + Xshift;
    tZcoordinate[1] = (float)(Zcoordinate[1]) + Yshift;
    }
}

/*----------------------------------------------------------------------------*/

/**
 * Check the geometry of the fiducial pattern to be sure that it is valid.
 * @param Zcoordinates[][] The list of seven fiducial coordinates.
 * @param xsize The width of the image in pixels.
 * @param ysize The height of the image in pixels.
 * @return true if the point geometry is ok, else false.
 */
bool Calibration::CheckFiducialGeometry(int Zcoordinates[7][2], int xsize, int ysize)
{
  Column2Vector  P1, P3, P5, P7;
  Column2Vector  D71, D53, D13, D75;
  int            i;
  float          dotp;

  // First check that the coordinates are in range.
  if (this->VerboseFlag)
    {
    std::cerr << "Zcoordinates\n";
    }
  for(i=0; i<7; i++)
  {
    if (this->VerboseFlag)
      {
      std::cerr << Zcoordinates[i][0] << ", " << Zcoordinates[i][1] << std::endl;
      }
    if(Zcoordinates[i][0]<0 || Zcoordinates[i][0]>=ysize ||
       Zcoordinates[i][1]<0 || Zcoordinates[i][1]>=xsize)
    {
      if (this->VerboseFlag)
	{
	std::cerr << "Calibration::CheckFiducialGeometry - fiducial coordinates out of range. No frame lock on this image." << std::endl;
	}
      return(false);
    }
  }

  // Check that corner points form a parallelogram.
  P1.setvalues((float)Zcoordinates[0][0], (float)Zcoordinates[0][1]);
  P3.setvalues((float)Zcoordinates[2][0], (float)Zcoordinates[2][1]);
  P5.setvalues((float)Zcoordinates[4][0], (float)Zcoordinates[4][1]);
  P7.setvalues((float)Zcoordinates[6][0], (float)Zcoordinates[6][1]);
  D71 = P7 - P1;
  D53 = P5 - P3;
  D13 = P1 - P3;
  D75 = P7 - P5;
  D71.normalize();
  D53.normalize();
  D13.normalize();
  D75.normalize();
  // Check that opposite edges are within 10 degrees of parallel.
  dotp = D71.getX()*D53.getX() + D71.getY()*D53.getY();
  if(dotp<0) dotp *= -1.0;
  if(dotp < cos(5.0*M_PI/180.0)) return(false);
  dotp = D13.getX()*D75.getX() + D13.getY()*D75.getY();
  if(dotp<0) dotp *= -1.0;
  if(dotp < cos(5.0*M_PI/180.0)) return(false);

  return(true);
}


/*----------------------------------------------------------------------------*/

/**
 * Find the centre of the fiducial pattern. A cross-sectional image will
 * intercept each of the Z-frame's seven line fiducials. Once these seven
 * intercepts are detected, this method computes the centre of the region
 * bounded by these points.
 * @param points[][] Image coordinates of the seven fiducial points.
 * @param rmid Row coordinate at centre.
 * @param cmid Column coordinate at centre.
 */
void Calibration::FindFidCentre(float points[7][2], float &rmid, float &cmid)
{
  int    i;
  float  minrow=0.0, maxrow=0.0, mincol=0.0, maxcol=0.0;

  // Find the bounding rectangle.
  for(i=0; i<7; i++)
  {
    // find minimum row coordinate
    if(points[i][0]<minrow || i==0)
      minrow = points[i][0];

    // find maximum row coordinate
    if(points[i][0]>maxrow || i==0)
      maxrow = points[i][0];

    // find minimum column coordinate
    if(points[i][1]<mincol || i==0)
      mincol = points[i][1];

    // find maximum column coordinate
    if(points[i][1]>maxcol || i==0)
      maxcol = points[i][1];
  }

  // Centre of bounding rectangle.
  rmid = (minrow + maxrow)/2.0;
  cmid = (mincol + maxcol)/2.0;
}

/*----------------------------------------------------------------------------*/

/**
 * This method identifies the four corner fiducials, based on known geometry
 * of the Z-frame.
 * @param points[][] The fiducial coordinates detected in the previous step.
 * @param pmid The centre of the rectangular region bounded by the fiducial
 *             points.
 */
void Calibration::FindFidCorners(float points[7][2], float *pmid)
{
  int    i;
  float  itemp[2];
  float  distances[7], dtemp;
  bool   swapped;

  // Compute distances between each fiducial and the midpoint.
  for(i=0; i<7; i++)
  {
    distances[i] = CoordDistance(pmid, &(points[i][0]));
  }

  // Sort distances in descending order. The four corner points will be
  // furthest away from the centre and will be sorted to the top of the
  // coordinate list.
  swapped = true;
  // Loop until there are no more exchanges (Bubble Sort)
  while(swapped)
  {
    swapped = false;
    for(i=0; i<6; i++)
        if(distances[i]<distances[i+1])
        {
          // Swap distances.
          dtemp = distances[i];
          distances[i] = distances[i+1];
          distances[i+1] = dtemp;

          // Swap corresponding coordinates in the fiducial list.
          itemp[0] = points[i][0];
          itemp[1] = points[i][1];
          points[i][0] = points[i+1][0];
          points[i][1] = points[i+1][1];
          points[i+1][0] = itemp[0];
          points[i+1][1] = itemp[1];

          swapped = true;
        }
  }

  // Choose the order of the corners, based on their separation distance.
  // First find the closest point to first corner in the list.
  // This must be an adjacent corner.
  float pdist1 = CoordDistance(&(points[0][0]), &(points[1][0]));
  float pdist2 = CoordDistance(&(points[0][0]), &(points[2][0]));
  if(pdist1>pdist2)
  {
    itemp[0] = points[1][0];
    itemp[1] = points[1][1];
    points[1][0] = points[2][0];
    points[1][1] = points[2][1];
    points[2][0] = itemp[0];
    points[2][1] = itemp[1];
  }
  // Now find closest point (of third or fourth) to second corner in list.
  // This will become the third corner in the sequence.
  pdist1 = CoordDistance(&(points[1][0]), &(points[2][0]));
  pdist2 = CoordDistance(&(points[1][0]), &(points[3][0]));
  if(pdist1>pdist2)
  {
    itemp[0] = points[2][0];
    itemp[1] = points[2][1];
    points[2][0] = points[3][0];
    points[2][1] = points[3][1];
    points[3][0] = itemp[0];
    points[3][1] = itemp[1];
  }
}

/*----------------------------------------------------------------------------*/

/**
 * Find the distance between two image points.
 * TO DO: this should be moved to ZLinAlg.
 * @param p1 First image point coordinates.
 * @param p2 Second image point coordinates.
 * @return Distance between points.
 */
float Calibration::CoordDistance(float *p1, float *p2)
{
  float sqdist;

  sqdist = (p1[0]-p2[0])*(p1[0]-p2[0]) + (p1[1]-p2[1])*(p1[1]-p2[1]);

  // RISK: Argument for SQRT may be negative. Overflow?
  if(sqdist<0)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Calibration::CoordDistance - \
                              negative SQRT argument.\n" << std::endl;
      }
    return(0);
    }
  else
    {
    return(sqrt((float)(sqdist)));
    }
}

/*----------------------------------------------------------------------------*/

/**
 * Put the fiducial coordinate point list in sequential order by matching the
 * three remaining points to their neighbouring ordered corner points.
 * TO DO: messy, need to improve readability.
 * @param points[][] The fiducial coordinate point list.
 * @param rmid The centre of the fiducial pattern in the row coordinate.
 * @param cmid The centre of the fiducial pattern in the column coordinate.
 */
void Calibration::OrderFidPoints(float points[7][2], float rmid, float cmid)
{
  int    pall[9]={0,-1,1,-1,2,-1,3,-1,0};  // prototype index list for all points
  int    pall2[7];
  int    pother[3]={4,5,6};                // indices of points other than corners
  int    i,j;
  float  points_temp[7][2];
  float  cdist, pdist1, pdist2;

  // Find fiducial points that fit between the corners.
  for(i=0; i<7; i+=2)
    for(j=0; j<3; j++)
    {
      if(pother[j]==-1)
      {
        // This point has already been placed.
        continue;
      }
      cdist = CoordDistance(&(points[pall[i]][0]), &(points[pall[i+2]][0]));
      pdist1 = CoordDistance(&(points[pall[i]][0]), &(points[pother[j]][0]));
      pdist2 = CoordDistance(&(points[pall[i+2]][0]), &(points[pother[j]][0]));

      // RISK: divide by zero.
      if(cdist<MEPSILON)
        {
	if (this->VerboseFlag)
	  {
	  std::cerr <<  "Calibration::OrderFidPoints - \
                                divide by zero." << std::endl;
	  }
        // TO DO: this should be detected in the first sanity check.
	}
      else
        {
        if(((pdist1+pdist2)/cdist)<1.05)
          {
            pall[i+1] = pother[j];
            pother[j] = -1;
            break;
          }
        }
    }

  // Re-order the points.
  // Find the -1. The last remaining -1 index marks the two corner points that
  // do not have a fiducial lying between them. By convention, we start ordering
  // the coordinate points from one of these corners.
  for(i=1; i<9; i++)
      if(pall[i]==-1) break;

  // Find the direction to order the points
  // (traverse points clockwise in the image).
  float d1x=(points[pall[0]][0]-rmid);
  float d1y=(points[pall[0]][1]-cmid);
  float d2x=(points[pall[2]][0]-rmid);
  float d2y=(points[pall[2]][1]-cmid);
  float nvecz=(d1x*d2y-d2x*d1y);
  int direction = 0;
  if(nvecz<0)
    direction = -1;
  else
    direction = 1;

  // Do the re-ordering in the clockwise direction.
  for(j=0; j<7; j++)
  {
      i += direction;
      if(i==-1) i=7;
      if(i==9) i=1;
      pall2[j] = pall[i];
  }

  // Create the new ordered point list.
  for(i=0; i<7; i++)
  {
      points_temp[i][0] = points[pall2[i]][0];
      points_temp[i][1] = points[pall2[i]][1];
  }
  for(i=0; i<7; i++)
  {
      points[i][0] = points_temp[i][0];
      points[i][1] = points_temp[i][1];
  }
}

/*----------------------------------------------------------------------------*/

/**
 * Compute the pose of the fiducial frame relative to the image plane, using
 * an adaptation of an algorithm presented by Susil et al.: "A Single image
 * Registration Method for CT-Guided Interentions", MICCAI 1999.
 * @param Zcoordinates[][] Ordered Z-frame coordinates.
 * @param Zposition Estimated position of Z-frame origin w.r.t. image origin.
 * @param Zorientation Estimated orientation of the Z-frame w.r.t. the image
 *        frame--expressed as a quaternion.
 */
int Calibration::LocalizeFrame(float Zcoordinates[7][2],
			       Column3Vector &Zposition,
			       Quaternion &Zorientation)
{
  Column3Vector       Pz1, Pz2, Pz3;
  Column3Vector       Oz;
  Column3Vector       P2f, P4f, P6f;
  Column3Vector       Cf, Ci, Cfi;
  Column3Vector       Vx, Vy, Vz;
  Quaternion          Qft, Qit;
  float               angle;
  Column3Vector       axis;
  std::ostringstream  outs;


  //--- Compute diagonal points in the z-frame coordinates -------
  // Frame origin is at lower corner of Side 1,
  // y-axis is vertical, x-axis is horizontal.

  //--- SIDE 1
  // Map the three points for this z-fiducial.
  Pz1.setvalues( Zcoordinates[0][0], Zcoordinates[0][1], 0.0 );
  Pz2.setvalues( Zcoordinates[1][0], Zcoordinates[1][1], 0.0 );
  Pz3.setvalues( Zcoordinates[2][0], Zcoordinates[2][1], 0.0 );

  // Origin and direction vector of diagonal fiducial.
  // The origin is the end of the diagonal fiducial attached to Pz3
  Oz.setvalues( 30.0, 30.0, -30.0 );
  Vz.setvalues( 0.0, -1.0, 1.0 );

  // Solve for the diagonal intercept in Z-frame coordinates.
  SolveZ(Pz1, Pz2, Pz3, Oz, Vz, P2f);

  //--- BASE
  // Map the three points for this z-fiducial.
  Pz1.setvalues( Zcoordinates[2][0], Zcoordinates[2][1], 0.0 );
  Pz2.setvalues( Zcoordinates[3][0], Zcoordinates[3][1], 0.0 );
  Pz3.setvalues( Zcoordinates[4][0], Zcoordinates[4][1], 0.0 );

  // Origin and direction vector of diagonal fiducial.
  // The origin is the end of the diagonal fiducial attached to Pz3
  Oz.setvalues( -30.0, 30.0, -30.0 );
  Vz.setvalues( 1.0, 0.0, 1.0 );

  // Solve for the diagonal intercept in Z-frame coordinates.
  SolveZ(Pz1, Pz2, Pz3, Oz, Vz, P4f);

  //--- SIDE 2
  // Map the three points for this z-fiducial.
  Pz1.setvalues( Zcoordinates[4][0], Zcoordinates[4][1], 0.0 );
  Pz2.setvalues( Zcoordinates[5][0], Zcoordinates[5][1], 0.0 );
  Pz3.setvalues( Zcoordinates[6][0], Zcoordinates[6][1], 0.0 );

  // Origin and direction vector of diagonal fiducial.
  // The origin is the end of the diagonal fiducial attached to Pz3
  Oz.setvalues( -30.0, -30.0, -30.0 );
  Vz.setvalues( 0.0,  1.0, 1.0 );

  // Solve for the diagonal intercept in Z-frame coordinates.
  SolveZ(Pz1, Pz2, Pz3, Oz, Vz, P6f);

  //--- Compute Transformation Between Image and Frame -----------
  // Compute orientation component first.
  // Compute z-frame cross section coordinate frame

  Vx = P2f - P6f;
  Vy = P4f - P6f;
  Vz = Vx * Vy;
  Vy = Vz * Vx;

  Vx.normalize();
  Vy.normalize();
  Vz.normalize();

  /*
  Vx = P4f - P2f;
  Vy = P6f - P2f;

  Vz = Vx * Vy;
  Vy = Vz * Vx;
  Vx.normalize();
  */
  if(Qft.ComputeFromRotationMatrix(Vx, Vy, Vz) == false)
    return LocalizeFrameComputeFromRotation;

  // Compute image cross-section coordinate frame
  Pz1.setvalues( Zcoordinates[1][0], Zcoordinates[1][1], 0.0);
  Pz2.setvalues( Zcoordinates[3][0], Zcoordinates[3][1], 0.0);
  Pz3.setvalues( Zcoordinates[5][0], Zcoordinates[5][1], 0.0);

  Vx = Pz1 - Pz3;
  Vy = Pz2 - Pz3;

  Vz = Vx * Vy;
  Vy = Vz * Vx;

  Vx.normalize();
  Vy.normalize();
  Vz.normalize();

  if(Qit.ComputeFromRotationMatrix(Vx, Vy, Vz) == false)
    return LocalizeFrameComputeImageCrossSection;

  // Rotation between frame and image: Qif = Qit/Qft
  Zorientation = Qit/Qft;

  // Compute axis-angle.
  angle = 2*acos(Zorientation.getW());
  if(fabs(angle)>15.0)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Calibration::LocalizeFrame - Rotation angle too large, something is wrong." << std::endl;
      }
    return LocalizeFrameAngle;
    }
  if(angle==0.0)
    {
    axis.setX(1.0);
    axis.setY(0.0);
    axis.setZ(0.0);
    }
  else
    {
    axis.setvalues(Zorientation.getX()/
                      sqrt((float)(1-Zorientation.getW()*Zorientation.getW())),
                      Zorientation.getY()/
                      sqrt((float)(1-Zorientation.getW()*Zorientation.getW())),
                      Zorientation.getZ()/
                      sqrt((float)(1-Zorientation.getW()*Zorientation.getW())));
    }
  // RISK: Negative argument for SQRT OR Divide By Zero.
  // TO DO: Overflow unlikely, but check for this condition.
  axis.normalize();

  outs.str("");
  outs << "Rotation Angle [degrees]: " << angle*180.0/3.14159;
  if (this->VerboseFlag)
    {
    std::cerr << outs.str().c_str() << std::endl;
    }
  outs.str("");
  outs  << "Rotation Axis: [" << axis.getX() << "," << axis.getY() << ","
        << axis.getZ() << "]";
  if (this->VerboseFlag)
    {
    std::cerr << outs.str().c_str() << std::endl;
    }

  // Compute translational component.
  // Centroid of triangle in frame coordinates
  Cf = (P2f + P4f + P6f)/3.0;

  // Centroid of frame triangle in image coordinates
  Cfi = Zorientation.RotateVector(Cf);

  // Centroid of triangle in image coordinates
  Ci = (Pz1 + Pz2 + Pz3)/3.0;

  // Displacement of frame in image coordinates.
  Zposition = Ci - Cfi;

  if(fabs(Zposition.getZ())>20.0)
    {
    if (this->VerboseFlag)
      {
      std::cerr << "Calibration::LocalizeFrame - Displacement too large, something is wrong." << std::endl;
      }
      return LocalizeFrameDisplacement;
  }

  outs.str("");
  outs  << "Displacement [mm]: [" << Zposition.getX() << "," << Zposition.getY()
        << "," << Zposition.getZ() << "]";
  if (this->VerboseFlag)
    {
    std::cerr << outs.str().c_str() << std::endl;
    }

  return RegisterSuccess;
}

/*----------------------------------------------------------------------------*/

/**
 * Find the the point at which the diagonal line fiducial is intercepted,
 * using the three intercepts for a single set of planar line fiducials
 * contained in one side of the Z-frame.
 * @param P1  Intercept point of first line fiducial in image.
 * @param P2  Intercept point of second line fiducial in image.
 * @param P3  Intercept point of third line fiducial in image.
 * @param Oz  Origin of this side of the Z-frame, in the Z-frame coordinates.
 * @param Vz  Vector representing the orientation of this side of the Z-frame,
 *            in the Z-frame coordinates.
 * @param P2f Result: diagonal intercept in physical Z-frame coordinates.
 */
void Calibration::SolveZ(Column3Vector P1, Column3Vector P2,
                               Column3Vector P3, Column3Vector Oz,
                               Column3Vector Vz, Column3Vector &P2f)
{
   Column3Vector  Vtmp;
   float          D12, D23, Ld, Lc;

   // Normalize the direction vector of the diagonal fiducial.
   Vz.normalize();

   // Compute intercept.
   Vtmp = P1 - P2;
   D12 = Vtmp.norm();
   Vtmp = P2 - P3;
   D23 = Vtmp.norm();
   Ld = 60.0*sqrt((float)2.0);
   Lc = Ld*D23/(D12+D23);

   // Compute P2 in frame coordinates.
   P2f = Oz + Vz*Lc;
}


/*----------------------------------------------------------------------------*/

/**
 * Find the largest magnitude value in a complex k-space image.
 * @param realmat The matrix of real components.
 * @param imagmat The matrix of imaginary components.
 * @return The magnitude value of the largest k-space element.
 */
Real Calibration::ComplexMax(Matrix &realmat, Matrix &imagmat)
{
  Real maxabs=0.0, valabs=0.0, sqmag=0.0;

  for(int i=0; i<realmat.nrows(); i++)
    for(int j=0; j<realmat.ncols(); j++)
  {
      // Compute squared magnitude of the complex matrix element.
    sqmag = ((realmat.element(i,j)*realmat.element(i,j)) +
        (imagmat.element(i,j)*imagmat.element(i,j)));

      // RISK: Argument for sqrt cannot be negative. Overflow?
    if(sqmag<0)
      {
      if (this->VerboseFlag)
	{
	std::cerr << "Calibration::ComplexMax - \
                                negative sqrt argument." << std::endl;
	}
      }
    else
      {
      // SQRT for magnitude of complex matrix element.
      valabs = sqrt((double)(sqmag));
      }

      // Find maximum magnitude.
    if(maxabs < valabs)
    {
      maxabs = valabs;
    }
  }

  return(maxabs);
}

/*----------------------------------------------------------------------------*/

/**
 * Find the maximum value in a matrix.
 * @param realmat A matrix.
 * @return The value of the largest matrix element.
 */
Real Calibration::RealMax(Matrix &realmat)
{
  Real maxabs=0;


  for(int i=0; i<realmat.nrows(); i++)
    for(int j=0; j<realmat.ncols(); j++)
    {
        // Find the maximum element value.
      if(maxabs < realmat.element(i,j))
      {
        maxabs = realmat.element(i,j);
      }
    }

  return(maxabs);
}

/*----------------------------------------------------------------------------*/

/**
 * Find the maximum value in a matrix, as well as its row and column
 * coordinates in the matrix.
 * @param inmatrix The input matrix.
 * @param row The Resulting row index at which the max value occurs.
 * @param col The Resulting column index at which the max value occurs.
 * @return The value of the largest matrix element.
 */
Real Calibration::FindMax(Matrix &inmatrix, int &row, int &col)
{
  Real maxabs=0;
  row = col = 0;

  // Avoid 10-pixel margin, due to image artifact.
  for(int i=10; i<inmatrix.nrows()-10; i++)
    for(int j=10; j<inmatrix.ncols()-10; j++)
  {
    if(maxabs < inmatrix.element(i,j))
    {
          // Record the maximum value, as well as the coordinates where it
          // occurs.
      maxabs = inmatrix.element(i,j);
      row = i;
      col = j;
    }
  }

  return(maxabs);
}

/*
identify the objects within the input image using a threshold filter with value [threshold]
*/
void Calibration::Burn3D(short* inImage, float threshold)
{
  if (this->VerboseFlag)
    {
    std::cerr << "RUNNING 3d BURN" << std::endl;
    std::cerr << "Threshold..." << threshold << std::endl;
    }
  this->BurnedImage = new short[InputImageDim[0] * InputImageDim[1] * InputImageDim[2]];
  this->BurnLabelMap = new int[InputImageDim[0] * InputImageDim[1] * InputImageDim[2]];
  //start by thresholding inImage and writing output to this->BurnedImage
  if (this->VerboseFlag)
    {
    std::cerr << "Made images" << std::endl;
    }
  for (int i = 0; i < (InputImageDim[0] * InputImageDim[1] * InputImageDim[2]); i++)
  {
	if (inImage[i] > threshold)
	{
	  this->BurnedImage[i] = inImage[i];
	}
	else
	{
	  this->BurnedImage[i] = 0;
	}
	//initialize this->BurnLabelMap
	this->BurnLabelMap[i] = 0;
  }
  if (this->VerboseFlag)
    {
    std::cerr << "threshed images" << std::endl;
    }
  this->LabelCountNum = this->RunBurn(this->SurroundPercent);
  this->LabelCount = new int[this->LabelCountNum];
  for (int i = 0; i < this->LabelCountNum; i++)
  {
    this->LabelCount[i] = 0;
  }
  for (int k = 1; k < InputImageDim[2] - 1; k++)
  {
    for (int j = 1; j < InputImageDim[1] - 1; j++)
      {
	for (int i = 1; i < InputImageDim[0] - 1; i++)
	  {
	    this->LabelCount[this->GetPixel(this->BurnLabelMap, i, j, k)] ++;
	  }
      }
  }
  if (this->VerboseFlag)
    {
    for (int i = 0; i < this->LabelCountNum; i++)
      {
      if (this->LabelCount[i] != 0)
	{
	std::cerr << "Label " << i << " count : " << this->LabelCount[i] << std::endl;
	}
      }
    }
}


// Loop through image and remove pixels that aren't surrounded at least
// [surround]% with other pixels
int Calibration::RunBurn(float surround)
{
  if (this->VerboseFlag)
    {
    std::cerr << "starting burn" << std::endl;
    }
  for (int k = 1; k < InputImageDim[2]-1; k++)
  {
    for (int j = 1; j < InputImageDim[1]-1; j++)
      {
	for (int i = 1; i < InputImageDim[0]-1; i++)
	  {
	    float surroundCount = 0;
	    if (this->GetPixel(this->BurnedImage, i, j, k) > 0)
	      {
		for (int a = -1; a < 2; a++)
		  {
		    for (int b = -1; b < 2; b++)
		      {
			for (int c = -1; c < 2; c++)
			  {
			    surroundCount = surroundCount + (this->GetPixel(this->BurnedImage, i + a, j + b, k + c)>0);
			  }
		      }
		  }
	      }
	    surroundCount = (surroundCount-1)/26;
	    if (surroundCount >= surround)
	      {
		this->BurnLabelMap[(k*InputImageDim[1] * InputImageDim[0] + j *InputImageDim[0] + i)] = 1;
	      }
	  }
      }
  }
  if (this->VerboseFlag)
    {
    std::cerr << "end surround" << std::endl;
    }
  int burnNumber = 2;
  for (int k = 1; k < InputImageDim[2] - 1; k++)
  {
    for (int j = 1; j < InputImageDim[1] - 1; j++)
      {
	for (int i = 1; i < InputImageDim[0] - 1; i++)
	  {
	    if (this->GetPixel(this->BurnLabelMap, i, j, k) == 1)
	      {
		this->DoBurn(i, j, k, burnNumber,1);
		burnNumber++;
	      }
	  }
      }
  }
  if (this->VerboseFlag)
    {
    std::cerr << "end BURN" << std::endl;
    }
  return burnNumber;
}

short Calibration::GetPixel(short* inImage, int i, int j, int k)
{
  return inImage[(k*InputImageDim[1] * InputImageDim[0] + j *InputImageDim[0] + i)];
}

int Calibration::GetPixel(int* inImage, int i, int j, int k)
{
  return inImage[(k*InputImageDim[1] * InputImageDim[0] + j *InputImageDim[0] + i)];
}

void Calibration::DoBurn(int i, int j, int k, int n, int deep)
{
  if (deep < this->RecursionLimit)
  {
	if (this->GetPixel(this->BurnLabelMap, i, j, k) == 1)
	{
	  if (this->GetPixel(this->BurnLabelMap, i + 1, j, k)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i + 1, j, k);
	  }
	  else if (this->GetPixel(this->BurnLabelMap, i - 1, j, k)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i - 1, j, k);
	  }
	  else if (this->GetPixel(this->BurnLabelMap, i, j+1, k)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i, j+1, k);
	  }
	  else if (this->GetPixel(this->BurnLabelMap, i, j-1, k)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i, j-1, k);
	  }
	  else if (this->GetPixel(this->BurnLabelMap, i, j, k+1)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i, j, k+1);
	  }
	  else if (this->GetPixel(this->BurnLabelMap, i, j, k-1)>1)
	  {
		n = this->GetPixel(this->BurnLabelMap, i, j, k-1);
	  }
	  this->BurnLabelMap[(k*InputImageDim[1] * InputImageDim[0] + j *InputImageDim[0] + i)] = n;
	  this->DoBurn(i + 1, j, k, n, deep + 1);
	  this->DoBurn(i - 1, j, k, n, deep + 1);
	  this->DoBurn(i, j - 1, k, n, deep + 1);
	  this->DoBurn(i, j + 1, k, n, deep + 1);
	  this->DoBurn(i, j, k - 1, n, deep + 1);
	  this->DoBurn(i, j, k + 1, n, deep + 1);
	}
  }
}

void Calibration::ConvertBurn()
{
  float voxSize = this->VoxelSize[0] * this->VoxelSize[1] * this->VoxelSize[2];
  if (this->VerboseFlag)
    {
    std::cerr << "voxSize: " << voxSize << ", min:" << this->MinMarkerSize / voxSize << " max:" << this->MaxMarkerSize / voxSize << std::endl;
    }
	
  for (int i = 0; i < InputImageDim[0] * InputImageDim[1] * InputImageDim[2]; i++)
  {
	if (this->BurnLabelMap[i] > 1)
	{
	  if (this->LabelCount[this->BurnLabelMap[i]] > (this->MinMarkerSize / voxSize) &&
	      this->LabelCount[this->BurnLabelMap[i]] < (this->MaxMarkerSize / voxSize))
	  { 
	  //do nothing	
	  }
	  else
	  {
		InputImage[i] = 0;
	  }
	}
	else
	{
	  InputImage[i] = 0;
	}
  }
  if (this->VerboseFlag)
    {
    std::cerr << std::endl;
    }
}

float Calibration::GetMax(short* inImage)
{
  float max = 0;
  for (int i = 0; i < InputImageDim[0] * InputImageDim[1] * InputImageDim[2]; i++)
  {
    max = max*(InputImage[i] < max) + InputImage[i] * (InputImage[i] >= max);
  }
  return max;
}

float Calibration::GetMin(short* inImage)
{
  float min = 0;
  for (int i = 0; i < InputImageDim[0] * InputImageDim[1] * InputImageDim[2]; i++)
  {
	min = min*(InputImage[i] > min) + InputImage[i] * (InputImage[i] <= min);
  }
  return min;
}

void Calibration::SetHistogramMaximumBin(int maxBin)
{
  this->HistogramMaximumBin = maxBin;
}

void Calibration::SetHistogramNumberOfBins(int numBins)
{
  this->HistogramNumberOfBins = numBins;
}

void Calibration::SetVerbose(bool flag)
{
  this->VerboseFlag = flag;
}

bool Calibration::GetVerbose()
{
  return this->VerboseFlag;
}

/**
 * Return a string explaining the input error code.
 * @param code The input erorr code
 * @return A string explaining the erorr code
 */
const char* Calibration::RegisterReturnCodeString(int code)
{
  switch (code)
    {
    case RegisterError:
      return "Default registration error code.";
      break;
    case RegisterSuccess:
      return "Registration succeeded.";
      break;
    case RegisterSliceOutOfBounds:
      return "Slice index is less than zero or more than max number of slices.";
      break;
    case RegisterQuaternionError:
      return "Failed to register quaternion, adjust off peak percent, peak radius, max bad peaks.";
      break;
    case RegisterQuaternionException:
      return "Failed to register quaternion. Unknown exception.";
      break;
    case RegisterQuaternionBadGeometry:
      return "Failed on check of fiducial geometry.";
      break;
    case RegisterQuaternionLocateFiducials:
      return "Failed to locate fiducials.";
      break;
    case RegisterNotEnoughFrameLocks:
      return "Did not find fiducials on enough slices, adjust minimum frame locks.";
      break;
    case RegisterStandardDeviationError:
      return "Standard deviation of calculated transform is too large.";
      break;
    case LocateFiducialsNotSquare:
      return "Input 2D image slice is not square.";
      break;
    case LocateFiducialsBadPeaks:
      return "Unable to locate fiducials in image, too many bad peaks. Peak radius + off peak percent combined to define valid peaks.  If markers have lower contrast versus background, reduce the off peak percent.  Fuzzier marker cross sections will benefit from larger peak radius.";
      break;
    case LocalizeFrameError:
      return "Failed to find fiducials on slice.";
      break;
    case LocalizeFrameComputeFromRotation:
      return "Failed to compute transformation between image and calibrator.";
      break;
    case LocalizeFrameComputeImageCrossSection:
      return "Failed to compute image cross-section coordinate frame.";
      break;
    case LocalizeFrameAngle:
      return "Localize markers: Rotation angle too large, > 15, something is wrong.";
      break;
    case LocalizeFrameDisplacement:
      return "Localize markers: Displacement too large, > 20, something is wrong.";
      break;
    default:
      return "Unknown";
    }
}

}
