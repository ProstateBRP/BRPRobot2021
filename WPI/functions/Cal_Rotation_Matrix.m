function Rmat = Cal_Rotation_Matrix(R_in,axis)
% CAL_ROTATION_MATRIX 回転行列を作成する
% input：
%   theta_in - 回転量
%   axis     - 回転軸（x:0,y:1,z:2）
% output：
%   RMat - 回転行列
% 参考：MathWorks公式ヘルプ
%   https://jp.mathworks.com/help/symbolic/rotation-matrix-and-transformation-matrix.html

switch axis
    case R_axis.x
        Rmat = [1, 0, 0;  0, cos(R_in), -sin(R_in);  0, sin(R_in), cos(R_in)]; % x軸周りの回転行列を生成
    case R_axis.y
        Rmat = [cos(R_in), 0, sin(R_in);  0, 1, 0;  -sin(R_in), 0, cos(R_in)]; % y軸周りの回転行列を生成
    case R_axis.z
        Rmat = [cos(R_in), -sin(R_in), 0;  sin(R_in), cos(R_in), 0;  0, 0, 1]; % z軸周りの回転行列を生成
    otherwise
        Rmat = eye(3); % 単位行列を生成
        disp('Rmat axis error')
end

end

