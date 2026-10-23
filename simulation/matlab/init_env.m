%% Orion Digital Twin - Phase 1 Environment Initialization
% Verifies MATLAB workspace, sets up search paths, and displays system status.

function status = init_env()
    fprintf('=================================================================\n');
    fprintf('    NASA ORION DIGITAL TWIN — MATLAB SIMULATION ENVIRONMENT      \n');
    fprintf('=================================================================\n');
    
    % Determine project paths
    currentFile = mfilename('fullpath');
    [matlabDir, ~, ~] = fileparts(currentFile);
    projectRoot = fullfile(matlabDir, '..', '..');
    
    addpath(genpath(fullfile(projectRoot, 'simulation')));
    fprintf('[+] Added simulation directories to MATLAB path.\n');
    
    % Check MATLAB version and release
    v = ver('matlab');
    fprintf('[*] MATLAB Version: %s (Release %s)\n', v.Version, v.Release);
    
    % Check available toolboxes
    toolboxes = {'Simulink', 'Stateflow', 'Simscape', 'DSP System Toolbox', 'MATLAB Coder'};
    fprintf('\n--- Toolbox Availability Check ---\n');
    for i = 1:length(toolboxes)
        tbName = toolboxes{i};
        installed = ~isempty(ver(tbName));
        if installed
            fprintf('[*] %-22s : INSTALLED\n', tbName);
        else
            fprintf('[!] %-22s : NOT INSTALLED (Fallback algorithms will be used)\n', tbName);
        end
    end
    
    % Display baseline spacecraft mass and geometry parameters
    fprintf('\n--- Orion MPCV Baseline Parameters Loaded ---\n');
    OrionSpecs.CM.diameter_m = 5.029;
    OrionSpecs.CM.height_m = 3.350;
    OrionSpecs.CM.dry_mass_kg = 9300.0;
    OrionSpecs.ESM.propellant_mass_kg = 8618.0;
    OrionSpecs.ESM.wet_mass_kg = 15460.0;
    OrionSpecs.TotalLiftoffMass_kg = 35380.0;
    
    fprintf('    Crew Module Base Diameter : %.3f m\n', OrionSpecs.CM.diameter_m);
    fprintf('    Crew Module Height        : %.3f m\n', OrionSpecs.CM.height_m);
    fprintf('    Crew Module Dry Mass      : %.1f kg\n', OrionSpecs.CM.dry_mass_kg);
    fprintf('    ESM Usable Propellant     : %.1f kg\n', OrionSpecs.ESM.propellant_mass_kg);
    fprintf('    Liftoff Stack Mass        : %.1f kg\n', OrionSpecs.TotalLiftoffMass_kg);
    
    fprintf('=================================================================\n');
    fprintf('    Phase 1 MATLAB Environment Initialized Successfully.         \n');
    fprintf('=================================================================\n');
    
    status = true;
end
