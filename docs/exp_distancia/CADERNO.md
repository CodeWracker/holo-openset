# Caderno de laboratório: distância, autofocus e focal stack

Protocolo: `docs/exp_distancia/PROTOCOLO.md`. Branch `exp/distancia-autofocus`, partindo de `9488fce` (main).
Todos os comandos rodam da raiz do repositório, depois de `source scripts/exp_distancia/env.sh`
(resultados em `results_exp_distancia/`, logs em `logs/exp_distancia/`, 4 threads por processo).

Máquina: DGX H100 compartilhada (6 × H100 80 GB via MPS, 224 CPUs). Horários em BRT (UTC−3).

---

## 2026-11-13 — Etapa 0: preparação e reprodução

### Ambiente

- Código: `9488fce`, árvore limpa. Ambiente do paper já instalado em `../.envbuild/holo-openset`
  (Python 3.11.18, PyTorch 2.5.1+cu121, o `requirements-lock.txt`); usei esse em vez de criar outro conda.
- Carga do servidor às 11:46: `load average 400.68, 398.14, 390.15`; as seis GPUs a 100 % de utilização e
  56–76 GB ocupados por outros usuários (MPS, sem reserva). **Não há GPU livre.** Isso não afeta acurácia, mas
  invalida medições de tempo em GPU (regra 8.1 do protocolo); ver "Timing de referência" abaixo.

### Desvios do protocolo nesta etapa

1. **`reproduce download` não funciona**: `holo_openset/reproduce.py` tem `ZENODO_RECORD = None` (o registro ainda
   não foi publicado). Usei os tars do registro que estão em `../.envbuild/zenodo/` (os mesmos que serão publicados),
   conferidos um a um contra `checksums/zenodo.sha256` (9/9 OK) e desempacotados em `data/` e `models/`, que é
   exatamente o que o `download` faz.
2. **`reproduce check` é 12/12, não 11/11**: hoje são 11 tabelas + `numbers.tex`. O texto do protocolo (e do
   README, "ten tables") está uma tabela atrasado.
3. **`reproduce check` depende do que está em `models/`**: a macro `\NModels` conta os `.pt` em disco. Com só
   `models/realistic` desempacotado deu 110 e o check falhou (11/12, `numbers.tex`); com os quatro conjuntos de
   modelos em disco (ou com nenhum) dá 240 e passa. Não é um problema dos resultados, mas quem desempacotar só
   parte do registro vê o check falhar.
4. `paper tables` (e portanto `reproduce check`) **regrava `results/data_summary.json`** quando o conjunto base
   está em disco, mesmo sendo só leitura em espírito. O conteúdo regravado é idêntico (`git status` limpo), mas é
   uma escrita em `results/` que o protocolo proíbe; fica registrado.

### Comandos

```bash
git checkout -b exp/distancia-autofocus                       # a partir de 9488fce
# tars locais do registro, conferidos contra checksums/zenodo.sha256 e desempacotados em data/ e models/
pytest -q                                                     # 11 passed
python -m holo_openset reproduce check                        # 12/12 files identical to expected/
python -m holo_openset reproduce verify-data                  # 10 files match, 0 differ, 64 not on disk
bash scripts/exp_distancia/etapa0_sanity.sh cuda:4            # tmux expdist; log em logs/exp_distancia/etapa0_sanity.log
```

O `etapa0_sanity.sh` rodou em `cuda:4` das 11:51 às 12:15 (load 377 no início, 365 no fim): simulou
`variants/session_5`, construiu os caches `rec_z0`/`rec_af` (e `autofocus.csv`) de `variants/session_5` e de
`realistic` com o código do paper e rodou o `robustness` dos quatro fluxos. Os números da Etapa 0 ficam guardados à
parte, para nunca se misturarem com os do estudo:

```bash
mkdir -p results_exp_distancia/etapa0 && cp results_exp_distancia/robustness.csv results_exp_distancia/etapa0/
```

### Reprodução da linha `session_5` (Tabela 10)

F1 aberto macro (`novel_open_macro_f1`), média de r1–r5, este run contra `results/robustness.csv` do paper
(comparação linha a linha com o script `etapa0_compare.py` do scratchpad, chaves rep, variant, flow):

| conjunto | fluxo | F1 (nosso) | F1 (paper) |
|---|---|---|---|
| base | prop | 0,9635 | 0,9635 |
| base | bank_jit | 0,9629 | 0,9629 |
| base | rec_z0 | 0,9641 | 0,9641 |
| base | rec_af | 0,9642 | 0,9642 |
| session_5 | prop | 0,7490 | 0,7489 |
| session_5 | bank_jit | 0,8387 | 0,8387 |
| session_5 | rec_z0 | 0,7526 | 0,7527 |
| session_5 | rec_af | 0,9636 | 0,9636 |

- 40 linhas (4 fluxos × 2 conjuntos × 5 repetições), todas presentes no CSV do paper. Maior diferença absoluta sobre
  todas as métricas e linhas: **0,0038** (`world5_new_class_acc`, r3, session_5, rec_af: 0,6628 contra 0,6667). Maior
  diferença de F1 numa linha: 0,00075; nas médias por fluxo, ≤ 1e-4. Critério do protocolo (0,01): **atendido**.
- 10 das 40 linhas são idênticas (< 1e-12): exatamente as de `prop` e `bank_jit` no base, que leem os hologramas do
  Zenodo (idênticos ao publicado). As linhas de `rec_z0`/`rec_af` no base diferem um pouco porque os caches
  `rec_*.npy` do base foram reconstruídos nesta máquina; as de `session_5` diferem porque o próprio conjunto foi
  regravado (ver verify-data abaixo). Diferença por linha (máximo sobre as métricas):

| conjunto | fluxo | r1 | r2 | r3 | r4 | r5 |
|---|---|---|---|---|---|---|
| base | bank_jit | 0 | 0 | 0 | 0 | 0 |
| base | prop | 0 | 0 | 0 | 0 | 0 |
| base | rec_af | 0,00127 | 0,00251 | 0,00128 | 0,00138 | 0 |
| base | rec_z0 | 0,00127 | 0 | 0,00128 | 0 | 0 |
| session_5 | bank_jit | 0,00127 | 0,00125 | 0,00128 | 0,00138 | 0,00020 |
| session_5 | prop | 0,00127 | 0,00079 | 0,00255 | 0,00138 | 0,00079 |
| session_5 | rec_af | 0,00254 | 0,00251 | 0,00383 | 0,00275 | 0,00129 |
| session_5 | rec_z0 | 0,00254 | 0,00251 | 0,00199 | 0,00138 | 0,00078 |

### verify-data

```bash
python -m holo_openset reproduce verify-data      # 10 files match, 2 differ, 62 not on disk
```

Diferem: `variants/session_5/holograms.npy` e `variants/session_5/backgrounds.npy`. **Esperado**: esses dois foram
regravados aqui (`simulate variant session_5`) e o `docs/REPRODUCIBILITY.md` diz que outro build de PyTorch/CUDA move
alguns pixels pelo arredondamento (0,02 % no base); mesmo assim o F1 bate com o paper (tabela acima). Os 10 arquivos
do conjunto base (hologramas, blank frames, anotações, metadados) batem com `checksums/data.sha256`.

### Timing de referência (configurações do paper)

Em `results_exp_distancia/etapa0/`, para não se misturar com a medição final do estudo (E5). Um de cada vez, em tmux,
com `uptime` e `nvidia-smi` antes e depois (logs `logs/exp_distancia/etapa0_timing_{gpu,cpu}.log`):

```bash
HOLO_RESULTS=$PWD/results_exp_distancia/etapa0 python -m holo_openset experiment timing --device cuda:1 --rep 1
HOLO_RESULTS=$PWD/results_exp_distancia/etapa0 python -m holo_openset experiment timing --device cpu --rep 1 --sizes 640x640
```

- GPU: `cuda:1` (a de mais memória livre), 16:46–16:50. Antes: load 255,7 (1 min; 383,8 / 425,8 em 5 e 15 min), GPUs
  0–5 com 81,1 / 65,2 / 65,3 / 68,6 / 65,7 / 69,6 GB e 96–100 % de utilização. Depois: load 82,6; 79,0 / 53,6 / 65,3 /
  68,6 / 66,1 / 69,6 GB, 97–100 %.
- CPU: um core (`--threads 1`, `process_time`), 16:50–16:51. Load 82,9 no início e 93,2 no fim.

Razão nosso/paper por estágio (GPU: chave `min_s`; CPU: chave `median_s`; tempos em ms):

| estágio | GPU 640 nosso | GPU 640 paper | razão | GPU quadro inteiro nosso | paper | razão | CPU 640 nosso | CPU 640 paper | razão |
|---|---|---|---|---|---|---|---|---|---|
| flat_field | 7,05 | 0,055 | 127,6 | 8,10 | 0,180 | 45,0 | 0,68 | 1,17 | 0,58 |
| layer_real | 7,44 | 0,169 | 44,1 | 7,78 | 0,567 | 13,7 | 2,45 | 5,55 | 0,44 |
| layer_complex | 8,28 | 0,250 | 33,2 | 9,54 | 1,084 | 8,8 | 5,53 | 11,74 | 0,47 |
| layer_prop | 6,40 | 0,284 | 22,6 | 8,71 | 1,103 | 7,9 | 5,60 | 9,70 | 0,58 |
| layer_bank | 4,98 | 0,293 | 17,0 | 19,44 | 3,531 | 5,5 | 32,9 | 53,3 | 0,62 |
| layer_bank_jit | 6,81 | 0,370 | 18,4 | 21,82 | 3,662 | 6,0 | 36,8 | — | — |
| layer_bank_w1 | 6,56 | 0,308 | 21,3 | 32,05 | 4,814 | 6,7 | 64,9 | 86,0 | 0,75 |
| layer_bank_w3 | 5,67 | 0,307 | 18,4 | 34,43 | 4,758 | 7,2 | 58,8 | 125,9 | 0,47 |
| backprop | 12,52 | 0,166 | 75,2 | 21,20 | 0,976 | 21,7 | 10,2 | 22,0 | 0,47 |
| autofocus | 42,9 | 4,89 | 8,8 | 758,3 | 123,7 | 6,1 | 4072 | 7423 | 0,55 |
| per_object | 20,7 | 1,75 | 11,8 | 249,0 | 48,2 | 5,2 | 834 | 1492 | 0,56 |
| twin | 42,9 | 8,53 | 5,0 | 449,5 | 85,8 | 5,2 | 749 | 1632 | 0,46 |
| channels | 8,47 | 0,689 | 12,3 | 10,05 | 1,786 | 5,6 | 19,6 | 41,8 | 0,47 |
| yolo_tiled | 104,8 | 13,0 | 8,1 | 2532 | 221,7 | 11,4 | 424 | 1331 | 0,32 |
| embed | 19,0 | 2,24 | 8,5 | 31,0 | 2,44 | 12,7 | 96,6 | 170,2 | 0,57 |
| decide | 9,60 | 0,100 | 96,3 | 8,66 | 0,118 | 73,4 | 0,07 | 0,16 | 0,45 |

O `timing_cpu.csv` do paper não tem `layer_bank_jit` (o modelo foi cronometrado depois, em outro run).

Razões entre estágios que importam para o estudo (estágio / backprop), nosso contra paper:

| razão | GPU 640 nosso | paper | GPU quadro inteiro nosso | paper | CPU 640 nosso | paper |
|---|---|---|---|---|---|---|
| autofocus / backprop | 3,43 | 29,4 | 35,8 | 126,7 | 397 | 338 |
| layer_bank / backprop | 0,40 | 1,76 | 0,92 | 3,62 | 3,21 | 2,43 |
| layer_bank_jit / backprop | 0,54 | 2,23 | 1,03 | 3,75 | 3,59 | — |
| layer_prop / backprop | 0,51 | 1,70 | 0,41 | 1,13 | 0,55 | 0,44 |
| yolo_tiled / backprop | 8,37 | 77,9 | 119,5 | 227,1 | 41,4 | 60,6 |
| twin / backprop | 3,43 | 51,3 | 21,2 | 87,9 | 73,1 | 74,3 |

**Veredito, regra 8.1: o run em GPU não vale.** É o caso descrito no REPRODUCIBILITY.md: na GPU saturada (MPS, 100 %
de outros usuários) toda chamada sincronizada custa 5–20 ms, qualquer que seja o tamanho. Evidências: `flat_field`
custa 7,1 ms a 640 × 640 e 8,1 ms no quadro inteiro (paper: 0,055 → 0,180 ms); `decide` (uma multiplicação 5k × 128)
custa 6–10 ms em todo tamanho (paper 0,1 ms); o `backprop` cresce só 1,69× de 640 × 640 ao quadro inteiro (paper
5,86×; área 25,8×); o autofocus, 114 reconstruções numa chamada, sai a 0,38 ms por reconstrução a 640 × 640, menos que
um único `backprop` (12,5 ms). As razões entre estágios em GPU ficam 2–14× menores que as do paper, porque a latência
fixa por chamada domina. Não repeti: a medição de tempo em GPU fica para a E5, numa GPU ociosa.

**CPU: plausível.** Todos os estágios custam 0,32–0,75 do tempo do paper (CPU mais rápida ou menos disputada; mediana
da razão ≈ 0,5), e as razões entre estágios ficam perto das do paper: autofocus/backprop 397 contra 338 (1,18×),
twin/backprop 73 contra 74, layer_prop/backprop 0,55 contra 0,44, layer_bank/backprop 3,2 contra 2,4. A maior
discrepância é o YOLO (0,32×, razão para o backprop 41 contra 61). Só 640 × 640 foi medido em CPU (o quadro inteiro
leva horas; fica para a E5).

### Checkpoint 0

- Ambiente do paper, `pytest` 11/11, `reproduce check` 12/12, `verify-data` 10 OK e 2 diferenças esperadas
  (`variants/session_5`, regravado nesta máquina).
- Reprodução da linha `session_5`: F1 de prop, bank_jit, rec_z0, rec_af = 0,7490 / 0,8387 / 0,7526 / 0,9636 (paper
  0,7489 / 0,8387 / 0,7527 / 0,9636); base 0,96 nos quatro. Maior diferença de qualquer métrica em qualquer linha:
  0,0038. **Reproduz o paper.**
- Timing de referência: CPU com razões entre estágios próximas às do paper (custo absoluto ≈ 0,5×); GPU **inválido**
  pela regra 8.1 (GPU saturada, custo fixo por chamada). Carga do servidor: load 83–430, seis GPUs a 96–100 %.
- Resultados: `results_exp_distancia/etapa0/{robustness,timing_gpu,timing_cpu}.csv`.
