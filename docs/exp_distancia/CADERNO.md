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

---

## 2026-11-13 — Etapa 1: código do estudo e invariância

### Integração do código

O código das Seções 6.2–6.5 foi escrito e testado num worktree à parte (branch `wip/etapa1`, 5 commits sobre
`3fe514c`), enquanto a Etapa 0 terminava com o código do paper. Como o commit da Etapa 0 (`60b2939`) entrou depois de
`3fe514c`, o `git merge --ff-only wip/etapa1` recusou (históricos divergentes). Rebaseei os 5 commits sobre `60b2939`
(sem conflito: os arquivos não se tocam) e então o fast-forward passou; a árvore de código (`holo_openset/`, `tests/`,
`scripts/`) depois do merge é idêntica byte a byte à de `a620fd9`, a ponta original de `wip/etapa1`
(`git diff --quiet a620fd9 HEAD -- holo_openset tests scripts`). Os hashes dos 5 commits mudaram (`94eefd3`..`154373f`).

```bash
git -C <worktree> rebase 60b2939
git merge --ff-only wip/etapa1          # HEAD 154373f
git worktree remove <worktree> && git branch -d wip/etapa1
```

O que mudou (`git diff 3fe514c..HEAD`, só código): simulador com `frame_z_std`, `frame_z_walk` e `tilt_deg` (todos
desligados por padrão, cada sorteio novo com seu `random.Random`); `reconstruct.py` com `Focus`, `autofocus`
generalizado, o registro `FOCUS` (vazio por enquanto), `distances` e `build_caches` escrevendo `autofocus_<método>.csv`
para os métodos do estudo; fluxos do estudo com pesos emprestados; `experiments/focus.py`; `robustness --by-session` e
`--own`; `full_frames`/`timing --frames-set`; CLI `simulate variant --split` e `simulate full --name`.

### Testes

```bash
python -m pytest -q                              # 19 passed  (com HOLO_RESULTS desligado; ver nota 1)
python -m holo_openset reproduce check           # 12/12 files identical to expected/  (idem)
git status --short                               # results/ intocado
```

Notas de ambiente (não são mudanças de código):

1. `env.sh` aponta `HOLO_RESULTS` para `results_exp_distancia/`, e tanto `reproduce check` quanto o teste
   `test_tables_of_the_paper_match_the_results` geram as tabelas a partir de `HOLO_RESULTS`. Com o `env.sh` ativo, o
   check falhou (entre os que diferem, `tab_scale`, `tab_stack` e `tab_stages`, porque os CSVs do paper não estão lá) e o teste falhou
   (18 passed, 1 failed), e ambos escreveram `results_exp_distancia/data_summary.json` (apagado). Rodados com
   `unset HOLO_RESULTS` (lendo `results/`, como no paper): 19 passed e 12/12. Para o check e o teste, sempre
   `unset HOLO_RESULTS`.
2. O pacote não está instalado no ambiente do paper (`../.envbuild/holo-openset`): `pytest` (o executável) e
   `python scripts/...` não acham `holo_openset`. Uso `python -m pytest` e `PYTHONPATH=$PWD python scripts/...`.

### Invariância (protocolo 6.1, item 3)

```bash
PYTHONPATH=$PWD python scripts/exp_distancia/invariance.py --device cuda:1     # tmux; log logs/exp_distancia/invariance_session_5.log
```

16:55–17:37, `cuda:1` (load 76 no início, 395 no fim; as seis GPUs a 43–100 % de outros usuários). Regrava
`variants/session_5` com o código novo em `data/_check/session_5`, reconstrói `rec_z0`/`rec_af` e o `autofocus.csv` e
compara valor a valor com o que o código do paper escreveu na Etapa 0, **nesta mesma máquina e build**. Saída:

```
wrote /home/jovyan/compartilhado/ralph/openset-microscopy/holo-openset/data/_check/session_5 (800, 640, 640)
identical  session_5/holograms.npy  (800, 640, 640) 0.0000% of the values differ, rms 0.0000
identical  session_5/backgrounds.npy  (50, 640, 640) 0.0000% of the values differ, rms 0.0000
identical  session_5/annotations.csv  
identical  session_5/metadata.csv  
identical  session_5/dust.csv  
identical  session_5/sessions.csv  
identical  session_5/physics.json  (without the new fields, all of them off)
identical  session_5/rec_z0.npy  (800, 3, 640, 640) 0.0000% of the values differ, rms 0.0000
identical  session_5/rec_af.npy  (800, 3, 640, 640) 0.0000% of the values differ, rms 0.0000
identical  session_5/autofocus.csv  
ALL IDENTICAL
```

O código novo, com os efeitos novos desligados, grava os mesmos hologramas e escreve as mesmas reconstruções que o
código do paper, bit a bit. A primeira tentativa (16:55) falhou com `ModuleNotFoundError` (nota 2 acima) antes de
escrever qualquer coisa.

### Checagem longa do base (em andamento)

`invariance.py --base` (regravar as 5000 imagens do base em `data/_check/realistic` e comparar com `data/realistic` e
`checksums/data.sha256`) ainda não foi lançado: prioridade mais baixa, roda em segundo plano depois das etapas
urgentes (ver abaixo). Pelo achado da figura do Checkpoint 1, ele só pode bater com os checksums publicados até a
diferença entre builds.

### Figura do Checkpoint 1

```bash
PYTHONPATH=$PWD python scripts/exp_distancia/fig_checkpoint1.py --device cuda:2    # docs/exp_distancia/img/checkpoint1_holograms.png
```

Imagem de teste 1 do base (sessão 0, 11 letras, z da sessão 19,0492 mm), gravada três vezes com as funções de
`sim/generate.py` exatamente como `generate()` grava uma imagem: física do base; `frame_z_std = 0,05`; `tilt_deg = 10`.
Na imagem 1, o sorteio de `frame_z_std` deu z = 19,1206 mm (+0,37 %, um sorteio pequeno de N(0; 5 %)); a inclinação
leva as letras de −55…+123 µm para −111…+111 µm em torno de z (deslocamentos de −70 a +55 µm). Linhas: holograma;
holograma − base (escala ±3 níveis, percentil 99,5); |U| retropropagado em z₀ = 19,25 mm.

**Identidade bit a bit com o publicado: não.** Regravar a imagem 1 do base nesta máquina dá **0,0259 % dos pixels
diferentes** do holograma publicado (`data/realistic/holograms.npy`, linha 1), com diferença máxima de 7 níveis de cinza.
Ou seja, este build não é o build que escreveu o conjunto publicado (o `docs/REPRODUCIBILITY.md` relata 0,02 % entre
builds). Portanto a prova bit a bit de que o código novo não muda nada é a comparação de `session_5` acima (código do
paper contra código novo NESTE build: idênticos), e o base regravado aqui só pode bater com os checksums publicados até
essa diferença entre builds.

### Timing de referência numa GPU ociosa (pedido do responsável)

Às 21:43 o servidor estava calmo (load 82 / 57 / 50), mas nenhuma GPU estava ociosa: amostrando `nvidia-smi` por 10 s,
GPU 0 a 93–98 %, GPU 1 a 3–100 % (média ≈ 25 %), GPUs 2–5 a 39–100 %. Pela instrução (só numa GPU a 0 % de outros
usuários), **não rodei**; fica pendente para quando houver uma GPU ociosa (o mesmo comando, com
`HOLO_RESULTS=$PWD/results_exp_distancia/etapa1_timing_idle`).

### Decisões de projeto e desvios do protocolo (tomados pelo responsável)

1. Os conjuntos novos `frame_2`, `frame_5` e `walk_05` ficam em `sim/variants.STUDY` (e `ALL = VARIANTS + STUDY`), não
   em `VARIANTS`: a fila do paper (`pipeline.py`), `simulate variants`, `tab_robustness` e `fig_robustness` iteram sobre
   `VARIANTS` e precisam continuar com os seus 32 conjuntos.
2. Os fluxos do estudo (`rec_<método de foco>`, `rec_edfw`) ficam em `flows.STUDY`, incorporados a `FLOWS` mas fora de
   `PAPER_FLOWS`, que é o que a fila treina e o que `e2e`, `robustness` e `full_frames` rodam por padrão.
3. O alias `weights` é resolvido quando um modelo é CARREGADO (`experiments/common.model`, `cli evaluate`, via
   `flows.weights_of`), e não dentro de `paths.weights` como diz o texto do protocolo: `paths.weights` também é onde o
   `train` escreve, e o alias ali faria `train --flow rec_afn` pular, ou com `--force` sobrescrever, o `rec_af_r1.pt` do
   paper. `robustness --own` avalia um fluxo com o seu próprio checkpoint (linhas salvas como `<fluxo>+own`).
4. `build_caches`: os métodos do paper mantêm o seu laço e o `autofocus.csv` intocados; os métodos do estudo escrevem
   `rec_<m>.npy` e `autofocus_<m>.csv`. Armadilha preexistente, mantida: `reconstruct --methods z0` sozinho reescreve o
   `autofocus.csv` com `z_af = z0`.
5. `simulate full`: novo `--name`; agora se recusa a sobrescrever um conjunto existente sem `--force`; e `--n-images`
   tinha padrão 5000 para todos os subcomandos, de modo que `simulate full` sem `--n-images 40` (como está escrito o
   comando de E2 no protocolo) gravaria 5000 quadros inteiros: o padrão agora é 5000 para base/small e 40 para full.
6. `simulate variant --split val` escreve `data/variants_val/<nome>`.
7. `reconstruct.Focus` tem, além do que o protocolo lista, `fill` (com máscara, a amplitude fora dela vira 1 antes de
   propagar: o ruído das regiões sem luz se espalha pela janela inteira ao ser propagado, então mascarar só a nitidez
   não basta) e a varredura também vai testar `bin = 8`; ambos são candidatos só de validação.
8. A deriva `frame_z_walk` começa em 0: a primeira imagem de uma sessão está na distância da sessão.
9. O `docs/REPRODUCIBILITY.md` diz que a fila tem 555 jobs; o código do paper tem 575 (documento desatualizado); o
   teste novo fixa 575.
