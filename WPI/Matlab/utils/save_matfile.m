% % ワークスペースのみ保存
save('result.mat')

% スクリプトごと保存
baseFolderName  = 'result/NC';    
foldername = Gen_Generate_ResDir(baseFolderName);
save([foldername,'/result.mat'])