/*==========================================================================

  Portions (c) Copyright 2008 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See Doc/copyright/copyright.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   ZFrame Registration
  Module:    $HeadURL: http://svn.slicer.org/Slicer3/trunk/Modules/OpenIGTLinkIF/vtkIGTLToMRMLBase.h $
  Date:      $Date: 2009-01-05 13:28:20 -0500 (Mon, 05 Jan 2009) $
  Version:   $Revision: 8267 $

==========================================================================*/

#ifndef __Registration_h
#define __Registration_h

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
}

namespace zf_9fid {

  typedef float  Matrix4x4[4][4];

  class Registration
  {

  public:

    // Methods related to finding the fiducial artifacts in the MR images.
    Registration();
    ~Registration();

  public:
    int SetBaseLocation(std::string baseLocation);
    int SetInputImage(short* inputImage, int dimensions[3], Matrix4x4& transform);
    int SetOrientationBase(float orentation[4]);
    int SetFrameTopology(float frameTopology[6][3]);
    int SetManualZFrameFiducials(float zFrameFids[9][2], bool manualRegistration);
    int SetAutomaticRegistration(bool manualRegistration);
    int Register(int range[2],float Zposition[3], float Zorientation[4]);

  protected:
    void Init(int xsize, int ysize);
    int  RegisterQuaternion(float position[3], float quaternion[4],
                            float ZquaternionBase[4],
                            Matrix& srcImage, int dimension[3], float spacing[3]);
    bool LocateFiducials(Matrix &image, int xsize, int ysize,
                        int Zcoordinates[9][2], float tZcoordinates[9][2]);
    void FindSubPixelPeak(int Zcoordinate[2], float tZcoordinate[2],
                          Real Y0, Real Yx1, Real Yx2, Real Yy1, Real Yy2);
    bool CheckFiducialGeometry(int Zcoordinates[9][2], int xsize, int ysize);
    void FindFidCentre(float points[9][2], float &rmid, float &cmid);
    void FindFidCorners(float points[9][2], float *pmid);
    void OrderFidPoints(float points[9][2], float rmid, float cmid);

    // Methods related to solving for the frame pose w.r.t. the imaging plane.
  public:
    bool LocalizeFrame(float Zcoordinates[9][2], Column3Vector &Zposition,
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

  protected:

    short *   InputImage;
    int       InputImageDim[3];
    Matrix4x4 InputImageTrans;
    float     ZOrientationBase[4];
    std::string baseLocation;
    float     frameTopology[6][3];
    float     zFrameFids[9][2];
    bool      manualRegistration; 

    //BTX
    Matrix SourceImage, MaskImage;
    Matrix IFreal, IFimag, MFreal, MFimag, zeroimag;
    Matrix PFreal, PFimag;
    Matrix PIreal, PIimag;
    //ETX

  };

}


namespace zf_7fid {

  typedef float  Matrix4x4[4][4];

  // void PrintMatrix(Matrix4x4 &matrix);
  // void QuaternionToMatrix(float* q, Matrix4x4& m);
  // void MatrixToQuaternion(Matrix4x4& m, float* q);
  // void Cross(float *a, float *b, float *c);
  // void IdentityMatrix(Matrix4x4 &matrix);

  class Registration
  {

  public:

    // Methods related to finding the fiducial artifacts in the MR images.
    Registration();
    ~Registration();

  public:
    int SetInputImage(short* inputImage, int dimensions[3], Matrix4x4& transform);
    int SetOrientationBase(float orentation[4]);
    int SetFrameTopology(float frameTopology[6][3]);
    int SetManualZFrameFiducials(float zFrameFids[7][2], bool manualRegistration);
    int SetAutomaticRegistration(bool manualRegistration);
    int Register(int range[2],float Zposition[3], float Zorientation[4]);

  protected:
    void Init(int xsize, int ysize);
    int  RegisterQuaternion(float position[3], float quaternion[4],
                            float ZquaternionBase[4],
                            Matrix& srcImage, int dimension[3], float spacing[3]);
    bool LocateFiducials(Matrix &image, int xsize, int ysize,
                        int Zcoordinates[9][2], float tZcoordinates[9][2]);
    void FindSubPixelPeak(int Zcoordinate[2], float tZcoordinate[2],
                          Real Y0, Real Yx1, Real Yx2, Real Yy1, Real Yy2);
    bool CheckFiducialGeometry(int Zcoordinates[9][2], int xsize, int ysize);
    void FindFidCentre(float points[9][2], float &rmid, float &cmid);
    void FindFidCorners(float points[9][2], float *pmid);
    void OrderFidPoints(float points[9][2], float rmid, float cmid);

    // Methods related to solving for the frame pose w.r.t. the imaging plane.
  public:
    bool LocalizeFrame(float Zcoordinates[9][2], Column3Vector &Zposition,
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

  protected:

    short *   InputImage;
    int       InputImageDim[3];
    Matrix4x4 InputImageTrans;
    float     ZOrientationBase[4];
    float     frameTopology[6][3];
    float     zFrameFids[7][2];
    bool      manualRegistration; 

    //BTX
    Matrix SourceImage, MaskImage;
    Matrix IFreal, IFimag, MFreal, MFimag, zeroimag;
    Matrix PFreal, PFimag;
    Matrix PIreal, PIimag;
    //ETX

  };

}

#endif // __Registration_h
