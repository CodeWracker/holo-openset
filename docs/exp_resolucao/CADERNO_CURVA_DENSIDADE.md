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

## 2026-11-15, 11:34 — D6: r2–r5 em 15, 69, 154 e 343; tabela final, figura e α da família

r2–r5 lançados às 10:51 (15 e 69 no tmux `res_curve_reps_A`; 154 e 343 em `res_curve_reps_B`, 90 s depois), fim às
11:18. As 75 avaliações da família existem (5 níveis × 3 fluxos × 5 repetições), cada teste lido uma vez; os 75
modelos rodaram os 3000 passos (conferido no log). Treino por repetição ≈ 2,5–5 min (dois processos na GPU),
avaliação ≈ 20–40 s. Disco: conjuntos 8,7–9,1 GB cada (≈ 44 GB), modelos 669 MB por nível.

### Tabela final (`results_exp_resolucao/density_curve.csv`, por nível e fluxo; `density_curve_reps.csv`, por repetição; `density_curve_reading.json`)

D = 111,8 µm (D_rms(192)). Média (mín.–máx.) de 5 repetições, teste:

| nível | por janela / mm² | área | sobrep. (π D² σ) | raw F1 | raw rej. | prop F1 | prop rej. | rec_z0 F1 | rec_z0 rej. |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 8,06 / 7,06 | 0,54 % | 0,242 (0,277) | 0,937 (0,925–0,947) | 0,714 (0,614–0,827) | 0,975 (0,969–0,978) | 0,983 (0,937–1,000) | 0,977 (0,974–0,980) | 0,996 (0,988–1,000) |
| 15 | 15,12 / 13,24 | 1,04 % | 0,405 (0,520) | 0,922 (0,913–0,931) | 0,612 (0,531–0,698) | 0,974 (0,972–0,975) | 0,993 (0,982–1,000) | 0,978 (0,976–0,981) | 0,993 (0,985–1,000) |
| 69 | 69,08 / 60,47 | 4,78 % | 0,907 (2,374) | 0,855 (0,847–0,861) | 0,260 (0,211–0,303) | 0,972 (0,969–0,976) | 0,975 (0,944–0,995) | 0,973 (0,959–0,978) | 0,967 (0,848–0,998) |
| 154 | 154,10 / 134,90 | 10,54 % | 0,995 (5,295) | 0,789 (0,782–0,794) | 0,089 (0,059–0,115) | 0,957 (0,943–0,964) | 0,864 (0,717–0,950) | 0,972 (0,970–0,973) | 0,976 (0,969–0,983) |
| 343 | 343,15 / 300,40 | 23,35 % | 1,000 (11,79) | 0,668 (0,660–0,682) | 0,032 (0,022–0,039) | 0,942 (0,936–0,953) | 0,744 (0,650–0,865) | 0,960 (0,953–0,965) | 0,895 (0,833–0,944) |

Acerto fechado (média): raw 0,977 / 0,970 / 0,941 / 0,894 / 0,770; prop 0,997 / 0,997 / 0,992 / 0,987 / 0,975;
rec_z0 0,998 / 0,999 / 0,997 / 0,994 / 0,985 (8 / 15 / 69 / 154 / 343).

Camada − crops e reconstrução − camada (média, mín.–máx.):

| nível | prop − raw F1 | prop − raw rej. | rec_z0 − prop F1 | rec_z0 − prop rej. | limiares do P0 (F1 / rej. / os dois, de 5) |
|---|---|---|---|---|---|
| 8 | +0,038 (0,031–0,050) | +0,269 (0,170–0,366) | +0,002 | +0,013 | 0 / 2 / 0 |
| 15 | +0,052 (0,041–0,062) | +0,381 (0,302–0,451) | +0,004 | +0,000 | 0 / 5 / 0 |
| 69 | +0,116 (0,109–0,126) | +0,715 (0,641–0,766) | +0,001 | −0,009 | 5 / 5 / 5 |
| 154 | +0,168 (0,161–0,172) | +0,775 (0,649–0,834) | +0,015 | +0,111 | 5 / 5 / 5 |
| 343 | +0,273 (0,268–0,277) | +0,712 (0,624–0,827) | +0,018 | +0,152 | 5 / 5 / 5 |

### "Caiu" pela regra do Q0 (contra o nível 8, mesma repetição; 4 de 5), aplicada mecanicamente

| nível | raw F1 / rej. (repetições que caíram) | prop F1 / rej. | rec_z0 F1 / rej. |
|---|---|---|---|
| 15 | não (0) / não (0) | não / não | não / não |
| 69 | não (0) / **caiu (5)** | não / não | não / não |
| 154 | **caiu (5)** / **caiu (5)** | não / não | não / não |
| 343 | **caiu (5)** / **caiu (5)** | não (0) / não (0) | não / não |

Quedas médias da camada contra o esparso: F1 −0,001 / −0,003 / −0,018 / −0,033; rejeição +0,010 / −0,008 / −0,119 /
−0,239 (15 / 69 / 154 / 343). **Onde a camada cai: a camada não caiu, nem em F1 nem em rejeição, até a densidade
obtida (343 letras por janela, 300 por mm², 23,35 % de área).** A reconstrução também não caiu.

### Figura (`docs/exp_resolucao/img/density_curve.png` e `.pdf`, `scripts/exp_resolucao/density_curve_figure.py`, só lê os csv)

Eixo x: π D² σ em escala log, marcas com a razão de sobreposição de cada nível (0,242 / 0,405 / 0,907 / 0,995 /
1,0000); em cima, objetos por mm² obtidos; painéis F1 e rejeição; crops, camada e reconstrução; círculos abertos e
linha pontilhada = r1, cheios com barra e linha contínua = média, mínimo e máximo das 5 repetições.

### α da família (`results_exp_resolucao/curve_alpha.csv`, `scripts/exp_resolucao/curve_alpha.py`)

Calibrado recalculado por `train.calibrate_alpha` (as 32 imagens que o `train()` sorteou), como no
`pilot_five_reps.py`; treinado do checkpoint (`fourier.alpha`). Os 25 calibrados recalculados batem com os que o log
de cada treino imprimiu (6 casas). Distância (mm), média (mín.–máx.):

| nível | calibrado | treinado | variação |
|---|---|---|---|
| 8 | 0,9965 (0,9943–0,9999) | 0,9647 (0,9629–0,9679) | −3,19 % (−3,70 a −2,93) |
| 15 | 0,9976 (0,9971–0,9999) | 0,9655 (0,9594–0,9701) | −3,23 % |
| 69 | 0,9993 (0,9971–0,9999) | 0,9716 (0,9677–0,9775) | −2,77 % |
| 154 | 0,9999 (todos) | 0,9788 (0,9750–0,9874) | −2,11 % |
| 343 | 0,9999 (todos) | 0,9835 (0,9795–0,9858) | −1,64 % |

Nível 8, por repetição (α calibrado → mm; α treinado → mm; variação): r1 0,001056 → 0,9971; 0,001025 → 0,9679;
−2,93 % · r2 0,001059 → 0,9999; 0,001020 → 0,9629; −3,70 % · r3 0,001053 → 0,9943; 0,001020 → 0,9629; −3,16 % ·
r4 0,001053 → 0,9943; 0,001020 → 0,9631; −3,14 % · r5 0,001056 → 0,9971; 0,001024 → 0,9667; −3,04 %.

`pytest`: 72 passam; `reproduce check`: 13/13.

## 2026-11-15, 13:43 — D7: controle S (Q2), começo; parado antes de gravar, com duas perguntas

### Passo 1: as leis do `small_near` (com arquivo e linha)

- Gerado por `simulate small` (`holo_openset/cli.py:70–75`): `G.generate(data/small_near, phys=dict(sets, z0=2e-3),
  n_images=5000, workers, layout='small')`; pela pipeline do paper com `--workers 16` (`holo_openset/pipeline.py:49`).
- `generate` (`holo_openset/sim/generate.py:182`): semente 17, 100 imagens por sessão, 50 sessões, divisão por
  sessão 35 / 7 / 8 (`split_sessions`, `generate.py:162–165`); 3500 / 700 / 800 imagens (conferido no
  `metadata.csv`); câmera semente 7, 8 brancos.
- Física (`data/small_near/physics.json`, conferida campo a campo contra `Physics()`): o padrão inteiro, a menos de
  z₀ = 2,0 mm: margem 1728, alcance 1024, profundidade normal com desvio 50 µm cortada em ±150 µm, poeira 2/mm² em
  +1,0 e −0,2 mm, poeira da janela 7/mm² a 0,5 mm, LED 385 nm ± 10 nm em 7 comprimentos de onda, pinhole 100 µm a 15
  cm, feixe, PRNU 1 %, poço 6000 e⁻, exposição 0,45, leitura 3 e⁻, 8 bits, caixa do pixel (s = 1).
- Layout `SmallLayout` (`holo_openset/sim/scene.py:28–31`, herdando `Layout`, `scene.py:17–25`): fonte inteira
  uniforme em 16–48 px (`rng.randint`, `scene.py:146`), borda 6 px, espaçamento 4 px, 3–18 letras por janela
  (média 8, desvio 3), 72 % distintas, rotação ±35°, 500 tentativas; letras de fora da janela com a mesma densidade
  (`make_scene`, `scene.py:182–203`).
- Receita do paper para ele (`pipeline.py:105–110`): `train --set small_near --flow F --rep R --no-aux` (grade
  padrão de α, sem `--alpha-extend`) e `evaluate --set small_near --flow F --rep R`; o cache `rec_z0` vem de
  `reconstruct --set small_near --methods z0 af twin` (`pipeline.py:54`).

**O que o caminho novo não consegue escrever hoje:** o `FresnelLayout` deriva fonte mínima, fonte máxima, borda e
espaçamento de um único `scale` × os valores do `Layout` (70, 118, 12, 6; `scene.py:58–61`). O `SmallLayout` pede
16 / 48 / 6 / 4, que não são proporcionais (16/70 = 0,229; 48/118 = 0,407; 6/12 = 0,5; 4/6 = 0,667). Pela regra
("se alguma lei não puder ser reproduzida exatamente no caminho novo, pare"), parei antes da convergência e da
gravação. Proposta (não implementada): quatro parâmetros opcionais do `FresnelLayout` (`font_min`, `font_max`,
`border`, `margin`) que, dados, substituem os derivados do `scale`; ausentes, nada muda (os digests das cenas
conferem). Ficariam também, como no controle B, as diferenças de definição do caminho novo: fonte contínua em [16,
48] em vez de inteira, posição contínua, caixa do pixel que contém a tinta para o espaçamento, poeira na grade mestra.

**Segunda pergunta:** o `data/small_near` em disco não tem `rec_z0.npy`. A referência `rec_z0` precisa dele;
`reconstruct --set small_near --methods z0` o escreveria dentro de `data/small_near` (≈ 6 GB, como a pipeline do
paper faz). Não escrevi.

### Passo 5 (parcial): referência, `small_near` em disco, r1, GPU 5 (a GPU 4 estava ocupada por outro usuário)

`python -m holo_openset train --set small_near --flow raw|prop --rep 1 --no-aux --device cuda:5 --threads 4`;
`python -m holo_openset evaluate --set small_near --flow raw|prop --rep 1 --device cuda:5 --threads 4`
(log `logs/exp_resolucao/curve_S_reference.log`, 13:41–13:43; teste lido uma vez):

| fluxo | F1 | rejeição | paper r1 (só referência) |
|---|---|---|---|
| raw | 0,7909 | 0,1176 | 0,7939 / 0,0974 |
| prop | 0,9633 | 0,8953 | 0,9710 / 0,9420 |
| rec_z0 | não rodado (falta o cache) | | 0,9712 / 0,9622 |

α da camada: calibrado 0,002100 (o log diz "the bench would be 0,002118", 2,0 mm), depois do treino 0,002079.

## 2026-11-15, 13:51 — D7 (continuação): respostas do responsável; comprimentos dados no layout físico, cache de `rec_z0`, convergência a 2 mm, nativa × convergida, referência completa

Respostas (mensagem do responsável): (1) implementar os quatro comprimentos opcionais; (2) pode escrever o cache
`rec_z0` em `data/small_near` com o comando da pipeline, sem alterar o que existe.

### Comprimentos dados (commit `64e9e94`; a única mudança no pacote)

- `FresnelLayout` (`holo_openset/sim/scene.py`): `font_min`, `font_max`, `border`, `margin` (`LENGTHS`), dados,
  substituem os derivados do `scale`; o `physics.json` guarda os dados em `layout_params['lengths_given']` (ausente se
  nenhum), e só esses são lidos de volta (`generate.make_layout`): os comprimentos que o `physics.json` dos conjuntos
  de antes já registra não viram "dados". `simulate fresnel --layout font_min=16 …` os converte (`cli.py`).
- `tests/test_layout_lengths.py` (6 testes): sem comprimentos dados, os digests das quatro cenas de antes (para
  `FresnelLayout()`, `lengths_given={}` e o layout relido de um `physics.json`), e um `physics.json` antigo não
  gera `lengths_given`; dados (16, 48, 6, 4): os valores chegam à cena e são os do `SmallLayout`, voltam iguais pelo
  `physics.json`, os tamanhos sorteados ficam em [16, 48], a caixa de tinta das anotadas respeita a borda de 6 px
  (a 1/8 px), e o espaçamento de 4 px vale entre quaisquer duas letras; um conjunto gerado guarda e relê os quatro.
- `pytest`: **78 passam** (72 + 6); `reproduce check`: **13/13** (`env -u HOLO_RESULTS -u HOLO_MODELS`).
- **Diferenças de definição que ficam (as do controle B), e que entram na leitura:** fonte contínua em [16, 48] em
  vez de inteira; posição contínua (a 1/16 px) em vez de inteira; espaçamento medido na caixa de pixels que contém a
  tinta; glifo desenhado na grade mestra 16× e levado à grade de gravação por média de área (no `small_near`, o glifo
  é desenhado a 1× pelo Pillow); poeira na grade mestra. **O controle troca duas peças ao mesmo tempo: a propagação
  sobreamostrada e o desenho das letras.** As cenas não são as mesmas do `small_near` (sorteios contínuos), só as
  mesmas leis, sementes e sessões.

Leis escritas no caminho novo (`scripts/exp_resolucao/small_near_control.sh`): `--layout factor=16 scale=1 font_min=16
font_max=48 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3 letters_max=18`, `--set-physics z0=2.0e-3
oversample=<s>` (o resto é o padrão, como o `physics.json` do `small_near`), 5000 imagens, 100 por sessão, semente 17.

### Cache `rec_z0` do `small_near` (`small_near_control.sh 5 ref_cache`, 13:47:37–13:48:16, código `64e9e94`)

Disco antes: 2,0 TB livres. Comando: `python -m holo_openset reconstruct --set small_near --methods z0 --device
cuda:5` (o da pipeline, `pipeline.py:54`, só com `z0`). Lista da pasta (tamanho, data) e sha256 de `holograms.npy`,
`backgrounds.npy`, `annotations.csv`, `metadata.csv`, `physics.json`, `sessions.csv`, `dust.csv` e as contagens de
`labels/` e `objects/` antes e depois (`logs/exp_resolucao/S_small_near_{before,after}.txt`): **iguais**; a única
diferença são dois arquivos novos, `rec_z0.npy` (6 144 000 128 bytes) e `autofocus.csv` (158 329 bytes; o mesmo
comando o escreve, como na pipeline). `holograms.npy` sha256 `4c62181a…d7776`.

### Convergência a 2,0 mm (`small_near_control.sh 5 converge` → `results_exp_resolucao/oversampling_convergence_small_near.csv`)

4 cenas (imagens 0, 1250, 2500, 3750), 50 µm, margem 1728, alcance 1024, layout acima, raster mestre 16×, sem ruído.

| par | rel_rms por cena | dif. máx. (níveis) | passa (≤ 1 %) |
|---|---|---|---|
| (1, 2) | 5,82 / 4,96 / 4,84 / 4,76 % | 3,78 | não |
| (2, 4) | 0,80 / 0,73 / 0,67 / 0,59 % | 0,60 | sim |

**Pela regra do P0: s = 2.** Raster mestre: 16× (o do piloto, múltiplo de 2; sem desvio de raster como o do controle B).
(2, 4) passa com folga menor que a 1 mm (0,80 % contra 1 %).

### Nativa × convergida, separando as duas peças (`oversampling_convergence.py native`, `S_CONV=2` → `oversampling_native_small_near.csv`; e s = 4 → `_s4.csv`)

Mesmas 4 cenas físicas; normalizado pelo rms do padrão da gravação convergida (s = 2, raster mestre). (i) só a
propagação: a mesma máscara no pixel (a média de área do raster mestre em 1 px, o que o caminho nativo lê) com s = 1 e
com s = 2; (ii) só o desenho: a máscara no pixel contra o raster mestre, as duas com s = 2; total: nativa (s = 1,
máscara no pixel) contra convergida.

| cena | total | (i) propagação | (ii) desenho | dif. máx. total / (i) / (ii) (níveis) |
|---|---|---|---|---|
| 0 | 5,82 % | 5,15 % | 7,18 % | 1,93 / 2,02 / 2,83 |
| 1250 | 4,96 % | 3,79 % | 6,32 % | 2,26 / 1,47 / 3,11 |
| 2500 | 4,84 % | 3,44 % | 6,55 % | 3,78 / 3,27 / 6,07 |
| 3750 | 4,76 % | 3,57 % | 6,25 % | 2,76 / 1,81 / 3,29 |

Com s = 4 no lugar de 2: total 4,77–5,77 %, (i) 3,55–5,25 %, (ii) 6,92–7,65 %. As duas peças se compensam em parte
(o desenho sozinho erra mais que o total). Nota: aqui a "máscara no pixel" é a média do raster mestre; no `small_near`
o glifo foi desenhado a 1× pelo Pillow, o que é ainda outra máscara (não medida).

### Referência completa (`small_near` em disco, r1, `--no-aux`, grade padrão de α; teste lido uma vez)

| fluxo | F1 | rejeição | fechada | limiar | paper r1 (F1 / rej.) |
|---|---|---|---|---|---|
| raw | 0,7909 | 0,1176 | — | — | 0,7939 / 0,0974 |
| prop | 0,9633 | 0,8953 | — | — | 0,9710 / 0,9420 |
| rec_z0 | 0,9778 | 0,9871 | — | — | 0,9712 / 0,9622 |

(rec_z0: `small_near_control.sh 5 ref_train` e `ref_evaluate`, 13:48–13:49; raw e prop do D7 anterior.)

## 2026-11-15, 14:25 — D7 (fim): `small_near_newrec` gravado, D, treinos, tabela e a leitura do Q2

### Gravação e sanidade

`S_CONV=2 MASTER=16 WORKERS=6 bash scripts/exp_resolucao/small_near_control.sh 5 record` (tmux `res_S_record`,
13:49:24–14:16:32, 1628 s; 6 construtores, 6–9 threads prontas, `cpu.pressure` some avg10 = 0,00; GPU 5): `simulate
fresnel --name small_near_newrec --n-images 5000 --workers 6 --set-physics z0=2.0e-3 oversample=2 --layout factor=16
scale=1 font_min=16 font_max=48 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3 letters_max=18`. Disco:
8,7 GB com o `rec_z0.npy`. `physics.json`: `lengths_given` = 16 / 48 / 6 / 4, `oversample` 2, z₀ 2,0 mm.

Sanidade (`small_near_control.sh 5 verify` = `bench_sanity.py --set small_near_newrec --ref small_near`, só treino;
`results_exp_resolucao/small_near_newrec_sanity.json`, folha `docs/exp_resolucao/img/small_near_newrec_examples.png`):
3500 / 700 / 800 imagens e 8,06 letras por imagem (3–18), as do `small_near`; lado da caixa inteira p5 / p50 / p95 =
15 / 27 / 40,6 px (`small_near`: 15 / 28 / 42), N_F 0,204 / 0,660 / 1,493 (0,204 / 0,710 / 1,597); lado da tinta
14,1 / 25,8 / 39,6 px; nível médio 101,36 (101,31), brancos 101,51 (101,50); ruído refeito das sementes: média
0,001–0,007, rms 2,091–2,101 (2,091–2,101). A fonte contínua e a caixa de tinta da grade mestra deixam as letras
≈ 1 px menores na mediana, como no controle B.

### D e sobreposição no caminho novo (`small_near_control.sh 5 diameter`, antes de qualquer treino; `hologram_diameter_small_near_newrec*`)

Mesmas definição e amostra (semente 20261115, 10 por classe), leis do `small_near_newrec` (layout físico com os
comprimentos dados, raster 16×, s = 2), raios × √2 (R = 136 / 181 / 272 / 362 px), janela 1088, margem 1728.
**D_rms(192·k) = 99,2 px = 165,7 µm** (convergiu: 256/192 difere 0,006 %); D_86 167,5 µm; D_vis 233,0 µm. Com 7,06
letras por mm² na janela: π D² σ = **0,609**, sobreposição **0,456** (o `small_near` nativo: 157,5 µm, 0,550,
0,423).

### Treino e avaliação do controle (`reconstruct` 68 s; `train` raw 14:19:35, prop 14:21:01, rec_z0 14:22:31, 276 s no total; `evaluate` 41 s; teste lido uma vez)

α da camada: calibrado 0,002111, depois do treino 0,002106 (referência: 0,002100 → 0,002079; "the bench would be"
0,002118 = 2,0 mm).

### Tabela (`results_exp_resolucao/small_near_control.csv`, `small_near_control_reading.json`; `small_near_control.sh 5 table`)

| linha | fluxo | F1 | rejeição | fechada | limiar | D (µm) | π D² σ | sobreposição |
|---|---|---|---|---|---|---|---|---|
| referência (`small_near` em disco, `--no-aux`, agora) | raw | 0,7909 | 0,1176 | 0,8885 | 0,5856 | 157,5 | 0,550 | 0,423 |
| | prop | 0,9633 | 0,8953 | 0,9957 | 0,9859 | | | |
| | rec_z0 | 0,9778 | 0,9871 | 0,9990 | 0,9871 | | | |
| controle (`small_near_newrec`) | raw | 0,7993 | 0,1200 | 0,8992 | 0,5994 | 165,7 | 0,609 | 0,456 |
| | prop | 0,9728 | 0,9775 | 0,9955 | 0,9876 | | | |
| | rec_z0 | 0,9728 | 0,9541 | 0,9982 | 0,9881 | | | |
| paper r1 (só referência) | raw | 0,7939 | 0,0974 | 0,8969 | 0,5733 | | | |
| | prop | 0,9710 | 0,9420 | 0,9965 | 0,9842 | | | |
| | rec_z0 | 0,9712 | 0,9622 | 0,9984 | 0,9870 | | | |
| R_curva (família u50, crops, r1, níveis 15–69, peso 0,104 no 69) | raw | 0,9074 | 0,5137 | 0,9688 | | | 0,609 | 0,456 |

### Leitura do Q2, aplicada mecanicamente (só crops)

R_ant = (0,7909; 0,1176); controle = (0,7993; 0,1200); R_curva = (0,9074; 0,5137). Distâncias: F1 0,0084 a R_ant
contra 0,1081 a R_curva; rejeição 0,0024 contra 0,3937. **Mais perto de R_ant nas duas: pela regra, a amostragem
nativa não explica o desvio; o conjunto continua fora da curva.** O controle troca duas peças ao mesmo tempo (a
propagação sobreamostrada e o desenho das letras); como nenhuma das duas muda os crops, a leitura vale para as duas
juntas. Nenhum outro braço foi rodado.

### O que pareceu estranho

1. Os crops do controle ficaram onde estavam (0,799 / 0,120 contra 0,791 / 0,118), embora a gravação nativa difira
   da convergida em 4,8–5,8 % do padrão nas cenas da conferência (3,4–5,2 % só da propagação, 6,2–7,2 % só do
   desenho): o erro de amostragem é grande na imagem e não pesa nos crops.
2. A camada melhorou no controle (rejeição 0,895 → 0,978) e a reconstrução caiu em rejeição (0,987 → 0,954), em
   uma repetição só; sem critério para elas.
3. Na mesma sobreposição (0,456), os crops da família de 1 mm dariam 0,907 / 0,514 por interpolação; as letras
   pequenas a 2 mm ficam 0,11 / 0,39 abaixo, nos dois caminhos de gravação. Diferenças que ficam entre os dois: o
   tamanho das letras em pixels (mediana 26 px contra 17,5 px), a faixa de N_F (0,20–1,49 contra 0,30–0,98), a
   distância (2 mm contra 1 mm) e a profundidade (normal de 50 µm cortada em ±150 µm contra uniforme ±25 µm). Não
   investiguei.

## 2026-11-15, 16:01 — D8: Fase S (Q3: C, D, L), o que vai rodar, ANTES de qualquer treino ou leitura de teste

Pré-registro: `CADERNO_CURVA.md`, Q3 (commit `b97121d`), seções C, D e L. GPUs 0, 1 e 2. Script da fase:
`scripts/exp_resolucao/phaseS.sh <GPU> <passo>` (fila retomável; logs `logs/exp_resolucao/S2_*.log`).

- **C (coluna de 2 mm):** `small_near_newrec` em disco; os dez fluxos de `SMALL_FLOWS` (`pipeline.py:31`), r1–r5,
  receita `train --set small_near_newrec --flow F --rep R --no-aux` e `evaluate --set small_near_newrec --flow F
  --rep R` (`pipeline.py:105–110`), `--threads 4`. Caches: `rec_z0` existe (Q2-S); `rec_af` e `rec_twin` por
  `reconstruct --set small_near_newrec --methods af twin` (a pipeline roda `z0 af twin` de uma vez, `pipeline.py:54`;
  o `rec_z0.npy` não é reescrito; o `autofocus.csv` do conjunto, escrito pela reconstrução só em z₀, é reescrito
  com as distâncias do autofoco; cópia dele antes em `logs/exp_resolucao/S2_small_near_newrec_autofocus_z0only.csv`).
  `wiener`, `learned`, `complex`, `prop`, `bank_jit`, `bank_w3` e `raw` leem o holograma. Os modelos e as
  avaliações de r1 de `raw`, `prop`, `rec_z0` já existem e são pulados (não retreinados, não relidos). Cada
  avaliação nova lê o teste uma vez, na própria fila; a tabela só junta os json.
- **C, ao lado:** nativa × convergida para as letras pequenas a 19,25 mm (leis do `small_z0`: as do `small_near`
  com z₀ = 19,25 mm), pares (1, 2) e (2, 4) e a separação em propagação e desenho, 4 cenas sem ruído. Se a nativa
  passar de 1 %, paro e aviso; não regravo.
- **D (controles em r1; s = 2, raster 16, semente 17, 5000 imagens):**
  - `small_near_ctlN`: fontes = as do conjunto base × √(2,0 / 19,25) = 0,3223292 (a lei da família padrão: o `scale`
    do `FresnelLayout`, contínuo em 22,563–38,035 px), borda 6 e espaçamento 4 dados (como no `small_near_newrec`);
    `--layout factor=16 scale=0.3223291856101521 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3
    letters_max=18`, `--set-physics z0=2.0e-3 oversample=2`.
  - `small_near_ctlP`: o `small_near_newrec` com `depth_uniform=25e-6` (`--layout factor=16 scale=1 font_min=16
    font_max=48 border=6 margin=4 …`, `--set-physics z0=2.0e-3 oversample=2 depth_uniform=25e-6`).
  - Antes dos treinos: sanidade contra o `small_near_newrec`, D e sobreposição, tamanhos e N_F (p5 / p50 / p95)
    escritos aqui. Depois: r1, `raw`, `prop`, `rec_z0`, `--no-aux`.
- **D, estratificada:** registro aqui que é **uma segunda passada no mesmo teste do `small_near_newrec`, com o mesmo
  modelo de crops de r1 e o mesmo limiar**; não escolhe nada.
- **L:** o teste de `curve_feasibility_343.csv` a 514 e 771 letras por janela, nas mesmas 20 cenas (sem holograma).

## 2026-11-15, 16:40 — D9: Q3-C (coluna de 2 mm, cinco repetições), letras pequenas a 19,25 mm, Q3-L

### C. `small_near_newrec`, dez fluxos × r1–r5 (teste lido uma vez por modelo)

- Caches (`phaseS.sh 0 caches`, 16:01–16:04, 190 s): `reconstruct --set small_near_newrec --methods af twin` →
  `rec_af.npy`, `rec_twin.npy`; `autofocus.csv` reescrito com as distâncias do autofoco (cópia da versão só-z₀ em
  `logs/exp_resolucao/S2_small_near_newrec_autofocus_z0only.csv`); `rec_z0.npy` intocado.
- Filas (`phaseS.sh <GPU> queue`, `--no-aux`, `--threads 4`): A (GPU 1: raw, prop, rec_z0, learned, complex; 16:02–16:39),
  B (GPU 2: wiener, bank_jit, bank_w3; 16:02–16:35), C (GPU 0: rec_af, rec_twin; 16:06–16:27). 47 treinos novos, todos
  com 3000 passos (conferido no log); os 3 de r1 que existiam foram pulados (modelo e json).
- Tabela: `python scripts/exp_resolucao/small_near_five_reps.py` → `results_exp_resolucao/small_near_newrec_five_reps.csv`
  e `_reading.json` (coluna do paper lida de `results/eval/small_near`, nada escrito lá). Média (mín.–máx.) de 5:

| fluxo | F1 novo | F1 paper | Δ F1 | rejeição nova | rejeição paper | Δ rej. | fechada nova / paper | conhecidas nova / paper |
|---|---|---|---|---|---|---|---|---|
| raw | 0,8060 (0,799–0,811) | 0,7929 | +0,013 | 0,191 (0,120–0,242) | 0,153 | +0,038 | 0,896 / 0,888 | 0,890 / 0,884 |
| learned | 0,9508 (0,938–0,963) | 0,9445 | +0,006 | 0,818 (0,688–0,938) | 0,773 | +0,044 | 0,981 / 0,979 | 0,953 / 0,952 |
| complex | 0,9493 (0,934–0,960) | 0,9554 | −0,006 | 0,795 (0,649–0,914) | 0,843 | −0,048 | 0,985 / 0,986 | 0,955 / 0,956 |
| wiener | 0,9643 (0,956–0,975) | 0,9659 | −0,002 | 0,890 (0,761–0,980) | 0,906 | −0,016 | 0,992 / 0,991 | 0,959 / 0,960 |
| prop | 0,9732 (0,972–0,976) | 0,9721 | +0,001 | 0,986 (0,974–1,000) | 0,963 | +0,022 | 0,995 / 0,996 | 0,957 / 0,959 |
| bank_jit | 0,9697 (0,960–0,975) | 0,9769 | −0,007 | 0,950 (0,862–1,000) | 0,986 | −0,037 | 0,996 / 0,997 | 0,957 / 0,963 |
| bank_w3 | 0,9740 (0,971–0,977) | 0,9720 | +0,002 | 0,968 (0,933–1,000) | 0,956 | +0,012 | 0,995 / 0,996 | 0,962 / 0,960 |
| rec_z0 | 0,9744 (0,972–0,978) | 0,9741 | +0,000 | 0,985 (0,954–1,000) | 0,970 | +0,016 | 0,998 / 0,998 | 0,959 / 0,962 |
| rec_af | 0,9749 (0,969–0,978) | 0,9765 | −0,002 | 0,982 (0,950–1,000) | 0,988 | −0,005 | 0,998 / 0,998 | 0,960 / 0,962 |
| rec_twin | 0,9774 (0,973–0,981) | 0,9765 | +0,001 | 0,985 (0,939–1,000) | 0,979 | +0,006 | 0,997 / 0,998 | 0,964 / 0,964 |

- **Previsão registrada:** "nenhum fluxo muda o F1 médio em mais de 0,02" → **vale** (maior mudança: raw, +0,013).
  "A ordem das rotas não muda (crops muito abaixo; rotas com propagação juntas)" → **vale na forma registrada**: os
  crops são os últimos nos dois (0,806 contra 0,793), e as sete rotas com propagação ficam juntas (F1 0,964–0,977
  contra 0,966–0,977; a menor delas fica 0,158 acima dos crops, contra 0,173). **A ordem exata não é a mesma**: dentro
  das rotas com propagação (diferenças ≤ 0,013) e entre `learned` e `complex` (0,951 / 0,949 contra 0,945 / 0,955) os
  lugares trocam; as trocas estão dentro do espalhamento das repetições.

### C, ao lado: letras pequenas a 19,25 mm (sem teste; `phaseS.sh 0 converge_z0`, `S_CONV=2 … native_z0`)

Leis do `small_z0` (as do `small_near` com z₀ = 19,25 mm; o layout físico com os comprimentos dados, raster 16×),
4 cenas, 50 µm, margem 1728, alcance 1024, sem ruído (`oversampling_convergence_small_z0.csv`,
`oversampling_native_small_z0.csv`):

| | cena 0 | 1250 | 2500 | 3750 | dif. máx. |
|---|---|---|---|---|---|
| (1, 2) = nativa × s = 2, total | 0,63 % | 0,79 % | 0,54 % | 0,73 % | 0,35 níveis |
| (2, 4) | 0,053 % | 0,070 % | 0,042 % | 0,059 % | 0,05 níveis |
| só a propagação (máscara no pixel, s = 1 × s = 2) | 0,50 % | 0,44 % | 0,27 % | 0,49 % | 0,23 níveis |
| só o desenho (máscara no pixel × raster mestre, s = 2) | 0,87 % | 1,08 % | 0,75 % | 1,01 % | 0,52 níveis |

**(1, 2) passa (máximo 0,79 %): pela regra do P0, a amostragem do sensor já é a convergida a 19,25 mm, e a gravação
nativa do `small_z0` fica dentro da tolerância de 1 %.** Nada regravado. (Uma primeira chamada do `converge_z0` foi
interrompida por mim no começo, antes de escrever qualquer arquivo, porque eu a lancei com um sexto processo ainda
rodando; relançada logo depois, sem mudança.)

### L. O gerador acima de 300 por mm² (`curve_feasibility.py --levels 514 771` → `curve_feasibility_dense.csv`; sem holograma)

As 20 cenas do teste do 343 (imagens 0, 263, …, 4999), física do `bench_1mm` com 50 / 150 µm, layout do piloto.

| nível pedido | por mm² | pedidas por janela (média) | colocadas por janela (média, mín.–máx.) | puladas na janela | puladas no total | área coberta | s por cena |
|---|---|---|---|---|---|---|---|
| 343 (D1) | 300 | — | 344,7 (294–389) | 0 | 0 | 23,2 % | 2,5 |
| 514 | 450 | 516,2 | 512,3 (453–560) | 77 de 10 180 (0,76 %) | 199 de 30 203 (0,66 %) | 34,2 % (30,4–36,7) | 8,0 |
| 771 | 675 | 773,5 | 656,0 (636–677) | 2350 de 15 326 (15,3 %) | 6924 de 45 537 (15,2 %) | 41,7 % (40,4–42,8) | 13,7 |

A 514 o gerador coloca quase tudo (abaixo dos 5 % do Q0); a 771 ele satura em ≈ 650 letras por janela (≈ 575 por
mm², ≈ 42 % de área), e o nível entraria com a densidade obtida.

## 2026-11-15, 16:46 — D10: Q3-D, `small_near_ctlN` gravado e conferido, ANTES do treino

`phaseS.sh 0 record_ctlN` (tmux `res_S2_recN`, 16:04:06–16:42:46, 2320 s, 6 construtores): `simulate fresnel --name
small_near_ctlN --n-images 5000 --workers 6 --set-physics z0=2.0e-3 oversample=2 --layout factor=16
scale=0.3223291856101521 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3 letters_max=18`.
`physics.json`: `scale` 0,32233 (fontes 22,563–38,035 px, a lei da família padrão), `lengths_given` = borda 6 e
espaçamento 4 (os do `small_near_newrec`); física idêntica à do `small_near_newrec` (z₀ 2,0 mm, normal 50 / 150 µm,
s = 2).

`phaseS.sh 0 prep_ctlN` (191 s; `small_near_ctlN_sanity.json` contra o `small_near_newrec`, só treino;
`hologram_diameter_small_near_ctlN*`; `reconstruct --methods z0`):

| | `small_near_ctlN` | `small_near_newrec` | família padrão (`curve_u50_L008`, 1,0 mm) |
|---|---|---|---|
| lado da caixa inteira p5 / p50 / p95 | 19 / 25 / 34 px | 15 / 27 / 40,6 px | 14 / 18 / 24 px |
| N_F (caixa inteira) | 0,327 / 0,566 / 1,047 | 0,204 / 0,660 / 1,493 | 0,355 / 0,587 / 1,043 |
| lado da tinta | 18,1 / 24,5 / 32,9 px | 14,1 / 25,8 / 39,6 px | 12,8 / 17,4 / 23,3 px |
| N_F (tinta) | **0,295 / 0,544 / 0,979** | 0,179 / 0,603 / 1,417 | **0,297 / 0,547 / 0,982** |
| D_rms(192·k) | 164,6 µm | 165,7 µm | 111,8 µm |
| π D² σ / sobreposição | 0,601 / 0,451 | 0,609 / 0,456 | 0,277 / 0,242 |

Contagens (3500 / 700 / 800, 8,06 letras por imagem, 3–18), nível médio (101,40 contra 101,36) e ruído (rms
2,091–2,101) iguais. **Só a faixa de tamanhos (e com ela a de N_F) mudou; a de N_F agora é a da família padrão.** D e
a sobreposição quase não mudaram (164,6 contra 165,7 µm): o padrão a 2 mm é dominado pelo alcance da franja, não pelo
tamanho da letra. A seguir: r1, `raw`, `prop`, `rec_z0`, `--no-aux` (GPU 0).

## 2026-11-15, 16:52 — D11: Q3-D, `small_near_ctlP` gravado e conferido, ANTES do treino (e o r1 do ctlN, que já saiu)

`phaseS.sh 2 record_ctlP` (tmux `res_S2_recP`, 16:06:11–16:48:37, 2546 s, 6 construtores): `simulate fresnel --name
small_near_ctlP --n-images 5000 --workers 6 --set-physics z0=2.0e-3 oversample=2 depth_uniform=25e-6 --layout factor=16
scale=1 font_min=16 font_max=48 border=6 margin=4 letters_mean=8 letters_std=3 letters_min=3 letters_max=18`.
`prep_ctlP` (174 s): anotações iguais às do `small_near_newrec` em todas as colunas a menos de `depth` e `z` (as
mesmas letras: a lei uniforme usa o mesmo sorteio); |depth| máx. 24,9993 µm, desvio 14,427 µm (lei uniforme ±25
µm); lados (15 / 27 / 40,6 px), N_F (tinta 0,179 / 0,603 / 1,417), contagens, nível médio (101,36) e ruído (rms
2,091–2,102) **idênticos aos do `small_near_newrec`**. D_rms(192·k) = 165,7 µm, π D² σ = 0,609, sobreposição 0,456
(o mesmo do `small_near_newrec`: a medida de D é feita com profundidade 0, então não vê a lei). **Só a lei de
profundidade mudou.** A seguir: r1, `raw`, `prop`, `rec_z0` (GPU 2).

`small_near_ctlN` r1 (fila `S2_queue_ctlN`, 16:46–16:51, teste lido uma vez): `raw` 0,9160 / 0,5298; `prop` 0,9759 /
0,9895; `rec_z0` 0,9607 / 0,8494 (F1 / rejeição). A leitura do Q3-D sai na tabela, quando o ctlP existir.

## 2026-11-15, 16:58 — D12: Q3-D, tabela dos dois controles, leitura do Q3 e leitura estratificada

### Tabela (`python scripts/exp_resolucao/small_near_factors.py` → `results_exp_resolucao/small_near_factors.csv`, `small_near_factors_reading.json`; o mesmo código de geometria e de interpolação do Q2-S)

| conjunto | o que muda | D | π D² σ / sobrep. | raw F1 / rej. | prop F1 / rej. | rec_z0 F1 / rej. |
|---|---|---|---|---|---|---|
| `small_near_newrec` (R_reg) | — | 165,7 µm | 0,609 / 0,456 | 0,7993 / 0,1200 | 0,9728 / 0,9775 | 0,9728 / 0,9541 |
| `small_near_ctlN` | faixa de N_F da família | 164,6 µm | 0,601 / 0,451 | **0,9160 / 0,5298** | 0,9759 / 0,9895 | 0,9607 / 0,8494 |
| `small_near_ctlP` | lei de profundidade da família | 165,7 µm | 0,609 / 0,456 | **0,8032 / 0,1361** | 0,9778 / 0,9968 | 0,9743 / 0,9984 |

R_curva (crops da família u50 em r1, interpolação em log(π D² σ) entre os níveis 15 e 69): para o ctlN 0,9079 /
0,5163 (peso 0,095 no 69); para o ctlP 0,9074 / 0,5137 (peso 0,104).

### Leitura do Q3-D, aplicada mecanicamente (só crops)

| controle | dist. F1 a R_reg / a R_curva | dist. rejeição a R_reg / a R_curva | mais perto de | resultado |
|---|---|---|---|---|
| ctlN | 0,1167 / **0,0081** | 0,4098 / **0,0135** | R_curva nas duas | **o fator explica o desvio** |
| ctlP | **0,0039** / 0,1042 | **0,0161** / 0,3776 | R_reg nas duas | **o fator não explica** |

A previsão registrada ("D-N volta para a curva e D-P não") valeu. É uma repetição, descritivo. Camada e reconstrução
ao lado, sem critério: no ctlN a reconstrução cai em rejeição (0,849 contra 0,954 no R_reg); no ctlP as duas sobem
(0,997 e 0,998).

### Leitura estratificada (`python scripts/exp_resolucao/small_near_strata.py --set small_near_newrec --device cuda:2` → `results_exp_resolucao/small_near_newrec_strata.csv`, `.json`)

Segunda passada no teste do `small_near_newrec` com o modelo de crops de r1 e o limiar dele (registrado no D8). O
script refaz os passos do `evaluate` e confere: limiar 0,59941 igual ao do json, acerto das conhecidas 0,8932 e
rejeição 0,1200 iguais aos do json. Tamanho = lado maior da caixa inteira, terços em 22 e 31 px. Vizinha = o centro de
outra letra (anotada ou em volta da janela, das cenas refeitas das sementes; poeira não conta) a menos de D = 99,2 px;
43,2 % das letras do teste têm uma (distância mediana à mais próxima: 109,3 px).

| estrato | conhecidas | não vistas | aceitação das conhecidas | acerto das conhecidas | rejeição das não vistas | acerto em fechado |
|---|---|---|---|---|---|---|
| todas | 5129 | 1242 | 0,968 | 0,893 | 0,120 | 0,899 |
| pequenas (12–22 px) | 1714 | 464 | 0,924 | 0,713 | 0,129 | 0,727 |
| médias (22–31 px) | 1695 | 467 | 0,981 | 0,971 | 0,131 | 0,975 |
| grandes (31–56 px) | 1720 | 311 | 0,998 | 0,996 | 0,090 | 0,997 |
| com vizinha a menos de D | 2188 | 563 | 0,944 | 0,855 | 0,165 | 0,865 |
| sem vizinha | 2941 | 679 | 0,985 | 0,922 | 0,083 | 0,925 |
| pequenas, com vizinha | 755 | 229 | 0,868 | 0,632 | 0,210 | 0,654 |
| pequenas, sem vizinha | 959 | 235 | 0,968 | 0,777 | 0,051 | 0,784 |
| médias, com vizinha | 724 | 205 | 0,971 | 0,953 | 0,171 | 0,959 |
| médias, sem vizinha | 971 | 262 | 0,989 | 0,985 | 0,099 | 0,987 |
| grandes, com vizinha | 709 | 129 | 0,997 | 0,993 | 0,078 | 0,994 |
| grandes, sem vizinha | 1011 | 182 | 0,999 | 0,998 | 0,099 | 0,998 |

Em todos os estratos as não vistas são aceitas em ≥ 79 %. O que varia: o acerto das conhecidas cai nas letras
pequenas (0,713, contra 0,996 nas grandes) e mais nas pequenas com vizinha (0,632). A rejeição é maior com vizinha
(0,165 contra 0,083), onde o score todo é mais baixo (a aceitação das conhecidas também cai). Descritivo; não escolhe
nada.

## 2026-11-15, 17:00 — D13: Q4, os dois controles a cinco repetições (ANTES de qualquer treino ou leitura de teste)

Pré-registro: `CADERNO_CURVA.md`, Q4 (commit `273c558`). Roda: r2–r5 de `raw`, `prop`, `rec_z0` em `small_near_ctlN` e
`small_near_ctlP` (24 treinos e avaliações), `--no-aux`, `--threads 4`, pela fila do `phaseS.sh` (r1 pulado: modelo e
json existem), quatro filas em tmux (`res_S3_*`): ctlN r2–r3 (GPU 0), ctlP r2–r3 (GPU 1), ctlN r4–r5 e ctlP r4–r5
(GPU 2). Cada avaliação lê o teste uma vez, na fila. Tabela: `scripts/exp_resolucao/small_near_factors_five_reps.py` →
`results_exp_resolucao/small_near_factors_five_reps.csv` e `_reading.json` (a leitura do Q4: por repetição, R_reg(k) =
crops do `small_near_newrec` em k; R_curva(k) = crops da família u50 em k, interpolados em log(π D² σ) entre 15 e 69
na sobreposição do controle, com o código do Q2-S / Q3-D; "volta para a curva" se mais perto de R_curva(k) nas duas
métricas; ≥ 4 de 5 → explica; ≥ 4 de 5 mais perto de R_reg(k) nas duas → não explica; o resto inconclusivo). O
`small_near_factors.csv` (r1) fica como está.

## 2026-11-15, 17:15 — D14: Q4, os dois controles com cinco repetições (resultado)

Filas (`res_S3_*`, 17:00–17:14): 24 treinos novos, todos com 3000 passos (conferido no log); r1 pulado. Teste lido uma
vez por modelo. `python scripts/exp_resolucao/small_near_factors_five_reps.py` → `results_exp_resolucao/small_near_factors_five_reps.csv`,
`_reading.json` (o `small_near_factors.csv` de r1 ficou como estava).

| controle | rep | crops F1 / rej. | R_reg(k) | R_curva(k) | mais perto (F1; rej.) | prop F1 / rej. | rec_z0 F1 / rej. |
|---|---|---|---|---|---|---|---|
| ctlN | 1 | 0,916 / 0,530 | 0,799 / 0,120 | 0,908 / 0,516 | R_curva; R_curva | 0,976 / 0,990 | 0,961 / 0,849 |
| ctlN | 2 | 0,933 / 0,721 | 0,811 / 0,224 | 0,915 / 0,571 | R_curva; R_curva | 0,974 / 0,998 | 0,973 / 1,000 |
| ctlN | 3 | 0,923 / 0,590 | 0,802 / 0,152 | 0,909 / 0,501 | R_curva; R_curva | 0,958 / 0,825 | 0,976 / 0,960 |
| ctlN | 4 | 0,923 / 0,630 | 0,807 / 0,220 | 0,922 / 0,649 | R_curva; R_curva | 0,979 / 1,000 | 0,977 / 0,996 |
| ctlN | 5 | 0,929 / 0,657 | 0,810 / 0,242 | 0,923 / 0,656 | R_curva; R_curva | 0,975 / 1,000 | 0,979 / 0,999 |
| ctlN | média | **0,925 / 0,626** | 0,806 / 0,191 | 0,915 / 0,578 | | 0,972 / 0,963 | 0,973 / 0,961 |
| ctlP | 1 | 0,803 / 0,136 | 0,799 / 0,120 | 0,907 / 0,514 | R_reg; R_reg | 0,978 / 0,997 | 0,974 / 0,998 |
| ctlP | 2 | 0,812 / 0,218 | 0,811 / 0,224 | 0,915 / 0,568 | R_reg; R_reg | 0,970 / 1,000 | 0,971 / 1,000 |
| ctlP | 3 | 0,804 / 0,176 | 0,802 / 0,152 | 0,909 / 0,498 | R_reg; R_reg | 0,974 / 0,977 | 0,980 / 1,000 |
| ctlP | 4 | 0,822 / 0,316 | 0,807 / 0,220 | 0,921 / 0,646 | R_reg; R_reg | 0,974 / 1,000 | 0,967 / 0,980 |
| ctlP | 5 | 0,808 / 0,193 | 0,810 / 0,242 | 0,922 / 0,651 | R_reg; R_reg | 0,972 / 0,998 | 0,973 / 1,000 |
| ctlP | média | **0,810 / 0,208** | 0,806 / 0,191 | 0,915 / 0,575 | | 0,974 / 0,994 | 0,973 / 0,996 |

`small_near_newrec` (cinco repetições): camada 0,973 / 0,985, reconstrução 0,974 / 0,985.

**Leitura do Q4, aplicada mecanicamente:** ctlN volta para a curva em **5 de 5** → **a faixa de N_F explica o
desvio**; ctlP fica mais perto de R_reg em **5 de 5** → **a lei de profundidade não explica**. Distâncias médias:
ctlN F1 0,119 a R_reg contra 0,009 a R_curva, rejeição 0,434 contra 0,055; ctlP F1 0,005 contra 0,105, rejeição
0,038 contra 0,367. As duas previsões registradas valeram.

Ao lado, sem critério: a rejeição de 0,849 da reconstrução no ctlN em r1 não se repete (r2–r5: 0,960–1,000; média
0,961, mín. 0,849, máx. 1,000, contra 0,985 no `small_near_newrec`); a camada no ctlN teve r3 em 0,825 de rejeição
(média 0,963). No ctlP as duas rotas ficam em 0,994–0,996 de rejeição média.
