import ROOT
import numpy as np
import array
import uproot
import sys
from math import sqrt

def gaussFit(h,name,Run, xmin=-1, xmax=-1):

    x = ROOT.RooRealVar(f"x_{name}","E/E_{True}",
                        h.GetXaxis().GetXmin(),
                        h.GetXaxis().GetXmax())

    data = ROOT.RooDataHist(f"data_{name}", "data",ROOT.RooArgList(x),h)

    peak = h.GetBinCenter(h.GetMaximumBin())

    mean  = ROOT.RooRealVar(f"mean_{name}", "Gaussian mean",peak,peak-3,peak+3)

    sigma = ROOT.RooRealVar(f"sigma_{name}", "Gaussian sigma",h.GetRMS(),0.1*h.GetRMS(),5*h.GetRMS())

    gauss = ROOT.RooGaussian(f"gauss_{name}", "Gaussian",x,mean,sigma)

    nsig = ROOT.RooRealVar(f"nsig_{name}", "signal yield",h.Integral(),0.0,10.0*h.Integral())

    model = ROOT.RooAddPdf(f"model_{name}", "extended Gaussian model",ROOT.RooArgList(gauss),ROOT.RooArgList(nsig))

    fitArgs = [
        ROOT.RooFit.Extended(True),
        ROOT.RooFit.Save(),
        ROOT.RooFit.PrintLevel(-1)
    ]

    if xmin >= 0 and xmax >= 0:
        fitArgs.insert(0, ROOT.RooFit.Range("fitRange"))
        x.setRange("fitRange", xmin, xmax)

    result = model.fitTo(data, *fitArgs)

    canvas = ROOT.TCanvas()

    frame = x.frame()
    data.plotOn(frame)
    model.plotOn(frame, ROOT.RooFit.Range("fitRange"),ROOT.RooFit.NormRange("fitRange"))

    frame.Draw()

    pt = ROOT.TPaveText(0.60, 0.65, 0.88, 0.88, "NDC")
    pt.SetFillColor(0)
    pt.SetTextFont(42)
    pt.SetBorderSize(0)
    pt.SetTextSize(0.05)

    pt.AddText(f"m_{{core}} = {mean.getVal():.3g} #pm {mean.getError():.3g}")
    pt.AddText(f"#sigma_{{core}} = {sigma.getVal():.3g} #pm {sigma.getError():.3g}")

    pt.Draw()

    canvas.Update()

    canvas.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/FitPlots_gauss/fit_gauss_run_{Run}.root")

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }

def cbFit(h,name,Run,xmin=-1,xmax=-1):

    x = ROOT.RooRealVar(f"x_{name}", "E/E_{True}", h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())

    data = ROOT.RooDataHist(f"data_{name}", "data", ROOT.RooArgList(x), h)

    peak = h.GetBinCenter(h.GetMaximumBin())

    mean  = ROOT.RooRealVar(f"mean_{name}", "DCB mean",peak,peak-3,peak+3)

    sigma = ROOT.RooRealVar(f"sigma_{name}", "DCB sigma",h.GetRMS(),0.1*h.GetRMS(),5*h.GetRMS())

    alphaL = ROOT.RooRealVar(f"alphaL_{name}", "alphaL", 1.5, 0.1, 5.0)
    nL     = ROOT.RooRealVar(f"nL_{name}",     "nL",     3.0, 0.5, 20.0)

    alphaR = ROOT.RooRealVar(f"alphaR_{name}", "alphaR", 1.5, 0.1, 5.0)
    nR     = ROOT.RooRealVar(f"nR_{name}",     "nR",     3.0, 0.5, 20.0)

    dcb = ROOT.RooCrystalBall(f"dcb_{name}", "Double Crystal Ball",x,mean,sigma,alphaL, nL,alphaR, nR)

    nsig = ROOT.RooRealVar(f"nsig_{name}", "signal yield",h.Integral(),0.0,10.0*h.Integral())
    model = ROOT.RooAddPdf(f"model_{name}", "extended DCB model",ROOT.RooArgList(dcb),ROOT.RooArgList(nsig))

    fitArgs = [
        ROOT.RooFit.Extended(True),
        ROOT.RooFit.Save(),
        ROOT.RooFit.PrintLevel(-1)
    ]

    if xmin >= 0 and xmax >= 0:
        fitArgs.insert(0, ROOT.RooFit.Range("fitRange"))
        x.setRange("fitRange", xmin, xmax)

    result = model.fitTo(data, *fitArgs)


    canvas = ROOT.TCanvas()

    frame = x.frame()
    data.plotOn(frame)
    model.plotOn(frame, ROOT.RooFit.Range("fitRange"),ROOT.RooFit.NormRange("fitRange"))

    frame.Draw()
    canvas.Update()

    canvas.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/FitPlots_dcb/fit_dcb_run_{Run}.root")

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }

def main():

    if len(sys.argv) < 2:
        print("Usage: python3 plotter_resolution.py [gauss|dcb]")
        sys.exit(1)

    fit_type = sys.argv[1].lower()

    if fit_type not in ["gauss", "dcb"]:
        print("Error: choose 'gauss' or 'dcb'")
        sys.exit(1)

    Ebins=[20,40,60,80,100,120,150,200,250]
    Run=[19366,19352,19348,19347,19372,19343,19344,19327,19293]
    En,eEn,mu,emu,sigma,esigma = [],[],[],[],[],[]
    roofit_objects = []

    lin = ROOT.TGraphErrors(len(Ebins))
    res = ROOT.TGraphErrors(len(Ebins))
    res2 = ROOT.TGraphErrors(len(Ebins))

    for ie in range(len(Ebins)):

        c = ROOT.TCanvas()
        c.SetGrid()

        run=Run[ie]
        energy=Ebins[ie]

        file=uproot.open(f"/eos/cms/store/group/dpg_ecal/comm_ecal/upgrade/testbeam/ECALTB_H4_Oct2025/reco/run_{run}/{run}_0002_reco.root")

        tree=file["tree"]
        charge=tree["ecal_charge_sum_5x5"].array(library="np")

        charge_np = np.array(charge, dtype=np.float64)
        charge_np = np.ascontiguousarray(charge_np)
        weights = np.ones(len(charge_np), dtype=np.float64)

        h = ROOT.TH1F(f"Charge_5x5_{run}", "", 250, 0, 50000)
        h.FillN(len(charge_np), charge_np, weights)

        h.GetXaxis().SetTitle("Charge [ADC]")
        h.GetYaxis().SetTitle("Nevents")

#        if run == 19327:
#            h.Draw()
            #h.SetAxisRange(0,800)
#            c.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/Test2.pdf")

        mean = h.GetMean()
        rms  = h.GetRMS()

        xmin = mean - 2*rms
        xmax = mean + 2*rms

        if fit_type=="gauss":
            results = gaussFit(h,h.GetName(),run,xmin,xmax)
        if fit_type=="dcb":
            results = cbFit(h,h.GetName(),run,xmin,xmax)

        roofit_objects.append(results)

        mu_val, emu_val = results["mean"]
        sig_val, esig_val = results["sigma"]

        resolution_error = sqrt(esig_val**2*(1/mu_val)**2+sig_val**2*(sig_val/mu_val**2)**2)

        print("Energy/Mean/eMean/Sigma/eSigma")
        print(energy,mu_val,emu_val,sig_val,esig_val)

        lin.SetPoint(ie, mu_val, energy)
        lin.SetPointError(ie,sig_val,0)

        res.SetPoint(ie,energy,sig_val)
        res.SetPointError(ie,0,esig_val)

        res2.SetPoint(ie,energy,100*(sig_val/mu_val))
        res2.SetPointError(ie,0,resolution_error)

    lin.SetMarkerStyle(24)
    lin.SetMarkerSize(0.8)
    lin.SetMarkerColor(ROOT.kBlack)
    res.SetMarkerStyle(24)
    res.SetMarkerSize(0.8)
    res.SetMarkerColor(ROOT.kBlack)
    res2.SetMarkerStyle(24)
    res2.SetMarkerSize(0.8)
    res2.SetMarkerColor(ROOT.kBlack)
    ROOT.gStyle.SetOptTitle(1)
    ROOT.gStyle.SetTitleAlign(23)
    ROOT.gStyle.SetTitleX(0.5)

    lin.SetTitle(f"Energy linearity ({fit_type} fit);Mu_charge_5x5 [ADC];Beam energy [GeV]")
    lin.Draw("AP")
    c.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/Energy_linearity_{fit_type}.pdf")
    res.SetTitle(f"Sigma vs Beam energy ({fit_type} fit);Beam energy [GeV];Sigma_charge_5x5 [ADC]")
    res.Draw("AP")
    c.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/SigmavsBeamEn_{fit_type}.pdf")
    res2.SetTitle(f"Resolution ({fit_type} fit);Beam energy[GeV];Sigma/Mu_(charge_5x5) [%]")
    res2.Draw("AP")
    c.SaveAs(f"/eos/user/l/lfaiella/CMS_ECAL_Thesis/Plots_resolution_april/Resolution_{fit_type}.pdf")


    input("finito")
if __name__ == "__main__":
    main()
