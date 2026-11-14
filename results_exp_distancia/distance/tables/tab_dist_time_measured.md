| flow | read (ms) | compute (ms) | embed + decide (ms) | without the detector (ms) | total with the detector (ms) | x stack 5 | F1 end to end |
|---|---|---|---|---|---|---|---|
| rec_z0 | 17.9 | 3.3 | 3.7 | 25.6 | 204 | 1.08 | 0.975 ± 0.006 |
| rec_af | 17.8 | 126.5 | 3.9 | 148.3 | 326 | 1.73 | 0.975 ± 0.005 |
| rec_afs † | 17.9 | 27.9 | 3.7 | 49.5 | 228 | 1.20 | 0.975 ± 0.005 |
| rec_afsc † | 17.8 | 3.6 | 3.6 | 25.1 | 203 | 1.07 | 0.975 ± 0.005 |
| rec_afc | 17.7 | 5.1 | 3.6 | 26.4 | 205 | 1.08 | 0.975 ± 0.005 |
| rec_afr | 17.8 | 14.6 | 3.6 | 36.1 | 214 | 1.13 | 0.975 ± 0.005 |
| rec_edfw | 17.9 | 209.2 | 3.9 | 230.9 | 409 | 2.16 | 0.972 ± 0.009 |
| prop | 2.8 | 1.2 | 3.6 | 7.6 | 186 | 0.98 | 0.973 ± 0.008 |
| bank_jit | 2.8 | 3.6 | 4.6 | 11.1 | 189 | 1.00 | 0.974 ± 0.004 |
| bank_wide | 2.8 | 4.9 | 5.0 | 12.6 | 191 | 1.01 | 0.940 ± 0.006 |
| bank_w2 | 2.8 | 6.1 | 5.5 | 14.4 | 192 | 1.02 | 0.944 ± 0.012 |

Timed run of the full frames in e5, one GPU. read = load (layers) or normalise (reconstructions: read the frame and the blank frame and normalise); compute = reconstruction, search of the distance, per-object focus, channels or layer. read, compute, embed + decide: medians over frames and repetitions of each group; "without the detector": median over frames and repetitions of the sum of all the stages of the flow in a frame (so the three groups do not add up to it exactly); total = that + the detector (178.1 ms, median). x stack 5: total over the total of bank_jit. F1 on the detected boxes, mean (repetitions present: r1, r2, r3, r4, r5).
† the search of the distance ran on the first frame of each session only: its median over the frames where it ran is divided by the frames of a session of the set (rec_afs: 5, rec_afsc: 5).
