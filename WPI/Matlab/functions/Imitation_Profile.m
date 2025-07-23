function [alpha, omega_hat] = Imitation_Profile(k, k_max, theta_d)
% IMITATION_PROFILE 論文のFig.4(alpha-k)及びFig.3(ω_hat-theta_d-alpha)に該当するプロファイルデータを模擬
% input：
%   k       - the desired vurvature 
%   k_max   - xxx
%   theta_d - target angle
% output：
%   alpha     - steering effort
%   omega_hat - A normalized instataneous rotational velocity (式(1)の結果と一致するものと予想)

%% Fig.4 - 1-exp(-x)の水平漸近する関数でプロファイルを模擬
% Horizontal_Asymptotic_Coefficient = 1; % 水平漸近線の値 (Original Satoshi)
% exp_Coefficient = 1.2*2.0*10^3; % プロファイルに対してそれらしい値を採用 (Original Satoshi)

a4 = -1.8672;
a3 = 5.5652;
a2 = -6.642;
a1 = 3.9418;
a0 = 0.00048228;
coef = [a4/k_max^4, a3/k_max^3, a2/k_max^2, a1/k_max, a0]; % Ryo added

k = abs(k); % プロファイルに適用できるよう、曲率がマイナスになった場合の対応(仮置き20240530)

% k = k; % scaling (added Ryo 20250106)

if (k < k_max) && (k >= 0)
    % alpha = (1-exp(-k*exp_Coefficient)) * Horizontal_Asymptotic_Coefficient;  % Original (Satoshi)
    alpha = coef(1) * k^4 + coef(2) * k^3 + coef(3) * k^2 + coef(4) * k + coef(5); %(added Ryo 20250106)
elseif k < 0
    alpha = 0;
else
    alpha = 1;
end

%% Fig.3 - cos関数でプロファイルを模擬
omega_hat = 1 + alpha * (cos(theta_d) - 1) / 2; % 2項は0～-alphaの値を取る

end

