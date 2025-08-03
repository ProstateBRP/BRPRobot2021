function transformation_mtx = apply_rotation(transformation_mtx, amount)
% This function applies a transformation about desired axis and returns the
% new transformation
alpha = amount (1);
beta = amount(2);
gamma = amount(3);
Rx = [1 0 0 0;
    0 cosd(alpha) -sind(alpha) 0;
    0 sind(alpha) cosd(alpha) 0;
    0 0 0 1];
Ry = [cosd(beta) 0 sind(beta) 0;
    0 1 0 0;
    -sind(beta) 0 cosd(beta) 0;
    0 0 0 1];
Rz = [cosd(gamma) -sind(gamma) 0 0;
    sind(gamma) cosd(gamma) 0 0;
    0 0 1 0;
    0 0 0 1];

transformation_mtx = transformation_mtx * Rx * Ry * Rz;

end