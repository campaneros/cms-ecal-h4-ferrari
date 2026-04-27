import os,json,uproot,argparse,sys,ROOT
import numpy as np
import array
import glob
from math import sqrt
import csv

def has_branch(fname, branch):
    f = ROOT.TFile.Open(fname)
    if not f or f.IsZombie():
        return False
    t = f.Get("tree")
    if not t:
        return False

    return t.GetBranchStatus(branch)

def cbFit(h,name,Run,output_dir,seed_channel,xmin=-1,xmax=-1):

    x = ROOT.RooRealVar(f"x_{name}_{Run}", "E/E_{True}", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())

    data = ROOT.RooDataHist(f"data_{name}_{Run}", "data", ROOT.RooArgList(x), h)

    peak = h.GetBinCenter(h.GetMaximumBin())

    mean  = ROOT.RooRealVar(f"mean_{name}", "DCB mean",peak,peak-3,peak+3)

    sigma = ROOT.RooRealVar(f"sigma_{name}", "DCB sigma",h.GetRMS(),0.1*h.GetRMS(),5*h.GetRMS())

    alphaL = ROOT.RooRealVar(f"alphaL_{name}", "alphaL", 1.5, 0.1, 5.0)
    nL     = ROOT.RooRealVar(f"nL_{name}",     "nL",     3.0, 0.5, 20.0)

    alphaR = ROOT.RooRealVar(f"alphaR_{name}", "alphaR", 1.5, 0.1, 5.0)
    nR     = ROOT.RooRealVar(f"nR_{name}",     "nR",     3.0, 0.5, 20.0)

    dcb = ROOT.RooCrystalBall(f"dcb_{name}", "Double Crystal Ball",x,mean,sigma,alphaL, nL,alphaR, nR)

    nsig = ROOT.RooRealVar(f"nsig_{name}", "signal yield",h.Integral(),0.0,10.0*h.Integral())
    model = ROOT.RooAddPdf(f"model_{name}_{Run}", "extended DCB model",ROOT.RooArgList(dcb),ROOT.RooArgList(nsig))

    fitArgs = [
        ROOT.RooFit.Extended(True),
        ROOT.RooFit.Save(),
        ROOT.RooFit.PrintLevel(-1)
    ]

    if xmin >= 0 and xmax >= 0:
        fitArgs.insert(0, ROOT.RooFit.Range("fitRange"))
        x.setRange("fitRange", xmin, xmax)

    result = model.fitTo(data, *fitArgs)

    c = ROOT.TCanvas()

    frame = x.frame()
    data.plotOn(frame)
    model.plotOn(frame, ROOT.RooFit.Range("fitRange"),ROOT.RooFit.NormRange("fitRange"))

    frame.Draw()

    chi2 = frame.chiSquare()

    pt = ROOT.TPaveText(0.60, 0.65, 0.88, 0.88, "NDC")
    pt.SetFillColor(0)
    pt.SetTextFont(42)
    pt.SetBorderSize(0)
    pt.SetTextSize(0.05)

    pt.AddText(f"m_{{core}} = {mean.getVal():.3g} #pm {mean.getError():.3g}")
    pt.AddText(f"#sigma_{{core}} = {sigma.getVal():.3g} #pm {sigma.getError():.3g}")
    pt.AddText(f"#chi^2_{{core}} = {chi2:.3g}" )

    pt.Draw()

    c.Update()

    filename_h = f"SeedChannelHistoWithMask_{seed_channel}"
    subdir = f"Run_{Run}_Seed_{seed_channel}"
    os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    output_path_h = os.path.join(output_dir,subdir, filename_h)
    c.SaveAs(output_path_h + ".pdf")
    c.SaveAs(output_path_h + ".root")
    c.Clear()

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }


def main(arguments):

    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-i",  f"--input-dir", type=str, required=True, help="input directory containing ROOT file with unpacked tree")
    parser.add_argument("-ro", f"--plot-output-dir", type=str, required=True, help="directory for output plots")
    parser.add_argument("-j", f"--run-info-json", type=str, required=False, help="run and energy sample")

    args = parser.parse_args(arguments)

    json_dict = json.load(open(args.run_info_json, "r"))
    input_dir = args.input_dir
    plot_output_dir = args.plot_output_dir
    Run = json_dict["global"]["run info"]["run list"]
    SeedChannel = json_dict["global"]["run info"]["seed channel"]
    EtaCenter = json_dict["global"]["run info"]["eta center"]
    PhiCenter = json_dict["global"]["run info"]["phi center"]
    roofit_objects = []
    charge_dict = {}
    intercalib_dict = {}

    with open("intercalibration_info.csv", "w", newline="") as f:

        writer = csv.writer(f)
        writer.writerow(["seed_channel", "x_center_hodo", "y_center_hodo","a_eta","b_eta","a_phi","b_phi","calibrationfactor"])

        for ie in range(len(Run)):

            c = ROOT.TCanvas()
            c.SetGrid()

            run = Run[ie]
            seed_channel = SeedChannel[ie]
            eta_center = EtaCenter[ie]
            phi_center = PhiCenter[ie]

            chain = ROOT.TChain("tree")

            pattern = os.path.join(input_dir, f"run_{run}/{run}_*_reco.root")

            for f in glob.glob(pattern):
                if has_branch(f, "ecal_charge_sum_5x5"):
                    chain.Add(f)
                else:
                    print("Skipping:", f)

            print(f"Run {run}: added {chain.GetNtrees()} files")


            h1 = ROOT.TH2F(f"ieta_centroid_vs_hodox_{run}", "", 500,-20,10,1000,50,57)
            chain.Draw(f"Sum$( (abs(ecal_iphi_within_5x5) < 2)*(abs(ecal_ieta_within_5x5) < 2)*(4.9 + log(ecal_charge_divided_5x5))*ecal_ieta )/Sum$( (abs(ecal_iphi_within_5x5) < 2)*(abs(ecal_ieta_within_5x5) < 2)*(4.9 + log(ecal_charge_divided_5x5)) ):(hodo_x1_cl0_pos + hodo_x2_cl0_pos)/2>>ieta_centroid_vs_hodox_{run}", "hodo_x1_single_cl_flag && hodo_x2_single_cl_flag", "goff")

            h1.SetStats(0)
            h1.SetTitle("iEta_{centroid} vs Hodo_x;X [mm];ieta")
            h1.SetMarkerStyle(24)
            h1.SetMarkerSize(0.8)
            h1.SetMarkerColor(ROOT.kBlack)
            ROOT.gStyle.SetOptTitle(1)
            ROOT.gStyle.SetTitleAlign(23)
            ROOT.gStyle.SetTitleX(0.5)
            h1.Draw("COLZ")

            hprof1 = h1.ProfileX()
            hprof1.Draw("same")

            fit1 = ROOT.TF1("fit", "pol1",-8,2)
            hprof1.Fit(fit1,"R")

            slope1 = fit1.GetParameter(1)
            const1 = fit1.GetParameter(0)
            chi2_1  = fit1.GetChisquare()
            ndf1 = fit1.GetNDF()

            pave1 = ROOT.TPaveText(0.15, 0.7, 0.35, 0.88, "NDC")
            pave1.SetFillColor(0)
            pave1.SetTextFont(42)
            pave1.SetTextSize(0.03)
            pave1.SetBorderSize(1)

            pave1.AddText(f"Offset_eta = {const1:.3f}")
            pave1.AddText(f"Slope = {slope1:.3f}")
            pave1.AddText(f"#chi^2 = {chi2_1:.2f}")
            #pave1.AddText(f"Ndof = {ndf1}")
            pave1.Draw()
            fit1.Draw("same")

            filename_h1 = f"EtaCentroidvsHodoX_{run}"
            subdir = f"Run_{run}_Seed_{seed_channel}"
            os.makedirs(os.path.join(plot_output_dir, subdir), exist_ok=True)
            output_path_h1 = os.path.join(plot_output_dir,subdir, filename_h1)
            c.SaveAs(output_path_h1 + ".pdf")
            c.SaveAs(output_path_h1 + ".root")

            xcenter_hodo = (eta_center-const1)/slope1

            eta_min = eta_center - 4*abs(slope1)
            eta_max = eta_center + 4*abs(slope1)
            print("etamin/etamax",eta_min, eta_max)

    ######

            c2 = ROOT.TCanvas()
            c2.SetGrid()

            h2 = ROOT.TH2F(f"iphi_centroid_vs_hodoy_{run}","",500,-20,20,1000,0,10)
            chain.Draw(f"Sum$( (abs(ecal_iphi_within_5x5) < 2)*(abs(ecal_ieta_within_5x5) < 2)*(4.9 + log(ecal_charge_divided_5x5))*ecal_iphi )/Sum$( (abs(ecal_iphi_within_5x5) < 2)*(abs(ecal_ieta_within_5x5) < 2)*(4.9 + log(ecal_charge_divided_5x5)) ):hodo_y1_cl0_pos>>iphi_centroid_vs_hodoy_{run}", "hodo_y1_single_cl_flag && hodo_y2_single_cl_flag", "goff")

            h2.SetStats(0)
            h2.SetTitle("Phi_{centroid}vsHodoY;Y [mm];iphi")
            h2.SetMarkerStyle(24)
            h2.SetMarkerSize(0.8)
            h2.SetMarkerColor(ROOT.kBlack)
            ROOT.gStyle.SetOptTitle(1)
            ROOT.gStyle.SetTitleAlign(23)
            ROOT.gStyle.SetTitleX(0.5)
            h2.Draw("COLZ")

            hprof2 = h2.ProfileX()
            hprof2.Draw("same")

            fit2 = ROOT.TF1("fit", "pol1",0,10)
            hprof2.Fit(fit2,"R")

            const2 = fit2.GetParameter(0)
            slope2 = fit2.GetParameter(1)
            chi2_2  = fit2.GetChisquare()
            ndf2 = fit2.GetNDF()

            pave2 = ROOT.TPaveText(0.15, 0.7, 0.35, 0.88, "NDC")
            pave2.SetFillColor(0)
            pave2.SetTextFont(42)
            pave2.SetTextSize(0.03)
            pave2.SetBorderSize(1)

            pave2.AddText(f"Offset_phi = {const2:.3f}")
            pave2.AddText(f"Slope = {slope2:.3f}")
            pave2.AddText(f"#chi^2 = {chi2_2:.2f}")
            #pave2.AddText(f"Ndof = {ndf2}")
            pave2.Draw()
            fit2.Draw("same")

            filename_h2 = f"PhiCentroidvsHodoY_{run}"
            subdir = f"Run_{run}_Seed_{seed_channel}"
            os.makedirs(os.path.join(plot_output_dir, subdir), exist_ok=True)
            output_path_h2 = os.path.join(plot_output_dir,subdir, filename_h2)
            c2.SaveAs(output_path_h2 + ".pdf")
            c2.SaveAs(output_path_h2 + ".root")
            c2.Clear()

            ycenter_hodo = (phi_center-const2)/slope2

            phi_min = phi_center - 4*abs(slope2)    #Warning:abs is present because slope2<0
            phi_max = phi_center + 4*abs(slope2)
            print("phimin/phimax",phi_min, phi_max)

    #######

            c = ROOT.TCanvas()
            c.SetGrid()

            h = ROOT.TH1F(f"SeedChannelHistoWithMask_{seed_channel}", "", 500,0,20000)
            chain.Draw(f"ecal_charge_seed>>SeedChannelHistoWithMask_{seed_channel}", f"(ecal_ieta > {eta_min} && ecal_ieta < {eta_max} && ecal_iphi > {phi_min} && ecal_iphi < {phi_max})")
            h.SetStats(0)
            h.SetTitle("Seed channel charge;Charge [ADC];Events")
            h.SetMarkerStyle(24)
            h.SetMarkerSize(0.8)
            h.SetMarkerColor(ROOT.kBlack)
            ROOT.gStyle.SetOptTitle(1)
            ROOT.gStyle.SetTitleAlign(23)
            ROOT.gStyle.SetTitleX(0.5)
            #h.Draw("COLZ")

            max_bin = h.GetMaximumBin()
            max_position = h.GetBinCenter(max_bin)
            max_value = h.GetBinContent(max_bin)
            bin1 = h.FindFirstBinAbove(max_value/2)
            bin2 = h.FindLastBinAbove(max_value/2)
            fwhm = h.GetBinCenter(bin2) - h.GetBinCenter(bin1)

            fit_min = max_position - 2.5*fwhm
            fit_max = max_position + 1.5*fwhm

            results = cbFit(h,h.GetName(),run,plot_output_dir,seed_channel,fit_min,fit_max)

            roofit_objects.append(results)

            mu_val, emu_val = results["mean"]
            sig_val, esig_val = results["sigma"]

            hc = ROOT.TH1F(f"Charge_5x5_{seed_channel}", "", 500,0,20000)
            chain.Draw(f"ecal_charge_sum_5x5>>Charge_5x5_{seed_channel}","")
            hc.SetStats(0)
            hc.SetTitle("Seed channel 5x5 charge;Charge [ADC];Events")
            hc.SetMarkerStyle(24)
            hc.SetMarkerSize(0.8)
            hc.SetMarkerColor(ROOT.kBlack)
            ROOT.gStyle.SetOptTitle(1)
            ROOT.gStyle.SetTitleAlign(23)
            ROOT.gStyle.SetTitleX(0.5)


            charge_dict[seed_channel] = hc.GetBinCenter(hc.GetMaximumBin())
            intercalib_dict[seed_channel] = 1/mu_val

            print("Seed/Charge/intercalib factor:",seed_channel,charge_dict[seed_channel],intercalib_dict[seed_channel])

            writer.writerow([seed_channel,f"{float(xcenter_hodo):.5f}",f"{float(ycenter_hodo):.5f}",f"{float(const1):.5f}",f"{float(slope1):.5f}",f"{float(const2):.5f}",f"{float(slope2):.5f}",f"{float(intercalib_dict[seed_channel]):.10f}"])

    c_calib = ROOT.TCanvas()
    h_calib = ROOT.TH1F("h_calib", "Calibrated charge;Charge;Entries", 500, 0,2)

    for ch in SeedChannel:
        c = charge_dict[ch]
        ic = intercalib_dict[ch]
        h_calib.Fill(c * ic)
        print("Charge/intercalib factor:",c,ic,c*ic)

    h_calib.Draw()
    c_calib.Update()
    filename_h_calib = f"CalibratedCharge"
    output_path_h_calib = os.path.join(plot_output_dir,filename_h_calib)
    c_calib.SaveAs(output_path_h_calib + ".pdf")
    c_calib.SaveAs(output_path_h_calib + ".root")

    #Charge_sum_5x5_string = "+".join([f"charge[{ch}] * {intercalib[ch]}" for ch in SeedChannel])


    input("finito")
if __name__ == "__main__":
    main(sys.argv[1:])
