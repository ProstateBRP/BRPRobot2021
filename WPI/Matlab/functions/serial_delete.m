% 開いているシリアルポートオブジェクトを検索
serialPorts = instrfind;

% 開いているシリアルポートが存在する場合
if ~isempty(serialPorts)
    % 各シリアルポートを閉じる
    fclose(serialPorts);
    % シリアルポートオブジェクトを削除
    delete(serialPorts);
end