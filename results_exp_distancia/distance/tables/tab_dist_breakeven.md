| stack | search | GPU search (ms) | GPU D (ms; % of the layer) | GPU n* | GPU n* raw | GPU n* ±3 % | GPU n* raw, e5_a1 | GPU n* simple | GPU per frame (x) | CPU search (s) | CPU D (s; % of the layer) | CPU n* | CPU n* raw | CPU n* ±3 % | CPU n* simple | CPU per frame (x) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bank_jit | blind | 123 | 0.60 (17 %) | 205 | 205 | 155–304 | 212 | 48 | 35.7 | 116 | 0.106 (4 %) | ≈ same cost | 1099 | 470–never | 83 | 49.1 |
|  | afc | 1.6 | 0.60 (17 %) | 2.6 | 2.6 | 2.0–3.9 | 2.7 | 0.6 | 1.3 | 1.0 | 0.106 (4 %) | ≈ same cost | 9.9 | 4.2–never | 0.7 | 1.4 |
|  | afr | 11.2 | 0.60 (17 %) | 19 | 19 | 14–28 | 19 | 4.4 | 4.0 | 9.5 | 0.106 (4 %) | ≈ same cost | 90 | 38–never | 6.7 | 4.9 |
| bank_wide | blind | 123 | 1.80 (38 %) | 68 | 68 | 61–78 | 69 | 33 | 26.7 | 116 | 0.824 (26 %) | 141 | 141 | 118–176 | 55 | 37.9 |
|  | afc | 1.6 | 1.80 (38 %) | 0.9 | 0.9 | 0.8–1.0 | 0.9 | 0.4 | 1.0 | 1.0 | 0.824 (26 %) | 1.3 | 1.3 | 1.1–1.6 | 0.5 | 1.1 |
|  | afr | 11.2 | 1.80 (38 %) | 6.2 | 6.2 | 5.5–7.1 | 6.2 | 3.0 | 3.0 | 9.5 | 0.824 (26 %) | 12 | 12 | 9.6–14 | 4.5 | 3.8 |
| bank_w2 | blind | 123 | 3.01 (51 %) | 41 | 41 | 38–45 | 41 | 25 | 21.2 | 116 | 1.784 (44 %) | 65 | 65 | 59–73 | 38 | 29.0 |
|  | afc | 1.6 | 3.01 (51 %) | 0.5 | 0.5 | 0.5–0.6 | 0.5 | 0.3 | 0.8 | 1.0 | 1.784 (44 %) | 0.6 | 0.6 | 0.5–0.7 | 0.3 | 0.8 |
|  | afr | 11.2 | 3.01 (51 %) | 3.7 | 3.7 | 3.4–4.1 | 3.7 | 2.3 | 2.4 | 9.5 | 1.784 (44 %) | 5.3 | 5.3 | 4.8–6.0 | 3.1 | 2.9 |

Full frame. n*: frames per mounting above which searching the distance once per mounting is cheaper than the focal stack. Complete accounting (the main figure): n* = T_search / D, D = T_layer − T_conv, T_conv = T_flat_field + T_backprop + T_channels; simple (protocol, Q2): T_conv = T_backprop; "never": the stack is cheaper at every n. Rule: a crossover is not resolved by the measurement when moving T_layer and T_conv by ±3 % in opposite directions flips the sign of D (printed "≈ same cost": the stack costs the same as one reconstruction) or changes n* by more than a factor 2 (printed as the range n* takes inside ±3 %). Raw: n* as computed, kept for the record; e5_a1: the other GPU attempt of the timing session (min_s), the same stages measured again (not mixed into any time). All values, with ±1 % too: tab_dist_breakeven.csv. Per frame: the front end of the search on every image (rec_af, rec_afc, rec_afr) over the front end of the stack, n = 1. Sums of measured stage times; timing from e5 (GPU, minimum) and e5 (CPU, one core, median).
