% Takes igtl image received and shows a selected slice
% Alternatively, accepts a matrix (2D, 3D or 4D for RGB channels) and
% assumes LPS coordinates
% Any valid slice can be selected. If no slice is specified, shows the
% middle slice. If 0 or a negative slice is specified, shows the last slice
function igtlShowImage(input, slice)
    if ~isfield(input, 'matrix')
        inputDim = ndims(input);
        if (inputDim > 1) && (inputDim < 5) % 2D, 3D or 4D (channels) matrix
            image.matrix = input;
        else
            error('Unsupported image input');
        end
    else
        inputDim = ndims(input.matrix);
        if (inputDim > 1) && (inputDim < 5) % 2D, 3D or 4D (channels) matrix
            image = input;
        else
            error('Unsupported image input');
        end
    end
    if ~isfield(image, 'coordinate')
        image.coordinate = 2;
    elseif (image.coordinate ~= 1) && (image.coordinate ~= 2)
        error('Invalid coordinate: %d. Use 1 for RAS or 2 for LPS.', image.coordinate);
    end
    % Get image dimensions
    [width, height, depth, channels] = size(image.matrix);
    if nargin < 2
        slice = round(depth / 2); % Use middle slice
    elseif slice <= 0             % Use last slice
        slice = depth;
    elseif (slice > depth)
        error('Invalid slice number: %d. Max slice is %d', slice, depth);
    end
    % Display the image dimensions
    disp(['Image Dimensions: Width = ', num2str(width), ...
          ', Height = ', num2str(height), ...
          ', Depth = ', num2str(depth), ...
          ', Channels = ', num2str(channels)]);
    % Extract the relevant slice
    if depth > 1
        img_to_display = squeeze(image.matrix(:,:,slice,:)); % Get middle slice
    else
        img_to_display = squeeze(image.matrix); % Single slice
    end
    % Apply coordinate adjustment
    if image.coordinate == 1  % RAS (Right-Anterior-Superior)
        img_to_display  = rot90(img_to_display);   % Rotate 90°
        img_to_display  = fliplr(img_to_display);  % Flip Left-Right
        coord_label = 'RAS converted to LPS';
    elseif image.coordinate == 2  % LPS (Left-Posterior-Superior)
        coord_label = 'LPS';
    else
        error('Invalid coordinate system. Use 1 for RAS, 2 for LPS.');
    end
    % Display the image
    figure;
    imshow(img_to_display, []);
    title(sprintf('Displaying Slice %d of %d (%s)', slice, depth, coord_label));
end