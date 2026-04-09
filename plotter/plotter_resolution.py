import os,json,uproot,argparse,sys,ROOT
import numpy as np
import array
from math import sqrt


def gaussFit(h,name,Run,output_dir, xmin=-1, xmax=-1):

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

    if xmin >= 0 and xmax >= 0:
        model.plotOn(frame,
                   ROOT.RooFit.Range("fitRange"),
                   ROOT.RooFit.NormRange("fitRange"))
    else:
        model.plotOn(frame)

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

    canvas.Update()

    filename = f"fit_gauss_run_{Run}"
    output_path = os.path.join(output_dir, filename)
    canvas.SaveAs(output_path + ".pdf")
    canvas.SaveAs(output_path + ".root")

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }

def cbFit(h,name,Run,output_dir,xmin=-1,xmax=-1):

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

    canvas.Update()

    filename = f"fit_dcb_run_{Run}"
    output_path = os.path.join(output_dir, filename)
    canvas.SaveAs(output_path + ".pdf")
    canvas.SaveAs(output_path + ".root")

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }


def lognFit(h, name, Run, output_dir, xmin=-1, xmax=-1):

    x = ROOT.RooRealVar(f"x_{name}", "E/E_{True}",
                        h.GetXaxis().GetXmin(),
                        h.GetXaxis().GetXmax())

    data = ROOT.RooDataHist(f"data_{name}", "data",
                            ROOT.RooArgList(x), h)

    peak  = h.GetBinCenter(h.GetMaximumBin())
    sigma0 = h.GetRMS()

    eta   = ROOT.RooRealVar(f"eta_{name}",   "eta",   0.1, 0.01, 1.0)
    sigma = ROOT.RooRealVar(f"sigma_{name}", "sigma", sigma0, 0.1, 10000)
    mean  = ROOT.RooRealVar(f"mean_{name}",  "peak",  peak, peak-3*sigma0, peak+3*sigma0)
    amp = ROOT.RooRealVar("amp", "amplitude", 0.3*h.Integral(), 0, 1e7)

    sqrt2pi = ROOT.RooConstVar("sqrt2pi", "sqrt2pi", (2*3.14159265)**0.5)
    c235    = ROOT.RooConstVar("c235", "2.35 const", 2.35)

    expr = "x[4] * (x[1] / (x[5] * x[2] * ((2/x[6]) * log(x[1]*x[6]/2 + sqrt(1 + pow(x[1]*x[6]/2,2)))))) * exp(-0.5 * pow(log(max(1e-4, 1 - (x[1]/x[2])*(x[0] - x[3])))/((2/x[6]) * log(x[1]*x[6]/2 + sqrt(1 + pow(x[1]*x[6]/2,2)))) ,2))"

    logn_pdf = ROOT.RooGenericPdf(f"logn_{name}","log-normal-like",expr,ROOT.RooArgList(x, eta, sigma, mean, amp, sqrt2pi,c235))
    nsig = ROOT.RooRealVar(f"nsig_{name}", "signal yield",h.Integral(),0.0,10.0*h.Integral())
    model = ROOT.RooAddPdf(f"model_{name}", "extended logn model",ROOT.RooArgList(logn_pdf),ROOT.RooArgList(nsig))

    fitArgs = [
        ROOT.RooFit.Extended(True),
        ROOT.RooFit.Save(),
        ROOT.RooFit.PrintLevel(-1)
    ]

    if xmin >= 0 and xmax >= 0:
        x.setRange("fitRange", xmin, xmax)
        fitArgs.insert(0, ROOT.RooFit.Range("fitRange"))

    result = model.fitTo(data, *fitArgs)

    canvas = ROOT.TCanvas()
    frame = x.frame()

    data.plotOn(frame)
    model.plotOn(frame,ROOT.RooFit.Range("fitRange"),ROOT.RooFit.NormRange("fitRange"))

    frame.Draw()

    chi2 = frame.chiSquare()

    pt = ROOT.TPaveText(0.60, 0.65, 0.88, 0.88, "NDC")
    pt.SetFillColor(0)
    pt.SetTextFont(42)
    pt.SetBorderSize(0)
    pt.SetTextSize(0.05)

    pt.AddText(f"Peak = {mean.getVal():.3g} ± {mean.getError():.3g}")
    pt.AddText(f"Sigma = {sigma.getVal():.3g} ± {sigma.getError():.3g}")
    pt.AddText(f"#chi^2_{{core}} = {chi2:.3g}" )

    pt.Draw()

    canvas.Update()

    filename = f"fit_logn_run_{Run}"
    output_path = os.path.join(output_dir, filename)
    canvas.SaveAs(output_path + ".pdf")
    canvas.SaveAs(output_path + ".root")

    return {
        "mean": (mean.getVal(), mean.getError()),
        "sigma": (sigma.getVal(), sigma.getError())
    }


def main(arguments):

    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-g",  f"--fit-type", type=str, required=True, help="fit type")
    parser.add_argument("-i",  f"--input-dir", type=str, required=True, help="input directory containing ROOT file with unpacked tree")
    parser.add_argument("-ro", f"--plot-output-dir", type=str, required=True, help="directory for output plots")
    parser.add_argument("-f", f"--fit-output-dir", type=str, required=True, help="directory for fits")
    parser.add_argument("-j", f"--run-info-json", type=str, required=False, help="run and energy sample")

    args = parser.parse_args(arguments)

    json_dict = json.load(open(args.run_info_json, "r"))
    fit_type=args.fit_type

    input_dir=args.input_dir
    plot_output_dir=args.plot_output_dir
    fit_output_dir=args.fit_output_dir
    os.makedirs(plot_output_dir, exist_ok=True)
    os.makedirs(fit_output_dir, exist_ok=True)

    Run=json_dict["global"]["run info"]["run list"] #[20,40,60,80,100,120,150,200,250]
    Ebins=json_dict["global"]["run info"]["run energies"] #[19366,19352,19348,19347,19372,19343,19344,19327,19293]
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

        input_filename = f"run_{run}/{run}_0002_reco.root"
        input_path = os.path.join(input_dir, input_filename)
        print("Opening file:", input_path)
        file = uproot.open(input_path)
        print("File opened")

        tree=file["tree"]
        charge=tree["ecal_charge_sum_5x5"].array(library="np")

        charge_np = np.array(charge, dtype=np.float64)
        charge_np = np.ascontiguousarray(charge_np)
        weights = np.ones(len(charge_np), dtype=np.float64)

        h = ROOT.TH1F(f"Charge_5x5_{run}", "", 250, 0, 50000)
        h.FillN(len(charge_np), charge_np, weights)

        h.GetXaxis().SetTitle("Charge [ADC]")
        h.GetYaxis().SetTitle("Nevents")

        max_bin = h.GetMaximumBin()
        max_position = h.GetBinCenter(max_bin)
        max_value = h.GetBinContent(max_bin)
        bin1 = h.FindFirstBinAbove(max_value/2)
        bin2 = h.FindLastBinAbove(max_value/2)
        fwhm = h.GetBinCenter(bin2) - h.GetBinCenter(bin1)

        xmin = max_position - 2*fwhm
        xmax = max_position + 2*fwhm

        if fit_type=="gauss":
            results = gaussFit(h,h.GetName(),run,fit_output_dir,xmin,xmax)
        if fit_type=="dcb":
            results = cbFit(h,h.GetName(),run,fit_output_dir,xmin,xmax)
        if fit_type=="logn":
            results = lognFit(h,h.GetName(),run,fit_output_dir,xmin,xmax)

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
    filename_lin = f"Energy_linearity_{fit_type}"
    output_path_lin = os.path.join(plot_output_dir, filename_lin)
    c.SaveAs(output_path_lin + ".pdf")
    c.SaveAs(output_path_lin + ".root")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/Energy_linearity_{fit_type}.pdf")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/Energy_linearity_{fit_type}.root")
    c.Clear()

    res.SetTitle(f"Sigma vs Beam energy ({fit_type} fit);Beam energy [GeV];Sigma_charge_5x5 [ADC]")
    res.Draw("AP")
    filename_res = f"SigmavsBeamEn_{fit_type}"
    output_path_res = os.path.join(plot_output_dir, filename_res)
    c.SaveAs(output_path_res + ".pdf")
    c.SaveAs(output_path_res + ".root")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/SigmavsBeamEn_{fit_type}.pdf")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/SigmavsBeamEn_{fit_type}.root")
    c.Clear()

    res2.SetTitle(f"Resolution ({fit_type} fit);Beam energy[GeV];Sigma/Mu_(charge_5x5) [%]")
    res2.Draw("AP")
    filename_res2 = f"Resolution_{fit_type}"
    output_path_res2 = os.path.join(plot_output_dir, filename_res2)
    c.SaveAs(output_path_res2 + ".pdf")
    c.SaveAs(output_path_res2 + ".root")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/Resolution_{fit_type}.pdf")
#    c.SaveAs(f"/eos/user/l/lfaiella/www/h4dqm/ECAL_TB_2025/Plots_resolution_april/Resolution_{fit_type}.root")


    input("finito")
if __name__ == "__main__":
    main(sys.argv[1:])
