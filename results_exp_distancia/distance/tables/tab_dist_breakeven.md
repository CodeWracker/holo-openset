| stack | search | GPU search (ms) | GPU n* | GPU n* simple | GPU per frame (x) | CPU search (s) | CPU n* | CPU n* simple | CPU per frame (x) |
|---|---|---|---|---|---|---|---|---|---|
| bank_jit | blind | 123 | 205 | 48 | 35.7 | 116 | 1099 | 83 | 49.1 |
|  | afc | 1.6 | 2.6 | 0.6 | 1.3 | 1.0 | 9.9 | 0.7 | 1.4 |
|  | afr | 11.2 | 19 | 4.4 | 4.0 | 9.5 | 90 | 6.7 | 4.9 |
| bank_wide | blind | 123 | 68 | 33 | 26.7 | 116 | 141 | 55 | 37.9 |
|  | afc | 1.6 | 0.9 | 0.4 | 1.0 | 1.0 | 1.3 | 0.5 | 1.1 |
|  | afr | 11.2 | 6.2 | 3.0 | 3.0 | 9.5 | 12 | 4.5 | 3.8 |
| bank_w2 | blind | 123 | 41 | 25 | 21.2 | 116 | 65 | 38 | 29.0 |
|  | afc | 1.6 | 0.5 | 0.3 | 0.8 | 1.0 | 0.6 | 0.3 | 0.8 |
|  | afr | 11.2 | 3.7 | 2.3 | 2.4 | 9.5 | 5.3 | 3.1 | 2.9 |

Full frame. n*: frames per mounting above which searching the distance once per mounting is cheaper than the focal stack. Complete accounting (the main figure): n* = T_search / (T_layer − (T_flat_field + T_backprop + T_channels)); simple (protocol, Q2): n* = T_search / (T_layer − T_backprop); "never": the stack is cheaper at every n. Per frame: the front end of the search on every image (rec_af, rec_afc, rec_afr) over the front end of the stack, n = 1. Sums of measured stage times; timing from e5 (GPU, minimum) and e5 (CPU, one core, median).
