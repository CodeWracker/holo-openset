# Levantamento Z: a distância amostra–sensor de uma bancada lensless com LED e pinhole

Levantamento feito em 2026-11-14 (subagente "levantamento-z") para o Checkpoint Z (`PROTOCOLO_Z.md`, itens 2 e 3) e
para a atualização do orientador recebida durante o trabalho: o prof. Sobieranski confirmou que a lamínula fica muito
perto do sensor e só não encosta porque o sensor esquenta, ou seja, z da ordem de 1 mm. "No levantamento, o foco passa
a ser fechar esse número (lamínula + vidro do sensor + folga), com referências."

Regra seguida em todo o documento: **um número só aparece como valor de um trabalho se foi lido no próprio texto**, com
a página e um trecho literal (em inglês, como no original). O que é conta minha, hipótese ou comunicação pessoal está
marcado como tal. "Não informado" quer dizer que procurei e o texto lido não dá o valor.

Convenções de página: "p." é a página impressa do periódico quando o PDF do editor foi lido; "PDF p." é a página do
arquivo; para os manuscritos de autor lidos no PubMed Central (XML do PMC, sem paginação) dou a **seção** do artigo.
Os arquivos baixados estão em `../referencias/z/<chave>/` (fora do git); a URL de cada leitura está na seção 4.

---

## 0. Resumo: o orçamento da distância e o z proposto

**Orçamento** (detalhes, fontes e citações na seção 2). Distância geométrica = soma das espessuras; distância efetiva =
caminho equivalente em ar para a difração, Σ tᵢ/nᵢ (aproximação paraxial, seção 2.2). O sensor é tomado como o
Aptina/ON Semi **MT9J003** (o artigo de 2015 não dá o modelo, mas as dimensões que ele dá batem exatamente com a área
óptica do desenho do encapsulamento desse sensor; seção 2.1b).

| pilha (do objeto até os fotodiodos) | termos (mm) e fonte | geométrica mín / típ / máx (mm) | **efetiva em ar** mín / típ / máx (mm) |
|---|---|---|---|
| **A. amostra na face interna de uma lamínula tipo 1½ voltada para o sensor** (a montagem que a comunicação pessoal descreve) | lamínula 0,16 / 0,17 / 0,19 (ISO 8255-1, n = 1,5255) + folga de ar 0,05 / 0,2 / 0,5 (**sem fonte**: comunicação pessoal "não encosta"; valores meus) + vidro do sensor 0,4 (n = 1,5255) + folga vidro–chip 0,125 ± 0,05 (datasheet MT9J003, p. 54) | 0,69 / **0,90** / 1,27 | 0,49 / **0,70** / 1,06 |
| A1. idem com lamínula tipo 1 (0,13–0,17) | lamínula 0,13 / 0,15 / 0,17 + o resto como em A | 0,66 / 0,88 / 1,25 | 0,47 / 0,69 / 1,05 |
| B. amostra sobre uma lâmina de 1,0 mm deitada no sensor (lâmina para baixo) | lâmina 1,0 ± 0,05 (ficha Thermo, n = 1,5171) + folga 0,05 / 0,2 / 0,5 + pacote 0,525 ± 0,05 | 1,48 / 1,73 / 2,13 | 1,01 / 1,25 / 1,63 |
| C. vidro do sensor removido, lamínula sobre o chip | lamínula 0,16–0,19 + folga 0,02 / 0,1 / 0,3 (**sem fonte**) | 0,18 / 0,27 / 0,49 | 0,13 / 0,21 / 0,43 |
| referência da literatura: lâmina "directly atop the protective glass" de um MT9P031 (Bishara et al. 2011) | valor declarado no artigo | ≈ 0,7 | (não informado) |
| referência: alturas de Greenbaum & Ozcan 2012 (MT9P031, vidro protetor no lugar) | valores declarados | ~0,7 a ~1 | (não informado) |

Se a preparação líquida do esperma (10 µL sob lamínula de 8 × 8 mm, Sobieranski 2015 p. 5) se espalha por toda a
lamínula, a camada de líquido tem 10/64 ≈ 0,16 mm (conta minha); objetos não sedimentados podem estar até ~0,12 mm
efetivos (0,16/1,33) acima da face da lamínula. Isso é variação **dentro** da sessão (profundidade por objeto).

**z proposto para a bancada simulada: z = 0,7 mm de distância efetiva em ar** (geométrica ≈ 0,9 mm), faixa plausível
**0,5–1,1 mm** efetiva (pilha A), com a pilha B (1,25 mm efetiva) como alternativa "lâmina para baixo". Sustentam:
o próprio autor (comunicação pessoal ao orientador, sem página); o encapsulamento do sensor (0,525 mm do topo do vidro
ao plano da imagem, datasheet MT9J003 p. 54); a espessura normalizada da lamínula (ISO 8255-1); e os números que o grupo
de Ozcan declara para a mesma situação, "placed directly atop the protective glass of the image sensor, i.e.,
approximately z ≈ 0.7 mm" (Bishara 2011) e "to achieve a measurement with a lower Z2 distance, the sensor's protective
glass will have to be removed" com Z2 mínimo ~700 µm (Greenbaum & Ozcan 2012). Variação proposta: entre sessões,
σ ≈ 0,1 mm (dominada pela folga de ar, que não tem fonte; a tolerância da lamínula dá só ±0,01–0,02 mm e a do pacote
±0,05 mm); dentro da sessão, profundidades de 0 a ~0,12 mm efetivos para amostras líquidas e quase zero para amostras
secas ou sedimentadas.

**Coerência com as resoluções publicadas** (seção 6): com LED de 385 nm, 10 nm (largura **suposta**, seção 7), pinhole
de 100 µm a 15 cm, as fórmulas simples de corte de Zhang et al. (2020) dão, a 0,7 mm, meio-período limite de 0,94 µm
pela largura de banda e 0,23 µm pelo pinhole; a 19,25 mm, 4,9 µm e 7,4 µm. O artigo de 2015 resolve 2,76 µm com um
quadro e 1,55 µm com 49 quadros (suplemento): **incompatível com 19,25 mm, compatível com z ≲ 1,9 mm**, e o caso de
0,7 mm reproduz o quadro "pixel limita um quadro só; super-resolução de pixel ganha até o limite de coerência" que todos
os trabalhos de chip-scale descrevem.

---

## 1. Sobieranski et al. 2015 em detalhe

Referência: A. C. Sobieranski, F. Inci, H. C. Tekin, M. Yuksekkaya, E. Comunello, D. Cobra, A. von Wangenheim,
U. Demirci, "Portable lensless wide-field microscopy imaging platform based on digital inline holography and
multi-frame pixel super-resolution", *Light: Science & Applications* 4, e346 (2015), DOI 10.1038/lsa.2015.119.
Lidos: o PDF do editor (11 páginas) e o Supplementary Information (arquivo .docx do editor, sem paginação; cito pela
seção). Também li a versão do PMC (PMC5898403) e ela **diverge** do PDF em dois pontos (ver 1.6).

### 1.1 Geometria declarada (PDF do editor, p. 2, "Experimental setup")

Conferido na página renderizada (a camada de texto do PDF troca µ por "m"; na imagem lê-se µm):

> "In Figure 1a, a light-source is used to illuminate the samples with a pinhole (b), where an ultraviolet LED of
> 385 nm, model M385L2 from ThorLabs was used." (p. 2)

> "This chamber was projected to image samples using cover glasses or microfluidic channels (Figure 1c), and signatures
> are recorded by a CMOS sensor (Figure 1d) and a xy-stage having dimensions of 10 × 10 cm² placed 5 cm away from the
> sensor. On top of it, LED was placed in a cylindrical structure with 100 µm diameter pinhole located 15 cm away from
> the sensor. CMOS imaging sensor is fixed from the bottom side of the platform, where the distance between sample and
> electronic detector is as small as possible." (p. 2)

> "The CMOS sensor used to capture the hologram shadows is an Aptina 10 megapixel monochromatic sensor with dimensions
> of 6.413 mm × 4.589 mm (≈30 mm²), spatial resolution of 3840 × 2748 pixels, frame rate of 3.2 frames per second, and
> 1.67 µm of pixel-size. 8-bit raw data can be directly accessed from the sensor via Software Development Kit" (p. 2)

| grandeza | valor no artigo | onde |
|---|---|---|
| comprimento de onda | 385 nm (LED Thorlabs M385L2) | p. 2 |
| largura de banda | **não informada** (nem no texto principal nem no suplemento) | — |
| pinhole | 100 µm de diâmetro | p. 2 |
| pinhole–sensor | 15 cm (**até o sensor**, não até a amostra) | p. 2 |
| amostra–sensor | "as small as possible", sem número | p. 2 |
| sensor | Aptina, 10 MP, monocromático, 3840 × 2748, 1,67 µm, 6,413 × 4,589 mm, 3,2 fps, 8 bits; **modelo não informado** | p. 2 |
| deslocamento da fonte | "arbitrarily displaced (i.e., 1–2 mm)" (p. 9); "very small displacements (i.e., 1-2mm) of the light source" (SI, "Feature-based Image Registration") | p. 9; SI |
| quadros | "a displacement matrix of varied sifts of the light-source (7 × 7 different positions)" | p. 3 |
| resolução | "a spatial resolution of 1.55 µm on a field-of-view of ≈30 mm²" (resumo, p. 1; também p. 9) | p. 1, 9 |
| amostras | esperma: "10 µL was added on a glass slide, and mounted with an 8 × 8 mm cover slip" (p. 5); plaquetas: microcanais de PMMA (40,5 × 24,5 mm), fita adesiva dupla de 50 µm ("DSA, 50 µm for microchannel height") e "glass cover slide (40.5 × 24.5 mm)" (p. 5) | p. 5 |

O artigo **não diz de que lado** da lâmina/lamínula fica a amostra em relação ao sensor, nem a espessura da "glass cover
slide" do microcanal.

### 1.2 A super-resolução e as resoluções (Supplementary Information)

> "The obtained results show improvement of the resolution for the multiple 7×7 frames (group number 8 / Element 3
> (1.55 µm resolution)) compared to 3×3 frames (group number 7 / Element 6 (2.19 µm resolution)) and a single frame
> (group number 7 / Element 4 (2.76 µm resolution))." (SI, "Holographic Signal Resolution")

(O "×" é um símbolo da fonte Symbol no .docx; extraído como texto puro ele some e vira "33" e "77". Conferi no XML do
.docx: `w:sym w:font="Symbol" w:char="F0B4"`, que é ×. A figura S3 tem os rótulos "Single Frame", "3x3 frames",
"7x7 frames".) As três resoluções são **larguras de linha** do alvo USAF 1951 (G7E4 = 181 pl/mm → 2,76 µm;
G7E6 → 2,19 µm; G8E3 = 322,5 pl/mm → 1,55 µm), isto é, meio-período.

Tabela S1 do suplemento (comparação feita pelos autores): "Presented Approach | Arbitrary, automatic registration |
1.67 | ~1.55 | ~30"; "Ozcan`s Group | Precise with an array of 23 LED`s | 1.67, 2.4 | ~1 | ~24" (colunas: esquema,
pixel em µm, resolução em µm, FOV em mm²).

Como a super-resolução é feita (p. 3): registro por pontos-chave SURF + homografia por RANSAC, depois otimização
subpixel por colônia de formigas contínua (ACO_R) minimizando uma energia com termo de fidelidade e um termo de nitidez
(Laplaciano modificado), Eq. (1) p. 4. Tempo: "to acquire the LR set (by shifting the light-source) 2 minutes
approximately were required" (SI, "Computational Specifications and Analysis").

### 1.3 A Eq. (S3) e a unidade do "z = [30k, 45k, 60k, 70k]"

Legenda da Fig. 2 (p. 3, conferida na página renderizada):

> "Figure 2 Numerical diffraction of a sperm sample hologram. First to third rows the real (ℜ), imaginary (ℑ) and
> composition (ℜ + ℑ) parts of the diffraction are shown, respectively. Diffractive distances from the first to fourth
> columns are z = [30k, 45k, 60k, 70k] (k = x1000), according to Equation (S3) of Supplementary Information." (p. 3)

Suplemento, seção "Diffraction Calculation" (as equações S1–S3 são objetos OLE do MathType; li o texto delas nos
registros de texto das prévias WMF/EMF embutidas no .docx):

> "The diffractive distance between the source plane u(x1,y1) and the destination plane u(x,y) (detector-plane) is used
> as a parameter of the numerical diffraction calculation. **We used z×λ to compute the distance between the object and
> the detector plane**, where image is formed with a wavelength of the light-source λ. For HR holograms, a scale factor
> k is applied to up-sampling the distance z and make diffraction equivalent to the LR and HR images." (SI)

> Eq. (S3): H(f_x, f_y) = exp( i z √(k² − 4π²(f_x² + f_y²)) ) — "where k=2π /λ and z are used as the wave-number and
> the distance between object and detector plane." (SI; a raiz é desenhada como linha na prévia, os demais símbolos
> estão nos registros de texto)

Conclusão sobre a unidade: **no código descrito no suplemento, o "z" é adimensional e a distância física é z × λ**,
isto é, o z é contado em comprimentos de onda. Logo "z = 50k" = 50 000 λ = 19,25 mm e as colunas da Fig. 2 seriam
30 000–70 000 λ = 11,6–27,0 mm a 385 nm. A leitura "50k = 50 000 λ" do simulador **está de acordo com o suplemento**.

Mas o suplemento abre uma segunda possibilidade, que o texto não permite decidir: "For HR holograms, a scale factor k
is applied to up-sampling the distance z". Se a Fig. 2 for de hologramas super-resolvidos e o código mantiver o passo
de 1,67 µm para a imagem ampliada, a propagação só é equivalente com z multiplicado pelo quadrado do fator de ampliação
(escala de Fresnel: λ z f² invariante; conta minha). Com fator 7 (7 × 7 posições), 50 000 λ / 49 = 0,39 mm e
30k–70k → 0,24–0,55 mm. **Isto é hipótese**, a ser testada no código da bancada (tarefa Z1 do subagente "piloto"); o
artigo não diz se a Fig. 2 é LR ou HR nem qual é o fator. O "k" da legenda (k = ×1000) e o "k" do suplemento (fator
de escala; também o número de onda) são três usos da mesma letra.

### 1.4 O que o artigo permite concluir sobre z, mesmo sem número

1. Física simples (seção 6): com o pinhole de 100 µm a 15 cm e LED de ~10 nm, a 19,25 mm o holograma não guarda
   franjas mais finas que ~5–7 µm de meio-período, mas o artigo resolve 2,76 µm com **um quadro** e 1,55 µm com 49.
   Isso exige z efetivo ≲ 6 mm (um quadro) e ≲ 1,9 mm (49 quadros), se a banda for 10 nm.
2. Contagem de franjas (inferência minha, a partir de p. 7): "Generally, LR holograms present periodicity until the
   seventh or eighth cycle, although intensities are also well-described by the HR holograms. For a higher number of
   cycles, the correspondence between LR and HR is lost". Se o que corta as franjas no LR é o pixel (e não a
   coerência; é o que a melhora com HR sugere), o período local da n-ésima franja de um objeto pontual,
   √(λz/2n), vale 2 pixels em n ≈ 7–8, o que dá z ≈ 2n(2p)²/λ ≈ **0,41–0,46 mm**. A 19,25 mm a 8ª franja teria
   período de ~21 µm (13 pixels), bem amostrada, e a super-resolução não teria o que recuperar.
3. Deslocamento da fonte de 1–2 mm a ~15 cm desloca o holograma de s·z/L (Bishara 2010, Eq. 3, com o fator n do
   vidro): a 0,7 mm, ~5–9 µm (3–6 pixels); a 19,25 mm, ~150–300 µm. O artigo diz que o registro não depende de passos
   pequenos ("the system is unconstrained to relatively small steps of the light-source", p. 9), então este ponto
   **não** discrimina z; registro aqui só para não ser usado como argumento.
4. O autor confirmou ao orientador (comunicação pessoal, sem página) que a lamínula fica quase encostada no sensor.

### 1.5 Respostas às perguntas do protocolo sobre o artigo de 2015

- Unidade do z da Eq. (S3): comprimentos de onda (z × λ), com fator de escala adicional para hologramas HR, não
  especificado.
- Distância amostra–sensor: não há número no artigo nem no suplemento.
- Pinhole–amostra: o artigo dá pinhole–**sensor** = 15 cm; pinhole–amostra = 15 cm − z.
- Largura de banda do LED: não está no artigo (seção 7).

### 1.6 Divergências entre o PDF do editor e a versão do PMC

No XML do PMC (PMC5898403), a mesma frase diz "a xy-stage having dimensions of 10 × 10 cm2 placed **15 cm** away from
the sensor. On top of it, LED was placed in a cylindrical structure with **100 mm** diameter pinhole located 15 cm away
from the sensor." O PDF do editor diz "**5 cm**" e "**100 µm**" (conferido na imagem da p. 2). Vale o PDF do editor.
O "100 mm (likely a typo)" de `docs/EQUIPMENT.md` provavelmente veio do HTML/PMC: no artigo de registro está 100 µm.

---

## 2. Orçamento da distância (lamínula + vidro do sensor + folga)

### 2.1 Os termos, com fonte

**(a) Lado da amostra e espessura do vidro entre amostra e sensor.**

O que os trabalhos lidos dizem sobre a montagem:

| trabalho | montagem declarada | trecho e local |
|---|---|---|
| Sobieranski 2015 | esperma em lâmina sob lamínula 8 × 8 mm; plaquetas em microcanal sobre "glass cover slide"; lado não informado | "10 µL was added on a glass slide, and mounted with an 8 × 8 mm cover slip" (p. 5) |
| Bishara 2011 | lâmina com a amostra sobre o vidro protetor do sensor, z ≈ 0,7 mm | "The object slide to be imaged (e.g., a blood smear) is placed directly atop the protective glass of the image sensor, i.e., approximately z ≈ 0.7 mm away from the active area of the sensor chip (Aptina MT9P031I12STM; complementary metal-oxide-semiconductor—CMOS)" (PMC3151573, parágrafo do arranjo) |
| Greenbaum & Ozcan 2012 | lamínulas de 50–250 µm entre amostra e sensor dão Z2 de ~0,7 a ~1 mm; abaixo disso, só removendo o vidro do sensor | "The Z2 distance is controlled by placing glass cover slips with different thicknesses between the sample and the sensor-chip. The thicknesses of our glass cover slips varied between 50 µm and 250 µm, hence the corresponding Z2 distances varied between ~0.7 mm and ~1 mm." (seção 7); "The lowest measurement plane is typically taken with a Z2 value of ~700 µm ... Note that to achieve a measurement with a lower Z2 distance, the sensor's protective glass will have to be removed." (seção 5) |
| Mudanyali 2010 | esfregaço sobre lamínula "type 0"; objetos de teste em lamínulas "type-1" de 150 µm | "1µL of sample was dropped on the top of a type 0 glass cover slip" (Sample preparation); "Borosilicate type-1 cover glasses (150µm thickness)" (Fabrication of test objects) |
| Tseng 2010 | esfregaço sobre lamínula tipo 1 | "1 μL of sample was dropped on the top of a type 1 glass cover slip" (Sample preparation) |
| Seo 2009 | solução em lâmina coberta por lamínula, posta sobre a área ativa | "a total solution volume of 10–100 µl is dropped on a microscope slide using a micro-pipette and gently sandwiched by another identical cover glass. Then, the sample is positioned using a vacuum pen ... onto the active region of the sensor array." (Set-up) |
| Luo 2016 | grades sobre lâmina de vidro de ~100 µm; amostra a 100–500 µm do sensor | "fabricated on a ~100 μm glass slide (N-BK7, Schott AG)" (PDF p. 3); "placed 100–500 μm above the image sensor chip" (PDF p. 3) |
| Greenbaum 2013 | substrato fino de ~50 µm, folga com óleo, 50–150 µm do sensor (CMOS de 1,12 µm) | "smeared on a thin glass substrate (~50 μm). During the lensfree imaging process, the vertical distance between the objects and the image sensor surface was on the order of 50–150 μm. This gap between the substrate and image sensor planes is filled with a refractive index matching oil" (p. 7) |
| Zhang et al. 2020 (revisão do problema) | o vidro protetor impõe 0,3–2 mm | "due to the existence of protective glass covering the surface of the camera sensor, there is usually always a certain distance between the sample plane and the detector plane (typically 0.3−2 mm)" (arXiv v1, PDF p. 3) |
| Isikman 2012 (revisão) | amostra diretamente sobre o sensor, < 4 mm | "the sample is placed directly on the top of an optoelectronic sensor array (such as a CMOS chip) with typically <4 mm vertical distance to its active area" (seção II) |

Espessuras normalizadas (fontes de fabricante/norma):

- **Lamínula**, ISO 8255-1:2011 (2ª edição, 2011-04-15; prévia gratuita do iTeh; a norma vigente é a 3ª edição,
  2017, que não li), Tabela 1, p. 2 (PDF p. 6): "Type 1½ | 0,17 | +0,02 −0,01"; "Type 1½ H | 0,17 | +0,005 −0,005";
  "Type 1 | 0,17 | +0,00 −0,04" (mm). Ou seja, tipo 1½: 0,16–0,19 mm; tipo 1: 0,13–0,17 mm. Índice, p. 3 (PDF p. 7):
  "Principal refractive index: n = 1,525 5 ± 0,001 5" (a 546,07 nm). "In addition to the thicknesses given in Table 1,
  cover glasses are available in other thicknesses" (p. 2). Tipo 0 e tipo 2 não estão na prévia; não tenho fonte para
  eles.
- **Lâmina**, ficha da Thermo Scientific (Menzel-Gläser) "objekttraeger_uk_0715_0209", p. 2: "Manufactured in
  accordance with ISO 8037/I dimensions: 26 x 76 x 1.0 mm"; "Thickness tolerance ±0.05 mm"; "Refractive index: At
  λ = 546.07 nm = 1.5171".

Montagem da bancada: o artigo não diz; a comunicação pessoal (a lamínula quase encosta no sensor) indica **lâmina por
cima, lamínula para baixo, voltada para o sensor**. Espermatozoides mortos tendem a sedimentar sobre a superfície de
baixo, que nessa montagem é a lamínula (inferência minha; o artigo diz só "Sperm samples were incubated on the glass
slides until they are metabolically dead", p. 5).

**(b) Vidro protetor do sensor e folga até o chip.**

O artigo de 2015 **não dá o modelo** do sensor ("an Aptina 10 megapixel monochromatic sensor", p. 2). O candidato é o
Aptina (hoje onsemi) **MT9J003**, 1/2,3", 10 MP, pixel de 1,67 µm: o desenho do encapsulamento iLCC de 48 pinos cota a
área óptica em "(6.413 CTR)" × "(4.589 CTR)" mm, exatamente as dimensões que o artigo dá para o sensor (6,413 mm ×
4,589 mm = 3840 × 2748 pixels de 1,67 µm). É uma identificação **por comparação**, não confirmada pelo artigo; o
datasheet descreve a versão colorida ("The output from the sensor is a Bayer pattern", p. 3) e o artigo diz
monocromático. Datasheet lido: onsemi "MT9J003/D", Rev. 7, agosto de 2024 (com marca d'água "DISCONTINUED" na página do
encapsulamento); conferido também na Rev. E (05/2015, cópia da The Imaging Source), Figura 33, p. 74, com os mesmos
números.

Página 54 (Rev. 7), "PACKAGE DIMENSIONS, ILCC48 10x10, CASE 847AK", corte A–A (lido na imagem ampliada do desenho; a
atribuição de cada cota a um par de superfícies é **minha leitura** das linhas de chamada, conferida pela soma das
espessuras das notas):

- "0.525±0.05" — do topo do vidro (lid) ao plano do chip (superfície de imagem);
- "(0.125)" — folga entre a face interna do vidro e o chip (cota de referência);
- "0.725±0.075" — do plano de assentamento ao plano do chip; altura total "(1, 25)";
- notas: "4. List material: Borosilicate glass 0.4 thickness. Refractive index at 20°C = 1.5255 @ 546 nm and
  1.5231 @ 588 nm."; "6. Image sensor die 0.2 thickness."; "Maximum tilt of optical area relative to top of cover
  glass: 20 microns." e, na linha seguinte, "... 50 microns." (duas tolerâncias de inclinação, sem explicação).

Consistência: 0,4 (vidro) + 0,125 (ar) = 0,525 mm. O encapsulamento alternativo tPLCC (Rev. E, Figura 34, p. 75) tem
"Gloss thickness: 300mm typ." (sic: 300 µm) e outra geometria; não sei qual dos dois a câmera da bancada usa.

Se a câmera da bancada tiver uma janela ou filtro de proteção adicional, ele soma à pilha; o artigo não diz nada e a montagem descrita ("CMOS imaging sensor is fixed from the bottom side of the
platform", p. 2) sugere sensor nu. **Não verificado.**

O que os artigos dizem sobre o vidro do sensor: Greenbaum & Ozcan 2012 (acima: abaixo de ~0,7 mm, só removendo o
vidro); Bishara 2011 ("directly atop the protective glass", z ≈ 0,7 mm, sensor MT9P031 de 2,2 µm); Bishara 2010, Eq. 3
usa "n2 = 1.5 is the refractive index of the cover glass before the detector array" (seção 3); Tseng 2010 e Isikman
2012 removem a **lente** do celular ("whose lens is physically removed", Isikman 2012, seção III.B), não o vidro.
Nenhum dos trabalhos lidos dá a espessura do vidro protetor do seu sensor.

**(c) Folga de ar entre a lamínula e o vidro do sensor.** Só há a comunicação pessoal do prof. Sobieranski ao
orientador (não encosta porque o sensor esquenta; **sem página**). Não achei valor na literatura. No orçamento usei
0,05 / 0,2 / 0,5 mm como mínimo / típico / máximo — **escolha minha**, sem fonte. O aquecimento do sensor tem fonte:
"the surface temperature of the sensor chip can easily reach above 40 °C after 'continuous' operation for, for
example, more than 10 min" (Greenbaum et al. 2012, Nat. Methods, seção "Imaging speed"), e o mesmo texto diz que o
problema é menor nos holográficos "because of the greater distance (for example, 1–2 mm) between the sample and the
sensor chip". Sobre **deriva térmica da distância** (o z mudar com o aquecimento) não encontrei nada nos trabalhos
lidos.

### 2.2 Distância geométrica e distância efetiva

Uma placa de vidro de espessura t e índice n entre a amostra e o sensor equivale, para a difração paraxial, a t/n de
ar: no meio o comprimento de onda é λ/n, e o termo de Fresnel exp(−iπ λ z f²) vira exp(−iπ (λ/n) t f²), isto é,
z_ef = t/n. É uma aproximação de livro-texto (óptica de Fourier paraxial; não li a página de um livro para citar,
então fica marcada como aproximação); fora do paraxial o kernel do espectro angular no vidro, √(n²/λ² − f²), não se
reduz exatamente a um z em ar. A mesma razão 1/n aparece com fonte em Bishara 2010, Eq. 3, para o deslocamento do
holograma: "S_hologram/S_aperture = z2/z1 × n1/n2, where n1 = 1 is the refractive index of air, and n2 = 1.5 is the
refractive index of the cover glass before the detector array" (seção 3). Por isso o borrão do pinhole também usa a
distância efetiva: d = D · z_ef / L. Luo 2016 corrige o índice do substrato por comprimento de onda ("the refractive
index of the glass substrate (100 μm, N-BK7, Schott AG, Mainz, Germany) at each wavelength is also corrected using the
dispersion formula for borosilicate glass", PDF p. 3), o que mostra que o grupo trata o vidro explicitamente na
reconstrução.

**O z que o simulador deve usar é o efetivo** (ele propaga em ar). A dispersão do vidro (n de 1,5255 a 546 nm; um
pouco maior a 385 nm, valor que não tenho de fonte) muda z_ef em menos de 1 % e pode ser ignorada.

### 2.3 Tabela do orçamento

Termos (mm), com índice; geométrica = Σt; efetiva = Σt/n. Contas em
`/home/jovyan/privado/.persist/.cache/tmp/claude-1000/-home-jovyan-compartilhado-ralph-openset-microscopy/2460bd2f-62a2-4eb8-bda4-b04332eeb593/scratchpad/levz/budget.py`.

| pilha | termo | mín | típ | máx | n | fonte |
|---|---|---|---|---|---|---|
| A | lamínula tipo 1½ | 0,16 | 0,17 | 0,19 | 1,5255 | ISO 8255-1:2011, Tab. 1, p. 2; índice p. 3 |
| A | folga de ar lamínula–vidro do sensor | 0,05 | 0,20 | 0,50 | 1 | **sem fonte** (comunicação pessoal: "não encosta"); valores meus |
| A | vidro do sensor | 0,40 | 0,40 | 0,40 | 1,5255 | MT9J003/D Rev. 7, p. 54, nota 4 |
| A | folga vidro–chip | 0,075 | 0,125 | 0,175 | 1 | idem, cota (0,125) e tolerância ±0,05 da cota 0,525 (atribuí a tolerância toda à folga) |
| **A** | **total** | **0,685** | **0,895** | **1,265** | | geométrica |
| **A** | **efetiva** | **0,49** | **0,70** | **1,06** | | Σt/n |
| A1 | igual a A com lamínula tipo 1 (0,13 / 0,15 / 0,17) | 0,655 / 0,875 / 1,245 geom. | | | | efetiva 0,47 / 0,69 / 1,05 |
| B | lâmina 1,0 ± 0,05 (n = 1,5171) + folga + pacote | 1,475 / 1,725 / 2,125 geom. | | | | efetiva 1,01 / 1,25 / 1,63; ficha Thermo p. 2 |
| C | lamínula + folga 0,02 / 0,1 / 0,3 (vidro removido) | 0,18 / 0,27 / 0,49 geom. | | | | efetiva 0,13 / 0,21 / 0,43; folga sem fonte |
| todas | + camada líquida (objetos em suspensão) | 0 | — | 0,16 | 1,33 | 10 µL / (8 × 8 mm), conta minha com os dados da p. 5 |

Comparação com a literatura: pilha A típica (0,90 mm geométrica) está entre o "z ≈ 0.7 mm" de Bishara 2011 (lâmina
diretamente sobre o vidro de um MT9P031, sem folga declarada) e o "~1 mm" de Greenbaum & Ozcan 2012; os dois
declaram a distância sem dizer se é geométrica ou efetiva.

### 2.4 Variação entre sessões e dentro da sessão

- Tolerância da lamínula: ±0,01–0,02 mm (ISO), isto é, ±0,01 mm efetivos. Pequena.
- Tolerância do pacote: ±0,05 mm (datasheet). Fixa para um sensor (não varia entre sessões).
- Folga de ar: é o termo que varia a cada montagem, e o único sem fonte. A comunicação pessoal sugere que ela é
  ajustada à mão para não encostar e que muda com o aquecimento; não há número. Proposta: σ_sessão ≈ 0,1 mm em z_ef
  (≈ 15 % de 0,7 mm). Se o simulador mantiver a forma `z ~ z0(1 + N(0, s²))`, isso é s ≈ 15 %.
- Dentro da sessão: amostras secas ou sedimentadas na lamínula ficam num plano (mais as "pequenas deformidades do
  material" que o autor mencionou ao orientador); amostras líquidas espalham objetos por até ~0,12 mm efetivos acima
  da lamínula. Inclinação: o datasheet admite até 20–50 µm de inclinação da área óptica em relação ao topo do vidro
  (p. 54), ou seja, ~±0,02 mm de variação de z ao longo do chip.

---

## 3. A tabela do levantamento

Legenda: λ/Δλ = comprimento de onda / largura de banda; D = pinhole ou núcleo da fibra; L = fonte–amostra (z1);
z = amostra–sensor (z2); PSR = super-resolução de pixel. "n.i." = não informado no texto lido. Referências no
formato autores, ano, periódico, volume, páginas, DOI. Todos os valores estão citados com local na seção 4.

| # | referência | λ / Δλ | D | L (z1) | z (z2) | pixel / sensor | PSR ou outro passo sintético | resolução declarada (tipo) | FOV |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Sobieranski et al. 2015, Light Sci. Appl. 4, e346, 10.1038/lsa.2015.119 | 385 nm (LED M385L2) / n.i. | 100 µm | 15 cm até o **sensor** | "as small as possible" (n.i.) | 1,67 µm; Aptina 10 MP mono, 3840 × 2748 | sim, deslocamento manual da fonte, 3 × 3 e 7 × 7 | 2,76 µm (1 quadro), 2,19 µm (9), 1,55 µm (49): largura de linha USAF | ≈30 mm² |
| 2 | Mudanyali et al. 2010, Lab Chip 10, 1417–1428, 10.1039/c000453g | 591 nm / 18 nm (LED) | 50 ou 100 µm | ~2–5 cm | "<1–2 mm" | 2,2 µm; MT9P031, 5 MP | não (recuperação iterativa de fase; holograma interpolado 4–6×) | "~1–2 µm"; fenda de 1,94 µm FWHM resolvida (menor detalhe) | ~24 mm² |
| 3 | Tseng et al. 2010, Lab Chip 10, 1787–1792, 10.1039/c003477k | 587 nm / ~20 nm (LED) | ~100 µm | ~4 cm | "<2 mm" | ~2,2 µm (sensor RGB de celular, 5 MP) | não | "~1.5–2 µm" para sensor mono de mesmo pixel (sub-pixel), pior com o RGB | ~23,8 mm² |
| 4 | Seo et al. 2009, Lab Chip 9, 777–787, 10.1039/b813943a | monocromador (350–1000 nm) / n.i. — **não é LED** | ~100 µm | ~5 cm | exemplo Z = 625 µm (também Z = 200 µm no sistema antigo) | 2,2 µm (MT9P031); 9,0 µm (KAI-10002) | não | não informada (citometria) | n.i. no trecho lido |
| 5 | Bishara et al. 2010, Opt. Express 18, 11181–11191, 10.1364/OE.18.011181 | 500–600 nm / ~5 nm (lâmpada de Xe + monocromador) — **não é LED** | fibra ~50 µm | ~10 cm | ~0,75 mm | 2,2 µm, 5 MP | sim, 36 quadros (L = 6), também 5, 12 e 16 | ~0,6 µm com PSR (largura 1/e da derivada da fase); "<2µm" e NA < 0,2 sem PSR | ~24 mm² |
| 6 | Bishara et al. 2011, Lab Chip 11, 1276–1279, 10.1039/c0lc00684j | 633 nm / ~15–20 nm filtrado a ~10 nm (LED) | fibra 105 µm | 3–6 cm | ≈0,7 mm (lâmina sobre o vidro protetor) | ~2,2 µm; MT9P031 | sim, 23 LEDs/fibras | "<1 µm" com PSR (espaçamento de 1 µm resolvido) | ~24 mm² |
| 7 | Greenbaum & Ozcan 2012, Opt. Express 20, 3129–3143, 10.1364/OE.20.003129 | 550 nm (também 490) / ~5 nm (lâmpada de Xe + monocromador) — **não é LED** | fibra 100 µm | ~10 cm | ~0,7–1 mm (multialtura) | 2,2 µm; MT9P031 | sim, ~16 quadros por altura, 2–5 alturas | letras a ~1 µm de distância separadas (menor detalhe) | ~24 mm² |
| 8 | Greenbaum et al. 2012, Nat. Methods 9, 889–895, 10.1038/nmeth.2114 (**Perspective: faixas típicas**) | LED; banda "a few nanometers to 20–30 nm" | "50–100 μm" | n.i. | "typically ≤0.1–2 mm" | 1,1 µm (CMOS 16 MP) e 6,8 µm (CCD) nos exemplos | sim, "typically ~10–100" quadros; até 100 | meio-período <350 nm (530 nm, CMOS 1,1 µm); ~2,19 µm (CCD 6,8 µm) | ~20,5 mm²; ~18 cm² |
| 9 | Isikman et al. 2012, IEEE J. Sel. Top. Quantum Electron. 18, 1059–1072, 10.1109/JSTQE.2011.2161460 (**revisão: faixas típicas**) | LED / "1–15 nm" | "d~0.1 mm"; "~0.05–0.1 mm" | "z1~4–10 cm" | "<4 mm"; "<2mm" (celular) | n.i. de forma geral | — | "typically been ~1.5 μm" sem PSR (sistemas de um LED) | ~24 mm² |
| 10 | Greenbaum et al. 2013, Sci. Rep. 3, 1717, 10.1038/srep01717 | 480 nm / ~4 nm (fonte n.i.); 372 nm (LED) / n.i. | n.i. | n.i. | ~390 µm (CCD); 50–150 µm com óleo (CMOS) | 6,8 µm (CCD KAF-39000, **pixel grande**); 1,12 µm (CMOS cor) | sim (deslocamento da fonte; nº de quadros n.i.) + deconvolução da função do pixel | CCD: 5,52 µm (1 quadro), ~2,2 µm (PSR), ~1,74 µm (PSR + deconv.), meio-período; CMOS: linha de 225 nm | ~18 cm²; ~20 mm² |
| 11 | Luo et al. 2016, Light Sci. Appl. 5, e16060, 10.1038/lsa.2016.60 | 480–513 nm / ~2 nm por linha (supercontínuo sintonizável) — **não é LED** | n.i. (fibra) | n.i. | 100–500 µm | 1,12 µm (Sony IU081, cor) | sim: 5 ou 9 deslocamentos, ou 5–12 comprimentos de onda | menor meio-período 0,98 µm (1 quadro), 0,69 / 0,62 µm (5 / 9 deslocamentos), ~0,25 µm (com multialtura/abertura sintética) | >20 mm² |
| 12 | Kesavan et al. 2014, Sci. Rep. 4, 5942, 10.1038/srep05942 (CEA-Leti) | 525 nm (LED) / n.i. | 150 µm | ~5 cm | n.i. ("without considering distance to sensor") | 2,2 µm; MT9P031 RGB | não | não resolve extensões de 3–5 µm | n.i. no trecho lido |
| 13 | Agbana et al. 2017, Opt. Lett. 42, 2271–2274, 10.1364/OL.42.002271 | 635 nm / 0,8 nm (fonte Thorlabs S1FC635 em fibra monomodo) — **não é LED** | fibra monomodo | onda plana; ou fonte a Z = 16 mm | 2, 13 e 26 mm (plano); L* = 2, 8,5, 26 mm (divergente) | 1,67 µm; UI-1942LE, 3840 × 2748 (**mesmo formato da bancada**) | não | G7E5, "feature width of 2.5µm" (configuração ótima) | n.i. |
| 14 | Zhang, Sun, Chen, Zuo 2020, IEEE Trans. Comput. Imaging 6, 697–710, 10.1109/TCI.2020.2964247 (li o preprint arXiv:1906.06231v1) | LED, 460/520/620 nm, filtros de 20 e 30 nm | pinholes de 1,0 e 1,3 mm com difusor | 4; 7,5; 12,5; ~20 cm | 465 µm; 547 µm; 1499 µm | 1,67 µm (DMM 27UJ003-ML); também 2,2, 3,75, 4,4 µm | não (análise de resolução sem PSR) | meio-período ~1,953 µm (20 nm, z = 1,499 mm) e ~2,461 µm (30 nm); ~6,20 µm (pinhole 1 mm a 4 cm) | n.i. |
| 15 | Amann, von Witzleben, Breuer 2019, Sci. Rep. 9, 11260, 10.1038/s41598-019-47689-1 | 430 nm / 15 nm FWHM (LED) | 15 µm | 24,09 mm | 5,91 mm (fonte–sensor 30 mm; ampliação ≈1,25) | 1,12 µm (Raspberry Pi Cam v2) | não | G7E1, "line width of 3.91 μm" (LED); 1,55 µm com diodo laser | n.i. |

---

## 4. Citações por trabalho (página e URL de leitura)

### 4.1 Sobieranski et al. 2015
PDF: https://www.nature.com/articles/lsa2015119.pdf ; suplemento:
https://static-content.springer.com/esm/art%3A10.1038%2Flsa.2015.119/MediaObjects/41377_2015_BFlsa2015119_MOESM186_ESM.docx ;
PMC: PMC5898403 (via NCBI E-utilities efetch). Citações na seção 1.

### 4.2 Mudanyali et al. 2010 (PMC2902728, manuscrito de autor, NIHMS206727; seções)
- Lab Chip 10(11):1417–1428, DOI 10.1039/c000453g (metadados do PMC).
- Lensfree Holographic Microscope Design: "The LED source (OSRAM Opto Semiconductors Inc., Part# LY E65B – center
  wavelength: 591 nm, bandwidth: 18 nm) is butt-coupled to a 50 or 100 µm pinhole without the use of any focusing or
  alignment optics, illuminating the entire FOV of ~24 mm2 (CMOS chip, Model: MT9P031, Micron Technology – pixel size:
  2.2 µm, 5 Mpixels). ... Following Figure 1, typical z1 and z2 distances used in our design are ~2–5 cm and <1–2 mm,
  respectively."
- Introduction: "achieves ~1–2 µm resolution (sufficient to image e.g., sub-cellular structures in a blood smear) over
  a large field of view (FOV) of ~24 mm2".
- Results: "the gap between the squares is estimated as 1.94 µm (FWHM) from the reconstructed image cross-section ...
  Considering the fact that the pixel size at the sensor is 2.2 µm, this result implies a sub-pixel resolution".
- Image reconstruction: "the raw holograms are upsampled typically by a factor of four to six, using cubic spline
  interpolation before the iterative reconstruction procedure".
- Discussion: "Bringing the object plane much closer to the sensor surface together with a fringe magnification of F~1
  is one of the key steps in making lensless microscopy possible with a large incoherent source".

### 4.3 Tseng et al. 2010 (PMC2941438; seções)
- Lab Chip 10(14):1787–1792, DOI 10.1039/c003477k.
- Design of lensfree cellphone microscope: "The LED source (OSRAM Opto Semiconductors Inc., Part# LY E63B-CBEA-26-1-Z –
  Center wavelength: 587 nm, Bandwidth: ~20 nm) is butt-coupled to a ~100 μm pinhole ... illuminating the entire FOV of
  ~23.8 mm2 of the cell-phone camera chip. Following Fig. 1, typical distances used in our design are ~4 cm between the
  source and the sample; and <2 mm between the sample and the sensor planes."
- Results and discussion: "The spatial resolution of our reconstructions, under unit fringe magnification, is limited
  by the pixel size at the sensor, which in our case was ~2.2 μm for each color pixel. For a monochrome sensor of the
  same pixel size, we can normally achieve a sub-pixel resolution of ~1.5–2 μm".

### 4.4 Seo et al. 2009 (PMC3931575; seções)
- Lab Chip 9(6):777–787, DOI 10.1039/b813943a.
- Set-up: "we used a digital monochromator (Oriel Cornerstone™ 260–1/4m, Newport) along with a standard grade fused
  silica fiber which consists of a bundle of 250µm diameter fibers (77564, Newport). For Holographic-LUCAS experiments,
  we used a pinhole diameter of ~100 µm placed ~5 cm above the sensor array."
- Results: "sampled with a pixel size of 2.2 µm"; "even at a larger sample-to-sensor distance of Z = 625 µm"; sistema
  antigo: "a pixel size of 9.0 µm, under λ = 400 nm and at Z = 200 µm".

### 4.5 Bishara et al. 2010 (PMC2898729, NIHMS204745; seções)
- Opt. Express 18(11):11181–11191, DOI 10.1364/OE.18.011181.
- 3. Experimental setup: "We use a spatially incoherent light source (Xenon lamp attached to a monochromator,
  wavelength: 500-600 nm, spectral bandwidth: ~5nm) coupled to an optical fiber with a core size of ~50μm, which also
  acts as a large pinhole/aperture. The distance between the fiber end and the object plane (z1 ~10cm) is much larger
  than the distance between the object and the detector planes (z2 ~ 0.75mm). Our detector is a CMOS sensor with
  2.2μm×2.2μm pixel size, and a total active area of ~24.4 mm2."
- Eq. 3 (mesma seção): "n1 = 1 is the refractive index of air, and n2 = 1.5 is the refractive index of the cover glass
  before the detector array. For z1 = 10cm and z2 = 0.75mm, the ratio between these two shifts become
  Shologram/Saperture ~1/200".
- 4. Results: "Initially we used L = 6, i.e., we shifted the object holograms by one sixth of a pixel in each
  direction, for a total of 36 lensfree holograms."; "The 1/e width of all the peaks shown in Fig. 3(e) is ≤ 0.6μm,
  which leads to the conclusion that our resolution is ~0.6μm with an NA of ~0.5."
- 1. Introduction: "the finite pixel size at the sensor chip can unfortunately record holographic oscillations
  corresponding to only an effective NA of ~0.1-0.2, which limits the spatial resolution to <2µm."
- Bishara 2010 também resume o trabalho anterior do grupo: "a spatially incoherent light source that is filtered by an
  unusually large aperture (~50-100µm diameter) ... the large aperture of the illumination source is now geometrically
  de-magnified by a factor that is proportional to M=z1/z2 which is typically 100-200."

### 4.6 Bishara et al. 2011 (PMC3151573; parágrafos)
- Lab Chip 11(7):1276–1279, DOI 10.1039/c0lc00684j.
- Arranjo: "each LED (OSRAM TOPLED SuperRed, 633 nm) is butt-coupled to an individual multi-mode fiber-optic waveguide
  with a core diameter of 105 μm ... The bandwidth of each LED is ~15–20 nm, but it is filtered down to ~10 nm using a
  simple colour filter ... The object slide to be imaged (e.g., a blood smear) is placed directly atop the protective
  glass of the image sensor, i.e., approximately z ≈ 0.7 mm away from the active area of the sensor chip (Aptina
  MT9P031I12STM ...), and a distance of 3–6 cm away from the fiber-optic cables."
- "achieves a wide field-of-view (FOV) of ~24 mm2 together with a resolution of <1 μm. At the heart of this
  field-portable microscope lies an array of 23 multi-mode fiber-optic waveguides".
- Fig. 2: "A raw lensfree hologram ... is undersampled due to relatively large pixel size (~2.2 μm)"; Fig. 3: "The
  spacing between the letters "U" and "C" in this etched pattern is 1 μm, and the two letters are clearly resolved".

### 4.7 Greenbaum & Ozcan 2012 (PMC3364049; seções)
- Opt. Express 20(3):3129–3143, DOI 10.1364/OE.20.003129.
- 3.: "It is composed of a partially-coherent light source (Xenon lamp attached to a monochromator, with bandwidth of
  ~5 nm), that is coupled to a multi-mode fiber (100 µm core diameter). The fiber-tip to sample distance (Z1) is
  ~10 cm, while the sample to sensor distance (Z2) is ~0.7-1 mm (Fig. 1). The detector is a CMOS chip (Aptina MT9P031,
  5 Mega-pixel) with a 2.2µm pixel size."
- 5.: "The lowest measurement plane is typically taken with a Z2 value of ~700 µm ... Note that to achieve a
  measurement with a lower Z2 distance, the sensor's protective glass will have to be removed. The highest intensity
  measurement is typically taken with a Z2 value of ~1 mm".
- 7.: "The thicknesses of our glass cover slips varied between 50 µm and 250 µm, hence the corresponding Z2 distances
  varied between ~0.7 mm and ~1 mm."; "one SR hologram is synthesized from the LR image-stack (typically 16 images in
  each stack)"; "the letters 'U' and 'C' are ~1 µm apart" e "are clearly separated".
- 1.: LEDs "placed at ~3-6 cm away from the sample plane"; "the presented technique can work with a spectral
  illumination bandwidth of e.g., ~5-10 nm and a spatial coherence diameter of e.g., < 0.5 mm at the detector plane."

### 4.8 Greenbaum et al. 2012, Nat. Methods (PMC3477589, Perspective; seções)
- Nat. Methods 9(9):889–895, DOI 10.1038/nmeth.2114.
- Key components: "The spectral bandwidth of the source can vary from a few nanometers to 20–30 nm depending on the
  sample-to-detector distance and the resolution requirement of the system. Because the sample plane is close to the
  detector plane (typically ≤0.1–2 mm), the scattered light rays and the background light can still interfere at the
  sensor chip".
- Idem: "the spatial coherence diameter that is required at the sampling plane is small, typically less than
  0.5–1 mm. This implies that an LED can be directly coupled to a large-core fiber-optic cable or a simple pinhole (for
  example, 50–100 μm in diameter)".
- Reconstruction techniques: "shifting the light source and capturing multiple (typically ~10–100) subpixel-shifted
  lens-free images of the same static object".
- Gigapixel imaging: "a half-pitch resolution of <350 nm in air (illumination wavelength, 530 nm) across an FOV of
  ~20.5 mm2 ... the CMOS chip (Sony Corp.) is a 16-megapixel color (RGB) sensor with a pixel size of ~1.1 μm"; Fig. 3:
  "We used up to 100 (10 × 10) subpixel-shifted raw lens-free holograms"; CCD: "a half-pitch resolution of ~2.19 μm ...
  each pixel is physically 6.8 μm wide".
- Imaging speed: "the surface temperature of the sensor chip can easily reach above 40 °C after 'continuous' operation
  for, for example, more than 10 min ... This concern also exists for lens-free holographic approaches, but to a lesser
  degree because of the greater distance (for example, 1–2 mm) between the sample and the sensor chip."

### 4.9 Isikman et al. 2012 (PMC3902671, revisão; seções)
- IEEE J. Sel. Top. Quantum Electron. 18(3):1059–1072, DOI 10.1109/JSTQE.2011.2161460 (Crossref).
- II.: "the sample is placed directly on the top of an optoelectronic sensor array (such as a CMOS chip) with typically
  <4 mm vertical distance to its active area. ... spatially filtered through a photon-efficient pinhole with a
  diameter of d~0.1 mm, after which it propagates a vertical distance of z1~4–10 cm until it reaches the object plane".
- III.C: "the maximum resolution achieved by these systems has typically been ~1.5 μm [35],[36] over a FOV of ~24";
  fibras "at a height of z1~5–6 cm away from the sensor-chip".
- IV.: "a source with 1–15 nm bandwidth"; "a pinhole with a diameter of ~0.05–0.1 mm"; "the demagnification factor
  is typically ~100–200 owing to the large z1/z2 ratio, hence the pinhole is scaled down to <1 μm at the detector
  plane."
- III.D (tomografia): "a 3D spatial resolution of <1 μm × <1 μm × <3 μm (in x, y and z, respectively) over a large
  imaging volume of 15 mm3"; filtros "centered at ~640 nm with ~10 nm bandwidth".

### 4.10 Greenbaum et al. 2013 (PDF https://www.nature.com/articles/srep01717.pdf; páginas impressas = PDF)
- Sci. Rep. 3:1717, DOI 10.1038/srep01717.
- p. 1: "by placing the sample close (e.g., <1–2 mm) to the active area of an image sensor chip".
- p. 5: "the illumination wavelength was 480 nm (illumination bandwidth ~4 nm) and the objects were located at
  ~390 μm away from the CCD image sensor active area. ... The thinnest resolved grating lines are within Group 6
  Element 4, which corresponds to a half-pitch resolution of ~5.52 μm"; "The entire group 7 can now be resolved, which
  translates to a half-pitch resolution of ~2.2 μm"; com deconvolução "~1.74 μm".
- p. 2: "by utilizing a light emitting diode (LED) with a short illumination wavelength (λ = 372 nm), this pixel
  super-resolution based lensfree on-chip microscope can resolve periodic grating lines with a line-width of 225 nm".
- p. 7: "the vertical distance between the objects and the image sensor surface was on the order of 50–150 μm. This gap
  between the substrate and image sensor planes is filled with a refractive index matching oil"; "we used lateral
  movements of the light source, which was mounted on an X-Y stage (Newport, SMC100PP)".

### 4.11 Luo et al. 2016 (PDF https://www.nature.com/articles/lsa201660.pdf; PDF p.)
- Light Sci. Appl. 5:e16060, DOI 10.1038/lsa.2016.60.
- PDF p. 3: "the central wavelength of the source is scanned within a spectral range of 10–30 nm (for example, from 498
  to 510 nm) with a step size of ~3 nm. The spectral linewidth of illumination at each wavelength is ~2 nm ... a color
  CMOS sensor chip with a pixel size of 1.12 μm manufactured for cellphone camera modules (IU081, Sony Corporation ...).
  During the imaging process, the specimen is mounted on a transparent substrate and placed 100–500 μm above the image
  sensor chip."
- PDF p. 6 (Fig. 3): "Smallest resolved half-pitch: 0.98 μm" (um quadro), "0.69 μm" e "0.62 μm" (5 e 9
  deslocamentos), "0.62 μm" / "0.55 μm" (varredura de comprimento de onda).
- PDF p. 7: "can achieve a half-pitch resolution close to the image sensor's pixel pitch (that is, ~1 μm in Figure 3a,
  using a CMOS sensor that has a 1.12-μm pixel pitch)".
- PDF p. 10: "a few light-emitting diodes, each with a standard spectral bandwidth of 15–30 nm".

### 4.12 Kesavan et al. 2014 (PDF https://www.nature.com/articles/srep05942.pdf; PDF p.)
- Sci. Rep. 4:5942, DOI 10.1038/srep05942.
- PDF p. 10 (Methods): "a 12-bit APTINA MT9P031 CMOS RGB imaging sensor with a pixel pitch of 2.2 μm, measuring
  5.7 × 4.3 mm, and light-emitting diode (LED) (dominating wavelength 525 nm) with a pinhole of 150 μm (Fig. 1). ...
  Illumination is provided by the LED along with the pinhole from a distance of ~5 cm."
- PDF p. 8: "the culture dish is simply placed on the device installed permanently inside the incubators, without
  considering distance to sensor".
- PDF p. 10: "the setup cannot resolve fine lamellipodial and filopodial extensions (3–5 µm, Supplementary Fig. 5c)".

### 4.13 Agbana et al. 2017 (manuscrito aceito, https://repository.tudelft.nl/file/File_f2cb5cae-4710-4aa6-9c7b-c9d33a5b9dd6 ; PDF p.; o manuscrito numera as páginas 1–4, a versão publicada é 2271–2274)
- PDF p. 4 (manuscrito p. 3): "We designed a microscope using Thorlabs light source S1FC635 Thorlabs with a central
  wavelenght of 635nm and ∆λ = 0.8nm. Since a single-mode fiber was used, a complete spatial coherence and limited
  temporal coherence was assumed. A commercial CMOS sensor UI-1942LE (3840×2748), with pixel pitch p = 1.67µm was used".
- PDF p. 4: Eq. (13) "L ≈ 4p²/∆λ" (distância amostra–sensor ótima para coerência temporal); Eq. (11) "L = p/A_s"
  (coerência espacial, A_s = abertura numérica da fonte); "resolves element 5 of group 7, with feature width of
  2.5µm."
- PDF p. 5 (legenda da Fig. 4): "L = 2 mm, corresponding to undersampling (left), L = 13mm, corresponding to optimal
  case described by Eq. 13 (middle), and L = 26mm, corresponding to resolution loss due to low coherence (right)."

### 4.14 Zhang, Sun, Chen, Zuo 2020 (arXiv https://arxiv.org/pdf/1906.06231 v1; PDF p.)
- Publicado como IEEE Trans. Comput. Imaging 6:697–710 (2020), DOI 10.1109/TCI.2020.2964247 (Crossref); li o
  preprint, os números podem diferir na versão publicada.
- PDF p. 7–8: Eq. (12) "TCTF(u) = sinc(z2 ∆λ |u|²/2)" e Eq. (13) meio-período "q = 1/(2|u|) = √(z2∆λ/8)".
- PDF p. 10: Eq. (16) "q = 1/(2|u|) = z2∆s/(2z1)" (coerência espacial; ∆s = diâmetro da fonte).
- PDF p. 3: "(typically 0.3−2 mm)" (citada na seção 2.1).
- PDF p. 15: "the sample-to-senor distance is usually 450µm, and the source-to-sample distance is about 10cm. In
  addition, the illumination source has central wavelength 600nm with the spectral width 10nm ... and the sensor has
  the pixel size of 1.67µm".
- PDF p. 17: "The central wavelength of the illumination source is ∼ 520nm, and the resolution target is ∼ 1499µm(z2)
  away from the sensor. When the spectral width is 20nm, the theoretical half-pitch resolution calculated according to
  Eq. 13 is 1.936µm, and the actual reconstruction resolution is ∼ 1.953µm ... the reconstruction resolution is about
  2.461µm (5th element in group 7) with the spectral width ∆λ = 30nm".
- PDF p. 18: "When ∆s = 1mm ... When z1 is 4cm, the theoretical half-pitch resolution is 5.81µm, and the actual
  reconstructed result is ∼ 6.20µm"; "the sample-to-sensor distance is z2 = 465µm".
- PDF p. 19: z2 = 547 µm, "the resolution is at least 1.74µm".

### 4.15 Amann, von Witzleben, Breuer 2019 (PDF https://www.nature.com/articles/s41598-019-47689-1.pdf; PDF p.)
- Sci. Rep. 9:11260, DOI 10.1038/s41598-019-47689-1.
- PDF p. 2: "the object glass plate at a distance of 24.09 mm from the fibre exit facet"; "a 430 nm emitting high-power
  LED ... impinge on objects to be imaged (z = 5.91 mm)".
- PDF p. 3: "For both experiments, equal spatial separations between emission facet, microscope glass plate, carrying
  the micro-objects under investigation, and CMOS detector are chosen. A distance of 30 mm between light source and
  detector is selected"; "a Raspberry Pi CMOS detector camera with a pixel size of (1.12 × 1.12) μm²".
- PDF p. 7: "spectral bandwidth of ΔλLED of 15 nm (full-width-half-maximum)"; "A high-precision stainless steel pinhole
  with a diameter of (15 ± 1.5) μm ($75, P15D, Thorlabs Inc.)".
- PDF p. 6: "With LED illumination, element 1 of group 7 is the last resolvable element corresponding to a resolution of
  128 line pairs/mm and a line width of 3.91 μm. For LD illumination, element 3 of group 8 is still resolvable, leading
  to a resolution of 322.5 line pairs/mm and a line width of 1.55 μm."

### 4.16 Fontes de espessura (seção 2)
- onsemi, MT9J003/D, Rev. 7 (agosto de 2024), p. 54: https://www.onsemi.com/pub/Collateral/MT9J003-D.PDF ; Rev. E
  (05/2015), p. 74:
  https://s1-dl.theimagingsource.com/api/2.5/packages/publication/sensor-onsemi/mt9j003/48e04e9e-4165-570c-b3f5-eb536571dc47/mt9j003_1.1.en_US.pdf
  (p. 2 da Rev. 7: "Pixel Size 1.67 x 1.67 µm", "Active Pixels 3856 (H) x 2764 (V) (Entire Sensor)").
- ISO 8255-1:2011, prévia: https://cdn.standards.iteh.ai/samples/51961/2bd7c5a577a94d5782a7a16e465b04f4/ISO-8255-1-2011.pdf
- Thermo Scientific, lâminas: https://assets.thermofisher.com/TFS-Assets/APD/brochures/objekttraeger_uk_0715_0209.pdf

---

## 5. Trabalhos considerados e deixados de fora

| trabalho | motivo |
|---|---|
| Isikman et al. 2011, PNAS 108, 7296–7301, 10.1073/pnas.1015638108 (tomografia) | texto completo inacessível: o XML do PMC (PMC3088621) veio sem corpo, a página do PMC exige captcha e o PDF da PNAS respondeu com página de verificação. O resumo da tomografia entra pela revisão de Isikman 2012 (item 9) |
| Repetto, Piano, Pontiggia 2004, Opt. Lett. 29, 1132, 10.1364/OL.29.001132 (LED, geometria com ampliação) | metadados confirmados no Crossref; texto atrás de paywall, não está no PMC |
| McLeod & Ozcan 2016, Rep. Prog. Phys. 79, 076001, 10.1088/0034-4885/79/7/076001 | metadados confirmados; não está no PMC, sem cópia aberta encontrada |
| Ozcan & McLeod 2016, Annu. Rev. Biomed. Eng. 18, 77–102, 10.1146/annurev-bioeng-092515-010849 | metadados confirmados; não está no PMC |
| Feng & Wu 2017 (Opt. Express, fonte estendida) e Roy et al. 2017 (revisão) | não verifiquei a referência; deixados de fora, como manda a instrução |
| Sanz et al. 2017, Sci. Rep. 7, 43291, 10.1038/srep43291 | lido, mas usa diodos laser (fora do escopo LED + pinhole); útil para a geometria com ampliação: "typical magnification factors ranging from 5X to 20X depending of the layout distances" (PDF p. 2) e o protótipo com "(d-z) ≅ 0.5 mm and z = 7 mm meaning that M ≅ 15X" (PDF p. 3–4) |
| PDFs da Optica (Opt. Express, Opt. Lett.) | o servidor devolve página anti-robô; usei os manuscritos do PMC (Bishara 2010, Greenbaum & Ozcan 2012) e o repositório da TU Delft (Agbana 2017) |
| ficha do LED Thorlabs M385L2 | páginas de catálogo arquivadas da Thorlabs devolveram página anti-robô (curl e WebFetch); ver seção 7 |

---

## 6. O que a literatura sustenta

**Duas geometrias.** (i) *On-chip, ampliação ≈ 1*: amostra perto do sensor, fonte longe. É a de todos os trabalhos do
grupo de Ozcan, de CEA-Leti (Kesavan 2014) e de Zhang 2020, e a do artigo de 2015. Faixas lidas: z = 0,05–0,15 mm (com
vidro removido ou substrato fino e óleo, Greenbaum 2013), 0,1–0,5 mm (Luo 2016), 0,39 mm (Greenbaum 2013, CCD),
0,45–1,5 mm (Zhang 2020), ~0,7–1 mm com o vidro protetor no lugar (Bishara 2010/2011, Greenbaum & Ozcan 2012), até
"<1–2 mm" e "<2 mm" (Mudanyali 2010, Tseng 2010); as revisões dão "typically ≤0.1–2 mm" (Greenbaum 2012) e "<4 mm"
(Isikman 2012); Zhang 2020 atribui "0.3−2 mm" ao vidro protetor. Fonte a 3–10 cm (até 20 cm em Zhang), pinhole ou
fibra de 50–150 µm (Zhang usa 1–1,3 mm com difusor justamente para degradar a coerência espacial), banda de ~2 a
20–30 nm. (ii) *In-line com ampliação*: amostra perto da fonte. Entre os trabalhos com LED lidos só Amann 2019 (fonte
a 24 mm, amostra a 5,9 mm do sensor, pinhole de 15 µm, ampliação ≈ 1,25); Agbana 2017 (fonte coerente) e Sanz 2017
(laser) mostram a configuração divergente com pinhole muito menor (15 µm, fibra monomodo) e ampliação de 5–20×. **Um
pinhole de 100 µm a 15 cm só é compatível com a geometria (i).**

**O pinhole de 100 µm a 15 cm é típico?** Sim no diâmetro (50–150 µm em todos os on-chip com LED), e a distância de
15 cm é um pouco maior que os 3–10 cm usuais, o que só melhora a coerência espacial. Não há razão na literatura para
mudar D ou L do simulador.

**Coerência com as resoluções relatadas** (fórmulas simples de corte de Zhang 2020: q_t = √(z Δλ/8) pela banda,
q_s = z D /(2 L) pela fonte; e o pixel, que limita um quadro a ~p de meio-período, como Luo 2016 diz: "half-pitch
resolution close to the image sensor's pixel pitch"). Checagem das fórmulas com os próprios trabalhos (contas minhas
em `budget.py`):

| trabalho | condição | q_t / q_s previstos | relatado |
|---|---|---|---|
| Zhang 2020 | 520 nm, 20 nm, z = 1,499 mm | 1,94 µm / — | 1,953 µm (o artigo prevê 1,936) |
| Amann 2019 | 430 nm, 15 nm, z = 5,91 mm, 15 µm a 24 mm | 3,33 / 1,84 µm | 3,91 µm (um quadro) |
| Bishara 2011 | 633 nm, 10 nm, z ≈ 0,7, 105 µm a 3–6 cm | 0,94 / 0,6–1,2 µm | <1 µm com PSR |
| Bishara 2010 | 600 nm, 5 nm, z 0,75, 50 µm a 10 cm | 0,68 / 0,19 µm | ~0,6 µm com PSR |
| Mudanyali 2010 | 591 nm, 18 nm, z 1–2 mm | 1,5–2,1 µm / — | ~1–2 µm, um quadro (pixel 2,2) |

Para a bancada (385 nm, 10 nm suposto, 100 µm a 150 − z mm, pixel 1,67 µm; Nyquist 299 ciclos/mm):

| z efetivo | q_t (banda) | q_s (pinhole) | d = Dz/L | leitura |
|---|---|---|---|---|
| 0,49 mm (A mín) | 0,78 µm | 0,16 µm | 0,33 µm | pixel limita um quadro; PSR pode chegar a ~0,8 µm |
| **0,70 mm (A típ)** | **0,94 µm** | **0,23 µm** | **0,47 µm** | idem; corte da banda (~535 c/mm) acima do Nyquist: o sensor subamostra, a PSR tem o que recuperar |
| 1,00 mm | 1,12 µm | 0,34 µm | 0,67 µm | idem |
| 1,25 mm (B típ) | 1,25 µm | 0,42 µm | 0,84 µm | idem; 1,55 µm ainda cabe |
| 2,0 mm (`small_near`) | 1,58 µm | 0,68 µm | 1,35 µm | 1,55 µm com PSR no limite |
| 5 mm | 2,50 µm | 1,72 µm | 3,45 µm | um quadro (2,76 µm) no limite; 1,55 µm impossível |
| 19,25 mm (atual) | 4,91 µm | 7,36 µm | 14,7 µm | incompatível até com o resultado de um quadro |

Limites: q_t ≤ 1,55 µm exige z ≤ 1,92 mm (10 nm) ou ≤ 1,60 mm (12 nm); q_t ≤ 2,76 µm exige z ≤ 6,1 mm (10 nm). As
fórmulas de Agbana 2017 apontam para o mesmo lugar: a distância ótima pela coerência temporal, L ≈ 4p²/Δλ, dá 1,12 mm
para p = 1,67 µm e Δλ = 10 nm; pela coerência espacial, L = p/A_s com A_s = 50 µm/150 mm, dá 5,0 mm.

Ressalvas: são primeiros zeros de modelos com espectro retangular; o modelo do paper (gaussiano, `eq:envelope`) e a
ferramenta de envelope dão números diferentes em detalhe. O resultado de um quadro (2,76 µm) é pior que o pixel
(1,67 µm) em todos os z ≤ 2 mm, o que é normal: ruído, gêmea e a resposta do pixel (Greenbaum 2013 tira um fator ~3 de
NA só com PSR + deconvolução). Nada disso muda a conclusão: **19,25 mm não é compatível com o que o artigo de 2015
mostra; 0,5–1,9 mm é.**

---

## 7. Largura de banda do LED da bancada

- O artigo de 2015 nomeia o LED ("an ultraviolet LED of 385 nm, model M385L2 from ThorLabs", p. 2) e **não dá a
  largura de banda**, nem no texto principal nem no suplemento.
- Tentei a página de catálogo arquivada da Thorlabs para o M385L2 (https://www.thorlabs.com/catalogpages/Obsolete/2023/M385L2.pdf)
  por curl e por WebFetch: o servidor devolve uma página anti-robô. **Não li a ficha.** Um resultado de buscador
  atribui "10 nm FWHM" a catálogos da Thorlabs e a um revendedor, mas isso é trecho de buscador e não entra como fonte.
- Portanto: os 10 nm do simulador **não têm fonte lida**; são plausíveis pela faixa da literatura (Greenbaum 2012:
  "a few nanometers to 20–30 nm"; Isikman 2012: "1–15 nm"; Luo 2016: LEDs com "15–30 nm"; Bishara 2011 filtra um LED
  de 15–20 nm para ~10 nm). Para fechar, alguém com navegador precisa abrir a ficha da Thorlabs (ou o professor
  confirmar). Incluí uma linha com 12 nm no CSV para ver a sensibilidade.

---

## 8. Proposta e configurações candidatas

**Proposta: z = 0,7 mm efetivo** (pilha A, faixa 0,5–1,1 mm), D = 100 µm e pinhole a 15 cm do sensor (L = 150 − z),
λ = 385 nm, Δλ = 10 nm (suposto), pixel 1,67 µm, σ_sessão ≈ 0,1 mm, profundidade dentro da sessão 0–0,12 mm.
Referências por número: z — comunicação pessoal + MT9J003/D p. 54 + ISO 8255-1 Tab. 1 + Bishara 2011 (≈0,7 mm sobre o
vidro protetor) + Greenbaum & Ozcan 2012 (~0,7 mm mínimo com o vidro); D e L — Sobieranski 2015 p. 2, dentro das
faixas de Greenbaum 2012 e Isikman 2012.

**Alternativa 1: z = 1,0 mm** (número redondo, dentro da faixa A e perto do ótimo de Agbana para 10 nm). Prós: fácil de
justificar, margem para a folga desconhecida. Contra: nenhum relevante; fica a 0,3 mm do típico.

**Alternativa 2: z = 1,25 mm** (pilha B, lâmina de 1 mm para baixo). Vale se a montagem real for a lâmina voltada
para o sensor, o que contradiz a comunicação pessoal ("a lamínula" perto do sensor). Ainda compatível com 1,55 µm.

Em todas, o corte da banda (≈ 400–700 ciclos/mm) fica acima do Nyquist do sensor (299 ciclos/mm): o sensor subamostra o
holograma, a redução da parte A não se aplica (b = 1), e o `small_near` a 2 mm passa a ser o conjunto mais perto do
realista. Isso é consequência a ser calculada pelo outro agente com o envelope exato.

Configurações para a ferramenta de envelope: `results_exp_resolucao/envelope_candidates.csv`, colunas `name,
wavelength_nm, bandwidth_nm, pinhole_um, source_distance_mm, z_mm, pixel_um` e as livres `z_geom_mm, reference, page,
note`. **`z_mm` é a distância efetiva em ar**; `source_distance_mm` é pinhole–amostra (150 − z geométrico para a
bancada). Resumo:

| name | λ (nm) | Δλ (nm) | D (µm) | L (mm) | z (mm, efetivo) | pixel (µm) |
|---|---|---|---|---|---|---|
| bench_A_typ (proposta) | 385 | 10 | 100 | 149,1 | 0,70 | 1,67 |
| bench_A_min | 385 | 10 | 100 | 149,3 | 0,49 | 1,67 |
| bench_A_max | 385 | 10 | 100 | 148,7 | 1,06 | 1,67 |
| bench_A_typ_bw12 | 385 | 12 | 100 | 149,1 | 0,70 | 1,67 |
| bench_round_1mm | 385 | 10 | 100 | 148,8 | 1,00 | 1,67 |
| bench_B_typ | 385 | 10 | 100 | 148,3 | 1,25 | 1,67 |
| bench_small_near_2mm | 385 | 10 | 100 | 148,0 | 2,00 | 1,67 |
| bench_current_19p25_L130 | 385 | 10 | 100 | 130,75 | 19,25 | 1,67 |
| bench_current_19p25_L150 | 385 | 10 | 100 | 150 | 19,25 | 1,67 |
| zhang2020_led_dl20 (validação) | 520 | 20 | 0 | 200 | 1,499 | 1,67 |
| zhang2020_led_dl30 (validação) | 520 | 30 | 0 | 200 | 1,499 | 1,67 |
| amann2019_led (validação) | 430 | 15 | 15 | 24,09 | 5,91 | 1,12 |
| bishara2011_led_fibre | 633 | 10 | 105 | 45 | 0,70 | 2,2 |
| bishara2010_lamp_fibre | 600 | 5 | 50 | 100 | 0,75 | 2,2 |
| greenbaum2012oe_lamp_fibre | 550 | 5 | 100 | 100 | 0,70 | 2,2 |
| tseng2010_led_cellphone | 587 | 20 | 100 | 40 | 2,0 | 2,2 |
| mudanyali2010_led | 591 | 18 | 100 | 35 | 1,0 | 2,2 |

As linhas de validação comparam o envelope com resoluções medidas (Zhang: 1,953 e 2,461 µm de meio-período; Amann:
3,91 µm de largura de linha). Nas linhas da literatura, onde o artigo dá faixa (L de 3–6 cm, z "<1–2 mm") escolhi um
ponto e disse qual na coluna `note`; e o z da literatura é o declarado, sem saber se é geométrico ou efetivo.

---

## 9. O que não pude verificar, e o que contradiz o que estava escrito

Não verificado:
- O modelo exato do sensor da bancada (o artigo diz só "Aptina 10 megapixel monochromatic"); a identificação com o
  MT9J003 é por coincidência das dimensões 6,413 × 4,589 mm; não sei se é a versão monocromática, nem se o
  encapsulamento é o iLCC (vidro 0,4 mm) ou o tPLCC (vidro 0,3 mm), nem se a câmera tem janela adicional.
- A folga de ar (só comunicação pessoal) e qualquer dado sobre deriva térmica de z.
- A largura de banda do M385L2 (ficha bloqueada).
- O lado da amostra na bancada e a espessura das lamínulas/lâminas usadas (o artigo dá só "8 × 8 mm cover slip" e
  "glass cover slide (40.5 × 24.5 mm)").
- Se a Fig. 2 de 2015 é de hologramas LR ou HR e qual é o fator de escala do z para HR (hipótese da seção 1.3).
- Isikman 2011 PNAS, Repetto 2004, McLeod & Ozcan 2016 (sem acesso aberto).
- A norma ISO 8255-1 vigente (2017); li a prévia da edição de 2011.

Pontos que contradizem ou corrigem textos do projeto:
1. **A unidade do z está no suplemento**: "We used z×λ to compute the distance between the object and the detector
   plane". A leitura 50k = 50 000 λ está certa como unidade; o problema não é a unidade, é que a física do artigo
   (2,76 µm com um quadro, 1,55 µm com 49) não cabe em 19,25 mm com essa fonte. O suplemento ainda menciona um fator
   de escala de z para hologramas HR, que pode explicar números grandes de z na Fig. 2 (hipótese).
2. **O pinhole está a 15 cm do sensor**, não da amostra (p. 2). A 19,25 mm, L = 130,75 mm e o borrão do pinhole é
   14,7 µm, não 12,8 µm (a tabela do orientador e o paper usam L = 15 cm). Irrelevante a 0,7 mm (149,3 mm).
3. `docs/EQUIPMENT.md` diz "pinhole of '100 mm' ... 100 um is inferred (likely a typo)": no PDF do editor está
   escrito 100 µm (a versão do PMC é que tem "100 mm" e também "15 cm" no lugar de "5 cm" para a mesa xy).
4. `docs/EQUIPMENT.md` atribui a Greenbaum et al. 2012 (Nat. Methods) "LED of 10-20 nm band ... at a few centimetres,
   sample under 1 mm from the sensor". O texto diz banda "from a few nanometers to 20–30 nm", amostra "typically
   ≤0.1–2 mm", pinhole "50–100 μm", e não dá a distância da fonte.
5. A largura de banda de 10 nm do simulador e da tabela do orientador não vem do artigo de 2015 (seção 7).
6. A frase do orientador "com a amostra a poucos mm, o sensor subamostra o holograma" está de acordo com a literatura e
   com as contas aqui: a 0,7 mm o corte da banda (~535 ciclos/mm no modelo retangular) passa do Nyquist (299).
