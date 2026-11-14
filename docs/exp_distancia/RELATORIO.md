# Relatório: quando o focal stack economiza tempo de verdade

Protocolo: `docs/exp_distancia/PROTOCOLO.md`. Caderno: `docs/exp_distancia/CADERNO.md`. Branch `exp/distancia-autofocus`.

## 0. Origem dos números

Tabelas copiadas de `results_exp_distancia/distance/tables/*.md` sem alterar valores (ponto decimal; colunas cortadas; sem desvio padrão nas Tabelas 1 e 6). Macros em `results_exp_distancia/numbers_distancia.tex`; o resto vem do caderno. Comando: `bash scripts/exp_distancia/relatorio.sh`. Sessão de tempo `results_exp_distancia/e5/`: GPU da tentativa 2 (`e5_a2`, escolha do responsável) e um core de CPU.

## 1. Respostas

- **Q1** (z fixo por sessão): não; a busca uma vez por sessão tem o F1 da busca em todo quadro e, feita com a busca barata, custa o mesmo que `rec_z0`, menos que o stack.
- **Q2** (z por quadro): o ganho existe contra a busca cega, mas contra a busca barata em todo quadro cai para no máximo 1,3× (GPU) e 1,4× (CPU) no front end, e o critério pré-registrado só vale para o stack de 5 no drift lento (e em `frame_2` na leitura B).
- **Q3** (busca mais barata e robusta): sim; uma busca de ±10 % sobre a amplitude reduzida 4× custa 1/78 da cega em GPU, não perde F1 e recupera os conjuntos com ruído forte e feixe estreito.
- **Q4** (inclinação): não na faixa plausível; nada muda até 5°, e a 15° a diferença a favor do stack é +0,005, em 4 de 5 repetições.

### Q1: evidência

Em `base`, `session_2` e `session_5`, `rec_afs` (busca cega no primeiro quadro da sessão) e `rec_af` (busca cega em todo quadro) diferem em 0,000 na média pareada (`tab_dist_paired`). H1 se confirma. Com n = 100, `rec_afs` custa 4,2 ms por quadro em GPU, e `rec_afsc` (a busca barata por sessão) custa o mesmo que `rec_z0` (Tabela 3). O stack de 5 custa mais que `rec_afsc`, embora menos que `rec_afs`, e perde 0,125 de F1 em `session_5` contra `rec_afc`. Os stacks largos perdem de 0,011 a 0,020 contra `rec_afc` nos seis conjuntos sem ruído forte nem feixe estreito, sobretudo em rejeição das classes não vistas: no base, 0,826 e 0,838, contra 0,913–0,924 dos outros fluxos (`tab_dist_rejection.md`; o AUROC cai menos, 0,966–0,967 contra 0,978–0,983, `tab_dist_auroc.md`).

Variância entre sessões (`tab_dist_sessions`): a busca cega por sessão erra por mais de 192 µm (1 % de z₀) em 4 das 8 sessões de `fullwell_500` e em 7 das 8 de `beam_narrow`. Nelas a acurácia nas classes vistas de `rec_afs` vai a 0,000 e 0,042 em duas sessões de `fullwell_500` e a 0,000 nas sete de `beam_narrow`. A busca barata por sessão não erra em nenhuma sessão desses conjuntos (acurácia 0,916–0,957). Em `session_5` nenhuma das duas erra.

**Tabela 1.** Open-set F1 nas janelas de teste, média de r1–r5. Negrito: mais de 0,05 abaixo do mesmo fluxo no base.

| fluxo | base | session_2 | session_5 | frame_2 | frame_5 | walk_05 | fullwell_500 | beam_narrow |
|---|---|---|---|---|---|---|---|---|
| rec_z0 | 0.964 | 0.939 | **0.753** | 0.955 | **0.865** | 0.934 | 0.950 | 0.959 |
| rec_af | 0.964 | 0.964 | 0.964 | 0.964 | 0.964 | 0.964 | **0.770** | **0.432** |
| rec_afs | 0.964 | 0.964 | 0.964 | 0.927 | **0.727** | 0.927 | **0.803** | **0.220** |
| rec_afsc | 0.964 | 0.964 | 0.964 | 0.927 | **0.725** | 0.926 | 0.949 | 0.959 |
| rec_afM | 0.964 | 0.964 | 0.964 | 0.946 | **0.798** | 0.963 | **0.734** | **0.404** |
| rec_afc | 0.964 | 0.964 | 0.964 | 0.965 | 0.964 | 0.965 | 0.949 | 0.959 |
| rec_afr | 0.964 | 0.964 | 0.964 | 0.965 | 0.964 | 0.965 | 0.950 | 0.959 |
| prop | 0.963 | 0.939 | **0.749** | 0.954 | **0.865** | 0.930 | 0.956 | **0.879** |
| bank_jit | 0.963 | 0.957 | **0.839** | 0.961 | 0.924 | 0.953 | 0.963 | **0.878** |
| bank_wide | 0.952 | 0.952 | 0.944 | 0.952 | 0.949 | 0.951 | 0.952 | **0.871** |
| bank_w2 | 0.952 | 0.953 | 0.944 | 0.953 | 0.948 | 0.952 | 0.952 | **0.875** |


### Q2: evidência

As políticas por sessão caem mais do que H2 esperava: em `frame_5`, `rec_afs` e `rec_afsc` ficam em 0,727 e 0,725, abaixo de `rec_z0`, e não em 0,75. `rec_afM` (busca cega a cada 10 quadros) só serve no drift lento. Os stacks largos ficam a 0,015–0,016 de `rec_af` em `frame_5`, como H2 previa; o de 5 fica 0,040 abaixo de `rec_afc`.

Tempo (Tabela 3). Contra `rec_af`, o front end do stack de 5 é 35,71× mais barato em GPU e 49,10× em CPU; fim a fim, 1,71× e 5,75×. Contra `rec_afc` sobram 1,28× e 1,39×, cerca de 1 ms e 0,9 s por quadro; fim a fim, 1,01× e 1,04×. Os stacks largos, os únicos que seguram o F1 a 5 %, custam mais que `rec_afc` em GPU. Em CPU o de 7 é mais barato que `rec_afc`; o de 9 não.

Critério (Tabela 4). "Mais barato que o mais barato dos fluxos convencionais que atingem esse F1" admite duas leituras: **A**, os convencionais com F1 a até 0,02 do melhor (a tolerância dada ao stack); **B**, os que atingem o F1 do stack. O stack de 5 cumpre em `walk_05` nas duas (3,52 contra 4,50 ms e 2,42 contra 3,36 s, contra `rec_afc`). Em `frame_2` cumpre só na B, porque na A `rec_z0` (0,955) qualifica e custa 2,93 ms. O de 7 só é mais barato em CPU; o de 9 nunca cumpre. Em `session_5` os largos falham o 0,02 por 0,0004. Em `fullwell_500` os stacks ficam acima do melhor convencional mas custam mais que `rec_z0`; na B nenhum convencional chega ao F1 deles, caso que a leitura não cobre. **A escolha entre A e B é do orientador.** Ressalvas: o melhor convencional às vezes ganha por menos de 0,0002 (`rec_afc` 0,96475 contra `rec_afr` 0,96473 em `walk_05`), o que muda a referência da diferença mas não os vereditos; e o critério usa o F1 das janelas, enquanto nos quadros inteiros os stacks largos ficam 0,032–0,038 abaixo de `rec_afc` (`tab_dist_frames_paired.md`).

n\* (Tabela 5, Figura 1) é o número de quadros por montagem acima do qual buscar uma vez por montagem fica mais barato que o stack. Para o stack de 5 com a busca barata: 2,6 (GPU) e 9,9 (CPU) na conta completa, que cobra do convencional flat field, back-propagation e canais (regra 8.4); 0,6 e 0,7 na simplificada (Seção 3 do protocolo). Com a busca cega: 205 e 1099; 48 e 83.

**Tabela 2.** Erro de distância no teste: mediana (µm) / falha grosseira (% com erro > 192,5 µm). Entre parênteses, reconstruções por imagem (amortizadas em `afs`, `afsc`, `afM`).

| conjunto | af (114) | afs (1.1) | afsc (0.18) | afM (11.4) | afc (18.0) | afr (36.0) |
|---|---|---|---|---|---|---|
| base | 50 / 1.4 | 40 / 0.0 | 71 / 0.0 | 49 / 1.2 | 50 / 0.2 | 36 / 0.4 |
| session_2 | 49 / 2.2 | 66 / 0.0 | 61 / 0.0 | 46 / 0.0 | 56 / 0.8 | 32 / 0.1 |
| session_5 | 50 / 2.0 | 40 / 0.0 | 20 / 0.0 | 42 / 2.5 | 28 / 0.1 | 35 / 0.2 |
| frame_2 | 49 / 1.6 | 393 / 73.5 | 433 / 75.5 | 319 / 65.0 | 41 / 0.6 | 34 / 0.2 |
| frame_5 | 47 / 2.4 | 1033 / 87.9 | 1053 / 88.2 | 806 / 80.1 | 45 / 0.2 | 33 / 0.4 |
| walk_05 | 47 / 1.5 | 416 / 73.8 | 388 / 68.5 | 135 / 35.9 | 43 / 0.0 | 34 / 0.1 |
| fullwell_500 | 447 / 70.2 | 201 / 50.0 | 67 / 0.0 | 441 / 67.5 | 50 / 1.8 | 31 / 0.4 |
| beam_narrow | 13049 / 74.0 | 13121 / 87.5 | 73 / 0.0 | 13049 / 72.5 | 50 / 0.2 | 31 / 0.4 |


**Tabela 3.** Tempo por quadro inteiro: somas de tempos de estágio medidos (`e5`; GPU mínimo, CPU um core mediana), não medições de ponta a ponta. Total = front end + YOLO + embedding + decisão. † amortizado: busca / 100 ou / 10 (`rec_afM`). Últimas colunas: razão para `bank_jit`, front end / total.

| fluxo | GPU front (ms) | GPU total (ms) | CPU front (s) | CPU total (s) | × stack 5, GPU | × stack 5, CPU |
|---|---|---|---|---|---|---|
| rec_z0 | 2.9 | 172 | 2.3 | 24.4 | 0.83 / 1.00 | 0.96 / 1.00 |
| rec_af | 126 | 295 | 119 | 141 | 35.71 / 1.71 | 49.10 / 5.75 |
| rec_afs † | 4.2 | 173 | 3.5 | 25.5 | 1.18 / 1.00 | 1.44 / 1.04 |
| rec_afsc † | 2.9 | 172 | 2.3 | 24.4 | 0.83 / 1.00 | 0.96 / 1.00 |
| rec_afM † | 15.2 | 184 | 14.0 | 36.0 | 4.32 / 1.07 | 5.77 / 1.47 |
| rec_afc | 4.5 | 174 | 3.4 | 25.4 | 1.28 / 1.01 | 1.39 / 1.04 |
| rec_afr | 14.1 | 183 | 11.8 | 33.9 | 4.00 / 1.06 | 4.88 / 1.38 |
| rec_edfw | 210 | 379 | 166 | 188 | 59.47 / 2.19 | 68.67 / 7.69 |
| prop | 1.1 | 170 | 0.78 | 22.8 | 0.31 / 0.99 | 0.32 / 0.93 |
| bank_jit | 3.5 | 173 | 2.4 | 24.5 | 1.00 / 1.00 | 1.00 / 1.00 |
| bank_wide | 4.7 | 174 | 3.1 | 25.2 | 1.34 / 1.01 | 1.30 / 1.03 |
| bank_w2 | 5.9 | 175 | 4.1 | 26.2 | 1.68 / 1.01 | 1.69 / 1.07 |


**Tabela 4.** Critério da Seção 3 do protocolo (`tab_dist_criterion`): F1 das janelas, front end do quadro inteiro (Tabela 3). Convencionais: `rec_z0`, `rec_af`, `rec_afs`, `rec_afsc`, `rec_afM`, `rec_afc`, `rec_afr`. Fora de "not cheaper"/"F1 fails", o veredito foi decidido contra `rec_afc`, exceto `frame_2`/`bank_jit` na A e `fullwell_500` na A (contra `rec_z0`) e `fullwell_500` na B (sem convencional).

| conjunto | melhor convencional (F1) | stack | stack − melhor (mesmo sinal) | F1 a 0,02 | A | B |
|---|---|---|---|---|---|---|
| base | rec_afr 0.964 | bank_jit | -0.0015 (2/5) | yes | not cheaper | not cheaper |
|  |  | bank_wide | -0.0119 (5/5) | yes | not cheaper | not cheaper |
|  |  | bank_w2 | -0.0119 (5/5) | yes | not cheaper | not cheaper |
| session_2 | rec_afc 0.964 | bank_jit | -0.0078 (5/5) | yes | not cheaper | not cheaper |
|  |  | bank_wide | -0.0121 (5/5) | yes | not cheaper | not cheaper |
|  |  | bank_w2 | -0.0115 (5/5) | yes | not cheaper | not cheaper |
| session_5 | rec_afsc 0.964 | bank_jit | -0.1255 (5/5) | no | F1 fails | F1 fails |
|  |  | bank_wide | -0.0204 (5/5) | no | F1 fails | F1 fails |
|  |  | bank_w2 | -0.0204 (5/5) | no | F1 fails | F1 fails |
| frame_2 | rec_afc 0.965 | bank_jit | -0.0042 (5/5) | yes | not cheaper | met (GPU and CPU) |
|  |  | bank_wide | -0.0123 (5/5) | yes | not cheaper | not cheaper |
|  |  | bank_w2 | -0.0119 (5/5) | yes | not cheaper | not cheaper |
| frame_5 | rec_afr 0.964 | bank_jit | -0.0405 (5/5) | no | F1 fails | F1 fails |
|  |  | bank_wide | -0.0154 (5/5) | yes | cheaper on CPU only | cheaper on CPU only |
|  |  | bank_w2 | -0.0161 (5/5) | yes | not cheaper | not cheaper |
| walk_05 | rec_afc 0.965 | bank_jit | -0.0122 (5/5) | yes | met (GPU and CPU) | met (GPU and CPU) |
|  |  | bank_wide | -0.0137 (5/5) | yes | cheaper on CPU only | cheaper on CPU only |
|  |  | bank_w2 | -0.0131 (5/5) | yes | not cheaper | not cheaper |
| fullwell_500 | rec_afr 0.950 | bank_jit | +0.0127 (5/5) | yes | not cheaper | none reaches it |
|  |  | bank_wide | +0.0017 (3/5) | yes | not cheaper | none reaches it |
|  |  | bank_w2 | +0.0023 (3/5) | yes | not cheaper | none reaches it |
| beam_narrow | rec_afr 0.959 | bank_jit | -0.0808 (5/5) | no | F1 fails | F1 fails |
|  |  | bank_wide | -0.0877 (5/5) | no | F1 fails | F1 fails |
|  |  | bank_w2 | -0.0841 (5/5) | no | F1 fails | F1 fails |


**Tabela 5.** n\* no quadro inteiro (`tab_dist_breakeven`). Completa: T_busca / (T_camada − (T_flat_field + T_backprop + T_canais)); simplificada: T_busca / (T_camada − T_backprop). "per frame": front end da busca em todo quadro sobre o do stack (n = 1).

| stack | busca | GPU busca (ms) | GPU n\* | GPU n\* simpl. | GPU per frame (×) | CPU busca (s) | CPU n\* | CPU n\* simpl. | CPU per frame (×) |
|---|---|---|---|---|---|---|---|---|---|
| bank_jit | blind | 123 | 205 | 48 | 35.7 | 116 | 1099 | 83 | 49.1 |
|  | afc | 1.6 | 2.6 | 0.6 | 1.3 | 1.0 | 9.9 | 0.7 | 1.4 |
|  | afr | 11.2 | 19 | 4.4 | 4.0 | 9.5 | 90 | 6.7 | 4.9 |
| bank_wide | blind | 123 | 68 | 33 | 26.7 | 116 | 141 | 55 | 37.9 |
|  | afc | 1.6 | 0.9 | 0.4 | 1.0 | 1.0 | 1.3 | 0.5 | 1.1 |
|  | afr | 11.2 | 6.2 | 3.0 | 3.0 | 9.5 | 12 | 4.5 | 3.8 |
| bank_w2 | blind | 123 | 41 | 25 | 21.2 | 116 | 65 | 38 | 29.0 |
|  | afc | 1.6 | 0.5 | 0.3 | 0.8 | 1.0 | 0.6 | 0.3 | 0.8 |
|  | afr | 11.2 | 3.7 | 2.3 | 2.4 | 9.5 | 5.3 | 3.1 | 2.9 |


![Custo do front end por quadro em função de n](img/fig_dist_breakeven.png)

**Figura 1** (`fig_dist_breakeven`). Front end por quadro inteiro contra n, quadros por busca (log). Curvas: buscas cega e barata uma vez por montagem. Retas: os três stacks, `rec_z0` e a busca barata em todo quadro. Círculos: n\*. (a) Uma GPU, mínimo. (b) Um core de CPU, mediana.

![Custo contra F1 nos quadros inteiros](img/fig_dist_cost_f1.png)

**Figura 2** (`fig_dist_cost_f1`). Custo em uma GPU (log; somas de estágios) contra F1 fim a fim nos quadros inteiros; melhor é para cima e para a esquerda. (a) z fixo por sessão, front end. (b) O mesmo, com o detector. (c) z mudando 5 % por quadro, front end. (d) O mesmo, com o detector.

### Q3: evidência

A `afc` (`r10b-b4-tog`) busca em ±10 % de z₀, com 7 + 11 candidatos, sobre a amplitude reduzida 4 × 4 por média, com o ToG do paper: 18 reconstruções de 1/16 dos pixels. No quadro inteiro custa 78× menos que a cega em GPU e 111× menos em CPU (`\DistSearchBlindOverAfcGpu`, `\DistSearchBlindOverAfcCpu`). Nos seis conjuntos limpos, `rec_afc` − `rec_af` é no máximo 0,0005 em módulo na média pareada (`scripts/exp_distancia/paired_check.py`). Sob `fullwell_500` ganha +0,179 e sob `beam_narrow` +0,527, 5/5. A falha grosseira cai de 70,2 % para 1,8 % e de 74,0 % para 0,2 % (Tabela 2). A `afr` (±15 %, redução 2×, campo suavizado com σ = 2 px) erra menos e tem o mesmo F1, mas custa cerca de 7× (GPU) e 9× (CPU) a `afc`. Com um modelo treinado nas reconstruções da `afc` (r1), o F1 muda no máximo 0,006 (`tab_dist_own`).

O que consertou o ruído aparece na validação (`tab_dist_focus_val`). Falhas grosseiras em `fullwell_500` / `beam_narrow`: busca cega 70,6 / 49,9 %; só estreitar a faixa 66,9 / 21,9 %; só reduzir 4× 1,0 / 12,1 %; só suavizar 0,7 / 5,7 %; estreitar e reduzir (a `afc`) 0,9 / 0,9 %. O que resolve é tirar as altas frequências antes do ToG, por média ou por suavização; o critério de Tamura não precisou mudar, e estreitar sozinho não resolve. A frase do paper deve dizer "como o autofocus cego na resolução do sensor", não "como o autofocus com o critério de Tamura", sem sugerir que só a redução funciona.

### Q4: evidência

Até 5° nenhum fluxo muda o F1 em mais de 0,001 (caderno, E4). A 15°, `rec_z0`, `rec_af` e `rec_afc` perdem cerca de 0,008 e o stack de 5 perde 0,0021 (Tabela 6, Figura 3). A diferença pareada stack de 5 − `rec_afc` é +0,000 a 10° (3/5) e +0,005 a 15° (4/5) (`tab_dist_frames_paired.md`). O foco por objeto em faixa larga (`rec_edfw`) fica plano, mas custa 210 ms de front end em GPU e 166 s em CPU, 2,16× o stack de 5 fim a fim no run medido (Tabela 7). A perda só aparece entre 10° e 15°: pela regra do E4, é limite da simulação, não vantagem do método.

**Tabela 6.** F1 fim a fim (caixas do detector) nos quadros inteiros, média de r1–r5. Negrito: mais de 0,05 abaixo do mesmo fluxo nos quadros do paper. `--`: não rodado nesse conjunto (decidido no congelamento).

| fluxo | quadros do paper | frame5 | 0° | 1° | 2° | 5° | 10° | 15° |
|---|---|---|---|---|---|---|---|---|
| rec_z0 | 0.975 | **0.862** | 0.975 | 0.975 | 0.975 | 0.975 | 0.973 | 0.967 |
| rec_af | 0.975 | 0.975 | 0.975 | 0.975 | 0.975 | 0.974 | 0.973 | 0.967 |
| rec_afs | 0.975 | **0.835** | -- | -- | -- | -- | -- | -- |
| rec_afsc | 0.975 | **0.835** | -- | -- | -- | -- | -- | -- |
| rec_afc | 0.975 | 0.975 | 0.975 | 0.975 | 0.975 | 0.975 | 0.973 | 0.967 |
| rec_afr | 0.975 | 0.975 | -- | -- | -- | -- | -- | -- |
| rec_edfw | -- | -- | 0.972 | 0.972 | 0.972 | 0.972 | 0.972 | 0.973 |
| prop | 0.973 | **0.866** | -- | -- | -- | -- | -- | -- |
| bank_jit | 0.974 | 0.930 | 0.974 | 0.974 | 0.974 | 0.974 | 0.973 | 0.972 |
| bank_wide | 0.940 | 0.937 | 0.940 | 0.940 | 0.940 | 0.940 | 0.940 | 0.939 |
| bank_w2 | 0.944 | 0.940 | 0.944 | 0.944 | 0.944 | 0.944 | 0.943 | 0.943 |
| detector recall | 0.997 | 0.996 | 0.997 | 0.997 | 0.997 | 0.997 | 0.997 | 0.997 |


![F1 contra a inclinação da lâmina](img/fig_dist_tilt.png)

**Figura 3** (`fig_dist_tilt`). F1 fim a fim nos quadros inteiros contra a inclinação da lâmina (eixo de baixo, graus). Eixo de cima: variação de z na borda do quadro, 3,2 mm × tan θ, em µm. Uma linha por fluxo. Painel único.

## 2. Tempo: o que a medição mostra além do combinado

**(a) O fim a fim é do detector.** Nas somas de estágios o YOLO custa 166,82 ms de 170–175 ms em GPU para os fluxos baratos (Tabela 3). No run medido o detector custa 178,1 ms de 186–205 ms (Tabela 7).

**(b) Os canais custam mais que a back-propagation.** `channels` (escala por percentil da entrada da rede, só no fluxo convencional) custa 1,78 ms em GPU e 1,19 s em CPU, contra 0,97 ms e 1,01 s da back-propagation; por isso as duas contas de n\* divergem. Na completa, o denominador do stack de 5 é 0,60 ms em GPU e cerca de 0,1 s em CPU. Entre as duas tentativas de GPU ele mudou 0,02 ms (0,58 para 0,60 ms) e moveu n\* de 212 para 205 (caderno, Etapa 4). Com a busca barata, n\* fica entre 0,3 e 9,9 para os três stacks nas duas contas. Na janela de 640 px em GPU, o stack de 5 (0,19 ms) é mais barato que a própria reconstrução em z₀ (0,59 ms) (`tab_dist_time`).

**(c) Ler o blank frame pesa mais que a busca barata.** No run medido, os fluxos de reconstrução gastam cerca de 18 ms lendo quadro e blank frame (float32, 3840 × 2748 × 4 bytes ≈ 42 MB) e normalizando; os de camada, 2,8 ms (Tabela 7). Esses 15 ms superam todas as diferenças de cálculo entre os fluxos com busca barata e os stacks e não têm a ver com a busca; num instrumento o blank frame ficaria na memória. Por isso o run medido dá `rec_afc` 1,08× o stack de 5 fim a fim, e a soma de estágios, 1,01×. A Tabela 3 (cálculo, GPU e CPU, sem disco) é a que entra no critério e em n\*; a Tabela 7 mostra o pipeline como está implementado (só GPU).

**(d) A CPU desta sessão é cerca de 2× mais rápida que a do paper** (back-propagation 1,01 contra 2,19 s; busca cega 116,44 contra 238,73 s; Seção 2.3 do protocolo), com outra carga (load 59–89 aqui; cerca de 230 no paper). Em GPU os estágios principais batem com o paper a menos de 4 %, menos o YOLO (166,82 contra 221,7 ms). Só comparamos razões dentro da nossa sessão.

**Tabela 7.** Run medido de quadros inteiros (`e5/full_frames_time.csv`, uma GPU; `tab_dist_time_measured`). Grupos: medianas de cada grupo. "sem detector": mediana da soma por quadro (os grupos não somam exatamente a ela). Total = sem detector + detector (178,1 ms). † busca no primeiro quadro de cada sessão, dividida pelos 5 quadros da sessão.

| fluxo | read (ms) | compute (ms) | embed + decide (ms) | sem detector (ms) | total com detector (ms) | × stack 5 | F1 fim a fim |
|---|---|---|---|---|---|---|---|
| rec_z0 | 17.9 | 3.3 | 3.7 | 25.6 | 204 | 1.08 | 0.975 ± 0.006 |
| rec_af | 17.8 | 126.5 | 3.9 | 148.3 | 326 | 1.73 | 0.975 ± 0.005 |
| rec_afs † | 17.9 | 27.9 | 3.7 | 49.5 | 228 | 1.20 | 0.975 ± 0.005 |
| rec_afsc † | 17.8 | 3.6 | 3.6 | 25.1 | 203 | 1.07 | 0.975 ± 0.005 |
| rec_afc | 17.7 | 5.1 | 3.6 | 26.4 | 205 | 1.08 | 0.975 ± 0.005 |
| rec_afr | 17.8 | 14.6 | 3.6 | 36.1 | 214 | 1.13 | 0.975 ± 0.005 |
| rec_edfw | 17.9 | 209.2 | 3.9 | 230.9 | 409 | 2.16 | 0.972 ± 0.009 |
| prop | 2.8 | 1.2 | 3.6 | 7.6 | 186 | 0.98 | 0.973 ± 0.008 |
| bank_jit | 2.8 | 3.6 | 4.6 | 11.1 | 189 | 1.00 | 0.974 ± 0.004 |
| bank_wide | 2.8 | 4.9 | 5.0 | 12.6 | 191 | 1.01 | 0.940 ± 0.006 |
| bank_w2 | 2.8 | 6.1 | 5.5 | 14.4 | 192 | 1.02 | 0.944 ± 0.012 |


## 3. Plausibilidade física

**z fixo por sessão.** É a bancada: uma montagem rende cerca de 100 quadros, e z muda entre montagens. A resposta sensata é buscar uma vez por montagem.

**z por quadro, independente.** Cada quadro é uma montagem nova, como numa triagem com uma imagem por amostra num aparelho point-of-care: o limite n = 1 da Figura 1. A 2 % o desvio típico é cerca de 0,4 mm; a 5 %, 0,05 × 19,25 mm ≈ 1 mm por quadro, variação grande para uma lâmina apoiada. Não sabemos se uma montagem real varia tanto.

**Drift lento (`walk_05`).** Cerca de 5 % depois de 100 quadros: drift térmico ou mecânico, ou plataforma que desliza a amostra. A resposta convencional é refocar a cada M quadros.

**Ruído forte e feixe estreito.** `fullwell_500` é um poço de 500 e⁻, 12× menor que o do base; `beam_narrow` é um feixe com cintura de 0,9–1,3 meias diagonais (2,0–3,5 no base), em que a iluminação cai mais em direção às bordas. São estresses da aquisição, não cenários medidos na bancada; mostram onde a busca cega quebra.

**Inclinação.** A variação de z na borda do quadro é cerca de ±56 µm a 1°, ±112 µm a 2°, ±280 µm a 5°, ±560 µm a 10° e ±860 µm a 15°. Um spread de profundidade de 300 µm não custa nada a nenhum fluxo (Tabela 10 do paper, transcrita na Seção 2.3 do protocolo). **O prof. Sobieranski não foi consultado.** O limite de 2° é suposição nossa, e a pergunta fica para o orientador.

**A redução 4× antes da busca.** O LED de 10 nm e o pinhole de 100 µm deixam pouco contraste acima de cerca de 70 ciclos/mm (Fig. 2b do paper). Reduzir 4× leva o Nyquist de 299 para cerca de 75 ciclos/mm. Isso foi conferido pelo erro de distância: com a `afc` o erro mediano na validação fica em 31–43 µm nos quatro conjuntos, contra 48 µm da cega nos dois limpos; com redução 8× aparecem 5–9 % de falhas grosseiras (`tab_dist_focus_val`).

## 4. O que isso muda no paper (sugestões, sem editar o paper)

Os pontos estão nas Seções 1 e 2. Frases para adaptar (todas as macros existem em `numbers_distancia.tex`):

- "With the distance fixed within a session, the cheap search done once per session gives the open-set F1 of a search on every frame (paired difference \DistPairSessionFiveRecAfscMinusRecAf\ with 5\,\% between sessions) at \DistTimeRecAfscFrontGpuBigMs~ms per frame on one GPU, the front end of a reconstruction at $z_0$ (\DistTimeRecZZeroFrontGpuBigMs~ms) and less than the focal stack (\DistTimeBankJitFrontGpuBigMs~ms)."
- "Against the blind search on every frame, the front end of the focal stack is \DistTimeRecAfFrontRatioGpuBig$\times$ cheaper on one GPU and \DistTimeRecAfFrontRatioCpuBig$\times$ on one CPU core (\DistTimeRecAfTotalRatioGpuBig$\times$ and \DistTimeRecAfTotalRatioCpuBig$\times$ end to end); against a cheap search on every frame, only \DistTimeRecAfcFrontRatioGpuBig$\times$ and \DistTimeRecAfcFrontRatioCpuBig$\times$ (\DistTimeRecAfcTotalRatioGpuBig$\times$ and \DistTimeRecAfcTotalRatioCpuBig$\times$ end to end)."
- "The fragility of the autofocus under strong shot noise and a narrow beam belonged to the blind search at the full resolution of the sensor: the same Tamura criterion on the amplitude averaged $4\times4$ over $\pm$10\,\% of $z_0$ costs \DistSearchBlindOverAfcGpu$\times$ less, lowers the gross failures from \DistErrFullwellFiveZeroZeroAfGross\,\% to \DistErrFullwellFiveZeroZeroAfcGross\,\% and from \DistErrBeamNarrowAfGross\,\% to \DistErrBeamNarrowAfcGross\,\%, and recovers \DistPairFullwellFiveZeroZeroRecAfcMinusRecAf\ and \DistPairBeamNarrowRecAfcMinusRecAf\ of open-set F1."
- "With this cheap search done once per mounting, reconstructing is cheaper than the focal stack of five distances once a mounting yields more than \DistNstarBankJitAfcGpu\ frames on one GPU and \DistNstarBankJitAfcCpu\ on one CPU core."
- "The focal stack keeps a constant cost with no search, and under strong shot noise its F1 is \DistCritFullwellFiveZeroZeroBankJitDiff\ above the best conventional flow; under a narrow beam it loses \DistPairBeamNarrowBankJitMinusRecAfc\ against the cheap search."
- "A tilted slide is no argument for the stack: at 15$^\circ$ it differs from the cheap search by \DistFramePairTiltFifteenBankJitMinusRecAfc\ (\DistFramePairSignTiltFifteenBankJitMinusRecAfc\ repetitions with that sign)."

Para o critério: `\DistCritMetCountA` (1) e `\DistCritMetCountB` (2) de `\DistCritRows` (24) linhas; vereditos em `\DistCrit<Conjunto><Stack>VerdictA` e `...VerdictB`.

## 5. O que deu errado, o que não foi confirmado e o que não foi testado

- **Zenodo não publicado**: tars locais conferidos contra `checksums/zenodo.sha256`; `reproduce check` é 12/12 (11 tabelas mais `numbers.tex`), não 11/11.
- **Base regravado não é idêntico ao do Zenodo**: 0,0191 % dos valores dos hologramas diferem (diferença de build); `session_5` é idêntico dentro do build.
- **`full_frames_tilt0` difere dos quadros do paper** em 0,0286 % dos pixels, pelo mesmo motivo; F1 igual a 10⁻⁴.
- **E5 em duas tentativas**: a 1 não chegou ao `full_frames` por erro de ordem nosso; o responsável decidiu pela 2; GPU a 0 % mas com 6,3 GB de outro usuário; load 29–44 (GPU) e 59–89 (CPU).
- **CPU cerca de 2× mais rápida que no paper**: só razões dentro da sessão são comparáveis.
- **Empate na escolha do `afc`** que o pré-registro não previa, decidido no congelamento sem dado de teste.
- **Faixa do `afc`**: nominal ±10 %, efetiva ±13,3 %; uma imagem de `frame_5` a +13,47 % ficou fora (erro de 25,5 µm na borda); escolhida em validação com a mesma distribuição do teste; fora dela a busca falha por construção, não testado.
- **"Busca barata a cada M quadros" não foi rodada**: provavelmente custaria menos que o stack de 5 no drift lento, não medido.
- **Quadros inteiros com z por quadro só a 5 %**; `rec_afM` não rodou nos quadros inteiros.
- **Modelo próprio só na r1 e só para `rec_afc`** (maior diferença 0,006).
- **Checkpoints 0–3** passados por critérios objetivos, sem aprovação explícita do orientador.
- **Tempos dos runs de acurácia não são usados** (GPUs compartilhadas a 90–100 %).
- **Critério ambíguo**: leituras A e B dão 1 e 2 de 24 linhas; a B não cobre o caso sem convencional (`fullwell_500`); aplicado só nas janelas.
- **O prof. Sobieranski não foi consultado** sobre a inclinação plausível.
- **O subagente dos runs foi interrompido** antes do relatório dele; tudo estava no caderno e nos CSVs.

## 6. Checklist da Seção 12

O checklist item a item, com evidência, está no caderno (Etapa 4). Seis dos oito itens estão cumpridos. Dois não estão ao pé da letra:
- base idêntico ao Zenodo: diferença de build de 0,0191 % dos valores;
- tabelas de tempo com GPU e CPU: o run medido de quadros inteiros (Tabela 7) é só GPU.
