% OpenIGTLink server that executes the received string commands
function receiver = OpenIGTLinkMessageReceiver(sock, onRxStatusMsg, onRxStringMsg, onRxTransformMsg, onRxPointMsg, onRxImageMsg)
    global onRxStatusMessage onRxStringMessage onRxTransformMessage onRxPointMessage onRxImageMessage;
    global socket;
    global timeout;
    onRxStatusMessage = onRxStatusMsg;
    onRxStringMessage = onRxStringMsg;
    onRxTransformMessage = onRxTransformMsg;
    onRxPointMessage = onRxPointMsg;
    onRxImageMessage = onRxImageMsg;
    socket = sock;
    timeout = 500000;
    receiver.readMessage = @readMessage;
    receiver.readCommandMessage = @readCommandMessage;
end

% Process message content. Handle message content according with their types
function [name, type, data] = readMessage()
    global onRxStatusMessage onRxStringMessage onRxTransformMessage onRxPointMessage onRxImageMessage;
    msg = ReadOpenIGTLinkMessage();
    messageType = char(msg.dataTypeName);
    messageType = deblank(messageType);
    type = messageType;
    if strcmpi(messageType, 'STATUS')
        [name, data] = handleStatusMessage(msg, onRxStatusMessage);
    elseif strcmpi(messageType, 'STRING')
        [name, data] = handleStringMessage(msg, onRxStringMessage);
    elseif strcmpi(messageType, 'TRANSFORM')
        [name, data] = handleTransformMessage(msg, onRxTransformMessage);
    elseif strcmpi(messageType, 'POINT')
        [name, data] = handlePointMessage(msg, onRxPointMessage);
    elseif strcmpi(messageType, 'IMAGE')
        [name, data] = handleImageMessage(msg, onRxImageMessage);
    else
        disp(['Currently unsupported message type:', messageType])
    end
end

% Process message content. Handle message content according with their types
function [name, data] = readCommandMessage()
    global onRxStringMessage;
    msg = ReadOpenIGTLinkMessage();
    messageType = char(msg.dataTypeName);
    messageType = deblank(messageType);
    if strcmpi(messageType, 'STRING')
        [name, data] = handleStringMessage(msg, onRxStringMessage);
    else
        disp(['Unexpected message type:', messageType])
    end
end


%% Message content decoding (type specific)

% STATUS Message content
% Obs: 3DSlicer is currently sending all zero bytes status messages (code = 0 - invalid packet)
% Commented out message parsing for that reason
function [name, message] = handleStatusMessage(msg, onRxStatusMessage)
    if (length(msg.content)<30)
        disp('Error: STATUS message received with incomplete contents')
        return
    end
    code = convertUint8Vector(msg.content(1:2), 'uint16');
    subCode = convertUint8Vector(msg.content(3:10), 'int64');
    errorName = char(msg.content(11:30));
    message = char(msg.content(31:length(msg.content)));
    name = msg.deviceName;
    onRxStatusMessage(name, message);
end

% STRING Message content
function [name, message] = handleStringMessage(msg, onRxStringMessage)
    if (length(msg.content)<5)
        disp('Error: STRING message received with incomplete contents')
        msg.string='';
        return
    end
    strMsgEncoding = convertUint8Vector(msg.content(1:2), 'uint16');
    if (strMsgEncoding~=3)
        disp(['Warning: STRING message received with unknown encoding ',num2str(strMsgEncoding)])
    end
    strMsgLength = convertUint8Vector(msg.content(3:4), 'uint16');
    message = char(msg.content(5:4+strMsgLength));
    name = msg.deviceName;
    onRxStringMessage(name, message);
end

% TRANSFORM Message content
function [name, transform] = handleTransformMessage(msg, onRxTransformMessage)
    transform = diag([1 1 1 1]);
    k=1;
    for i=1:4
        for j=1:3
            transform(j,i) = convertUint8Vector(msg.content(4*(k-1) +1:4*k), 'single');
            k = k+1;
        end
    end
    name = msg.deviceName;
    onRxTransformMessage(name , transform);
end

% POINT Message
function [name, pointList] = handlePointMessage(msg, onRxPointMessage)
    pointDataSize = 136;
    numPoints = floor((length(msg.content))/pointDataSize);
    % Preallocate structure array
    points(numPoints) = struct('name', '', 'group', '', 'RGBA', [], 'XYZ', [], 'diameter', [], 'owner', ''); 
    pointList = zeros(numPoints, 3);
    for i = 1:numPoints
        % Compute offset for this point
        offset = (i-1) * pointDataSize; 
        % Extract data using the computed offset
        points(i).name = char(msg.content(offset + (1:64)));  % Name field (64 bytes)
        points(i).group = char(msg.content(offset + (65:96))); % Group field (32 bytes)
        points(i).RGBA = [msg.content(offset + 97), msg.content(offset + 98), ...
                          msg.content(offset + 99), msg.content(offset + 100)]; % RGBA (4 bytes)
        points(i).XYZ = [convertUint8Vector(msg.content(offset + (101:104)), 'single'), ...
                         convertUint8Vector(msg.content(offset + (105:108)), 'single'), ...
                         convertUint8Vector(msg.content(offset + (109:112)), 'single')]; % XYZ (3 × 4 bytes)
        points(i).diameter = convertUint8Vector(msg.content(offset + (113:116)), 'single'); % Diameter (4 bytes)
        points(i).owner = char(msg.content(offset + (117:136))); % Owner (20 bytes)
        % Store XYZ in pointList
        pointList(i,:) = points(i).XYZ;
    end
    name = msg.deviceName;
    onRxPointMessage(name , pointList);
end

function [name, image] = handleImageMessage(msg, onRxImageMessage)
    disp('IMAGE message incoming');
    % Image Header
    versionNumber = convertUint8Vector(msg.content(1:2), 'uint16');
    numberOfComponents = uint64(msg.content(3));
    scalarType = uint8(msg.content(4)); % (2:int8, 3:uint8, 4:int16, 5:uint16, 6:int32, 7:uint32, 10:float32, 11:float64)
    image.endian = uint8(msg.content(5));     % (1:BIG 2:LITTLE)
    image.coordinate = uint8(msg.content(6)); % (1:RAS 2:LPS)

    Ri = uint64(convertUint8Vector(msg.content(7:8), 'uint16'));    % Number of pixels in direction i
    Rj = uint64(convertUint8Vector(msg.content(9:10), 'uint16'));   % Number of pixels in direction j
    Rk = uint64(convertUint8Vector(msg.content(11:12), 'uint16'));  % Number of pixels in direction k

    Tx = convertUint8Vector(msg.content(13:16), 'single');  % Transverse vector (direction for i index)/
    Ty = convertUint8Vector(msg.content(17:20), 'single');  % Vector length is pixel size in i [mm]
    Tz = convertUint8Vector(msg.content(21:24), 'single'); 

    Sx = convertUint8Vector(msg.content(25:28), 'single');  % Transverse vector (direction for j index)/
    Sy = convertUint8Vector(msg.content(29:32), 'single');  % Vector length is pixel size in j [mm]
    Sz = convertUint8Vector(msg.content(33:36), 'single');  

    Nx = convertUint8Vector(msg.content(37:40), 'single');  % Normal vector of image plane (direction for k index)/
    Ny = convertUint8Vector(msg.content(41:44), 'single');  % Vector length is pixel size in k (slice thickness) [mm]
    Nz = convertUint8Vector(msg.content(45:48), 'single');  

    Px = convertUint8Vector(msg.content(49:52), 'single');  % Center position of the image [mm]
    Py = convertUint8Vector(msg.content(53:56), 'single');  
    Pz = convertUint8Vector(msg.content(57:60), 'single');  

    Di = convertUint8Vector(msg.content(61:62), 'uint16'); % Starting index of subvolume (ROI)
    Dj = convertUint8Vector(msg.content(63:64), 'uint16'); 
    Dk = convertUint8Vector(msg.content(65:66), 'uint16'); 

    DRi = convertUint8Vector(msg.content(67:68), 'uint16'); % Number of pixels of subvolume (ROI)
    DRj = convertUint8Vector(msg.content(69:70), 'uint16'); 
    DRk = convertUint8Vector(msg.content(71:72), 'uint16'); 

    image.origin = [Px, Py, Pz];
    image.orientation = [Tx, Ty, Tz; Sx, Sy, Sz; Nx, Ny, Nz];
    imageRawData = msg.content(73:length(msg.content));
    imageData = extractImageData(imageRawData, numberOfComponents, scalarType, image.endian);
    
    image.matrix = reshapeImageData(imageData, Ri, Rj, Rk, numberOfComponents);

    name = msg.deviceName;
    onRxImageMessage(name, image);
end

%% General message decoding
% http://openigtlink.org/protocols/v2_header.html
% https://openigtlink.org/protocols/v3_proposal.html

% Parse OpenIGTLink message header
function msg = ParseOpenIGTLinkMessageHeader(rawMsg)
    msg.versionNumber = convertUint8Vector(rawMsg(1:2), 'uint16');
    msg.dataTypeName = char(rawMsg(3:14));
    msg.deviceName = char(rawMsg(15:34));
    msg.timestamp = convertUint8Vector(rawMsg(35:42), 'uint64');
    msg.bodySize = convertUint8Vector(rawMsg(43:50), 'uint64');
    msg.bodyCrc = convertUint8Vector(rawMsg(51:58), 'uint64');
end

% Parse OpenIGTLink message body
function msg = ParseOpenIGTLinkMessageBody(msg)
    if (msg.versionNumber==1) % Body has only content (Protocol v1 and v2)
        msg.content = msg.body;     % Copy data from body to content
        msg = rmfield(msg, 'body'); % Remove the old field 'body'
        msg.extHeaderSize = [];
        msg.metadataHeaderSize = [];
        msg.metadataSize = [];
        msg.msgID = [];
        msg.metadataNumberKeys = [];
        msg.metadata = [];
    elseif (msg.versionNumber==2) % Body has extended_header, content and metadata (Protocol v3)
        % Extract extended_header
        msg.extHeaderSize = convertUint8Vector(msg.body(1:2), 'uint16');
        msg.metadataHeaderSize = convertUint8Vector(msg.body(3:4), 'uint16');
        msg.metadataSize = convertUint8Vector(msg.body(5:8), 'uint32');
        msg.msgID = convertUint8Vector(msg.body(9:12), 'uint32');
        % Extract content
        contentSize = msg.bodySize - (uint64(msg.extHeaderSize) + uint64(msg.metadataHeaderSize) + uint64(msg.metadataSize));
        msg.content = msg.body(13:12+contentSize);
        % Extract metadata
        msg.metadataNumberKeys = convertUint8Vector(msg.body(13+contentSize:14+contentSize), 'uint16');
        msg.metadata = msg.body(15+contentSize:length(msg.body));
        msg = rmfield(msg, 'body'); % Remove the old field 'body'
    end
end

% Receive message header and body and check for completeness
function msg = ReadOpenIGTLinkMessage()
    global timeout;
    openIGTLinkHeaderLength = 58;
    % Get message header
    headerData = ReadWithTimeout(openIGTLinkHeaderLength, timeout);
    % Check is complete header was received
    if (length(headerData)==openIGTLinkHeaderLength)
        % Get Message header
        msg = ParseOpenIGTLinkMessageHeader(headerData);
        % Get Message body
        msg.body = ReadWithTimeout(msg.bodySize, timeout);  
        % Check CRC64 check sum
        calculatedCrc = convertUint8Vector(igtlComputeCrc(msg.body), 'uint64');
        if (calculatedCrc ~= msg.bodyCrc)
            error('ERROR: Failed check sum')
        end
        % Separate msg.body into extended_header, content, meta_data
        msg = ParseOpenIGTLinkMessageBody(msg);
    else
        error('ERROR: Timeout while waiting receiving OpenIGTLink message header')
    end
end    

% Buffer expected number of bytes with timeout
function data = ReadWithTimeout(requestedDataLength, timeoutSec)
    import java.net.Socket
    import java.io.*
    import java.net.ServerSocket
    global socket;
    data = zeros(1, requestedDataLength, 'uint8'); % preallocate to improve performance
    signedDataByte = int8(0);
    bytesRead = 0;
    while (bytesRead < requestedDataLength)    
        % Computing (requestedDataLength-bytesRead) is an int64 operation, which may not be available on Matlab R2009 and before
        int64arithmeticsSupported =~ isempty(find(strcmp(methods('int64'),'minus'),1));
        if int64arithmeticsSupported
            % Full 64-bit arithmetics
            bytesToRead = min(socket.inputStream.available, requestedDataLength-bytesRead);
        else
            % Fall back to floating point arithmetics
            bytesToRead = min(socket.inputStream.available, double(requestedDataLength)-double(bytesRead));
        end  
        if (bytesRead == 0 && bytesToRead > 0)
            % starting to read message header
            tstart = tic;
        end
        for i = bytesRead+1:bytesRead+bytesToRead
            signedDataByte = DataInputStream(socket.inputStream).readByte;
            if signedDataByte>=0
                data(i) = signedDataByte;
            else
                data(i) = bitcmp(-signedDataByte,'uint8')+1;
            end
        end            
        bytesRead = bytesRead+bytesToRead;
        if (bytesRead>0 && bytesRead<requestedDataLength)
            % check if the reading of the header has timed out yet
            timeElapsedSec=toc(tstart);
            if(timeElapsedSec>timeoutSec)
                % timeout, it should not happen
                % remove the unnecessary preallocated elements
                data = data(1:bytesRead);
                break
            end
        end
    end
end

%% Auxiliar functions

% Conversion from array of bytes to given type
function result = convertUint8Vector(uint8Vector, targetType)
    % Ensure the input is a uint8 vector
    if ~isa(uint8Vector, 'uint8')
        error('Input must be of type uint8.');
    end
    % Use typecast to convert uint8 to the specified target type
    result = swapbytes(typecast(uint8Vector, targetType));
end

function pixel_values = extractImageData(image_data, numberOfComponents, T, E)
    % Define a mapping of T values to MATLAB data types
    type_map = containers.Map([2, 3, 4, 5, 6, 7, 10, 11], ...
                              {'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'single', 'double'});
    % Validate the type code T
    if ~isKey(type_map, T)
        error('Invalid type code T: %d. Supported types: 2, 3, 4, 5, 6, 7, 10, 11.', T);
    end 
    % Get corresponding MATLAB data type
    data_type = type_map(T);
    disp(['Image Data Type = ', data_type]);
    % Determine number of bytes per element
    bytes_per_element = numel(typecast(cast(0, data_type), 'uint8'));
    % Ensure image_data is in uint8 format
    image_data = uint8(image_data(:)); % Ensure it's a column vector
    % Check if image_data length is a multiple of bytes_per_element * numberOfComponents
    total_components = bytes_per_element * numberOfComponents;
    num_elements = floor(length(image_data) / total_components);
    if mod(length(image_data), total_components) ~= 0
        warning('image_data length is not a multiple of %d. Truncating extra bytes.', total_components);
    end
    % Extract only the valid portion of image_data
    valid_data = image_data(1:num_elements * total_components);
    % Reshape into an array where each row represents a full pixel (all components)
    reshaped_data = reshape(valid_data, bytes_per_element, []);
    % Convert bytes to the specified data type
    if E == 1  % Big-Endian
        pixel_values = swapbytes(typecast(reshaped_data(:), data_type));
    elseif E == 2  % Little-Endian
        pixel_values = typecast(reshaped_data(:), data_type);
    else
        error('Invalid endianness E: %d. Use 1 for BIG-ENDIAN or 2 for LITTLE-ENDIAN.', E);
    end
    % Reshape the output to [num_components, num_pixels] format
    pixel_values = reshape(pixel_values, numberOfComponents, []).';
end

function reshaped_image = reshapeImageData(pixel_values, width, height, depth, numberOfComponents)
    % Validate input size
    [num_pixels, num_channels] = size(pixel_values);

    % Ensure numberOfComponents matches the input data
    if num_channels ~= numberOfComponents
        error('Mismatch: The provided pixel array does not match the expected number of components.');
    end

    % Check if the total number of pixels matches the expected dimensions
    expected_pixels = width * height * depth;
    if num_pixels ~= expected_pixels
        error('Mismatch: The provided pixel array does not match the specified dimensions.');
    end

    % Reshape the 2D array into a 4D matrix: [width, height, depth, numberOfComponents]
    reshaped_image = reshape(pixel_values, [width, height, depth, numberOfComponents]);
end
