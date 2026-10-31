# The equipment behind the simulation

Why the simulator uses the values it uses. **Confirmed** means the cited source states it; **inferred** is our
conclusion from the source; **unconfirmed** is still open.

## The reference bench

Sobieranski et al., *Portable lensless wide-field microscopy imaging platform based on digital inline holography and
multi-frame pixel super-resolution*, Light: Science & Applications 4, e346 (2015), DOI 10.1038/lsa.2015.119.

| item | what the paper says | status |
|---|---|---|
| source | UV LED of 385 nm, Thorlabs M385L2 | confirmed |
| aperture | LED in a cylinder with a pinhole of "100 mm" at 15 cm from the sensor | confirmed; 100 um is inferred (likely a typo) |
| LED bandwidth | not stated | unconfirmed; 10 nm is typical of UV LEDs of this kind |
| sensor | monochrome Aptina CMOS, 10 MP, 1.67 um pixel, 3840 x 2748 px, 6.413 x 4.589 mm | confirmed |
| file | 8-bit raw data from the SDK | confirmed; file format unconfirmed |
| sample-to-sensor distance | "as small as possible"; no value in the text | unconfirmed; 50,000 wavelengths = 19.25 mm is the value of the laboratory routine and of the public dataset |
| reconstruction | angular spectrum method; the twin image is not removed | confirmed |
| autofocus | not mentioned | unconfirmed |
| super-resolution | 49 frames with the source shifted; 1.55 um resolution on about 30 mm2 | confirmed |

**Open question.** A 100 um pinhole at 15 cm, with the sample at 19.25 mm, blurs the hologram by about 13 um. That
suits objects of tens of micrometres but not the 1.55 um resolution of the 2015 paper, which suggests a smaller
distance or pinhole on the bench. We keep 19.25 mm and also study a sample at 2 mm.

## Image size

One frame of the bench has 3840 x 2748 px: 10.55 MP, about 10.5 MB at 8 bits, 29.4 mm2. The 640 x 640 window of the
dataset is 1/26 of that area. It is the processing unit of the dataset, not the size of an acquisition.

## Other lensless set-ups

* **Ozcan group (UCLA).** LED of 10-20 nm band with a pinhole of about 50-100 um at a few centimetres, sample under
  1 mm from the sensor. Greenbaum et al., Nat. Methods 9, 889 (2012).
* **imec.** 10 MP sensor with 1.67 um pixels and about 30 mm2. Stahl et al., Proc. SPIE 8947 (2014).
* **LED or laser.** A laser gives more coherence, but also speckle and multiple reflections, and costs more. LED and
  pinhole are the norm in low-cost lensless microscopy.

## Reconstructions in practice

| step | in practice | here |
|---|---|---|
| blank-frame division | hologram divided by the background without the sample | `sqrt(I/B)` |
| propagation | angular spectrum or Fresnel, one FFT pair per distance | `rec_z0` |
| autofocus | sweep the distance, keep the sharpest (Zhang et al., Opt. Lett. 2017) | `rec_af`, 73 + 41 candidates |
| per-object focus | a stack of distances, each object in its plane | `rec_edf` |
| twin-image removal | iterative with constraints (Latychevskaia & Fink, PRL 98, 233901, 2007) | `rec_twin`, 50 passes |
| pixel super-resolution | several shifted frames | not simulated: every compared route works on one frame |

The bench itself does back-propagation at a known distance, plus super-resolution. Autofocus and twin-image removal
come from the literature.

## Scale of the objects

The letters of the base set are about 75-210 um wide, far larger than the platelets (2-3 um) and sperm heads (3-5 um) imaged
on the bench, which cover 1-3 px without super-resolution. Letters are a controlled stand-in for objects whose classes
differ by shape. The small-object sets cover 20-60 um.
