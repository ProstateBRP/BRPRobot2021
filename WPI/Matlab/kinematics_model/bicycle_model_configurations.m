% Bicycle model configurations
% Unit Vectors
e1 = [1;0;0];
e2 = [0;1;0];
e3 = [0;0;1];

% Geometric Relations
%mm
l2 = 0;%23.775; mm For unicycle model this will be zero
max_curvature = 0.001972715714235; %9.0402e-04
V1 = [e3; max_curvature * e1];
V2 = [zeros(3,1); e3];

% const double max_curvature_hard_phantom{0.001972715714235};
% const double max_curvature_soft_hard{0.0018228}; 
% const double max_curvature_ex_vivo{0.001284188980207};
% const double max_curvature_hard_soft{0.001684067110623};
