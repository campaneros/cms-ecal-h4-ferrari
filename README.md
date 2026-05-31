Ferrari:
Fast ECAL Rough Reconstruction and Analysis from Raw Inputs


WARNING: Checks of all .sh part not done yet at this stage, but nothing was changed upstream, so no problems expected a priori. This release is not considered stable in that section.


This stage is released as Ferrari2.0beta as a pre-test, with the 2025 program dubbed Ferrari1.0
For an electron spill (1k events) takes in average 5 seconds for the reconstruction + plot part (no DANTE unpacking), on lxplus
We have the possibility to go on a dedicated GPU machine to go even faster [not needed but maybe helpful]


Main changes	in code	structure w.r.t. 2025: github.com/delvecchiomarco/ECAL_TB2025
- Removed hardcoded features as	much as	possible. in principle everything should be settable from config json or adding custom reco files in a dedicated folder
- All detectors not requiring the generic-reco (the one starting from waveforms, defined in reco_functions) have custom reco defined in a custom-recos folder
- Defined a registry with a dedicated decorator to tag custom-recos functions. Needed functions must be added in the plugin section of the config json so they are imported at runtime. Now two new parameters ("decode" and "custom_reco") in the config json defined which function (from the registry) is used to, respectively, pre-process waveforms (for generic-reco), or, to perform another reco from scratch (hodoscope / bcp clock)
- Timing functions in a dedicated folder, selected at runtime based on config json 
- The code is ready to have the generic-reco part running on GPU is needed (not needed for ECAL but we could decide to do it anyway), by switching numpy --> cupy and scipy.ndimage --> cupy analogue
- Plots	now saved as hist + canvases in	1 .root	file per spill,	instead	of one .root file per plot as in 2025 --> much much faster
- All plots rendered by jsroot dynamically in the front-end
- Syntax to define plots is now completely numpy-based, instead of ROOT-numpy hybrid as in 2025. Branches must be written as "${branch_name}" and the corresponding numpy array is automatically taken inside the ROOT.FillN code
- Masks in the plots are now weights, to allow re-weighting histograms if needed

Main changes w.r.t. 2025 in the reconstruction:
- Zero-suppression based on peak threshold, except for diagnostic plots
- Baseline_subtraction, charges and timing only perfomed on non zero-suppressed channels
- Added Least Squares Fit (new multifit algorithm for phase-2, without OOT PU, ported to numpy) --> lsfit Amplitudes / Time
- Added possibility to change central region width (3x3, 5x5, 7x7, etc. default=5x5)
- All timing algorithms (except lsfit) now require positive slope to interpolate timing, i.e. they automatically choose a timing in the rising edge if multiple solutions are possible
- Clock timing improved
- Possibility to apply gain ratios, in the map with flag switchable from config json
- Possibility to apply a scale factor to charges, to have average charges equal to average peak values in magnitude
- Logarithmic centroid enforced, with offset ("3.8", taken from CMSSW or DANTE) settable from json

Main changes w.r.t. 2025 in the plots:
- Added ieta:iphi:A_5x5	plot
- Added mcp - ECAL timing plot (clock corrected)
- Added 3x3 charge plot
- Added MCP efficiency and ECAL seed charge profiles vs. hodoscope positions
- Plots re-shuffled between main and subfolders


Missing features before test beam:
- Test hadd watcher (no changes expected)
- Test re-reco feature: processes on-the-fly entire run reco (no unpacking and plots) with multiple cores
- Test new define_envs.sh feature: having all paths defined in a dedicated .sh
- Test fullexecution.sh / integration with DANTE
- Switch cpu/gpu generic-reco execution at runtim from define_envs.sh (if we decide to go on GPU)


For tests run a command like this:
```
python3 -m ferrari_core.reco -i /eos/cms/store/group/dpg_ecal/comm_ecal/upgrade/testbeam/ECALTB_H4_Oct2025/DataTree/19435/0001.root -r 19327 -s 1 -ro /tmp/testing/ -opt electrons -po </eos/user/r/rgargiul/www/test_ferrari>
```
Electrons and laser spills tested for now, from run 19327
