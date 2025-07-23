function M = expSE3(e)
% 
% Computes the exponential map M of 4x4 se3 Lie algebra w^, M = exp(e^)
% 
M = zeros(4,4);
w = e(1:3,1:3);
t = e(1:3,4);

% Converting w to exponential map (SO3) form
W = fromLieSO3(w);
L = sqrt(W(1)^2 + W(2)^2 + W(3)^2);
V = eye(3) + (((1-cos(L))/L^2) * w) + (((L-sin(L))/L^3) * w^2);
M(1:3,4) = V*t;
M(1:3,1:3) = expSO3(w);
M(4,4) = 1;