%% Receiver function example
function testSendMessage()
    clc; close all;

    % Start connection
    igtlConnection = igtlConnect('127.0.0.1',18944);
    sender = OpenIGTLinkMessageSender(igtlConnection);
    
    % Send a STRING message
    msg = 'Hello World!';
    sender.WriteOpenIGTLinkStringMessage('StringTest', msg);

    % Send a STRING message
    status = struct('code', 13, 'subCode', 0, 'errorName', 'none', 'message', 'STATUS_OK');
    sender.WriteOpenIGTLinkStatusMessage('StatusTest', status);  

    % Send a TRANSFORM message
    theta = 0; translation = [1.0, 2.0, 3.0];
    matrix = [cos(theta), -sin(theta), 0, translation(1);
              sin(theta), cos(theta),  0, translation(2);
              0,          0,           1, translation(3);
              0,          0,           0, 1];
    sender.WriteOpenIGTLinkTransformMessage('TransformTest', matrix);

    % Send POINT messages
    pointList_F = [1.0, 2.0, 3.0;
                   4.0, 5.0, 6.0;
                   7.0, 8.0, 9.0];
    sender.WriteOpenIGTLinkPointMessage('F', pointList_F);

    pointList_P = [-20, -15, -10;  
    	           -20, -15,  10;  
    	           -20,  15, -10; 
    	           -20,  15,  10;  
    	            20, -15, -10;  
    	            20, -15,  10;  
    	            20,  15, -10;  
    	            20,  15,  10];  

    sender.WriteOpenIGTLinkPointMessage('P', pointList_P);
    
    % Send image
    % IMAGE 1 - RTDose example image (already in RAS) - int32
    load('../RTDose.mat', 'dose_image');   % Load image varible
    igtlShowImage(dose_image, 1);       % Show slice 1
    sender.WriteOpenIGTLinkImageMessage('IMAGE_1', dose_image);

    % IMAGE 2 - Matlab generated image
    width = 320; height = 240; depth = 5;
    N = round(height / 4);
    base_gradient = uint16(repmat(linspace(0, 65535, width), height, 1));
    imageLPS.matrix = repmat(base_gradient, 1, 1, depth);
    for d = 1:depth
        shade_value = uint16(65535 * (1 - (d - 1) / (depth - 1)));  % Decreasing shade
        imageLPS.matrix(1:N, 1:N, d) = shade_value;                 % Assign to slice d
    end
    imageLPS.coordinate = 2;    %(1:RAS, 2:LPS)
    imageRAS.matrix  = convert2RAS(imageLPS.matrix); % Matlab is LPS: Convert to RAS (3D Slicer standard)
    imageRAS.coordinate = 1;    %(1:RAS, 2:LPS)
    igtlShowImage(imageRAS, 1); % Show slice 1
    sender.WriteOpenIGTLinkImageMessage('IMAGE_2', imageRAS);
   
    % Close connection
    igtlDisconnect(igtlConnection);
end

% Convert LPS (Matlab arrays) to RAS (3D Slicer standard)
function imageRAS = convert2RAS(imageLPS)
    imageRAS  = rot90(imageLPS);   % Rotate 90° to align with RAS standard
    imageRAS  = fliplr(imageRAS);  % Flip Left-Right for RAS
end