% 実行中の全てのタイマーを取得
timers = timerfind;

% タイマーが存在する場合
if ~isempty(timers)
    stop(timers);  % タイマーを停止
    delete(timers);  % タイマーを削除
    disp('All timers have been stopped and deleted');
else
    disp('No timers running');
end