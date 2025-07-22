#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkTransformFileWriter.h"
#include "itkAffineTransform.h"

#include "itkPluginUtilities.h"

#include "Registration.h"
#include <ZFrameRegistrationCLP.h>


using namespace std;

int main( int argc, char * argv[] )
{
    PARSE_ARGS;
    
    const unsigned int Dimension = 3;
    
    typedef short PixelType;

    typedef itk::Image<PixelType, Dimension> ImageType;
    typedef itk::ImageFileReader<ImageType> ReaderType;
    ReaderType::Pointer reader = ReaderType::New();
    
    typedef itk::Matrix<double, 4, 4> MatrixType;
    
    reader->SetFileName(inputVolume.c_str());
    reader->Update();
    
    ImageType::Pointer image = reader->GetOutput();
    
    typedef ImageType::SizeType Size3D;
    Size3D dimensions = image->GetLargestPossibleRegion().GetSize();
    
    ImageType::DirectionType itkDirections = image->GetDirection();
    ImageType::PointType itkOrigin = image->GetOrigin();
    ImageType::SpacingType itkSpacing = image->GetSpacing();
    
    double origin[3] = {itkOrigin[0], itkOrigin[1], itkOrigin[2]};
    double spacing[3] = {itkSpacing[0], itkSpacing[1], itkSpacing[2]};
    double directions[3][3] = {{1.0,0.0,0.0},{0.0,1.0,0.0},{0.0,0.0,1.0}};
    for (unsigned int col=0; col<3; col++)
        for (unsigned int row=0; row<3; row++)
            directions[row][col] = itkDirections[row][col];
    
    MatrixType rtimgTransform;
    rtimgTransform.SetIdentity();
    
    int row, col;
    for(row=0; row<3; row++)
    {
        for(col=0; col<3; col++)
            rtimgTransform[row][col] = spacing[col] * directions[row][col];
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
    imageTransform[0][0] = imageToWorldTransform[0][0];
    imageTransform[1][0] = imageToWorldTransform[1][0];
    imageTransform[2][0] = imageToWorldTransform[2][0];
    imageTransform[0][1] = imageToWorldTransform[0][1];
    imageTransform[1][1] = imageToWorldTransform[1][1];
    imageTransform[2][1] = imageToWorldTransform[2][1];
    imageTransform[0][2] = imageToWorldTransform[0][2];
    imageTransform[1][2] = imageToWorldTransform[1][2];
    imageTransform[2][2] = imageToWorldTransform[2][2];
    imageTransform[0][3] = imageToWorldTransform[0][3];
    imageTransform[1][3] = imageToWorldTransform[1][3];
    imageTransform[2][3] = imageToWorldTransform[2][3];


    MatrixType ZFrameBaseOrientation;
    ZFrameBaseOrientation.SetIdentity();
    
    // ZFrame base orientation
    zf::Matrix4x4 ZmatrixBase;
    ZmatrixBase[0][0] = (float) ZFrameBaseOrientation[0][0];
    ZmatrixBase[1][0] = (float) ZFrameBaseOrientation[1][0];
    ZmatrixBase[2][0] = (float) ZFrameBaseOrientation[2][0];
    ZmatrixBase[0][1] = (float) ZFrameBaseOrientation[0][1];
    ZmatrixBase[1][1] = (float) ZFrameBaseOrientation[1][1];
    ZmatrixBase[2][1] = (float) ZFrameBaseOrientation[2][1];
    ZmatrixBase[0][2] = (float) ZFrameBaseOrientation[0][2];
    ZmatrixBase[1][2] = (float) ZFrameBaseOrientation[1][2];
    ZmatrixBase[2][2] = (float) ZFrameBaseOrientation[2][2];
    ZmatrixBase[0][3] = (float) ZFrameBaseOrientation[0][3];
    ZmatrixBase[1][3] = (float) ZFrameBaseOrientation[1][3];
    ZmatrixBase[2][3] = (float) ZFrameBaseOrientation[2][3];
    
    // Convert Base Matrix to quaternion
    float ZquaternionBase[4];
    zf::MatrixToQuaternion(ZmatrixBase, ZquaternionBase);
    
    // Set slice range
    int range[2];
    range[0] = startSlice;
    range[1] = endSlice;
    
    float Zposition[3];
    float Zorientation[4];
    
    // Call Z-frame registration
    // zf::Registration * registration;
    // registration = new zf::Registration();
    
    int dim[3];
    dim[0] = dimensions[0];
    dim[1] = dimensions[1];
    dim[2] = dimensions[2];
    int r = -1;
    bool manualRegistration = false;

    // std::cout << "zframeConfig: " << zframeConfig << std::endl;
    // std::cout << "Frame topology: " << frameTopology << std::endl;
    // std::cout << "zFrameFids: " << zFrameFids << std::endl;

    // Convert frameTopology string back into an array of floats
    float frameTopologyArr[6][3];
    float x, y, z;
    std::string substring, z_substr;
    size_t pos, pos_start, pos_end = 0;

    int numFids = 0;
    if (zframeConfig == "z001") { numFids = 7; }
    else if (zframeConfig == "z002" || zframeConfig == "z003") { numFids = 9; }
    //float zFrameFidsArr[numFids][2];
	auto zFrameFidsArr = new float[numFids][2];

    for (int i = 0; i <= 5; ++i)
    {
        pos_start = frameTopology.find("["); 
        pos_end = frameTopology.find("]"); 
        substring = frameTopology.substr(pos_start + 1, pos_end);
        frameTopology.erase(0, pos_end + 1); // Erase the first occurence from frameTopology string

        // std::cout << "frameTopology: " << frameTopology << std::endl;
        // std::cout << "substring: " << substring << std::endl;

        // Separate the substring at the commas twice and use std::stof() to convert the string to float to find x, y, and z
        pos = substring.find(",");
        x = std::stof(substring.substr(0, pos));
        substring.erase(0, pos + 1);

        pos = substring.find(",");
        y = std::stof(substring.substr(0, pos));
        z = std::stof(substring.erase(0, pos + 2 ));

        frameTopologyArr[i][0] = x;
        frameTopologyArr[i][1] = y;
        frameTopologyArr[i][2] = z;
    }
    // Final result is stored in frameTopologyArr[6][3]
    // The first 3 rows contain the origin points in RAS coordinates of Side 1, Base, and Side 2, respectively. 
    // The 4th, 5th, and 6th rows contain the diagonal vectors in RAS coordinates of Side 1, Base, and Side 2.

    // If zFrameFidsString is not empty, then the user manually selected points to use in registration. 
    // Convert zFrameFidsString back into an array of floats for use in the registration algorithm
    if (zFrameFids.length() > 1)
    {   
        manualRegistration = true;
        for (int i = 0; i < numFids; ++i)
        {
            pos_start = zFrameFids.find("["); 
            pos_end = zFrameFids.find("]"); 
            substring = zFrameFids.substr(pos_start + 1, pos_end);
            zFrameFids.erase(0, pos_end + 1); // Erase the first occurence from frameTopology string

            // Separate the substring at the commas twice and use std::stof() to convert the string to float to find x, y, and z
            pos = substring.find(",");
            x = std::stof(substring.substr(0, pos));
            substring.erase(0, pos + 1);

            pos = substring.find(",");
            // y = std::stof(substring.substr(0, pos));
            y = std::stof(substring.substr(0, pos));
            // z = std::stof(substring.erase(0, pos + 2 ));

            zFrameFidsArr[i][0] = x;
            zFrameFidsArr[i][1] = y;
            // zFrameFidsArr[i][2] = z;

            std::cout << "zFrameFidsArr: " << zFrameFidsArr[i][0] << ", " << zFrameFidsArr[i][1] << std::endl;
        }
    }

    // Toggle registration algorithm based on zframe configuration (currently, only z001 [7 fid], z002 [9 fid], z003 [9fid], and z004 [7fid])
    if (zframeConfig == "z001" || zframeConfig == "z004" || zframeConfig == "z005")
    {
        // Zframe z001 is a 7-fiducial frame; run the 7-fiducial registration [Namespace zf_7fid]
        // Zframe z004 is a 7-fiducial frame; run the 7-fiducial registration [Namespace zf_7fid]
        zf_7fid::Registration * registration;
        registration = new zf_7fid::Registration();
        
        registration->SetInputImage(image->GetBufferPointer(), dim, imageTransform);
        registration->SetOrientationBase(ZquaternionBase);
        registration->SetFrameTopology(frameTopologyArr);
        if (manualRegistration) { registration->SetManualZFrameFiducials(zFrameFidsArr, manualRegistration); }
        else { registration->SetAutomaticRegistration(manualRegistration); }
        r = registration->Register(range, Zposition, Zorientation);
        
        delete registration;
        cout << r << endl;
    }
    else if (zframeConfig == "z002" || zframeConfig == "z003")
    {
        // Zframe z002 is a 9-fiducial frame with the base Z on the top; run the 9-fiducial registration with baseLocation "top" [Namespace zf_9fid]
        // Zframe z003 is a 9-fiducial frame with the base Z on the bottom; run the 9-fiducial registration with baseLocation "bottom" [Namespace zf_9fid]
        zf_9fid::Registration * registration;
        registration = new zf_9fid::Registration();

        if (zframeConfig == "z002") { registration->SetBaseLocation("top"); }
        else if (zframeConfig == "z003") { registration->SetBaseLocation("bottom"); }
        registration->SetInputImage(image->GetBufferPointer(), dim, imageTransform);
        registration->SetOrientationBase(ZquaternionBase);
        registration->SetFrameTopology(frameTopologyArr);
        if (manualRegistration) { registration->SetManualZFrameFiducials(zFrameFidsArr, manualRegistration); }
        else { registration->SetAutomaticRegistration(manualRegistration); }
        r = registration->Register(range, Zposition, Zorientation);
        
        delete registration;
        cout << r << endl;
    }
    else
    {
        std::cout << "Invalid z-frame configuration. Cannot run registration algorithm." << std::endl;
        return EXIT_FAILURE ;
    }
    
    //registration->SetInputImage(image->GetBufferPointer(), dim, imageTransform);
    //registration->SetOrientationBase(ZquaternionBase);
    // int r = registration->Register(range, Zposition, Zorientation);
    
    // delete registration;
    
    // cout << r << endl;
    
    if (r)
    {
        // Convert quaternion to matrix
        zf::Matrix4x4 matrix;
        zf::QuaternionToMatrix(Zorientation, matrix);

        MatrixType zMatrix;
        zMatrix.SetIdentity();
        zMatrix[0][0] = matrix[0][0];
        zMatrix[1][0] = matrix[1][0];
        zMatrix[2][0] = matrix[2][0];
        zMatrix[0][1] = matrix[0][1];
        zMatrix[1][1] = matrix[1][1];
        zMatrix[2][1] = matrix[2][1];
        zMatrix[0][2] = matrix[0][2];
        zMatrix[1][2] = matrix[1][2];
        zMatrix[2][2] = matrix[2][2];
        zMatrix[0][3] = Zposition[0];
        zMatrix[1][3] = Zposition[1];
        zMatrix[2][3] = Zposition[2];

        cout << "RAS Transformation Matrix:" << endl;
        cout << zMatrix << endl;
        
        zMatrix = zMatrix * lps2RasTransformMatrix;
        zMatrix = (MatrixType)zMatrix.GetInverse() * lps2RasTransformMatrix;

        
        typedef itk::Matrix<double, 3, 3> TransformMatrixType;
        TransformMatrixType lpsTransformMatrix;
        lpsTransformMatrix.SetIdentity();
        lpsTransformMatrix[0][0] = zMatrix[0][0];
        lpsTransformMatrix[1][0] = zMatrix[1][0];
        lpsTransformMatrix[2][0] = zMatrix[2][0];
        lpsTransformMatrix[0][1] = zMatrix[0][1];
        lpsTransformMatrix[1][1] = zMatrix[1][1];
        lpsTransformMatrix[2][1] = zMatrix[2][1];
        lpsTransformMatrix[0][2] = zMatrix[0][2];
        lpsTransformMatrix[1][2] = zMatrix[1][2];
        lpsTransformMatrix[2][2] = zMatrix[2][2];
        
        typedef itk::AffineTransform<double> RegistrationTransformType;
        RegistrationTransformType::OutputVectorType translation;
        translation[0] = zMatrix[0][3];
        translation[1] = zMatrix[1][3];
        translation[2] = zMatrix[2][3];
        
        typedef itk::AffineTransform<double, 3> TransformType;
        TransformType::Pointer transform = TransformType::New();
        transform->SetMatrix(lpsTransformMatrix);
        transform->SetTranslation(translation);
        
        if (outputTransform != "")
        {
            itk::TransformFileWriter::Pointer markerTransformWriter = itk::TransformFileWriter::New();
            markerTransformWriter->SetInput(transform);
            markerTransformWriter->SetFileName(outputTransform.c_str());
            try
            {
                markerTransformWriter->Update();
            }
            catch (itk::ExceptionObject &err)
            {
                std::cerr << err << std::endl;
                return EXIT_FAILURE ;
            }
            
        }
    }
    
    return EXIT_SUCCESS;
}
