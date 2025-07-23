function W = fromLieSO3(w)
% 
% w = toLieSO3(W)
% Converts 3x3 so(3) Lie algebra w to 3x1 SO(3) W
% 
if w(2)==-w(4) && w(3)==-w(7) && w(6)==-w(8)
    W = [w(6);w(7);w(2)];
else
	W = null(1);
end