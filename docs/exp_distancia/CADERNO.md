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

---

## 2026-11-13 — Pré-registro da Etapa 2: varredura do autofocus e políticas de foco

Escrito e commitado **antes** de rodar qualquer varredura. Nada aqui usa o split de teste; o subcomando
`experiment focus sweep` só lê imagens de validação e recusa um conjunto que não as tenha.

### Candidatos (E3, parte 1)

256 buscas, o produto de três eixos (`holo_openset/experiments/focus.py`: `SEARCH`, `BINS`, `CRITERIA`):

| eixo | valores |
|---|---|
| faixa e candidatos (grosso + fino) | cega 0,2–2,1 z₀ (73+41, a do paper); ±30 % (31+21); ±20 % (21+21); ±15 % (15+11, o exemplo do protocolo; 15+21; 9+15); ±10 % (11+11; 7+11) |
| redução da amplitude por média | 1, 2, 4 e 8 (8 está além da lista do protocolo; só entra se a validação o sustentar) |
| critério | ToG do paper; ToG do campo suavizado (σ = 1 e 2 px); máscara onde o blank frame > 20 % do máximo, com e sem preencher a amplitude fora dela com 1 (`fill`), com e sem suavização (σ = 1,5 e 2 px) |

Conjuntos de validação (700 imagens cada, as mesmas cenas): `realistic` (val), `variants_val/frame_5`,
`variants_val/fullwell_500`, `variants_val/beam_narrow`. Por candidato e conjunto: erro |z − z verdadeiro| mediano e
percentil 90, taxa de **falha grosseira** (erro > 1 % de z₀ = 192,5 µm, cerca de seis profundidades de campo),
número de reconstruções, **custo** = reconstruções / bin² (reconstruções equivalentes da imagem inteira) e o tempo
medido na varredura (só indicativo: GPU compartilhada; o tempo que vale é o de E5).

### Regras de escolha (mecânicas: `experiment focus select`)

Condição "acha a distância": erro mediano ≤ 50 µm **e** falha grosseira ≤ a do autofocus cego do paper + 1 ponto
percentual, em `realistic` (val) **e** em `variants_val/frame_5`.

1. **`afc` (barato):** o de menor custo entre os que satisfazem a condição; empate: menor percentil 90 (o pior dos
   dois conjuntos).
2. **`afr` (robusto):** entre os que satisfazem a condição e não custam mais que o cego (114), o de menor falha
   grosseira no pior dos dois conjuntos ruidosos (`fullwell_500`, `beam_narrow`); empates dentro de 0,5 ponto: menor
   percentil 90 nos ruidosos, depois menor custo.
3. **`afx` (os dois):** o mais barato que satisfaz a condição e cuja falha grosseira em cada conjunto ruidoso é no
   máximo a do `afr` + 1 ponto. Se coincidir com `afc` ou `afr`, vão ao teste só dois.

No máximo esses três vão ao teste, com o modelo de `rec_af`. O custo usado na escolha é o proxy acima, não o tempo
medido, porque a GPU compartilhada não dá tempos confiáveis para 256 candidatos; a ordem de custo será conferida em E5.

### Políticas de foco (`experiment focus policy`)

- **`afs`, k ∈ {1, 3}:** com as distâncias que o autofocus cego achou em cada imagem de validação de `realistic`,
  `variants_val/session_5`, `variants_val/fullwell_500` e `variants_val/beam_narrow` (7 sessões cada), a distância da
  sessão é a mediana das k primeiras imagens. k = 3 só se reduzir o número de sessões com falha grosseira, somado
  sobre os quatro conjuntos; senão k = 1 (mais barato).
- **`afM`, M ∈ {2, 5, 10, 20, 50}:** em `variants_val/walk_05`, o maior M cuja acurácia nas classes vistas da
  validação (modelos `rec_af` e limiares do conjunto base, média das 5 repetições; galeria = imagens pares da
  validação do base, consultas = imagens ímpares da variante reconstruídas na distância da política) fica a até 0,01
  da de M = 1. Se nenhum, M = 2.
- **`afsx` (derivado, sem parâmetro novo):** a busca `afx` (ou `afr`, se `afx` não existir) feita uma vez por
  sessão com o mesmo k de `afs`. É o "melhor autofocus razoável" de Q1 quando a distância é fixa na sessão.

### O que será rodado no teste depois de congelar (declarado agora)

Uma única matriz, com todos os fluxos em todos os conjuntos de janelas, cinco repetições, `--by-session`:
conjuntos `base`, `session_2`, `session_5`, `fullwell_500`, `beam_narrow`, `frame_2`, `frame_5`, `walk_05`;
fluxos `rec_z0`, `rec_af`, `rec_afs`, `rec_afsx`, `rec_afM`, `rec_afc`, `rec_afr`, `rec_afx`, `prop`, `bank_jit`,
`bank_wide`, `bank_w2`. Nenhum fluxo ou conjunto é acrescentado ou retirado depois de ver resultados de teste; se
algo precisar mudar, a mudança e o motivo vão para o caderno antes.

Checagem do modelo próprio (protocolo 6.4): `rec_afx` (ou `rec_afc`, se `afx` não existir) treinado na r1 com as
cenas auxiliares reconstruídas pelo mesmo método, comparado com o modelo emprestado de `rec_af` nos oito conjuntos;
critério: diferença de F1 ≤ 0,01 em todos.

O primeiro run de qualquer método novo no teste só acontece depois do commit que registra as escolhas em
`reconstruct.FOCUS`, com data neste caderno.

---

## 2026-11-13 — Timing de referência na GPU mais livre (adendo à Etapa 1)

Às 21:43 nenhuma GPU estava a 0 % (ver acima). Às 21:55 a GPU 4 alternava: em 20 amostras de 1 s, 0 % em 13 e 34–89 %
nas outras 7 (outro usuário com rajadas curtas; 26,9 GB ocupados por outros). Como o `timing` reporta o **mínimo** de 20
repetições, que pega as janelas ociosas, rodei nela e julguei a validade pela regra 8.1 (crescimento com o tamanho):

```bash
HOLO_RESULTS=$PWD/results_exp_distancia/etapa1_timing_idle python -m holo_openset experiment timing --device cuda:4 --rep 1
```

21:56:30–21:57:06 (código novo; os estágios do paper mais `layer_bank_wide`, `layer_bank_w2`, `per_object_wide`).
Antes: load 48,9; GPU 4 a 0 %, as outras a 70–100 %. Depois: load 42,6; GPU 4 a 46 %. Log
`logs/exp_distancia/etapa1_timing_idle.log`.

Razão nosso/paper por estágio (`min_s`, GPU; tempos em ms):

| estágio | 640 nosso | 640 paper | razão | 2048 razão | quadro inteiro nosso | paper | razão |
|---|---|---|---|---|---|---|---|
| flat_field | 0,029 | 0,055 | 0,52 | 1,01 | 0,177 | 0,180 | 0,98 |
| layer_real | 0,089 | 0,169 | 0,53 | 0,94 | 0,568 | 0,567 | 1,00 |
| layer_complex | 0,131 | 0,250 | 0,53 | 0,97 | 1,082 | 1,084 | 1,00 |
| layer_prop | 0,135 | 0,284 | 0,47 | 0,92 | 1,093 | 1,103 | 0,99 |
| layer_bank | 0,189 | 0,293 | 0,65 | 0,97 | 3,513 | 3,531 | 0,99 |
| layer_bank_jit | 0,188 | 0,370 | 0,51 | 0,97 | 3,508 | 3,662 | 0,96 |
| layer_bank_w1 | 0,231 | 0,308 | 0,75 | 0,98 | 5,757 | 4,814 | 1,20 |
| layer_bank_w3 | 0,230 | 0,307 | 0,75 | 0,97 | 5,785 | 4,758 | 1,22 |
| backprop | 0,089 | 0,166 | 0,53 | 0,94 | 0,968 | 0,976 | 0,99 |
| autofocus | 4,78 | 4,89 | 0,98 | 1,23 | 151,5 | 123,7 | 1,22 |
| per_object | 1,66 | 1,75 | 0,95 | 1,11 | 54,5 | 48,2 | 1,13 |
| twin | 5,78 | 8,53 | 0,68 | 1,20 | 104,2 | 85,8 | 1,21 |
| channels | 0,519 | 0,689 | 0,75 | 1,45 | 2,02 | 1,79 | 1,13 |
| yolo_tiled | 9,70 | 12,96 | 0,75 | 0,76 | 163,9 | 221,7 | 0,74 |
| embed | 1,63 | 2,24 | 0,73 | 0,66 | 2,38 | 2,44 | 0,98 |
| decide | 0,070 | 0,100 | 0,70 | 0,75 | 0,108 | 0,118 | 0,92 |

Estágios novos (`min_s`, ms; 640 / 1280 / 2048 / quadro inteiro): `layer_bank_wide` 0,229 / 0,776 / 1,826 / 5,767;
`layer_bank_w2` 0,281 / 0,961 / 2,292 / 7,026; `per_object_wide` 2,50 / 12,2 / 35,3 / 103,4.

Razões entre estágios (estágio / backprop), nosso contra paper:

| razão | 640 nosso | paper | 2048 nosso | paper | quadro inteiro nosso | paper |
|---|---|---|---|---|---|---|
| autofocus / backprop | 53,8 | 29,4 | 165,1 | 125,5 | 156,4 | 126,7 |
| layer_bank / backprop | 2,13 | 1,76 | 3,75 | 3,61 | 3,63 | 3,62 |
| layer_bank_jit / backprop | 2,11 | 2,23 | 3,75 | 3,62 | 3,62 | 3,75 |
| layer_prop / backprop | 1,52 | 1,70 | 1,07 | 1,09 | 1,13 | 1,13 |
| yolo_tiled / backprop | 109,2 | 77,9 | 168,8 | 208,4 | 169,2 | 227,1 |
| twin / backprop | 65,1 | 51,3 | 106,9 | 83,6 | 107,7 | 87,9 |

**Veredito, regra 8.1: válido a partir de 2048 × 2048 e no quadro inteiro.** O `backprop` cresce 2,0 / 4,1 / 10,9×
de 640 a 1280 / 2048 / quadro inteiro (paper 1,18 / 2,32 / 5,86×) e o autofocus 4,0 / 12,5 / 31,7× (paper 3,9 / 9,9 /
25,3×); no quadro inteiro os estágios de uma chamada batem com o paper a 1–4 % (backprop 0,968 contra 0,976 ms,
layer_bank_jit 3,51 contra 3,66 ms) e as razões entre estágios também (layer_bank_jit/backprop 3,62 contra 3,75).
Ressalvas: (1) a 640 × 640 os estágios de uma chamada saem a ≈ 0,5× do paper, o que faz o autofocus/backprop subir para
54 contra 29: o backprop de 0,09 ms está perto do custo fixo de lançamento, e a razão nesse tamanho é sensível a isso;
(2) três entradas de 1280 × 1280 estão contaminadas pelas rajadas do outro usuário mesmo no mínimo de 20 (flat_field
0,304 ms, layer_real 0,384 ms, layer_prop 2,566 ms, contra 0,06–0,32 no paper e contra os valores vizinhos); (3) o
autofocus, o twin e o per_object (iterativos, centenas de kernels) saem 13–22 % mais caros que no paper no quadro inteiro.
A GPU não estava ociosa o tempo todo, então isto é uma referência, não a medição final (E5).

---

## 2026-11-13 — Etapa 2: dados de validação, varredura do autofocus, seleção e políticas

Pré-registro commitado em `9e41879` às 21:44:19, antes de qualquer varredura (a primeira, o smoke test, começou às
21:46:35; a primeira varredura real, às 21:47:08). Servidor calmo nesta etapa: load 25–63; GPUs ainda com outros
usuários (a maioria a 90–100 %, com janelas mais livres em 0, 1, 2 e 4).

### Dados de validação (cenas do split de validação do base, 700 imagens cada)

```bash
# tmux ed_val1, cuda:0, 21:44 -> ~21:54 (log logs/exp_distancia/val_v1.log)
python -m holo_openset simulate variant frame_5 fullwell_500 walk_05 --split val --device cuda:0 --workers 6
# tmux ed_val2, cuda:1, 21:45 -> ~21:55 (log logs/exp_distancia/val_v2.log)
python -m holo_openset simulate variant beam_narrow session_5 --split val --device cuda:1 --workers 6
```

Conferência (script do scratchpad `check_val.py`, log `logs/exp_distancia/check_val.log`):

```
frame_5: holograms (700, 640, 640) (non-empty rows 700), split=val, sessions 7, annotations 5711 equal to base val: True, ids equal: True
   physics: frame_z_std=0.05 frame_z_walk=0.0 tilt_deg=0.0 session_z_std=0.005 full_well=6000.0 beam_waist=[2.0, 3.5]
   z per session: distinct values min 100 max 100; z/z_session - 1: std 0.0496, min -0.1575, max +0.1416; first image of each session at the session z: False
   OK
fullwell_500: holograms (700, 640, 640) (non-empty rows 700), split=val, sessions 7, annotations 5711 equal to base val: True, ids equal: True
   physics: frame_z_std=0.0 frame_z_walk=0.0 tilt_deg=0.0 session_z_std=0.005 full_well=500.0 beam_waist=[2.0, 3.5]
   z per session: distinct values min 1 max 1; z/z_session - 1: std 0.0000, min +0.0000, max +0.0000; first image of each session at the session z: True
   OK
walk_05: holograms (700, 640, 640) (non-empty rows 700), split=val, sessions 7, annotations 5711 equal to base val: True, ids equal: True
   physics: frame_z_std=0.0 frame_z_walk=0.005 tilt_deg=0.0 session_z_std=0.005 full_well=6000.0 beam_waist=[2.0, 3.5]
   z per session: distinct values min 100 max 100; z/z_session - 1: std 0.0238, min -0.0592, max +0.0548; first image of each session at the session z: True
   OK
beam_narrow: holograms (700, 640, 640) (non-empty rows 700), split=val, sessions 7, annotations 5711 equal to base val: True, ids equal: True
   physics: frame_z_std=0.0 frame_z_walk=0.0 tilt_deg=0.0 session_z_std=0.005 full_well=6000.0 beam_waist=[0.9, 1.3]
   z per session: distinct values min 1 max 1; z/z_session - 1: std 0.0000, min +0.0000, max +0.0000; first image of each session at the session z: True
   OK
session_5: holograms (700, 640, 640) (non-empty rows 700), split=val, sessions 7, annotations 5711 equal to base val: True, ids equal: True
   physics: frame_z_std=0.0 frame_z_walk=0.0 tilt_deg=0.0 session_z_std=0.05 full_well=6000.0 beam_waist=[2.0, 3.5]
   z per session: distinct values min 1 max 1; z/z_session - 1: std 0.0000, min +0.0000, max +0.0000; first image of each session at the session z: True
   OK
ALL CHECKS PASSED
```

Todos com 700 hologramas não vazios, as mesmas 700 imagens e as mesmas 5711 anotações (image_id, caixa, classe) das
linhas de validação de `data/realistic/annotations.csv`. z varia por imagem em `frame_5` (100 valores por sessão, desvio
relativo 4,96 %) e `walk_05` (100 valores por sessão, até ±5,9 %, a primeira imagem de cada sessão no z da sessão); é
constante por sessão nos outros três.

### Varredura (E3 parte 1)

Smoke test, fora das pastas do projeto (7 imagens de validação × 256 candidatos, `cuda:2`, 21:46:35–21:46:50):

```bash
HOLO_RESULTS=$S/smoke/results HOLO_LOGS=$S/smoke/logs python -m holo_openset experiment focus sweep --device cuda:2 --sets realistic --stride 100
```

Rodou sem erro; tempo medido de busca 1,41 s por imagem (os 256 candidatos); `blind-b1-tog` com erro mediano 20,7 µm,
p90 70,9 µm, nenhuma falha grosseira nas 7 imagens. Nenhuma mudança em `focus.py`.

Varreduras reais (uma sessão tmux por conjunto; logs `logs/exp_distancia/sweep_<conjunto>.log`; as distâncias por
candidato e imagem em `logs/exp_distancia/focus_sweep/<conjunto>.npz`):

| conjunto | GPU | início | fim | tempo de busca medido (256 candidatos), s/imagem |
|---|---|---|---|---|
| realistic (val) | cuda:2, depois cuda:0 | 21:47:08 | 22:07:26 | 1,71 |
| variants_val/beam_narrow | cuda:5, depois cuda:0 | 21:49:00 | 22:09:45 | 1,76 |
| variants_val/frame_5 | cuda:1 | 21:50:02 | 22:11:04 | 1,79 |
| variants_val/fullwell_500 | cuda:0 | 21:51:05 | 22:02:02 | 0,93 |
| variants_val/session_5 e walk_05 (só `blind-b1-tog`) | cuda:1 | 21:55:24 | 21:55:59 | 0,019 |

```bash
python -m holo_openset experiment focus sweep --device cuda:N --sets <conjunto>
python -m holo_openset experiment focus sweep --device cuda:1 --sets variants_val/session_5 variants_val/walk_05 --candidates blind-b1-tog
```

`realistic` e `beam_narrow` ficaram lentos nas GPUs 2 e 5 (até 7 s/imagem, carga de outros usuários): interrompi cada
um logo depois de um ponto de salvamento (425 e 375 imagens salvas; as imagens feitas depois do último salvamento foram
descartadas junto com o seu tempo) e retomei na GPU 0, que estava a 2–6 %; a retomada reaproveita o `.npz` (logs da
primeira parte em `sweep_<conjunto>_part1_cuda*.log`). O tempo por imagem é só indicativo (GPU compartilhada). As quatro
matrizes estão completas (256 × 700, todas finitas) e o `focus_sweep.csv` tem 256 linhas por conjunto.

### Seleção (regras pré-registradas)

```bash
python -m holo_openset experiment focus select      # log logs/exp_distancia/focus_select.log
```

Resultado: `cheap` (afc) = `r10b-b4-m`, `robust` (afr) = `r15b-b2-s2`, `both` (afx) = `r10b-b4-tog`; 174 de 256
candidatos satisfazem a condição "acha a distância". Saída completa em `results_exp_distancia/focus_selection.json`.

| candidato | papel | custo | conjunto | mediana (µm) | p90 (µm) | falha grosseira |
|---|---|---|---|---|---|---|
| blind-b1-tog | referência | 114 | realistic | 48,4 | 123,9 | 1,29 % |
| | | | frame_5 | 47,7 | 122,9 | 2,43 % |
| | | | fullwell_500 | 391,7 | 13343 | 70,57 % |
| | | | beam_narrow | 187,5 | 13417 | 49,86 % |
| r10b-b4-m | afc | 1,125 | realistic | 30,9 | 93,1 | 0,86 % |
| | | | frame_5 | 42,5 | 105,7 | 0,71 % |
| | | | fullwell_500 | 35,3 | 97,4 | 0,86 % |
| | | | beam_narrow | 30,9 | 97,6 | 2,86 % |
| r15b-b2-s2 | afr | 9 | realistic | 29,3 | 84,8 | 0,43 % |
| | | | frame_5 | 32,8 | 83,4 | 0,29 % |
| | | | fullwell_500 | 29,3 | 84,8 | 0,86 % |
| | | | beam_narrow | 29,3 | 84,8 | 0,86 % |
| r10b-b4-tog | afx | 1,125 | realistic | 30,9 | 93,1 | 0,86 % |
| | | | frame_5 | 42,5 | 105,7 | 0,71 % |
| | | | fullwell_500 | 35,3 | 97,4 | 0,86 % |
| | | | beam_narrow | 30,9 | 93,1 | 0,86 % |

**Empate não resolvido pela regra escrita (para o responsável decidir):** na regra 1 (afc), três candidatos empatam
em custo (1,125) **e** no desempate pré-registrado (percentil 90 do pior conjunto limpo, 105,705 µm): `r10b-b4-m`,
`r10b-b4-mf` e `r10b-b4-tog` (têm as mesmas distâncias em `realistic` e `frame_5`). O `select` escolheu `r10b-b4-m` pela
ordem alfabética do índice, um critério que não está no pré-registro. `r10b-b4-tog`, que é o afx, está entre os
empatados; com ele como afc, afc e afx coincidiriam e iriam ao teste só dois (regra 3). Não mudei nada.

### Políticas

```bash
python -m holo_openset experiment focus policy --device cuda:0      # 22:11:33–22:12:13; log logs/exp_distancia/focus_policy.log
```

Saída:

```
1 {'base set': 0.9499, 'true distance': 0.953, 1: 0.9534, 2: 0.9516, 5: 0.9508, 10: 0.9481, 20: 0.9411, 50: 0.931, 0: 0.913}
2 {'base set': 0.9501, 'true distance': 0.9537, 1: 0.9519, 2: 0.9523, 5: 0.9515, 10: 0.9492, 20: 0.9404, 50: 0.936, 0: 0.9254}
3 {'base set': 0.9503, 'true distance': 0.9524, 1: 0.952, 2: 0.9511, 5: 0.952, 10: 0.949, 20: 0.9426, 50: 0.9348, 0: 0.9228}
4 {'base set': 0.95, 'true distance': 0.9483, 1: 0.9488, 2: 0.9466, 5: 0.9466, 10: 0.9419, 20: 0.9376, 50: 0.9324, 0: 0.9233}
5 {'base set': 0.9495, 'true distance': 0.9407, 1: 0.942, 2: 0.9412, 5: 0.9407, 10: 0.939, 20: 0.9341, 50: 0.9253, 0: 0.9148}
              policy                        set  sessions  sessions_gross      n   median_um        p90_um        max_um     gross  val_known_acc  val_known_acc_std  reps
0   session, first 1                  realistic       7.0             0.0  700.0   20.652809     91.720645     91.720645  0.000000            NaN                NaN   NaN
1   session, first 3                  realistic       7.0             0.0  700.0    4.347191     68.054318     68.054318  0.000000            NaN                NaN   NaN
2        every image                  realistic       NaN             NaN  700.0   48.353471    123.883702    483.562585  0.012857            NaN                NaN   NaN
3   session, first 1     variants_val/session_5       7.0             0.0  700.0   41.465286    130.543176    130.543176  0.000000            NaN                NaN   NaN
4   session, first 3     variants_val/session_5       7.0             0.0  700.0   41.465286    130.543176    130.543176  0.000000            NaN                NaN   NaN
5        every image     variants_val/session_5       NaN             NaN  700.0   42.206448    135.625854    735.625854  0.022857            NaN                NaN   NaN
6   session, first 1  variants_val/fullwell_500       7.0             4.0  700.0  206.945682  13583.562585  13583.562585  0.571429            NaN                NaN   NaN
7   session, first 3  variants_val/fullwell_500       7.0             4.0  700.0  206.945682  13583.562585  13583.562585  0.571429            NaN                NaN   NaN
8        every image  variants_val/fullwell_500       NaN             NaN  700.0  391.720645  13343.054318  19226.395373  0.705714            NaN                NaN   NaN
9   session, first 1   variants_val/beam_narrow       7.0             2.0  700.0  122.441353  13508.562585  13508.562585  0.285714            NaN                NaN   NaN
10  session, first 3   variants_val/beam_narrow       7.0             2.0  700.0   54.347191  13458.562585  13458.562585  0.285714            NaN                NaN   NaN
11       every image   variants_val/beam_narrow       NaN             NaN  700.0  187.500000  13416.720645  13604.347191  0.498571            NaN                NaN   NaN
12          base set       variants_val/walk_05       NaN             NaN    NaN         NaN           NaN           NaN       NaN       0.949968           0.000300   5.0
13     true distance       variants_val/walk_05       NaN             NaN    NaN         NaN           NaN           NaN       NaN       0.949617           0.005396   5.0
14       every image       variants_val/walk_05       NaN             NaN  700.0   51.350967    127.012327   1033.421817  0.021429       0.949615           0.004570   5.0
15           every 2       variants_val/walk_05       NaN             NaN  700.0   63.697368    169.991795   1033.421817  0.060000       0.948574           0.004722   5.0
16           every 5       variants_val/walk_05       NaN             NaN  700.0   81.996070    253.769183    642.816316  0.165714       0.948306           0.004748   5.0
17          every 10       variants_val/walk_05       NaN             NaN  700.0  129.578264    358.844477    811.115304  0.347143       0.945438           0.004724   5.0
18          every 20       variants_val/walk_05       NaN             NaN  700.0  187.854360    520.093643    936.115304  0.491429       0.939153           0.003350   5.0
19          every 50       variants_val/walk_05       NaN             NaN  700.0  253.706684    612.014641   1186.115304  0.624286       0.931915           0.004174   5.0
20  session, first 1       variants_val/walk_05       NaN             NaN  700.0  369.858201    749.537771   1057.502675  0.764286       0.919875           0.005592   5.0
```

O que as regras pré-registradas dão (aplicação mecânica, sem interpretação):

- **afs:** sessões com falha grosseira somadas nos quatro conjuntos: k = 1 → 0 + 0 + 4 + 2 = 6; k = 3 → 0 + 0 + 4 + 2 =
  6. k = 3 não reduz, então **k = 1**.
- **afM:** acurácia nas classes vistas da validação de `walk_05` com M = 1: 0,949615. M = 2: 0,948574 (−0,0010);
  M = 5: 0,948306 (−0,0013); M = 10: 0,945438 (−0,0042); M = 20: 0,939153 (−0,0105); M = 50: 0,931915 (−0,0177).
  O maior M a até 0,01 de M = 1 é **M = 10**.
- **afsx:** a busca `afx` (`r10b-b4-tog`) uma vez por sessão com k = 1.

Nada foi registrado em `reconstruct.FOCUS` e nenhum método novo rodou no teste: as escolhas esperam a revisão do
responsável.

### Nota sobre a figura do Checkpoint 1

A checagem longa do base (`invariance.py --base`, tmux `inv_base`, `cuda:4`, lançada às 21:57:50, em andamento) já
escreveu as primeiras linhas de `data/_check/realistic/holograms.npy`. A gravação da imagem 1 feita pelo script da
figura (em GPU) é idêntica pixel a pixel à linha 1 escrita pelo `generate()` neste build (0 pixels diferentes), e essa
linha difere do publicado nos mesmos 0,0259 % (máx. 7 níveis); nas primeiras 250 imagens, 0,0187 % dos pixels diferem
do publicado, e todas as 250 têm alguma diferença. Isso confirma que a diferença é do build, não do script.

---

## 2026-11-13, 22:16 — Congelamento das escolhas da Etapa 2 (antes de qualquer método novo ver o teste)

Revisão da varredura e das políticas pelo responsável, e registro em `reconstruct.FOCUS` (commit deste registro).

**Um empate que o pré-registro não previa.** Na regra 1 (`afc`), três candidatos empatam no custo (1,125) e no
desempate previsto (pior p90 nos conjuntos limpos, 105,7 µm): `r10b-b4-tog`, `r10b-b4-m` e `r10b-b4-mf`. Nos dois
conjuntos limpos os três acham exatamente as mesmas distâncias: com o feixe da bancada a máscara de 20 % não exclui
nada. O `focus select` ficou com `r10b-b4-m` só por ordem alfabética, o que não é regra. Decisão, tomada sem nenhum
dado de teste: entre candidatos indistinguíveis pelas regras, fica o que faz menos operações, `r10b-b4-tog` (sem
máscara, o critério do paper). É também o candidato que a regra 3 (`afx`) escolheu sozinha. Consequência prevista no
pré-registro: `afc` e `afx` coincidem, e **vão ao teste duas buscas, não três**.

| nome | busca | reconstruções | custo | o que é |
|---|---|---|---|---|
| `afc` (= `afx`) | `r10b-b4-tog`: ±10 % de z₀, 7 + 11 candidatos, amplitude reduzida 4×, ToG | 18 | 1,125 | a mais barata que acha a distância, e a mais barata que resiste ao ruído |
| `afr` | `r15b-b2-s2`: ±15 %, 15 + 21, reduzida 2×, campo suavizado σ = 2 px | 36 | 9 | a de menos falhas grosseiras sob ruído |
| `afs` | busca cega do paper, uma vez por sessão, k = 1 | 114 / n | — | regra do k: k = 3 não reduz as 6 sessões com falha |
| `afM` | busca cega do paper a cada M = 10 imagens | 114 / 10 | — | regra do M: M = 20 cai 0,0105 abaixo de M = 1 |
| `afsc` | a busca `afc` uma vez por sessão, k = 1 | 18 / n | — | o `afsx` do pré-registro, com o nome da busca que ficou |

**O que a varredura mostra, só na validação** (falha grosseira em `realistic` / `frame_5` / `fullwell_500` /
`beam_narrow`): busca cega do paper 1,3 / 2,4 / 70,6 / 49,9 %. Só estreitar a faixa não resolve o ruído (`r10b-b1-tog`:
3,1 / 3,3 / 66,9 / 21,9 %). Só reduzir a amplitude 4× resolve o ruído e parte do feixe (`blind-b4-tog`: 0,7 / 0,7 /
1,0 / 12,1 %); só suavizar também (`blind-b1-s2`: 1,0 / 0,9 / 0,7 / 5,7 %). As duas coisas juntas resolvem tudo
(`r10b-b4-tog`: 0,9 / 0,7 / 0,9 / 0,9 %). Reduzir 8× é demais numa janela de 640 px (5–11 % de falhas). A máscara do
blank frame não foi o que fez diferença. Isto é validação: o teste dirá se se sustenta.

**Matriz de teste, como declarada no pré-registro, com os nomes que ficaram:** conjuntos `base`, `session_2`,
`session_5`, `fullwell_500`, `beam_narrow`, `frame_2`, `frame_5`, `walk_05`; fluxos `rec_z0`, `rec_af`, `rec_afs`,
`rec_afsc`, `rec_afM`, `rec_afc`, `rec_afr`, `prop`, `bank_jit`, `bank_wide`, `bank_w2` (onze: `rec_afx` saiu por
coincidir com `rec_afc`). Piloto na r1, depois r2–r5. Checagem do modelo próprio: `rec_afc`, r1.

**Quadros inteiros, declarado agora, antes de rodar:** E1 (os 40 quadros do paper) e E2 (`full_frames_frame5`) com
`rec_z0`, `rec_af`, `rec_afs`, `rec_afsc`, `rec_afc`, `rec_afr`, `prop`, `bank_jit`, `bank_wide`, `bank_w2` (`rec_afM`
não entra: com 5 quadros por sessão, refocar a cada 10 é o mesmo que `rec_afs`). E4 (inclinação) com os seis fluxos
do protocolo (`rec_z0`, `rec_af`, `rec_edfw`, `bank_jit`, `bank_wide`, `bank_w2`) mais `rec_afc`, que passou a ser o
autofocus de referência do estudo.

**n\*, declarado agora:** a conta principal usa o front end completo de cada fluxo, como manda a regra 8.4 do
protocolo: convencional = flat field + busca / n + uma back-propagation + canais; stack = a camada. A fórmula
simplificada da Seção 3 do protocolo, T_af / (T_stack − T_backprop), que não cobra do fluxo convencional o flat
field e os canais, é reportada ao lado.

---

## 2026-11-13, 22:18 — Etapa 3: o teste (E1–E5) com as escolhas congeladas

Tudo nesta etapa roda o que o congelamento das 22:16 (`68e81ea`) fixou; nenhum parâmetro, fluxo ou conjunto foi
mudado. Ambiente: `source scripts/exp_distancia/env.sh` (4 threads por processo). O driver dos dados de teste (tmux
`ed_dados`, `cuda:3`, `scripts/exp_distancia/dados_teste.sh`) estava simulando `fullwell_500` quando a etapa começou.

### E5, sessão de tempo: CPU (um core)

```bash
# tmux e5_cpu, 22:18:26 -> 22:24:56 (log logs/exp_distancia/e5_cpu.log)
HOLO_RESULTS=$PWD/results_exp_distancia/e5 python -m holo_openset experiment timing --device cpu --rep 1
```

Load 89,2 / 74,8 / 59,2 no começo e 70,4 / 75,4 / 64,4 no fim. Terminou em 6,5 min (não horas): todos os 21 estágios
nos quatro tamanhos (640², 1280², 2048², 2748 × 3840), 5 repetições por estágio (2 para os iterativos no quadro
inteiro), `--threads 1`. Saída `results_exp_distancia/e5/timing_cpu.csv`. Mediana (`median_s`, ms):

| estágio | 640² | 1280² | 2048² | quadro inteiro |
|---|---|---|---|---|
| flat_field | 0,620 | 0,302 | 7,80 | 112,3 |
| backprop | 6,91 | 40,0 | 456,1 | 1008 |
| channels | 18,0 | 157,1 | 332,4 | 1192 |
| autofocus | 3583 | 18260 | 45600 | 116400 |
| autofocus_afc | 13,1 | 119,8 | 191,9 | 1045 |
| autofocus_afr | 148,4 | 1685 | 4194 | 9482 |
| per_object | 704,8 | 3986 | 9539 | 24980 |
| per_object_wide | 1472 | 7384 | 19050 | 48350 |
| layer_prop | 4,15 | 23,9 | 194,9 | 779 |
| layer_bank_jit | 25,2 | 461,2 | 1055 | 2419 |
| layer_bank_wide | 46,5 | 488,2 | 1267 | 3136 |
| layer_bank_w2 | 62,9 | 660,3 | 1790 | 4097 |
| yolo_tiled | 320,6 | 4456 | 7199 | 21370 |
| embed | 60,5 | 171,6 | 304,8 | 685,4 |
| decide | 0,179 | 0,095 | 0,151 | 0,294 |

Anotado sem interpretar: `flat_field` a 1280² (0,30 ms) sai abaixo do de 640² (0,62 ms).

### E5, sessão de tempo: GPU, tentativa 1 (`e5_a1`)

Script novo `scripts/exp_distancia/e5_gpu.sh <cuda:N> <pasta>`: `uptime` e `nvidia-smi` de todas as GPUs; 20 amostras
de 1 s da utilização da GPU do run; `timing --rep 1`; `full_frames --rep 1 2 3 4 5` com os onze fluxos (`rec_z0`,
`rec_af`, `rec_afs`, `rec_afsc`, `rec_afc`, `rec_afr`, `rec_edfw`, `prop`, `bank_jit`, `bank_wide`, `bank_w2`); de
novo 20 amostras e `uptime`/`nvidia-smi`.

Às 22:19–22:20 nenhuma GPU estava a 0 % o tempo todo (amostras de 30 s: GPU 0 média 21 %, 1 18 %, 2 13 % com 20 zeros
em 30, 3 a nossa simulação, 4 34 % com rajadas, 5 95 %). Às 22:20:41 a GPU 2 deu 0 % em 20 de 20 amostras (15,6 GB
ocupados por outro usuário, sem uso de computação); nenhum job nosso nela.

```bash
# tmux e5_a1, 22:20:46 (log logs/exp_distancia/e5_a1.log)
bash scripts/exp_distancia/e5_gpu.sh cuda:2 results_exp_distancia/e5_a1
```

Antes: load 62,7 / 68,7 / 59,1; GPUs 0 21 %, 1 18 %, 2 0 %, 3 99 % (nossa simulação), 4 0 %, 5 100 %; GPU 2 a 0 % nas
20 amostras. `timing`: 22:21:09 → 22:21:36 (load 65,9 no fim). **Validade (regra 8.1, `min_s` de `timing_gpu.csv`):
backprop no quadro inteiro 0,965 ms (paper 0,976; 0,99×), autofocus 123,3 ms (paper 123,7; 1,00×), `flat_field` a
640² 0,030 ms (< 0,2): válida.**

O `full_frames` caiu logo no início (`FileNotFoundError: data/realistic/rec_afs.npy`): a galeria de cada fluxo são as
janelas de validação do base reconstruídas por aquele fluxo, e os caches do estudo no base ainda não existiam (a Etapa 2
os constrói). Com `set -e` o script parou ali, sem as amostras e o `nvidia-smi` do fim. Além disso, o fluxo `rec_edfw`
também não teria galeria: `data/realistic/rec_edfw.npy` não existia e o pacote não tinha como construí-lo
(`reconstruct --methods edfw` recusava o método). Correção abaixo. A tentativa 1 fica como está (timing válido,
`full_frames` não rodou); a sessão completa, num só run, vai para uma tentativa 2.

### Correção no pacote: cache `rec_edfw` (commit `740a667`)

`build_caches` aceita agora os métodos de `EDF` que não são do paper (`edfw`): por imagem, o autofocus cego e depois
`per_object` com a faixa de `EDF['edfw']` (±6 %, 49 passos) nas caixas anotadas, exatamente como o `front_end` do
`full_frames` faz com `rec_edfw` e como o `edf` do paper é construído; escreve `rec_edfw.npy` e `autofocus_edfw.csv` e
não toca no `autofocus.csv`. Não muda número nenhum já produzido (só um ramo novo). `pytest`: 20 passed. Conferência:
o `z_af` do `autofocus_edfw.csv` do base é igual ao do `autofocus.csv` nas 5000 imagens (diferença máxima 0).

### Caches dos métodos do estudo (Etapa 2 do pedido)

```bash
python -m holo_openset reconstruct --set <conjunto> --methods afs afM afc afr afsc --device cuda:N
python -m holo_openset reconstruct --set realistic --methods edfw --device cuda:4      # galeria de rec_edfw
```

| conjunto | GPU | início | fim | log |
|---|---|---|---|---|
| realistic | cuda:2 | 22:23:19 | 22:26:40 | `cache_realistic.log` |
| realistic (edfw) | cuda:4 | 22:24:29 | 22:26:03 | `cache_realistic_edfw.log` |
| variants/session_5 | cuda:2 | 22:30:16 | 22:32:20 | `cache_session_5.log` |
| session_2, fullwell_500, beam_narrow (em série) | cuda:1 | 22:32:37 | 22:38:11 | `cache_<conjunto>.log` |
| frame_2, frame_5, walk_05 (em série) | cuda:2 | 22:33:37 | 22:39:55 | `cache_<conjunto>.log` |

Todos com saída 0. O driver terminou as seis variantes e os seus caches z0/af às 22:32:10 (passou para os quadros
inteiros) antes de eu começar os caches delas. Load 44–100 nesse intervalo; às 22:28 todas as GPUs, menos a 0, foram a
100 % com outros usuários. Os logs de autofocus dos oito conjuntos de teste (`autofocus.csv`, `autofocus_<método>.csv`)
estão copiados em `results_exp_distancia/autofocus_logs/<conjunto>/`.

### Erro de distância no split de teste

```bash
python -m holo_openset experiment focus error --split test --sets realistic variants/session_2 variants/session_5 \
  variants/fullwell_500 variants/beam_narrow variants/frame_2 variants/frame_5 variants/walk_05 --methods af afs afM afc afr afsc
# 22:40:29, log logs/exp_distancia/focus_error_test.log -> results_exp_distancia/focus_error.csv, focus_error_sessions.csv
```

800 imagens de teste por conjunto. Mediana / p90 do erro (µm) e falha grosseira (erro > 1 % de z₀):

| conjunto | af | afs | afM | afc | afr | afsc |
|---|---|---|---|---|---|---|
| realistic | 50,3 / 106,5 / 1,38 % | 40,4 / 74,7 / 0 % | 49,2 / 101,2 / 1,25 % | 50,1 / 103,0 / 0,25 % | 35,8 / 88,0 / 0,38 % | 71,0 / 115,7 / 0 % |
| session_2 | 49,5 / 123,8 / 2,25 % | 66,1 / 120,6 / 0 % | 45,7 / 104,9 / 0 % | 56,1 / 101,2 / 0,75 % | 32,0 / 81,9 / 0,13 % | 60,5 / 95,2 / 0 % |
| session_5 | 50,0 / 121,9 / 2,00 % | 40,4 / 98,7 / 0 % | 41,8 / 108,0 / 2,50 % | 28,2 / 116,4 / 0,13 % | 34,8 / 79,7 / 0,25 % | 20,3 / 91,0 / 0 % |
| fullwell_500 | 446,8 / 12951 / 70,3 % | 201,3 / 13299 / 50,0 % | 441,2 / 12779 / 67,5 % | 50,1 / 103,0 / 1,75 % | 31,1 / 88,0 / 0,38 % | 67,0 / 103,0 / 0 % |
| beam_narrow | 13049 / 13375 / 74,0 % | 13121 / 13744 / 87,5 % | 13049 / 13391 / 72,5 % | 50,1 / 103,0 / 0,25 % | 31,1 / 88,0 / 0,38 % | 73,5 / 115,7 / 0 % |
| frame_2 | 49,4 / 120,9 / 1,63 % | 392,9 / 1029 / 73,5 % | 318,6 / 793,5 / 65,0 % | 41,0 / 100,4 / 0,63 % | 33,7 / 84,5 / 0,25 % | 433,0 / 1027 / 75,5 % |
| frame_5 | 46,6 / 125,4 / 2,38 % | 1032,9 / 2468 / 87,9 % | 806,1 / 1984 / 80,1 % | 45,0 / 102,5 / 0,25 % | 32,6 / 84,5 / 0,38 % | 1053,3 / 2484 / 88,3 % |
| walk_05 | 46,8 / 124,6 / 1,50 % | 416,3 / 1050 / 73,8 % | 135,4 / 370,8 / 35,9 % | 42,6 / 103,1 / 0 % | 33,6 / 83,5 / 0,13 % | 387,6 / 1067 / 68,5 % |

### E1–E3: piloto da matriz de janelas na r1

```bash
# tmux rob_r1, cuda:1, 22:40:0x -> 22:43:37 (log logs/exp_distancia/robustness_r1.log)
python -m holo_openset experiment robustness --device cuda:1 --by-session --rep 1 \
  --variants base session_2 session_5 fullwell_500 beam_narrow frame_2 frame_5 walk_05 \
  --flows rec_z0 rec_af rec_afs rec_afsc rec_afM rec_afc rec_afr prop bank_jit bank_wide bank_w2
```

Checagem do piloto: 88 linhas da r1 (11 fluxos × 8 conjuntos), nenhum NaN nas colunas `novel_*`; as 8 linhas de
`rec_z0`, `rec_af`, `prop`, `bank_jit` em `base` e `session_5` comparadas com `results_exp_distancia/etapa0/robustness.csv`:
maior diferença absoluta em todas as colunas de métrica 1,1 × 10⁻¹⁶ (idênticas a menos do arredondamento do csv).
`robustness_sessions.csv`: 704 linhas (8 sessões de teste por conjunto). Piloto aceito; r2–r5 lançadas às 22:44 no
mesmo `cuda:1` (tmux `rob_r25`, log `robustness_r2-5.log`). O `robustness.csv` do topo de `results_exp_distancia/`
continha as 40 linhas da Etapa 0 (r1–r5); as da r1 foram reescritas com valores idênticos e as das r2–r5 serão
reescritas pelo run das r2–r5.

### E1–E3: r2–r5 da matriz de janelas

```bash
# tmux rob_r25, cuda:1, 22:44 -> 22:56:08 (log logs/exp_distancia/robustness_r2-5.log; load 49–61; GPU 1 a 100 % com outro usuário)
python -m holo_openset experiment robustness --device cuda:1 --by-session --rep 2 3 4 5 \
  --variants base session_2 session_5 fullwell_500 beam_narrow frame_2 frame_5 walk_05 \
  --flows rec_z0 rec_af rec_afs rec_afsc rec_afM rec_afc rec_afr prop bank_jit bank_wide bank_w2
```

`robustness.csv`: 88 linhas por repetição (440), nenhum NaN nas colunas `novel_*`; as 40 linhas da Etapa 0 (quatro
fluxos em `base` e `session_5`, r1–r5) são iguais às de `etapa0/robustness.csv` (diferença máxima 0).
`robustness_sessions.csv`: uma linha por repetição × conjunto × fluxo × sessão de teste (8 sessões).

novel_open_macro_f1 (média ± dp, 5 repetições)

| fluxo | base | session_2 | session_5 | fullwell_500 | beam_narrow | frame_2 | frame_5 | walk_05 |
|---|---|---|---|---|---|---|---|---|
| rec_z0 | 0,9641 ± 0,0070 | 0,9389 ± 0,0081 | 0,7526 ± 0,0107 | 0,9499 ± 0,0074 | 0,9591 ± 0,0072 | 0,9547 ± 0,0069 | 0,8655 ± 0,0100 | 0,9336 ± 0,0080 |
| rec_af | 0,9642 ± 0,0054 | 0,9641 ± 0,0053 | 0,9636 ± 0,0060 | 0,7699 ± 0,0066 | 0,4318 ± 0,0041 | 0,9643 ± 0,0056 | 0,9643 ± 0,0052 | 0,9644 ± 0,0045 |
| rec_afs | 0,9637 ± 0,0050 | 0,9637 ± 0,0046 | 0,9640 ± 0,0053 | 0,8029 ± 0,0070 | 0,2202 ± 0,0028 | 0,9272 ± 0,0059 | 0,7268 ± 0,0117 | 0,9275 ± 0,0055 |
| rec_afsc | 0,9641 ± 0,0061 | 0,9639 ± 0,0056 | 0,9643 ± 0,0056 | 0,9488 ± 0,0055 | 0,9591 ± 0,0052 | 0,9270 ± 0,0082 | 0,7246 ± 0,0125 | 0,9264 ± 0,0059 |
| rec_afM | 0,9643 ± 0,0051 | 0,9640 ± 0,0054 | 0,9637 ± 0,0056 | 0,7339 ± 0,0060 | 0,4041 ± 0,0052 | 0,9457 ± 0,0061 | 0,7976 ± 0,0115 | 0,9625 ± 0,0041 |
| rec_afc | 0,9642 ± 0,0052 | 0,9644 ± 0,0052 | 0,9640 ± 0,0055 | 0,9490 ± 0,0058 | 0,9589 ± 0,0053 | 0,9648 ± 0,0052 | 0,9639 ± 0,0047 | 0,9647 ± 0,0043 |
| rec_afr | 0,9644 ± 0,0049 | 0,9643 ± 0,0049 | 0,9641 ± 0,0052 | 0,9501 ± 0,0045 | 0,9591 ± 0,0044 | 0,9647 ± 0,0053 | 0,9643 ± 0,0047 | 0,9647 ± 0,0038 |
| prop | 0,9635 ± 0,0041 | 0,9392 ± 0,0041 | 0,7490 ± 0,0073 | 0,9562 ± 0,0045 | 0,8789 ± 0,0057 | 0,9539 ± 0,0038 | 0,8645 ± 0,0086 | 0,9298 ± 0,0050 |
| bank_jit | 0,9629 ± 0,0046 | 0,9566 ± 0,0047 | 0,8387 ± 0,0093 | 0,9628 ± 0,0050 | 0,8783 ± 0,0054 | 0,9605 ± 0,0043 | 0,9237 ± 0,0055 | 0,9525 ± 0,0042 |
| bank_wide | 0,9525 ± 0,0077 | 0,9523 ± 0,0080 | 0,9439 ± 0,0083 | 0,9518 ± 0,0078 | 0,8714 ± 0,0082 | 0,9525 ± 0,0077 | 0,9489 ± 0,0070 | 0,9511 ± 0,0058 |
| bank_w2 | 0,9525 ± 0,0065 | 0,9529 ± 0,0058 | 0,9438 ± 0,0071 | 0,9524 ± 0,0061 | 0,8750 ± 0,0077 | 0,9528 ± 0,0065 | 0,9482 ± 0,0060 | 0,9517 ± 0,0056 |

novel_unknown_rejection (média ± dp, 5 repetições)

| fluxo | base | session_2 | session_5 | fullwell_500 | beam_narrow | frame_2 | frame_5 | walk_05 |
|---|---|---|---|---|---|---|---|---|
| rec_z0 | 0,9233 ± 0,0553 | 0,9263 ± 0,0525 | 0,9497 ± 0,0415 | 0,9233 ± 0,0485 | 0,9212 ± 0,0537 | 0,9251 ± 0,0563 | 0,9375 ± 0,0526 | 0,9279 ± 0,0544 |
| rec_af | 0,9131 ± 0,0430 | 0,9155 ± 0,0433 | 0,9135 ± 0,0445 | 0,9309 ± 0,0340 | 0,9744 ± 0,0161 | 0,9149 ± 0,0444 | 0,9158 ± 0,0411 | 0,9105 ± 0,0387 |
| rec_afs | 0,9186 ± 0,0455 | 0,9170 ± 0,0424 | 0,9176 ± 0,0445 | 0,9289 ± 0,0376 | 0,9927 ± 0,0034 | 0,9202 ± 0,0432 | 0,9451 ± 0,0332 | 0,9171 ± 0,0469 |
| rec_afsc | 0,9199 ± 0,0403 | 0,9163 ± 0,0437 | 0,9174 ± 0,0417 | 0,9068 ± 0,0381 | 0,9123 ± 0,0401 | 0,9195 ± 0,0407 | 0,9446 ± 0,0315 | 0,9191 ± 0,0404 |
| rec_afM | 0,9173 ± 0,0428 | 0,9163 ± 0,0430 | 0,9167 ± 0,0419 | 0,9400 ± 0,0293 | 0,9753 ± 0,0162 | 0,9152 ± 0,0454 | 0,9361 ± 0,0382 | 0,9155 ± 0,0411 |
| rec_afc | 0,9191 ± 0,0410 | 0,9165 ± 0,0443 | 0,9153 ± 0,0421 | 0,9099 ± 0,0407 | 0,9124 ± 0,0410 | 0,9180 ± 0,0422 | 0,9176 ± 0,0391 | 0,9121 ± 0,0372 |
| rec_afr | 0,9192 ± 0,0437 | 0,9157 ± 0,0445 | 0,9172 ± 0,0454 | 0,9103 ± 0,0448 | 0,9130 ± 0,0453 | 0,9182 ± 0,0452 | 0,9176 ± 0,0428 | 0,9127 ± 0,0398 |
| prop | 0,9240 ± 0,0608 | 0,9310 ± 0,0524 | 0,9502 ± 0,0388 | 0,9175 ± 0,0611 | 0,9377 ± 0,0559 | 0,9296 ± 0,0578 | 0,9422 ± 0,0460 | 0,9297 ± 0,0534 |
| bank_jit | 0,9220 ± 0,0375 | 0,9232 ± 0,0358 | 0,9409 ± 0,0301 | 0,9213 ± 0,0399 | 0,9337 ± 0,0392 | 0,9191 ± 0,0404 | 0,9299 ± 0,0371 | 0,9245 ± 0,0355 |
| bank_wide | 0,8258 ± 0,0673 | 0,8245 ± 0,0662 | 0,8293 ± 0,0573 | 0,8237 ± 0,0668 | 0,8609 ± 0,0498 | 0,8235 ± 0,0622 | 0,8260 ± 0,0575 | 0,8277 ± 0,0540 |
| bank_w2 | 0,8377 ± 0,0721 | 0,8393 ± 0,0666 | 0,8387 ± 0,0654 | 0,8370 ± 0,0728 | 0,8706 ± 0,0640 | 0,8359 ± 0,0717 | 0,8341 ± 0,0686 | 0,8385 ± 0,0694 |

### E1, quadros inteiros: os 40 quadros do paper

```bash
# tmux ff_e1, cuda:4, 22:42:06 -> 23:03:53 (log logs/exp_distancia/ff_e1.log); load 48,5 no começo, 56,1 no fim; GPU 4 a 100 % com outro usuário
FL="rec_z0 rec_af rec_afs rec_afsc rec_afc rec_afr prop bank_jit bank_wide bank_w2"
python -m holo_openset experiment full_frames --device cuda:4 --flows $FL
```

Saída `results_exp_distancia/full_frames.csv`, `full_frames_time.csv`, `full_frames_focus.csv`. **Os tempos por estágio
destes runs de acurácia foram tomados em GPUs compartilhadas (a 100 % com outros usuários) e com outros jobs nossos
rodando; não são o tempo do estudo (que é o de E5).** Exemplo do efeito: o estágio `normalise` (ler o quadro e o blank
frame do disco e normalizar) aparece com 0,26–0,56 s por quadro neste log.

Conferência com o paper (`results/full_frames.csv`, mesmas repetições e caixas): `prop`, `bank_jit`, `bank_wide`,
`bank_w2` iguais (diferença máxima de F1 1,1 × 10⁻¹⁶); `rec_af` 2,8 × 10⁻⁵ e `rec_z0` 8,9 × 10⁻⁵ (as galerias destes
saem dos caches `rec_z0.npy`/`rec_af.npy` reconstruídos neste build).

`full_frames.csv`, caixas detectadas (`boxes == det`), média ± dp sobre as repetições:

| fluxo | reps | open-set F1 | rejeição | recall do detector | falsos positivos rejeitados |
|---|---|---|---|---|---|
| rec_z0 | 5 | 0,9750 ± 0,0063 | 0,9263 | 0,9967 | 0,9606 |
| rec_af | 5 | 0,9752 ± 0,0054 | 0,9165 | 0,9967 | 0,9554 |
| rec_afs | 5 | 0,9751 ± 0,0055 | 0,9175 | 0,9967 | 0,9583 |
| rec_afsc | 5 | 0,9752 ± 0,0054 | 0,9173 | 0,9967 | 0,9596 |
| rec_afc | 5 | 0,9752 ± 0,0053 | 0,9180 | 0,9967 | 0,9591 |
| rec_afr | 5 | 0,9751 ± 0,0053 | 0,9185 | 0,9967 | 0,9604 |
| prop | 5 | 0,9732 ± 0,0083 | 0,9188 | 0,9967 | 0,9484 |
| bank_jit | 5 | 0,9737 ± 0,0045 | 0,9255 | 0,9967 | 0,9387 |
| bank_wide | 5 | 0,9401 ± 0,0062 | 0,8307 | 0,9967 | 0,8830 |
| bank_w2 | 5 | 0,9436 ± 0,0123 | 0,8453 | 0,9967 | 0,8817 |

### E2, quadros inteiros: `full_frames_frame5` (distância por quadro, 5 %)

O driver terminou os sete conjuntos de quadros inteiros às 23:13:46 (`full_frames_frame5`, `full_frames_tilt{0,1,2,5,10,15}`;
tmux `ed_dados` encerrado sozinho). Script novo `scripts/exp_distancia/ff_run.sh <cuda:N> <conjunto> <fluxos>`:
`uptime`/`nvidia-smi` antes e depois e o `full_frames --frames-set` (cinco repetições, o padrão).

```bash
# tmux ff_frame5, cuda:1, 22:57:20 -> 23:15:41 (log logs/exp_distancia/ff_frame5.log); load 48,3 -> 57,2; GPU 1 a 100 % com outro usuário
bash scripts/exp_distancia/ff_run.sh cuda:1 full_frames_frame5 rec_z0 rec_af rec_afs rec_afsc rec_afc rec_afr prop bank_jit bank_wide bank_w2
#  = python -m holo_openset experiment full_frames --device cuda:1 --frames-set full_frames_frame5 --flows <os dez>
```

Saída `results_exp_distancia/full_frames_frame5{,_time,_focus}.csv`. Tempos por estágio: GPU compartilhada, não são E5.

`full_frames_frame5.csv`, caixas detectadas (`boxes == det`), média ± dp sobre as repetições:

| fluxo | reps | open-set F1 | rejeição | recall do detector | falsos positivos rejeitados |
|---|---|---|---|---|---|
| rec_z0 | 5 | 0,8617 ± 0,0083 | 0,9410 | 0,9964 | 0,9704 |
| rec_af | 5 | 0,9747 ± 0,0055 | 0,9141 | 0,9964 | 0,9582 |
| rec_afs | 5 | 0,8354 ± 0,0071 | 0,9285 | 0,9964 | 0,9689 |
| rec_afsc | 5 | 0,8351 ± 0,0071 | 0,9289 | 0,9964 | 0,9696 |
| rec_afc | 5 | 0,9751 ± 0,0055 | 0,9164 | 0,9964 | 0,9597 |
| rec_afr | 5 | 0,9751 ± 0,0058 | 0,9155 | 0,9964 | 0,9603 |
| prop | 5 | 0,8658 ± 0,0085 | 0,9386 | 0,9964 | 0,9572 |
| bank_jit | 5 | 0,9302 ± 0,0065 | 0,9298 | 0,9964 | 0,9402 |
| bank_wide | 5 | 0,9371 ± 0,0094 | 0,8266 | 0,9964 | 0,8726 |
| bank_w2 | 5 | 0,9397 ± 0,0125 | 0,8396 | 0,9964 | 0,8830 |

Erro de distância por quadro (`full_frames_frame5_focus.csv`, |z − z verdadeiro|, µm, 40 quadros × 5 repetições):
mediana / p90 / máximo: `rec_af` 10,3 / 24,9 / 32,3; `rec_afc` 30,1 / 59,2 / 67,5; `rec_afr` 11,9 / 22,2 / 29,5;
`rec_afs` 491,4 / 2174 / 2877; `rec_afsc` 503,9 / 2137 / 2879; `rec_z0` 650,3 / 1676 / 1868.

### Modelo próprio (protocolo 6.4): `rec_afc`, r1

```bash
# tmux own_aux, cuda:2, desde 22:41:03 (log logs/exp_distancia/own_aux_sim.log): cenas auxiliares da r1 em data/realistic/aux/ (pasta nova)
python -m holo_openset simulate aux --rep 1 --device cuda:2 --workers 6
#   r1 (2000, 640, 640), 15813 letras, pronto às 23:18 (GPU 2 a 100 % com outro usuário: ~37 min); o r1_cal, que o
#   comando também grava e o treino não usa, continua sendo simulado
# tmux own_rec, cuda:4, 23:18 -> 23:19:19 (log own_rec_afc.log)
python -m holo_openset reconstruct --aux r1 --methods afc --device cuda:4               # aux/r1_rec_afc.npy, aux/r1_autofocus_afc.csv
# tmux own_train, cuda:4, 23:19:34 -> 23:20:3x, 3000 passos em 56 s (log own_train_rec_afc.log)
HOLO_MODELS=$PWD/models_exp_distancia python -m holo_openset train --flow rec_afc --rep 1 --device cuda:4
# tmux own_rob, cuda:4, 23:20:4x -> 23:21:26 (log own_robustness.log); nenhum outro robustness rodando
HOLO_MODELS=$PWD/models_exp_distancia python -m holo_openset experiment robustness --device cuda:4 --own --rep 1 --flows rec_afc \
  --variants base session_2 session_5 fullwell_500 beam_narrow frame_2 frame_5 walk_05
```

O checkpoint ficou em `models_exp_distancia/realistic/rec_afc_r1.pt` (fora de `models/`); `models_exp_distancia/`
entrou no `.gitignore`. Load 39–42; GPU 4 com rajadas de outro usuário (12 de 20 amostras a 0 %). O run acrescentou 8
linhas `rec_afc+own` ao `robustness.csv` (448 linhas no total); com `--own` e sem `--by-session`, nada no
`robustness_sessions.csv`.

F1 aberto (`novel_open_macro_f1`), r1:

| conjunto | rec_afc (modelo de rec_af) | rec_afc+own | diferença (own − emprestado) |
|---|---|---|---|
| base | 0,9567 | 0,9610 | +0,0044 |
| session_2 | 0,9559 | 0,9619 | +0,0060 |
| session_5 | 0,9560 | 0,9605 | +0,0044 |
| fullwell_500 | 0,9400 | 0,9447 | +0,0046 |
| beam_narrow | 0,9507 | 0,9565 | +0,0058 |
| frame_2 | 0,9577 | 0,9619 | +0,0041 |
| frame_5 | 0,9573 | 0,9600 | +0,0026 |
| walk_05 | 0,9585 | 0,9610 | +0,0025 |

Maior diferença absoluta 0,0060 (`session_2`). Critério pré-registrado (diferença ≤ 0,01 em todos): satisfeito nos oito.

### E4, quadros inteiros: lâmina inclinada

```bash
FT="rec_z0 rec_af rec_afc rec_edfw bank_jit bank_wide bank_w2"
bash scripts/exp_distancia/ff_run.sh cuda:N full_frames_tilt$t $FT      # uma sessão tmux ff_tilt$t por conjunto; log logs/exp_distancia/ff_tilt$t.log
```

| θ | GPU | início | fim | load início → fim |
|---|---|---|---|---|
| 0° | cuda:1 | 22:58:20 | 23:11:42 | 53,6 → 49,3 |
| 1° | cuda:3 | 22:59:33 | 23:15:53 | 48,5 → 56,1 |
| 2° | cuda:4 | 23:04:25 | 23:14:18 | 53,0 → 47,3 |
| 5° | cuda:4 | 23:05:25 | 23:16:20 | 53,9 → 58,0 |
| 10° | cuda:1 | 23:12:08 | 23:23:32 | 62,5 → 38,0 |
| 15° | cuda:3 | 23:15:50 | 23:34:07 | 56,1 → 31,3 |

Todas as GPUs com outros usuários (90–100 %) e outros jobs nossos rodando ao mesmo tempo: os tempos por estágio destes
runs não são o tempo do estudo. Saída `results_exp_distancia/full_frames_tilt{0,1,2,5,10,15}{,_time,_focus}.csv`.

Open-set F1 com as caixas detectadas (`boxes == det`), média ± dp sobre as 5 repetições:

| fluxo | 0° | 1° | 2° | 5° | 10° | 15° |
|---|---|---|---|---|---|---|
| rec_z0 | 0,9749 ± 0,0064 | 0,9749 ± 0,0061 | 0,9749 ± 0,0059 | 0,9747 ± 0,0062 | 0,9734 ± 0,0063 | 0,9667 ± 0,0069 |
| rec_af | 0,9752 ± 0,0052 | 0,9750 ± 0,0052 | 0,9749 ± 0,0053 | 0,9745 ± 0,0054 | 0,9725 ± 0,0054 | 0,9672 ± 0,0060 |
| rec_afc | 0,9752 ± 0,0053 | 0,9750 ± 0,0052 | 0,9749 ± 0,0054 | 0,9746 ± 0,0053 | 0,9727 ± 0,0058 | 0,9668 ± 0,0060 |
| rec_edfw | 0,9722 ± 0,0091 | 0,9722 ± 0,0088 | 0,9720 ± 0,0086 | 0,9721 ± 0,0089 | 0,9723 ± 0,0090 | 0,9726 ± 0,0087 |
| bank_jit | 0,9737 ± 0,0045 | 0,9737 ± 0,0043 | 0,9736 ± 0,0044 | 0,9738 ± 0,0043 | 0,9731 ± 0,0043 | 0,9716 ± 0,0045 |
| bank_wide | 0,9401 ± 0,0061 | 0,9402 ± 0,0063 | 0,9403 ± 0,0063 | 0,9403 ± 0,0066 | 0,9404 ± 0,0064 | 0,9395 ± 0,0075 |
| bank_w2 | 0,9436 ± 0,0122 | 0,9440 ± 0,0122 | 0,9441 ± 0,0125 | 0,9442 ± 0,0124 | 0,9434 ± 0,0120 | 0,9429 ± 0,0120 |

Conferência de `full_frames_tilt0` contra `full_frames` (log `logs/exp_distancia/check_tilt0.log`): hologramas com
120542 de 422092800 pixels diferentes (0,0286 %), diferença máxima 17 níveis, todos os 40 quadros com alguma
diferença; blank frames (`backgrounds.npy`, float32) diferentes em 0,0414 % dos pixels, diferença máxima 1,875;
`annotations.csv` e `metadata.csv` idênticos byte a byte (8268 letras). O esperado era cerca de 0,02 % (a diferença
entre builds já vista no base: 0,0187 % nas primeiras 250 imagens); saiu 0,0286 %.

### E5, sessão de tempo: GPU, tentativa 2 (`e5_a2`), e qual tentativa conta

Desvio, anotado antes de ver o resultado: pela regra do pedido, a primeira tentativa válida é a que conta, e não
haveria segunda tentativa depois de uma válida. Fiz a tentativa 2 porque a 1 não chegou ao `full_frames` (faltavam os
caches das galerias) e a sessão de E5 pede `timing` e `full_frames` no mesmo run. Às 23:24:56 a GPU 1 deu 0 % em 20 de
20 amostras, sem job nosso nela (o `ff_tilt10` tinha acabado às 23:23:32); rodando ao mesmo tempo, nossos: `ff_tilt15`
(`cuda:3`) e a simulação `own_aux` (`cuda:2`).

```bash
# tmux e5_a2, 23:28:09 -> 23:34:27 (log logs/exp_distancia/e5_a2.log)
bash scripts/exp_distancia/e5_gpu.sh cuda:1 results_exp_distancia/e5_a2
```

Antes: load 33,2 / 36,0 / 44,3; GPUs 0 25 %, 1 0 % (6,3 GB de outro usuário), 2 100 %, 3 100 %, 4 42 %, 5 100 %; GPU 1
a 0 % nas 20 amostras. `timing` 23:28:31 → 23:28:58; `full_frames` (5 repetições, 11 fluxos) 23:28:58 → 23:34:04.
Depois: GPU 1 a 0 % nas 20 amostras; load 29,3 / 33,2 / 40,5. **Validade: backprop no quadro inteiro 0,970 ms (0,99×),
autofocus 122,9 ms (0,99×), `flat_field` a 640² 0,030 ms: válida.** O F1 do `full_frames` da tentativa 2 é igual ao de
E1 (`full_frames.csv`) nas 100 linhas (diferença máxima 0).

Pela regra escrita, **a que conta é a tentativa 1** (a primeira válida): o `timing_gpu.csv` dela foi copiado para
`results_exp_distancia/e5/` (ao lado do `timing_cpu.csv`). Ela não tem `full_frames`; a única sessão de E5 com
`timing` e `full_frames` no mesmo run é a tentativa 2, que fica em `results_exp_distancia/e5_a2/` para o responsável
decidir. As duas dão os mesmos tempos a 1–3 % nos estágios do quadro inteiro.

`min_s` (ms) das duas tentativas e do paper (`results/timing_gpu.csv`):

| estágio | a1 640² | a1 quadro | a2 640² | a2 quadro | paper 640² | paper quadro |
|---|---|---|---|---|---|---|
| flat_field | 0,0304 | 0,1786 | 0,03009 | 0,1781 | 0,05528 | 0,18 |
| backprop | 0,09047 | 0,9654 | 0,08962 | 0,9696 | 0,1665 | 0,9761 |
| channels | 0,5219 | 1,798 | 0,473 | 1,777 | 0,6886 | 1,786 |
| autofocus | 4,786 | 123,3 | 4,807 | 122,9 | 4,893 | 123,7 |
| autofocus_afc | 0,5243 | 1,595 | 0,5114 | 1,577 | — | — |
| autofocus_afr | 0,7808 | 11,18 | 0,7738 | 11,18 | — | — |
| per_object | 1,623 | 45,87 | 1,604 | 45,48 | 1,749 | 48,16 |
| per_object_wide | 2,496 | 85,52 | 2,48 | 84,68 | — | — |
| layer_prop | 0,1477 | 1,103 | 0,1321 | 1,096 | 0,2835 | 1,103 |
| layer_bank_jit | 0,1948 | 3,523 | 0,1861 | 3,523 | 0,3705 | 3,662 |
| layer_bank_wide | 0,2355 | 4,74 | 0,2286 | 4,72 | — | — |
| layer_bank_w2 | 0,2842 | 5,947 | 0,2799 | 5,931 | — | — |
| yolo_tiled | 10,45 | 165,8 | 8,074 | 166,8 | 12,96 | 221,7 |
| embed | 1,594 | 2,434 | 1,506 | 2,346 | 2,239 | 2,436 |
| decide | 0,07172 | 0,1073 | 0,06962 | 0,09179 | 0,09966 | 0,118 |

`full_frames` da tentativa 2 (`e5_a2/full_frames_time.csv`), mediana por quadro (s) da soma dos estágios de cada fluxo,
sem a detecção (0,178 s, comum a todos): `rec_z0` 0,0256, `rec_af` 0,1483, `rec_afs` 0,0250, `rec_afsc` 0,0249,
`rec_afc` 0,0264, `rec_afr` 0,0361, `rec_edfw` 0,2309, `prop` 0,0076, `bank_jit` 0,0111, `bank_wide` 0,0126, `bank_w2`
0,0144. O estágio `normalise` (ler e normalizar o quadro) é 0,018 s nos fluxos de reconstrução; `load` 0,003 s nos de
camada. Para `rec_afs`/`rec_afsc` o estágio `autofocus` só aparece no primeiro quadro de cada sessão.

### Fim da Etapa 3: conferências

- `own_aux` (simulação das cenas auxiliares da r1) terminou às 23:38:02 com saída 0: `r1` 15813 letras, `r1_cal`
  16422 letras (load 31,6 no fim). Nenhum job nosso ficou rodando.
- `env -u HOLO_RESULTS python -m pytest -q`: 20 passed.
- `env -u HOLO_RESULTS python -m holo_openset reproduce check`: 12/12 arquivos idênticos a `expected/`.
- `git status`: limpo; nada em `results/`, `expected/`, `models/` ou `data/full_frames` mudou. Caches novos (todos em
  `data/`, fora do git): `rec_{afs,afM,afc,afr,afsc}.npy` e `autofocus_<método>.csv` nos oito conjuntos de janelas,
  `data/realistic/rec_edfw.npy` e `autofocus_edfw.csv`, `data/realistic/aux/` (r1, r1_cal, `r1_rec_afc.npy`,
  `r1_autofocus_afc.csv`); modelo `models_exp_distancia/realistic/rec_afc_r1.pt`.

---

## 2026-11-13, 23:45 — Etapa 4: sessão de tempo que conta, gerador e relatório

### Nota sobre o subagente dos runs

O subagente que conduziu os runs da Etapa 3 foi interrompido por engano logo depois do commit `bfd4a0d` (fim da Etapa
3). Nada ficou rodando: o `own_aux` já tinha terminado às 23:38:02 e nenhum tmux nosso estava ativo. Ele não chegou a
escrever o relatório dele; a revisão da Etapa 3 foi feita por este caderno e pelos CSVs de `results_exp_distancia/`.

### Qual sessão de E5 conta (decisão do responsável)

**Decisão do responsável: a sessão de E5 que conta é a `e5_a2`.** Motivos:

1. O protocolo (7, E5) define a sessão de medição como `timing` **e** `full_frames` no mesmo run, e a regra 10.4
   proíbe misturar runs numa mesma tabela. Só a `e5_a2` tem as duas coisas.
2. A `e5_a1` não chegou ao `full_frames` por um erro de ordem nosso (as galerias dos fluxos do estudo ainda não
   tinham sido construídas), não por causa de nenhum tempo medido.
3. A regra "vale a primeira tentativa válida" foi escrita para impedir a escolha entre sessões completas. A primeira
   (e única) sessão completa e válida é a 2.
4. A escolha não depende dos valores: as duas tentativas concordam a 1–3 % nos estágios do quadro inteiro (tabela da
   Etapa 3 acima e n\* abaixo).

`results_exp_distancia/e5/` passa a conter a sessão 2 em GPU (`timing_gpu.csv`, `full_frames.csv`,
`full_frames_time.csv`, `full_frames_focus.csv`, cópias byte a byte de `e5_a2/`) e o run de CPU (`timing_cpu.csv`,
22:18). O `timing_gpu.csv` que estava em `e5/` era cópia da `e5_a1`, que continua em `e5_a1/` como réplica. O
orientador pode reverter.

n\* no quadro inteiro, GPU (`min_s`), com cada tentativa (`break_even` de `holo_openset/paper/distance.py`; script
`nstar_attempts.py` do scratchpad). Conta completa: n\* = T_busca / (T_camada − (T_flat_field + T_backprop +
T_channels)); simplificada: n\* = T_busca / (T_camada − T_backprop).

| stack | busca | completa a1 | completa a2 | simplificada a1 | simplificada a2 |
|---|---|---|---|---|---|
| bank_jit | cega | 212 | 205 | 48 | 48 |
| bank_jit | afc | 2,7 | 2,6 | 0,6 | 0,6 |
| bank_wide | cega | 69 | 68 | 33 | 33 |
| bank_wide | afc | 0,9 | 0,9 | 0,4 | 0,4 |
| bank_w2 | cega | 41 | 41 | 25 | 25 |
| bank_w2 | afc | 0,5 | 0,5 | 0,3 | 0,3 |

A maior diferença é a da conta completa de `bank_jit` com a busca cega (212 contra 205, 3 %): o denominador é pequeno
(3,523 − 2,942 = 0,581 ms na a1; 3,523 − 2,925 = 0,598 ms na a2), então 17 µs de diferença nos estágios mudam n\* em 7.

### Integração do gerador

O gerador das tabelas, macros e figuras (`holo_openset/paper/distance.py`) e os testes dele foram escritos num
worktree à parte e trazidos para este branch por cherry-pick: `b712ede` (era `192d189`) e `d000e7f` (era `3ac7478`).
O worktree já foi removido.

### Duas conferências para o relatório (só leitura de logs e metadados)

**Checagem longa do base (`invariance.py --base`).** Lançada às 21:57:50 (Etapa 2) e terminada às 22:15 (horário do
log), mas o resultado nunca tinha sido anotado aqui. Final de `logs/exp_distancia/invariance_base.log`:

```
DIFFERENT  realistic/holograms.npy  (5000, 640, 640) 0.0191% of the values differ, rms 0.0430
DIFFERENT  realistic/holograms.npy against checksums/data.sha256
DIFFERENT  realistic/backgrounds.npy  (50, 640, 640) 0.0039% of the values differ, rms 0.0025
DIFFERENT  realistic/backgrounds.npy against checksums/data.sha256
identical  realistic/annotations.csv / metadata.csv / dust.csv / sessions.csv / physics.json
SOMETHING DIFFERS
```

O base regravado com o código novo neste build difere do publicado em 0,0191 % dos valores dos hologramas e 0,0039 %
dos blank frames; anotações, metadados, poeira, sessões e física são idênticos. É a diferença entre builds já vista
(0,0187 % nas primeiras 250 imagens); a prova de que o código novo não muda nada continua sendo `session_5`, idêntico
bit a bit dentro deste build (Etapa 1). O item do checklist 12 "base idêntico ao Zenodo" **não é cumprido ao pé da
letra**.

**Faixa do `afc` contra as distâncias do teste.** A busca `afc` tem 7 candidatos grossos em [0,90; 1,10] z₀ (passo
0,0333 z₀) e a busca fina vai de um passo grosso abaixo a um acima do melhor (`reconstruct.autofocus`, `fine =
linspace(c - step, c + step, n_fine)`), então a faixa efetiva é [0,867; 1,133] z₀ (±13,3 %). Script
`range_check.py` do scratchpad (lê `data/<conjunto>/metadata.csv`, split de teste, e o `autofocus_afc.csv` copiado):

```
variants/session_5: z/z0 - 1 in [-0.1073, +0.1140], beyond +-10 %: 300, beyond +-13.33 %: 0
variants/frame_5:   z/z0 - 1 in [-0.1314, +0.1347], beyond +-10 %: 26,  beyond +-13.33 %: 1
variants/walk_05:   z/z0 - 1 in [-0.0761, +0.1094], beyond +-10 %: 5,   beyond +-13.33 %: 0
full_frames_frame5: z/z0 - 1 in [-0.0867, +0.0970], beyond +-10 %: 0,   beyond +-13.33 %: 0
(os outros conjuntos de teste ficam dentro de ±5,6 %)
frame_5, largest deviation: image 1454, true z 21.8421 mm (+0.1347), afc 21.8167 mm (+0.1333), error 25.5 um
```

O maior desvio do teste (+13,47 %, uma imagem de `frame_5`) fica 0,14 ponto fora da faixa efetiva; o `afc` devolveu a
borda da faixa (+13,33 %) com erro de 25,5 µm, abaixo do limiar de falha grosseira (192,5 µm). Fora dessa faixa a busca
barata falha por construção; isso não foi testado com distâncias maiores.

### Gerador, saídas e relatório (Etapa 4, 23:47 → 00:10)

Nenhum run de experimento, simulação, reconstrução ou treino nesta etapa: só o gerador, `pytest` e o `reproduce check`
(CPU, 4 threads). Nada escrito em `results/`, `expected/`, `models/` ou `data/`; nenhum CSV de resultado mudou.

Mudanças em `holo_openset/paper/distance.py` (commits `c5f012f`, `e8eb484`):

1. `tab_dist_time_measured`: o total sai em ms sem casas (coluna "total with the detector (ms)") e é o detector
   (mediana) mais a **mediana por quadro da soma de todos os estágios do fluxo** (coluna nova "without the detector
   (ms)"; antes era a soma das medianas dos grupos, 0,8 ms menor em `rec_z0`). Coluna nova "x stack 5" (total do fluxo
   / total de `bank_jit`). Grupos read / compute / embed + decide com uma casa. Macros renomeadas: `\DistMeasDetectMs`,
   `\DistMeas<Fluxo>TotalMs`, `...FlowMs`, `...OverBankJit` (as antigas em s não eram usadas por nenhum teste).
   Conferido: mediana por quadro sem detector `rec_z0` 25,6, `rec_af` 148,3, `rec_afc` 26,4, `rec_afr` 36,1, `rec_edfw`
   230,9, `prop` 7,6, `bank_jit` 11,1, `bank_wide` 12,6, `bank_w2` 14,4 ms; detector 178,1 ms; `normalise` 17,7–17,9
   ms contra `load` 2,8 ms.
2. Tabela nova `tab_dist_frames_paired` (tex + md + macros `\DistFramePair...`): diferenças pareadas de F1 fim a fim por
   repetição nos oito conjuntos de quadros inteiros, pares `rec_afc − rec_af`, `bank_jit|bank_wide|bank_w2 − rec_afc`,
   `rec_edfw − rec_afc` (onde os dois rodaram).
3. Tabela nova `tab_dist_criterion` (tex + md + macros `\DistCrit...`) e função `criterion()`: o critério da Seção 3 do
   protocolo aplicado mecanicamente nos 8 conjuntos de janelas × 3 stacks, com o front end do quadro inteiro de E5
   (amortizados com n = 100), nas duas leituras (A: convencionais com F1 ≥ melhor − 0,02; B: convencionais com F1 ≥ F1
   do stack). Convencionais: `rec_z0`, `rec_af`, `rec_afs`, `rec_afsc`, `rec_afM`, `rec_afc`, `rec_afr`. Resultado:
   cumprido em 1 de 24 linhas na leitura A (`bank_jit`, `walk_05`) e em 2 na B (`bank_jit` em `walk_05` e `frame_2`).
4. Macros `\DistSearchBlindOver{Afc,Afr}{Gpu,Cpu}` (busca cega / busca congelada no quadro inteiro: 78, 111, 11, 12).
5. Figuras: em `fig_dist_tilt` a legenda foi para baixo do eixo; em `fig_dist_breakeven` os rótulos à direita são
   posicionados por blocos centrados nos valores (sem sobreposição, dentro do eixo) e ligados à sua reta por um traço
   da cor dela. Conferidos a olho nos PNGs: um rótulo legível por reta nos dois painéis. PDFs salvos sem data de criação
   (rodar de novo dá os mesmos bytes).
6. Teste novo `test_distance_criterion_reads_the_phrase_two_ways` (números inventados em que A e B divergem, e os casos
   "F1 fails", "none reaches it" e "cheaper on CPU only"); o teste de entradas ausentes passa a exigir as duas tabelas
   novas.

Script novo `scripts/exp_distancia/relatorio.sh`: ativa o `env.sh`, roda o gerador, copia
`results_exp_distancia/distance/numbers_distancia.tex` para `results_exp_distancia/numbers_distancia.tex` e os PNGs
para `docs/exp_distancia/img/`.

```bash
bash scripts/exp_distancia/relatorio.sh                    # 1532 macros; saídas commitadas em e0f5a87 e 7730d1b
env -u HOLO_RESULTS python -m pytest -q                    # 23 passed
env -u HOLO_RESULTS python -m holo_openset reproduce check # 12/12 files identical to expected/
git diff --stat 9488fce HEAD -- results expected           # vazio
```

Relatório: `docs/exp_distancia/RELATORIO.md` (commit `d80b0b2`).

### Checklist da Seção 12

- ✔ `pytest` (23 passed) e `reproduce check` (12/12) passam no commit final, com `HOLO_RESULTS` desligado.
- ✘ Base gerado com o código novo idêntico ao do Zenodo: 0,0191 % dos valores dos hologramas e 0,0039 % dos blank
  frames diferem (diferença de build; ver acima); `session_5` é idêntico bit a bit entre o código do paper e o novo
  dentro deste build.
- ✔ Resultados novos em `results_exp_distancia/`; `git diff --stat 9488fce HEAD -- results expected` vazio.
- ✔ Escolhas de hiperparâmetro datadas antes do primeiro run no teste: pré-registro 21:44:19 (`9e41879`), congelamento
  22:16:15–22:16:23 (`058f8f9`, `03a2a21`, `68e81ea`); primeiro uso de método novo depois disso: timing de CPU 22:18:26
  (só tempo), primeiros caches do teste 22:23:19.
- ✘ (parcial) Toda tabela de tempo com front end e fim a fim, GPU e CPU, de um único run: `tab_dist_time` e
  `tab_dist_breakeven` cumprem (sessão `e5`, GPU e CPU em comandos separados); `tab_dist_time_measured` é só GPU (o
  `full_frames` não rodou em CPU).
- ✔ Custo amortizado de `afs` e `afM` identificado como soma de tempos medidos (marca † e notas de `tab_dist_time`).
- ✔ Cada cenário tem um parágrafo de plausibilidade física (relatório, Seção 3).
- ✔ O relatório diz o que não foi confirmado e o que não foi testado (relatório, Seção 5).
