function w = toLieSE3(W)
% 
% w = toLieSE3(W)
% Converts six element SE(3) matrix W to 4x4 se(3) Lie algebra w
% 
w = zeros(4,4);
if ((size(W,1) == 1)&&(size(W,2) == 6))||((size(W,1) == 6)&&(size(W,2) == 1))
    w(1:3,1:3) = toLieSO3(W(4:6));
    w(1:3,4) = W(1:3);
end
