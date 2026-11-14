# Relatório: quando o focal stack economiza tempo de verdade

Protocolo: `docs/exp_distancia/PROTOCOLO.md`. Caderno: `docs/exp_distancia/CADERNO.md`. Branch `exp/distancia-autofocus`.

## 0. Origem dos números

Tabelas copiadas de `results_exp_distancia/distance/tables/*.md` sem alterar valores (ponto decimal; colunas cortadas; sem desvio padrão nas Tabelas 1 e 2). Macros em `results_exp_distancia/numbers_distancia.tex`; o resto vem do caderno. Comando: `bash scripts/exp_distancia/relatorio.sh`. Sessão de tempo `results_exp_distancia/e5/`: GPU da tentativa 2 (`e5_a2`, escolha do responsável) e um core de CPU. Revisado em 2026-11-14 com as conferências da revisão do orientador (tarefas A1–A7 do `TODO.md`; comandos e números no caderno).

## 1. Respostas

- **Q1** (z fixo por sessão): não; a busca uma vez por sessão tem o F1 da busca em todo quadro e, feita com a busca barata, custa o mesmo que `rec_z0`.
- **Q2** (z por quadro): o ganho existe contra a busca cega; contra a busca barata em todo quadro, a diferença de front end que sobra vem de detalhes de implementação (Seção 2), e o critério pré-registrado (leitura A) só vale para o stack de 5 no drift lento.
- **Q3** (busca mais barata e robusta): sim, supondo z₀ conhecido a ±13 % (Seção 3); uma busca de ±10 % sobre a amplitude reduzida 4× custa 1/78 da cega em GPU, não perde F1 e recupera os conjuntos com ruído forte e feixe estreito.
- **Q4** (inclinação): não na faixa plausível; nada muda até 5°, e a 15° a diferença a favor do stack é +0,005, em 4 de 5 repetições.

### Q1: evidência

Em `base`, `session_2` e `session_5`, `rec_afs` (busca cega no primeiro quadro da sessão) e `rec_af` (busca cega em todo quadro) diferem em 0,000 na média pareada (`tab_dist_paired`). H1 se confirma. Com n = 100, `rec_afs` custa 4,2 ms por quadro em GPU, e `rec_afsc` (a busca barata por sessão) custa o mesmo que `rec_z0` (Tabela 3). O stack de 5 perde 0,125 de F1 em `session_5` contra `rec_afc` (o sorteio de z dessa variante exagera isso; Q2). Os stacks largos perdem de 0,011 a 0,020 contra `rec_afc` nos seis conjuntos sem ruído forte nem feixe estreito, sobretudo em rejeição das classes não vistas: no base, 0,826 e 0,838, contra 0,913–0,924 dos outros fluxos (`tab_dist_rejection.md`; o AUROC cai menos, 0,966–0,967 contra 0,978–0,983, `tab_dist_auroc.md`).

Por sessão (`tab_dist_sessions`): a busca cega por sessão erra por mais de 1 % de z₀ em 4 das 8 sessões de `fullwell_500` e 7 das 8 de `beam_narrow`, e nelas `rec_afs` acerta 0,000–0,042 das classes vistas; a busca barata por sessão não erra em nenhuma (0,916–0,957).

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

**`frame_5` × `session_5`** (Tabela 2; `scripts/exp_distancia/frame_vs_session.py`). Mesmo desvio de z (5 %, sem corte), mas `session_5` sorteia 8 valores (as sessões de teste) e `frame_5` 800. Os 8 saíram desfavoráveis: −10,4, +4,8, −2,2, +11,4, −1,3, +0,8, −0,7 e −10,7 % de z₀; rms 6,9 % (percentil 95 entre sorteios de 8 de N(0, 5 %)), três além de 2σ (0,4 % dos sorteios). A curva por imagem de `frame_5` explica `session_5` sessão por sessão: `rec_z0` acerta 0,10–0,18 das classes vistas nas três sessões a ±10–11 % e `frame_5` dá 0,14 na faixa de 10–12 %; previsto para os 8 z, F1 0,745 contra 0,753 medido, e no stack de 5 0,825 contra 0,839 (os controles mostram que a previsão sai cerca de 0,01 baixa). Não é limiar (o do base, nos dois) nem a sessão (as mesmas sessões no base são normais). Com 8 sessões sorteadas de N(0, 5 %), a linha de 5 % daria em média 0,856 para `rec_z0` e 0,917 para o stack, perto de `frame_5` (0,865 e 0,924): **a linha de 5 % entre sessões da tabela de robustez do paper exagera o dano em cerca de 0,10 de F1 (`rec_z0`, `prop`) e 0,08 (stack), quase o dobro da queda esperada.** O `session_5` medido fica no percentil 5 (`rec_z0`) e 2 (stack); entre sorteios, o F1 de `rec_z0` vai de 0,75 a 0,94 (5–95 %). `frame_5` é a estimativa estável.

**Tabela 2.** `frame_5` × `session_5`, F1 open-set (`tab_dist_frame_session`, que traz também a acurácia nas classes vistas). Previsto: 100 imagens de `frame_5` por sessão, da faixa de |z/z₀ − 1| de cada uma das 8, protocolo estrito, 200 sorteios, média r1–r5. Monte Carlo: 1000 sorteios de 8 sessões de N(0, 5 %).

| métrica | fluxo | base | frame_5 | session_5 | previsto para os 8 z | Monte Carlo: média (5–95 %) | percentil do medido |
|---|---|---|---|---|---|---|---|
| F1 | rec_z0 | 0.964 | 0.865 | 0.753 | 0.745 | 0.856 (0.751–0.936) | 5 |
|  | prop | 0.963 | 0.865 | 0.749 | 0.740 | 0.855 (0.750–0.934) | 5 |
|  | bank_jit | 0.963 | 0.924 | 0.839 | 0.825 | 0.917 (0.858–0.955) | 2 |

Tempo (Tabela 3). Contra `rec_af`, o front end do stack de 5 é 35,71× mais barato em GPU e 49,10× em CPU; fim a fim, 1,71× e 5,75×. Contra `rec_afc` sobram 1,28× e 1,39× no front end, que vêm do estágio `channels` (Seção 2b), e 1,01× e 1,04× fim a fim; nada disso é argumento. Os stacks largos, os únicos que seguram o F1 a 5 %, custam mais que `rec_afc` em GPU.

Critério (Tabela 4). A frase do protocolo "mais barato que o mais barato dos fluxos convencionais que atingem esse F1" admite duas leituras: **A**, os convencionais com F1 a até 0,02 do melhor (a mesma tolerância dada ao stack); **B**, os que atingem o F1 do stack. A ambiguidade era do texto do protocolo; a leitura A foi adotada na revisão do orientador de 2026-11-14, e a B fica calculada como alternativa. Na A o critério vale em 1 de 24 linhas: o stack de 5 em `walk_05` (3,52 contra 4,50 ms e 2,42 contra 3,36 s, contra `rec_afc`, diferença de F1 −0,012). A B acrescenta `frame_2`, onde na A `rec_z0` (0,955) qualifica e custa 2,93 ms; a escolha não muda a conclusão. Em `session_5` os largos falham o 0,02 por 0,0004; em `fullwell_500` os stacks passam o melhor convencional mas custam mais que `rec_z0`. Ressalvas: o critério usa o F1 das janelas (nos quadros inteiros os stacks largos ficam 0,032–0,038 abaixo de `rec_afc`, `tab_dist_frames_paired.md`), e a vantagem que decide `walk_05` é a dos canais (Seção 2b).

n\* (Tabela 5, Figura 1) é o número de quadros por montagem acima do qual buscar uma vez por montagem fica mais barato que o stack: T_busca / D, com D = T_camada − T_conv. Para o stack de 5, na conta completa (T_conv = flat field + back-propagation + canais, regra 8.4), D é 0,60 ms em GPU (17 % da camada) e 0,106 s em CPU (4 %), diferença de dois tempos de 2,4 s. Regra (fixada antes de olhar a tabela): se mover T_camada e T_conv em ±3 % em sentidos opostos troca o sinal de D, ou muda n\* mais que um fator 2, o cruzamento não é resolvido pela medição. As três células do stack de 5 em CPU caem na regra (D vai de +0,25 a −0,04 s): **o stack de 5 custa o mesmo que uma reconstrução, sem ponto de cruzamento preciso**. Em GPU ficam no limite (2,0–3,9 quadros com a busca barata, 155–304 com a cega; as duas tentativas dão 2,6 e 2,7), e um estágio não cobrado de 0,36 ms (Seção 2b) comeria 60 % de D. Os stacks largos custam mais que uma reconstrução (D de 26–51 % da camada) e com a busca barata têm n\* abaixo de 2.

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


**Tabela 4.** Critério da Seção 3 do protocolo (`tab_dist_criterion`): F1 das janelas, front end do quadro inteiro (Tabela 3). Convencionais: `rec_z0`, `rec_af`, `rec_afs`, `rec_afsc`, `rec_afM`, `rec_afc`, `rec_afr`. Veredito: leitura A (a reportada); B, a alternativa. Fora de "not cheaper"/"F1 fails", o veredito foi decidido contra `rec_afc`, exceto `frame_2`/`bank_jit` e `fullwell_500` na A (contra `rec_z0`) e `fullwell_500` na B (sem convencional).

| conjunto | melhor convencional (F1) | stack | stack − melhor (mesmo sinal) | F1 a 0,02 | veredito (A) | B (alternativa) |
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


**Tabela 5.** n\* no quadro inteiro (`tab_dist_breakeven`; valores crus e ±1 % em `tab_dist_breakeven.csv`). Completa: n\* = T_busca / D, D = T_camada − (T_flat_field + T_backprop + T_canais); simplificada: D = T_camada − T_backprop. "±3 %": n\* com T_camada e T_conv movidos 3 % em sentidos opostos. "≈ same cost": o sinal de D muda dentro de ±3 % (regra no texto). "cru": o valor calculado, só para registro.

| stack | busca | GPU busca (ms) | GPU D (ms; % camada) | GPU n\* | GPU ±3 % | GPU simpl. | CPU busca (s) | CPU D (s; % camada) | CPU n\* | CPU cru | CPU ±3 % | CPU simpl. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bank_jit | blind | 123 | 0.60 (17 %) | 205 | 155–304 | 48 | 116 | 0.106 (4 %) | ≈ same cost | 1099 | 470–never | 83 |
|  | afc | 1.6 |  | 2.6 | 2.0–3.9 | 0.6 | 1.0 |  | ≈ same cost | 9.9 | 4.2–never | 0.7 |
|  | afr | 11.2 |  | 19 | 14–28 | 4.4 | 9.5 |  | ≈ same cost | 90 | 38–never | 6.7 |
| bank_wide | blind | 123 | 1.80 (38 %) | 68 | 61–78 | 33 | 116 | 0.824 (26 %) | 141 | 141 | 118–176 | 55 |
|  | afc | 1.6 |  | 0.9 | 0.8–1.0 | 0.4 | 1.0 |  | 1.3 | 1.3 | 1.1–1.6 | 0.5 |
|  | afr | 11.2 |  | 6.2 | 5.5–7.1 | 3.0 | 9.5 |  | 12 | 12 | 9.6–14 | 4.5 |
| bank_w2 | blind | 123 | 3.01 (51 %) | 41 | 38–45 | 25 | 116 | 1.784 (44 %) | 65 | 65 | 59–73 | 38 |
|  | afc | 1.6 |  | 0.5 | 0.5–0.6 | 0.3 | 1.0 |  | 0.6 | 0.6 | 0.5–0.7 | 0.3 |
|  | afr | 11.2 |  | 3.7 | 3.4–4.1 | 2.3 | 9.5 |  | 5.3 | 5.3 | 4.8–6.0 | 3.1 |


![Custo do front end por quadro em função de n](img/fig_dist_breakeven.png)

**Figura 1** (`fig_dist_breakeven`). Front end por quadro inteiro contra n, quadros por busca (log). Curvas: buscas cega e barata uma vez por montagem. Retas: os três stacks, `rec_z0` e a busca barata em todo quadro. Círculos: n\*; cinza, "≈": cruzamento não resolvido pela medição (regra da Tabela 5). (a) Uma GPU, mínimo. (b) Um core de CPU, mediana.

![Custo contra F1 nos quadros inteiros](img/fig_dist_cost_f1.png)

**Figura 2** (`fig_dist_cost_f1`). Custo em uma GPU (log; somas de estágios) contra F1 fim a fim nos quadros inteiros; melhor é para cima e para a esquerda. (a) z fixo por sessão, front end. (b) O mesmo, com o detector. (c) z mudando 5 % por quadro, front end. (d) O mesmo, com o detector.

### Q3: evidência

A `afc` (`r10b-b4-tog`) busca em ±10 % de z₀, com 7 + 11 candidatos, sobre a amplitude reduzida 4 × 4 por média, com o ToG do paper: 18 reconstruções de 1/16 dos pixels. No quadro inteiro custa 78× menos que a cega em GPU e 111× menos em CPU (`\DistSearchBlindOverAfcGpu`, `\DistSearchBlindOverAfcCpu`). Nos seis conjuntos limpos, `rec_afc` − `rec_af` é no máximo 0,0005 em módulo na média pareada (`scripts/exp_distancia/paired_check.py`). Sob `fullwell_500` ganha +0,179 e sob `beam_narrow` +0,527, 5/5. A falha grosseira cai de 70,2 % para 1,8 % e de 74,0 % para 0,2 % (`tab_dist_focus.md`). A `afr` (±15 %, redução 2×, campo suavizado com σ = 2 px) erra menos e tem o mesmo F1, mas custa cerca de 7× (GPU) e 9× (CPU) a `afc`. Com um modelo treinado nas reconstruções da `afc` (r1), o F1 muda no máximo 0,006 (`tab_dist_own`).

O que consertou o ruído aparece na validação (`tab_dist_focus_val`). Falhas grosseiras em `fullwell_500` / `beam_narrow`: busca cega 70,6 / 49,9 %; só estreitar a faixa 66,9 / 21,9 %; só reduzir 4× 1,0 / 12,1 %; só suavizar 0,7 / 5,7 %; estreitar e reduzir (a `afc`) 0,9 / 0,9 %. O que resolve é tirar as altas frequências antes do ToG, por média ou por suavização; o critério de Tamura não precisou mudar, e estreitar sozinho não resolve. A frase do paper deve dizer "como o autofocus cego na resolução do sensor", não "como o autofocus com o critério de Tamura", sem sugerir que só a redução funciona.

### Q4: evidência

Até 5° nenhum fluxo muda o F1 em mais de 0,001 (caderno, E4). A 15°, `rec_z0`, `rec_af` e `rec_afc` perdem cerca de 0,008 e o stack de 5 perde 0,0021 (Figura 3; `tab_dist_frames.md`). A diferença pareada stack de 5 − `rec_afc` é +0,000 a 10° (3/5) e +0,005 a 15° (4/5) (`tab_dist_frames_paired.md`). O foco por objeto em faixa larga (`rec_edfw`) fica plano, mas custa 210 ms de front end em GPU e 166 s em CPU, 2,16× o stack de 5 fim a fim no run medido (Tabela 6). A perda só aparece entre 10° e 15°: pela regra do E4, é limite da simulação, não vantagem do método.

![F1 contra a inclinação da lâmina](img/fig_dist_tilt.png)

**Figura 3** (`fig_dist_tilt`). F1 fim a fim nos quadros inteiros contra a inclinação da lâmina (eixo de baixo, graus). Eixo de cima: variação de z na borda do quadro, 3,2 mm × tan θ, em µm. Uma linha por fluxo. Painel único.

## 2. Tempo: o que a medição mostra além do combinado

**(a) O fim a fim é do detector.** Nas somas de estágios o YOLO custa 166,82 ms de 170–175 ms em GPU para os fluxos baratos (95–98 %; Tabela 3) e 21,37 s de 22,8–26,2 s num core de CPU (82–94 %). No run medido o detector custa 178,1 ms de 186–205 ms (Tabela 6).

**(b) O que sobra contra a busca barata é detalhe de implementação.** `channels` (escala de cada canal da entrada da rede pelo seu percentil 99,9 com `torch.quantile`, só no fluxo convencional) custa 1,78 ms em GPU e 1,19 s em CPU, mais que a back-propagation (0,97 ms; 1,01 s). Sem esse estágio, isto é, com uma escala fixa calibrada uma vez, `rec_afc` custaria 4,50 − 1,78 = 2,72 ms contra 3,52 ms do stack de 5 em GPU (0,77×) e 3,36 − 1,19 = 2,17 s contra 2,42 s em CPU (0,90×), e `rec_z0` 1,15 ms e 1,12 s. A escala fixa **não foi testada em F1**: o percentil faz parte da entrada com que a rede foi treinada, e a escala fixa ainda custaria uma passada elemento a elemento, não medida. Há também um estágio que a soma não cobra dos convencionais: no run medido, converter a entrada de 3 canais para float e centrá-la custa 0,36 ms em GPU (a camada do stack já inclui isso para o seu canal; em CPU não foi medido); e, no sentido oposto, o embedding do stack (15 canais) custa 1,0–1,9 ms a mais que o dos convencionais, o que a soma também não cobra (só entra no fim a fim). Na janela de 640 px em GPU, o stack de 5 (0,19 ms) é mais barato que a própria reconstrução em z₀ (0,59 ms) (`tab_dist_time`). **Nem o 1,28× nem as contas acima são argumento para o paper.**

**(c) Ler o blank frame pesa mais que a busca barata.** No run medido, os fluxos de reconstrução gastam cerca de 18 ms lendo quadro e blank frame (float32, 3840 × 2748 × 4 bytes ≈ 42 MB) e normalizando; os de camada, 2,8 ms (Tabela 6). Esses 15 ms superam todas as diferenças de cálculo entre os fluxos com busca barata e os stacks e não têm a ver com a busca; num instrumento o blank frame ficaria na memória, e então `rec_afc` ficaria em cerca de 11,5 ms sem o detector, contra 11,1 do stack de 5 (1,08× → cerca de 1,00× com o detector). Também é detalhe de implementação, não argumento. A Tabela 3 (cálculo, GPU e CPU, sem disco) é a que entra no critério e em n\*; a Tabela 6 mostra o pipeline como está implementado (só GPU).

**(d) A CPU desta sessão é cerca de 2× mais rápida que a do paper** (back-propagation 1,01 contra 2,19 s; busca cega 116,44 contra 238,73 s; Seção 2.3 do protocolo), com outra carga (load 59–89 aqui; cerca de 230 no paper). Em GPU os estágios principais batem com o paper a menos de 4 %, menos o YOLO (166,82 contra 221,7 ms). Só comparamos razões dentro da nossa sessão.

**Tabela 6.** Run medido de quadros inteiros (`e5/full_frames_time.csv`, uma GPU; `tab_dist_time_measured`). Grupos: medianas de cada grupo. "sem detector": mediana da soma por quadro (os grupos não somam exatamente a ela). Total = sem detector + detector (178,1 ms). † busca no primeiro quadro de cada sessão, dividida pelos 5 quadros da sessão.

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

**A faixa da busca barata.** A `afc` supõe z₀ conhecido dentro da faixa dela: nominal ±10 %, efetiva ±13,3 %, porque a passada fina vai um passo grosso além do melhor candidato. É o que uma bancada calibrada dá (o maior desvio do teste, +13,47 % numa imagem de `frame_5`, ficou na borda, com erro de 25,5 µm). Fora dessa faixa a busca falha por construção; isso não foi testado. O stack tem as suas suposições: α calibrado nas imagens de treino e desvios dentro do jitter de treino (em `frame_5` o stack de 5 fica com F1 ≥ 0,94 até 6 % de desvio e cai depois: 0,89 em 6–8 %, 0,74 em 8–10 %; caderno A1).

**A redução 4× antes da busca.** O LED de 10 nm e o pinhole de 100 µm deixam pouco contraste acima de cerca de 70 ciclos/mm (Fig. 2b do paper). Reduzir 4× leva o Nyquist de 299 para cerca de 75 ciclos/mm. Isso foi conferido pelo erro de distância: com a `afc` o erro mediano na validação fica em 31–43 µm nos quatro conjuntos, contra 48 µm da cega nos dois limpos; com redução 8× aparecem 5–9 % de falhas grosseiras (`tab_dist_focus_val`).

## 4. O que isso muda no paper (sugestões, sem editar o paper)

Os pontos estão nas Seções 1 a 3. Nenhuma frase usa a razão de front end contra a busca barata (1,28×/1,39×) nem um n\* preciso. Frases para adaptar (todas as macros existem em `numbers_distancia.tex`):

```latex
With the distance fixed within a session, the cheap search done once per session gives the open-set
F1 of a search on every frame (paired difference \DistPairSessionFiveRecAfscMinusRecAf\ with 5\,\%
between sessions) at the cost of a reconstruction at $z_0$ (\DistTimeRecAfscFrontGpuBigMs\ against
\DistTimeRecZZeroFrontGpuBigMs~ms of front end per frame on one GPU).

No route to the distance is cheaper in a way that matters: end to end, the detector takes
\DistStageYoloTiledGpuBigMs~ms of the \DistTimeRecZZeroTotalGpuBigMs~ms of a reconstruction at $z_0$
on one GPU, so that a cheap search on every frame and the focal stack cost the same end to end
(ratio \DistTimeRecAfcTotalRatioGpuBig\ on one GPU, \DistTimeRecAfcTotalRatioCpuBig\ on one CPU core);
only the blind search on every frame costs more (\DistTimeRecAfTotalRatioGpuBig$\times$ and
\DistTimeRecAfTotalRatioCpuBig$\times$ the stack).

The fragility of the autofocus under strong shot noise and a narrow beam belonged to the blind
search at the full resolution of the sensor: the same Tamura criterion on the amplitude averaged
$4\times4$ over $\pm$\DistSearchAfcRangePct\,\% of $z_0$ costs \DistSearchBlindOverAfcGpu$\times$
less, lowers the gross failures from \DistErrFullwellFiveZeroZeroAfGross\,\% to
\DistErrFullwellFiveZeroZeroAfcGross\,\% and from \DistErrBeamNarrowAfGross\,\% to
\DistErrBeamNarrowAfcGross\,\%, and recovers \DistPairFullwellFiveZeroZeroRecAfcMinusRecAf\ and
\DistPairBeamNarrowRecAfcMinusRecAf\ of open-set F1.

This narrow search assumes that $z_0$ is known within its range ($\pm$\DistSearchAfcRangePct\,\%
nominal, $\pm$\DistSearchAfcRangeEffPct\,\% with its fine pass), as on a calibrated bench; beyond it
the search fails by construction.

With this cheap search done once per mounting, the focal stack of five distances costs about as much
as one reconstruction: its layer exceeds what a reconstruction costs besides the search by
\DistNstarDenBankJitGpu~ms on one GPU and \DistNstarDenBankJitCpu~s on one CPU core
(\DistNstarDenShareBankJitGpu\,\% and \DistNstarDenShareBankJitCpu\,\% of the layer), too little for
the measurement to give a number of frames at which one becomes cheaper than the other.

The 5\,\% row of distance between sessions rests on eight draws of the distance, three of them
beyond two standard deviations; with the distance drawn per frame (800 draws) the reconstruction at
$z_0$ keeps an open-set F1 of \DistSessFiveRecZZeroFOneFrameFive\ instead of
\DistSessFiveRecZZeroFOneMeasured, and the focal stack \DistSessFiveBankJitFOneFrameFive\ instead of
\DistSessFiveBankJitFOneMeasured.

What remains for the focal stack is that it needs no wavelength, pixel pitch, distance or blank
frame and tolerates a drift of the distance inside its training jitter: under strong shot noise its
F1 is \DistCritFullwellFiveZeroZeroBankJitDiff\ above the best conventional flow
(\DistCritFullwellFiveZeroZeroBankJitSign\ repetitions), under a narrow beam it loses
\DistPairBeamNarrowBankJitMinusRecAfc\ against the cheap search, and on full frames the wider stacks
lose \DistFramePairPaperBankWideMinusRecAfc\ and \DistFramePairPaperBankWTwoMinusRecAfc.

A tilted slide is no argument for the stack: at 15$^\circ$ it differs from the cheap search by
\DistFramePairTiltFifteenBankJitMinusRecAfc\ (\DistFramePairSignTiltFifteenBankJitMinusRecAfc\
repetitions with that sign).
```

Para o critério: `\DistCritMetCount` (1, leitura A) e `\DistCritMetCountB` (2) de `\DistCritRows` (24) linhas; vereditos em `\DistCrit<Conjunto><Stack>Verdict` (A) e `...VerdictB`. n\* crus: `\DistNstarRaw...`; `\DistNstar...` é a célula impressa ("≈ same cost" onde a regra diz).

## 5. O que deu errado, o que não foi confirmado e o que não foi testado

- **Zenodo não publicado**: tars locais conferidos contra `checksums/zenodo.sha256`.
- **Base regravado não é idêntico ao do Zenodo**: 0,0191 % dos valores dos hologramas diferem (diferença de build); `session_5` é idêntico dentro do build, e foi regravado de novo em 2026-11-14 (A2).
- **`full_frames_tilt0` difere dos quadros do paper** em 0,0286 % dos pixels (reconferido); F1 igual a 10⁻⁴. Regravados neste build com o código do paper, os primeiros 8 quadros saem iguais a `full_frames_tilt0` bit a bit: a diferença é do build (ou da cópia que gerou os publicados), não do código do estudo.
- **Pareamento das cenas conferido** (A2): anotações idênticas menos profundidade e z em todos os conjuntos novos, z de cada imagem igual ao do desenho, inclinação com o azimute da sessão; uma imagem de `frame_5` com z movido 0,0001 % difere da do base em 0,07 % dos pixels.
- **A linha de 5 % entre sessões do paper** exagera o dano (8 sorteios desfavoráveis; Q2).
- **Contas de tempo com assimetrias pequenas**: a soma de estágios não cobra 0,36 ms (GPU) de conversão da entrada dos convencionais nem o embedding mais caro do stack (Seção 2b); a correção pediria um estágio novo no `timing.py`.
- **E5 em duas tentativas**: a 1 não chegou ao `full_frames` (erro de ordem nosso); vale a 2; n\* muda 3–4 % entre as duas.
- **Empate na escolha do `afc`**, decidido no congelamento sem dado de teste.
- **Faixa do `afc`** (±13,3 % efetiva) suposta conhecida; fora dela, não testado (Seção 3).
- **Critério**: leitura A adotada (1 de 24 linhas); a B (2 de 24) não cobre o caso sem convencional (`fullwell_500`); aplicado só nas janelas.
- **Não testado**: escala fixa no lugar do percentil dos canais (só a conta, Seção 2b); "busca barata a cada M quadros" (provavelmente custaria menos que o stack de 5 no drift lento); `full_frames` em CPU; quadros inteiros com z por quadro só a 5 %; `rec_afM` nos quadros inteiros.
- **Modelo próprio só na r1 e só para `rec_afc`** (maior diferença 0,006).
- **Checkpoints 0–3** passados por critérios objetivos, sem aprovação explícita do orientador.
- **O prof. Sobieranski não foi consultado** sobre a inclinação plausível.

## 6. Checklist da Seção 12

O checklist item a item, com evidência, está no caderno (Etapa 4). Seis dos oito itens estão cumpridos. Dois não estão ao pé da letra:
- base idêntico ao Zenodo: diferença de build de 0,0191 % dos valores;
- tabelas de tempo com GPU e CPU: o run medido de quadros inteiros (Tabela 6) é só GPU.
