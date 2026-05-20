import numpy as np
import ROOT
import sys


class PiecewiseCubicSplineNP:

    def __init__(self, segments, Ts):
        self.x0 = np.array([s["x0"] for s in segments])
        self.x1 = np.array([s["x1"] for s in segments])
        self.xc = np.array([s["xc"] for s in segments])

        self.a = np.array([s["a"] for s in segments])
        self.b = np.array([s["b"] for s in segments])
        self.c = np.array([s["c"] for s in segments])
        self.d = np.array([s["d"] for s in segments])
        self.Ts = Ts

    def _select(self, x):

        x = np.asarray(x)[None, ...]  # (1, E, C, N)

        x0 = self.x0[:, None, None, None]
        x1 = self.x1[:, None, None, None]

        inside = (x >= x0) & (x <= x1)

        idx = np.argmax(inside, axis=0)  # (E, C, N)

        xc = self.xc[idx]
        dx = x[0] - xc
        #print("x", x, "dx", dx)
        mask = np.abs(dx) <= (self.Ts / 2.0)

        return idx, dx, mask


    def eval(self, x):

        idx, dx, mask = self._select(x)

        a = self.a[idx]
        b = self.b[idx]
        c = self.c[idx]
        d = self.d[idx]

        f = a + b*dx + c*dx*dx + d*dx*dx*dx

        return np.where(mask, f, 0.0)



    def derivative(self, x):

        idx, dx, mask = self._select(x)

        b = self.b[idx]
        c = self.c[idx]
        d = self.d[idx]

        deriv = b + 2*c*dx + 3*d*dx*dx

        return np.where(mask, deriv, 0.0)



def fit_pulse_iterative(waveforms, pulse, t, t_data_peak, t_template_peak, n_iter=4):

    EC, N = waveforms.shape

    # initial alignment from DATA only
    dt = np.full((EC), t_data_peak - t_template_peak)   # (EC)
    A  = np.ones((EC))


    for _ in range(n_iter):

        # -------------------------
        # build shifted time grid
        # -------------------------
        # (EC, N)
        t_shift = t[None, :] - dt[:, None]

        # -------------------------
        # evaluate pulse
        # -------------------------
        P  = pulse.eval(t_shift)        # (EC, N)
        dP = pulse.derivative(t_shift) # (EC, N)

        # -------------------------
        # projections (sum over samples)
        # -------------------------
        Ap = np.sum(waveforms * P, axis=1)   # (EC)
        Ad = np.sum(waveforms * dP, axis=1)

        PP   = np.sum(P * P, axis=1)
        PdP  = np.sum(P * dP, axis=1)
        dPdP = np.sum(dP * dP, axis=1)

        # -------------------------
        # solve 2x2 system
        # -------------------------
        denom = PP * dPdP - PdP * PdP
        denom = np.clip(denom, 1e-12, None)

        A_new = (Ap * dPdP - Ad * PdP) / denom
        Ccorr = (Ad * PP - Ap * PdP) / denom

        # -------------------------
        # update
        # -------------------------
        dt += (-Ccorr / np.clip(A_new, 1e-12, None))
        A = A_new

    return A, dt



def run_fit(signal_window, mask_under_thr, spline_file, sampling_rate):
    Ts = 1/sampling_rate

    valid = ~mask_under_thr

    idx_valid = cp.where(valid)

    signal_window_valid = signal_window[idx_valid]

    segs = load_segments_txt(spline_file)
    pulse = PiecewiseCubicSplineNP(segs, Ts)

    t_grid = np.arange(signal_window_valid.shape[1]) * Ts

    pulse_values = pulse.eval(t_grid)
    t_pulse_peak = t_grid[np.argmax(pulse_values)]


    amp_valid, dt_valid = fit_pulse_iterative(
        signal_window_valid,
        pulse,
        t_grid,
        signal_samples_pre_peak,  # data peak (scalar)
        t_pulse_peak     # model peak (scalar)
    )

    fit_time_valid = dt + np.ones(dt.shape)*signal_samples_pre_peak*Ts + max_idx*Ts

    fit_t = np.zeros(mask_under_thr.shape, dtype=np.float32)

    fit_t[idx_valid] = fit_time_valid

    amp_fit = np.zeros(mask_under_thr.shape, dtype=np.float32)

    amp_fit[idx_valid] = amp_valid

    return (amp_fit, fit_t)
