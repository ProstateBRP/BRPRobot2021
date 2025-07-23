function T_inv = inverseHomogeneousTransform(T)
    % Calculate the inverse of a 4x4 homogeneous transformation matrix.
    %
    % Parameters:
    %   T - A 4x4 homogeneous transformation matrix.
    %
    % Returns:
    %   T_inv - The inverse of the given homogeneous transformation matrix.

    % Check if the input is a 4x4 matrix
    if size(T, 1) ~= 4 || size(T, 2) ~= 4
        error('Input matrix must be a 4x4 matrix.');
    end

    % Extract the rotation and translation components
    R = T(1:3, 1:3); % Top-left 3x3 rotation matrix
    t = T(1:3, 4);   % Top-right 3x1 translation vector

    % Compute the inverse rotation (transpose of the rotation matrix)
    R_inv = R.';
    % Compute the inverse translation
    t_inv = -R_inv * t;

    % Construct the inverse transformation matrix
    T_inv = eye(4);
    T_inv(1:3, 1:3) = R_inv;
    T_inv(1:3, 4) = t_inv;
end

