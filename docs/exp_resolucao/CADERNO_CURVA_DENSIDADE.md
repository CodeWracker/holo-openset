# Caderno do executor "densidade" (curva de densidade e cinco repetições no denso)

Etapa de `PROTOCOLO_CURVA.md`, pré-registro do responsável em `CADERNO_CURVA.md` (Q0, Q1, …). Só o executor
"densidade" escreve aqui. Entradas em ordem de tempo, com a hora real do relógio. GPU 5 (H100, compartilhada), um
processo de GPU por vez, 4 threads por processo, sessões tmux `res_curve_*`.

## 2026-11-15, 08:36 — D1: fase 1 (cinco repetições no denso, diâmetro do holograma, curva preparada sem gravar)

### 1. Item a do Q0: r2–r5 no `bench_1mm_dense`

- `scripts/exp_resolucao/controls_1mm.sh` ganhou `REP` (1–5) nos passos `*_train` e `*_evaluate`, como o
  `pilot_1mm.sh`: com `REP=1` o script faz o que fazia (os arquivos de r1 existem e não são refeitos: o treino diz
  "exists", a avaliação pula o json); logs de REP > 1 em `logs/exp_resolucao/controls_<passo>_r<REP>.log` (o brief
  pede `curve_*.log`; mantive o nome do script que já existia). Commit `controls_1mm.sh: the repetition…`.
- Comando (tmux `res_curve_dense_reps`, 08:15–08:29):
  `for R in 2 3 4 5; do REP=$R bash scripts/exp_resolucao/controls_1mm.sh 5 dense_train && REP=$R bash
  scripts/exp_resolucao/controls_1mm.sh 5 dense_evaluate; done`. Treino dos três fluxos 110 / 154 / 293 / 163 s (r2–r5;
  r1 levou 318 s ontem: a GPU estava mais carregada; conferido que todos rodaram os 3000 passos), avaliação 17–36 s.
- α da camada: calibrado 0,001059 em todas (mesmos 32 hologramas de treino); depois do treino 0,001033 / 0,001038 /
  0,001037 / 0,001036 (r2–r5; r1 0,0010366) → 0,976–0,980 mm.
- Tabela: `python scripts/exp_resolucao/dense_five_reps.py` → `results_exp_resolucao/dense_five_reps.csv`. Teste
  lido uma vez por modelo.

| rep | raw F1 / rej. / fechada | prop F1 / rej. / fechada | rec_z0 F1 / rej. / fechada | prop − raw F1 / rej. | rec_z0 − prop F1 / rej. |
|---|---|---|---|---|---|
| 1 | 0,7957 / 0,0797 / 0,9004 | 0,9595 / 0,8994 / 0,9871 | 0,9676 / 0,9517 / 0,9951 | +0,1638 / +0,8196 | +0,0080 / +0,0523 |
| 2 | 0,7949 / 0,0907 / 0,8969 | 0,9685 / 0,9685 / 0,9875 | 0,9735 / 0,9945 / 0,9941 | +0,1735 / +0,8778 | +0,0050 / +0,0260 |
| 3 | 0,7883 / 0,0871 / 0,8905 | 0,9569 / 0,8717 / 0,9864 | 0,9708 / 0,9681 / 0,9933 | +0,1686 / +0,7846 | +0,0139 / +0,0964 |
| 4 | 0,7954 / 0,1278 / 0,8983 | 0,9671 / 0,9476 / 0,9866 | 0,9653 / 0,9247 / 0,9948 | +0,1717 / +0,8198 | −0,0018 / −0,0229 |
| 5 | 0,7886 / 0,0963 / 0,8938 | 0,9753 / 0,9850 / 0,9880 | 0,9749 / 0,9937 / 0,9955 | +0,1868 / +0,8887 | −0,0005 / +0,0087 |
| média | 0,7926 / 0,0963 / 0,8960 | 0,9655 / 0,9344 / 0,9871 | 0,9704 / 0,9665 / 0,9946 | +0,1729 / +0,8381 | +0,0049 / +0,0321 |
| mín. | 0,7883 / 0,0797 / 0,8905 | 0,9569 / 0,8717 / 0,9864 | 0,9653 / 0,9247 / 0,9933 | +0,1638 / +0,7846 | −0,0018 / −0,0229 |
| máx. | 0,7957 / 0,1278 / 0,9004 | 0,9753 / 0,9850 / 0,9880 | 0,9749 / 0,9945 / 0,9955 | +0,1868 / +0,8887 | +0,0139 / +0,0964 |

Limiares do P0 para camada − crops, descritivo: F1 ≥ 0,10 em **5 de 5**; rejeição ≥ 0,30 em **5 de 5**; as duas em
**5 de 5**.

### 2. Diâmetro efetivo do holograma (Q0, "Diâmetro efetivo…")

`python scripts/exp_resolucao/hologram_diameter.py --device cuda:5` (tmux `res_curve_diameter`, 53 s) →
`results_exp_resolucao/hologram_diameter.csv`, `hologram_diameter_summary.json`,
`docs/exp_resolucao/img/hologram_diameter.png`. Nenhum conjunto de dados lido além do `physics.json` do `bench_1mm`
(as leis).

- Amostra: semente **20261115** (`random.Random`), 26 classes × 10; por letra, na ordem: tamanho de fonte uniforme
  em 15,95–26,89 px, fonte, rotação ±35°, absorção e fase com as leis do conjunto (`material`, profundidade forçada a
  0); raster mestre 16×; cada letra sozinha, centrada numa janela 768 × 768, margem 394 (o disco de 256 px e o alcance
  da franja mais fina cabem no canvas sem dobra), z = 1,0 mm exatos, s = 4, banda do LED e pinhole do conjunto, sem
  ruído, sem poeira (nem da janela do sensor), sem perfil de feixe. B = a mesma gravação sem a letra; p = I/B − 1;
  e = p².
- Escolhas minhas de execução (não mudam a regra): o centroide da energia é tirado no disco de 256 px em torno do
  centro da janela; D_vis olha o perfil (anéis de 1 px) até R = 352 px ("não volta a passar" verificado até ali;
  nenhuma letra estava acima do ruído em 352); ruído = 2,1 / 101,5 = 2,07 %.
- Resultados (px de 1,67 µm; média / mediana / p5 / p95):
  - lado da tinta: 17,7 / 17,5 / 12,8 / 23,9
  - D_rms(96): 66,7 / 66,5 / 57,8 / 75,9; D_rms(128): 66,8 / 66,5 / 57,8 / 76,0; **D_rms(192): 66,8 / 66,5 / 57,9 /
    76,0**; D_rms(256): 66,9 / 66,6 / 57,9 / 76,1
  - D_vis: 94,9 / 98,0 / 70,0 / 110,0 (mín. 16: um Z de padrão fraco, abaixo do ruído quase desde o centro)
  - D_86: 68,7 / 68,5 / 59,5 / 77,7
- **D_ef** (regra dos pares): D_rms(192) **66,9 px = 111,8 µm**; D_vis 95,4 px = 159,3 µm; D_86 68,8 px = 114,9 µm
  (D_rms(256): 67,0 px = 112,0 µm).
- Convergência: D_ef de D_rms(256) difere do de D_rms(192) em **0,17 %** (por letra: mediana 0,15 %, p95 0,35 %,
  todas abaixo de 5 %). **Pela regra do Q0, o eixo usa D_rms(192).**
- Razão de sobreposição 1 − exp(−π D_ef² σ):

| σ (por mm²) | 7 | 13 | 60 | 135 | 300 |
|---|---|---|---|---|---|
| D_rms(192) = 111,8 µm | 0,240 | 0,400 | 0,905 | 0,995 | 1,000 |
| D_86 = 114,9 µm | 0,252 | 0,417 | 0,917 | 0,996 | 1,000 |
| D_vis = 159,3 µm | 0,428 | 0,645 | 0,992 | 1,000 | 1,000 |

- **Para o responsável:** com D ≈ 112 µm o eixo de sobreposição satura acima de 60 por mm²: os níveis 154 e 343
  (0,995 e 1,000) ficam no mesmo ponto do eixo. O D da letra é ≈ 3,8× o lado dela (o padrão a 1 mm vai a ~33 px do
  centroide em rms). Seo 2009 dá D ≈ 50 µm para as células deles. O Q0 deixa a escala do eixo para depois desta
  medida: a densidade (segundo eixo) separa os níveis; a sobreposição, não.
- Figura: perfil radial de |p| (média azimutal) de 6 letras (do menor ao maior lado) contra o ruído; o padrão cai
  abaixo do ruído entre 30 e 60 px; há dois lóbulos fracos (~10⁻⁴) em ~135 e ~205 px.

### 3. A curva preparada, sem gravar

- `scripts/exp_resolucao/density_curve.sh <GPU> <passo>` com `LAW` (d50 | u50), `LEVEL` (8, 15, 69, 154, 343), `REP`,
  `WORKERS` (padrão 8); passos `record`, `verify`, `reconstruct`, `train`, `evaluate`, `table`; conjuntos
  `data/curve_<LAW>_L<nível com 3 dígitos>`; logs `logs/exp_resolucao/curve_<passo>_<LAW>_L<nível>[_r<REP>].log`.
  - `record`: o comando do `pilot_1mm.sh record` com a lei de profundidade e `fill_mean=LEVEL`.
  - `verify`: `controls_checks.py dense` contra o nível esparso da família (anotações e o resto idênticos, gravações
    sem o enchimento idênticas às do esparso, letras por janela, puladas, área coberta) e `bench_sanity.py`.
  - `train` / `evaluate`: a receita do piloto (`--no-aux`, `prop` com `--alpha-extend 12`), repetição `REP`.
  - `table`: `density_curve_table.py` → `density_curve_<LAW>.csv` e `_reading.json`, com as regras do Q0 b ("caiu",
    "as curvas se separam", onde a camada cai, limiares do P0 com cinco repetições), a densidade obtida e a razão de
    sobreposição com o D_ef do eixo. Rodado em seco com `bench_1mm` no papel do esparso e `bench_1mm_dense` no de 154
    (só para exercitar o código; os arquivos de saída foram apagados).
  - `LAW=d50`: `depth_std=50e-6 depth_max=150e-6`; o nível esparso dessa lei **é o `bench_1mm_depth50`** do outro
    executor (mesmas sementes, física igual à do denso a menos da profundidade; layout igual a menos de `fill_mean`),
    que o script nunca regrava. `LAW=u50`: recusa ("não implementado", Q1).
- **Viabilidade do nível 343** (20 cenas na CPU, um processo, imagens 0, 263, …, 4999, lei d50;
  `results_exp_resolucao/curve_feasibility_343.csv`, log `curve_feasibility_343.log`): **0 letras de enchimento
  puladas** (alvos 287–380 na janela, 624–711 na faixa, todos colocados); letras por janela **344,7** (294–389); área
  coberta (soma das caixas de tinta na janela, a medida do K2) **23,2 %** (20,3–25,6 %); **2,54 s por cena**
  (2,40–2,73). Para comparação, 5 cenas de 154 na mesma hora: 155 por janela, 10,2 %, 1,15 s.
- **Construtores e imagens** (`python scripts/exp_resolucao/curve_workers_check.py same --n 16 --workers 8`): as 16
  primeiras imagens do `bench_1mm_dense` gravadas de novo em `$TMPDIR` com 1 e com 8 construtores: hologramas,
  anotações e `metadata.csv` idênticos entre si, e hologramas e anotações idênticos aos do conjunto guardado (a
  coluna `split` difere por construção: um conjunto de uma sessão a põe em treino). **O número de construtores não
  muda as imagens.**
- **Tempo de gravação** (`curve_workers_check.py timing`, 96 imagens, GPU 5 sem outro processo pesado no momento;
  `results_exp_resolucao/curve_workers_check.json`): s por imagem depois da primeira → estimativa para 5000:

| nível | construtores | s/imagem | 5000 imagens | threads prontas (média / p95 / máx.) |
|---|---|---|---|---|
| 15 | 8 | 0,162 | 13,5 min | 4,7 / 14,2 / 35 |
| 154 | 8 | 0,332 | 27,7 min | 6,6 / 11,1 / 15 |
| 343 | 8 | 0,576 | 48,0 min | 8,2 / 14,0 / 16 |
| 343 | 12 | 0,576 | 48,0 min | 7,0 / 14,8 / 21 |

  O nível 69 fica entre 15 e 154 (≈ 20 min, interpolado, não medido). Com 8 construtores a gravação já é limitada
  pela GPU (12 não ganham nada); 8 cabem no orçamento de 24 threads prontas (máximo medido 16; o pico de 35 no nível
  15 durou uma amostra, na partida do pool). A medida foi feita com a GPU livre; com o outro executor na mesma GPU, o
  tempo cresce. Total da família d50 (15, 69, 154, 343): ≈ 1 h 50 min de gravação, mais ~1 min de verificação, 75 s
  de reconstrução e ~2–5 min de treino e 1 min de avaliação por nível e repetição; disco ≈ 9 GB por nível (36 GB).
- **Lei (ii), uniforme em ±25 µm (não implementada):** um campo novo em `Physics` (por exemplo `depth_uniform =
  25e-6`, meia largura; 0 = desligado e fora do `physics.json` enquanto 0, como `oversample`); em `scene.material`, o
  mesmo único `rng.gauss` que hoje vira `depth_std · g` (cortado) vira `depth_uniform · erf(g/√2)` (uniforme em
  ±25 µm, porque erf(g/√2) = 2Φ(g) − 1). O fluxo de sorteios não muda (um gauss por objeto), então as cenas são as
  mesmas a menos das profundidades, e as letras ficam pareadas, uma a uma, com as do `d50` (a mesma g, levada por uma
  função crescente). O nível esparso dessa lei teria de ser gravado (`LEVEL=8`, ≈ 14 min). Testes: desligado, os
  digests das cenas e a referência nativa iguais; ligado, mesmas linhas a menos de `depth` e `z`, profundidades em
  ±25 µm com distribuição uniforme (teste de Kolmogorov–Smirnov em alguns milhares), e o mapeamento g → profundidade
  conferido contra o `d50` na mesma cena. Estimativa: ≈ 1 h com pytest (≈ 1,5 min) e `reproduce check`.

### O que parece estranho ou merece olhar

1. O eixo de sobreposição satura (0,905 em 60 por mm², 0,995 em 135, 1,000 em 300): com D ≈ 112 µm os níveis 154 e
   343 coincidem nele. Decisão de escala do eixo é do responsável (Q0).
2. O nível esparso da lei d50 é um conjunto do outro executor (`bench_1mm_depth50`, r1 treinado e avaliado por ele).
   O Q0 manda r2–r5 no esparso de qualquer jeito: quem roda? (Eu rodaria com `density_curve.sh LEVEL=8`, que só
   treina e avalia nele, sem regravar; os arquivos de r1 dele não são tocados.)
3. O `controls_checks.py dense` reporta como diferença de `physics.json` o campo `like` (o `bench_1mm_depth50` foi
   feito com `simulate like`; os da curva com `simulate fresnel`): esperado, não é física.

## 2026-11-15, 09:02 — D2: fase 2, a lei uniforme no simulador e o começo das gravações

Respostas do responsável (mensagem da fase 2 e Q1): lei padrão uniforme em ±25 µm; o nível esparso é novo
(`curve_u50_L008`) e é meu; o `bench_1mm_depth50` sai da curva; eixo fixado no Q1 (π D² σ em escala log, D =
111,8 µm).

### A lei uniforme (commit `a25df48`)

- `Physics.depth_uniform` (padrão 0; ausente do `physics.json` enquanto 0, como `oversample`). Em
  `scene.material`, o mesmo único `rng.gauss` g da profundidade vira `depth_uniform · erf(g/√2)` quando o campo é
  > 0; senão, a normal cortada de sempre (a mesma expressão). Vale para tudo que passa por `material`: letras
  anotadas, de fora da janela e de enchimento (e as letras dos layouts do paper). A poeira não passa por `material`
  (planos fixos). Com a lei ligada, `depth_std` e `depth_max` não são lidos; nos conjuntos da curva ficam os valores
  do piloto (2,6 / 7,8 µm), para que a única diferença de física contra o `bench_1mm` seja `depth_uniform`.
- `tests/test_depth_uniform.py` (8 testes, 3,5 s): desligado, os digests das quatro cenas de antes do enchimento;
  ligado (layout físico com enchimento e layout do paper), as mesmas linhas a menos de `depth`, os mesmos objetos
  a menos da profundidade, |depth| ≤ 25 µm, a profundidade = 25 µm · erf(g/√2) com o g da lei normal (onde ela não
  é cortada), a poeira igual; 5000 sorteios uniformes pelo teste de Kolmogorov–Smirnov (p > 0,01) com desvio
  25/√3 = 14,4 µm (±3 %); `generate()` com e sem a lei: anotações iguais a menos de `depth` e `z`, poeira,
  sessões e quadros em branco idênticos, `physics.json` diferindo só em `depth_uniform`. A referência nativa
  (`test_oversample`) continua bit a bit.
- `pytest`: **72 passam** (64 + 8). `reproduce check`: **13/13**.
- `density_curve.sh`: `LAW=u50` → `depth_std=2.6e-6 depth_max=7.8e-6 depth_uniform=25e-6`; o nível 8 é gravado
  sem enchimento (`curve_u50_L008`) e conferido por `controls_checks.py sparse` contra o `bench_1mm`.

### Gravações (GPU 5, tmux `res_curve_rec_L<nível>`, 8 construtores cada)

- 08:54 `LAW=u50 LEVEL=8 bash scripts/exp_resolucao/density_curve.sh 5 record`.
- 08:56 `LAW=u50 LEVEL=343 WORKERS=8 ... record`, em paralelo. Dois processos de GPU rendem quase a soma: L008
  0,15 → 0,20 s por imagem, L343 0,58 → 0,60 s por imagem (GPU a 86–97 %); threads prontas 3–19,
  `cpu.pressure` some avg10 = 0,00. Fico com dois processos de GPU no máximo.

## 2026-11-15, 09:15 — D3: `curve_u50_L008` gravado e conferido; r1–r5 lançados

- Gravação: 955 s (08:54:55–09:10:50; em paralelo com L343 a partir de 08:56). Disco: ≈ 3 GB sem o `rec_z0.npy`.
- `LAW=u50 LEVEL=8 bash scripts/exp_resolucao/density_curve.sh 5 verify` (16 s) → `results_exp_resolucao/curve_u50_L008_checks.json`,
  `curve_u50_L008_sanity.json`, folha de contato `docs/exp_resolucao/img/curve_u50_L008_examples.png`:
  - `annotations.csv` contra o `bench_1mm`: 40 309 linhas (28 227 / 5711 / 6371), todas as colunas iguais a menos de
    `depth` e `z`; z − depth igual (diferença máxima 1,0 × 10⁻¹⁶ m).
  - Profundidades: |depth| máx. 24,9993 µm (≤ 25 µm), média −0,016 µm, desvio **14,437 µm** (esperado 25/√3 =
    14,434 µm), Kolmogorov–Smirnov contra a uniforme em ±25 µm p = 0,90. Pareamento com o piloto: nas 40 199 letras
    em que a normal do piloto não foi cortada, depth = 25 µm · erf((depth_piloto / 2,6 µm)/√2) com diferença máxima
    1,0 × 10⁻²⁰ m.
  - Idênticos ao `bench_1mm` byte a byte: `metadata.csv`, `dust.csv`, `sessions.csv`, `backgrounds.npy`, os 5000
    rótulos YOLO e os 1600 mapas de verdade (a profundidade não entra neles). `physics.json`: a única diferença é
    `depth_uniform = 2,5 × 10⁻⁵` (o campo `like` é igual: os dois feitos por `simulate fresnel`).
  - Duas imagens refeitas da semente (100, treino; 0, teste), com o gerador de ruído: **idênticas** às guardadas.
  - Sanidade (treino): lados de tinta 12,81 / 17,38 / 23,29 px (os do piloto), nível médio 101,49 (piloto 101,49),
    brancos 101,51, ruído refeito das sementes média 0,002–0,007, rms 2,091–2,102.
- 09:11 `reconstruct` (47 s) e, em sequência, `train` + `evaluate` de r1 a r5 (tmux `res_curve_L008_run`).

## 2026-11-15, 10:21 — D4: L008 r1–r5 prontos (arquivo para o executor "distância"); L154 e L343 gravados e conferidos

### `curve_u50_L008`, r1–r5 (09:12–09:25; teste lido uma vez)

Treino dos três fluxos 138–160 s por repetição, avaliação ≈ 18 s; todos os modelos com 3000 passos.

| rep | raw F1 / rej. | prop F1 / rej. | rec_z0 F1 / rej. |
|---|---|---|---|
| 1 | 0,9251 / 0,6135 | 0,9747 / 0,9799 | 0,9737 / 0,9952 |
| 2 | 0,9384 / 0,7145 | 0,9775 / 1,0000 | 0,9787 / 1,0000 |
| 3 | 0,9367 / 0,7247 | 0,9693 / 0,9370 | 0,9796 / 0,9876 |
| 4 | 0,9466 / 0,8272 | 0,9775 / 0,9975 | 0,9753 / 0,9984 |
| 5 | 0,9374 / 0,6898 | 0,9748 / 1,0000 | 0,9777 / 0,9992 |

`results_exp_resolucao/curve_u50_L008_ready.json` escrito às 09:26 (conjunto, os 15 modelos, as 15 avaliações, o
commit das avaliações e o da lei de profundidade). Os modelos e o conjunto não serão regravados nem apagados.

### Gravações

| nível | início | parede | observação |
|---|---|---|---|
| 343 | 08:56 | 4588 s | em paralelo com L008, L154 e o executor "distância" na GPU 5 (0,6 → ~2 s por imagem quando eram três) |
| 154 | 09:25 | 2565 s | |
| 69 → 15 | 10:08 | em curso | em sequência no mesmo tmux |

### Conferências (`density_curve.sh verify`, contra `curve_u50_L008`)

| | L154 | L343 |
|---|---|---|
| `annotations.csv` idêntico byte a byte | sim (40 309) | sim |
| rótulos, mapas, poeira, sessões, brancos, metadata comum | idênticos | idênticos |
| `physics.json` | só `fill_mean` = 154 | só `fill_mean` = 343 |
| sem enchimento = L008 (imagens 100 e 0) / com = o conjunto | 0 / 0 níveis | 0 / 0 níveis |
| enchimento muda o holograma (rms) | 15,8–16,9 níveis | 23,0–24,4 níveis |
| letras por janela (média, dp, p5–p95, mín.–máx.) | 154,10, 12,36, 134–175, 116–205 | 343,15, 18,42, 313–374, 287–418 |
| na faixa, por 640² | 153,84 | 342,76 |
| área coberta (caixas de tinta, 100 cenas) | 10,54 % | 23,35 % |
| letras de enchimento puladas | 0 | 2 (em 2 imagens, de ≈ 5 milhões) |
| nível médio de cinza (treino) | — | 97,16 |

O L154 da lei uniforme tem as mesmas posições, classes e contagens do `bench_1mm_dense` (só as profundidades mudam),
por isso os números de densidade coincidem.

### α da família (pedido do responsável): `scripts/exp_resolucao/curve_alpha.py` → `results_exp_resolucao/curve_alpha.csv`

Mesmo código do `pilot_five_reps.py`: α calibrado recalculado na CPU por `train.calibrate_alpha` nos mesmos 32
hologramas de treino que o `train()` sorteou (RandomState(0)), grade estendida 12 passos; α treinado do checkpoint
(`fourier.alpha`); distância pela mesma conversão (`pilot_five_reps.mm`). Conferido: o calibrado recalculado do L008
bate, nas cinco repetições, com o que o log do treino imprimiu (6 casas). Rodo de novo no fim, com todos os níveis.

## 2026-11-15, 10:51 — D5: L069 e L015 gravados e conferidos; r1 em todos os níveis; a regra "as curvas se separam" (ANTES de r2–r5)

### Gravações e conferências (contra `curve_u50_L008`)

| | L015 | L069 |
|---|---|---|
| gravação | 929 s (10:30–10:46) | 1331 s (10:08–10:30) |
| `annotations.csv` byte a byte, rótulos, mapas, poeira, sessões, brancos, metadata comum | idênticos | idênticos |
| `physics.json` | só `fill_mean` = 15 | só `fill_mean` = 69 |
| sem enchimento = L008 / com = o conjunto (imagens 100 e 0) | 0 / 0 níveis | 0 / 0 níveis |
| enchimento muda o holograma (rms) | 1,5–4,0 níveis | 10,3–10,5 níveis |
| letras por janela (média, dp, p5–p95, mín.–máx.) | 15,12, 3,67, 10–22, 5–32 | 69,08, 8,27, 55–83, 44–103 |
| na faixa, por 640² | 15,04 | 68,89 |
| área coberta | 1,04 % | 4,78 % |
| puladas | 0 | 0 |

### r1 (teste lido uma vez por modelo; `results_exp_resolucao/density_curve.csv`, `_reps.csv`, `_reading.json`)

`LAW=u50 bash scripts/exp_resolucao/density_curve.sh 5 table`. Correção no script antes: o passo `table` não tem
`LEVEL` e o `printf %03d ""` falhava sob `set -e` (agora `${LEVEL:-0}`; nada mais muda).

| nível | por janela / mm² | área | sobreposição (π D² σ) | raw F1 / rej. | prop F1 / rej. | rec_z0 F1 / rej. | prop − raw F1 / rej. | rec_z0 − prop F1 / rej. |
|---|---|---|---|---|---|---|---|---|
| 8 | 8,06 / 7,06 | 0,54 % | 0,242 (0,277) | 0,9251 / 0,6135 | 0,9747 / 0,9799 | 0,9737 / 0,9952 | +0,050 / +0,366 | −0,001 / +0,015 |
| 15 | 15,12 / 13,24 | 1,04 % | 0,405 (0,520) | 0,9129 / 0,5435 | 0,9751 / 0,9815 | 0,9762 / 0,9863 | +0,062 / +0,438 | +0,001 / +0,005 |
| 69 | 69,08 / 60,47 | 4,78 % | 0,907 (2,374) | 0,8608 / 0,2576 | 0,9695 / 0,9678 | 0,9590 / 0,8478 | +0,109 / +0,710 | −0,011 / −0,120 |
| 154 | 154,10 / 134,90 | 10,54 % | 0,995 (5,295) | 0,7895 / 0,0588 | 0,9557 / 0,8325 | 0,9695 / 0,9694 | +0,166 / +0,774 | +0,014 / +0,137 |
| 343 | 343,15 / 300,40 | 23,35 % | 1,000 (11,79) | 0,6739 / 0,0386 | 0,9417 / 0,7383 | 0,9527 / 0,8333 | +0,268 / +0,700 | +0,011 / +0,095 |

Diferença para o esparso (mesma repetição, r1), F1 / rejeição:

| nível | raw | prop | rec_z0 |
|---|---|---|---|
| 15 | −0,012 / −0,070 | +0,001 / +0,002 | +0,003 / −0,009 |
| 69 | −0,064 / **−0,356 (caiu em rejeição)** | −0,005 / −0,012 | −0,015 / −0,147 |
| 154 | **−0,136 / −0,555 (caiu nas duas)** | −0,019 / −0,147 | −0,004 / −0,026 |
| 343 | **−0,251 / −0,575 (caiu nas duas)** | −0,033 / −0,242 | −0,021 / −0,162 |

- **"Caiu" (r1, provisório):** os crops caem em rejeição a partir do 69 e em F1 a partir do 154. A camada e a
  reconstrução não caem em nenhum nível (a maior queda da camada é −0,033 de F1 e −0,242 de rejeição, no 343).
- **"As curvas se separam" (r1), aplicada mecanicamente:** 15 → sim, por (ii) (camada − crops em rejeição = +0,438
  ≥ 0,30); 69 → sim, por (i), (ii) e (iii); 154 → sim, por (i), (ii) e (iii); 343 → sim, por (i), (ii) e (iii). O 8
  recebe de qualquer jeito (já tem r1–r5). **Portanto r2–r5 em todos os quatro níveis: 15, 69, 154 e 343.**
- Lançados a seguir, em dois processos de GPU: 15 e 69 num tmux, 154 e 343 no outro.

### Q1, os conjuntos que já existem no mesmo eixo (descritivo; nenhum teste lido)

`python scripts/exp_resolucao/hologram_diameter.py --set realistic|small_near --device cuda:5`, cada um pelo seu
caminho de gravação (layout do paper: tamanho de fonte inteiro, máscara no pixel; caminho nativo, s = 1; o z₀, a
margem e as leis do próprio conjunto; profundidade 0; sem ruído, sem poeira). Os raios crescem com √(z₀ / 1 mm)
(o tamanho do padrão com o mesmo número de Fresnel), e a janela cresce para conter R_OUT·k.

- **Um erro meu de código, achado e corrigido antes de qualquer número:** na generalização, a variável da escala dos
  raios (`k`) era sobrescrita pelo índice da letra no laço (`for k in range(10)`), e a primeira chamada (realistic)
  caiu com NaN (energia nula no disco de raio 0). Corrigido (`ks`); a versão corrigida, rodada de novo no
  `bench_1mm`, refaz o `hologram_diameter.csv` da fase 1 **byte a byte** (o resumo e a figura da fase 1 foram
  restaurados do git, intocados). O rótulo `layout` dos dois resumos novos dizia "type" (classe, não instância):
  corrigido no código e no campo dos dois json.

| conjunto | z₀ | k | R (192 nominal) | janela | lado p50 | D_rms(192) (D_ef) | conv. 256/192 | D_86 | D_vis | letras por mm² (janela / faixa) | π D² σ | sobreposição |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bench_1mm (fase 1) | 1,0 mm | 1 | 192 px | 768 | 17,5 px | 111,8 µm | 0,17 % | 114,9 µm | 159,3 µm | 7,06 | 0,277 | 0,242 |
| small_near | 2,0 mm | 1,414 | 272 px | 1088 | 28,0 px | **157,5 µm** (94,3 px) | 0,00006 % | 161,4 µm | 226,8 µm | 7,06 / 7,00 | 0,550 | **0,423** |
| realistic | 19,25 mm | 4,387 | 842 px | 3200 | 80,0 px | **447,1 µm** (267,7 px) | 0,04 % | 455,1 µm | 668,2 µm | 7,06 / 7,00 | 4,43 | **0,988** |

(`hologram_diameter_realistic*`, `hologram_diameter_small_near*`; figuras `img/hologram_diameter_<conjunto>.png`.)
Nos três, D_rms convergiu (todas as letras dentro de 5 %), então o eixo usa D_rms(192·k).
