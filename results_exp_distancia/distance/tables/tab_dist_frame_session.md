| metric | flow | base | frame_5 | session_5 | predicted for its 8 draws | predicted, paired with base | Monte Carlo: mean (5–95 %) | percentile of session_5 |
|---|---|---|---|---|---|---|---|---|
| F1 | rec_z0 | 0.964 | 0.865 | 0.753 | 0.745 | 0.746 | 0.856 (0.751–0.936) | 5 |
|  | prop | 0.963 | 0.865 | 0.749 | 0.740 | 0.742 | 0.855 (0.750–0.934) | 5 |
|  | bank_jit | 0.963 | 0.924 | 0.839 | 0.825 | 0.827 | 0.917 (0.858–0.955) | 2 |
| Known | rec_z0 | 0.953 | 0.790 | 0.625 | 0.615 | 0.617 | 0.778 (0.625–0.904) | 5 |
|  | prop | 0.951 | 0.788 | 0.620 | 0.609 | 0.612 | 0.776 (0.623–0.901) | 5 |
|  | bank_jit | 0.952 | 0.884 | 0.748 | 0.729 | 0.733 | 0.875 (0.776–0.937) | 2 |

frame_5 and session_5 have the same nominal distance distribution (5 %), drawn per image (800 draws) and per session (8). Predicted: 100 images per session of session_5 drawn from the frame_5 images whose |z / z0 - 1| is in the bin of that session (bins 0-1-2-3-4-6-8-10-12 %), metrics of the strict protocol on the pooled queries, 200 draws, mean over r1-r5; paired: the same drawn scenes minus their value in the base set, plus the base value. Monte Carlo: 1000 draws of 8 sessions from N(0, 5 %), each predicted the same way. F1: open-set F1; Known: accepted and correct share of the seen classes. scripts/exp_distancia/frame_vs_session.py; frame_vs_session_mc.csv.
