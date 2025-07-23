function y_unit_vector = quaternion2y(quaternion)
    % Input: quaternion = [q0, q1, q2, q3] (scalar part + vector part)
    % Output: y_unit_vector = [x, y, z] (unit vector representing the Y-axis direction)

    % Normalize the quaternion to ensure it represents a valid rotation
    quaternion = quaternion / norm(quaternion);

    % Extract components of the quaternion
    q0 = quaternion(1); % Scalar part
    q1 = quaternion(2); % Vector part x
    q2 = quaternion(3); % Vector part y
    q3 = quaternion(4); % Vector part z

    % Compute the rotation matrix from the quaternion
    R = [
        1 - 2*(q2^2 + q3^2),  2*(q1*q2 - q0*q3),      2*(q1*q3 + q0*q2);
        2*(q1*q2 + q0*q3),    1 - 2*(q1^2 + q3^2),    2*(q2*q3 - q0*q1);
        2*(q1*q3 - q0*q2),    2*(q2*q3 + q0*q1),      1 - 2*(q1^2 + q2^2)
    ];

    % Extract the second column of the rotation matrix (Y-axis direction)
    y_unit_vector = R(:, 2);
end