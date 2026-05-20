import json
import time, re, os, ROOT, sys
import numpy as np
import traceback
import shutil

#not implemented!!
def plot_chunk(args):
    """
    Wrapper to handle chunking for multiprocessing.
    """
    plotconf_df, arrays, plot_output_folder, kwargs = args

    plotconf_df.apply(lambda row: plot(row, arrays, plot_output_folder, **kwargs), axis=1)



def eval_formula(formula, data_dict):
    """
    Evaluate a formula with ${var} syntax and optional @ for broadcasting axes.

    - ${var} -> uproot_dict["var"]
    - ${var}@ -> uproot_dict["var"][:, np.newaxis]
    - ${var}@@ -> uproot_dict["var"][:, np.newaxis][:, np.newaxis] etc.
    """

    def replace_var(m):
        varname = m.group(1)
        at_symbols = m.group(2) or ""
        arr = f'uproot_dict["{varname}"]'
        if at_symbols:
            arr += ''.join(['[:, np.newaxis]' for _ in at_symbols])
        return arr

    # Match ${var} optionally followed by one or more @ symbols
    pattern = re.compile(r'\$\{\s*(\w+)\s*\}(\@*)')
    expr = pattern.sub(replace_var, formula)

    # Safe eval environment
    safe_globals = {"uproot_dict": data_dict, "np": np, "__builtins__": {}}
    return eval(expr, safe_globals)


def draw_TT_grid(hist, c):
    c.cd()
    lines = []
    line_color = ROOT.kBlack
    line_style = 1
    line_width = 1
    x_min = hist.GetXaxis().GetXmin()
    x_max = hist.GetXaxis().GetXmax()
    y_min = hist.GetYaxis().GetXmin()
    y_max = hist.GetYaxis().GetXmax()

    # vertical grid lines
    for i in range(1, 66, 5):
      x = i - 0.5
      line = ROOT.TLine(x, y_min, x, y_max)
      line.SetLineColor(line_color)
      line.SetLineStyle(line_style)
      line.SetLineWidth(line_width)
      line.Draw("same")
      lines.append(line)  

    # horizontal grid lines
    for j in range(1, 11, 5):
      y = j - 0.5
      line = ROOT.TLine(x_min, y, x_max, y)
      line.SetLineColor(line_color)
      line.SetLineStyle(line_style)
      line.SetLineWidth(line_width)
      line.Draw("same")
      lines.append(line)
    return lines  



def plot(row, uproot_dict, outputfolder, f=None, just_draw=False):

  try:
    os.makedirs(f"{outputfolder}/{row.folder}/", exist_ok=True)

    if not os.path.exists(f"{outputfolder}/{row.folder}/index.php"):
      shutil.copy2(f"{outputfolder}/index.php", f"{outputfolder}/{row.folder}/index.php")
    if not os.path.exists(f"{outputfolder}/{row.folder}/jsroot_viewer.php"):
      shutil.copy2(f"{outputfolder}/jsroot_viewer.php", f"{outputfolder}/{row.folder}/jsroot_viewer.php")
  except Exception:
    print(traceback.format_exc(), file=sys.stderr, flush=True)

  ROOT.gErrorIgnoreLevel = ROOT.kError

  print(f"outputfolder: {outputfolder}", file=sys.stderr, flush=True)


  try:
    name = row['name']

    print(name, file=sys.stderr, flush=True)

    os.makedirs(f"{outputfolder}/{row.folder}/", exist_ok=True)

    #legacy... very slow!
    #f = ROOT.TFile(f"{outputfolder}/{row.folder}/{name}.root", ("update" if just_draw else "recreate"))
    #f.cd()

    ROOT.gROOT.SetBatch(ROOT.kTRUE)

    c = ROOT.TCanvas(f"{name}_canvas")
    c.cd()

    if just_draw:
      for key in f.GetListOfKeys():
        obj = key.ReadObj()
        try:
          if obj.InheritsFrom("TCanvas"):
            f.Delete(f"{key.GetName()};{key.GetCycle()}")
        except TypeError:
          pass

    if just_draw:
      pass
    else:
      if str(row.cuts).strip() == "":
        first_key = next(iter(uproot_dict.keys()))
        mask = np.ones((uproot_dict[first_key].shape[0],), dtype=bool)
      else:
        mask = eval_formula(row.cuts, uproot_dict)

      x = eval_formula(row.x, uproot_dict)[mask]
      nevents = x.shape[0]
      x = x.ravel()

    if str(row.y).strip() == "0" and str(row.z).strip() == "0":
        if just_draw:
          h = f.Get(f"{name}")
        else:
          h = ROOT.TH1F(name, row.title, int(row.binsnx), float(row.binsminx), float(row.binsmaxx))

          time_fill = time.time()
          h.FillN(len(x), x.astype(np.float64), np.ones_like(x, dtype=np.float64))
          print(f"fillN 1D took {time.time() - time_fill}", file=sys.stderr, flush=True)

        h.Draw("HIST")
        h.SetFillColorAlpha(ROOT.kBlue, 0.2)
        h.SetLineColor(eval(f"ROOT.{row.color}"))
        binw = (float(row.binsmaxx) - float(row.binsminx)) / int(row.binsnx)
        h.GetXaxis().SetRangeUser(h.GetMean() - 3*h.GetRMS(), h.GetMean() + 3*h.GetRMS()) #iterative...
        h.GetXaxis().SetRangeUser(h.GetMean() - 3*h.GetRMS(), h.GetMean() + 3*h.GetRMS())
        h.GetXaxis().SetRangeUser(h.GetMean() - 5*h.GetRMS(), h.GetMean() + 5*h.GetRMS())
        h.GetYaxis().SetTitle(f"entries / {float(f'{binw:.1g}'):g} {row.ylabel}")

        c.Update()
        max_bin = h.GetMaximumBin()
        max_position = h.GetBinCenter(max_bin)
        max_value = h.GetBinContent(max_bin)
        bin1 = h.FindFirstBinAbove(max_value/2)
        bin2 = h.FindLastBinAbove(max_value/2)
        fwhm = h.GetBinCenter(bin2) - h.GetBinCenter(bin1)

        pave = ROOT.TPaveText(0.65, 0.7, 0.85, 0.88, "NDC")
        pave.SetFillColor(0)  # Transparent background
        pave.SetTextFont(42)
        pave.SetTextSize(0.03)
        pave.SetBorderSize(0)

        # add three lines
        pave.AddText(f"Events in hist. = {h.Integral()}")
        pave.AddText(f"FWHM/2.35 = {fwhm/2.35:.3f}")
        pave.AddText(f"Peak at x = {max_position:.3f}")
        if max_position > 1000: pave.AddText(f"Ratio = {fwhm/max_position/2.35:.3f}")

        pave.Draw()


    elif str(row.y).strip() != "0" and str(row.z).strip() == "0":
        if just_draw:
          h = f.Get(f"{name}")
        else:
          y = eval_formula(row.y, uproot_dict)[mask].ravel()
          h = ROOT.TH2F(name, row.title,
                      int(row.binsnx), float(row.binsminx), float(row.binsmaxx),
                      int(row.binsny), float(row.binsminy), float(row.binsmaxy))
          print("x.shape: ", x.shape, flush=True)
          print("y.shape: ", y.shape, flush=True)
          time_fill = time.time()
          h.FillN(len(x), x.astype(np.float64), y.astype(np.float64), np.ones_like(x, dtype=np.float64))
          print(f"fillN 2D took {time.time() - time_fill}", file=sys.stderr, flush=True)

        h.Draw("ZCOL")
        h.GetYaxis().SetTitle(row.ylabel)

    else:
        ROOT.gStyle.SetPalette(ROOT.kLightTemperature)
        if just_draw:
          h = f.Get(f"{name}")
        else:
          y_notflat = eval_formula(row.y, uproot_dict)[mask]
          n_ch = y_notflat.shape[1]
          y = y_notflat.ravel()
          z = eval_formula(row.z, uproot_dict)[mask].ravel()
          h = ROOT.TH2D(name, row.title,
                            int(row.binsnx), float(row.binsminx), float(row.binsmaxx),
                            int(row.binsny), float(row.binsminy), float(row.binsmaxy))

          time_fill = time.time()
          h.FillN(len(x),
                x.astype(np.float64),
                y.astype(np.float64),
                z.astype(np.float64)*n_ch)
          print(f"fillN 2D took {time.time() - time_fill}", file=sys.stderr, flush=True)

        h.Scale(1/h.GetEntries())
        h.Draw("ZCOL")

        # 5x5 grid fot TTs
        if row.tt:
          lines = draw_TT_grid(h, c)

        h.SetContour(int(row.contours))
        h.GetZaxis().SetTitle(row.zlabel)
        h.GetYaxis().SetTitle(row.ylabel)
        h.GetXaxis().SetNdivisions(505)
        h.GetYaxis().SetNdivisions(505)
        c.SetRightMargin(0.18)

    h.GetXaxis().SetTitle(row.xlabel)

    t_save = time.time()
    #c.SaveAs(f"{outputfolder}/{row.folder}/{name}.png")
    #print(f"saving png took {time.time() - t_save}s", file=sys.stderr, flush=True)

    t_save = time.time()
    f.cd()
    if just_draw: c.Write("", ROOT.TObject.kOverwrite)
    else:
      #t_save = time.time()
      c.Write()
      #print(f"writing canvas  took {time.time() - t_save}s", file=sys.stderr, flush=True)
      t_save = time.time()
      #c.Print(f"{outputfolder}/{row.folder}/{name}_canvas.pdf")
      #print(f"printing canvas to PDF took {time.time() - t_save}s", file=sys.stderr, flush=True)
      #t_save = time.time()
      if str(row.y).strip() != "0" and str(row.z).strip() != "0": h.Scale(h.GetEntries())
      print(f"rescaling h took {time.time() - t_save}s", file=sys.stderr, flush=True)
      #t_save = time.time()
      #h.SaveAs(f"{outputfolder}/{row.folder}/{name}_histo.root")
      #print(f"writing histo withsaveas took {time.time() - t_save}s", file=sys.stderr, flush=True)
      #t_save = time.time()
      #ROOT.TBufferJSON.ExportToFile(f"{outputfolder}/{row.folder}/{name}_histo.json", h)
      #print(f"writing histo to JSON took {time.time() - t_save}s", file=sys.stderr, flush=True)
      #t_save = time.time()
      h.Write()
    #f.Close()
    #print(f"writing histo to file and saving .root took {time.time() - t_save}s", file=sys.stderr, flush=True)
    #del c
    #del h

  except Exception:
    print(traceback.format_exc(), file=sys.stderr, flush=True)



