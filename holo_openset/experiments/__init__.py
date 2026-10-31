"""The experiments of the paper. Each module has main(argv) and writes to results/holo_openset:

  e2e           the YOLO localiser + every flow, strict protocol, on the 640 x 640 test windows
  robustness    every flow, trained and calibrated on the base acquisition, on the robustness sets
  oracle        the training-free pixel oracle (Wiener + threshold + pixel comparison), base set and robustness sets
  discovery     open-world discovery: clustering cut chosen with calibration twins, B-cubed on the test unknowns
  full_frames   full sensor frames (3840 x 2748 px, 29.4 mm^2): time and accuracy of every flow, end to end
  timing        time of every stage on one CPU core and on one GPU, from a 640 x 640 window to a full frame
  fidelity      fidelity of the reconstructions to the object (PSNR) and error of the autofocus
  gaps          what the idealised model leaves out (periodic boundary, the |o|^2 term), measured on the scenes
"""
