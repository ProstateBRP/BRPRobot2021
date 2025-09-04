classdef Kinematics < handle
    %PROSTATEKINEMATICS_MATLAB Prostate surgery robot kinematics calculation class
    %   This class implements forward and inverse kinematics for the prostate
    %   surgery robot based on the C++ implementation
    
    properties (Constant)
        RADIAN_TO_DEGREE = 57.29578;
        % Robot Specific Parameters (from C++ implementation)
        lengthTrapSideLink = 124.0;        % L
        widthTrapTop = 84.0;               % B
        heightLowerTrapOffset = 12.0;      % H1
        heightUpperTrapOffset = 67.5;      % H2
        lengthNeedleTipOffset = 205.0;     % Zoffset
        distanceBetweenTraps = 181.5;      % D
    end
    
    properties
        % Values that update with motion
        xFrontPointOfRotation
        yFrontPointOfRotation
        zFrontPointOfRotation
        xRearPointOfRotation
        yRearPointOfRotation
        zRearPointOfRotation
        
        % Angulation Variables
        C   % Distance between point of rotation and center of front trapezoid stage in Z-direction
        h   % Distance between needle's direction and center of front trapezoid stage in vertical direction
    end
    
    methods
        function obj = Kinematics()
            % Initialize motion variables
            obj.xFrontPointOfRotation = 0.0;
            obj.yFrontPointOfRotation = 0.0;
            obj.zFrontPointOfRotation = 0.0;
            obj.xRearPointOfRotation = 0.0;
            obj.yRearPointOfRotation = 0.0;
            obj.zRearPointOfRotation = 0.0;
            
            % Angulation Variables
            obj.C = 0.0;
            obj.h = 0.0;
        end
        
        function FK = ForwardKinematics(obj, xFrontSlider1, xFrontSlider2, xRearSlider1, xRearSlider2, zInsertion, NeedleT)
            %FORWARDKINEMATICS Calculate forward kinematics
            %   Inputs:
            %       xFrontSlider1, xFrontSlider2 - Front left and right slider positions
            %       xRearSlider1, xRearSlider2   - Rear left and right slider positions
            %       zInsertion                   - Needle insertion depth
            %   Output:
            %       FK - Structure containing forward kinematics results
            
            % Initialize output structure
            FK = struct();
            
            %*** BASE FORWARD KINEMATICS ***%
            obj.xFrontPointOfRotation = (xFrontSlider1 + xFrontSlider2) / 2;
            
            yF_1 = obj.heightLowerTrapOffset + obj.heightUpperTrapOffset;
            yF_2 = obj.lengthTrapSideLink^2;
            yF_3 = ((xFrontSlider1 - xFrontSlider2 - obj.widthTrapTop) / 2)^2;
            
            % Check if calculation is valid
            if yF_2 - yF_3 < 0
                error('Invalid slider positions: outside workspace limits');
            end
            
            obj.yFrontPointOfRotation = yF_1 + sqrt(yF_2 - yF_3);
            obj.zFrontPointOfRotation = -obj.C;
            
            obj.xRearPointOfRotation = (xRearSlider1 + xRearSlider2) / 2;
            yR_1 = obj.heightLowerTrapOffset + obj.heightUpperTrapOffset;
            yR_2 = obj.lengthTrapSideLink^2;
            yR_3 = ((xRearSlider1 - xRearSlider2 - obj.widthTrapTop) / 2)^2;
            
            % Check if calculation is valid
            if yR_2 - yR_3 < 0
                error('Invalid slider positions: outside workspace limits');
            end
            
            obj.yRearPointOfRotation = yR_1 + sqrt(yR_2 - yR_3);
            obj.zRearPointOfRotation = 0;
            % Alpha is the yaw angle of the needle tip relative to an imaginary straight insertion line
            alpha = atan2(obj.xFrontPointOfRotation - obj.xRearPointOfRotation, obj.distanceBetweenTraps);

            % Beta is the pitch angle of the needle tip relative to an imaginary straight insertion line
            beta = atan2(obj.yRearPointOfRotation - obj.yFrontPointOfRotation, obj.distanceBetweenTraps);
            
            % Rotation matrices
            rotationBaseToTipYaw = [cos(alpha), 0, sin(alpha);
                                   0, 1, 0;
                                   -sin(alpha), 0, cos(alpha)];
            
            rotationBaseToTipPitch = [1, 0, 0;
                                     0, cos(beta), -sin(beta);
                                     0, sin(beta), cos(beta)];
            
            rotationBaseToTip = rotationBaseToTipYaw * rotationBaseToTipPitch;
            
            % Calculate needle tip position
            FK.xNeedleBase = ((obj.lengthNeedleTipOffset + zInsertion) * cos(beta) * sin(alpha)) + ...
                           (obj.h * sin(beta) * sin(alpha)) + obj.xFrontPointOfRotation;
            
            FK.yNeedleTip = (obj.h * cos(beta)) - ...
                           ((obj.lengthNeedleTipOffset + zInsertion) * sin(beta)) + obj.yFrontPointOfRotation;
            
            FK.zNeedleTip = ((obj.lengthNeedleTipOffset + zInsertion) * cos(beta) * cos(alpha)) + ...
                           (obj.h * sin(beta) * cos(alpha)) + obj.zFrontPointOfRotation;
            
            % Base to treatment transformation matrix
            FK.BaseToTreatment = eye(4);
            FK.BaseToTreatment(1:3, 1:3) = rotationBaseToTip;
            FK.BaseToTreatment(1:3, 4) = [FK.xNeedleBase; FK.yNeedleTip; FK.zNeedleTip];
            
            % Additional outputs for convenience
            FK.needleBase = [FK.xNeedleBase; FK.yNeedleTip; FK.zNeedleTip];
            FK.frontRotationCenter = [obj.xFrontPointOfRotation; obj.yFrontPointOfRotation; obj.zFrontPointOfRotation];
            FK.rearRotationCenter = [obj.xRearPointOfRotation; obj.yRearPointOfRotation; obj.zRearPointOfRotation];
            FK.alphaDeg = alpha * obj.RADIAN_TO_DEGREE;
            FK.betaDeg = beta * obj.RADIAN_TO_DEGREE;
            FK.alphaRad = alpha;
            FK.betaRad = beta;
            FK.rotationMatrix = rotationBaseToTip;
            FK.frontSliders = [xFrontSlider1; xFrontSlider2];
            FK.rearSliders = [xRearSlider1; xRearSlider2];
            FK.insertion = zInsertion;
            FK.NeedleTip = FK.BaseToTreatment * NeedleT;
        end
        
        function IK = InverseKinematics(obj, TargetPose)
            %INVERSEKINEMATICS Calculate inverse kinematics
            %   Input:
            %       TargetPose - 4x4 homogeneous transformation matrix
            %   Output:
            %       IK - Structure containing inverse kinematics results
            
            % Initialize output structure
            IK = struct();
            
            % Calculate Alpha and Beta values based on the target pose
            alpha = atan2(-TargetPose(3, 1), TargetPose(1, 1));
            beta = atan2(-TargetPose(2, 3), TargetPose(2, 2));
            
            % Calculate the insertion value
            IK.zInsertion = ((TargetPose(3, 4) - (obj.h * sin(beta) * cos(alpha))) / ...
                            (cos(beta) * cos(alpha))) - obj.lengthNeedleTipOffset;
            
            % Calculate the coordinate of the front point of rotation
            xFrontPointOfRotationDesired = TargetPose(1, 4) - ...
                                          (((obj.lengthNeedleTipOffset + IK.zInsertion) * cos(beta) * sin(alpha)) + ...
                                           (obj.h * sin(beta) * sin(alpha)));
            
            yFrontPointOfRotationDesired = TargetPose(2, 4) - ...
                                          ((obj.h * cos(beta)) - ...
                                           ((obj.lengthNeedleTipOffset + IK.zInsertion) * sin(beta)));
            
            % Calculating front right and left slider amounts
            frontHeight = yFrontPointOfRotationDesired - (obj.heightLowerTrapOffset + obj.heightUpperTrapOffset);
            
            % Check if calculation is valid
            if obj.lengthTrapSideLink^2 - frontHeight^2 < 0
                error('Target position outside workspace: front stage');
            end
            
            x1_f = 2 * xFrontPointOfRotationDesired;                                            % Front Left Leg
            x2_f = (2 * sqrt(obj.lengthTrapSideLink^2 - frontHeight^2)) + obj.widthTrapTop;   % Front Right Leg
            
            % Solving a 2 equation 2 unknown using A*X = B -> X = A\B
            rightHandSide_f = [x1_f; x2_f];
            coefficientMatrix = [1, 1; 1, -1];
            solutionMatrix_f = coefficientMatrix \ rightHandSide_f;
            IK.xFrontSlider1 = solutionMatrix_f(1);
            IK.xFrontSlider2 = solutionMatrix_f(2);
            
            % Calculate the coordinate of the rear point of rotation
            xRearPointOfRotationDesired = TargetPose(1, 4) - ...
                                         (((obj.lengthNeedleTipOffset + IK.zInsertion + obj.distanceBetweenTraps) * cos(beta) * sin(alpha)) + ...
                                          (obj.h * sin(beta) * sin(alpha)));
            
            yRearPointOfRotationDesired = TargetPose(2, 4) - ...
                                         ((obj.h * cos(beta)) - ...
                                          ((obj.lengthNeedleTipOffset + IK.zInsertion + obj.distanceBetweenTraps) * sin(beta)));
            
            % Calculating rear right and left slider amounts
            rearHeight = yRearPointOfRotationDesired - (obj.heightLowerTrapOffset + obj.heightUpperTrapOffset);
            
            % Check if calculation is valid
            if obj.lengthTrapSideLink^2 - rearHeight^2 < 0
                error('Target position outside workspace: rear stage');
            end
            
            x1_r = 2 * xRearPointOfRotationDesired;                                           % Rear Left Leg
            x2_r = (2 * sqrt(obj.lengthTrapSideLink^2 - rearHeight^2)) + obj.widthTrapTop;  % Rear Right Leg
            
            % Solving a 2 equation 2 unknown using A*X = B -> X = A\B
            rightHandSide_r = [x1_r; x2_r];
            solutionMatrix_r = coefficientMatrix \ rightHandSide_r;
            IK.xRearSlider1 = solutionMatrix_r(1);
            IK.xRearSlider2 = solutionMatrix_r(2);
            
            IK.zRotation = 0; % FROM OPENIGTLINKTRACKING
            
            % Additional outputs
            IK.alphaDeg = alpha * obj.RADIAN_TO_DEGREE;
            IK.betaDeg = beta * obj.RADIAN_TO_DEGREE;
            IK.alphaRad = alpha;
            IK.betaRad = beta;
        end
        
        function angulation = GetAngulation(obj, xFrontSlider1, xFrontSlider2, xRearSlider1, xRearSlider2)
            %GETANGULATION Calculate alpha and beta angles from slider positions
            %   Returns: [alpha_deg, beta_deg]
            
            obj.xFrontPointOfRotation = (xFrontSlider1 + xFrontSlider2) / 2;
            
            yF_1 = obj.heightLowerTrapOffset + obj.heightUpperTrapOffset;
            yF_2 = obj.lengthTrapSideLink^2;
            yF_3 = ((xFrontSlider1 - xFrontSlider2 - obj.widthTrapTop) / 2)^2;
            
            if yF_2 - yF_3 < 0
                error('Invalid slider positions: outside workspace limits');
            end
            
            obj.yFrontPointOfRotation = yF_1 + sqrt(yF_2 - yF_3);
            obj.zFrontPointOfRotation = -obj.C;
            
            obj.xRearPointOfRotation = (xRearSlider1 + xRearSlider2) / 2;
            yR_1 = obj.heightLowerTrapOffset + obj.heightUpperTrapOffset;
            yR_2 = obj.lengthTrapSideLink^2;
            yR_3 = ((xRearSlider1 - xRearSlider2 - obj.widthTrapTop) / 2)^2;
            
            if yR_2 - yR_3 < 0
                error('Invalid slider positions: outside workspace limits');
            end
            
            obj.yRearPointOfRotation = yR_1 + sqrt(yR_2 - yR_3);
            
            % Alpha is the yaw angle of the needle tip relative to an imaginary straight insertion line
            alpha = atan2(obj.xFrontPointOfRotation - obj.xRearPointOfRotation, obj.distanceBetweenTraps);
            alpha_deg = alpha * obj.RADIAN_TO_DEGREE;
            
            % Beta is the pitch angle of the needle tip relative to an imaginary straight insertion line
            beta = atan2(obj.yRearPointOfRotation - obj.yFrontPointOfRotation, obj.distanceBetweenTraps);
            beta_deg = beta * obj.RADIAN_TO_DEGREE;
            
            angulation = [alpha_deg, beta_deg];
        end
        
        function isValid = CheckWorkspaceLimits(obj, xFrontSlider1, xFrontSlider2, xRearSlider1, xRearSlider2)
            %CHECKWORKSPACELIMITS Check if slider positions are within workspace limits
            
            % Check physical limits of slider differences
            frontDiff = abs(xFrontSlider1 - xFrontSlider2 - obj.widthTrapTop) / 2;
            rearDiff = abs(xRearSlider1 - xRearSlider2 - obj.widthTrapTop) / 2;
            
            maxDiff = obj.lengthTrapSideLink - 10; % Safety margin
            
            isValid = frontDiff < maxDiff && rearDiff < maxDiff;
        end
        
        function plotRobot(obj, xFrontSlider1, xFrontSlider2, xRearSlider1, xRearSlider2, zInsertion, figureHandle)
            %PLOTROBOT Plot the robot configuration
            
            if nargin < 7
                figureHandle = figure();
            end
            
            figure(figureHandle);
            clf;
            
            try
                FK = obj.ForwardKinematics(xFrontSlider1, xFrontSlider2, xRearSlider1, xRearSlider2, zInsertion);
                
                % Plot setup
                hold on;
                grid on;
                axis equal;
                xlabel('X [mm]');
                ylabel('Y [mm]');
                zlabel('Z [mm]');
                title('Prostate Surgery Robot Configuration');
                
                % Set axis limits
                xlim([-150, 150]);
                ylim([0, 350]);
                zlim([-100, 450]);
                
                % Draw base frame
                obj.drawBaseFrame();
                
                % Draw trapezoid stages
                obj.drawTrapezoidStage(FK.frontRotationCenter, [xFrontSlider1, xFrontSlider2], 'b', 'Front Stage');
                rearCenter = FK.rearRotationCenter;
                rearCenter(3) = rearCenter(3) + obj.distanceBetweenTraps;
                obj.drawTrapezoidStage(rearCenter, [xRearSlider1, xRearSlider2], 'g', 'Rear Stage');
                
                % Draw connection between stages
                plot3([FK.frontRotationCenter(1), FK.rearRotationCenter(1)], ...
                      [FK.frontRotationCenter(2), FK.rearRotationCenter(2)], ...
                      [FK.frontRotationCenter(3), rearCenter(3)], ...
                      'k-', 'LineWidth', 3, 'DisplayName', 'Connection');
                
                % Draw needle
                obj.drawNeedle(FK.frontRotationCenter, FK.needleTip);
                
                % Draw coordinate frame at needle tip
                obj.drawCoordinateFrame(FK.needleTip, FK.rotationMatrix, 30);
                
                legend('show');
                view(45, 20);
                
            catch ME
                fprintf('Error plotting robot: %s\n', ME.message);
                text(0, 100, 200, 'Error: Outside Workspace', 'FontSize', 16, 'Color', 'red', 'HorizontalAlignment', 'center');
            end
        end
    end
    
    methods (Access = private)
        function drawBaseFrame(obj)
            %DRAWBASEFRAME Draw robot base frame
            baseSize = 80;
            baseVertices = [-baseSize, 0, -50;
                           baseSize, 0, -50;
                           baseSize, 0, 400;
                           -baseSize, 0, 400;
                           -baseSize, 0, -50];
            plot3(baseVertices(:, 1), baseVertices(:, 2), baseVertices(:, 3), 'k-', 'LineWidth', 2, 'DisplayName', 'Base Frame');
        end
        
        function drawTrapezoidStage(obj, center, sliders, color, label)
            %DRAWTRAPEZOIDSTAGE Draw trapezoid stage
            width = obj.widthTrapTop;
            
            % Four leg positions of trapezoid
            leftLegX = sliders(1);
            rightLegX = sliders(2);
            
            % Top vertices of trapezoid
            topLeft = [center(1) - width/2, center(2), center(3)];
            topRight = [center(1) + width/2, center(2), center(3)];
            
            % Bottom leg positions
            bottomLeft = [leftLegX, obj.heightLowerTrapOffset, center(3)];
            bottomRight = [rightLegX, obj.heightLowerTrapOffset, center(3)];
            
            % Draw trapezoid
            trapezoidVertices = [bottomLeft; topLeft; topRight; bottomRight; bottomLeft];
            plot3(trapezoidVertices(:, 1), trapezoidVertices(:, 2), trapezoidVertices(:, 3), ...
                  'Color', color, 'LineWidth', 3, 'DisplayName', label);
            
            % Draw links
            plot3([bottomLeft(1), topLeft(1)], [bottomLeft(2), topLeft(2)], [bottomLeft(3), topLeft(3)], ...
                  'Color', color, 'LineWidth', 4);
            plot3([bottomRight(1), topRight(1)], [bottomRight(2), topRight(2)], [bottomRight(3), topRight(3)], ...
                  'Color', color, 'LineWidth', 4);
            
            % Mark center point and slider positions
            scatter3(center(1), center(2), center(3), 150, color, 'o', 'filled');
            scatter3([leftLegX, rightLegX], [bottomLeft(2), bottomRight(2)], [center(3), center(3)], ...
                    100, color, 's', 'filled');
        end
        
        function drawNeedle(obj, startPoint, endPoint)
            %DRAWNEEDLE Draw needle
            plot3([startPoint(1), endPoint(1)], [startPoint(2), endPoint(2)], [startPoint(3), endPoint(3)], ...
                  'r-', 'LineWidth', 6, 'DisplayName', 'Needle');
            scatter3(endPoint(1), endPoint(2), endPoint(3), 200, 'r', '^', 'filled', 'DisplayName', 'Needle Tip');
        end
        
        function drawCoordinateFrame(obj, origin, rotationMatrix, scale)
            %DRAWCOORDINATEFRAME Draw coordinate frame
            if nargin < 4
                scale = 30;
            end
            
            % X-axis (red)
            xEnd = origin + rotationMatrix(:, 1) * scale;
            plot3([origin(1), xEnd(1)], [origin(2), xEnd(2)], [origin(3), xEnd(3)], 'r-', 'LineWidth', 3);
            
            % Y-axis (green)
            yEnd = origin + rotationMatrix(:, 2) * scale;
            plot3([origin(1), yEnd(1)], [origin(2), yEnd(2)], [origin(3), yEnd(3)], 'g-', 'LineWidth', 3);
            
            % Z-axis (blue)
            zEnd = origin + rotationMatrix(:, 3) * scale;
            plot3([origin(1), zEnd(1)], [origin(2), zEnd(2)], [origin(3), zEnd(3)], 'b-', 'LineWidth', 3);
        end
    end
end
