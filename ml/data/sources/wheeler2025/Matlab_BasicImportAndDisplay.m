%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%  Matlab_BasicImportAndDisplay.m  %%%%%%%%%%
%%%%%%%%%%        License: CC-BY 4.0        %%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%Script Redacted for Matlab R2024a by William Wheeler, November 2024.
%Latest update: January 2025.

%This matlab script "Matlab_BasicImportAndDisplay.m" import And display experimental data from the open access data repository "Aging study on twenty A123 18650 Graphite/LFP 1,1 Ah cells" in https://doi.org/10.57745/OLBXKT.
%More information is available in the open access publication:
%Wheeler, W., Bultel, Y., Venet, P. & Ali, S. Ageing study on twenty A123 18650 Graphite/LFP 1.1 Ah cells. Recherche Data Gouv, https://doi.org/10.57745/OLBXKT (2025) [under publication].

%This work (dataset, script and additional information or files) are licensed under CC BY 4.0, https://creativecommons.org/licenses/by-sa/4.0/.


%% init matlab 
clear all
close all
clc

%% Init varables

%Open waitbar
myWaitbar = waitbar(0,"Starting...");

%Import charac files only or  charac and aging files
ONOFF_importCharacData = true;
ONOFF_importAgingData = true;
ONOFF_importEisData = true;

datafolderpath = '..\Data\';

%Colors and marks for plots
plotColor = [100, 0, 90 ; 100, 25, 92; 100, 50, 95; ... %cells 1a, 1b, 1c.
    100, 50, 0; 100, 60, 20; 90, 70, 40; ... %cells 2a, 2b, 2c.
    0, 0, 0; 50, 50, 50; ... %cells 3a, 3b.
    67, 0, 100; 75, 25, 100; 67, 40, 80; ... %cells 4a, 4b, 4c.
    0, 70, 100; 30, 79, 100; 54, 79, 90; ... %cells 5a, 5b, 5c.
    0, 50, 11; 0, 70, 15; 0, 90, 20; ... %cells 6a, 6b, 6c.
    100, 0, 0 ; 100, 30, 30; 100, 60, 60 ]; %cells 7a, 7b, 7c.

plotMark = ['*' ; '+' ; 'x' ;... %cells 1a, 1b, 1c.
    '*' ; '+' ; 'x' ; ... %cells 2a, 2b, 2c.
    '*' ; '+' ; ... %cells 3a, 3b.
    '*' ; '+' ; 'x' ; ... %cells 4a, 4b, 4c.
    '*' ; '+' ; 'x' ; ... %cells 5a, 5b, 5c.
    '*' ; '+' ; 'x' ; ... %cells 6a, 6b, 6c.
    '*' ; '+' ; 'x' ]; %cells 7a, 7b, 7c.


%% Find subfolders for all cells

dirInfo = dir(datafolderpath);
dirInfo(~[dirInfo.isdir]) = [];  %Remove non-directories
tf = ismember( {dirInfo.name}, {'.', '..'});
dirInfo(tf) = [];  %Remove current and parent directory.

isCellFolder = startsWith({dirInfo.name}.', 'Cell' );
dirCell = dirInfo(isCellFolder);

nbCell = length(dirCell);


%% Find charac and aging files for each cell

waitbar( 0, myWaitbar,'Finding aging and characterisation files...');

for i = 1:nbCell 
    
    cell(i).name = dirInfo(i).name;
    
    dirCellInfo = dir( strcat(datafolderpath, dirInfo(i).name, '\agingdata_50degC\') );
    dirCellInfo([dirCellInfo.isdir]) = [];  %Remove directories
    tf = ismember( {dirCellInfo.name}, {'.', '..'});
    dirCellInfo(tf) = [];  %Remove current and parent directory
    
    %find carac and aging folders
    isCharacFiles = startsWith({dirCellInfo.name}.', strcat('WWH_18650_', lower(dirInfo(i).name), '_charac') );
    cell(i).characfileslist = dirCellInfo(isCharacFiles);
    cell(i).nbcharac = length(cell(i).characfileslist);
    isAgingFiles = startsWith({dirCellInfo.name}.', strcat('WWH_18650_', lower(dirInfo(i).name), '_aging') );
    cell(i).agingfileslist = dirCellInfo(isAgingFiles);
    cell(i).nbaging = length(cell(i).agingfileslist);

    %Find EIS files
    dirEisInfo = dir( strcat(datafolderpath, cell(i).name,'\initialcharac_25degC\EIS\') );
    dirEisInfo([dirEisInfo.isdir]) = [];  %remove directories
    tf = ismember( {dirEisInfo.name}, {'.', '..'});
    dirEisInfo(tf) = [];  %remove current and parent directory.
    cell(i).EIS.initial.FilesList = dirEisInfo;
    
    dirEisInfo = dir( strcat(datafolderpath, cell(i).name,'\finalcharac_25degC\EIS\') );
    dirEisInfo([dirEisInfo.isdir]) = [];  %remove directories
    tf = ismember( {dirEisInfo.name}, {'.', '..'});
    dirEisInfo(tf) = [];  %remove current and parent directory.
    cell(i).EIS.final.FilesList = dirEisInfo;
end


%% Import Cell Capacity, Cycle number and EIS

if exist('./extractedData.mat', 'file') == 2 %Data already exists in a .mat file: import and use the .mat file.
    load('./extractedData.mat');
else %Data has never been imported in matlab. Import files and save in a .mat file.
    for i = 1:nbCell
        
        %Import charac data for each cell in the structure
        if ONOFF_importCharacData == true

            %Import charac file
            for j = 1:length(cell(i).characfileslist)

             waitbar( 0.8*(i-1)/nbCell + 0.8*j/(length(cell(i).characfileslist)+length(cell(i).agingfileslist))/nbCell , ...
                myWaitbar, ...
                strcat("Import ", cell(i).name, " - characterisation file: ", num2str(j), '/', num2str(length(cell(i).characfileslist)) ) );                 

                data = fct_import_csv( strcat( cell(i).characfileslist(j).folder, '\', cell(i).characfileslist(j).name) );

                %Find cycle number
                strsplit = split(cell(i).characfileslist(j).name, '_');
                strsplit = split(strsplit(4), '.csv');
                strsplit = split(strsplit(1), 'charac');
                cell(i).charac(j).cycle = str2double(strsplit(2));

                %Find cell capacity
                ischargecapacity = find(data{:,"Step_Index"} == 13); % find( data(:,) == 13 );
                cell(i).charac(j).chargecapacity = max( data{ischargecapacity,"Charge_Capacity"} );

                %Avoid data that is less than 20% of the initial capacity. Correct any missing data caused by technical issues during characterization cycle 100 in cells 1a, 2a, 2c, and 3a.
                if cell(i).charac(j).chargecapacity <= 0.1 * cell(i).charac(1).chargecapacity
                    cell(i).charac(j).chargecapacity = NaN;
                end

                %Compute SoH
                cell(i).charac(j).soh = 100 * cell(i).charac(j).chargecapacity / cell(i).charac(1).chargecapacity;
                %Clear temporary variables
                clear data filename cellname celltype strsplit ischargecapacity
            end
        end
    
         %Import aging data for each cell in the structure
        if ONOFF_importAgingData == true

            %Import aging files
            for j = 1:length(cell(i).agingfileslist)
    
                waitbar( 0.8*(i-1)/nbCell + 0.8*(length(cell(i).characfileslist)+j)/(length(cell(i).characfileslist)+length(cell(i).agingfileslist))/nbCell , ...
                        myWaitbar, ...
                        strcat("Import ", cell(i).name, " - aging file: ", num2str(j), '/', num2str(length(cell(i).characfileslist)) ) );
                
                data = fct_import_csv( strcat( cell(i).agingfileslist(j).folder, '\', cell(i).agingfileslist(j).name) );
                
                %Find the first and last cycle numbers
                strsplit = split(cell(i).agingfileslist(j).name, '_');
                strsplit = split(strsplit(4), '.csv');
                strsplit = split(strsplit(1), 'aging');
                strsplit = split(strsplit(2), 'to');
                cell(i).aging(j).firstCycle = str2double(strsplit(1));
                cell(i).aging(j).lastCycle = str2double(strsplit(2));
                
                %Find the cycle number for aging files
                step = transpose(1:1:max(data{:,"Cycle_Index"}));

                %Find the total charge capacity
                isLastAgingCycleChargeValue = cell2mat( cellfun(@(x) find(data{:,"Cycle_Index"} == x & (data{:,"Step_Index"} == 2 | data{:,"Step_Index"} == 8), 1, 'last'), num2cell(step), 'UniformOutput', false ) );
                cell(i).aging(j).totalCapacityInCharge = sum( data{isLastAgingCycleChargeValue, "Charge_Capacity"} );
                
                %Find the total discharged capacity (Take into account the regenerative current caused by the use of a WLTP cycle.)
                step = transpose(1:1:max(data{:,"Cycle_Index"}));
                isLastAgingCycleDischargeValue = cell2mat( cellfun(@(x) find(data{:,"Cycle_Index"} == x & data{:,"Step_Index"} == 5, 1, 'last'), num2cell(step), 'UniformOutput', false ) );
                cell(i).aging(j).totalCapacityInDischarge = sum( data{isLastAgingCycleDischargeValue, "Discharge_Capacity"} ) + sum( data{isLastAgingCycleDischargeValue, "Charge_Capacity"} );
                
                %Compute the total cumulative transferred capacity
                if j == 1
                     cell(i).aging(j).totalCumulativeTransferredCapacity = cell(i).aging(j).totalCapacityInCharge + cell(i).aging(j).totalCapacityInDischarge ;
                else
                    cell(i).aging(j).totalCumulativeTransferredCapacity = cell(i).aging(j-1).totalCumulativeTransferredCapacity + cell(i).aging(j).totalCapacityInCharge + cell(i).aging(j).totalCapacityInDischarge; 
                end

                %Compute Full Equivalent Cycles (FEC)
                cell(i).aging(j).FEC = (cell(i).aging(j).totalCumulativeTransferredCapacity /2 )/cell(i).charac(1).chargecapacity ; %total transferred capacity divided by the cell initial capacity
            end
        end 
    end

    % Import EIS from EIS files for each cell in the structure
    if ONOFF_importEisData == true
        for i = 1:length(cell)
        
            waitbar( 0.8 + 0.2*(i-1+j)/(nbCell*3), ...
                    myWaitbar, ...
                    strcat("Import ", cell(i).name, " - EIS files") );

            %Import initial EIS
            for j = 1:length(cell(i).EIS.initial.FilesList)
                %Find SoC for each EIS 
                strsplit = split(cell(i).EIS.initial.FilesList(j).name, 'soc');
                strsplit = split(strsplit(2), 'pct');
                cell(i).EIS.initial.soc{j} = str2double(strsplit(1));

                %Import EIS data
                cell(i).EIS.initial.data{j} = fct_import_eis( strcat( cell(i).EIS.initial.FilesList(j).folder, '\', cell(i).EIS.initial.FilesList(j).name) );
            end

            %Import final EIS
            for j = 1:length(cell(i).EIS.final.FilesList)
                %Find SoC for each EIS 
                strsplit = split(cell(i).EIS.final.FilesList(j).name, 'soc');
                strsplit = split(strsplit(2), 'pct');
                cell(i).EIS.final.soc{j} = str2double(strsplit(1));

                %Import EIS file
                cell(i).EIS.final.data{j} = fct_import_eis( strcat( cell(i).EIS.final.FilesList(j).folder, '\', cell(i).EIS.final.FilesList(j).name) );
            end
        end
    end
end 


%% Save extracted data in .mat file

if exist('./extractedData.mat', 'file') ~= 2 %Data has never been imported into Matlab and saved in a mat file in the Matlab's script folder.
    waitbar( 1, myWaitbar,'Save data...');
    save("./extractedData.mat","cell");
end

%% Plot SoH versus cycles if ONOFF_iportcharacData is true

waitbar( 1, myWaitbar,'Plot figures...');

if ONOFF_importCharacData == true

    figure
    hold on
    for i=1:length(cell)
        %Find NaN values and excludes corresponding rows
        isNotNaN = not(isnan(vertcat(cell(i).charac.chargecapacity)));
        %Plot data
        xdata4plot = vertcat(cell(i).charac.cycle);
        ydata4plot = vertcat(cell(i).charac.chargecapacity);
        plot( xdata4plot(isNotNaN), ...
            ydata4plot(isNotNaN), ...
            'Color',plotColor(i,:)./100, ...
            'Marker',plotMark(i,:), ...
            'LineWidth',0.75, ...
            'MarkerSize',7,...
            'DisplayName', cell(i).name );
    end

    set(gca,'FontSize',12);
    legend('FontSize',10, ...
        'NumColumns',1, ...
        'Location','eastoutside'); %round(i/3));
    xlabel("Cycles");
    ylabel("Cell capacity (Ah)");
    
    grid on  
    hold off
end


%% Plot SoH versus Full Equivalent Cycles if ONOFF_importcharacData is true AND ONOFF_importAgingData is true
if ONOFF_importCharacData == true & ONOFF_importAgingData == true

    figure
    hold on
    for i=1:length(cell)
        %Find NaN values and excludes corresponding rows
        isNotNaN = not(isnan(vertcat(cell(i).charac.soh)));
        %Plot existing data
        xdata4plot = [0,; vertcat(cell(i).aging.FEC)];
        ydata4plot = vertcat(cell(i).charac.soh);
        plot( xdata4plot(isNotNaN), ...
            ydata4plot(isNotNaN), ...
            'Color',plotColor(i,:)./100, ...
            'Marker',plotMark(i,:), ...
            'LineWidth',0.75, ...
            'MarkerSize',7,...
            'DisplayName', cell(i).name );
    end
    set(gca,'FontSize',12);
    legend('FontSize',10, ...
        'NumColumns',1, ...
        'Location','eastoutside');
    xlabel("Full Equivalent Cycles");
    ylabel("SoH (%)");
    
    grid on  
    hold off

end

%% Plot EIS data at SoC=50% if ONOFF_importEisData == true
if ONOFF_importEisData == true
    
    figure("Name","Nyquist Plot at SoC = 50%")

    tlo = tiledlayout(1,2);
    tlo.TileSpacing = "tight";
    tlo.Padding = "compact";

    nexttile

    hold on
    for i=1:length(cell)
        isEISat50pcts = find( vertcat(cell(i).EIS.initial.soc{:}) == 50, 1, 'first'); % find EIS at SoC=50% 
        
        if not(isempty(isEISat50pcts))
            dataEIS = cell(i).EIS.initial.data{1, 2};

            plot( dataEIS{:,"impedanceR_Ohm"}, ...
                -dataEIS{:,"impedanceI_Ohm"}, ...
                'Color',plotColor(i,:)./100, ...
                'Marker',plotMark(i,:), ...
                'LineWidth',0.75, ...
                'MarkerSize',7,...
                'DisplayName', cell(i).name );
        else %No data to plot
            warning( strcat("No data found to plot EIS for ",cell(i).name), '.' );
        end
    end
    
    set(gca,'FontSize',12);
    lg = legend('FontSize',10, ...
        'NumColumns',1, ...
        'Location','eastoutside');
    title("(a) Initial characterization", ...
        'FontWeight','normal');
    xlabel("Re(Z) (\Omega)");
    ylabel("-Im(Z) (\Omega)");
    xlim([0.01, 0.07]);
    ylim([-0.020, 0.03]);
    set(gca,'DataAspectRatio',[1 1 1]) %Cartesian coordinate plot
    grid on  
    hold off

    nexttile
    hold on
    for i=1:length(cell)
        isEISat50pcts = find( vertcat(cell(i).EIS.final.soc{:}) == 50, 1, 'first'); % find EIS at SoC=50% 
        
        if not(isempty(isEISat50pcts))
            dataEIS = cell(i).EIS.final.data{1, 2};

            plot( dataEIS{:,"impedanceR_Ohm"}, ...
                -dataEIS{:,"impedanceI_Ohm"}, ...
                'Color',plotColor(i,:)./100, ...
                'Marker',plotMark(i,:), ...
                'LineWidth',0.75, ...
                'MarkerSize',7,...
                'DisplayName', cell(i).name );
        else %No data to plot
            warning( strcat("No data found to plot EIS for ",cell(i).name), '.' );
        end
    end
    set(gca,'FontSize',12);
    title("(b) Final characterization", ...
        'FontWeight','normal');
    xlabel("Re(Z) (\Omega)");
    ylabel("-Im(Z) (\Omega)");
    xlim([0.01, 0.07]);
    ylim([-0.020, 0.03]);
    set(gca,'DataAspectRatio',[1 1 1]) %Cartesian coordinates plot
    grid on
    hold off

    lg.Layout.Tile = 'east';
end


%% End script
waitbar( 1, myWaitbar,'Script end.');
close(myWaitbar); 





%% fct_import_csv imports delimited aging and characterisation data from .csv file
function data = fct_import_csv(filename, dataLines)

% Input handling
% Filename is compulsory
% If dataLines is not specified, define defaults:
if nargin < 2
    dataLines = [2, Inf];
end

% Setup the Import Options and import the data
opts = detectImportOptions(filename,"DecimalSeparator", ".");
opts.DataLines = dataLines;
opts.Delimiter = ";";

%Specify file level properties
opts.ImportErrorRule = "error";
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% Import the data
data = readtable(filename, opts);

end





%% fct_import_eis Import EIS data from a text file
function impedance = fct_import_eis(filename, dataLines)

% Input handling
% Filename is compulsory
% If dataLines is not specified, define defaults:
if nargin < 2
    dataLines = [21, Inf];
end

%% Setup the Import Options and import the data
opts = delimitedTextImportOptions("NumVariables", 6);

% Specify range and delimiter
opts.DataLines = dataLines;
opts.Delimiter = ",";

% Specify column names and types
opts.VariableNames = ["Number", "FrequencyHz", "impedanceR_Ohm", "impedanceI_Ohm", "Significance", "Time_s"];
opts.SelectedVariableNames = ["Number", "FrequencyHz", "impedanceR_Ohm", "impedanceI_Ohm", "Significance", "Time_s"];
opts.VariableTypes = ["double", "double", "double", "double", "double", "double"];

% Specify file level properties
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% Import the data
impedance = readtable(filename, opts);

end