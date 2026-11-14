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

## 2026-11-14, 13:20 — Parte A suspensa por ordem do orientador (piloto)

- Ordem recebida do responsável às 13:18 (instrução do orientador em `PROTOCOLO_Z.md`): segurar a parte A até
  fechar o z da bancada simulada. Às 13:18:51 matei a sessão `tmux` `res_build`
  (`scripts/exp_resolucao/build_sets.sh 5`, GPU 5); nenhum processo meu ficou rodando.
- O que estava feito: T0 (teste pareado do enrollment), T2 (b pelo modelo e às cegas; b = 4 registrado às 13:12)
  e o comando `reduce` com o pixel efetivo no código (commit `eb5dedf`; 7 testes novos em
  `tests/test_resolution.py`, incluindo α igual em b = 1, 2, 4 num holograma sintético).
- Conjuntos reduzidos no disco:
  - completos: `data/realistic_b1` (com `aux/r1`; 2,8 GB) e `data/variants_val_b1/{fullwell_500,beam_narrow}`
    (552 MB), todos com b = 1. Conferência byte a byte (`python scripts/exp_resolucao/check_b1.py`, 5 s, CPU):
    holograms, backgrounds, annotations, metadata, sessions, dust e `aux/r1_*` idênticos aos originais; o
    `physics.json` difere só pelas chaves novas `pixel` e `reduction`. O cache `rec_z0.npy` de `realistic_b1` não foi
    construído (a conferência acusa "missing" para ele).
  - parcial: `data/realistic_b2` (só `holograms.npy`, interrompido no meio). Apaguei esse diretório; fui eu que o
    criei nesta etapa. Nenhum outro arquivo foi apagado.
- O que não foi feito: as conferências (a) com os caches e os números de r1, (b) α nos dados reais em cada b e
  (c) figura das caixas; toda a T4 (nenhum conjunto com b = 2, 4, 8, nenhum treino, nenhum modelo em
  `models_exp_resolucao/`). Os scripts `alpha_b.py`, `train_pilot.sh` e `build_sets.sh` estão commitados
  (`02efd17`) como estavam, sem ter rodado (exceto o início de `build_sets.sh` descrito acima).
- **Nenhum split de teste de conjunto reduzido foi avaliado** (nenhuma avaliação de nenhum tipo rodou nesta etapa:
  `results_exp_resolucao/` só tem `enroll_paired.csv`, `envelope_*.csv` e `spectrum_*.csv`; não existe
  `results_exp_resolucao/eval/`). O T0 leu resultados de teste já existentes do paper, na resolução cheia.
- Estado da árvore: `env -u HOLO_RESULTS python -m pytest -q` → 44 passed; `reproduce check` → 13/13.

## 2026-11-14, 13:27 — Z1: a unidade do z no gerador original e no nosso (piloto)

Pedido de `PROTOCOLO_Z.md`, item 1. Nada foi rodado; só leitura de código e de texto.

**O gerador original** (o da Manu): `OLD-WRONG-projeto-e-testes/data/matlab_generation/{CV_FR_focus.m,run_z.m}`.
Há três cópias idênticas (md5 `a4985664…` e `baf1f123…`): essa, `OLD-WRONG-projeto-e-testes/holo_openset/octave/`
e `microscopia2/data/cbms2024/matlab_generation/` (a do CBMS 2024). A chamada, `run_z.m`, linha 9:

```matlab
[ realp imagp ] = CV_FR_focus(im, 1.67e-6, 1.67e-6, -385e-9 * 50000, 385e-9);
```

e o kernel, `CV_FR_focus.m`, linhas 9, 12, 19–22, 25–30 e 36–39:

```matlab
function [realp, imagp] = CV_FR_focus(object, dx, dy, z, lambda)
    k=2*pi/lambda;
    Lx = dx*Nxx;   Ly = dy*Nyy;
    criti = dx*Lx/lambda;
    dfx = 1./Lx;   dfy = 1./Ly;
    u = ones(Nyy,1)*[-Nxx/2:Nxx/2-1]*dfx;   v = [-Nyy/2:Nyy/2-1]'*ones(1,Nxx)*dfy;
    if z<=criti
        H = exp(i*k*z).*exp(-i*pi*lambda*z*(u.^2+v.^2));
```

- z entra em metros, no mesmo produto λ z (u² + v²) que o pixel de 1,67 µm (u em ciclos/m, Δf = 1/(N dx)). O valor
  é z = −385e-9 × 50 000 m = −19,25 mm: "50k" é 50 000 λ, escrito como produto explícito. Não é pixel, µm nem número
  de Fresnel. O sinal negativo não muda o holograma salvo (`run_z.m` grava só `realp`, e cos(πλzf²) é par em z).
- Achado lateral: `criti = dx·Lx/λ` é a distância crítica de amostragem do kernel de função de transferência
  (z ≤ N dx²/λ). Com N = 640, criti = 4,64 mm, menor que 19,25 mm; o teste `z<=criti` só passa porque z é
  negativo. Nas imagens 640 × 640 do gerador original o chirp do kernel fica subamostrado nas altas frequências. No
  nosso simulador o campo é 4096 × 4096 (janela 640 + 2 × 1728 de margem): criti = 29,7 mm > 19,25 mm.
- A porta em Python do mesmo gerador (`OLD-WRONG-projeto-e-testes/src/e12_generate_synthetic_originals.py`, linhas 29–32
  e 164) usa as mesmas constantes: `HOLOGRAPHY_Z = -385e-9 * 50000`,
  `transfer = np.exp(1j * k * z) * np.exp(-1j * np.pi * wavelength * z * (u**2 + v**2))`, e cita
  `data/matlab_generation/CV_FR_focus.m` como referência.

**O nosso simulador**, `holo_openset/sim/physics.py`: linha 46, `Z0 = 385e-9 * 50000` ("nominal sample-to-sensor
distance, 19.25 mm"); linhas 118–121, `freq_sq` com `fftfreq(..., d=pixel)` (ciclos/m, pixel 1,67e-6 m); linhas
125–129, `propagate(u, z, ...)`: `h = torch.exp(-1j * (math.pi * wavelength * z) * q)`; linhas 203 e 217, cada sessão
propaga com `z = session['z']` = z0 (1 + N(0; 0,005)) (`sim/scene.py`, linha 195). Mesma unidade (metros) e mesmo
valor do gerador original; a única diferença é o sinal (aqui z > 0 é a propagação da amostra ao sensor).

**O que diz o artigo da bancada** (Sobieranski et al. 2015; o PDF e o HTML que outro agente baixou em
`referencias/z/sob2015/`, e o suplementar .docx que baixei para o scratchpad e li como texto):
- Texto principal: "LED was placed in a cylindrical structure with 100 µm diameter pinhole located 15 cm away from the
  sensor. [...] the distance between sample and electronic detector is as small as possible." Legenda da Fig. 2:
  "Diffractive distances from the first to fourth columns are z = [30k, 45k, 60k, 70k] (k = x 1000), according to
  Equation (S3) of Supplementary Information".
- Suplementar, seção "Diffraction Calculation": "**We used z×λ to compute the distance between the object and the
  detector plane**, where image is formed with a wavelength of the light-source λ. **For HR holograms, a scale factor k
  is applied to up-sampling the distance z and make diffraction equivalent to the LR and HR images.**" A Eq. (S3) é a
  função de transferência H com k = 2π/λ (a fórmula é um objeto OLE que não li).
- Leituras possíveis, sem decidir:
  1. z da rotina = (parâmetro) × λ com o pixel de 1,67 µm: 50k → 19,25 mm; os z da Fig. 2 → 11,55; 17,33; 23,10;
     26,95 mm. É o que o código do gerador original faz.
  2. Se o parâmetro foi aplicado a imagens HR (super-resolvidas) tratadas com o pixel de 1,67 µm, a distância física
     seria parâmetro × λ / s², com s o fator de super-resolução (as frequências escalam com 1/pixel e χ = πλz f²):
     50k → 4,8 mm com s = 2; 2,1 mm com s = 3; 0,39 mm com s = 7. O suplementar diz que o fator multiplica o z para HR,
     mas não diz qual é, nem se a Fig. 2 é LR ou HR.
  3. O `run_z.m` aplica 50k a imagens sintéticas de letras ("ScatteredLetters", 640 × 640), não a hologramas da
     bancada: é um parâmetro de simulação do laboratório, não uma distância medida.
- Coerência com as resoluções do suplementar (USAF: quadro único 2,76 µm, 9 quadros 2,19 µm, 49 quadros 1,55 µm),
  pelo modelo do envelope (E < 0,1, meia-pitch = 1/(2 f_c), D = 100 µm, L = 15 cm, banda 10 nm suposta): 2,76 µm pede
  z ≤ 4,3 mm (4,5 sem o termo do pixel); 2,19 µm, z ≤ 2,8 mm; 1,55 µm, z ≤ 1,3 mm (1,5 sem o pixel), já acima do
  Nyquist. Com z = 19,25 mm o envelope deixa meia-pitch de 6,9 µm. Isso depende da banda de 10 nm, que o artigo não
  dá, e do limiar 0,1, que é uma convenção nossa.

## 2026-11-14, 13:27 — Z2: a tabela do orientador refeita com o modelo do pacote (piloto)

- Onde: container, CPU. `python scripts/exp_resolucao/envelope_table.py` (10 s). Saída:
  `results_exp_resolucao/envelope_z.csv` (todas as colunas; uma linha por z). Módulo novo `holo_openset/sim/envelope.py`
  (testado: reproduz a conta do painel (b) de `fig_fresnel` ponto a ponto).
- Borrão da fonte = diâmetro da imagem do pinhole no sensor, d = D z / L, D = 100 µm, L = 15 cm (o simulador e a eq.
  do paper tomam L do pinhole à **amostra**; o artigo diz 15 cm do pinhole ao **sensor**, o que daria L = 15 cm − z:
  a 19,25 mm o corte cairia de 72,4 para 66,8 ciclos/mm; a 2 mm ou menos, não muda nada). Sem outro fator.
- Corte = menor f com |E| < limiar, f ao longo de um eixo do sensor. Meia-pitch = 1/(2 f_c).

| z | d (µm) | f_c E < 0,1 | sem pixel | f_c E < 0,05 | sem pixel | b_max (0,1 / 0,05) | termo que manda em f_c (0,1): banda / pinhole / pixel | meia-pitch (µm) | sensor subamostra? | Fresnel de 50 µm | raio do padrão de 50 µm (µm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 19,25 mm | 12,83 | 72,37 | 72,60 | 78,25 | 78,46 | 4 / 3 | **pinhole**: 0,405 / 0,253 / 0,976 | 6,91 | não | 0,084 | 561 |
| 5 mm | 3,33 | 167,63 | 170,37 | 180,40 | 183,00 | 1 / 1 | **banda**: 0,173 / 0,661 / 0,876 | 2,98 | não | 0,325 | 348 |
| 2 mm | 1,33 | 266,40 | 278,06 | 286,55 | 297,67 | 1 / 1 | **banda**: 0,166 / 0,852 / 0,705 | 1,88 | não (corte a 89 % do Nyquist) | 0,812 | 230 |
| 1 mm | 0,67 | 362,24 | 397,19 | 390,70 | 424,70 | 1 / 1 | **banda**: 0,216 / 0,930 / 0,498 | 1,38 (1,67 num quadro) | **sim** | 1,623 | 140 |

(f em ciclos/mm; Nyquist 299,4. "Fresnel de 50 µm" = a²/(λz) com a = 25 µm. "Raio do padrão" = 25 µm + λ z min(f_c,
Nyquist): até onde chegam as franjas que o sensor ainda registra, eq. `eq:spread`.)

- **De onde vêm as diferenças para a tabela do orientador** (73, 170, 278, 397): os números dele são exatamente o
  nosso modelo **sem o termo de abertura do pixel** (coluna "sem pixel": 72,6; 170,4; 278,1; 397,2). A banda (σ = FWHM
  / 2,355) e o pinhole (L = 15 cm da amostra) são iguais nos dois. A equação do paper (`eq:envelope`) **inclui** o
  pixel (sinc(Δ f_x) sinc(Δ f_y)), e o painel (b) de `fig_fresnel` também ("all three"). O pixel pesa pouco a
  19,25 mm (0,976 em f_c: 72,4 contra 72,6) e cada vez mais perto do sensor (0,705 a 2 mm: 266 contra 278; 0,498 a
  1 mm: 362 contra 397).
- b_max: igual ao do orientador nas quatro distâncias (4, 1, 1, 1). Com o limiar 0,05, a 19,25 mm dá 3.
- Onde o sensor subamostra o holograma: a 1 mm, com ou sem pixel (o contraste passa de 0,1 até 362–397 ciclos/mm,
  acima do Nyquist de 299). A 2 mm o corte fica logo abaixo do Nyquist (266 com pixel; 278 sem; 298 sem pixel e com
  limiar 0,05). Pelo modelo, a fronteira (f_c = Nyquist com E < 0,1) fica em z = 1,56 mm (1,73 mm sem o pixel).
- Termo que manda: a 19,25 mm, a imagem do pinhole (60 % da queda em log, contra 39 % da banda); a 5, 2 e 1 mm, a
  banda do LED (76 %, 78 %, 67 %); o pixel chega a 30 % a 1 mm. Ou seja, perto do sensor o que limita é a banda de
  10 nm suposta, não o pinhole.

## 2026-11-14, 13:27 — Z3: tabela do envelope para qualquer configuração (piloto)

- Função: `holo_openset.sim.envelope` (`Setup(wavelength, bandwidth, pinhole, source_distance, z, pixel)`, em metros;
  `terms`, `envelope`, `cutoff`, `summary`). Convenções no docstring: banda gaussiana com σ = FWHM/2,355; d = D z / L
  com L do pinhole à amostra; f ao longo de um eixo do sensor; corte = primeira f com |E| < limiar, procurada até
  2000 ciclos/mm; b_max = max(1, ⌊1/(2Δ f_c)⌋); meia-pitch = 1/(2 f_c) (largura de linha da carta USAF) e, num
  quadro, max(meia-pitch, Δ); o corte sem o termo do pixel também sai.
- Uso: `python scripts/exp_resolucao/envelope_table.py --configs <csv> --out <csv>`. Colunas do csv: `name,
  wavelength_nm, bandwidth_nm, pinhole_um, source_distance_mm, z_mm, pixel_um` (opcional `object_um`); coluna
  ausente = valor da bancada; outras colunas (referência, página) passam para a saída. Exemplo:
  `scripts/exp_resolucao/envelope_configs_example.csv` (bancada, bancada a 2 mm, laser).
- Testes: `tests/test_resolution.py` (2 novos: o envelope da bancada é o do painel (b) da figura; o corte se move no
  sentido certo com D e a banda, e a subamostragem é marcada). `pytest` 46 passed, `reproduce check` 13/13.
