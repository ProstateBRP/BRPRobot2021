/*=========================================================================

Program:   Harmonus Marker Registration CLI
Module:    HMS_Marker_Detection
Language:  C++
Author:    Phill Marathakis

Copyright (c) Brigham and Women's Hospital. All rights reserved.
See ITKCopyright.txt or http://www.itk.org/HTML/Copyright.htm for details.

This software is distributed WITHOUT ANY WARRANTY; without even 
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#if defined(_MSC_VER)
#pragma warning ( disable : 4786 )
#endif

#ifdef __BORLANDC__
#define ITK_LEAN_AND_MEAN
#endif

#include "itkAffineTransform.h"
#include "itkConstantPadImageFilter.h"
#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkMinimumMaximumImageCalculator.h"
#include "itkOtsuThresholdImageFilter.h"
#include "itkPluginUtilities.h"
#include "itkTransformFileWriter.h"

#include <iostream>
#include <fstream>
#include <ctime>
#include <climits>

// For ZFrame
#include "Calibration.h"

#include "HMS_Marker_DetectionCLP.h"

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
namespace
{

  typedef std::vector<double> CoordType;
  typedef std::vector<CoordType> CoordSetType;

  // Read in the marker configuration from a comma separated value file filename.
  // Return the centroids and orientations in points, also set the configuration id and
  // description.
  int LoadMarkerConfiguration(const char* filename, CoordSetType& points,
			      std::string& markerID, std::string& markerDescription,
			      std::string& gridID,
			      bool debug=0)
  {
    if (!filename)
      {
	std::cerr << "Configuration file name not specified!"
		  << std::endl;
	return 0;
      }
    std::ifstream configfile (filename);
    if (!configfile.is_open())
      {
	std::cerr << "Unable to open configuration file "
		  << filename
		  << std::endl;
	return 0;
      }

    points.clear();

    CoordType point(3);
    CoordType norm(3);

    if (debug)
      {
	std::cerr << "Parsing Marker Configuration File: " << filename << std::endl;
      }
    std::string line;
    // headers
    std::string idStringPrefix = std::string("# Harmonus Marker Configuration ID = ");
    std::string descriptionStringPrefix = std::string("# Harmonus Marker Configuration Description = ");
    std::string gridIDStringPrefix = std::string("# Harmonus Guide Sheet ID = ");
    while ( configfile.good() )
      {
	int pointId = 0;
	int lineNumber = 0;
	while(std::getline(configfile,line))
	  {
	    lineNumber++;
	    if (debug)
	      {
		std::cerr << "Line length = " << line.size() << std::endl;
	      }
	    // check for comment lines, starting with # followed by space
	    if (line.size() > 1 &&
		line[0] == '#' &&
		line[1] == ' ')
	      {
		if (line.find(idStringPrefix) != std::string::npos)
		  {
		    markerID = line.substr(idStringPrefix.size(), std::string::npos);
		    std::cerr << "Marker file ID = '" << markerID << "'" << std::endl;
		  }
		else if (line.find(descriptionStringPrefix) != std::string::npos)
		  {
		    markerDescription = line.substr(descriptionStringPrefix.size(), std::string::npos);
		    std::cerr << "Marker file description = '" << markerDescription << "'" << std::endl;
		  }
		else if (line.find(gridIDStringPrefix) != std::string::npos)
		  {
		    gridID = line.substr(gridIDStringPrefix.size(), std::string::npos);
		    std::cerr << "Grid file ID = '" << gridID << "'" << std::endl;
		  }
		else
		  {
		    std::cerr << "\tunknown comment line: " << line << std::endl;
		  }
	      }
	    else
	      {
		std::stringstream  lineStream(line);
		std::string        cell;
		std::vector<double> values;
		values.clear();
		while(std::getline(lineStream,cell,','))
		  {
		    values.push_back(::atof(cell.c_str()));
		  }
		if (values.size() == 6)
		  {
		    point[0] = values[0];
		    point[1] = values[1];
		    point[2] = values[2];
		    norm[0] = values[3];
		    norm[1] = values[4];
		    norm[2] = values[5];
		    points.push_back(point);
		    points.push_back(norm);
		    if (debug)
		      {
			std::cerr << "Fiducial #" << pointId << ": "
				  << "Point=("  << point[0] << ", " << point[1] << ", " << point[2] << "); "
				  << "Normal=(" << norm[0] << ", " << norm[1] << ", " << norm[2] << ")"
				  << std::endl;
		      }
		    pointId ++;
		  }
		else
		  {
		    if (values.size() != 0)
		      {
			std::cerr << "Invalid configuration file format!\n\tfile :" << filename
				  << "\n\tline number: " << lineNumber
				  << "\n\tline: " << line
				  << std::endl;
			return 0;
		      }
		  }
	      }
	  }
      }
    configfile.close();

    return 1;
  }
  
  template <class T> int DoIt( int argc, char * argv[], T )
  {
    PARSE_ARGS;

    if (debug)
      {
      std::cerr << "Starting doit" << std::endl;
      }
    const unsigned int Dimension = 3;

    typedef   T InputPixelType;
    typedef int OutputPixelType;
    typedef float InternalPixelType;

    typedef itk::Image<InputPixelType,  Dimension> InputImageType;
    typedef itk::Image<InternalPixelType, Dimension> InternalImageType;
    typedef itk::Image<OutputPixelType, Dimension> OutputImageType;

    typedef itk::ImageFileReader<InputImageType>  ReaderType;
    typedef itk::ImageFileWriter<OutputImageType> WriterType;

    typename ReaderType::Pointer reader = ReaderType::New();
    typename WriterType::Pointer writer = WriterType::New();


    reader->SetFileName( inputVolume.c_str() );
    writer->SetFileName( outputVolume.c_str() );

    reader->Update();

    time_t t = time(0);
    struct tm * now = localtime(&t);

    CoordSetType points;
    std::string markerID, markerDescription, gridID;
    if (LoadMarkerConfiguration(markerConfigFile.c_str(), points, markerID, markerDescription, gridID, debug) <= 0)
    {
      return EXIT_FAILURE ;
    }
    if (debug)
      {
      std::cerr << "After loading marker configuration, marker id = '"
                << markerID << "', description = " << markerDescription
                << ", grid id = '" << gridID
                << "'\noutput parameter file: " << returnParameterFile
                << std::endl;
      }
    // Return the ids and description
    // Write out the return parameters in "name = value" form
    std::ofstream parameterStream;
    parameterStream.open(returnParameterFile.c_str() );
    if (parameterStream.is_open())
      {
	parameterStream << "markerConfigurationID = " << markerID << std::endl;
	parameterStream << "markerConfigurationDescription = " << markerDescription << std::endl;
	parameterStream << "markerConfigurationGridID = " << gridID << std::endl;
	parameterStream.close();
      }

    // output for ZFrame registration
    typedef itk::AffineTransform< double, 3> MarkerTransformType;
    MarkerTransformType::Pointer outputTransform = MarkerTransformType::New();
    bool successFlag = false;

    // If the marker configuration file is numbered as 4 or above, do
    // the ZFrame registration, otherwise fail out with a message that
    // the old configuration file has been deprecated.
    // Remove the RFR- from the ID
    std::string markerIDNumberString = markerID.substr(4, std::string::npos);
    if (debug)
      {
      std::cerr << "markerIDNumber: string " << markerIDNumberString << std::endl;
      }
    int markerIDNumber = std::stoi(markerIDNumberString);
    if (debug)
      {
      std::cerr << "\tint: " << markerIDNumber << std::endl;
      }
    bool isZFrame = false;
    if (markerIDNumber >= 4)
      {
      isZFrame = true;
      }
    if (debug)
      {
      std::cerr << "Checking for ZFrame configuration, marker id = '" << markerID << "', isZFrame = " << isZFrame << std::endl;
      }
    if (!isZFrame)
      {
      std::cerr << "\n\nERROR: non ZFrame registration has been deprecated, use version 0.2.0 or earlier with "
                << markerID.c_str()
                << std::endl;
      return EXIT_FAILURE;
      }
    bool ZFrameSuccess = true;
    int registrationReturnCode = zf::Calibration::RegisterSuccess;

    // *******************
    // ZFrame Registration
    // *******************

    if (debug)
      {
      std::cerr << "Doing ZFrame Registration" << std::endl;
      std::cerr << "\tstartSlice = " << startSlice << std::endl;
      std::cerr << "\tendSlice = " << endSlice << std::endl;
      }

    // WARNING: only works on short input images
    typedef short PixelType;

    // check type and max of input image
    InputImageType::Pointer inputImage = reader->GetOutput();
    itk::ImageIOBase::IOPixelType     pixelType;
    itk::ImageIOBase::IOComponentType componentType;
    itk::GetImageType(inputVolume, pixelType, componentType);
    if (componentType != itk::ImageIOBase::SHORT)
      {
      // check maximum and minimum, casting may be okay
      typedef itk::MinimumMaximumImageCalculator <InputImageType> calcType;
      calcType::Pointer calcFilter = calcType::New();
      calcFilter->SetImage(inputImage);
      calcFilter->Compute();
      InputPixelType maxIntensity = calcFilter->GetMaximum();
      InputPixelType minIntensity = calcFilter->GetMinimum();
      if (minIntensity < 0 || maxIntensity > SHRT_MAX)
        {
        std::cerr << "\nWARNING: Input image is not of type short.\nWARNING: Intensity range "
                  << minIntensity << " - " <<  maxIntensity
                  << " doesn't fit 0 - " << SHRT_MAX
                  << ".\nWARNING: ZFrame registration may not work with default settings when input image is cast to short.\n"
                  << std::endl;
        }
      }
    else
      {
      if (debug)
        {
        std::cerr << "Input image is SHORT" << std::endl;
        }
      }

    // Read in the input image
    typedef itk::Image<PixelType, Dimension> ImageType;
    typedef itk::ImageFileReader<ImageType> ZReaderType;
    ZReaderType::Pointer zreader = ZReaderType::New();
    zreader->SetFileName(inputVolume.c_str());
    zreader->Update();

    ImageType::Pointer image = zreader->GetOutput();

    // Check that the region over which to register is within the dimensions
    typedef ImageType::SizeType Size3D;
    Size3D dimensions = image->GetLargestPossibleRegion().GetSize();
    if (debug)
      {
      std::cerr << "Input image dimensions = "
                << dimensions[0] << ", "
                << dimensions[1] << ", "
                << dimensions[2] << std::endl;
      }
    // if end slice hasn't been set, set it to cover full volume
    if (endSlice == 0)
      {
      endSlice = dimensions[2];
      std::cerr << "End slice was 0, reset to " << endSlice << std::endl;
      }
    std::string sliceErrorString;
    // check slice range now when can give the image dimensions in the error message
    if (startSlice < 0)
      {
      sliceErrorString = sliceErrorString
        + "Start slice "
        + std::to_string(startSlice)
        + " is < 0! Image has "
        + std::to_string(dimensions[2])
        + " slices.  ";
      }
    else if (startSlice > dimensions[2])
      {
      sliceErrorString = sliceErrorString
        + "Start slice "
        + std::to_string(startSlice)
        + " is > image number of slices: "
        + std::to_string(dimensions[2])
        + ".  ";
      }

    if (endSlice <= 0)
      {
      sliceErrorString = sliceErrorString
        + "End slice "
        + std::to_string(endSlice)
        + " is <= 0! Image has "
        + std::to_string(dimensions[2])
        + " slices.  ";
      }
    else if (endSlice < startSlice)
      {
      sliceErrorString = sliceErrorString
        + "End slice "
        + std::to_string(endSlice)
        + " < start slice "
        + std::to_string(startSlice)
        + ". Image has "
        + std::to_string(dimensions[2])
        + " slices.  ";
      }
    else if (endSlice > dimensions[2])
      {
      sliceErrorString = sliceErrorString
        + "End slice "
        + std::to_string(endSlice)
        + " is > image number of slices: "
        + std::to_string(dimensions[2])
        + ".  ";
      }
    if (!sliceErrorString.empty())
      {
      if (debug)
        {
        std::cerr << "Have a slice range error string..." << std::endl;
        }
      // report in output parameters file
      parameterStream.open(returnParameterFile.c_str(), std::ofstream::app );
      if (parameterStream.is_open())
        {
        registrationReturnCode = zf::Calibration::RegisterSliceOutOfBounds;
        parameterStream << "returnCode = " << std::to_string(registrationReturnCode) << std::endl;
        parameterStream << "returnString = " << sliceErrorString.c_str() << std::endl;
        parameterStream.close();
        if (debug)
          {
          std::cerr << "Wrote slice error to " << returnParameterFile.c_str() << std::endl;
          }
        }
      // tests for slices out of range checks for this error string
      std::cerr << sliceErrorString.c_str()
                << std::endl;
      return EXIT_FAILURE;
      }

    // Ensure that the image is square along XY
    int dim[3];
    dim[0] = dimensions[0];
    dim[1] = dimensions[1];
    dim[2] = dimensions[2];

    // save the padding information to adjust the translation of the final matrix
    bool padded = false;
    ImageType::SizeType upperBoundary, lowerBoundary;
    if (dim[0] != dim[1])
      {
      std::cerr << "WARNING: input image is not square, padding!" << std::endl;
      padded = true;
      int diff = abs(dim[0] - dim[1]);
      std::cerr << "\tdims diff = " << diff << std::endl;
      int upper = ceil(diff/2.0);
      int lower = floor(diff/2.0);
      if (dim[0] > dim[1])
        {
        // Pad in Y
        upperBoundary[0] = 0;
        lowerBoundary[0] = 0;
        upperBoundary[1] = upper;
        lowerBoundary[1] = lower;
        }
      else
        {
        // Pad in X
        upperBoundary[0] = upper;
        lowerBoundary[0] = lower;
        upperBoundary[1] = 0;
        lowerBoundary[1] = 0;
        }
      // don't pad in z
      upperBoundary[2] = 0;
      lowerBoundary[2] = 0;
      if (debug)
        {
        std::cerr << "\tpad upper = " << upperBoundary << std::endl;
        std::cerr << "\tpad lower = " << lowerBoundary << std::endl;
        }

      ImageType::PixelType constantPixel = 0;
      typedef itk::ConstantPadImageFilter <ImageType, ImageType> ConstantPadImageFilterType;
      ConstantPadImageFilterType::Pointer padFilter = ConstantPadImageFilterType::New();
      padFilter->SetInput(image);
      padFilter->SetPadLowerBound(lowerBoundary);
      padFilter->SetPadUpperBound(upperBoundary);
      padFilter->SetConstant(constantPixel);
      padFilter->Update();
      image = padFilter->GetOutput();
      }

    dimensions = image->GetLargestPossibleRegion().GetSize();
    if (debug)
      {
      std::cerr << "\tAfter adjusting, input image dimensions = "
                << dimensions[0] << ", "
                << dimensions[1] << ", "
                << dimensions[2] << std::endl;
      }
    // double check the image is now square
    dim[0] = dimensions[0];
    dim[1] = dimensions[1];
    if (dim[0] != dim[1])
      {
      std::cerr << "Failed to make a square image!" << std::endl;
      return EXIT_FAILURE;
      }

    ImageType::DirectionType itkDirections = image->GetDirection();
    ImageType::PointType itkOrigin = image->GetOrigin();
    ImageType::SpacingType itkSpacing = image->GetSpacing();

    double origin[3] = {itkOrigin[0], itkOrigin[1], itkOrigin[2]};
    double spacing[3] = {itkSpacing[0], itkSpacing[1], itkSpacing[2]};
    double directions[3][3] = {{1.0,0.0,0.0},{0.0,1.0,0.0},{0.0,0.0,1.0}};
    for (unsigned int col=0; col<3; col++)
      {
      for (unsigned int row=0; row<3; row++)
        {
        directions[row][col] = itkDirections[row][col];
        }
      }

    typedef itk::Matrix<double, 4, 4> MatrixType;
    MatrixType rtimgTransform;
    rtimgTransform.SetIdentity();

    for (int row=0; row<4; row++)
      {
      for (int col=0; col<4; col++)
        {
        rtimgTransform[row][col] = spacing[col] * directions[row][col];
        }
      rtimgTransform[row][3] = origin[row];
      }

    //  LPS (ITK)to RAS (Slicer) transform matrix
    MatrixType lps2RasTransformMatrix;
    lps2RasTransformMatrix.SetIdentity();
    lps2RasTransformMatrix[0][0] = -1.0;
    lps2RasTransformMatrix[1][1] = -1.0;
    lps2RasTransformMatrix[2][2] =  1.0;
    lps2RasTransformMatrix[3][3] =  1.0;

    MatrixType imageToWorldTransform;
    imageToWorldTransform = lps2RasTransformMatrix * rtimgTransform;

    // Convert image position and orientation to zf::Matrix4x4
    zf::Matrix4x4 imageTransform;
    for (int row=0; row<4; row++)
      {
      for (int col=0; col<4; col++)
        {
	imageTransform[row][col] = imageToWorldTransform[row][col];
        }
      }

    MatrixType ZFrameBaseOrientation;
    ZFrameBaseOrientation.SetIdentity();

    // ZFrame base orientation
    zf::Matrix4x4 ZmatrixBase;
    for (int row=0; row<4; row++)
      {
      for (int col=0; col<4; col++)
        {
	ZmatrixBase[row][col] = (float) ZFrameBaseOrientation[row][col];
        }
      }

    // Convert Base Matrix to quaternion
    float ZquaternionBase[4];
    zf::MatrixToQuaternion(ZmatrixBase, ZquaternionBase);

    // Set slice range
    int range[2];
    range[0] = startSlice;
    range[1] = endSlice;

    float Zposition[3];
    float Zorientation[4];

    // Set up inputs to Z-frame registration
    dim[0] = dimensions[0];
    dim[1] = dimensions[1];
    dim[2] = dimensions[2];


    // Histogram the image to get a threshold
    typedef itk::Statistics::ImageToHistogramFilter < ImageType > ImageToHistogramFilterType;
    ImageToHistogramFilterType::Pointer imageToHistFilter = ImageToHistogramFilterType::New();
    imageToHistFilter->SetInput(image);

    if (histogramAutoBounds)
      {
      imageToHistFilter->SetAutoMinimumMaximum(true);
      }
    else
      {
      ImageToHistogramFilterType::HistogramType::MeasurementVectorType lowerBound(binsPerDimension);
      lowerBound.Fill(0);
      ImageToHistogramFilterType::HistogramType::MeasurementVectorType upperBound(binsPerDimension);
      upperBound.Fill(histogramUpperBound);
      imageToHistFilter->SetHistogramBinMinimum(lowerBound);
      imageToHistFilter->SetHistogramBinMaximum(upperBound);
      }
    ImageToHistogramFilterType::HistogramType::SizeType size(1); //1 for greyscale image
    size.Fill(binsPerDimension);

    imageToHistFilter->SetHistogramSize(size);
    imageToHistFilter->Update();

    ImageToHistogramFilterType::HistogramType* histo = imageToHistFilter->GetOutput();

    int maxBin = 0;
    float maxFreq = 0;
    if (debug)
      {
      std::cerr << "Histogram Frequency = ";
      }
    for (unsigned int i = 0; i < histo->GetSize()[0]; ++i)
      {
      if (histo->GetFrequency(i) > maxFreq)
        {
        maxBin = i;
        maxFreq = histo->GetFrequency(i);
        }
      if (debug)
        {
        std::cerr << histo->GetFrequency(i) << " ";
        }
      }
    if (debug)
      {
      std::cerr << std::endl;
      std::cout << std::endl;
      }
    // Call Z-frame registration
    zf::Calibration * calibration;
    calibration = new zf::Calibration();

    if (debug)
      {
      calibration->SetVerbose(true);
      }
    calibration->SetInputImage(image->GetBufferPointer(), dim, imageTransform);
    calibration->SetBurnFlag(burnFlag == 1);
    calibration->SetVoxelSize(spacing);
    calibration->SetHistogramMaximumBin(maxBin);
    calibration->SetHistogramNumberOfBins(binsPerDimension);
    calibration->SetOrientationBase(ZquaternionBase);
    calibration->SetBurnThresholdPercent(burnThresholdPercent);
    calibration->SetSurroundPercent(surroundPercent);
    calibration->SetRecursionLimit(recursionLimit);
    calibration->SetMinFrameLocks(minFrameLocks);
    calibration->SetMaxBadPeaks(maxBadPeaks);
    calibration->SetOffPeakPercent(offPeakPercent);
    calibration->SetPeakRadius(peakRadius);
    calibration->SetMaxStandardDeviationPosition(maxStdDevPos);
    calibration->SetMinMarkerSize((double)minimumObjectSize);
    calibration->SetMaxMarkerSize((double)maximumObjectSize);

    int returnValue = calibration->Register(range, Zposition, Zorientation);

    registrationReturnCode = returnValue;
    if (debug)
      {
      std::cerr << "registrationReturnCode = " << registrationReturnCode << std::endl;
      }

    double posStdDev[3] = {0.0, 0.0, 0.0};
    double quatStdDev[4] = {0.0, 0.0, 0.0, 0.0};
    calibration->GetPositionStdDev(posStdDev);
    calibration->GetQuaternionStdDev(quatStdDev);

    const char *returnCodeString = calibration->RegisterReturnCodeString(registrationReturnCode);
    delete calibration;

    std::cerr << "Output from calibration Register: "
		  << std::to_string(registrationReturnCode)
		  << ": "
		  << returnCodeString
		  << endl;

    // Return the result standard deviation via the parameters file
    std::cerr << "\tposition standard deviation = "
              << posStdDev[0] << ", "
              << posStdDev[1] << ", "
              << posStdDev[2]
              << endl;
    std::cerr << "\tquaternion standard deviation = "
              << quatStdDev[0] << ", "
              << quatStdDev[1] << ", "
              << quatStdDev[2] << ", "
              << quatStdDev[3]
              << endl;
    // append to the parameters file
    parameterStream.open(returnParameterFile.c_str(), std::ofstream::app );
    if (parameterStream.is_open())
      {
      parameterStream << "returnCode = " << std::to_string(registrationReturnCode) << std::endl;
      parameterStream << "returnString = " << returnCodeString << std::endl;
      parameterStream << "positionStdDev = " << posStdDev[0] << "," << posStdDev[1] << "," << posStdDev[2] << std::endl;
      parameterStream << "quaternionStdDev = " << quatStdDev[0] << "," << quatStdDev[1] << "," << quatStdDev[2] << "," << quatStdDev[3] << std::endl;
      parameterStream.close();
      if (debug)
        {
        std::cerr << "Wrote return codes and stddev to " << returnParameterFile.c_str() << std::endl;
        }
      }
    if (returnValue != zf::Calibration::RegisterSuccess)
      {
      std::cerr << "ZFrame registration failed.\n"
                << returnCodeString << std::endl;
      // print the string that ctest is seraching for when match not made
      std::cerr << "DIDN'T FIND ANY MATCHES\n";
      ZFrameSuccess = false;
      }
    if (returnValue == zf::Calibration::RegisterSuccess)
      {
      ZFrameSuccess = true;

      // Convert quaternion to matrix
      zf::Matrix4x4 matrix;
      zf::QuaternionToMatrix(Zorientation, matrix);

      MatrixType zMatrix;
      zMatrix.SetIdentity();
      for (int row=0; row<4; row++)
        {
        for (int col=0; col<4; col++)
          {
          zMatrix[row][col] = matrix[row][col];
          }
        }
      if (padded)
        {
        if (debug)
          {
          std::cerr << "Image was padded:"
                    << "\n\tlowerBoundary = "
                    << lowerBoundary[0] << ", " << lowerBoundary[1]
                    << "\n\tupperBoundary = "
                    << upperBoundary[0] << ", " << upperBoundary[1]
                    << "\n\tslice thickness = "
                    << spacing[0] << ", " << spacing[1] << ", " << spacing[2]
                    << "\n\tdirections diagonal = "
                    << directions[0][0] << ", " << directions[1][1] << ", " << directions[2][2]
                    << "\n\tadjusting the Z position from "
                    << Zposition[0] << ", " << Zposition[1] << ", " << Zposition[2] << std::endl;
          }
        // multiply by directions as the IJK to RAS direction matrix
        // may have flipped around axes
        zMatrix[0][3] = Zposition[0] + (lowerBoundary[0] * spacing[0] * directions[0][0]);
        zMatrix[1][3] = Zposition[1] + (lowerBoundary[1] * spacing[1] * directions[1][1]);
        // never pad in Z
        zMatrix[2][3] = Zposition[2];
        }
      else
        {
        zMatrix[0][3] = Zposition[0];
        zMatrix[1][3] = Zposition[1];
        zMatrix[2][3] = Zposition[2];
        }
      std::cerr << "RAS Transformation Matrix:" << endl;
      std::cerr << zMatrix << endl;

      zMatrix = zMatrix * lps2RasTransformMatrix;
      zMatrix = (MatrixType)zMatrix.GetInverse() * lps2RasTransformMatrix;


      typedef itk::Matrix<double, 3, 3> TransformMatrixType;
      TransformMatrixType lpsTransformMatrix;
      lpsTransformMatrix.SetIdentity();
      for(int row=0; row<3; row++)
        {
        for(int col=0; col<3; col++)
          {
          lpsTransformMatrix[row][col] = zMatrix[row][col];
          }
        }

      typedef itk::AffineTransform<double> RegistrationTransformType;
      RegistrationTransformType::OutputVectorType translation;
      translation[0] = zMatrix[0][3];
      translation[1] = zMatrix[1][3];
      translation[2] = zMatrix[2][3];

      outputTransform->SetMatrix(lpsTransformMatrix);
      outputTransform->SetTranslation(translation);

      // Write out an output image so Slicer can volume render labels.
      // Threshold the input image into a label map output volume.
      typedef itk::OtsuThresholdImageFilter<InputImageType, OutputImageType> BinaryTFilterType;
      BinaryTFilterType::Pointer thresholdFilter = BinaryTFilterType::New();
      thresholdFilter->SetInput(reader->GetOutput());
      // 8 is yellow in the Labels color table
      thresholdFilter->SetInsideValue(0);
      thresholdFilter->SetOutsideValue(8);
      writer->SetInput(thresholdFilter->GetOutput());
      writer->SetUseCompression(1);
      try
        {
        writer->Update();
        std::cerr << "Wrote output file " << writer->GetFileName() << std::endl;
        }
      catch (itk::ExceptionObject &err)
        {
        std::cerr << "ERROR writing output label image "
                  << writer->GetFileName() << ":\n" << err << std::endl;
        return EXIT_FAILURE;
        }

      // set the success flag for writing out the marker transform
      successFlag = true;
      }


    // *********************************
    // Write output transform.
    // *********************************
    typedef itk::TransformFileWriter TransformWriteType;
    if (markerTransform != "")
      {
      // write out the final transform
      TransformWriteType::Pointer markerTransformWriter;
      markerTransformWriter = TransformWriteType::New();
      markerTransformWriter->SetFileName(markerTransform);
      markerTransformWriter->SetInput(outputTransform);
      try
        {
        markerTransformWriter->Update();
        }
      catch (itk::ExceptionObject &err)
        {
        std::cerr << "Failed to write marker transform to file "
                  << markerTransformWriter->GetFileName() << "\n"
                  << err << std::endl;
        return EXIT_FAILURE;
        }
      }
    if (regSuccess != "")
      {
        TransformWriteType::Pointer successTransformWriter;
        successTransformWriter = TransformWriteType::New();
        successTransformWriter->SetFileName(regSuccess);
        MarkerTransformType::Pointer successTrans = MarkerTransformType::New();
        successTrans->SetIdentity();
        itk::AffineTransform<double, 3>::OutputVectorType successVector;
        if (successFlag)
          {
          successVector[0] = 1;
          }
        else
          {
          if (debug)
            {
            std::cerr << "Putting error code in success matrix: "
                      << std::to_string(registrationReturnCode)
                      << std::endl;
            }
          successVector[0] = registrationReturnCode;
          }

        successTrans->Translate(successVector);
        successTransformWriter->SetInput(successTrans);
        try
          {
          successTransformWriter->Update();
          if (debug)
            {
            std::cerr << "Wrote success transform: "
                      << successTransformWriter->GetFileName()
                      << std::endl;
            }
          }
        catch (itk::ExceptionObject &err)
          {
          std::cerr << "Failed to write success tranform to file "
                    << successTransformWriter->GetFileName() << "\n"
                    << err << std::endl;
          return EXIT_FAILURE;
          }
      }
    // return success if get to this point, rely on the success matrix to say if
    // registration was succesful or not
    return EXIT_SUCCESS;
  }

} // end of anonymous namespace





int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  itk::ImageIOBase::IOPixelType     pixelType;
  itk::ImageIOBase::IOComponentType componentType;

  try
    {
    itk::GetImageType(inputVolume, pixelType, componentType);

    // This filter handles all types on input, but only produces
    // signed types
    switch( componentType )
      {
      case itk::ImageIOBase::UCHAR:
        return DoIt( argc, argv, static_cast<unsigned char>(0) );
        break;
      case itk::ImageIOBase::CHAR:
        return DoIt( argc, argv, static_cast<char>(0) );
        break;
      case itk::ImageIOBase::USHORT:
        return DoIt( argc, argv, static_cast<unsigned short>(0) );
        break;
      case itk::ImageIOBase::SHORT:
        return DoIt( argc, argv, static_cast<short>(0) );
        break;
      case itk::ImageIOBase::UINT:
        return DoIt( argc, argv, static_cast<unsigned int>(0) );
        break;
      case itk::ImageIOBase::INT:
        return DoIt( argc, argv, static_cast<int>(0) );
        break;
      case itk::ImageIOBase::ULONG:
        return DoIt( argc, argv, static_cast<unsigned long>(0) );
        break;
      case itk::ImageIOBase::LONG:
        return DoIt( argc, argv, static_cast<long>(0) );
        break;
      case itk::ImageIOBase::FLOAT:
        return DoIt( argc, argv, static_cast<float>(0) );
        break;
      case itk::ImageIOBase::DOUBLE:
        return DoIt( argc, argv, static_cast<double>(0) );
        break;
      case itk::ImageIOBase::UNKNOWNCOMPONENTTYPE:
      default:
        std::cerr << "Unknown component type: " << componentType << std::endl;
        break;
      }
    }

  catch( itk::ExceptionObject & excep )
    {
    std::cerr << argv[0] << ": exception caught !" << std::endl;
    std::cerr << excep << std::endl;
    return EXIT_FAILURE;
    }
  return EXIT_SUCCESS;
}
