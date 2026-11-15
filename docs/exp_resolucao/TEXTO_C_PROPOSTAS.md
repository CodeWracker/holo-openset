# Frases propostas para a Introdução e a Discussion (parte C e precedente de Seo 2009)

2026-11-15. Escritor do Related Work (worktree `latex-wt-related`, branch `rewrite/related-work`). **Nenhuma destas
frases foi colocada no LaTeX:** a Introdução é do outro escritor (`latex-wt-sim`) e a Discussion fica para o
responsável. Cada frase traz a fonte (trabalho, página ou seção, e onde a frase original está transcrita) e as
macros que usa. Os números nossos só aparecem por macro já existente (`numbers.tex`, `numbers_distancia.tex`). As
chaves bibliográficas novas já estão no fim do `main.bib` do branch `rewrite/related-work`.

Fontes completas e frases originais: `LEVANTAMENTO_C.md` (tabela 3a e seção 5, itens 10–13).

---

## 1. Introdução

### I-1. Logo depois de apresentar a linha sem reconstrução (fim da frase "A line of work, ours included, skips the reconstruction ...")

```latex
This line is older than deep learning: Seo et al.~\cite{seo2009} recognised cells by the texture of their lensless holograms, without a reconstruction, and found that the recognition degrades when the holograms of neighbouring cells overlap. It is usually motivated by speed---the reconstruction is described as expensive, often as iterative~\cite{seo2009,kim2018,scherrer2022,xu2025plankton}, and so did we~\cite{rockembach}---but a reconstruction at a known distance is one pair of Fourier transforms, \TBackpropGpuBigMs\,ms per full frame on one GPU, while the detector that every route needs takes \TYoloTiledGpuBigMs\,ms (Section~\ref{sec:rq4}).
```

Fontes:
- Seo 2009, seção "Discussions" (PMC3931575, sem páginas): "there is no such digital reconstruction, and the
  detected holographic lensfree image is simply analyzed by a pattern recognition algorithm"; "Beyond this
  concentration level, the statistical overlap of the cell holograms reaches upto ≥37%, which increases the counting
  errors made by Holographic-LUCAS"; "numerically and computationally our approach is much simpler and faster".
- "iterative": Kim 2018 p. 2 ("This iterative algorithm is computationally intensive..."); Scherrer 2022, versão do
  autor, resumo e p. 2 ("this iterative and time-consuming step"); Xu 2025 p. 1 ("time-consuming iterative
  computation"); Seo 2009 não usa "iterative" (só "simpler and faster"), por isso está no primeiro grupo do
  "expensive". Se preferir só quem usa "iterative", tire `seo2009` desse `\cite`.
- Rockembach 2024 (`rockembach`): p. 364 ("computationally expensive due to the nature of numerical diffraction
  methods"), p. 365 ("The iterative and complex procedure for reconstruction usually makes real-time applications
  unfeasible").
- Nossos números: `\TBackpropGpuBigMs` (1.0) e `\TYoloTiledGpuBigMs` (166.8), `numbers.tex`, os mesmos da Seção RQ4.

### I-2. Correção do mecanismo, se o outro escritor quiser uma frase com o precedente

```latex
What defeats such networks is not that a pattern spreads beyond its crop but that the patterns of its neighbours enter it, the effect Seo et al.~\cite{seo2009} reported for counting on the raw hologram.
```

Fonte: Seo 2009, "Discussions" (acima). A frase sobre os nossos crops vem do controle C do piloto
(`RELATORIO_PILOTO_1MM.md`, seções 3 e 6); **não tem número**, de propósito: as macros do piloto estão no branch da
seção nova (`numbers_resolucao.tex`), que eu não vejo.

### I-3. Contribuição (se a lista de contribuições ganhar um item sobre o argumento de tempo)

```latex
(\emph{n})~A stage-by-stage timing, from a window to a full frame, which shows that the argument of speed for skipping the reconstruction, ours included~\cite{rockembach}, does not hold: one back-propagation costs \TBackpropGpuBigMs\,ms per frame on one GPU and the detector \FullDetectPctMinFloor\,\% or more of the computation of a frame in every flow that does not repeat the reconstruction on the whole frame (Section~\ref{sec:rq4}).
```

Fonte: as macros `\TBackpropGpuBigMs`, `\FullDetectPctMinFloor` (`numbers.tex`) e a frase da RQ4 em `06-results.tex`
("on one GPU it takes \FullDetectPctMinFloor\,\% or more of the computation of a frame in every flow that does not
repeat the reconstruction on the whole frame").

---

## 2. Discussion

### D-1. Recomendação para a área (a frase da C.3, ajustada ao que o levantamento achou)

```latex
A claim that a reconstruction-free route is faster should therefore be measured, stage by stage and on the same hardware, against a single back-propagation at a calibrated or cheaply searched distance---not against a blind search over hundreds of distances~\cite{Liu:21} or the full pipeline of a clean reconstruction~\cite{matthews2024}---and with the detector that both routes share in the timing. Where the stages were timed separately~\cite{gorocs2018,pirone2026}, the propagation was not the expensive one.
```

Fontes:
- Liu 2021, Tabela 5, nota b: "reconstruction distance range: 10 – 60 mm with step 0.1 mm" (501 distâncias por recorte
  de 227 × 227); p. 3: os recortes são dados prontos ("Each hologram is cropped to 300 × 300 pixels around the
  target"), sem detector cronometrado.
- Matthews 2024, Tabela 2 (p. 11): YOLOv5n "Desktop CPU 149" ms contra "Standard DHM on Desktop CPU ... 1658" ms; o
  DHM padrão é uma pilha de retropropagação para localizar em 3D (p. 5).
- Göröcs 2018, p. 7: "(1) segmentation of the full FOV hologram for object detection (~70 ms), (2) holographic
  autofocusing and reconstruction (~12 ms/object)" e "The deep learning-based phase-recovery step is currently the
  most intensive part of our algorithm, with a runtime of ~250 ms/object" (GTX 1080).
- Pirone 2026, Tabela 2 (p. 6): demodulação 0,0177 s, refoco 0,3975 s, desembrulhamento 0,0444 s; p. 7: "the
  refocusing stage is the main bottleneck"; "Interestingly, this is faster than directly classifying raw holograms".

### D-2. Densidade e o precedente

```latex
The density of the sample decides how far crops of the raw hologram can go. Seo et al.~\cite{seo2009} saw their reconstruction-free counting lose accuracy once about a third of the holograms overlapped, while counting after a reconstruction kept an error below 5\,\% with completely overlapping holograms~\cite{seo2010}; on our data the crops lose the rejection of novel classes first. A reconstruction-free recogniser should be evaluated at stated densities, preferably as the overlap ratio $1-\exp(-\pi D^2 H C)$ of Seo et al.~\cite{seo2009}.
```

Fontes:
- Seo 2009, "Discussions": "Overlap_Ratio = 1 − exp(−π D² H C) where D is the effective diameter of the cell
  hologram, H is the channel height and C is the concentration of the cell solution"; "the statistical overlap of the
  cell holograms reaches upto ≥37%, which increases the counting errors".
- Seo 2010 (PMC2892055), "Results and Discussion": "the reconstructed cell images yielded an absolute error rate of
  <5%, up to a cell density of ~0.4 × 10⁶ cells/μL"; "all of the lens-free RBC holograms are completely overlapping
  (because of a high cell density of ~0.4 × 10⁶/μL)". Isikman 2012 (seção III.A) relata o mesmo número, mas a frase
  dela não diz que a contagem foi na reconstrução (ver `LEVANTAMENTO_C.md`, seção 5, item 11).
- "lose the rejection of novel classes first": piloto a 1,0 mm e controle C (`RELATORIO_PILOTO_1MM.md`, seções 2 e
  3). **Sem número de propósito**; quando a curva de densidade tiver macros, a frase pode ganhar os números.
- "about a third": 37 % de Seo é "≥ 37 %"; se preferir o número, use "once 37\,\% or more of the holograms overlapped".

### D-3. Simulação (ligação com a seção nova "a simulação muda a resposta")

```latex
Simulations of raw holograms that place the objects without overlap, as amplitude-only objects lit by a plane wave at one distance~\cite{scherrer2022}, test the reconstruction-free route where it is easiest.
```

Fonte: Scherrer 2022, versão do autor, p. 6: "the 13 transmission functions are randomly placed without overlapping on
a 512 × 512 empty image"; "We have considered that the plankton are pure amplitude objects so that ϕ(x,y) = 0"; p. 7:
"λ = 530 nm (green), z = 0.8 mm"; onda plana ("The incident plane wave ... was simulated with U−(x,y) = 1"); p. 14:
"the object/camera distance was fixed at z = 0.8 mm during our simulations". **Não** incluí o nosso CBMS 2024 nesta
frase: o texto do artigo não diz se as letras podiam se sobrepor.

---

## 3. Abstract (se o responsável quiser uma frase sobre o tempo)

```latex
Timing every stage from a window to a full sensor frame shows that one back-propagation costs \TBackpropGpuBigMs\,ms per frame on one GPU, far less than the detector every route needs, so the argument of speed for skipping the reconstruction, our own earlier one included, does not hold.
```

Fonte: as mesmas macros de I-1.

---

## 4. O que **não** proponho e por quê

- "the reconstruction costs about 1 ms" com `\DistTimeRecZZeroFrontGpuBigMs`: essa macro vale 2,9 (front end com flat
  field e entrada da rede). O "≈ 1 ms" do orientador é a retropropagação sozinha (`\TBackpropGpuBigMs` = 1,0;
  `\DistStageBackpropGpuBigMs` = 0,97) ou a camada de propagação (`\TLayerPropGpuBigMs` = 1,1). No Related Work usei
  as três, cada uma com o nome certo.
- Números do piloto a 1,0 mm (rejeição 0,730 contra 0,997; 0,08 no denso): não há macro no meu branch. Ficam para
  quando as macros de `numbers_resolucao.tex` existirem.
- Atribuir ao Bravo-Frank 2024 a afirmação de custo: ele não a faz (p. 6: o tempo real vem da cascata
  YOLOv8n → YOLOv8). O trabalho seguinte do grupo (2025) faz a afirmação e reconstrói dois planos de Fresnel dentro do
  próprio pipeline "real-time" (arXiv, pp. 5–6).
