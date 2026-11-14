| flow | GPU front (ms), frame | GPU total (ms), frame | CPU front (s), frame | CPU total (s), frame | GPU front (ms), 640 | GPU total (ms), 640 | CPU front (ms), 640 | CPU total (ms), 640 | x stack 5, GPU frame (front / total) | x stack 5, CPU frame (front / total) |
|---|---|---|---|---|---|---|---|---|---|---|
| rec_z0 | 2.9 | 172 | 2.3 | 24.4 | 0.59 | 10.2 | 25.6 | 407 | 0.83 / 1.00 | 0.96 / 1.00 |
| rec_af | 126 | 295 | 119 | 141 | 5.4 | 15.0 | 3608 | 3990 | 35.71 / 1.71 | 49.10 / 5.75 |
| rec_afs † | 4.2 | 173 | 3.5 | 25.5 | 0.64 | 10.3 | 61.4 | 443 | 1.18 / 1.00 | 1.44 / 1.04 |
| rec_afsc † | 2.9 | 172 | 2.3 | 24.4 | 0.60 | 10.2 | 25.7 | 407 | 0.83 / 1.00 | 0.96 / 1.00 |
| rec_afM † | 15.2 | 184 | 14.0 | 36.0 | 1.1 | 10.7 | 384 | 765 | 4.32 / 1.07 | 5.77 / 1.47 |
| rec_afc | 4.5 | 174 | 3.4 | 25.4 | 1.1 | 10.8 | 38.7 | 420 | 1.28 / 1.01 | 1.39 / 1.04 |
| rec_afr | 14.1 | 183 | 11.8 | 33.9 | 1.4 | 11.0 | 174 | 555 | 4.00 / 1.06 | 4.88 / 1.38 |
| rec_edfw | 210 | 379 | 166 | 188 | 7.8 | 17.4 | 5074 | 5455 | 59.47 / 2.19 | 68.67 / 7.69 |
| prop | 1.1 | 170 | 0.78 | 22.8 | 0.13 | 9.8 | 4.2 | 385 | 0.31 / 0.99 | 0.32 / 0.93 |
| bank_jit | 3.5 | 173 | 2.4 | 24.5 | 0.19 | 9.8 | 25.2 | 406 | 1.00 / 1.00 | 1.00 / 1.00 |
| bank_wide | 4.7 | 174 | 3.1 | 25.2 | 0.23 | 9.9 | 46.5 | 428 | 1.34 / 1.01 | 1.30 / 1.03 |
| bank_w2 | 5.9 | 175 | 4.1 | 26.2 | 0.28 | 9.9 | 62.9 | 444 | 1.68 / 1.01 | 1.69 / 1.07 |

Sums of measured stage times (timing_gpu.csv: minimum of the repetitions; timing_cpu.csv: one core, median), NOT measurements end to end. Total = front end + yolo_tiled + embed + decide. † amortised: rec_afs (search / n), rec_afM (search / 10), rec_afsc (search / n), n = 100 (a session of the dataset). Frame = 3840 x 2748 px, 640 = the 640 x 640 window. Timing from e5 (GPU) and e5 (CPU).
Composition: rec_z0 = flat_field + backprop + channels; rec_af = flat_field + autofocus + backprop + channels; rec_afs = flat_field + autofocus/n + backprop + channels; rec_afsc = flat_field + autofocus_afc/n + backprop + channels; rec_afM = flat_field + autofocus/10 + backprop + channels; rec_afc = flat_field + autofocus_afc + backprop + channels; rec_afr = flat_field + autofocus_afr + backprop + channels; rec_edfw = flat_field + autofocus + per_object_wide + channels; prop = layer_prop; bank_jit = layer_bank_jit; bank_wide = layer_bank_wide; bank_w2 = layer_bank_w2.
