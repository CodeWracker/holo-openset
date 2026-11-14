# Caderno da integração no paper: os runs (item B1 de `docs/exp_distancia/TODO.md`)

Agente "integração-runs". Runs declarados antes de rodar em `CADERNO.md`, entrada "2026-11-14 — Depois da revisão do
orientador". Branch `exp/distancia-autofocus` (só local). Todos os comandos da raiz do repositório, depois de

```bash
source scripts/exp_distancia/env.sh; unset HOLO_RESULTS; export HOLO_LOGS=$PWD/logs/integracao
python -c "from holo_openset import paths; print(paths.RESULTS)"    # .../holo-openset/results
```

(4 threads por processo; resultados em `results/`, logs em `logs/integracao/`). Rascunho e cópias de segurança em
`/home/jovyan/privado/.persist/.cache/tmp/claude-1000/-home-jovyan-compartilhado-ralph-openset-microscopy/2460bd2f-62a2-4eb8-bda4-b04332eeb593/scratchpad/integracao/`
(abaixo: `$S`). Horários em BRT. GPUs 0–4 (a 5 é do agente "análise").

---

## 2026-11-14 — Preparação (09:00–09:20)

### Estado de partida

- `git status --short` limpo (inclusive `results/`); HEAD `395e2ed`.
- `data/variants/`: `beam_narrow frame_2 frame_5 fullwell_500 session_2 session_5 walk_05` (6,8 GB cada, 800 imagens
  de teste). Faltam 28 das 32 variantes de `VARIANTS` (as 4 presentes são `beam_narrow fullwell_500 session_2
  session_5`; `frame_2 frame_5 walk_05` são do `STUDY`).
- Carga às 09:10: load 6,2; 1 thread pronta; GPUs 0–2 ociosas (3–5 GB de outros), 3 e 5 a 98 %, 4 a 3 %.

### O que a leitura do código mostrou (antes de rodar)

1. **`build_caches` com métodos do paper (`z0 af edf twin`) sempre reescreve `autofocus.csv`** e não pula nada que
   exista; com `--methods z0` sozinho grava `autofocus.csv` com `z_af = z0`. Os métodos de `FOCUS` (`afc`) só
   escrevem `rec_afc.npy` e `autofocus_afc.csv`. Para não sobrescrever nenhum `autofocus.csv` existente (regra), os
   caches `edf`/`twin` e o `z0` de conferência são construídos com o mesmo comando do pacote, mas com `--set`
   apontando para um diretório de preparo (`data/_integ_staging/<conjunto>`, links simbólicos para `holograms.npy`,
   `backgrounds.npy`, `metadata.csv`, `annotations.csv`, `physics.json`, `sessions.csv`, `dust.csv`); depois só os
   `rec_*.npy` novos são movidos para o conjunto, e o `autofocus.csv` do preparo é comparado com o do conjunto.
2. **O conjunto base não tem mais `rec_edf.npy` nem `rec_twin.npy`** (`data/realistic` só tem `rec_z0`, `rec_af` e os
   caches do estudo). A galeria (janelas de validação do base) de `rec_edf` e `rec_twin` em `robustness` (passo 3b) e
   em `full_frames` (passo 6) lê esses caches: sem eles os dois fluxos não rodam. Eles serão reconstruídos no base,
   com o mesmo comando (`reconstruct --set realistic --methods edf twin`, via preparo), e são caches novos deste
   build: não são os bytes usados no paper.
3. **`experiments/oracle.py` rotula as variantes com `VARIANTS.get(v, ('base', 'base', {}))`**: em `frame_2`,
   `frame_5`, `walk_05` gravaria `effect = value = 'base'`. `robustness.py` usa `ALL`. Correção mínima proposta:
   `ALL` no lugar de `VARIANTS` nessa busca (o padrão de `--variants` não muda).
4. **`save()` (`experiments/common.py`) relê o csv com `pd.read_csv` (parser padrão, não `round_trip`) e o regrava
   inteiro.** Conferido numa cópia: reler e regravar os csv atuais muda o último dígito (1 ULP, ~1e-16) de floats nas
   linhas que o último `save` escreveu direto da memória (33 linhas em `robustness.csv`, 10 em `oracle.csv`, 2 em
   `e2e.csv`, 6 em `full_frames.csv`; `full_frames_time.csv` é estável). Isso vai acontecer em cada run; a
   conferência "linhas antigas inalteradas" é feita byte a byte e, onde não bater, com a diferença numérica máxima.
5. `full_frames` salva os tempos com chaves `rep, flow, frame, stage`; a detecção é gravada com `flow = 'all'` e é
   substituída pelo run novo. Os tempos de `bank` e `bank_w3` (que não estão no run novo) ficam, mas passam a
   conviver com uma detecção de outro run. Com `rec_afc` (fora de `PAPER_FLOWS`) o run também grava
   `results/full_frames_focus.csv` (arquivo novo).

### Correção mínima no pacote: rótulos do oráculo nos conjuntos do estudo

`holo_openset/experiments/oracle.py`: `effect, value` passam a vir de `ALL.get(v, ...)` (como em `robustness.py`) em vez
de `VARIANTS.get(v, ...)`. Sem isso, o passo 4 (oráculo em `frame_2`, `frame_5`, `walk_05`) gravaria
`effect = value = 'base'` nessas linhas. Nada mais muda (o padrão de `--variants` continua `base` + `VARIANTS`; as
linhas da bateria saem iguais). `pytest` rodado no fim (abaixo).

## 2026-11-14 — Passo 1: simulação das 28 variantes que faltavam (split de teste)

Comando da fila do paper (`pipeline.jobs()`: `simulate variants --workers 16`), restrito aos nomes que faltam e com
8 workers (o número de workers não muda as cenas: cada cena tem seu próprio gerador, `sim/generate.py`), na GPU 0,
um conjunto depois do outro, pelo script `scripts/exp_distancia/integ_sim.sh` (pula o que tem `physics.json`):

```bash
# tmux integ_sim, cuda:0 (log logs/integracao/sim_first.log): a primeira unidade, medida sozinha
bash scripts/exp_distancia/integ_sim.sh cuda:0 8 pinhole_200
# tmux integ_sim2, cuda:0 (log logs/integracao/sim_rest.log): as outras 27
bash scripts/exp_distancia/integ_sim.sh cuda:0 8 transparent read_60 fullwell_1500 fullwell_24000 read_10 read_30 \
  bits_6 bits_4 beam_flat laser band_0 band_20 band_40 pinhole_20 pinhole_50 source_5cm dust_0 dust_8 dust_20 opaque \
  absorbing depth_0 depth_150 depth_300 session_0 no_outside periodic
```

- `pinhole_200`: 09:12:16 → 09:12:59 (43 s; GPU 0 ociosa, load 9). Estimativa inicial: 27 × 45 s ≈ 20 min.
- Às 09:15 outros usuários passaram a ocupar todas as GPUs a 98–100 % (MPS); `fullwell_1500` levou 2 min 26 s.
  Estimativa revista: 2–3 min por conjunto, ≈ 1 h para as 27.

## 2026-11-14, 09:25 — Passo 7: arquivos de tempo do paper (decisão D4)

```bash
# cópias antigas guardadas antes em $S/backup0/timing_{gpu,cpu}.csv
cp results_exp_distancia/e5/timing_gpu.csv results/timing_gpu.csv    # = e5_a2/timing_gpu.csv (tentativa 2), cmp idêntico
cp results_exp_distancia/e5/timing_cpu.csv results/timing_cpu.csv
```

sha256 antigos: gpu `2316b228…`, cpu `bea5dff6…`; novos: gpu `d0593a3f…`, cpu `ccfd4009…`. Mesmo cabeçalho; os
novos têm 84 linhas (antes 64 em GPU, 60 em CPU): ganham `autofocus_afc`, `autofocus_afr`, `per_object_wide`,
`layer_bank_w2`, `layer_bank_wide` e, em CPU, `layer_bank_jit`.

Principais estágios, antigo → novo, em ms (GPU: `min_s`; CPU: `median_s`, um núcleo):

| estágio | GPU 640² | GPU quadro inteiro | CPU 640² | CPU quadro inteiro |
|---|---|---|---|---|
| flat_field | 0,055 → 0,030 | 0,180 → 0,178 | 1,17 → 0,62 | 375 → 112 |
| backprop | 0,166 → 0,090 | 0,976 → 0,970 | 22,0 → 6,9 | 2195 → 1008 |
| autofocus (cego) | 4,89 → 4,81 | 123,7 → 122,9 | 7423 → 3583 | 238 728 → 116 440 |
| autofocus_afc (novo) | — → 0,511 | — → 1,577 | — → 13,1 | — → 1045 |
| per_object | 1,75 → 1,60 | 48,2 → 45,5 | 1492 → 705 | 51 017 → 24 979 |
| twin | 8,53 → 5,78 | 85,8 → 85,3 | 1632 → 611 | 198 166 → 85 875 |
| channels | 0,689 → 0,473 | 1,79 → 1,78 | 41,8 → 18,0 | 3160 → 1192 |
| layer_real | 0,169 → 0,087 | 0,567 → 0,567 | 5,5 → 2,1 | 825 → 293 |
| layer_complex | 0,250 → 0,127 | 1,08 → 1,09 | 11,7 → 4,2 | 1780 → 914 |
| layer_prop | 0,284 → 0,132 | 1,10 → 1,10 | 9,7 → 4,2 | 1758 → 779 |
| layer_bank_jit | 0,370 → 0,186 | 3,66 → 3,52 | — → 25,2 | — → 2419 |
| yolo_tiled | 13,0 → 8,1 | 221,7 → 166,8 | 1331 → 321 | 52 787 → 21 374 |
| embed | 2,24 → 1,51 | 2,44 → 2,35 | 170 → 61 | 2037 → 685 |
| decide | 0,100 → 0,070 | 0,118 → 0,092 | 0,16 → 0,18 | 7,8 → 0,29 |

Em GPU o quadro inteiro quase não muda (exceto YOLO, 0,75×); a 640² tudo fica ≈ 0,5–0,7× (custo fixo de lançamento
menor numa GPU menos disputada). Em CPU tudo fica ≈ 0,3–0,5× (load 59–89 em vez de ≈ 230).

**`results/timing_cpu_layers.csv` e `results/timing_gpu_layers.csv`:** nenhum módulo do pacote, teste, script ou doc
os lê (`grep -rn _layers` no repositório: nenhuma ocorrência fora deles). Vêm da exploração de 2026-11-01:
`timing_cpu_layers.csv` do commit `83cbb9b` ("one CPU core, the new layers next to the old ones and one
back-propagation, in one run") e `timing_gpu_layers.csv` do `c581d87` ("the new layers and the full frames of prop,
bank and bank_w3 timed on an idle GPU"). Não foram mexidos.

## 2026-11-14, 09:26–09:37 — Passo 1 (cont.) e passo 2 (primeiros caches)

### Simulação: mudança para 1 worker

`fullwell_24000` levou 7 min 31 s (09:17:07 → 09:24:38) com 8 workers: o gargalo é o processo principal (100 % de
CPU esperando a GPU 0, que outros usuários ocupam a 100 %), não os workers (3,5 % de CPU cada). Para caber no limite de
3 processos com outro job ao lado, parei a sessão (`tmux kill-session -t integ_sim2`, às 09:26, durante `read_10`, que
ficou sem `physics.json` e é regravado do zero) e retomei com 1 worker (o número de workers não muda as cenas):

```bash
# tmux integ_sim3, cuda:0 (log logs/integracao/sim_rest2.log), desde 09:26:53
bash scripts/exp_distancia/integ_sim.sh cuda:0 1 read_10 read_30 bits_6 bits_4 beam_flat laser band_0 band_20 band_40 \
  pinhole_20 pinhole_50 source_5cm dust_0 dust_8 dust_20 opaque absorbing depth_0 depth_150 depth_300 session_0 \
  no_outside periodic
```

Prontos até aqui: `pinhole_200`, `transparent`, `read_60`, `fullwell_1500`, `fullwell_24000` (5 de 28). `read_10`
anda a ≈ 250 imagens a cada 7 min com a GPU 0 disputada (≈ 20 min por conjunto: estimativa de 7 h para os 23 que
faltam se a disputa continuar).

### Caches `rec_edf`, `rec_twin` do conjunto base (galerias)

```bash
# tmux integ_cache_base, cuda:1, 09:28:00 -> 09:31 (log logs/integracao/cache_realistic_edf_twin.log)
bash scripts/exp_distancia/integ_caches.sh cuda:1 realistic edf twin
#  = python -m holo_openset reconstruct --set _integ_staging/realistic --methods edf twin --device cuda:1
```

5000 imagens em ≈ 3 min. O script parou no fim por dois defeitos dele (não do pacote): comparou o `autofocus.csv` byte
a byte (o do preparo tem a coluna a mais `z_objects`, que o `edf` acrescenta) e montou mal o nome da cópia do log. Os
dados estavam certos; terminei à mão o que o script faria: `z_af`, `true_z`, `n_reconstructions` e `image_id` do
`autofocus.csv` do preparo **idênticos** aos de `data/realistic/autofocus.csv` nas 5000 imagens (diferença máxima de
`z_af` 0); cópia em `logs/integracao/staging_autofocus/realistic_edf_twin.csv`; `rec_edf.npy` e `rec_twin.npy`
(6,1 GB cada) movidos para `data/realistic/` (não existiam); preparo apagado. O script foi corrigido (compara as
colunas comuns em Python).

### Fila A de caches (cuda:1, 09:32:29 → 09:36:25, log `logs/integracao/cache_queue_a.log`, script `logs/integracao/queue_a.sh`)

```bash
bash scripts/exp_distancia/integ_caches.sh cuda:1 variants/<frame_2|frame_5|walk_05> edf twin   # via preparo
bash scripts/exp_distancia/integ_caches.sh cuda:1 variants/<pinhole_200|transparent|read_60> afc z0   # afc no conjunto, z0 via preparo
bash scripts/exp_distancia/integ_caches.sh cuda:1 variants/<fullwell_1500|fullwell_24000> afc
```

- `frame_2`, `frame_5`, `walk_05`: `rec_edf.npy`, `rec_twin.npy` novos (≈ 40 s por conjunto); o `autofocus.csv` do
  preparo é idêntico ao do conjunto nos três (diferença máxima de `z_af` 0).
- `rec_afc.npy` + `autofocus_afc.csv` em `pinhole_200`, `transparent`, `read_60`, `fullwell_1500`, `fullwell_24000`
  (≈ 15 s cada).
- `rec_z0.npy` em `pinhole_200`, `transparent`, `read_60` (para a conferência da re-simulação); o `autofocus.csv`
  só-z0 (com `z_af = z0`) ficou fora dos conjuntos, em `logs/integracao/staging_autofocus/`.

### Conferência da re-simulação (`rec_z0`, 5 repetições, resultados em `$S/sanity/`)

```bash
# tmux integ_sanity, cuda:1, 09:36:47 -> 09:37:16 (log logs/integracao/sanity_rec_z0.log)
RESULTS=$S/sanity bash scripts/exp_distancia/integ_run.sh experiment robustness --device cuda:1 --flows rec_z0 \
  --variants pinhole_200 transparent read_60
```

F1 aberto macro por repetição, paper (`results/robustness.csv`) → re-simulado:

| conjunto | r1 | r2 | r3 | r4 | r5 | média |
|---|---|---|---|---|---|---|
| pinhole_200 | 0,8906 → 0,8907 | 0,8921 → 0,8919 | 0,9142 → 0,9141 | 0,8962 → 0,8961 | 0,9046 → 0,9057 | 0,8996 → 0,8997 |
| transparent | 0,8923 → 0,8923 | 0,9097 → 0,9099 | 0,9106 → 0,9104 | 0,9095 → 0,9089 | 0,9056 → 0,9058 | 0,9055 → 0,9055 |
| read_60 | 0,9517 → 0,9516 | 0,9677 → 0,9678 | 0,9644 → 0,9644 | 0,9661 → 0,9663 | 0,9644 → 0,9644 | 0,9629 → 0,9629 |

Maior |diferença| de F1: 0,0010 (`pinhole_200`, r5); AUROC 0,0001; acerto dos vistos 0,0014; rejeição 0,0025;
`worldall_new_class_acc` 0,0026. Dentro dos ≈ 0,005 esperados para diferenças de arredondamento entre builds: a
re-simulação reproduz os conjuntos do paper (não bit a bit). Segue.

## 2026-11-14, 09:37–09:43 — Passo 3b: fluxos do paper em `frame_2`, `frame_5`, `walk_05` (em `results/`)

```bash
cp -p results/robustness.csv $S/before_3b/
# tmux integ_rob3b, cuda:1, 09:37:48 -> 09:42:09 (log logs/integracao/robustness_3b.log)
bash scripts/exp_distancia/integ_run.sh experiment robustness --device cuda:1 \
  --flows raw learned complex wiener prop bank_jit rec_z0 rec_af rec_afc rec_edf rec_twin --variants frame_2 frame_5 walk_05
python scripts/exp_distancia/integ_check.py $S/before_3b/robustness.csv results/robustness.csv --keys rep variant flow \
  --intended "variant in ['frame_2','frame_5','walk_05']"
python scripts/exp_distancia/integ_coincide.py frame_2 frame_5 walk_05
```

- 4 min 21 s, saída 0, nenhum `missing`. `robustness.csv`: 2278 → 2443 linhas (+165 = 11 fluxos × 3 conjuntos × 5
  repetições, todas novas). Nenhuma chave antiga sumiu; das 2278 linhas antigas, 2245 textualmente idênticas e 33
  (as de `bank_jit` r5, as últimas gravadas antes) com diferença de 1 ULP (máx. 1,1e-16), o efeito do `save` descrito
  na preparação.
- `effect` vem de `ALL` (`distance per frame (%)`, `distance drift per frame (%)`). **`value` saiu `2.0`, `5.0`, `0.5`**
  (no `results_exp_distancia/` está `2`, `5`, `0.5`): o lote deste run só tem esses três conjuntos, então o pandas
  faz a coluna `value` float. É só formatação (nenhum gerador de `holo_openset/paper` lê a coluna `value`); não mexi.
- **Coincidência com o estudo** (`rec_z0, rec_af, rec_afc, prop, bank_jit` × 3 conjuntos × 5 repetições = 75 linhas
  comuns): maior |diferença| **0** em todas as 10 métricas.

F1 aberto macro, média de 5 repetições (com `base`, `session_2`, `session_5` de `results/robustness.csv` ao lado):

| conjunto | raw | learned | complex | wiener | prop | bank_jit | rec_z0 | rec_af | rec_afc | rec_edf | rec_twin |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 0,781 | 0,928 | 0,934 | 0,910 | 0,963 | 0,963 | 0,964 | 0,964 | (3a) | 0,964 | 0,963 |
| session_2 | 0,780 | 0,913 | 0,922 | 0,880 | 0,939 | 0,957 | 0,939 | 0,964 | (3a) | 0,964 | 0,964 |
| session_5 | 0,782 | 0,835 | 0,850 | 0,737 | 0,749 | 0,839 | 0,753 | 0,964 | (3a) | 0,964 | 0,963 |
| frame_2 | 0,780 | 0,921 | 0,929 | 0,889 | 0,954 | 0,961 | 0,955 | 0,964 | 0,965 | 0,964 | 0,964 |
| frame_5 | 0,781 | 0,886 | 0,896 | 0,814 | 0,865 | 0,924 | 0,865 | 0,964 | 0,964 | 0,964 | 0,963 |
| walk_05 | 0,779 | 0,911 | 0,920 | 0,869 | 0,930 | 0,953 | 0,934 | 0,964 | 0,965 | 0,965 | 0,964 |

## 2026-11-14, 09:43–09:55 — Passo 5: avaliação principal e fim a fim de `rec_afc` no base

### Avaliação principal (`results/eval/realistic/rec_afc_r{1..5}.json`)

```bash
# tmux integ_eval, cuda:1, 09:43:21 -> 09:43:47 (log logs/integracao/eval_rec_afc.log); comando de pipeline.jobs()
bash scripts/exp_distancia/integ_run.sh evaluate --flow rec_afc --rep 1 2 3 4 5 --device cuda:1
```

Cinco JSON novos, `flow = rec_afc`, `set = train_set = realistic`, `tag = ''`, com exatamente as mesmas chaves dos de
`rec_af` (inclusive as 12 `world{5,20,all}_*` de enrollment). Modelo: o de `rec_af` (`flows.weights_of`). F1 aberto
macro `rec_afc` (`rec_af`): r1 0,9567 (0,9559), r2 0,9705 (0,9705), r3 0,9643 (0,9633), r4 0,9622 (0,9636),
r5 0,9673 (0,9674).

### Conferência do detector re-executado (fim a fim de `rec_af` num diretório de rascunho)

`data/realistic/dets_yolo_r{r}.csv` (as detecções do YOLO que o `e2e` guarda) não existiam mais: o `e2e` as refaz e
grava (arquivos novos no conjunto). Como os fluxos já em `results/e2e.csv` usaram as detecções do run do paper,
conferi antes o efeito de refazê-las, com o fluxo `rec_af` num diretório de rascunho (fora de `results/`):

```bash
# tmux integ_e2e_s, cuda:1, 09:44 -> 09:50 (log logs/integracao/e2e_sanity_rec_af.log)
RESULTS=$S/e2e_sanity bash scripts/exp_distancia/integ_run.sh experiment e2e --device cuda:1 --flows rec_af
```

Paper → refeito, por repetição: recall do detector idêntico nas 5; falsos positivos 42 → 41 em r1, iguais nas outras
4; F1 aberto 0,9526 → 0,9525, 0,9672 → 0,9672, 0,9551 → 0,9552, 0,9614 → 0,9614, 0,9669 → 0,9668; AUROC idêntica a 4
casas; rejeição: 0,8220 → 0,8212 (r1), 0,8263 → 0,8255 (r3), iguais nas outras; `worldall_new_class_acc` 0,8886 →
0,8899 (r3). Ou seja, o YOLO re-executado neste build dá praticamente as mesmas caixas (uma detecção falsa a menos em
r1); as linhas novas de `e2e.csv` (abaixo) usam essas detecções novas, as antigas as do paper.

### Fim a fim de `rec_afc` e `bank_jit` (em `results/e2e.csv`)

`results/e2e.csv` não tinha `bank_jit` (só `bank_w3`); o `e2e` aceita `bank_jit` sem nada especial (modelo próprio,
imagens = hologramas), então rodou junto, 5 repetições.

```bash
cp -p results/e2e.csv $S/before_e2e/
# tmux integ_e2e, cuda:1, 09:52:34 -> 09:53:15 (log logs/integracao/e2e_rec_afc_bank_jit.log)
bash scripts/exp_distancia/integ_run.sh experiment e2e --device cuda:1 --flows rec_afc bank_jit
python scripts/exp_distancia/integ_check.py $S/before_e2e/e2e.csv results/e2e.csv --keys rep flow \
  --intended "flow in ['rec_afc','bank_jit']"
```

41 s (as detecções já estavam gravadas). `e2e.csv`: 50 → 60 linhas (+10 novas); nenhuma chave antiga sumiu; 48 das
50 antigas idênticas, 2 (`prop` e `bank_w3` r5) com 1 ULP. Médias de 5 repetições (F1 aberto macro / AUROC /
rejeição das falsas detecções / `worldall_new_class_acc`): `rec_afc` 0,9602 / 0,9772 / 0,7737 / 0,9231;
`bank_jit` 0,9600 / 0,9790 / 0,7812 / 0,9342 (para comparação, do paper: `rec_af` 0,9606 / 0,9775 / 0,7844 / 0,9238;
`rec_z0` 0,9608; `prop` 0,9604; `bank_w3` 0,9566). Recall do detector 0,9954 em todos (as detecções novas têm o mesmo
recall das antigas).

## 2026-11-14, 09:26–10:52 — Passos 1 e 2 concluídos

- **Simulação** (`integ_sim3`, cuda:0, 1 worker): as 23 restantes terminaram às 10:51:49, saída 0. Tempo por conjunto
  (início → início do seguinte): `read_10` 11,6 min, `read_30` 11,2, `bits_6` 14,6, `bits_4` 6,5, `beam_flat` 4,4,
  `laser` 2,8; daí em diante 2–4 min cada (a disputa da GPU 0 caiu), `no_outside` 28 s e `periodic` 12 s (sem objetos
  fora do sensor). Total do passo 1: 09:12 → 10:52 (≈ 1 h 40 min). Agora os 32 conjuntos de `VARIANTS` estão em
  `data/variants/` (90 GB no total do diretório, contando os caches).
- **`rec_afc` nos conjuntos novos**: `scripts/exp_distancia/integ_afc_follow.sh cuda:1` (tmux `integ_afc`, log
  `logs/integracao/cache_afc_follow.log`, 09:53:45 → 10:52:13) construiu `rec_afc.npy` + `autofocus_afc.csv` de cada
  conjunto assim que o `physics.json` dele aparecia (23 conjuntos, ≈ 15–35 s cada, nenhum erro). Com a fila A,
  os 28 conjuntos novos têm `rec_afc`; os 4 da bateria que o estudo já tinha (`beam_narrow`, `fullwell_500`,
  `session_2`, `session_5`) e o base já tinham.

## 2026-11-14, 10:52–10:56 — Passo 3a: `rec_afc` no base e nas 32 variantes (em `results/`)

```bash
cp -p results/robustness.csv $S/before_3a/
# tmux integ_rob3a, cuda:1, 10:52:37 -> 10:56:18 (log logs/integracao/robustness_3a.log)
bash scripts/exp_distancia/integ_run.sh experiment robustness --device cuda:1 --flows rec_afc --variants base <as 32 de VARIANTS>
python scripts/exp_distancia/integ_check.py $S/before_3a/robustness.csv results/robustness.csv --keys rep variant flow --intended "flow == 'rec_afc'"
python scripts/exp_distancia/integ_coincide.py
```

- 3 min 41 s, saída 0, nenhum `missing`. 2443 → 2608 linhas (+165 = 33 conjuntos × 5 repetições, todas novas; as 15
  linhas de `rec_afc` de `frame_*`/`walk_05` do passo 3b não foram recalculadas, só regravadas pelo `save`).
  Nenhuma chave antiga sumiu; 2400 das 2428 linhas que não são de `rec_afc` idênticas, 28 (as de r5 de 3b) com 1 ULP.
- **Coincidência com `results_exp_distancia/robustness.csv`** (250 linhas com a mesma chave):
  - as **100 linhas escritas nesta integração** (`rec_afc` no base, `session_2`, `session_5`, `fullwell_500`,
    `beam_narrow`, `frame_2`, `frame_5`, `walk_05`: 40; `rec_z0`, `rec_af`, `prop`, `bank_jit` nos três
    conjuntos novos: 60) coincidem: maior |diferença| em todas as métricas **1,1e-16** (ruído de float da regravação);
  - as **150 linhas antigas do paper** com a mesma chave (`rec_z0`, `rec_af`, `prop`, `bank_jit`, `bank_w2`,
    `bank_wide` no base e nos 4 conjuntos da bateria que o estudo re-simulou) **não** são o mesmo cálculo: o paper
    usou os conjuntos e caches originais, o estudo os re-simulados/reconstruídos neste build. Diferença máxima de F1
    0,0023 (`beam_narrow`; base 0,0001, `fullwell_500` 0,0010, `session_2` 0,0004, `session_5` 0,0008), média
    0,00014; em todas as métricas 0,0055 (`world5_new_class_acc`). Mesma ordem da conferência do passo 1.
  - Consequência para a Tabela 10: a coluna `rec_afc` vem dos conjuntos deste build, as outras colunas das 32 linhas
    da bateria vêm dos conjuntos do paper (diferenças de arredondamento ≤ 0,001–0,002 de F1, ver passo 1).

F1 aberto macro, média de 5 repetições (`rec_z0`, `rec_af` de `results/robustness.csv`; `rec_afc` deste run):

| conjunto | rec_z0 | rec_af | rec_afc | afc − af | afc − z0 |
|---|---|---|---|---|---|
| base | 0,964 | 0,964 | 0,964 | +0,000 | +0,000 |
| fullwell_500 | 0,950 | 0,771 | 0,949 | +0,178 | -0,001 |
| fullwell_1500 | 0,961 | 0,959 | 0,961 | +0,002 | -0,000 |
| fullwell_24000 | 0,963 | 0,964 | 0,964 | +0,000 | +0,001 |
| read_10 | 0,964 | 0,964 | 0,964 | -0,000 | -0,000 |
| read_30 | 0,964 | 0,964 | 0,964 | +0,000 | -0,000 |
| read_60 | 0,963 | 0,962 | 0,963 | +0,001 | +0,000 |
| bits_6 | 0,964 | 0,964 | 0,964 | +0,000 | +0,000 |
| bits_4 | 0,953 | 0,944 | 0,954 | +0,010 | +0,001 |
| beam_narrow | 0,959 | 0,430 | 0,959 | +0,529 | -0,000 |
| beam_flat | 0,964 | 0,964 | 0,964 | +0,000 | +0,001 |
| laser | 0,948 | 0,952 | 0,951 | -0,001 | +0,003 |
| band_0 | 0,966 | 0,965 | 0,965 | -0,000 | -0,000 |
| band_20 | 0,958 | 0,958 | 0,957 | -0,000 | -0,000 |
| band_40 | 0,927 | 0,928 | 0,929 | +0,001 | +0,002 |
| pinhole_20 | 0,964 | 0,963 | 0,964 | +0,001 | +0,000 |
| pinhole_50 | 0,965 | 0,965 | 0,965 | +0,000 | +0,001 |
| pinhole_200 | 0,900 | 0,899 | 0,904 | +0,004 | +0,004 |
| source_5cm | 0,514 | 0,418 | 0,518 | +0,100 | +0,005 |
| dust_0 | 0,966 | 0,967 | 0,967 | +0,000 | +0,001 |
| dust_8 | 0,959 | 0,960 | 0,960 | -0,000 | +0,001 |
| dust_20 | 0,947 | 0,950 | 0,950 | +0,000 | +0,003 |
| opaque | 0,978 | 0,977 | 0,978 | +0,000 | -0,000 |
| absorbing | 0,899 | 0,899 | 0,901 | +0,002 | +0,002 |
| transparent | 0,906 | 0,906 | 0,906 | +0,000 | +0,000 |
| depth_0 | 0,964 | 0,964 | 0,965 | +0,000 | +0,001 |
| depth_150 | 0,963 | 0,963 | 0,963 | -0,000 | +0,001 |
| depth_300 | 0,959 | 0,958 | 0,959 | +0,001 | -0,000 |
| session_0 | 0,965 | 0,965 | 0,964 | -0,000 | -0,001 |
| session_2 | 0,939 | 0,964 | 0,964 | +0,000 | +0,025 |
| session_5 | 0,753 | 0,964 | 0,964 | +0,000 | +0,211 |
| no_outside | 0,974 | 0,973 | 0,973 | -0,000 | -0,000 |
| periodic | 0,980 | 0,979 | 0,980 | +0,000 | -0,000 |
| frame_2 | 0,955 | 0,964 | 0,965 | +0,000 | +0,010 |
| frame_5 | 0,865 | 0,964 | 0,964 | -0,000 | +0,098 |
| walk_05 | 0,934 | 0,964 | 0,965 | +0,000 | +0,031 |

Nenhum conjunto em que `rec_afc` perca mais de 0,02 para `rec_af` ou `rec_z0` (as maiores perdas: −0,0012
para `rec_af` em `laser`, −0,0010 para `rec_z0` em `fullwell_500`).

## 2026-11-14, 10:57–10:59 — Passo 4: oráculo de pixels em `frame_2`, `frame_5`, `walk_05`

Como a fila do paper (`experiment oracle --workers 16`, CPU), com 6 workers e nada mais rodando, só nos três conjuntos:

```bash
cp -p results/oracle.csv $S/before_oracle/
# tmux integ_oracle, CPU, 10:57:23 -> 10:59:26 (log logs/integracao/oracle.log)
bash scripts/exp_distancia/integ_run.sh experiment oracle --device cpu --workers 6 --variants frame_2 frame_5 walk_05
python scripts/exp_distancia/integ_check.py $S/before_oracle/oracle.csv results/oracle.csv --keys rep variant boxes \
  --intended "variant in ['frame_2','frame_5','walk_05']"
```

2 min, saída 0. `oracle.csv`: 330 → 360 linhas (+30 = 3 conjuntos × 5 repetições × caixas gt/det, todas novas); nenhuma
chave antiga sumiu; 320 antigas idênticas, 10 (`periodic`, as últimas gravadas) com 1 ULP. Rótulos certos com a
correção do `oracle.py` (`distance per frame (%)` 2 / 5, `distance drift per frame (%)` 0.5). F1 aberto macro (média de
5; recall do localizador por limiar entre parênteses, caixas `det`): `frame_2` gt 0,8720, det 0,6963 (0,593);
`frame_5` gt 0,8196, det 0,6697 (0,489); `walk_05` gt 0,8480, det 0,6921 (0,543) — ao lado, do paper: base gt 0,8840,
det 0,6910 (0,631); `session_2` 0,8620 / 0,6906; `session_5` 0,7873 / 0,6695.

## 2026-11-14, 11:00 — Passo 8: erro de distância da busca estreita na bateria (`results/focus_battery.csv`)

Com o comando do pacote que fez o `focus_error.csv` do estudo (mesma definição: erro |z encontrado − z verdadeiro|,
mediana em µm, falha grosseira = erro > 1 % de z0 = 192,5 µm), num diretório de rascunho, e copiado para
`results/focus_battery.csv`:

```bash
# CPU, 10:59:58 -> 11:00:01 (log logs/integracao/focus_battery.log)
HOLO_RESULTS=$S/focus python -m holo_openset experiment focus error --sets realistic variants/<32 de VARIANTS> \
  variants/frame_2 variants/frame_5 variants/walk_05 --methods af afc --split test
cp $S/focus/focus_error.csv results/focus_battery.csv
```

44 linhas: `afc` nos 36 conjuntos (18 reconstruções por imagem, 800 imagens de teste cada) e `af` (busca cega, 114)
onde o `autofocus.csv` existe (base, `fullwell_500`, `beam_narrow`, `session_2`, `session_5`, `frame_2`, `frame_5`,
`walk_05`; os `autofocus.csv` só-z0 da conferência do passo 1 ficaram fora dos conjuntos). As 16 linhas em comum com
`results_exp_distancia/focus_error.csv` são iguais (diferença máxima 0). Colunas: `set, method,
reconstructions_per_image, n, median_um, p90_um, max_um, gross`.

| conjunto | afc mediana (µm) | afc falhas grosseiras | af mediana (µm) | af falhas grosseiras | F1 afc − af | F1 afc − z0 |
|---|---|---|---|---|---|---|
| base | 50,1 | 0,25 % | 50,3 | 1,38 % | +0,000 | +0,000 |
| fullwell_500 | 50,1 | 1,75 % | 446,8 | 70,25 % | +0,178 | -0,001 |
| fullwell_1500 | 50,1 | 0,75 % | — | — | +0,002 | -0,000 |
| fullwell_24000 | 50,1 | 0,12 % | — | — | +0,000 | +0,001 |
| read_10 | 50,1 | 0,25 % | — | — | -0,000 | -0,000 |
| read_30 | 50,1 | 0,38 % | — | — | +0,000 | -0,000 |
| read_60 | 50,1 | 0,38 % | — | — | +0,001 | +0,000 |
| bits_6 | 50,1 | 0,25 % | — | — | +0,000 | +0,000 |
| bits_4 | 50,1 | 0,38 % | — | — | +0,010 | +0,001 |
| beam_narrow | 50,1 | 0,25 % | 13049,2 | 74,00 % | +0,529 | -0,000 |
| beam_flat | 50,1 | 0,25 % | — | — | +0,000 | +0,001 |
| laser | 37,3 | 0,75 % | — | — | -0,001 | +0,003 |
| band_0 | 42,2 | 0,25 % | — | — | -0,000 | -0,000 |
| band_20 | 50,1 | 1,75 % | — | — | -0,000 | -0,000 |
| band_40 | 86,1 | 11,62 % | — | — | +0,001 | +0,002 |
| pinhole_20 | 42,2 | 0,00 % | — | — | +0,001 | +0,000 |
| pinhole_50 | 42,2 | 0,12 % | — | — | +0,000 | +0,001 |
| pinhole_200 | 55,9 | 5,25 % | — | — | +0,004 | +0,004 |
| source_5cm | 55,9 | 7,25 % | — | — | +0,100 | +0,005 |
| dust_0 | 50,1 | 0,50 % | — | — | +0,000 | +0,001 |
| dust_8 | 42,2 | 0,25 % | — | — | -0,000 | +0,001 |
| dust_20 | 42,2 | 0,00 % | — | — | +0,000 | +0,003 |
| opaque | 37,3 | 0,12 % | — | — | +0,000 | -0,000 |
| absorbing | 42,2 | 0,88 % | — | — | +0,002 | +0,002 |
| transparent | 78,2 | 1,88 % | — | — | +0,000 | +0,000 |
| depth_0 | 42,2 | 0,25 % | — | — | +0,000 | +0,001 |
| depth_150 | 64,2 | 3,88 % | — | — | -0,000 | +0,001 |
| depth_300 | 103,0 | 23,38 % | — | — | +0,001 | -0,000 |
| session_0 | 0,0 | 0,25 % | — | — | -0,000 | -0,001 |
| session_2 | 56,1 | 0,75 % | 49,5 | 2,25 % | +0,000 | +0,025 |
| session_5 | 28,2 | 0,12 % | 50,0 | 2,00 % | +0,000 | +0,211 |
| no_outside | 50,1 | 0,38 % | — | — | -0,000 | -0,000 |
| periodic | 37,3 | 0,00 % | — | — | +0,000 | -0,000 |
| frame_2 | 41,0 | 0,62 % | 49,4 | 1,62 % | +0,000 | +0,010 |
| frame_5 | 45,0 | 0,25 % | 46,6 | 2,38 % | -0,000 | +0,098 |
| walk_05 | 42,6 | 0,00 % | 46,8 | 1,50 % | +0,000 | +0,031 |

(A mediana de 50,1 µm em muitos conjuntos é o passo da grade fina da busca; em `session_0` a distância verdadeira é z0,
que está na grade.) **Sinalizações (perda de F1 de `rec_afc` > 0,02 contra `rec_af` ou `rec_z0`): nenhuma.** Onde a
busca estreita mais erra a distância — `depth_300` (23,4 % de falhas grosseiras, mediana 103 µm), `band_40` (11,6 %),
`source_5cm` (7,3 %), `pinhole_200` (5,3 %), `depth_150` (3,9 %) — o F1 não cai (−0,000 a +0,005 contra `rec_z0`):
nesses conjuntos o "foco" do campo inteiro é mal definido (objetos em profundidades diferentes, fonte larga), e o erro
contra o z da sessão não mede o que o classificador vê. Fica como descrição para o líder.
