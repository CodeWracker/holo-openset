# Caderno do executor "distância" (item d da instrução de 2026-11-15)

Só o executor "distância" escreve aqui. Instrução do orientador em `PROTOCOLO_CURVA.md` (item d); pré-registro do
responsável em `CADERNO_CURVA.md` (Q0, "d. Distância"), que manda. Os passos de 0,7 mm vêm do piloto
(`CADERNO_PILOTO_1MM.md`: P0 "Robustez a 0,7 mm", P1, R3, R4, P2-A). Entradas datadas com `date`.

## 2026-11-15, 08:18 — D0: rodada d1 preparada (0,9 e 1,1 mm, cinco modelos do piloto), nada gravado ainda

### O que foi lido e conferido antes de escrever código

- **Variação de distância por sessão.** `simulate like --like bench_1mm --set-physics z0=...` (como o `record_07`)
  sorteia a sessão como z_s = z0 (1 + 0,005 N(0, 1)) com o mesmo gerador da sessão (`scene.session`), então a
  distância de cada sessão é a do conjunto de 1,0 mm vezes z0 / 1,0 mm, exatamente; `frame_z_std`, `frame_z_walk` e
  `tilt_deg` são 0 no `bench_1mm`. Para 0,9 e 1,1 mm faço igual: só `z0=0.9e-3` / `z0=1.1e-3`.
- **O tamanho das letras não muda com z0**: o `FresnelLayout` usa `scale` guardado em `layout_params` do
  `physics.json` de `bench_1mm` (0,22792), que o `like` copia.
- **Faixa da recalibração.** `calibrate_alpha` com `extend = 12` (como a 0,7 mm): grade geométrica de 0,485 a 75,5 mm
  (passo relativo 5,70 %), refino linear entre os vizinhos do melhor ponto. 0,9 e 1,1 mm estão dentro (0,9 mm fica
  na parte estendida, abaixo de 0,944 mm; 1,1 mm na grade original).
- **Como o z07 foi conferido.** O caderno do piloto registra a conferência por escrito só para o `depth50`
  (anotações iguais a menos de `depth` e `z`, poeira igual). Para o z07 não achei registro além de "mesmas cenas,
  sementes, sessões, câmera e gravador; só z₀ muda" (S3) e de o `experiment robustness` exigir as mesmas caixas e
  classes. Por isso escrevi `scripts/exp_resolucao/distance_checks.py` com as conferências pedidas e rodei-o
  **primeiro no z07 e no z07_val existentes** (só leitura; saída no scratchpad, não em `results_exp_resolucao/`):
  - `physics.json`: só `physics.z0` (0,0007 contra 0,001) e as chaves `like`/`split` diferem;
  - anotações (6371 teste / 5711 validação), `metadata.csv` (800 / 700), `sessions.csv` (50) e `dust.csv`
    (3772 / 3374 linhas): todas as colunas iguais às do split de `bench_1mm`, a menos de `z`; z − profundidade
    (anotações), z de metadata e de sessions na razão 0,7 com desvio relativo máximo 1,4 × 10⁻¹³;
  - câmera (`camera(7, física, layout)`): PRNU igual, as 6 partículas de poeira da janela iguais;
  - quadros em branco: não idênticos aos de 1,0 mm (diferença máxima 1,875 níveis; nível médio igual a 10⁻⁴
    níveis). Esperado: o borrão do pinhole é calculado para a distância da amostra (P1), e a poeira da janela é
    vista através dele. Fica registrado como descritivo;
  - uma imagem refeita da semente (a primeira da primeira sessão do split: 0 no teste, 2900 na validação), gravada
    como `generate` grava, com a física do conjunto: **idêntica à armazenada** (diferença máxima 0 níveis), e
    diferente da mesma imagem a 1,0 mm (rms 3,6 e 6,3 níveis).
  O mesmo script roda nos conjuntos novos.

### Código (nada em `holo_openset/` mudou)

- `scripts/exp_resolucao/distance_tests.sh` (novo; `pilot_1mm.sh` não foi tocado, então o comportamento e os nomes
  de 0,7 mm não podem mudar): `ZROB=09|11 [REP=1..5] bash scripts/exp_resolucao/distance_tests.sh 5 <passo>`, passos
  `record`, `checks`, `robust_a`, `robust_b`, `rep` (robust_a + robust_b da repetição), `table`. `ZROB=07` é
  recusado. Os comandos são os do `record_07`, `robust_a`, `robust_b` do piloto, trocando `z07` por `z09`/`z11` e
  `0.7e-3` por `0.9e-3`/`1.1e-3`. Logs `logs/exp_resolucao/dist_<passo>_z<ZROB>[_r<REP>].log`.
- **Desvio de nome, para não reescrever arquivo de 0,7 mm:** as linhas novas vão para
  `results_exp_resolucao/robustness_bench_1mm_dist.csv`, não para `robustness_bench_1mm.csv`. O `save` do
  `experiment robustness` regrava o csv inteiro ao acrescentar linhas (lê, concatena, escreve), o que reescreveria
  as linhas de 0,7 mm. O `robust_a` novo também não pede a variante `base` (as linhas de 1,0 mm já existem e são
  copiadas). Recalibração em `recal_bench_1mm_z09.json` e `recal_bench_1mm_z11.json`.
- `scripts/exp_resolucao/distance_checks.py` (acima) → `results_exp_resolucao/distance_checks_z09.json`, `_z11.json`.
- Antes de rodar, guardei md5 (csv e json) e tamanho/mtime (npy) de todos os arquivos de 0,7 mm e de 1,0 mm que entram
  na tabela, para conferir no fim que nada foi tocado.
- Commits `5ad8e3f` (scripts do passo e das conferências), `9cdeddb` (script da tabela). O script da tabela foi
  conferido antes de haver linhas novas, numa cópia de `robustness_bench_1mm.csv` no scratchpad, só com 0,7 e 1,0 mm:
  reproduz as médias / mín. / máx. de `pilot_five_reps_robustness.csv`.

## 2026-11-15, 08:34 — D1: rodada d1 rodada (gravação, conferência, como está, recalibrado, tabela) (execução)

GPU 5 (compartilhada com o executor "densidade"), um processo meu por vez, 4 threads (env.sh e linha de comando),
pressão de CPU `some avg10` 0,00 em todas as leituras, 2–8 threads prontas no container durante a gravação.

| passo | comando | início–fim | parede |
|---|---|---|---|
| record z09 | `ZROB=09 bash scripts/exp_resolucao/distance_tests.sh 5 record` (tmux `res_dist_rec`) | 08:18:39–08:22:55 | 256 s |
| record z11 | `ZROB=11 ... record` (mesma sessão tmux, em seguida) | 08:22:55–08:27:14 | 259 s |
| checks | `ZROB=09 ... checks`, `ZROB=11 ... checks` | 08:27:26–08:27:36 | 5 + 5 s |
| rep | `for Z in 09 11; do for R in 1 2 3 4 5; do ZROB=$Z REP=$R ... rep; done; done` (tmux `res_dist_eval`) | 08:27:46–08:33:41 | 355 s |
| table | `bash scripts/exp_resolucao/distance_tests.sh 5 table` (CPU) | 08:33:56 | 0 s |

Cada passo rodou uma vez (uma linha `start` por log); nenhum erro, nenhum "missing" nos logs. O `rep` de r1 levou
66 s (z09) e 58 s (z11), com as reconstruções e a recalibração; os outros 27–33 s. Disco: `z09` e `z11` 323 MB cada
antes das reconstruções (+ 3 × 0,98 GB de caches `rec_z0*.npy` cada), `z09_val` e `z11_val` 283 MB.

### Conferência dos conjuntos (`results_exp_resolucao/distance_checks_z09.json`, `_z11.json`)

Nos quatro conjuntos, o mesmo resultado do z07: `physics.json` difere só em `physics.z0` (0,0009 / 0,0011 contra
0,001) e em `like`/`split`; anotações (6371 / 5711 linhas), metadata (800 / 700), sessions (50) e poeira (3772 / 3374)
iguais às de `bench_1mm` em todas as colunas a menos de `z`; z − profundidade, z de metadata e de sessions na razão
0,9 e 1,1 com desvio relativo máximo ≤ 1,04 × 10⁻¹³; câmera igual (PRNU, as 6 partículas da janela); quadros em
branco não idênticos aos de 1,0 mm (diferença máxima 1,375 e 1,875 níveis, nível médio igual a 3 × 10⁻⁵), como no
z07; a imagem refeita da semente (0 no teste, 2900 na validação) é **idêntica** à armazenada nos quatro (diferença
máxima 0) e difere da mesma imagem a 1,0 mm (rms 2,66 / 5,04 níveis a 0,9 mm, 2,63 / 4,98 a 1,1 mm). Distância das
sessões: teste 0,8903–0,9103 mm (média 0,8991) e 1,0882–1,1125 mm (média 1,0989); validação média 0,9015 e 1,1018.

### Recalibração (32 hologramas de validação, os mesmos ids do z07; `recal_bench_1mm_z09.json`, `_z11.json`)

- Os ids sorteados (semente 0 sobre o split de validação) são os mesmos do z07 (o split é o mesmo), e a calibração
  de referência a 1,0 mm deu exatamente o mesmo α_ref do z07 (0,0010615955941839486 → 1,00263 mm).
- z verdadeiro = média das distâncias de sessão desses 32 hologramas (metadata do conjunto):

| distância | z verdadeiro | z literal (achado) | literal − verdadeiro | z por razão | razão − verdadeiro |
|---|---|---|---|---|---|
| 0,7 mm (copiado) | 0,70260 mm | 0,70092 mm | −0,00168 mm (−0,24 %) | 0,69908 mm | −0,00352 mm |
| 0,9 mm | 0,90335 mm | 0,90231 mm | −0,00104 mm (−0,12 %) | 0,89994 mm | −0,00341 mm |
| 1,1 mm | 1,10409 mm | 1,10479 mm | +0,00070 mm (+0,06 %) | 1,10189 mm | −0,00220 mm |
| (1,0 mm, referência) | 1,00372 mm | 1,00263 mm | −0,00109 mm | — | — |

  A variante por razão multiplica o z₀ **nominal** de 1,0 mm (não o verdadeiro dos 32, 1,00372) pela razão, por isso
  fica 0,2–0,35 % abaixo do verdadeiro em todas as distâncias.
- α do prop: literal 0,0009554 (0,9 mm) e 0,0011698 (1,1 mm) em todas as repetições; por razão, α treinado ×
  0,89994 / 1,10189: 0,0009260–0,0009300 e 0,0011339–0,0011387.

### Resultados (teste lido uma vez por linha; `results_exp_resolucao/distance_tests.csv`, por repetição em
`distance_tests_rows.csv`; linhas cruas em `robustness_bench_1mm_dist.csv`; 0,7 e 1,0 mm copiados de
`robustness_bench_1mm.csv`)

F1 open-set, média / mín. / máx. das cinco repetições:

| fluxo, condição | 0,7 mm | 0,9 mm | 1,0 mm | 1,1 mm |
|---|---|---|---|---|
| crops, como está | 0,9107 / 0,8965 / 0,9241 | 0,9483 / 0,9351 / 0,9549 | 0,9382 / 0,9283 / 0,9451 | 0,9246 / 0,9198 / 0,9306 |
| camada, como está | 0,0150 / 0,0146 / 0,0153 | 0,2208 / 0,1722 / 0,2567 | 0,9768 / 0,9736 / 0,9800 | 0,0811 / 0,0667 / 0,1088 |
| camada, recal. literal | 0,5095 / 0,4558 / 0,5453 | 0,5325 / 0,4932 / 0,5754 | — | 0,5598 / 0,5365 / 0,5905 |
| camada, recal. razão | 0,9137 / 0,8988 / 0,9296 | 0,9286 / 0,9079 / 0,9420 | — | 0,9149 / 0,8988 / 0,9354 |
| reconstrução, como está | 0,0150 / 0,0146 / 0,0153 | 0,1377 / 0,0931 / 0,1751 | 0,9789 / 0,9765 / 0,9806 | 0,1596 / 0,1325 / 0,1979 |
| reconstrução, recal. literal | 0,9629 / 0,9562 / 0,9683 | 0,9774 / 0,9736 / 0,9799 | — | 0,9732 / 0,9694 / 0,9772 |
| reconstrução, recal. razão | 0,9639 / 0,9577 / 0,9693 | 0,9794 / 0,9765 / 0,9816 | — | 0,9758 / 0,9723 / 0,9785 |

Rejeição das não vistas, média / mín. / máx.:

| fluxo, condição | 0,7 mm | 0,9 mm | 1,0 mm | 1,1 mm |
|---|---|---|---|---|
| crops, como está | 0,7428 / 0,6087 / 0,8375 | 0,7353 / 0,6143 / 0,8313 | 0,7299 / 0,6224 / 0,8288 | 0,7300 / 0,6514 / 0,8231 |
| camada, como está | 1,0000 (todas) | 1,0000 (todas) | 0,9975 / 0,9930 / 1,0000 | 1,0000 (todas) |
| camada, recal. literal | 0,9988 / 0,9938 / 1,0000 | 0,9995 / 0,9984 / 1,0000 | — | 0,9987 / 0,9953 / 1,0000 |
| camada, recal. razão | 0,9963 / 0,9821 / 1,0000 | 0,9975 / 0,9907 / 1,0000 | — | 0,9974 / 0,9936 / 1,0000 |
| reconstrução, como está | 1,0000 (todas) | 1,0000 (todas) | 0,9981 / 0,9914 / 1,0000 | 1,0000 (todas) |
| reconstrução, recal. literal | 0,9967 / 0,9852 / 1,0000 | 0,9978 / 0,9899 / 1,0000 | — | 0,9984 / 0,9938 / 1,0000 |
| reconstrução, recal. razão | 0,9964 / 0,9844 / 1,0000 | 0,9980 / 0,9907 / 1,0000 | — | 0,9983 / 0,9938 / 1,0000 |

Perda sem recalibrar (como está − 1,0 mm, F1, média / mín. / máx.): crops −0,0275 / +0,0101 / −0,0136 a 0,7 / 0,9 /
1,1 mm (0,9 mm: +0,0068 a +0,0127, positiva nas cinco); camada −0,9618 / −0,7560 / −0,8957; reconstrução −0,9639 /
−0,8412 / −0,8193. O que a recalibração por razão recupera (recal. − como está, F1): camada +0,8987 / +0,7078 /
+0,8338; reconstrução +0,9489 / +0,8417 / +0,8163.

Reconstrução recalibrada − camada recalibrada por razão, F1, por repetição (r1 … r5):

| distância | reconstrução por razão − camada por razão | reconstrução literal − camada por razão |
|---|---|---|
| 0,7 mm | 0,0452 / 0,0546 / 0,0516 / 0,0340 / 0,0656 (média 0,0502) | 0,0436 / 0,0534 / 0,0506 / 0,0322 / 0,0665 (0,0493) |
| 0,9 mm | 0,0530 / 0,0449 / 0,0475 / 0,0365 / 0,0721 (0,0508) | 0,0501 / 0,0435 / 0,0458 / 0,0336 / 0,0710 (0,0488) |
| 1,1 mm | 0,0554 / 0,0616 / 0,0664 / 0,0415 / 0,0797 (0,0609) | 0,0526 / 0,0583 / 0,0647 / 0,0376 / 0,0785 (0,0583) |

Em rejeição a mesma diferença fica entre −0,0031 e +0,0064.

### Conferências depois de rodar

- md5 de `robustness_bench_1mm.csv`, `recal_bench_1mm_z07.json`, `pilot_five_reps*.csv`, dos 15 json de
  `eval/bench_1mm/` e dos csv/json de `z07` e `z07_val` iguais aos de antes; tamanho e mtime dos npy de `z07*`
  iguais. Nenhuma linha nem arquivo de 0,7 mm foi tocado.
- As linhas de 1,0 mm (`base` de `robustness_bench_1mm.csv`) são as dos json de `eval/bench_1mm/` (diferença
  ≤ 1,1 × 10⁻¹⁶; o script da tabela confere isso a cada execução).
- O `rec_z0` "como está" foi reconstruído a 1,0000 mm, o literal a 0,9023 / 1,1048 mm e o por razão a 0,8999 /
  1,1019 mm (linhas "back-propagation at" dos logs).

### Desvios

1. Linhas novas em `robustness_bench_1mm_dist.csv` em vez de `robustness_bench_1mm.csv` (D0), para não regravar o
   arquivo que tem as linhas de 0,7 mm. O conteúdo das linhas é o mesmo que o `experiment robustness` escreveria lá.
2. O `robust_a` das distâncias novas não pede a variante `base` (a 0,7 mm pedia, e gravava de novo as linhas de
   1,0 mm em cada repetição): as de 1,0 mm são copiadas.
3. A conferência do z07 que eu rodei (D0) não estava no caderno do piloto por escrito; os critérios são os que o
   responsável listou. O json dela ficou no scratchpad (não em `results_exp_resolucao/`), por não ser deste item.

### O que parece estranho ou merece olhar (para o responsável; leitura minha, posterior aos números)

1. **±10 % já derruba quase tudo sem recalibrar.** A 0,9 e 1,1 mm a camada e a reconstrução "como estão" ficam com
   F1 0,08–0,26 e rejeição 1,000 nas cinco repetições: rejeitam quase tudo (acurácia das conhecidas, médias,
   0,04–0,13), mas a acurácia em conjunto fechado (médias) continua 0,76–0,92. O que se perde primeiro é o limiar (os escores caem abaixo do
   limiar de 1,0 mm), não a separação das classes. A 0,7 mm a fechada também caiu (0,19–0,20).
2. **Assimetria da camada:** como está, a camada vai pior a 1,1 mm (0,081) que a 0,9 mm (0,221). O α treinado
   corresponde a 0,972–0,976 mm (P2-A), então a camada está a −7,8 % de 0,9 mm e a +12,6 % de 1,1 mm. A reconstrução
   (focada em 1,0 mm) é quase simétrica (0,138 e 0,160).
3. **Crops a 0,9 mm melhores que a 1,0 mm** em F1 (+0,0068 a +0,0127, as cinco repetições), e piores a 0,7 e
   1,1 mm. Não é monótono na distância. Não tenho explicação; é a mesma galeria e o mesmo limiar de 1,0 mm.
4. **A literal da camada fica em 0,51–0,56 em todas as distâncias**, quase igual a 0,7, 0,9 e 1,1 mm: o que ela perde
   não depende de quanto a distância mudou, e sim de ela desfazer o deslocamento de −2,1 a −2,8 % que o treino deu ao
   α (P2-A). A por razão recupera para 0,91–0,93.
5. **Camada por razão contra reconstrução recalibrada: 0,050 / 0,051 / 0,061 de F1** (médias a 0,7 / 0,9 / 1,1 mm;
   todas as 15 diferenças por repetição entre +0,034 e +0,080, nenhuma negativa), enquanto a 1,0 mm as duas empatam
   (+0,0021 de média, P2-A). A reconstrução recalibrada volta ao nível de 1,0 mm já a 0,9 e 1,1 mm (0,979 e 0,976
   contra 0,979); a camada por razão não (0,929 e 0,915 contra 0,977), mesmo com só 10 % de mudança. A perda da
   camada aparece como acurácia das conhecidas (0,86–0,88 contra 0,96 a 1,0 mm), com a fechada intacta (0,995–0,996).
   Hipótese, não testada: a camada aprendeu, além de α, um filtro radial ajustado a 1,0 mm, que o reescalonamento de α
   não corrige; a galeria continua embutida a 1,0 mm.
6. Na reconstrução, a distância por razão (0,2–0,35 % abaixo do verdadeiro) dá F1 levemente maior que a literal (mais
   perto do verdadeiro) em 14 das 15 comparações (−0,0009 em r5 a 0,7 mm; as outras de +0,0010 a +0,0039). Pode ser que o modelo de `rec_z0` tenha sido treinado
   na reconstrução a 1,0 mm nominal com as sessões a ±0,5 %, e a razão reproduza essa relação; é uma diferença
   pequena.

## 2026-11-15, 08:55 — D2-prep: fase 2 preparada (rodada d2 e linhas de profundidade), esperando o `curve_u50_L008`

Pedido do responsável (mensagem da fase 2) e Q1 do `CADERNO_CURVA.md` (lido): lei padrão uniforme nos 50 µm do
canal (±25 µm; campo `depth_uniform`, implementado pelo executor "densidade", commit `777f68e`); nível esparso
`curve_u50_L008` com r1–r5. Um laço em segundo plano espera `results_exp_resolucao/curve_u50_L008_ready.json`. Eu só
leio o conjunto e os modelos dele.

### Código (nada em `holo_openset/` mudou; commits `8477d7d`, `c6b0a50`)

- `distance_tests.sh` ganhou `FAM=pilot|u50` (padrão `pilot` = d1, sem mudança: com `FAM=pilot` os nomes, os comandos
  e os logs são os mesmos, e a tabela da d1 sai igual byte a byte; conferido numa cópia no scratchpad).
  `FAM=u50 ZROB=07|09|11`: `--like curve_u50_L008` → `data/curve_u50_robust/z<ZZ>[_val]`, linhas em
  `robustness_curve_u50_L008_dist.csv`, `recal_curve_u50_L008_z<ZZ>.json`, `distance_checks_u50_z<ZZ>.json`, logs
  `dist_u50_*`. Na família padrão o 0,7 mm é gravado (não existe).
- `distance_checks.py` passou a escrever a lei de profundidade (todos os campos com `depth` no nome) do conjunto e se
  ela é igual à do `--ref`. Os json da d1 não foram refeitos.
- `distance_tests.py --family u50` → `distance_tests_u50.csv` e `_rows.csv`; a linha de 1,0 mm vem dos json de
  `eval/curve_u50_L008/`. Exercitado com entradas falsas no scratchpad (os números da d1 no lugar dos da família):
  sai igual à tabela da d1.
- `depth_tests.sh` (novo): `flat_on_u50` (i), `u50_on_flat` (ii), `u50_on_wide` (iii), `rep`, `table`; o mesmo
  `experiment robustness --variants-root . --variants <conjunto>` que o `depth_training.sh cross` do piloto usou.
  Linhas em `robustness_depth_from_bench_1mm.csv` (i) e `robustness_depth_from_curve_u50_L008.csv` (ii, iii).
- `depth_tests.py` → `depth_tests.csv` / `_rows.csv`: as linhas novas, a avaliação própria do `curve_u50_L008`
  (u50 → u50), e as que existem copiadas como estão: plano → plano e plano → lei larga de
  `pilot_five_reps_robustness.csv` (5 repetições, 4 casas), lei larga → lei larga e lei larga → plano de
  `depth_training.csv` (r1, 4 casas). Diferenças pareadas por repetição: plano → u50 − u50 → u50, plano → u50 −
  plano → plano, u50 → plano − u50 → u50, u50 → lei larga − u50 → u50.

### Escolhas declaradas antes de rodar

1. **Teste da lei larga em (iii):** `bench_1mm_robust/depth50`. Conferi que os 800 hologramas e as anotações são
   idênticos aos do split de teste de `bench_1mm_depth50` (os dois são "o mesmo teste"), e ele já tem o `rec_z0.npy`
   a 1,0 mm.
2. **Validação regravada:** como na d1 (e no `record_07`), o split de validação inteiro (700) é regravado em cada
   distância; a recalibração usa 32 deles (semente 0). O pedido fala em "os 32 hologramas"; gravar o split inteiro é
   o que o `simulate like` faz e mantém a d2 igual à d1. Só os 32 entram em algum número.

## 2026-11-15, 09:58 — D2: rodada d2 e linhas de profundidade rodadas (execução)

`curve_u50_L008_ready.json` apareceu às 09:25:43 (commits do executor "densidade": lei `a25df48`, avaliações
`a35c1e3`). O `physics.json` do `curve_u50_L008` difere do de `bench_1mm` só em `depth_uniform = 2,5e-5` (o
`depth_std`/`depth_max` de 2,6/7,8 µm ficam lá, sem uso); o `rec_z0` dele é a 1,0 mm (`autofocus.csv`, `z_af`
0,001). Antes de rodar, guardei md5 (csv, json, pt) e tamanho/mtime (npy) do `curve_u50_L008`, dos seus modelos e
avaliações, e de tudo da d1 e do piloto que entra nas tabelas.

GPU 5 (o executor "densidade" gravava L154 e L343 ao mesmo tempo; 9,9–10,9 GB usados na GPU 5), um processo meu por
vez, 4 threads; `some avg10` 0,00 em todas as leituras; 4–20 threads prontas no container (as minhas ≈ 4).

| passo | comando | início–fim | parede |
|---|---|---|---|
| record | `for Z in 07 09 11; do FAM=u50 ZROB=$Z bash scripts/exp_resolucao/distance_tests.sh 5 record; done` (tmux `res_dist_u50_rec`) | 09:26:08–09:39:56 | 275 + 276 + 277 s |
| checks | `FAM=u50 ZROB=07/09/11 ... checks` | 09:40:23–09:40:37 | 4–5 s cada |
| rep | `for Z in 07 09 11; do for R in 1..5; do FAM=u50 ZROB=$Z REP=$R ... rep; done; done` (tmux `res_dist_u50_eval`) | 09:40:46–09:53:36 | 770 s |
| profundidade | `for R in 1..5; do REP=$R bash scripts/exp_resolucao/depth_tests.sh 5 rep; done` (tmux `res_dist_depth`) | 09:54:17–09:57:26 | 189 s |
| tabelas | `FAM=u50 ... distance_tests.sh 5 table`; `depth_tests.sh 5 table` (CPU) | 09:57 | — |

Cada passo rodou uma vez (uma linha `start` por log), sem erro nem "missing". Commits `89740c0` (conferências),
`31181c6` (d2), `a4e80ab` (profundidade). Depois de rodar: md5 e mtime de tudo o que foi guardado continuam iguais
(nada do `curve_u50_L008`, dos seus modelos, da d1 nem do piloto foi tocado).

### Conferência dos conjuntos (`distance_checks_u50_z07.json`, `_z09.json`, `_z11.json`)

Os seis (`curve_u50_robust/z07`, `z07_val`, `z09`, `z09_val`, `z11`, `z11_val`) passam em tudo, como na d1:
`physics.json` difere do `curve_u50_L008` só em `z0` (e `like`/`split`); **a lei de profundidade é a do conjunto**
(`depth_uniform = 2,5e-5` nos seis; `depth_law_equal_ref` verdadeiro); anotações (6371 / 5711), metadata, sessions
e poeira (3772 / 3374) iguais a menos de z, z na razão exata (desvio ≤ 1,4 × 10⁻¹³); câmera igual; quadros em branco
até 1,375–1,875 níveis diferentes, como na d1; a imagem refeita da semente (0 e 2900) é idêntica à armazenada
(diferença 0) e difere da mesma imagem a 1,0 mm (rms 2,63–6,35 níveis). Distâncias das sessões iguais às da d1 (os
sorteios são os mesmos).

### Recalibração (`recal_curve_u50_L008_z07.json`, `_z09.json`, `_z11.json`; os mesmos 32 ids da d1)

| distância | z verdadeiro | achado (literal) | literal − verdadeiro | por razão | razão − verdadeiro |
|---|---|---|---|---|---|
| 0,7 mm | 0,70260 mm | 0,69893 mm | −0,00367 mm (−0,52 %) | 0,69710 mm | −0,00551 mm |
| 0,9 mm | 0,90335 mm | 0,90231 mm | −0,00104 mm | 0,89994 mm | −0,00341 mm |
| 1,1 mm | 1,10409 mm | 1,10479 mm | +0,00070 mm | 1,10189 mm | −0,00220 mm |
| (1,0 mm, referência) | 1,00372 mm | 1,00263 mm | −0,00109 mm | — | — |

A 0,9 e 1,1 mm e na referência a 1,0 mm, o α achado é **idêntico, bit a bit, ao da d1** (amostra plana). Conferi a
explicação: `calibrate_alpha` devolve um ponto de uma grade discreta (o refino tem passo de 0,27 % de α), e os
cinco valores estão exatamente nela; com a lei uniforme o ponto mais nítido caiu no mesmo ponto da grade, menos a
0,7 mm, onde caiu um passo abaixo (0,0007400 contra 0,0007421). α treinado dos cinco modelos `prop` do
`curve_u50_L008`: 0,0010248 / 0,0010195 / 0,0010196 / 0,0010198 / 0,0010236 (r1…r5) = 0,968 / 0,963 / 0,963 /
0,963 / 0,967 mm (os do piloto: 0,972–0,976 mm).

### d2: resultados (`results_exp_resolucao/distance_tests_u50.csv`, por repetição em `distance_tests_u50_rows.csv`;
linhas cruas em `robustness_curve_u50_L008_dist.csv`; 1,0 mm copiado de `eval/curve_u50_L008/<fluxo>_r<n>.json`)

F1 open-set, média / mín. / máx.:

| fluxo, condição | 0,7 mm | 0,9 mm | 1,0 mm | 1,1 mm |
|---|---|---|---|---|
| crops, como está | 0,9107 / 0,8921 / 0,9260 | 0,9459 / 0,9343 / 0,9562 | 0,9368 / 0,9251 / 0,9466 | 0,9233 / 0,9150 / 0,9350 |
| camada, como está | 0,0150 / 0,0146 / 0,0153 | 0,4261 / 0,3135 / 0,4946 | 0,9748 / 0,9693 / 0,9775 | 0,2893 / 0,2554 / 0,3259 |
| camada, recal. literal | 0,7334 / 0,6989 / 0,7635 | 0,7310 / 0,6831 / 0,7588 | — | 0,6697 / 0,6384 / 0,7097 |
| camada, recal. razão | 0,9190 / 0,9057 / 0,9326 | 0,9325 / 0,9265 / 0,9405 | — | 0,9303 / 0,9264 / 0,9406 |
| reconstrução, como está | 0,0150 / 0,0146 / 0,0153 | 0,2490 / 0,2261 / 0,2652 | 0,9770 / 0,9737 / 0,9796 | 0,3029 / 0,2678 / 0,3538 |
| reconstrução, recal. literal | 0,9645 / 0,9611 / 0,9737 | 0,9772 / 0,9720 / 0,9810 | — | 0,9731 / 0,9691 / 0,9781 |
| reconstrução, recal. razão | 0,9641 / 0,9606 / 0,9747 | 0,9783 / 0,9746 / 0,9814 | — | 0,9748 / 0,9701 / 0,9791 |

Rejeição das não vistas, média / mín. / máx.:

| fluxo, condição | 0,7 mm | 0,9 mm | 1,0 mm | 1,1 mm |
|---|---|---|---|---|
| crops, como está | 0,7369 / 0,6151 / 0,8673 | 0,7186 / 0,6087 / 0,8321 | 0,7140 / 0,6135 / 0,8272 | 0,7212 / 0,6401 / 0,8460 |
| camada, como está | 1,0000 (todas) | 0,9966 / 0,9902 / 1,0000 | 0,9829 / 0,9370 / 1,0000 | 0,9935 / 0,9681 / 1,0000 |
| camada, recal. literal | 0,9878 / 0,9689 / 1,0000 | 0,9909 / 0,9742 / 1,0000 | — | 0,9838 / 0,9471 / 1,0000 |
| camada, recal. razão | 0,9786 / 0,9215 / 1,0000 | 0,9818 / 0,9331 / 1,0000 | — | 0,9779 / 0,9160 / 1,0000 |
| reconstrução, como está | 1,0000 (todas) | 0,9998 / 0,9992 / 1,0000 | 0,9961 / 0,9876 / 1,0000 | 0,9986 / 0,9938 / 1,0000 |
| reconstrução, recal. literal | 0,9970 / 0,9868 / 1,0000 | 0,9967 / 0,9899 / 1,0000 | — | 0,9965 / 0,9907 / 1,0000 |
| reconstrução, recal. razão | 0,9973 / 0,9883 / 1,0000 | 0,9962 / 0,9876 / 1,0000 | — | 0,9965 / 0,9899 / 1,0000 |

Perda sem recalibrar (como está − 1,0 mm, F1), por repetição r1…r5:

| distância | crops | camada | reconstrução |
|---|---|---|---|
| 0,7 mm | −0,0330 / −0,0204 / −0,0366 / −0,0207 / −0,0199 | −0,9598 / −0,9624 / −0,9541 / −0,9629 / −0,9597 | −0,9589 / −0,9636 / −0,9643 / −0,9607 / −0,9626 |
| 0,9 mm | +0,0092 / +0,0121 / +0,0060 / +0,0096 / +0,0083 | −0,5759 / −0,4830 / −0,5026 / −0,5204 / −0,6613 | −0,7476 / −0,7171 / −0,7146 / −0,7483 / −0,7125 |
| 1,1 mm | −0,0100 / −0,0152 / −0,0137 / −0,0116 / −0,0172 | −0,6740 / −0,6936 / −0,6888 / −0,6516 / −0,7194 | −0,7059 / −0,6878 / −0,6594 / −0,6936 / −0,6238 |

Médias: crops −0,0261 / +0,0090 / −0,0136; camada −0,9598 / −0,5486 / −0,6855; reconstrução −0,9620 / −0,7280 /
−0,6741 (0,7 / 0,9 / 1,1 mm). O que a recalibração por razão recupera (F1, média): camada +0,9040 / +0,5063 /
+0,6410; reconstrução +0,9492 / +0,7293 / +0,6719.

Reconstrução recalibrada − camada recalibrada por razão, F1, r1…r5:

| distância | reconstrução por razão − camada por razão | reconstrução literal − camada por razão |
|---|---|---|
| 0,7 mm | 0,0448 / 0,0338 / 0,0420 / 0,0471 / 0,0580 (média 0,0451) | 0,0450 / 0,0348 / 0,0410 / 0,0476 / 0,0589 (0,0455) |
| 0,9 mm | 0,0481 / 0,0399 / 0,0481 / 0,0398 / 0,0534 (0,0459) | 0,0454 / 0,0385 / 0,0477 / 0,0394 / 0,0524 (0,0447) |
| 1,1 mm | 0,0436 / 0,0377 / 0,0510 / 0,0420 / 0,0481 (0,0445) | 0,0427 / 0,0354 / 0,0500 / 0,0401 / 0,0459 (0,0428) |

Em rejeição (reconstrução por razão − camada por razão): 0,0233 / 0 / 0,0669 / 0,0033 / 0 a 0,7 mm; 0,0121 / 0 /
0,0544 / 0,0057 / 0 a 0,9 mm; 0,0161 / −0,0008 / 0,0739 / 0,0057 / −0,0016 a 1,1 mm (r3 sempre a maior).

### Linhas de profundidade (`results_exp_resolucao/depth_tests.csv`, por repetição em `depth_tests_rows.csv`)

Plano = `bench_1mm` (2,6 µm); u50 = `curve_u50_L008` (uniforme ±25 µm); larga = normal 50 µm cortada em 150 µm
(`bench_1mm_robust/depth50`). Modelos, galeria e limiar do conjunto de treino. F1, média / mín. / máx. (n
repetições):

| treinado → testado | n | crops | camada | reconstrução | origem |
|---|---|---|---|---|---|
| plano → plano | 5 | 0,9382 / 0,9283 / 0,9451 | 0,9768 / 0,9736 / 0,9800 | 0,9789 / 0,9765 / 0,9806 | copiado, `pilot_five_reps_robustness.csv` |
| plano → u50 (i) | 5 | 0,9386 / 0,9288 / 0,9463 | 0,9578 / 0,9553 / 0,9646 | 0,9707 / 0,9647 / 0,9739 | novo |
| plano → larga | 5 | 0,9387 / 0,9288 / 0,9450 | 0,7842 / 0,7732 / 0,7997 | 0,8225 / 0,8014 / 0,8410 | copiado, `pilot_five_reps_robustness.csv` |
| u50 → plano (ii) | 5 | 0,9364 / 0,9247 / 0,9470 | 0,9794 / 0,9749 / 0,9816 | 0,9763 / 0,9708 / 0,9796 | novo |
| u50 → u50 | 5 | 0,9368 / 0,9251 / 0,9466 | 0,9748 / 0,9693 / 0,9775 | 0,9770 / 0,9737 / 0,9796 | copiado, `eval/curve_u50_L008` |
| u50 → larga (iii) | 5 | 0,9367 / 0,9247 / 0,9478 | 0,8584 / 0,8457 / 0,8631 | 0,8654 / 0,8505 / 0,8754 | novo |
| larga → plano | 1 | 0,9233 | 0,9836 | 0,9762 | copiado, `depth_training.csv` (r1) |
| larga → larga | 1 | 0,9239 | 0,9767 | 0,9751 | copiado, `depth_training.csv` (r1) |

Rejeição, média / mín. / máx.:

| treinado → testado | n | crops | camada | reconstrução |
|---|---|---|---|---|
| plano → plano | 5 | 0,7299 / 0,6224 / 0,8288 | 0,9975 / 0,9930 / 1,0000 | 0,9981 / 0,9914 / 1,0000 |
| plano → u50 (i) | 5 | 0,7299 / 0,6216 / 0,8305 | 0,9981 / 0,9953 / 1,0000 | 0,9981 / 0,9907 / 1,0000 |
| plano → larga | 5 | 0,7384 / 0,6296 / 0,8329 | 0,9986 / 0,9961 / 1,0000 | 0,9995 / 0,9984 / 1,0000 |
| u50 → plano (ii) | 5 | 0,7137 / 0,6111 / 0,8305 | 0,9816 / 0,9331 / 1,0000 | 0,9953 / 0,9860 / 1,0000 |
| u50 → u50 | 5 | 0,7140 / 0,6135 / 0,8272 | 0,9829 / 0,9370 / 1,0000 | 0,9961 / 0,9876 / 1,0000 |
| u50 → larga (iii) | 5 | 0,7183 / 0,6159 / 0,8362 | 0,9841 / 0,9479 / 1,0000 | 0,9961 / 0,9852 / 1,0000 |
| larga → plano | 1 | 0,5950 | 0,9968 | 1,0000 |
| larga → larga | 1 | 0,6047 | 0,9976 | 0,9944 |

Diferenças pareadas (mesma repetição e fluxo; F1, r1…r5):
- plano → u50 − plano → plano: camada −0,0217 / −0,0182 / −0,0201 / −0,0154 / −0,0195 (média −0,0190);
  reconstrução −0,0119 / −0,0101 / −0,0069 / −0,0058 / −0,0063 (−0,0082); crops −0,0003 a +0,0012.
- plano → u50 − u50 → u50 (treinar plano contra treinar na lei, no mesmo teste): camada −0,0194 / −0,0221 /
  −0,0125 / −0,0130 / −0,0180 (−0,0170); reconstrução −0,0091 / −0,0100 / −0,0059 / −0,0030 / −0,0037 (−0,0064).
- u50 → plano − u50 → u50: camada +0,0036 a +0,0056; reconstrução −0,0029 a +0,0009.
- u50 → larga − u50 → u50: camada −0,1166 / −0,1144 / −0,1072 / −0,1145 / −0,1291 (−0,1164); reconstrução
  −0,1232 / −0,1128 / −0,1073 / −0,1126 / −0,1023 (−0,1116).

### Desvios

1. Validação regravada inteira (700) em cada distância, como na d1; só os 32 da recalibração entram (D2-prep).
2. As linhas copiadas de `pilot_five_reps_robustness.csv` e `depth_training.csv` estão com as 4 casas desses
   arquivos (pedido: copiar sem recalcular); as linhas novas e a u50 → u50 têm precisão completa.
3. Nada além do pedido foi rodado.

### O que parece estranho ou merece olhar (leitura minha, depois dos números)

1. **Com a lei uniforme, a camada aguenta mais a distância errada sem recalibrar** (como está, a 0,9 / 1,1 mm:
   0,426 / 0,289 contra 0,221 / 0,081 na d1; a reconstrução 0,249 / 0,303 contra 0,138 / 0,160). Continua sendo uma
   queda de 0,5–0,7. A 0,7 mm as duas famílias rejeitam tudo (0,015).
2. **A camada literal fica bem melhor que na d1** (0,67–0,73 contra 0,51–0,56): o treino deslocou o α um pouco mais
   (α treinado a 0,963–0,968 mm, contra 0,972–0,976 mm no piloto; o α calibrado no início do treino desta família
   não foi lido por mim), mas o modelo treinado com 50 µm parece menos sensível a esse deslocamento.
   É leitura, não teste.
3. **A diferença reconstrução recalibrada − camada por razão continua ≈ 0,045 de F1 nas três distâncias** (15 de 15
   positivas, de +0,034 a +0,058), um pouco menor que na d1 (0,050–0,061). A 1,0 mm as duas empatam (u50 → u50:
   0,9770 − 0,9748 = +0,0022). Como na d1, a reconstrução recalibrada volta ao nível de 1,0 mm (0,978 / 0,975 contra
   0,977) e a camada não (0,933 / 0,930 contra 0,975).
4. **Rejeição da camada mais baixa e variável nesta família**, já a 1,0 mm (0,9829, mín. 0,9370 em r3, na avaliação
   do executor "densidade"), e na camada recalibrada (mín. 0,916–0,933, sempre r3). Na d1 a rejeição recalibrada
   ficava ≥ 0,982. A diferença de rejeição reconstrução − camada chega a 0,07 em r3.
5. **A recalibração a 0,7 mm caiu um passo da grade abaixo** com a lei uniforme (0,69893 mm, −0,52 % do
   verdadeiro, contra −0,24 % na d1); a 0,9, 1,1 e 1,0 mm achou exatamente o mesmo ponto da grade da d1. A resolução
   da grade (0,27 %) é do mesmo tamanho dos erros da recalibração, então a "distância achada" está quantizada.
6. **A perda do treino plano na lei padrão é pequena**: −0,019 (camada) e −0,008 (reconstrução) de F1, contra −0,19
   e −0,16 na lei larga. Os modelos treinados na lei padrão perdem −0,116 / −0,112 na lei larga, e não perdem nada no
   plano (camada +0,005). Os crops não mudam com a profundidade em nenhuma combinação (|Δ| ≤ 0,0043 de F1).
7. Crops a 0,9 mm de novo melhores que a 1,0 mm, nas cinco repetições (+0,006 a +0,012), como na d1.

## 2026-11-15, 13:45 — D3: teste J, o banco focal (`bank_jit`) a 0,9 e 1,1 mm sem recalibrar, r1 (execução)

Pré-registro: `CADERNO_CURVA.md`, Q2, seção J (commit `40a8956`), seguido como está escrito. Commits `e40badf`
(scripts) e `49cf2ae` (resultados).

### Receita (achada no pacote; nenhum hiperparâmetro mudou)

- `holo_openset/flows.py`: `'bank_jit': dict(mode='bank', fourier='learned', rec=None, train=dict(n_dist=5,
  alpha_jitter=0.05))`; `alpha_spread` fica no padrão de `train.train` (0,05): cinco propagações em α·(1 + {−5, −2,5,
  0, +2,5, +5} %), e a cada passo de treino todas as distâncias são multiplicadas por um fator uniforme em 1 ± 5 %.
  Resto da receita: o padrão de `train` (3000 passos, 16 imagens por passo, `lr_alpha` 1e-5, `lr_fourier` 0,3,
  semente 0), α inicial calibrado sem rótulo em 32 hologramas de treino. Não há seleção de modelo na receita (passos
  fixos); o limiar sai da validação de 1,0 mm, dentro do `evaluate`.
- Linha do paper (`holo_openset/pipeline.py`): `python -m holo_openset train --flow bank_jit --rep <r>`. Aqui, como em
  todo conjunto de 1 mm, `--no-aux`, e a grade da calibração estendida 12 passos, como na camada (`prop`) da família
  (`density_curve.sh`: `--alpha-extend 12`).
- Comando: `bash scripts/exp_resolucao/bank_jit_distance.sh 3 train` =
  `python -m holo_openset train --set curve_u50_L008 --flow bank_jit --rep 1 --no-aux --alpha-extend 12
  --device cuda:3 --threads 4`, tmux `res_dist_bankjit`, 13:43:11–13:44:13 (62 s), log
  `logs/exp_resolucao/bankjit_train.log`. Retomada: o `train` pula um modelo que já existe.

### GPU (desvio)

A instrução mandava a GPU 6. Este container só enxerga seis GPUs (`nvidia-smi -L`: 0–5; `torch.cuda.device_count()`
= 6; `CUDA_VISIBLE_DEVICES` vazio): a GPU 6 não existe aqui. Usei a **GPU 3** (1,7 GB usados, 0 % de uso antes de cada
job; 4 e 5 com os outros executores). Não muda nenhum número.

### α (mm, z = α (640 × 1,67 µm)² / (π λ))

- Calibrado (log do treino): α = 0,001056 → 0,997 mm (o log imprime 6 casas; é o mesmo sorteio de 32 imagens da
  camada de r1, cujo α calibrado é 0,001055729 → 0,99709 mm em `curve_alpha.csv`). Planos iniciais ≈ 0,947 / 0,972 /
  0,997 / 1,022 / 1,047 mm.
- Depois do treino (checkpoint `models_exp_resolucao/curve_u50_L008/bank_jit_r1.pt`): α = 0,0010268 / 0,0010319 /
  0,0010429 / 0,0010709 / 0,0010892 → **0,9698 / 0,9746 / 0,9850 / 1,0114 / 1,0287 mm**. O banco encolheu: de ±5 % em
  torno de 0,997 mm (0,100 mm de largura) para −1,5 / +4,4 % em torno de 0,985 mm (0,059 mm de largura).

### Avaliação, como está (modelo, galeria e limiar de 1,0 mm; cada teste lido uma vez)

- 1,0 mm: `bank_jit_distance.sh 3 evaluate` = `evaluate --set curve_u50_L008 --flow bank_jit --rep 1` →
  `results_exp_resolucao/eval/curve_u50_L008/bank_jit_r1.json` (13:44:26, 6 s).
- 0,9 e 1,1 mm: `... shifted` = `experiment robustness --set curve_u50_L008 --variants-root curve_u50_robust
  --variants z09 z11 --flows bank_jit --rep 1 --out robustness_curve_u50_L008_bank_jit` (o procedimento das linhas
  "como está" da d2) (13:44:32, 6 s).
- 0,7 mm (estresse, fora da regra): `... stress`, a mesma linha com `--variants z07` (13:44:38, 6 s).
- Tabela: `... table` → `results_exp_resolucao/bank_jit_distance.csv` (`scripts/exp_resolucao/bank_jit_distance.py`).

### Resultados (r1; `bank_jit_distance.csv`)

| distância | banco, como está: F1 / rejeição / fechado / conhecidas | crops como está F1 / rej. | camada como está | reconstrução como está | camada recal. razão | reconstrução recal. razão | reconstrução recal. literal |
|---|---|---|---|---|---|---|---|
| 1,0 mm | 0,9808 / 0,9992 / 0,9963 / 0,9671 | 0,9251 / 0,6135 | 0,9747 / 0,9799 | 0,9737 / 0,9952 | — | — | — |
| 0,9 mm | 0,6503 / 0,9936 / 0,9719 / 0,5059 | 0,9343 / 0,6087 | 0,3988 / 0,9952 | 0,2261 / 0,9992 | 0,9265 / 0,9823 | 0,9746 / 0,9944 | 0,9720 / 0,9944 |
| 1,1 mm | 0,6779 / 0,9968 / 0,9731 / 0,5297 | 0,9150 / 0,6401 | 0,3007 / 0,9992 | 0,2678 / 0,9992 | 0,9264 / 0,9791 | 0,9701 / 0,9952 | 0,9691 / 0,9944 |
| 0,7 mm (estresse) | 0,0148 / 1,0000 / 0,1973 / 0,0000 | 0,8921 / 0,6151 | 0,0148 / 1,0000 | 0,0148 / 1,0000 | 0,9161 / 0,9750 | 0,9609 / 0,9984 | 0,9611 / 0,9984 |

As linhas ao lado são as de r1 que já estavam em arquivo (1,0 mm: `eval/curve_u50_L008/<fluxo>_r1.json`; as outras:
`robustness_curve_u50_L008_dist.csv`, d2).

**Regra "aguenta" (Q2), aplicada mecanicamente** (banco − ele próprio a 1,0 mm):
- 0,9 mm: F1 −0,3305, rejeição −0,0056 → **não aguenta** (a queda de F1 passa de 0,10).
- 1,1 mm: F1 −0,3029, rejeição −0,0024 → **não aguenta**.
- **O banco não aguenta a mudança de distância de 10 %** (r1, descritivo). A 0,7 mm (fora da regra): F1 −0,9660.

Banco como está − reconstrução recalibrada (F1 / rejeição): por razão −0,3243 / −0,0008 (0,9 mm) e −0,2921 / +0,0016
(1,1 mm); literal −0,3216 / −0,0008 e −0,2912 / +0,0024. Preço a 1,0 mm (banco − camada / banco − reconstrução, F1):
**+0,0061 / +0,0071** (rejeição +0,0193 / +0,0040): em r1 o banco é um pouco melhor que as duas a 1,0 mm.

### O que pareceu estranho ou merece olhar (leitura minha)

1. O banco não aguenta pela regra, mas cai bem menos que a camada e a reconstrução sem recalibrar: F1 0,650 / 0,678
   contra 0,399 / 0,301 (camada) e 0,226 / 0,268 (reconstrução) a 0,9 / 1,1 mm. A rejeição fica (0,994 / 0,997) e o
   acerto em fechado também (0,972 / 0,973); o que cai é o acerto das conhecidas (0,51 / 0,53 contra 0,97): como na
   camada, os escores das conhecidas caem abaixo do limiar de 1,0 mm, sem que as classes se misturem.
2. Os planos aprendidos (0,970–1,029 mm) não cobrem 0,9 mm, e cobrem 1,1 mm menos ainda; o treino estreitou o banco
   (largura de 0,100 para 0,059 mm) e o deslocou para cima na ponta de fora (+4,4 %). Com o jitter de ±5 %, os planos
   do início do treino alcançavam 0,900–1,099 mm e os do fim 0,921–1,080 mm: 0,9 e 1,1 mm ficam na borda ou logo
   fora do que o treino viu, como o Q2 já dizia.
3. A 1,0 mm o banco é o melhor dos três em r1 (0,9808 contra 0,9747 e 0,9737). É uma repetição só.
4. A 0,7 mm o banco rejeita tudo, como a camada e a reconstrução.

### O que NÃO foi feito (como o Q2 manda)

r2–r5, banco mais largo ou com mais jitter, recalibração do banco. Nada em `results/`, `models/` nem `expected/`.

## 2026-11-15, 16:01 — D4: teste J2 preparado, antes de qualquer treino ou leitura de teste (execução)

Pré-registro: `CADERNO_CURVA.md`, Q3, seção J2 (commit `b97121d`); pedido do responsável da Fase S. Código no commit
`8262cae` (nada em `holo_openset/` mudou).

### O que conferi no pacote antes

- **Os bancos, como estão em `flows.FLOWS`:** `bank_jit` (`n_dist=5`, `alpha_jitter=0.05`, `alpha_spread` padrão
  0,05), `bank_wide` (`n_dist=7`, `alpha_spread=0.12`, `alpha_jitter=0.12`), `bank_w2` (`n_dist=9`, 0,12, 0,12),
  `bank_w3` (`n_dist=7`, `alpha_spread=0.12`, `alpha_jitter=0.05`). Os planos iniciais são α₀ (1 + linspace(−s, s,
  n)).
- **`--alpha-extend 12` e a calibração sem rótulo valem para os quatro igual ao `bank_jit`:** em `train.train`, os
  modos `prop` e `bank` passam pelo mesmo ramo (`alpha_init='calib'`, `calibrate_alpha(..., extend=alpha_extend)` em
  32 hologramas de treino); nenhum dos três bancos largos muda `alpha_init`. Com a mesma semente e as mesmas classes de
  cada repetição, o α₀ deve sair igual ao da camada (`prop`) da mesma repetição.
- **Recalibração por razão do banco sem mudar o pacote:** `experiments/robustness.py` já trata o banco: com
  `--alpha-json` e `--alpha-mode ratio`, todo o vetor `fourier.alpha` (todos os planos) é multiplicado por
  α / α_ref do json, só para os padrões de teste da distância nova; pesos, galeria (validação de 1,0 mm) e limiar não
  mudam; o cache do filtro depende da versão dos parâmetros, então a troca de α vale. É o mesmo caminho da linha
  `prop+recal_ratio` da d2. Os json são os da d2 (`recal_curve_u50_L008_z07/z09/z11.json`: 32 hologramas de
  validação sem rótulo na distância nova contra os mesmos ids na validação de 1,0 mm), lidos, não refeitos.

### Como vai rodar (`scripts/exp_resolucao/banks_distance.sh`)

- Por banco e repetição, nesta ordem (passo `rep`): `train` (`--no-aux --alpha-extend 12`; pula o modelo que existe:
  o `bank_jit` r1 é o do teste J), `evaluate` (1,0 mm → `eval/curve_u50_L008/<banco>_r<k>.json`; pula o que existe),
  `shifted` (como está, z09 e z11), `stress` (como está, z07), `recal` (por razão, z09 e z11, um json por distância),
  `recal_stress` (por razão, z07). O `bank_jit` r1 como está já foi lido no teste J
  (`robustness_curve_u50_L008_bank_jit.csv`) e não é lido de novo; as linhas recalibradas dele são novas.
- Linhas em `results_exp_resolucao/robustness_curve_u50_L008_banks_<banco>.csv`, **um arquivo por banco** (desvio de
  nome do pedido, que sugeria um csv por banco ou um só): o `save` do `experiment robustness` lê, concatena e regrava
  o csv inteiro, e duas filas escrevendo no mesmo arquivo ao mesmo tempo perderiam linhas. O csv do teste J não é
  reescrito.
- Quatro filas em tmux (`res_J2_<banco>`), uma por banco, r1 → r5: `bank_jit` e `bank_wide` na GPU 3, `bank_w2` e
  `bank_w3` na GPU 5 (dois processos por GPU, 4 threads cada, subidos com 1–2 min de intervalo). Logs
  `logs/exp_resolucao/J2_<banco>_<passo>_r<k>.log`.
- Tabela: `scripts/exp_resolucao/banks_distance.py` → `banks_distance.csv` e `banks_distance_rows.csv`. Camada e
  reconstrução (como estão e por razão, r1–r5) lidas de `distance_tests_u50_rows.csv` (6 casas, como estão
  guardadas). "Reconstrução recalibrada" = por razão, a variante principal da d2. A regra do Q3-J2 é aplicada às
  linhas como está.

## 2026-11-15, 16:31 — D5: teste J2 rodado (quatro bancos × r1–r5, como estão e recalibrados por razão) (execução)

Quatro filas em tmux (`res_J2_bank_jit` e `res_J2_bank_wide` na GPU 3; `res_J2_bank_w2` e `res_J2_bank_w3` na GPU
5), subidas às 16:02:20, 16:03:10, 16:03:40 e 16:04:57; terminaram às 16:17:00, 16:21:02, 16:30:34 e 16:30:34.
Comando de cada fila: `for R in 1..5; do HOLO_THREADS=4 OMP_NUM_THREADS=4 ... BANK=<banco> REP=$R bash
scripts/exp_resolucao/banks_distance.sh <GPU> rep; done`. Treinos: `bank_jit` 118–133 s, `bank_wide` 106–139 s,
`bank_w2` 211–236 s, `bank_w3` 205–230 s (duas filas por GPU). `some avg10` 0,00 em todas as leituras; 5–22 threads
prontas no container. Cada passo rodou uma vez (uma linha `start` por log), sem erro nem "missing"; o `bank_jit` r1
pulou treino, avaliação e as linhas como está (do teste J) e só leu as recalibradas. Tabela:
`bash scripts/exp_resolucao/banks_distance.sh 3 table`. Commits `dc9c62c` (resultados).

α calibrado no início do treino (log): 0,001056 (r1), 0,001059 (r2), 0,001053 (r3, r4, r5 em parte dos bancos; os
logs imprimem 6 casas), os mesmos da camada da mesma repetição: o sorteio das 32 imagens é o mesmo.

### Médias de cinco (`results_exp_resolucao/banks_distance.csv`), F1 / rejeição

| banco | 1,0 mm | 0,9 como está | 1,1 como está | 0,7 como está | 0,9 recal. | 1,1 recal. | 0,7 recal. |
|---|---|---|---|---|---|---|---|
| `bank_jit` (5, ±5 %, jitter 5 %) | 0,9786 / 0,9928 | 0,5751 / 0,9895 | 0,5793 / 0,9980 | 0,0150 / 1,0000 | 0,9599 / 0,9908 | 0,9591 / 0,9942 | 0,9330 / 0,9886 |
| `bank_wide` (7, ±12 %, 12 %) | 0,9766 / 0,9987 | 0,8601 / 0,9953 | 0,9087 / 0,9965 | 0,0181 / 0,9966 | 0,9608 / 0,9961 | 0,9544 / 0,9920 | 0,9048 / 0,9962 |
| `bank_w2` (9, ±12 %, 12 %) | 0,9761 / 0,9925 | 0,8672 / 0,9955 | 0,8920 / 0,9955 | 0,0171 / 1,0000 | 0,9601 / 0,9933 | 0,9547 / 0,9878 | 0,8991 / 0,9967 |
| `bank_w3` (7, ±12 %, 5 %) | 0,9786 / 0,9958 | 0,6094 / 0,9870 | 0,7034 / 0,9903 | 0,0153 / 0,9989 | 0,9622 / 0,9939 | 0,9652 / 0,9923 | 0,9326 / 0,9968 |
| camada (`prop`, d2) | 0,9748 / 0,9829 | 0,4261 / 0,9966 | 0,2893 / 0,9935 | 0,0150 / 1,0000 | 0,9325 / 0,9818 | 0,9303 / 0,9779 | 0,9190 / 0,9786 |
| reconstrução (`rec_z0`, d2) | 0,9770 / 0,9961 | 0,2490 / 0,9998 | 0,3029 / 0,9986 | 0,0150 / 1,0000 | 0,9783 / 0,9962 | 0,9748 / 0,9965 | 0,9641 / 0,9973 |

### Queda contra o próprio 1,0 mm (F1, média e faixa) e a regra do Q3-J2

| banco | 0,9 como está | 1,1 como está | 0,9 recal. | 1,1 recal. | aguenta (r1…r5) | veredito |
|---|---|---|---|---|---|---|
| `bank_jit` | −0,4035 (−0,4723 a −0,3305) | −0,3993 (−0,4759 a −0,3029) | −0,0187 | −0,0195 | não ×5 | **0 de 5** |
| `bank_wide` | −0,1165 (−0,1308 a −0,1040) | −0,0679 (−0,0885 a −0,0520) | −0,0158 | −0,0222 | não ×5 | **0 de 5** |
| `bank_w2` | −0,1089 (−0,1251 a −0,0920) | −0,0841 (−0,1074 a −0,0685) | −0,0159 | −0,0214 | não, sim, não, sim, não | **2 de 5** |
| `bank_w3` | −0,3692 (−0,4130 a −0,3122) | −0,2752 (−0,3110 a −0,2449) | −0,0164 | −0,0134 | não ×5 | **0 de 5** |

A rejeição nunca cai mais que 0,045 (todas as quedas de rejeição como está entre −0,0451 e +0,0264): quem decide a
regra é o F1. O `bank_wide` falha a 0,9 mm nas cinco (quedas de 0,104 a 0,131) e passa a 1,1 mm nas cinco; o
`bank_w2` falha a 0,9 mm em r1, r3, r5 (0,125, 0,125, 0,110) e a 1,1 mm em r3, r5 (0,107, 0,102). **Nenhum banco
aguenta a mudança de distância (≥ 4 de 5).** A 0,7 mm (fora da regra) todos rejeitam quase tudo (F1 0,015–0,023).

### Diferenças para a reconstrução e a camada (F1; média; positivos)

| banco | preço a 1,0 mm: − reconstrução / − camada (k de 5) | como está − reconstrução como está (k de 10) | como está − reconstrução recal. (k de 10) | recal. − reconstrução recal. (k de 10; k de 15 com 0,7) | recal. − camada recal. (k de 10; k de 15) |
|---|---|---|---|---|---|
| `bank_jit` | +0,0016 (4) / +0,0039 (5) | +0,3013 (10) | −0,3994 (0) | −0,0171 (1; 1 de 15) | +0,0281 (10; 14 de 15) |
| `bank_wide` | −0,0004 (3) / +0,0018 (3) | +0,6084 (10) | −0,0922 (0) | −0,0190 (0; 0 de 15) | +0,0262 (10; 10 de 15) |
| `bank_w2` | −0,0009 (2) / +0,0013 (2) | +0,6036 (10) | −0,0970 (0) | −0,0192 (0; 0 de 15) | +0,0260 (10; 10 de 15) |
| `bank_w3` | +0,0016 (5) / +0,0038 (4) | +0,3805 (10) | −0,3202 (0) | −0,0129 (0; 0 de 15) | +0,0323 (10; 15 de 15) |

Faixas e as diferenças de rejeição estão no csv (`kind = diff` e `diff_count`). "Reconstrução recalibrada" e "camada
recalibrada" são as por razão da d2, lidas de `distance_tests_u50_rows.csv`. Recalibrado − reconstrução recalibrada
a 0,7 mm: −0,0225 a −0,0625 (média por banco −0,0312 / −0,0593 / −0,0650 / −0,0315; no csv).

### Planos depois do treino (mm; `models_exp_resolucao/curve_u50_L008/<banco>_r<k>.pt`, `fourier.alpha`)

| banco | r1 | r2 | r3 | r4 | r5 |
|---|---|---|---|---|---|
| `bank_jit` | 0,9698 0,9746 0,9850 1,0114 1,0287 | 0,9735 0,9900 1,0196 0,9907 0,9936 | 0,9680 0,9708 0,9959 1,0040 1,0193 | 0,9607 0,9788 0,9875 1,0092 1,0107 | 0,9230 0,9477 0,9667 0,9846 0,9782 |
| `bank_wide` | 0,9234 0,9635 0,9651 1,0051 1,0137 1,0277 1,0384 | 0,9480 0,9548 0,9801 0,9838 0,9953 1,0366 1,0879 | 0,9356 0,9640 0,9746 0,9901 1,0056 1,0407 1,0451 | 0,8846 0,9673 0,9730 1,0009 1,0193 1,0283 1,0492 | 0,9393 0,9578 0,9940 0,9647 1,0001 1,0299 1,0442 |
| `bank_w2` | 0,9356 0,9691 0,9630 0,9773 0,9988 1,0071 1,0341 1,0490 1,0687 | 0,8139 0,9535 0,9684 0,9673 1,0046 0,9909 1,0383 1,0134 1,0707 | 0,9466 0,9568 0,9639 0,9754 0,9882 0,9953 1,0109 1,0597 1,0655 | 0,9637 0,9282 0,9618 0,9800 0,9848 1,0109 1,0227 1,0674 1,0493 | 0,9349 0,9528 0,9514 0,9786 0,9879 1,0288 1,0468 0,9916 1,0278 |
| `bank_w3` | 0,9080 0,9428 0,9480 0,9667 1,0030 1,0428 1,0749 | 0,8893 0,9618 0,9872 0,9966 1,0169 1,0277 1,0388 | 0,9003 0,9259 0,9296 0,9495 0,9727 1,0523 1,0647 | 0,8721 0,9319 0,9617 0,9766 0,9984 1,0074 1,0228 | 0,9240 0,9122 0,9350 0,9565 1,0052 0,9936 1,0092 |

Os planos iniciais eram α₀ (1 + linspace(−s, s, n)) com α₀ ≈ 0,994–1,000 mm: ±5 % ≈ 0,945–1,050 mm, ±12 % ≈
0,875–1,120 mm. Depois do treino todos os bancos ficam mais estreitos que no início (os de ±12 % entre ≈ 0,81–0,96 e
1,01–1,09 mm nas pontas), e os planos deixam de estar em ordem em vários modelos (por exemplo `bank_jit` r2:
1,0196 no meio; `bank_w2` r2: 0,8139 sozinho embaixo).

### Frase do Q3-J2 que os números sustentam

**(i) Nenhum banco aguenta → "o banco focal não dispensa a recalibração".** Nenhum dos quatro aguenta em ≥ 4 de 5
(máximo: `bank_w2`, 2 de 5). A frase (ii) não se aplica.

### Desvios

1. Um csv de robustez por banco (`robustness_curve_u50_L008_banks_<banco>.csv`), declarado no D4 antes de rodar,
   para que duas filas nunca regravem o mesmo arquivo.
2. Camada e reconstrução lidas de `distance_tests_u50_rows.csv` (6 casas, como guardadas): as diferenças com elas
   têm erro de arredondamento ≤ 5 × 10⁻⁷. Isso só pesa nas contagens de sinal a 0,7 mm "como está", onde banco e
   reconstrução rejeitam tudo e empatam (0,0148 contra 0,0148): ali o sinal de vários "+0,000000" é ruído de
   arredondamento, e o "k de 15" de "como está − reconstrução como está" não é informativo.

### O que parece estranho ou merece olhar (leitura minha)

1. **Recalibrado, o banco fecha boa parte da diferença da camada para a reconstrução, mas não toda:** banco
   recalibrado − camada recalibrada +0,026 a +0,032 (10 de 10 positivas nos quatro bancos); banco recalibrado −
   reconstrução recalibrada −0,013 a −0,019 (0 ou 1 de 10 positivas). A camada ficava 0,045 abaixo (d2).
2. **Os bancos largos caem bem menos sem recalibrar** (−0,07 a −0,12 contra −0,40 do `bank_jit`), mas a 0,9 mm
   passam da linha de 0,10 em quase todas as repetições. Os de jitter 12 % (`bank_wide`, `bank_w2`) caem menos que
   o de jitter 5 % com a mesma largura (`bank_w3`, −0,28 a −0,37): o jitter pesa mais que a largura dos planos.
3. **A queda é assimétrica:** todos caem mais a 0,9 mm que a 1,1 mm, menos o `bank_jit` (iguais). Os planos ficam
   mais densos acima de 1,0 mm em vários modelos, e o α treinado da camada já ficava abaixo de 1,0 mm (0,963–0,968).
4. **A 1,0 mm não há preço visível:** banco − reconstrução entre −0,0009 e +0,0016 de média, com sinais divididos.
5. O treino desordena os planos (item acima): a "largura ±12 %" é a do início do treino, não a do modelo final.
