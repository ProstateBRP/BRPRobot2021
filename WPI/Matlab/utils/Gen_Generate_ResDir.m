function foldername = Gen_Generate_ResDir(baseFolderName)
% Gen_ResDir - Generate a result directory with the following name convention:
%              baseFolderName_yyyymmdd possibly followed by _x if directory 
%              already exists. Also, copy all .m files from the current
%              directory into a new 'code' folder inside the generated folder.
%
% Syntax: foldername = Gen_ResDir(baseFolderName)
%
% Inputs:
%    baseFolderName - String, name of the base folder
%
% Outputs:
%    foldername - String, name of the generated folder

    % Get current date using datetime and format it as yyyymmdd
    currentDate = datetime('now','Format','yyyyMMdd');
    
    % Concatenate base folder name and current date
    foldername = [baseFolderName, '_', char(currentDate)];
    
    % Check if folder exists, if it does, append _x to make it unique
    counter = 1;
    while isfolder(foldername)
        foldername = [baseFolderName, '_', char(currentDate), '_', num2str(counter)];
        counter = counter + 1;
    end
    
    % Create the folder and the 'code' subfolder
    mkdir(foldername);
    mkdir(fullfile(foldername, 'code'));
    
    % Find all .m files in the current directory
    mfiles = dir(fullfile('**','*.m'));
    
    % Copy all found .m files to the 'code' subfolder
    for i = 1:length(mfiles)
        source = fullfile(mfiles(i).folder,mfiles(i).name);
        destination = fullfile(foldername, 'code', mfiles(i).name);
        copyfile(source, destination);
    end
end