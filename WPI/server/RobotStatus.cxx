/*=========================================================================

  Program:   BRP Prostate Robot: Testing Simulator (Robot)
  Language:  C++

  Copyright (c) Brigham and Women's Hospital. All rights reserved.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

  Please see
    http://wiki.na-mic.org/Wiki/index.php/ProstateBRP_OpenIGTLink_Communication_June_2013
  for the detail of the testing protocol.

=========================================================================*/

#include "RobotStatus.h"
#include "igtlMath.h"

RobotStatus::RobotStatus()
{
  igtl::IdentityMatrix(this->CalibrationMatrix);
  igtl::IdentityMatrix(this->TargetMatrix);
  this->FlagCalibration = 0;
  this->FlagTarget = 0;
}

RobotStatus::~RobotStatus()
{
}

void RobotStatus::SetCalibrationMatrix(igtl::Matrix4x4& matrix)
{
  this->FlagCalibration = 1;
  for (int i = 0; i < 4; i ++)
    {
    for (int j = 0; j < 4; j ++)
      {
      this->CalibrationMatrix[i][j] = matrix[i][j];
      }
    }
}

int RobotStatus::GetCalibrationMatrix(igtl::Matrix4x4& matrix)
{
  if (this->FlagCalibration)
    {
    for (int i = 0; i < 4; i ++)
      {
      for (int j = 0; j < 4; j ++)
        {
        matrix[i][j] = this->CalibrationMatrix[i][j];
        }
      }
    return 1;
    }
  else
    {
    return 0;
    }
}


void RobotStatus::SetTargetMatrix(igtl::Matrix4x4& matrix)
{
  this->FlagTarget = 1;

  for (int i = 0; i < 4; i ++)
    {
    for (int j = 0; j < 4; j ++)
      {
      this->TargetMatrix[i][j] = matrix[i][j];
      }
    }

}


int RobotStatus::GetTargetMatrix(igtl::Matrix4x4& matrix)
{
  if (this->FlagTarget)
    {
    for (int i = 0; i < 4; i ++)
      {
      for (int j = 0; j < 4; j ++)
        {
        matrix[i][j] = this->TargetMatrix[i][j];
        }
      }
    return 1;
    }
  else
    {
    return 0;
    }
}

