# Caderno: processar na resolução que a fonte permite

Registro de comandos, resultados e decisões da etapa descrita em `PROTOCOLO.md`. Plano e estado em `TODO.md`.
Regras: resultados em `results_exp_resolucao/`; escolhas só na validação; o que vai ao teste é registrado aqui, com
data, antes de rodar; nada em `results/` nem `expected/`.

## 2026-11-14, 13:05 — Abertura (responsável)

- Branch `exp/resolucao-fonte`, criado de `exp/distancia-autofocus` (`4e44f3a`).
- Hipóteses e critério: os do protocolo (H5, H5b, A.6), copiados em `TODO.md`, Seção 1. Nada foi rodado ainda.
- Decisões de desenho tomadas antes de rodar (R1–R7 de `TODO.md`): em particular, a imagem reduzida é guardada em
  uint8 depois de arredondar (o blank frame reduzido em float32); o piloto é r1, janelas, caixas anotadas,
  b ∈ {1, 2, 4, 8}, `raw`, `prop`, `rec_z0`, base + `fullwell_500` + `beam_narrow`, crop 64 × 64.
- **O fator b que vale para o critério sai da física (A.2) e será escrito aqui, com data, antes de qualquer avaliação
  no split de teste.** O piloto mede o F1 de teste nos quatro valores de b porque o protocolo pede a curva; nenhuma
  escolha é feita com ela. Tudo o que ainda for escolhido (tamanho do crop, armazenamento, detector) sai da
  validação.
- A partir daqui o caderno é escrito pelo subagente "piloto"; eu acrescento as minhas revisões em entradas marcadas
  "(responsável)".

## 2026-11-14, 13:10 — T0: teste pareado do enrollment (piloto)

- Onde: container da DGX, CPU, `source scripts/exp_resolucao/env.sh`. Comando:
  `python scripts/exp_resolucao/enroll_paired.py` (0,3 s). Lê só `results/eval/realistic/<fluxo>_r{1..5}.json`
  (as avaliações estritas do paper; nada foi rodado de novo). Saída: `results_exp_resolucao/enroll_paired.csv`
  (uma linha por camada × reconstrução × métrica, com a diferença de cada repetição).
- Métricas: as seis da tabela de enrollment do paper (`tab_enroll`) e as três `world5_*` que faltam (rank-1,
  rejeição das ausentes, acerto nas vistas). "Nova aceita" é `world*_new_class_acc`: a classe nova é aceita e
  correta. "Ausentes" são as 2 classes não vistas que continuam fora da galeria.
- Diferença pareada: valor da camada menos valor da reconstrução na mesma repetição. A contagem entre parênteses
  é quantas das 5 repetições têm o sinal da média (um empate exato em zero não conta).

Médias por fluxo (5 repetições):

| métrica | `prop` | `bank_jit` | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|---|---|
| k = 5, nova aceita | 0,674 | 0,654 | 0,629 | 0,546 | 0,560 | 0,573 | 0,627 |
| k = 20, nova aceita | 0,843 | 0,859 | 0,850 | 0,831 | 0,835 | 0,820 | 0,833 |
| todos, nova aceita | 0,937 | 0,943 | 0,931 | 0,929 | 0,929 | 0,931 | 0,943 |
| k = 20, rank-1 da nova | 0,880 | 0,896 | 0,872 | 0,856 | 0,856 | 0,854 | 0,886 |
| k = 20, rejeição das ausentes | 0,878 | 0,922 | 0,929 | 0,918 | 0,917 | 0,877 | 0,951 |
| k = 20, acerto nas vistas | 0,958 | 0,958 | 0,959 | 0,962 | 0,961 | 0,959 | 0,958 |
| k = 5, rank-1 da nova | 0,711 | 0,716 | 0,672 | 0,607 | 0,618 | 0,662 | 0,677 |
| k = 5, rejeição das ausentes | 0,918 | 0,915 | 0,949 | 0,926 | 0,924 | 0,876 | 0,955 |
| k = 5, acerto nas vistas | 0,958 | 0,959 | 0,959 | 0,962 | 0,961 | 0,959 | 0,958 |

`prop` menos cada fluxo de reconstrução: média da diferença pareada [mín, máx] (repetições com o sinal da média, de 5):

| métrica | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|
| k = 5, nova aceita | +0,046 [-0,077; +0,139] (3) | +0,128 [+0,011; +0,277] (5) | +0,114 [-0,001; +0,278] (4) | +0,101 [-0,059; +0,294] (4) | +0,047 [-0,036; +0,142] (3) |
| k = 20, nova aceita | -0,007 [-0,057; +0,040] (2) | +0,012 [-0,032; +0,060] (3) | +0,009 [-0,019; +0,036] (3) | +0,023 [-0,014; +0,051] (4) | +0,010 [-0,023; +0,069] (2) |
| todos, nova aceita | +0,006 [-0,017; +0,030] (4) | +0,008 [-0,004; +0,012] (4) | +0,008 [-0,003; +0,014] (4) | +0,005 [-0,006; +0,018] (4) | -0,006 [-0,028; +0,010] (4) |
| k = 20, rank-1 da nova | +0,008 [-0,027; +0,050] (3) | +0,025 [+0,008; +0,061] (5) | +0,024 [+0,005; +0,038] (5) | +0,026 [-0,009; +0,076] (4) | -0,005 [-0,037; +0,038] (3) |
| k = 20, rejeição das ausentes | -0,052 [-0,189; +0,008] (3) | -0,040 [-0,148; +0,064] (3) | -0,039 [-0,116; +0,060] (3) | +0,000 [-0,061; +0,061] (3) | -0,073 [-0,183; +0,000] (4) |
| k = 20, acerto nas vistas | -0,000 [-0,006; +0,009] (3) | -0,003 [-0,008; +0,004] (4) | -0,003 [-0,008; +0,004] (4) | -0,001 [-0,005; +0,005] (3) | +0,001 [-0,007; +0,009] (3) |
| k = 5, rank-1 da nova | +0,039 [-0,064; +0,145] (3) | +0,104 [+0,019; +0,229] (5) | +0,093 [+0,003; +0,222] (5) | +0,049 [-0,010; +0,107] (4) | +0,034 [-0,054; +0,144] (4) |
| k = 5, rejeição das ausentes | -0,031 [-0,087; +0,008] (3) | -0,008 [-0,093; +0,064] (2) | -0,006 [-0,099; +0,060] (2) | +0,042 [-0,036; +0,248] (3) | -0,037 [-0,121; +0,000] (4) |
| k = 5, acerto nas vistas | -0,000 [-0,006; +0,009] (3) | -0,004 [-0,008; +0,004] (4) | -0,003 [-0,008; +0,004] (4) | -0,001 [-0,005; +0,005] (3) | +0,000 [-0,007; +0,008] (3) |

`bank_jit` menos cada fluxo de reconstrução: média da diferença pareada [mín, máx] (repetições com o sinal da média, de 5):

| métrica | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|
| k = 5, nova aceita | +0,025 [-0,063; +0,086] (3) | +0,107 [-0,026; +0,211] (4) | +0,094 [-0,025; +0,212] (4) | +0,080 [-0,045; +0,258] (4) | +0,026 [-0,022; +0,105] (4) |
| k = 20, nova aceita | +0,009 [-0,037; +0,056] (3) | +0,028 [-0,028; +0,061] (4) | +0,024 [-0,027; +0,057] (4) | +0,039 [-0,025; +0,071] (4) | +0,026 [-0,059; +0,076] (4) |
| todos, nova aceita | +0,012 [-0,004; +0,045] (3) | +0,014 [-0,015; +0,038] (4) | +0,013 [-0,014; +0,038] (4) | +0,011 [-0,003; +0,033] (4) | +0,000 [-0,014; +0,011] (2) |
| k = 20, rank-1 da nova | +0,024 [-0,022; +0,052] (4) | +0,040 [+0,010; +0,069] (5) | +0,040 [+0,011; +0,089] (5) | +0,042 [+0,009; +0,099] (5) | +0,010 [-0,019; +0,040] (3) |
| k = 20, rejeição das ausentes | -0,007 [-0,109; +0,107] (4) | +0,004 [-0,121; +0,073] (4) | +0,006 [-0,132; +0,071] (3) | +0,045 [-0,057; +0,248] (2) | -0,028 [-0,079; +0,004] (3) |
| k = 20, acerto nas vistas | -0,000 [-0,004; +0,004] (3) | -0,003 [-0,006; +0,000] (4) | -0,003 [-0,006; -0,000] (5) | -0,000 [-0,003; +0,001] (3) | +0,001 [-0,002; +0,005] (3) |
| k = 5, rank-1 da nova | +0,044 [-0,006; +0,087] (4) | +0,110 [+0,019; +0,169] (5) | +0,098 [+0,019; +0,162] (5) | +0,054 [+0,000; +0,099] (4) | +0,039 [+0,003; +0,144] (5) |
| k = 5, rejeição das ausentes | -0,034 [-0,126; +0,022] (4) | -0,011 [-0,113; +0,067] (3) | -0,010 [-0,119; +0,093] (3) | +0,038 [-0,060; +0,285] (2) | -0,041 [-0,079; +0,012] (4) |
| k = 5, acerto nas vistas | +0,000 [-0,004; +0,005] (2) | -0,003 [-0,006; +0,001] (4) | -0,003 [-0,006; +0,001] (4) | -0,000 [-0,002; +0,002] (3) | +0,001 [-0,002; +0,005] (2) |


- O que os números dizem, sem interpretação: com k = 5, a `prop` aceita mais classes novas que todas as
  reconstruções na média, mas contra `rec_z0` e `rec_twin` só em 3 de 5 repetições, e contra `rec_z0` a diferença
  vai de −0,077 a +0,139. A rejeição das ausentes com k = 20 é menor na `prop` que em `rec_z0` (−0,052, 3 de 5,
  mínimo −0,189), `rec_af`, `rec_afc` e `rec_twin` (−0,073, 4 de 5); contra `rec_edf` é igual na média.

## 2026-11-14, 13:10 — T2(i): o b pelo modelo da bancada (piloto)

- Onde: container, CPU. `python scripts/exp_resolucao/envelope_cutoff.py` (1 s). Saídas:
  `results_exp_resolucao/envelope_cutoff.csv` e `envelope_curve.csv` (a curva E(f) a cada 0,1 ciclo/mm).
- E(f) é a eq. `eq:envelope` do paper, com as mesmas contas do painel (b) de `fig_fresnel`
  (`holo_openset/paper/figures.py`): banda gaussiana (FWHM 10 nm, σ_λ = 4,25 nm), imagem do pinhole
  (2 J1(π d f)/(π d f), d = D z / L) e pixel (sinc(Δ f)), numa direção do eixo do sensor (f_y = 0).
- f_c = a menor frequência em que |E| fica abaixo do limiar; em todos os casos |E| continua abaixo dele até o
  Nyquist (299,4 ciclos/mm). b_max = ⌊1 / (2 Δ f_c)⌋, Δ = 1,67 µm.

| distância | limiar | f_c (ciclos/mm) | b_max | banda em f_c | pinhole em f_c | pixel em f_c | d (µm) |
|---|---|---|---|---|---|---|---|
| 19,25 mm (base, `small_z0`) | 0,1 | 72,37 | 4 | 0,405 | 0,253 | 0,976 | 12,83 |
| 19,25 mm (base, `small_z0`) | 0,05 | 78,25 | 3 | 0,290 | 0,177 | 0,972 | 12,83 |
| 2 mm (`small_near`) | 0,1 | 266,40 | 1 | 0,166 | 0,852 | 0,705 | 1,33 |
| 2 mm (`small_near`) | 0,05 | 286,55 | 1 | 0,091 | 0,830 | 0,664 | 1,33 |

- Quem manda no corte: a 19,25 mm, a imagem do pinhole é o fator menor em f_c (0,253 contra 0,405 da banda;
  em log, 60 % da queda), e os dois juntos fazem o corte; o pixel quase não pesa (0,976). A 2 mm, a banda é o fator
  que manda (0,166), seguida do pixel (0,705); o pinhole quase não pesa (d = 1,3 µm). A 2 mm o corte fica a 89 % do
  Nyquist, então b_max = 1: o modelo diz para não reduzir.
- O limiar 0,05 dá b_max = 3 na base, um valor fora da grade do piloto {1, 2, 4, 8} (e 640 não é divisível por 3).

## 2026-11-14, 13:11 — T2(ii): pré-registro da regra cega (antes de calcular qualquer espectro)

Regra escrita agora, antes de abrir os hologramas; nada dela foi ajustado depois.

- Imagens: 256 hologramas do split de **treino** de cada conjunto (`realistic`, `small_z0`, `small_near`),
  sorteados com `np.random.RandomState(0).choice(ids_de_treino, 256, replace=False)`.
- Dois sinais por imagem: `I/B` (holograma em float dividido pelo blank frame da sua sessão, com B ≥ 1, como em
  `reconstruct.normalise` sem a raiz) e `I` puro. Cada um tem a média subtraída e é multiplicado por uma janela de
  Hann separável 640 × 640 (para o vazamento da borda não criar um piso falso nos eixos). Potência = |FFT|²
  dividida pela soma da janela ao quadrado, média nas 256 imagens.
- Anéis: raio inteiro k = round(√(kx² + ky²)) no grid de 640, k = 1 … 320 (até o Nyquist; os cantos além do
  Nyquist radial ficam de fora). Frequência do anel: f = k / (640 Δ) = 0,9357 k ciclos/mm.
- Piso: a mediana da potência dos anéis no quinto superior, k = 257 … 320 (240–299 ciclos/mm).
- Corte: o menor k_c tal que a potência de todos os anéis k ≥ k_c fica abaixo de **k_thr × piso, com k_thr = 2**.
  f_c = k_c / (640 Δ); b_cego = ⌊f_Nyquist / f_c⌋ = ⌊320 / k_c⌋.
- Sensibilidade (só reportada, não escolhe nada): k_thr ∈ {1,5; 2; 3}.
- O b do critério para a base será escrito na próxima entrada, comparando os dois métodos; se discordarem,
  registro os dois e não escolho.

## 2026-11-14, 13:12 — T2(ii)-(iii): espectro por anel, b às cegas e o b do critério (piloto)

- Onde: container, CPU, 4 threads. `python scripts/exp_resolucao/spectrum_rings.py` (14,5 s, os três conjuntos),
  depois `python scripts/exp_resolucao/fig_spectrum.py`. Saídas: `results_exp_resolucao/spectrum_rings.csv`
  (potência por anel, conjunto e sinal), `spectrum_cutoff.csv` (piso, k_c, f_c e b para cada k_thr) e a figura
  `docs/exp_resolucao/img/spectrum_cutoff.png`. Regra exatamente a do pré-registro das 13:11; nada mudou depois.

| conjunto | sinal | f_c (k_thr = 2) | b (k_thr = 2) | f_c (k_thr = 1,5) | b | f_c (k_thr = 3) | b | modelo f_c (E < 0,1 / 0,05) | b_max (0,1 / 0,05) |
|---|---|---|---|---|---|---|---|---|---|
| `realistic` | I/B | 72,98 | **4** | 75,79 | 3 | 70,17 | 4 | 72,37 / 78,25 | **4** / 3 |
| `realistic` | I | 72,98 | 4 | 75,79 | 3 | 70,17 | 4 | | |
| `small_z0` | I/B | 69,24 | **4** | 72,04 | 4 | 66,43 | 4 | 72,37 / 78,25 | **4** / 3 |
| `small_z0` | I | 69,24 | 4 | 72,04 | 4 | 65,49 | 4 | | |
| `small_near` | I/B | 173,09 | **1** | 190,87 | 1 | 157,19 | 1 | 266,40 / 286,55 | **1** / 1 |
| `small_near` | I | 172,16 | 1 | 188,06 | 1 | 152,51 | 1 | | |

(f_c em ciclos/mm; b = ⌊320 / k_c⌋ às cegas, ⌊1 / (2 Δ f_c)⌋ pelo modelo.)

- Legenda da figura `spectrum_cutoff.png`. (a)–(c): potência média por anel do espectro de 256 hologramas de
  treino, dividida pelo piso de ruído (a mediana dos anéis na faixa cinza, o quinto superior até o Nyquist), em
  escala log, contra a frequência em ciclos/mm; azul `I/B`, laranja `I` puro. A linha cheia horizontal é 2 × o
  piso (o limiar pré-registrado); as tracejadas verticais são o corte às cegas de cada sinal; a pontilhada preta é o
  corte do modelo (E < 0,1). (a) conjunto base a 19,25 mm; (b) letras pequenas a 19,25 mm; (c) letras pequenas a
  2 mm. (d): |E(f)| do modelo (eq. `eq:envelope`) a 19,25 mm (roxo) e 2 mm (verde-azulado), com os limiares 0,1
  (tracejado) e 0,05 (pontilhado) e os cortes correspondentes.
- Os dois métodos concordam no b nos três conjuntos: 4 na base e em `small_z0`, 1 em `small_near`. Na base, o
  corte às cegas (72,98) cai a 0,6 ciclo/mm do corte do modelo (72,37). A 2 mm os dois dão b = 1, mas os cortes não
  coincidem: o espectro encosta no piso em 173 ciclos/mm, o modelo em 266. `I/B` e `I` dão o mesmo corte (no
  máximo 1 anel de diferença).
- Sensibilidade: na base, o b fica entre 3 e 4 (k_thr = 1,5 e o limiar 0,05 do modelo dão 3); 4 está perto da
  fronteira (f_c > 74,85 ciclos/mm já daria 3). Em `small_z0` e `small_near`, nenhuma das variações muda o b.
- **b do critério pré-registrado (A.6) para o conjunto base: b = 4** (os dois métodos, com o limiar 0,1 do
  protocolo e o k_thr = 2 pré-registrado). Para os conjuntos pequenos, a regra dá b = 4 a 19,25 mm e b = 1 a 2 mm
  (não rodam no piloto).
- Até este momento nenhum conjunto reduzido existe e nenhuma avaliação de teste foi feita nesta etapa.
