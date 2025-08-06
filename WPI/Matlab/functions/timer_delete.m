% 実行中の全てのタイマーを取得
timers = timerfind;

% タイマーが存在する場合
if ~isempty(timers)
    stop(timers);  % タイマーを停止
    delete(timers);  % タイマーを削除
    disp('全てのタイマーが停止され、削除されました。');
else
    disp('実行中のタイマーはありません。');
end