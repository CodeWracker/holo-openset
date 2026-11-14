# Parâmetros do simulador: valor e fonte de cada um

Tarefa Z7 (segunda atualização do orientador, 2026-11-14 ≈ 14:10, em `PROTOCOLO_Z.md`): "uma tabela com todos os
parâmetros do simulador, o valor e a fonte de cada um (artigo, datasheet ou suposição nossa)". Feita pelo subagente
"levantamento-z" a partir do **código**, não da memória: `holo_openset/sim/physics.py` (dataclass `Physics` e
constantes do módulo), `holo_openset/sim/scene.py`, `holo_openset/sim/letters.py`, `holo_openset/sim/generate.py`,
`holo_openset/sim/variants.py`, e o `physics.json` do conjunto base (`data/realistic/physics.json`, que confere com os
valores padrão do código; `small_near` difere só em `z0 = 0.002`, `small_z0` em nada, os dois com o layout `small`).
Comparado com a tabela `tab:sim` de `../latex-openset-microscopy/sections/03b-bench.tex` (valores das macros em
`figures/paper/numbers.tex`) e com `docs/EQUIPMENT.md`. Nenhum desses arquivos foi alterado.

Versão legível por máquina: `results_exp_resolucao/simulator_parameters.csv` (colunas `parameter, code_name, value,
unit, models, source_type, source, page, quote, depends_on_z, note`; a citação literal e a nota completa de cada linha
estão lá).

## Classificação das fontes

- **artigo**: um texto que li, com página e citação literal (o artigo de 2015 e o suplemento, ou os trabalhos de
  `LEVANTAMENTO_Z.md`).
- **datasheet**: documento do fabricante, com revisão/data e página.
- **comunicação pessoal**: o que o prof. Sobieranski disse ao orientador e o orientador nos repassou (lamínula quase
  encostada no sensor, sem encostar porque ele esquenta; sem inclinação, só pequenas deformidades locais; brilho
  ajustado à mão com o shutter e o ganho analógico; LED M385L2 de 385 nm com 10 nm FWHM "no datasheet").
- **suposição nossa**: escolha nossa; a nota diz no que se apoia, se em algo.

A coluna "depende de z": `relative` = o parâmetro é definido como fração de z; `tuned` = valor dimensionado para
19,25 mm; `effect` = o valor não depende de z, mas o efeito dele no holograma cresce ou muda com z; `no` = não depende.

## As duas fontes novas desta tarefa

**LED (consegui a especificação).** A ficha em PDF do M385L2 continua inacessível (o catálogo arquivado da Thorlabs
responde com página anti-robô; o arquivo `thorcat/20900/M385L2-SpecSheet.pdf` não tem cópia no Wayback Machine). Mas a
**página de produto da Thorlabs "Mounted LEDs" (objectgroup_id=2692), aba Specs, capturada pelo Wayback Machine em
2015-05-04** (http://web.archive.org/web/20150504085727/http://www.thorlabs.com:80/newgrouppage9.cfm?objectgroup_id=2692),
tem a tabela de especificações com as colunas "Item # | Color | Nominal Wavelength | Minimum LED Power Output | Typical
LED Power Output | Maximum Current (CW) | Forward Voltage | Bandwidth (FWHM) | Viewing Angle (FWHM) | Chip Size |
Typical Lifetime" e a linha:

> "M385L2 | UV | 385 nm | 270 mW | 430 mW | 700 mA | 4.3 V | 10 nm | 120° | 1 mm x 1 mm | >10,000 h"

Logo, 10 nm FWHM tem fonte de fabricante (especificação na página do produto, não a ficha em PDF), e coincide com o que
o autor disse. Cópia em `../referencias/z/thorlabs_m385l2_wayback/group2015.html`. Isso corrige a seção 7 de
`LEVANTAMENTO_Z.md`, que dizia que a largura não tinha fonte lida.

**Sensor.** O artigo não dá o modelo; identifico-o com o onsemi MT9J003 pelas dimensões (ver `LEVANTAMENTO_Z.md`
2.1b). Do datasheet (MT9J003/D, Rev. 7, agosto de 2024; mesmos números na Rev. E de 05/2015), p. 2, "Table 1. KEY
PARAMETERS": "Pixel Size 1.67 x 1.67 µm"; "ADC Resolution 12-bit, On-die"; "Dynamic Range 65.2 dB"; "SNRMAX 34 dB";
"Color Filter Array RGB Bayer Pattern" (o artigo diz monocromático). p. 30: "The default settings of the sensor provide
a 3840 (H) x 2748 (V) image". p. 54: vidro de 0,4 mm, n = 1,5255, topo do vidro a 0,525 ± 0,05 mm do chip. O
datasheet **não dá** full well nem ruído de leitura em elétrons; se a SNR máxima for limitada por ruído de disparo,
34 dB implicam ~10^3,4 ≈ 2500 e⁻, e a faixa dinâmica de 65,2 dB implica ~2500/1820 ≈ 1,4 e⁻ de ruído de leitura
(contas minhas, não do datasheet).

## Tabela

| # | parâmetro | nome no código | valor (unidade) | fonte | página | depende de z |
|---|---|---|---|---|---|---|
| 1 | comprimento de onda central | `physics.WAVELENGTH` | 385 nm | **artigo** (Sobieranski 2015) | p. 2 | no |
| 2 | largura de banda do LED (FWHM) | `Physics.bandwidth` | 10 nm | **datasheet** (Thorlabs, tabela Specs, 2015) | aba Specs | effect |
| 3 | forma do espectro | `physics.wavelengths()` | gaussiana | **suposição nossa** | - | no |
| 4 | nós em comprimento de onda | `Physics.n_wavelengths` | 7 | **suposição nossa** (numérico) | - | effect |
| 5 | diâmetro do pinhole | `Physics.pinhole` | 100 µm | **artigo** | p. 2 | effect |
| 6 | distância do pinhole | `Physics.source_distance` | 0,15 m (código: até a amostra) | **artigo** (diz: até o **sensor**) | p. 2 | relative |
| 7 | tamanho do emissor do LED (não modelado) | — | 1 × 1 mm | **datasheet** (Thorlabs) | aba Specs | no |
| 8 | passo do pixel | `physics.PIXEL` | 1,67 µm | **artigo** (+ datasheet p. 2) | p. 2 | no |
| 9 | quadro inteiro | `physics.FULL_FRAME` | 3840 × 2748 px | **artigo** (+ datasheet p. 30) | p. 2 | no |
| 10 | área do sensor (derivada) | — | 6,413 × 4,589 mm | **artigo** (+ datasheet p. 54) | p. 2 | no |
| 11 | profundidade de bits | `Physics.bits` | 8 bits | **artigo** (ADC de 12 bits no datasheet) | p. 2 | no |
| 12 | full well | `Physics.full_well` | 6000 e⁻ | **suposição nossa** | - | no |
| 13 | ruído de leitura | `Physics.read_noise` | 3 e⁻ rms | **suposição nossa** | - | no |
| 14 | exposição | `Physics.exposure` | 0,45 do fundo de escala | **suposição nossa** | - | no |
| 15 | PRNU | `Physics.prnu` | 1 % rms | **suposição nossa** | - | no |
| 16 | abertura do pixel | `Physics.pixel_mtf` | caixa de 1 pixel | **suposição nossa** | - | no |
| 17 | grandeza registrada | `Physics.intensity` | intensidade \|U\|² | **suposição nossa** (física do detector) | - | no |
| 18 | modelo de propagação | `physics.propagate` | Fresnel, exp(−iπλz\|f\|²), em ar | **suposição nossa** (padrão, paraxial) | - | no |
| 19 | distância amostra–sensor | `physics.Z0`, `Physics.z0` | 19,25 mm | **suposição nossa** (unidade z×λ do suplemento; valor 50k da rotina) | SI, "Diffraction Calculation" | tuned |
| 20 | variação de z entre sessões | `Physics.session_z_std` | 0,5 % de z0 | **suposição nossa** | - | relative |
| 21 | variação de z por imagem | `Physics.frame_z_std` | 0 no base (2 %, 5 % nas variantes) | **suposição nossa** | - | relative |
| 22 | deriva de z por imagem | `Physics.frame_z_walk` | 0 no base (0,5 %/imagem em `walk_05`) | **comunicação pessoal** (o sensor esquenta) | - | relative |
| 23 | inclinação do plano da amostra | `Physics.tilt_deg` | 0° | **comunicação pessoal** (sem inclinação) | - | no |
| 24 | espalhamento de profundidade | `Physics.depth_std`, `depth_max` | 50 / 150 µm | **suposição nossa** | - | effect |
| 25 | absorção das letras | `absorption_mean/std/min` | 0,5 / 0,25 / 0,02 (máx. 1) | **suposição nossa** | - | no |
| 26 | fase das letras | `phase_mean/std/max` | 1,0 / 0,5 / 2,5 rad (mín. 0) | **suposição nossa** | - | no |
| 27 | classes | `letters.CLASSES` | 26 (A–Z) | **suposição nossa** (desenho do estudo) | - | no |
| 28 | fontes tipográficas | `letters.FONTS`, `AUX_FONTS` | 3 principais (DejaVuSans, DejaVuSerif, STIXGeneral); 25 auxiliares | **suposição nossa** | - | no |
| 29 | tamanho das letras (base) | `scene.Layout.font_min/max` | fonte de 70–118 px (caixas ~45–125 px, 75–210 µm) | **suposição nossa** | - | effect |
| 30 | tamanho das letras (conjuntos pequenos) | `scene.SmallLayout.font_min/max` | fonte de 16–48 px (12–36 px, 20–60 µm) | **suposição nossa** | - | effect |
| 31 | letras por janela | `scene.Layout.letters_*` | média 8, dp 3, 3–18 por 640 × 640 (fração distinta 0,72; borda 12 px; espaçamento 6 px) | **suposição nossa** | - | no |
| 32 | rotação | `scene.Layout.rotation` | ±35° | **suposição nossa** | - | no |
| 33 | letras fora da janela | `scene.make_scene` (reach) | mesma densidade de dentro; ~133 por janela | **suposição nossa** | - | no |
| 34 | janela | `physics.WINDOW` | 640 × 640 px (1,14 mm²) | **suposição nossa** (herdada do dataset público anterior, não lido aqui) | - | no |
| 35 | margem simulada | `Physics.margin` | 1728 px | **suposição nossa** | - | tuned |
| 36 | alcance dos objetos de fora | `Physics.reach` | 1024 px (1,7 mm) | **suposição nossa** | - | tuned |
| 37 | poeira no vidro | `Physics.dust_density` | 2 partículas/mm² por superfície | **suposição nossa** | - | no |
| 38 | profundidade das superfícies de vidro | `Physics.dust_depths` | +1,0 e −0,2 mm da amostra | **suposição nossa** (espessuras batem com lâmina de 1,0 mm e lamínula 0,17 mm, mas usadas como distância em ar) | - | effect |
| 39 | poeira na janela do sensor | `Physics.sensor_dust_density` | 7 partículas/mm² | **suposição nossa** | - | no |
| 40 | distância da janela do sensor | `Physics.sensor_dust_z` | 0,5 mm | **datasheet** (MT9J003 p. 54: 0,525 mm geométrico) | p. 54 | effect |
| 41 | forma da poeira | `scene.dust_mask`, `make_dust` | semieixo exp(N(ln 3; 0,6)) px em [1, 25]; absorção U(0,3; 1); fase U(0; 1,5) rad | **suposição nossa** | - | no |
| 42 | cintura do feixe | `Physics.beam_waist` | 2,0–3,5 semidiagonais (uniforme por sessão) | **suposição nossa** | - | no |
| 43 | descentramento do feixe | `Physics.beam_offset_std` | 0,18 semidiagonal | **suposição nossa** | - | no |
| 44 | quadros em branco por sessão | `generate.N_BLANKS` | 8 | **suposição nossa** | - | no |
| 45 | imagens por sessão | `per_session` | 100 | **suposição nossa** | - | no |
| 46 | sessões e partições | `generate.split_sessions` | 50 sessões; 35/7/8 (treino/val/teste); 5000 imagens | **suposição nossa** (protocolo) | - | no |
| 47 | sementes | `seed`, `CAMERA_SEED` | 17 / 7 | **suposição nossa** (implementação) | - | no |
| 48 | ganho analógico (não modelado) | — | — | **comunicação pessoal** (ajustado à mão) | - | no |

Citações das linhas com fonte (todas do PDF do editor de Sobieranski et al. 2015, p. 2, salvo indicação):
1: "an ultraviolet LED of 385 nm, model M385L2 from ThorLabs was used"; 5 e 6: "LED was placed in a cylindrical
structure with 100 µm diameter pinhole located 15 cm away from the sensor"; 8: "1.67 µm of pixel-size"; 9: "spatial
resolution of 3840 × 2748 pixels"; 10: "dimensions of 6.413 mm × 4.589 mm (≈30 mm²)"; 11: "8-bit raw data can be
directly accessed from the sensor via Software Development Kit"; 19: suplemento, "We used z×λ to compute the distance
between the object and the detector plane" (a unidade; o valor 50 000 vem da rotina do laboratório, que não é
publicação); 2 e 7: a linha da tabela da Thorlabs citada acima; 40: datasheet MT9J003 p. 54, "0.525±0.05", "(0.125)",
"4. List material: Borosilicate glass 0.4 thickness. Refractive index at 20°C = 1.5255 @ 546 nm".

## Contagem

Das 48 linhas, 45 são parâmetros do simulador (ficam de fora da contagem o tamanho do emissor do LED, a área do sensor,
que é derivada do quadro e do pixel, e o ganho analógico, que não é modelado):

| fonte | parâmetros |
|---|---|
| artigo | **6** (comprimento de onda, pinhole, distância do pinhole, pixel, quadro inteiro, bits) |
| datasheet | **2** (largura de banda do LED; distância da janela do sensor) |
| só comunicação pessoal | **2** (inclinação = 0; deriva de z por aquecimento, usada só na variante `walk_05`) |
| só suposição nossa | **35** |

Das 35 suposições, 16 são escolhas de desenho, numéricas ou de implementação (nós espectrais, grandeza registrada,
modelo de propagação, classes, fontes, tamanhos de letra base e pequeno, letras por janela, rotação, letras de fora,
janela, margem, alcance, imagens por sessão, sessões/partições, sementes) e 19 são **valores físicos sem fonte**:
forma do espectro, full well, ruído de leitura, exposição, PRNU, abertura do pixel, z0, variação entre sessões,
variação por imagem, espalhamento de profundidade, absorção, fase, densidade de poeira, profundidade das superfícies,
poeira do sensor, forma da poeira, cintura e descentramento do feixe, número de quadros em branco. Destes, z0 é o que
muda as conclusões; full well e ruído de leitura agora têm uma referência indireta (o datasheet do MT9J003, ver acima)
que sugere valores menores que os nossos (~2500 e⁻ e ~1,4 e⁻ contra 6000 e⁻ e 3 e⁻).

Algumas suposições têm apoio qualitativo sem valor: a comunicação pessoal sustenta que iluminação e exposição mudam por
sessão (linhas 14, 42, 43, 44) e que há pequenas variações locais de profundidade (linha 24); a faixa da literatura de
`LEVANTAMENTO_Z.md` sustenta os 10 nm (faixa "a few nanometers to 20–30 nm", Greenbaum 2012) e o pinhole de
50–150 µm.

## Parâmetros que dependem de z ou foram dimensionados para 19,25 mm

- **z0 = 19,25 mm** (linha 19): o valor em discussão; a proposta de `LEVANTAMENTO_Z.md` é 0,7 mm em ar (faixa
  0,5–1,1 mm).
- **session_z_std = 0,5 % de z** (linha 20), **frame_z_std** e **frame_z_walk** (21, 22): relativos. 0,5 % é 96 µm a
  19,25 mm e 3,5 µm a 0,7 mm; uma remontagem real a ~0,7 mm varia pela folga de ar (~0,1 mm estimado, sem fonte),
  ou seja ~15 %. Se z0 mudar, esses percentuais precisam ser redefinidos (ou passados para valores absolutos).
- **source_distance** (linha 6): o borrão é D·z/L com L = distância pinhole–amostra; o código usa L = 0,15 m fixo, o
  artigo dá 15 cm até o sensor, então L = 0,15 − z. Diferença de 13 % a 19,25 mm, desprezível a 0,7 mm.
- **margin = 1728 px e reach = 1024 px** (35, 36): dimensionados para 19,25 mm (leitura minha: a franja mais fina que o
  pixel registra percorre λz/(2p²) = 1329 px a 19,25 mm; a 0,7 mm são 48 px). Folgados demais a 1 mm; só custam
  memória e tempo.
- **n_wavelengths = 7** (linha 4): a soma em comprimento de onda precisa de mais nós quanto maior z·Δλ·f²; verificada
  só a 19,25 mm; a 0,7 mm sobra.
- **depth_std = 50 µm, depth_max = 150 µm** (24): absolutos; a 19,25 mm são 0,3 % de z, a 0,7 mm são 7 % — o mesmo
  número representa uma amostra relativamente muito mais espessa.
- **dust_depths = +1,0 e −0,2 mm** (38) e **sensor_dust_z = 0,5 mm** (40): espessuras geométricas de vidro usadas como
  distâncias em ar (as efetivas seriam ~0,66, ~0,11 e ~0,39 mm). A 19,25 mm isso não importa; a 0,7 mm a poeira da
  janela do sensor fica a 0,7 − 0,5 = 0,2 mm das letras (em ar efetivo seriam 0,31 mm) e a poeira da face externa da
  lamínula fica a 0,5 mm do sensor, quase no plano da poeira da janela. Precisa ser revisto junto com z0.
- **tamanho das letras e espalhamento do padrão** (29, 30): o quanto do padrão de uma letra cabe no crop depende de z
  (é o assunto do estudo de distância e da comparação base × `small_near` pedida pelo orientador).
- **bandwidth e pinhole** (2, 5): os valores são do equipamento; o efeito deles (corte do envelope) depende de z.

## Discordâncias entre código, tabela do paper e `EQUIPMENT.md`

1. **Distância do pinhole.** Artigo: "100 µm diameter pinhole located 15 cm away from the sensor" (p. 2). Código
   (`physics.py`, docstring: "a pinhole of diameter `pinhole` at `source_distance` from the sample") e paper
   (`tab:sim`: "pinhole \SimPinhole µm at \SimSourceCm cm (blur \SimBlurUm µm)", com \SimBlurUm = 12.8, e 03b: "a 100 µm
   pinhole placed 15 cm away ... blurs the hologram by 12.8 µm"): tratam 15 cm como pinhole–amostra. Com 15 cm até o
   sensor, o borrão a 19,25 mm é 14,7 µm.
2. **"100 mm".** `EQUIPMENT.md`: "pinhole of '100 mm' at 15 cm from the sensor | confirmed; 100 um is inferred (likely a
   typo)". O PDF do editor diz 100 µm; o "100 mm" está só na versão do PMC (que também diz "15 cm" em vez de "5 cm"
   para a mesa xy).
3. **Largura de banda.** `EQUIPMENT.md`: "LED bandwidth | not stated | unconfirmed; 10 nm is typical of UV LEDs of this
   kind". Não está no artigo, mas a especificação da Thorlabs dá 10 nm FWHM para o M385L2 (acima). O valor do código está
   certo; o status em `EQUIPMENT.md` e a seção 7 de `LEVANTAMENTO_Z.md` ficam desatualizados.
4. **Citação da revisão.** `EQUIPMENT.md` atribui a Greenbaum et al. 2012 "LED of 10-20 nm band with a pinhole of about
   50-100 um at a few centimetres, sample under 1 mm from the sensor". O texto diz: banda "from a few nanometers to
   20–30 nm", amostra "typically ≤0.1–2 mm", pinhole "50–100 μm", e não dá a distância da fonte.
5. **z0.** `EQUIPMENT.md`: "50,000 wavelengths = 19.25 mm is the value of the laboratory routine and of the public
   dataset"; paper 03b: "z_0 = 5·10⁴λ = 19.25 mm ... we keep them". Agora contradito pela comunicação pessoal (z da
   ordem de 1 mm). A unidade (z × λ) é confirmada pelo suplemento.
6. **Lado da poeira.** Código: `dust_depths = (1.0e-3, -0.2e-3)`, comentário "far side of the slide, top of the
   coverslip"; no código, profundidade positiva aumenta a distância ao sensor, então −0,2 mm fica **entre a amostra e o
   sensor** (lamínula voltada para o sensor, como o autor descreve). Paper (`tab:sim`): "(1 mm below and 0.2 mm above
   the sample)" — só bate se o sensor estiver desenhado em cima; na bancada o sensor está embaixo ("CMOS imaging sensor
   is fixed from the bottom side of the platform", p. 2). A redação do paper deveria dizer "on the far side of the slide
   and on the coverslip, between the sample and the sensor". E "top of the coverslip" no comentário do código é ambíguo
   pelo mesmo motivo.
7. **Sensor monocromático × Bayer.** Artigo: "monochromatic sensor"; datasheet do MT9J003 lido: "RGB Bayer Pattern". O
   simulador (monocromático) segue o artigo; a identificação do modelo continua por comparação.
8. **Full well e ruído de leitura.** Código e paper: 6000 e⁻ e 3 e⁻. O datasheet não os dá diretamente; seus números
   (SNR máx. 34 dB, faixa dinâmica 65,2 dB) indicam ~2500 e⁻ e ~1,4 e⁻ (contas minhas). As variantes `fullwell_500`
   a `fullwell_24000` e `read_10` a `read_60` cobrem a faixa.
9. **Referência quebrada.** A docstring de `physics.py` remete a `docs/pesquisa_equipamento_e_protocolo.md`, que não
   existe no repositório (o equivalente atual é `docs/EQUIPMENT.md`).
10. **Ganho analógico.** O autor ajustava brilho com shutter e ganho analógico; o simulador modela só a exposição
    (fração do fundo de escala), sem ganho. Não é uma discordância de valor, é uma omissão a declarar.

Fora isso, os valores da tabela `tab:sim` (macros de `numbers.tex`) conferem com o código e com o `physics.json` do
conjunto base: absorção N(0,5; 0,25²) em [0,02; 1], fase N(1; 0,5²) em [0; 2,5], profundidade N(0; 50²) µm com
|δ| ≤ 150 µm, z por sessão com 0,5 %, poeira 2/mm² e 7/mm², janela do sensor a 0,5 mm, 10 nm com 7 comprimentos de
onda, pinhole 100 µm, 15 cm, cintura 2–3,5, descentramento 0,18, full well 6000 e⁻, exposição 45 %, leitura 3 e⁻,
PRNU 1 %, 8 bits, 8 brancos, 100 imagens por sessão, 35/7/8 sessões, margem 1728 px, alcance 1,7 mm.
