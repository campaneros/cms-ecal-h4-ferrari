import timing.pseudo_t

def cf(signal_window, valid, max_idx, values_max, **kwargs):
  globals().update(kwargs)

  rise_valid = signal_window[valid, signal_samples_pre_peak - rise_samples_pre_peak:signal_samples_pre_peak + rise_samples_post_peak]
  thresholds = values_max * cf

  return {"time": timing.pseudo_t(rise_valid, valid, thresholds, sampling_rate, interpolation_factor, max_idx, rise_interp_left_samples, rise_interp_right_samples, rise_samples_pre_peak)}
