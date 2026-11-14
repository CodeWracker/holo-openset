# Caderno do piloto na distância certa (1,0 mm)

Caderno do piloto aprovado em `PROTOCOLO_PILOTO_1MM.md` (instrução do orientador, na íntegra). Entradas em ordem de
tempo, a mais recente embaixo, com a hora real do relógio. Quem escreve: o responsável (planejamento, pré-registro,
revisão) e o agente que executa (marcado "(execução)"). O caderno anterior da etapa é `CADERNO.md`.

## 2026-11-14, 15:50 — P0: pré-registro do piloto (responsável)

Escrito antes de qualquer código do piloto, de qualquer gravação e de qualquer treino. Nada foi rodado.

### O que o orientador fixou (itens 1–6 de `PROTOCOLO_PILOTO_1MM.md`)

1. Distância nominal z₀ = 1,0 mm; variação de z por sessão como no base (`session_z_std` = 0,005, relativa). O
   0,7 mm entra só como robustez, com os modelos de 1,0 mm, sem retreinar.
2. Letras com o mesmo número de Fresnel do base.
3. Gravação com sobreamostragem (campo numa grade mais fina, integração no pixel de 1,67 µm) e teste de convergência
   2× contra 4×.
4. Critério da tese central (abaixo).
5. Primeiro só r1, com crops (`raw`), camada de propagação (`prop`) e reconstrução em z₀ (`rec_z0`). Checkpoint com
   o orientador antes das cinco repetições.
6. No paper, o conjunto base de hoje passa a ser "a geometria do CBMS 2024", e os conjuntos são apresentados pelo
   número de Fresnel.

### Conferência da conta do item 2

N_F = (lado/2)² / (λ z), com λ = 385 nm, pixel 1,67 µm, lado = maior lado da caixa da letra
(`annotations.csv` do base, todos os splits: p5 / p50 / p95 = 57 / 77 / 103 px; mínimo e máximo 46 e 140 px).

| | lado no base (19,25 mm) | N_F | lado a 1,0 mm com o mesmo N_F |
|---|---|---|---|
| p5 | 57 px = 95,2 µm | 0,306 | 12,99 px = 21,7 µm |
| p50 | 77 px = 128,6 µm | 0,558 | 17,55 px = 29,3 µm |
| p95 | 103 px = 172,0 µm | 0,998 | 23,48 px = 39,2 µm |
| mín. | 46 px = 76,8 µm | 0,199 | 10,48 px = 17,5 µm |
| máx. | 140 px = 233,8 µm | 1,844 | 31,91 px = 53,3 µm |

A conta do orientador fecha: N_F de 0,31 a 1,00 no base (p5–p95), letras de 21,7 a 39,2 µm a 1,0 mm. O fator é
√(1,0 / 19,25) = 0,22792 nos comprimentos. Em tamanho de fonte: 70–118 px no base → 15,95–26,89 px a 1,0 mm.

`small_near` (letras pequenas a 2 mm): lado p5 / p50 / p95 = 15 / 27,75 / 42 px, N_F = 0,20 / 0,70 / 1,60. A mediana
(0,70; o orientador escreveu ≈ 0,72) cai dentro da faixa do base; a faixa dele é mais larga que a do base.

### O texto do CBMS 2024 (conferido no PDF que o orientador mandou às 15:44)

`referencias/c/rockembach2024_full/rockembach2024_cbms.pdf`, p. 367, seção "A. Dataset of Synthetic Holograms":
"The diffraction parameters used were λ = 385nm, z = 50k, pixel size of 1.67μm, and an output image resolution with
the same resolution of its input (640x640 pixels). After processing, a total of 200 holograms were generated". O z vem
sem unidade; o código do gerador dá 50 000 λ = 19,25 mm (`CADERNO.md`, Z1 e Z9). Fecha a pendência do Z9.

### Critério pré-registrado da tese central (item 4, palavras do orientador)

"a tese central (o crop falha, a camada sobre o holograma inteiro recupera) se mantém se, em pelo menos 4 de 5
repetições, a prop ficar pelo menos 0,10 acima dos crops em F1 e pelo menos 0,30 acima em rejeição das não vistas,
como no base e no small_near. Se não, reporta como está: a tese muda e a gente reescreve."

Como leio, para não haver escolha depois:
- **Métricas:** as mesmas das tabelas do paper e de `setup_comparison.csv`: `novel_open_macro_f1` (F1) e
  `novel_unknown_rejection` (rejeição das não vistas), no split de teste, com o limiar escolhido na validação.
- **Fluxos:** `prop` contra `raw` (crops do holograma), na mesma repetição (pareado).
- **Regra:** uma repetição conta a favor só se cumprir as **duas** condições (F1(prop) − F1(raw) ≥ 0,10 **e**
  rejeição(prop) − rejeição(raw) ≥ 0,30). A tese se mantém com 4 ou 5 repetições a favor em r1–r5.
- **O piloto em r1 não decide o critério.** Ele mostra uma repetição; o critério só é aplicado depois das cinco, que
  dependem do checkpoint (item 5).
- Referência: no base as diferenças médias são +0,183 (F1) e +0,820 (rejeição), 5 de 5; no `small_near`, +0,179 e
  +0,810, 5 de 5 (`results_exp_resolucao/setup_comparison.csv`).
- `rec_z0` é reportado ao lado, sem critério: ele diz se a reconstrução com a distância conhecida continua empatada
  com a camada.

### Teste de convergência da sobreamostragem (item 3): definição e tolerância (minha escolha)

- **O que se compara:** a mesma cena física gravada com fator s e com fator 2s (s = 1 é o simulador de hoje; depois
  2, 4, 8…), sem ruído nem quantização (`full_well` = 0, `read_noise` = 0, `prnu` = 0, `bits` = 0), com tudo o mais do
  conjunto (fonte, feixe, poeira, pixel). A cena tem de ser a mesma para todo s: a letra é definida em unidades
  físicas (tamanho, rotação, posição com resolução abaixo do pixel) e amostrada em cada grade.
- **Medida:** em cada cena, rms(I_s − I_2s) na janela, dividido pelo rms do padrão de I_2s (I_2s menos a gravação da
  mesma sessão sem objetos). Oito cenas a 1,0 mm e oito a 0,7 mm (o teste de robustez usa o mesmo gravador).
- **Tolerância:** "o mesmo" = no máximo **1 %** em todas as cenas. Reporto também a diferença em níveis de cinza de
  8 bits e em relação ao ruído de uma gravação (para dizer se ela ficaria abaixo do ruído).
- **Regra:** grava-se com o menor s tal que (s, 2s) passa, a 1,0 mm e a 0,7 mm. Se (2, 4) não passar, testa-se
  (4, 8), e assim por diante.
- O teste é feito na imagem, antes de qualquer modelo. Não retreino modelos para comparar fatores.

### Robustez a 0,7 mm (item 1): como será avaliada

- Cenas do split de teste do conjunto de 1,0 mm gravadas de novo com z₀ = 0,7 mm (mesmas sementes), com o mesmo
  gravador sobreamostrado. Modelos de r1 treinados a 1,0 mm, sem retreinar.
- **(a) Como está (o que o orientador pediu):** os modelos e a distância nominal de 1,0 mm, sem mudar nada.
- **(b) Recalibrado sem rótulo (acréscimo meu, reportado à parte):** a distância usada por `rec_z0` e o α da camada
  reestimados pela calibração sem rótulo que o método já tem (`calibrate_alpha`, critério de Tamura, em 32 hologramas
  do split de **validação** gravado a 0,7 mm); os pesos não mudam. A faixa de busca de hoje começa em 0,944 mm e não
  contém 0,7 mm: para estes conjuntos o limite inferior é estendido, com o mesmo passo relativo, antes de rodar. O
  padrão do código não muda.

### O que fica igual ao base e o que muda no conjunto de 1,0 mm

- Igual: fonte (385 nm, 10 nm, pinhole de 100 µm a 15 cm), feixe, poeira (densidades, planos a +1,0 mm e −0,2 mm da
  amostra, janela do sensor a 0,5 mm dos pixels: os três continuam do lado certo com z₀ = 1,0 mm), sensor (PRNU, poço
  de 6000 e⁻, exposição, ruído de leitura, 8 bits), material das letras, rotações, fontes, 5000 imagens em 50 sessões
  de 100, splits por sessão, protocolo open-set e classes de cada repetição.
- Muda: z₀ (1,0 mm), tamanho das letras (fator 0,22792), gravação sobreamostrada, margem e alcance do campo simulado
  (o padrão se espalha menos em pixels; a margem é conferida por medida).
- **Em aberto, perguntado ao orientador antes de gravar:** quantas letras por janela e o espalhamento de profundidade
  por objeto (ver P1).

## 2026-11-14, 16:24 — S1: gravação sobreamostrada no simulador e cena em unidades físicas (execução)

Commit `c1092ff`. Arquivos: `holo_openset/sim/physics.py`, `sim/scene.py`, `sim/letters.py`, `sim/generate.py`,
`tests/test_oversample.py`, `tests/fixtures/` (referência do caminho nativo).

### Caminho sobreamostrado (`Physics.oversample`, padrão 1)

- `oversample = 1`: `sensor_intensity` não mudou (o código antigo roda inteiro; o novo só entra com s > 1).
- s > 1 (`fine_intensity`, depois média s × s em `sensor_intensity`): campo na grade de passo 1,67 µm / s com o
  tamanho do canvas × s; cada letra e cada poeira das faces do vidro amostrada nessa grade e pré-propagada pela sua
  profundidade (em retalho com folga do alcance da franja mais fina dessa grade, como o nativo faz com o pixel; um
  grupo de poeiras de uma mesma profundidade cujo retalho passaria de meia tela é propagado na tela inteira, uma FFT
  por plano: é o caso da poeira a +1,0 mm na grade 4×, folga de 1105 células finas); os 7 comprimentos de onda da
  fonte propagados até o sensor (a FFT do campo espalhado é feita uma vez); a poeira da janela do sensor multiplica o
  campo no plano dela (0,5 mm antes dos pixels); a imagem do pinhole borra a intensidade na grade fina; o pixel é a
  média dos s × s (substitui o filtro de caixa `pixel_mtf` do nativo e serrilha o que passa de Nyquist, como um
  sensor). Feixe, PRNU, ruído de disparo, de leitura e quantização no pixel nativo, sem mudança (`record`).
- Convenção de coordenadas (a que faz o caminho fino coincidir com o nativo): o pixel j cobre [j, j+1) na tela, a
  célula fina K cobre [K/s, (K+1)/s) e vale o campo no seu centro; com s = 1 é a grade do nativo (amostra no centro
  do pixel, caixa centrada nele). Conferido: um objeto suave (gaussiana de σ = 4 px) gravado pelo nativo e com s = 4
  difere em 0,40 % (rms da diferença / rms do padrão); com 1 px de deslocamento seria 17,7 %.
- `pixel_mtf = False` com s > 1 levanta erro (não há pixel pontual definido numa grade fina).

### Cena independente da grade (`FresnelLayout`, `physical_scene`)

- Desenho escolhido: **raster mestre numa grade 16× mais fina que o pixel (0,10 µm), média por área em cada grade de
  simulação.** Cada letra é definida por classe, fonte, tamanho de fonte contínuo (uniforme em 15,95–26,89 px; o Pillow
  11 aceita tamanho fracionário), rotação, posição contínua (uniforme; guardada como a célula mestra do canto, isto é,
  com resolução de 1/16 px, nunca presa ao pixel), material e profundidade; o glifo é desenhado uma vez a 16 × o
  tamanho (até 430 px) e girado ali. Em cada grade s (divisor de 16) a máscara é a média do raster mestre em blocos de
  16/s, com o deslocamento do canto. Por quê: as amostragens ficam aninhadas exatamente (a máscara de s é a média 2 × 2
  da de 2s, verificado no teste), então a diferença entre s e 2s vem só da física amostrada, nunca de um objeto
  desenhado de outro jeito. Desenhar o glifo a fonte × s em cada s mudaria o hinting, o antialias e o recorte da tinta
  a cada s; e a posição pesa: no teste de semelhança, 1/32 px de erro de posição sozinho dá 3,6 %, mais que a
  tolerância. A máscara em pixels nativos (`mask`, `x`, `y`) é a mesma média com s = 1 e é o que o caminho nativo, a
  inclinação, os mapas de verdade e a tabela de poeira leem.
- Poeira: o mesmo princípio. As partículas das duas faces do vidro e as da janela do sensor (a câmera, `camera(...,
  lay)`) têm o polígono desenhado na grade mestra e posição contínua. Mesmas leis de tamanho e de material do base.
- Layout: `FresnelLayout(scale = √(1,0/19,25) = 0,2279212)`: fonte 15,954–26,895 px, borda 2,735 px, espaçamento
  1,368 px; `letters_mean/std/min/max` como parâmetros, padrão do base (8 ± 3, 3–18 por janela 640 × 640). O
  espaçamento é imposto numa grade de ocupação em pixels: caixa inteira que contém a tinta + max(1, round(1,368)) =
  1 px; a distância entre tintas fica ≥ 1 px, tipicamente 1–3 px (desvio: o 1,37 px exato não cabe numa grade de
  pixels; não muda a física). A ordem dos sorteios é a do `make_scene` do base, com contínuos no lugar dos inteiros (é
  um layout novo: nenhum conjunto existente depende dela). A cena depende de janela, margem, alcance, material e
  poeira, nunca de z₀ nem de s (teste).
- Tamanhos conferidos numa gravação de teste de 800 imagens (apagada depois, ver S3): lado da tinta p5 / p50 / p95 =
  12,8 / 17,4 / 23,2 px, N_F = 0,30 / 0,55 / 0,97; P0 previa 12,99 / 17,55 / 23,48 px (0,306 / 0,558 / 0,998).
- Anotações: `x0, y0, x1, y1` continuam inteiros (a caixa dos pixels que a letra toca, que contém a tinta; é o que
  `data.py`, `square_boxes`, `roi_align`, `reconstruct.int_boxes`, os rótulos YOLO e o teste de mesmas cenas de
  `robustness.py` leem); acrescentei `bx0, by0, bx1, by1` (caixa da tinta em px, float) e `font_size` passou a float.
  Nenhum conjunto existente muda.
- `physics.json`: `oversample` e `layout_params` só são escritos quando não são o padrão, para que um conjunto do
  paper regravado continue com o `physics.json` byte a byte igual (ele entra nos checksums dos dados).

### O que verifiquei sobre `oversample = 1`

Antes de mudar o código (commit `bed038c`), gravei `tests/fixtures/native_reference.npz` com o simulador nativo numa
cena pequena com todos os efeitos (janela 192 × 192, margem 128, alcance 96, poeira 40/mm² nas faces e 60/mm² na
janela): `sensor_intensity` (float64), `record` (uint8 com gerador semeado), quadro em branco e um conjunto de 4
imagens feito por `generate()` (hologramas e sha256 do `annotations.csv`). Depois da mudança, todos idênticos bit a bit
(`test_oversample_1_is_exactly_the_simulator_of_the_paper`), e o `physics.json` desse conjunto não ganhou chaves.

### Testes (`tests/test_oversample.py`, CPU, 5 s)

1. `oversample = 1` idêntico à referência (acima).
2. Convergência numa cena minúscula (janela 96, z₀ = 1,0 mm, todos os efeitos): (4, 8) = 0,18 %, (2, 4) = 0,90 %.
   **Desvio:** o brief pedia "s = 2 e s = 4 concordam dentro da tolerância"; nas cenas do conjunto (S2) o par (2, 4)
   NÃO passa, então o teste exige (4, 8) ≤ 1 % e (2, 4) pior que (4, 8), e não exige (2, 4) ≤ 1 %.
3. Semelhança de Fresnel (fonte pontual monocromática, sem pixel, intensidade na grade fina antes do pixel): a letra
   de lado L a 1 mm e a mesma letra de lado 2L (o raster mestre com cada célula em 2 × 2, canto a 2 × a distância)
   a 4 mm, comparadas com a grande em média 2 × 2: 0,89 % (limite 3 %); controle negativo com 2 mm: 128 % (> 30 %).
4. Alinhamento nativo × fino (0,40 %, acima). 5. Cena igual para todo s e z₀, amostragens aninhadas, caixa float
   dentro da inteira. 6. `generate()` com o layout novo e sobreamostrado, e o mesmo conjunto regravado a 0,7 mm por
   `like=`: mesmas anotações, `physics.json` com fator e layout. 7. s > 1 sem abertura de pixel dá erro. 8. (S3) a
   grade estendida de `calibrate_alpha` mantém os pontos.

`pytest`: 54 passam (46 de antes + 8). `reproduce check`: 13/13.

## 2026-11-14, 16:24 — S2: teste de convergência da sobreamostragem, margem e alcance (execução)

Commits `629424d` (script) e `77b29f7` (tabelas). Script `scripts/exp_resolucao/oversampling_convergence.py`, GPU 5
(H100, compartilhada), 4 threads. Logs em `logs/exp_resolucao/oversampling_*.log`.

Cenas: 8 cenas semeadas do layout do piloto (sementes e sessões das imagens 0, 625, …, 4375 de um conjunto de
`generate`, semente 17; sessões 0, 6, 12, 18, 25, 31, 37, 43; câmera semente 7), 3–13 letras na janela (mediana 9).
Física do conjunto sem ruído nem quantização (`full_well = read_noise = prnu = 0`, `bits = 0`), valores da câmera em
níveis de cinza de 8 bits. Medidas como no P0: rms(I_s − I_2s) na janela / rms(I_2s − B_2s), com B o quadro sem
objetos da mesma sessão (poeira da janela do sensor presente) na mesma grade; diferença máxima em níveis de cinza;
rms da diferença / rms do ruído de uma gravação real (disparo com poço de 6000 e⁻ e 3 e⁻ de leitura, sobre I_2s:
2,11 níveis); padrão rms ≈ 4,6 níveis.

### Margem e alcance (medidos antes, com s = 4, a 1,0 e 0,7 mm, com as duas profundidades)

```
python scripts/exp_resolucao/oversampling_convergence.py reach  --device cuda:5 --s 4 --reach 117 233 350
python scripts/exp_resolucao/oversampling_convergence.py margin --device cuda:5 --s 4 --reach 233 --margin-list 256 394
```

- Alcance R: cena sorteada com alcance 2R (margem 2R + 256), gravada com todos os objetos e sem os que não estão
  inteiros a até R da janela (letras e poeira das faces). Mudança máxima nas 8 cenas: R = 117 → 0,47 % (1,0 mm) /
  0,37 % (0,7 mm); R = 233 → 0,13 % / 0,12 %; R = 350 → 0,066 % / 0,036 %. Diferença máxima 0,10–0,13 níveis em R = 233.
- Margem m: a mesma cena com m e 2m (conferido: mesmas linhas e mesmos objetos). m = 256 → 0,106 % (1,0 mm) / 0,068 %
  (0,7 mm); m = 394 → 0,0011 % / 0,0011 % (diferença máxima 0,0003 níveis).
- **Escolha: margem 394 px, alcance 233 px** (os valores do base escalados por 0,22792). Os dois passam com folga de
  > 7× a tolerância. **Desvio a registrar:** valores menores também passam (margem 256, alcance 117); não desci até eles
  porque o ganho de tempo é pequeno (a gravação já custa 0,11 s por imagem) e os valores escalados mantêm o campo em
  volta da janela semelhante ao do base. Se preferir o menor que passa, é trocar `margin=256 reach=117` em
  `pilot_1mm.sh` (as cenas mudam).

### Convergência

```
python scripts/exp_resolucao/oversampling_convergence.py converge --device cuda:5 --margin 394 --reach 233 --s 1 2 4 8
```

rel_rms por cena (mín / mediana / máx das 8), diferença máxima em níveis de cinza e máx. da razão com o ruído:

| z₀ | profundidade | par | rel_rms mín / med / máx | dif. máx. (níveis) | / ruído (máx) | passa |
|---|---|---|---|---|---|---|
| 1,0 mm | 50 µm | (1, 2) | 7,09 / 8,49 / 9,21 % | 8,21 | 0,251 | não |
| 1,0 mm | 50 µm | (2, 4) | 1,04 / 1,16 / 1,40 % | 1,09 | 0,035 | não |
| 1,0 mm | 50 µm | (4, 8) | 0,23 / 0,25 / 0,32 % | 0,31 | 0,0088 | sim |
| 1,0 mm | 2,6 µm | (1, 2) | 7,08 / 8,45 / 9,29 % | 7,63 | 0,250 | não |
| 1,0 mm | 2,6 µm | (2, 4) | 1,04 / 1,16 / 1,40 % | 1,02 | 0,035 | não |
| 1,0 mm | 2,6 µm | (4, 8) | 0,23 / 0,25 / 0,32 % | 0,31 | 0,0088 | sim |
| 0,7 mm | 50 µm | (1, 2) | 8,80 / 10,87 / 11,37 % | 9,91 | 0,308 | não |
| 0,7 mm | 50 µm | (2, 4) | 1,40 / 1,55 / 1,78 % | 1,70 | 0,049 | não |
| 0,7 mm | 50 µm | (4, 8) | 0,34 / 0,35 / 0,46 % | 0,35 | 0,0121 | sim |
| 0,7 mm | 2,6 µm | (1, 2) | 8,83 / 10,91 / 11,38 % | 10,74 | 0,309 | não |
| 0,7 mm | 2,6 µm | (2, 4) | 1,39 / 1,54 / 1,78 % | 1,62 | 0,049 | não |
| 0,7 mm | 2,6 µm | (4, 8) | 0,34 / 0,35 / 0,46 % | 0,36 | 0,0122 | sim |

- **Pela regra do P0, grava-se com s = 4**: (2, 4) falha em todas as 32 combinações de cena, distância e profundidade
  (mínimo 1,04 %); (4, 8) passa em todas (máximo 0,46 %). A profundidade não muda a resposta (diferenças na 4ª casa).
- O simulador de hoje (s = 1) erra 7–11 % contra s = 2 nestas cenas (P0 citava 2–4 % para uma letra isolada sem
  poeira, `sim_sampling.csv`); a sequência 8,5 → 1,16 → 0,25 % (medianas, 1,0 mm) cai ~4–7× por duplicação.
- Onde está a diferença de (4, 8): 68–71 % da energia acima de metade do Nyquist do sensor; dentro das caixas das
  letras (+25 %) até 0,54–0,67 % e fora delas até 0,32–0,47 % (normalizados pelo rms do padrão da janela inteira).
- Densidade de letras: rodei também o outro candidato do P1 (número por janela escalado por 1/0,22792²: 154 ± 57,75,
  58–346; mediana 172 letras), só 50 µm, s = 2, 4, 8 (`--layout letters_mean=154 letters_std=57.75 letters_min=58
  letters_max=346 --tag _density_scaled`): (2, 4) 1,16–1,30 % (1,0 mm) e 1,56–1,76 % (0,7 mm), falha; (4, 8)
  0,25–0,30 % e 0,35–0,42 %, passa; diferença máxima 0,54 / 0,65 níveis, 4,7 / 5,8 % do ruído. Mesma resposta: s = 4.
- Tempo e memória por imagem (intensidade + câmera, mediana de 64 gravações, H100 compartilhada): s = 1: 0,010 s,
  0,17 GiB; s = 2: 0,030 s, 0,68 GiB; s = 4: 0,107 s, 3,0 GiB; s = 8: 0,420 s, 10,8 GiB (com 172 letras, s = 4:
  0,30 s).

Saídas: `results_exp_resolucao/oversampling_convergence.csv` (uma linha por distância, profundidade, cena e par),
`oversampling_timing.csv`, `oversampling_margin.csv`, `oversampling_reach.csv`, e os dois `*_density_scaled.csv`.

## 2026-11-14, 16:24 — S3: o piloto e a robustez a 0,7 mm preparados, não rodados (execução)

Commit `28539f7`. Nada do piloto foi gravado, treinado nem avaliado. `scripts/exp_resolucao/pilot_1mm.sh <GPU> <passo>`,
um passo por vez: `record`, `reconstruct`, `train`, `evaluate`, `record_07`, `robust_a`, `robust_b` (log em
`logs/exp_resolucao/pilot_<passo>.log` com início, fim e segundos). **As duas escolhas em aberto do orientador são
obrigatórias e não têm padrão:** `DEPTH=50|2.6` e `DENSITY=base|scaled` (ex.: `DEPTH=50 DENSITY=base bash
scripts/exp_resolucao/pilot_1mm.sh 5 record`).

- `record`: `simulate fresnel --name bench_1mm --n-images 5000 --set-physics z0=1.0e-3 oversample=4 margin=394
  reach=233 <profundidade> --layout <densidade> --workers 3` → `data/bench_1mm` (50 sessões de 100, 35/7/8 por sessão,
  como `simulate small`).
- `reconstruct`: `reconstruct --set bench_1mm --methods z0` (distância = z₀ do `physics.json` do conjunto, 1,0 mm).
- `train`: `train --set bench_1mm --flow {raw,prop,rec_z0} --rep 1 --no-aux`; o `prop` com `--alpha-extend 12`.
- `evaluate`: os três fluxos, r1 → `results_exp_resolucao/eval/bench_1mm/<fluxo>_r1.json`.
- `record_07`: `simulate like --like bench_1mm --name bench_1mm_robust/z07 --split test --set-physics z0=0.7e-3` e o
  mesmo com `--split val` → `bench_1mm_robust/z07_val` (mesmas cenas, sementes, sessões, câmera e gravador; só z₀ muda).
  Nomes fora de `data/variants*`.
- `robust_a` (a, como está): `reconstruct --set bench_1mm_robust/z07 --methods z0 --z0 <z₀ de bench_1mm>` e
  `experiment robustness --set bench_1mm --variants-root bench_1mm_robust --variants base z07 --flows raw prop rec_z0
  --rep 1 --out robustness_bench_1mm`.
- `robust_b` (b, recalibrado sem rótulo): `recalibrate_distance.py` roda `calibrate_alpha` (grade estendida) em 32
  hologramas do split de validação a 0,7 mm (ids sorteados com semente 0; nenhum rótulo lido) → α e z = α (640 ×
  1,67 µm)² / (π λ) em `results_exp_resolucao/recal_bench_1mm_z07.json` (com o mesmo cálculo nos mesmos ids a 1,0 mm,
  só para registro); `reconstruct ... --z0 <z> --tag _recal`; `experiment robustness ... --variants z07 --flows prop
  rec_z0 --alpha-json <json> --rec-tag _recal` → linhas `prop+recal` e `rec_z0+recal` no mesmo csv. Galeria (validação
  de 1,0 mm, embutida como o modelo foi treinado), pesos e limiar não mudam; só o α da camada (prop) e a distância da
  reconstrução (rec_z0) dos padrões de teste a 0,7 mm.

### Onde o código supunha 19,25 mm ou a grade do pixel, e o que fiz

1. Distância de `rec_z0`: `reconstruct.Holograms.z0` e `data.Dataset.z0` já vêm do `physics.json` do conjunto: 1,0 mm
   em `bench_1mm`, sem mudança. **Armadilha:** nas regravações a 0,7 mm o `physics.json` diz 0,7 mm, e reconstruir
   com o padrão usaria a distância verdadeira (um oráculo) na avaliação (a). Acrescentei `reconstruct --z0` (e
   `--tag`), e o passo `robust_a` passa o z₀ de `bench_1mm`.
2. `reconstruct.backprop`/`kernel`: unidades físicas (λ, pixel, z dado); certo a 1 mm. Nada a mudar.
3. `train.calibrate_alpha`: grade geométrica de α em [0,001; 0,08] = [0,944; 75,5] mm; 1,0 mm cai no 2º ponto
   (0,998 mm) e 0,7 mm fica fora. Acrescentei `extend` (e `train --alpha-extend`): N passos a mais abaixo, mesmo passo
   relativo (5,70 %), mantendo os 80 pontos (teste); 12 passos → 0,485 mm. Usado só no `prop` do piloto e na
   recalibração; padrão 0, inalterado.
4. Log do treino ("the bench would be …") usava o α de 19,25 mm; agora usa o z₀ do conjunto (só a mensagem).
5. `model.physics_weights` (fluxos `wiener`/`fresnel`, fora do piloto): já recebe o z₀ do conjunto. `reconstruct.COARSE`
   e `Focus` (autofoco, fora do piloto): relativos a z₀. Sem mudança.
6. Recortes: `square_boxes` (1,25 × a caixa) e `roi_align` a 64 × 64 recortam 16–29 px e ampliam 2,2–4×: é a
   consequência do pixel que o piloto quer medir; sem mudança.
7. `experiments/robustness.py`: rotulava qualquer variante fora da bateria do paper como "base"; agora usa o nome dela.
8. `camera`: faixa de poeira da janela = janela ± min(64, margem); com margem 394, ± 64 px como no base.

### Testes de caminho (sem o piloto)

Para conferir o caminho de ponta a ponta, gravei um conjunto de teste de 800 imagens com a física do piloto (50 µm,
8 letras) em `$TMPDIR` (scratchpad, fora de `data/`), suas regravações a 0,7 mm (teste e validação, 100 + 100),
`reconstruct --z0 1.0e-3`, a recalibração e `reconstruct --tag _recal`, e rodei `experiment robustness` (a) e (b) com
pesos **aleatórios não treinados** (só para exercitar o código; os números não significam nada e não foram guardados).
Tudo apagado depois. A recalibração deu z = 0,676 mm para a sessão de validação a 0,7001 mm (−3,4 %) e 0,980 mm para a
mesma sessão a 1,0001 mm (−2,0 %): o critério de Tamura sobre o holograma cru fica 2–3 % abaixo da distância nessa
sessão (uma sessão, 32 imagens; é o método como está, não corrigi).

### Estimativas medidas

- Gravação de `bench_1mm`: 800 imagens em 238 s (0,30 s por imagem de parede, 3 construtores de cena, GPU 5
  compartilhada; a parte da GPU é 0,11 s, o resto é cena, PNG e mapas) → 5000 ≈ 25 min. Disco: hologramas 2,05 GB,
  PNG ≈ 1,0 GB, fundos 82 MB, rótulos e objetos ≈ 6 MB → ≈ 3,2 GB; com `rec_z0.npy` (6,14 GB) ≈ 9,3 GB.
- `reconstruct --methods z0`: 800 em 12 s → 5000 ≈ 75 s.
- `record_07`: 100 imagens em 27 s (teste) e 15 s (validação), com a partida → 800 + 700 ≈ 6 min; disco ≈ 0,33 + 0,29
  GB de hologramas, 2 × 82 MB de fundos, 2 × 0,98 GB de caches (`rec_z0`, `rec_z0_recal`) ≈ 2,8 GB.
- Treinos (3000 passos, sem auxiliares): 56 s no `rec_afc` do estudo de distância
  (`logs/exp_distancia/own_train_rec_afc.log`), 1,3 min por modelo no resumo do paper (`results/run_summary.json`) →
  os três ≈ 3–5 min. Avaliação: 5 repetições em 26 s (`logs/integracao/eval_rec_afc.log`) → < 1 min os três.
  Robustez (a) e (b): ≈ 1–2 min cada. Total ≈ 40–45 min de GPU, ≈ 12 GB de disco.

### Pontos em aberto para o responsável

1. As duas perguntas do P1 (letras por janela, espalhamento de profundidade): o script exige as duas. Nenhuma muda o
   fator de sobreamostragem.
2. Margem e alcance: escolhi os valores escalados (394 / 233), não os menores que passam (256 / 117).
3. `lr_alpha = 1e-5` é absoluto: a 1,0 mm o α físico é 0,00106 (no base 0,0204), então um passo do Adam é ~1 % de α
   aqui contra ~0,05 % no base. Não mudei (é a receita do paper), mas o α depois do treino (que o log imprime) deve ser
   olhado.
4. Recalibração (b): substituí o α treinado pelo α calibrado a 0,7 mm (leitura literal do P0). A alternativa,
   escalar o α treinado pela razão α_cal(0,7) / α_cal(1,0), preservaria o que o treino moveu; o json guarda os dois
   α calibrados para isso. A galeria fica a de 1,0 mm.
5. Geometria a 0,7 mm: a poeira do topo da lamínula (−0,2 mm da amostra) fica a 0,5 mm do sensor, no mesmo plano da
   poeira da janela (0,5 mm), ± 3,5 µm com a variação de z por sessão: a lamínula estaria encostada na janela. A
   simulação aceita (camadas somadas em primeira ordem), mas fisicamente é o limite; a 1,0 mm há 0,3 mm de folga.
6. `font_size` agora é float nas anotações do conjunto novo (scripts que façam `int(...)` dele continuam funcionando).

## 2026-11-14, 16:32 — P1: respostas do orientador, revisão do gravador e o que fica fixado antes de gravar (responsável)

Escrito depois do S1–S3 (código e teste de convergência) e antes de gravar o conjunto, de treinar e de avaliar.

### Respostas do orientador às duas perguntas (≈ 16:25, pelo diálogo de perguntas)

1. **Letras por janela: 8 por janela de 640 × 640**, como no base e no `small_near` (`DENSITY=base`).
2. **Espalhamento de profundidade por objeto: 2,6 µm rms (máximo 7,8 µm)**, isto é, os 50 / 150 µm do base escalados
   com z (`DEPTH=2.6`); **os 50 µm entram como robustez**, com os mesmos modelos, sem retreinar.

### Revisão do S1–S3 (li o diff de `sim/physics.py` e o script do piloto; rodei os testes)

- `pytest`: 54 passam; `reproduce check`: 13/13. O caminho de s = 1 não mudou (o `sensor_intensity` só desvia quando
  `oversample > 1`).
- Fator de sobreamostragem: **s = 4**, pela regra do P0 ((2, 4) falha em todas as cenas, 1,04–1,78 %; (4, 8) passa em
  todas, ≤ 0,46 %). Margem 394 px e alcance 233 px (os do base escalados): aceito.
- **Um ponto que mando corrigir antes de gravar.** No caminho fino, como no nativo, os objetos fora do plano da
  amostra são pré-propagados pela sua profundidade só no comprimento de onda central, e depois as sete componentes da
  banda propagam z. A 19,25 mm a profundidade da poeira (+1,0 mm e −0,2 mm) é 5 % e 1 % de z e o erro é desprezível; a
  1,0 mm a poeira da face de trás da lâmina está a 2,0 mm do sensor e receberia a perda de coerência temporal de
  1,0 mm (ficaria mais nítida do que deve). Correção, só no caminho fino: cada plano de poeira é propagado por
  z + profundidade em cada comprimento de onda (soma no domínio de Fourier, sem transformadas a mais). As letras
  (2,6 µm, ou 50 µm no teste de robustez) continuam pré-propagadas no comprimento de onda central (erro de fase na
  borda da banda, na frequência de Nyquist: ≈ 0,02 rad a 7,8 µm e ≈ 0,4 rad a 150 µm, contra ≈ 2,8 rad do termo de z).
  O borrão da imagem do pinhole continua calculado para a distância da amostra em todos os planos (aproximação
  declarada: ele é o termo menor a estas distâncias). Depois da correção, o par (4, 8) é conferido de novo.
- Conferência cruzada pedida: o gravador novo contra a implementação independente de uma letra isolada
  (`scripts/exp_resolucao/sim_sampling.py::fine_recording`), que já tinha sido validada.

### Decisões sobre as dúvidas que o executor levantou (minhas; o orientador pode reverter)

- **Receita de treino igual à do paper**, incluindo `lr_alpha = 1e-5` (absoluto). Um passo absoluto em α dá a mesma
  variação de fase do núcleo em qualquer distância, então não há motivo físico para reescalar. Reporta-se o α
  calibrado e o α depois do treino, em mm.
- **Robustez a 0,7 mm, leitura (b):** a principal é a literal do P0 (o α calibrado a 0,7 mm substitui o treinado; a
  distância de `rec_z0` é a calibrada). Reporto ao lado, declarada agora, a variante por razão (α treinado ×
  α_cal(0,7) / α_cal(1,0), e z = 1,0 mm × a mesma razão), que cancela o viés da calibração.
- **Robustez à profundidade (pedido do orientador):** as cenas do split de teste gravadas de novo com 50 / 150 µm,
  z₀ = 1,0 mm, mesmas sementes (`bench_1mm_robust/depth50`); avaliação "como está", com os modelos de r1, a galeria
  e o limiar do conjunto principal; `rec_z0` na distância nominal.
- **Geometria a 0,7 mm:** a poeira do topo da lamínula (−0,2 mm da amostra) cai no mesmo plano da poeira da janela do
  sensor (0,5 mm). Fica como está e vai declarado no checkpoint: com os vidros do simulador, 0,7 mm é o limite em que
  a lamínula encosta na janela.

### O que será rodado (nesta ordem) e o que será reportado

1. Correção do plano de poeira, teste, par (4, 8) de novo, conferência cruzada.
2. `record` (`DEPTH=2.6 DENSITY=base`), `reconstruct`, `train` (r1: `raw`, `prop`, `rec_z0`, `--no-aux`), `evaluate`.
3. `record_07`, `robust_a`, `robust_b` (com a variante por razão), e a robustez de profundidade (`depth50`).
4. Vazamento do padrão para fora do crop nos tamanhos do conjunto novo e a tabela dos conjuntos pelo número de
   Fresnel.

O teste é lido uma vez, com o limiar da validação. Reporta-se o que sair. O critério do item 4 não é aplicado a r1
sozinho; as cinco repetições dependem do checkpoint com o orientador.


## 2026-11-14, 16:44 — R1–R3: plano de poeira em cada comprimento de onda, conferência cruzada, robustez de profundidade (execução)

Commits `2eb3fec` (código e testes), `9e010ae` (tabelas), `74a5224` (script do piloto). Logs:
`logs/exp_resolucao/r1_dustfix.log`.

### R1. Correção pedida no P1 (só no caminho fino)

- `fine_scattered_field(..., dust_planes)`: a poeira (`kind == 'dust'`, as faces do vidro a +1,0 mm e −0,2 mm) não é
  mais pré-propagada; o campo de cada profundidade fica numa tela à parte. Em `fine_intensity`, a FFT de cada plano é
  feita uma vez e, dentro do laço dos comprimentos de onda, entra no espectro com H(λ, zz + profundidade) (zz = z, ou
  z − 0,5 mm com a poeira da janela): nenhuma transformada a mais. As letras continuam pré-propagadas pela sua
  profundidade no λ central; o borrão do pinhole continua calculado para a distância da amostra (aproximação
  declarada). Caminho nativo intocado (o teste da referência de s = 1 continua bit a bit).
- Teste novo: sem pinhole, com a banda inteira e a poeira da janela, uma partícula a +1,0 mm gravada a z = 1,0 mm é
  igual à mesma partícula a profundidade 0 gravada a 2,0 mm: diferença máxima 0,0 (as mesmas contas); pelo caminho das
  letras (pré-propagação no λ central) a diferença seria 5,1 % do padrão (o teste exige > 2 %).
- O quanto as gravações mudaram (8 cenas, s = 4, 2,6 µm, sem ruído; o gravador antes da correção rodado de um
  `git worktree` em `2c9e3d4`, modos `dump`/`compare` do script; `results_exp_resolucao/oversampling_dustfix_change.csv`):
  rms(depois − antes) / rms do padrão = 1,06 / 2,66 / 4,89 % (mín / mediana / máx) a 1,0 mm e 1,07 / 2,79 / 5,49 % a
  0,7 mm; diferença máxima 2,17 e 2,53 níveis de cinza; quadros em branco idênticos (não têm poeira de vidro).
- Testes de convergência, margem e alcance rodados de novo com o gravador corrigido (os csv foram substituídos):
  (4, 8) com 2,6 µm: 0,23 / 0,25 / 0,32 % a 1,0 mm e 0,34 / 0,36 / 0,46 % a 0,7 mm → **passa, s = 4 mantido**;
  (2, 4): 1,09 / 1,19 / 1,43 % e 1,42 / 1,55 / 1,79 %, falha; (1, 2): 7,3–9,4 % e 8,8–11,5 %. Com 50 µm e com a
  densidade escalada, a mesma resposta ((4, 8) ≤ 0,46 % e ≤ 0,42 %). Margem 394: 0,0011 %; alcance 233: 0,14 %
  (1,0 mm) e 0,11 % (0,7 mm); alcance 117 subiu para 0,73 % (ainda passaria).

### R2. Conferência cruzada com a implementação independente

`python scripts/exp_resolucao/crosscheck_recorder.py --device cuda:5`: uma letra F absorvente (a = 0,6, sem fase), do
tamanho mediano do layout (fonte 21,42 px), desenhada na grade mestra e levada à grade 4× (máscara 63 × 37 células),
no centro de uma janela 640 com margem 256, sem poeira, sem feixe, sem ruído, a 1,0 mm, banda do LED e pinhole do
conjunto: o gravador (`sensor_intensity`, s = 4) contra `sim_sampling.py::fine_recording` (s = 4) com a MESMA máscara
fina: rms da diferença / rms do padrão = **7,2 × 10⁻¹⁵** (diferença máxima 4,4 × 10⁻¹⁶;
`results_exp_resolucao/crosscheck_recorder.json`). As duas fazem as mesmas contas (o disco do pinhole por J1 do torch
num, do scipy no outro), então a concordância é de arredondamento: o que ela confirma é a posição, as unidades, a
média no pixel e o recorte da janela.

### R3. Robustez de profundidade e variante por razão (preparados)

- `pilot_1mm.sh record_depth50`: `simulate like --like bench_1mm --name bench_1mm_robust/depth50 --split test
  --set-physics depth_std=50e-6 depth_max=150e-6`; `robust_depth50`: `reconstruct --z0 <1,0 mm>` e `experiment
  robustness --variants depth50 --flows raw prop rec_z0` (como está).
- Mesmas cenas a menos das profundidades: verificado em duas cenas (sementes das imagens 0 e 625) por teste
  (`test_the_depth_spread_moves_only_the_depths`): mesmos rasters, cantos, absorção, fase, tipo, mesma poeira, mesmas
  linhas de anotação a menos de `depth`, e as profundidades proporcionais (2,6/50) — é um único sorteio gaussiano por
  objeto, recortado em 3σ nos dois casos. Também vou conferir as anotações do conjunto gravado.
- `robust_b` ganhou a variante por razão: α treinado × α_cal(0,7)/α_cal(1,0) (`--alpha-mode ratio`) e `rec_z0` em
  1,0 mm × a mesma razão (`z_ratio` do json, cache `rec_z0_recal_ratio.npy`), linhas `prop+recal_ratio` e
  `rec_z0+recal_ratio`.

## 2026-11-14, 17:19 — R4: o piloto em r1 rodado (gravação, treino, avaliação, robustez) (execução)

GPU 5 (H100, compartilhada), um processo por vez, 4 threads, sessões tmux `res_pilot_*`, logs
`logs/exp_resolucao/pilot_<passo>.log` (início, fim, segundos). Escolhas do P1: `DEPTH=2.6 DENSITY=base`.

| passo | comando | parede |
|---|---|---|
| record | `DEPTH=2.6 DENSITY=base bash scripts/exp_resolucao/pilot_1mm.sh 5 record` | 1029 s |
| sanidade | `python scripts/exp_resolucao/bench_sanity.py --set bench_1mm --ref realistic --device cuda:5` | — |
| reconstruct | `pilot_1mm.sh 5 reconstruct` | 65 s |
| train | `pilot_1mm.sh 5 train` (raw 81 s, prop 92 s, rec_z0 101 s) | 274 s |
| validação | `python scripts/exp_resolucao/val_openset.py --set bench_1mm --flows raw prop rec_z0 --rep 1 --device cuda:5` | — |
| evaluate | `pilot_1mm.sh 5 evaluate` | 34 s |
| record_07 | `pilot_1mm.sh 5 record_07` | 207 s |
| robust_a / robust_b | `pilot_1mm.sh 5 robust_a`, `... robust_b` | 37 s / 89 s |
| depth50 | `pilot_1mm.sh 5 record_depth50`, `... robust_depth50` | 110 s / 48 s |

Disco: `data/bench_1mm` 8,7 GB (hologramas 2,0 GB, PNG 1,0 GB, `rec_z0.npy` 6,1 GB), `bench_1mm_robust/z07` 3,1 GB,
`z07_val` 0,28 GB, `depth50` 1,3 GB, modelos 134 MB.

**Erro meu no script, corrigido antes de gravar qualquer coisa do passo:** `record_07` montava o nome da saída com
`$([ $SP = val ] && echo _val)`, que falha sob `set -e` para o split de teste; a primeira chamada saiu logo depois do
cabeçalho, sem gravar nada (commit `e3c6db5`). Nenhum outro passo foi repetido.

### O conjunto (`results_exp_resolucao/bench_1mm_sanity.json`, só o split de treino lido)

- 5000 imagens, 3500 / 700 / 800 (treino / validação / teste, por sessão), 40 309 letras, 8,06 por imagem (3–18):
  as mesmas contagens do base (mesmas sementes; o sorteio do número e das classes vem antes de qualquer tamanho).
- Lado da caixa inteira p5 / p50 / p95 = 14 / 18 / 24 px (N_F 0,355 / 0,587 / 1,043); lado da tinta 12,81 / 17,38 /
  23,29 px (N_F 0,297 / 0,547 / 0,982). Base: 57 / 77 / 103 px (N_F 0,306 / 0,558 / 0,998).
- Exposição: nível médio de 100 hologramas de treino 101,49 (base 99,49; as letras pequenas cobrem menos área); quadros
  em branco 101,51 (base 101,50).
- Ruído: 4 hologramas de treino reconstruídos das sementes e gravados de novo sem ruído (mesma cena, sessão, câmera,
  PRNU): armazenado − sem ruído tem média 0,001–0,006 níveis (o conjunto se refaz exatamente das sementes) e rms
  2,091–2,102 níveis (base 2,069–2,096).
- Folha de contato `docs/exp_resolucao/img/bench_1mm_examples.png` (4 imagens de treino e 4 recortes de 192 px, caixas
  em metade): letras como padrões em anéis, caixas no centro dos padrões, poeira da janela como anéis concêntricos,
  feixe e ruído como no base. Nada me pareceu fora do lugar.

### α da camada de propagação (r1)

- Calibrado em 32 hologramas de treino (grade estendida 12 passos): α = 0,0010587 → **0,99986 mm** (as 32 imagens têm z
  médio verdadeiro 1,00081 mm). Depois do treino (`lr_alpha = 1e-5`): α = 0,0010332 → **0,97582 mm** (−2,4 %).

### Resultados de r1 (`results_exp_resolucao/eval/bench_1mm/<fluxo>_r1.json`; teste lido uma vez)

| fluxo | F1 teste | rejeição teste | acurácia fechada teste | acurácia conhecidas | AUROC | limiar |
|---|---|---|---|---|---|---|
| raw | 0,9283 | 0,6224 | 0,9780 | 0,9540 | 0,9447 | 0,8732 |
| prop | 0,9770 | 0,9952 | 0,9975 | 0,9612 | 0,9940 | 0,9931 |
| rec_z0 | 0,9765 | 1,0000 | 0,9984 | 0,9591 | 0,9975 | 0,9915 |

- prop − raw: F1 **+0,0486**, rejeição **+0,3728**. rec_z0 − prop: F1 −0,0004, rejeição +0,0048.
- Em r1, a rejeição passa a marca do P0 (≥ 0,30) e o F1 não (≥ 0,10). É uma repetição; o critério não se aplica a ela.
- Comparando com r1 dos conjuntos antigos (`sets_by_fresnel.csv`): o que mudou foi o raw, muito mais forte aqui (F1
  0,928, rejeição 0,622, contra 0,785 / 0,105 no base e 0,794 / 0,097 no small_near); prop e rec_z0 ficaram no nível
  de antes (0,977 / 0,995 e 0,977 / 1,000).
- Validação (`results_exp_resolucao/eval/bench_1mm/val_openset_r1.csv`, as 4 dobras da calibração de evaluate, classes
  vistas retiradas da galeria fazendo papel de desconhecidas, média): raw F1 0,9665, rejeição 0,9827, fechada 0,9773;
  prop 0,9713 / 1,0000 / 0,9972; rec_z0 0,9710 / 1,0000 / 0,9987. **Cuidado ao ler:** as "desconhecidas" da validação
  são classes de treino, então a rejeição ali não mede o mesmo que a do teste (classes nunca vistas); o evaluate não
  produz uma rejeição de validação com classes novas.

### Robustez (r1, modelos, galeria e limiar de `bench_1mm`; `results_exp_resolucao/robustness_bench_1mm.csv`)

| linha | raw F1 / rej. | prop F1 / rej. | rec_z0 F1 / rej. |
|---|---|---|---|
| base (1,0 mm) | 0,9283 / 0,6224 | 0,9770 / 0,9952 | 0,9765 / 1,0000 |
| 0,7 mm, (a) como está | 0,8965 / 0,6087 | 0,0148 / 1,0000 | 0,0148 / 1,0000 |
| 0,7 mm, (b) literal | — | 0,5453 / 1,0000 | 0,9562 / 1,0000 |
| 0,7 mm, (b) razão | — | 0,9125 / 0,9992 | 0,9577 / 1,0000 |
| 50 µm, como está | 0,9288 / 0,6296 | 0,7732 / 0,9968 | 0,8014 / 1,0000 |

- (a): prop e rec_z0 rejeitam tudo (acurácia das conhecidas 0, fechada 0,20 e 0,21): a 0,7 mm a camada e a
  reconstrução focam 0,3 mm longe, 30 % de z. O raw perde pouco.
- (b), calibração (`results_exp_resolucao/recal_bench_1mm_z07.json`, 32 hologramas de validação a 0,7 mm, sem rótulo):
  α = 0,00074214 → z = **0,70092 mm** (sessões a 0,7 mm × (1 ± 0,5 %)); nos mesmos ids a 1,0 mm, α_ref = 0,0010616 →
  1,00263 mm; razão 0,69908 → z_razão = **0,69908 mm**. Literal: α do prop 0,0010332 → 0,0007421; razão: → 0,0007223.
  O literal do prop fica em 0,545 porque o α treinado se afastou 2,4 % do calibrado e a substituição desfaz esse
  deslocamento; a razão o preserva (0,913). O rec_z0 recupera nas duas (0,956 e 0,958). Que (b) recupere também diz
  que (a) não é um defeito dos dados regravados.
- Profundidade 50 / 150 µm (`bench_1mm_robust/depth50`): as anotações do teste são idênticas às do conjunto principal
  em todas as colunas a menos de `depth` e `z` (6371 letras; profundidades na razão exata 50/2,6, desvio 2,60 →
  49,97 µm), a poeira também (conferido no csv além do teste unitário). prop e rec_z0 caem para 0,773 e 0,801 em F1
  (rejeição mantida); raw não muda (0,929).

## 2026-11-14, 17:19 — R5: vazamento para fora do crop e os conjuntos pelo número de Fresnel (execução)

### (i) Vazamento (`python scripts/exp_resolucao/pattern_in_crop_1mm.py --set bench_1mm --device cuda:5`)

Mesma definição de `pattern_in_crop.py` (uma letra absorvente, a = 0,6, no centro, sem poeira nem ruído, fonte do
conjunto, energia (I − 1)², quadrado de lado × 1,25), com o gravador sobreamostrado (s = 4), letras F, A, O, W
desenhadas na grade mestra com o lado da tinta = p5 / p50 / p95 do conjunto. Janela 1024 (e 512: os mesmos valores
até a 4ª casa, a janela basta). `results_exp_resolucao/pattern_in_crop_bench_1mm.csv` e `_summary.csv`.

| tamanho | lado da tinta | N_F a 1,0 mm | fora do crop (tinta) | fora (caixa inteira) | a 0,7 mm |
|---|---|---|---|---|---|
| p5 | 12,81 px | 0,297 | 0,609 (0,555–0,661) | 0,609 | 0,557 |
| p50 | 17,38 px | 0,547 | 0,547 (0,525–0,575) | 0,509 | 0,445 |
| p95 | 23,31 px | 0,984 | 0,395 (0,341–0,467) | 0,381 | 0,292 |

Base a 19,25 mm (`setup_comparison.csv`): 0,595 / 0,511 / 0,387. O vazamento ficou o do base, como o mesmo N_F prevê.

### (ii) Conjuntos pelo número de Fresnel (`python scripts/exp_resolucao/sets_by_fresnel.py` → `sets_by_fresnel.csv`)

| conjunto | z₀ | N_F p5 / p50 / p95 | fora do crop p5 / p50 / p95 | reps | F1 raw / prop / rec_z0 | rejeição raw / prop / rec_z0 |
|---|---|---|---|---|---|---|
| realistic | 19,25 | 0,306 / 0,558 / 0,998 | 0,595 / 0,511 / 0,387 | média 5 | 0,781 / 0,964 / 0,964 | 0,104 / 0,924 / 0,923 |
| realistic | | | | r1 | 0,785 / 0,960 / 0,952 | 0,105 / 0,852 / 0,836 |
| small_z0 | 19,25 | 0,021 / 0,074 / 0,166 | 1,000 / 0,982 / 0,805 | média 5 | 0,050 / 0,845 / 0,842 | 0,003 / 0,333 / 0,302 |
| small_z0 | | | | r1 | 0,055 / 0,852 / 0,846 | 0,001 / 0,320 / 0,325 |
| small_near | 2,0 | 0,204 / 0,710 / 1,597 | 0,761 / 0,487 / 0,277 | média 5 | 0,793 / 0,972 / 0,974 | 0,153 / 0,963 / 0,970 |
| small_near | | | | r1 | 0,794 / 0,971 / 0,971 | 0,097 / 0,942 / 0,962 |
| bench_1mm | 1,0 | 0,297 / 0,547 / 0,982 (tinta) | 0,609 / 0,547 / 0,395 | **r1 só** | 0,928 / 0,977 / 0,977 | 0,622 / 0,995 / 1,000 |

N_F do bench_1mm pela caixa inteira: 0,355 / 0,587 / 1,043. Os conjuntos antigos têm caixas iguais à tinta. As médias
de 5 vêm de `setup_comparison.csv`, os r1 dos antigos de `results/eval/<conjunto>/<fluxo>_r1.json` (só lidos).

### O que parece estranho ou merece olhar (para o responsável)

1. O crop do holograma (raw) é muito melhor a 1,0 mm que no base com o mesmo N_F e o mesmo vazamento (F1 0,928 contra
   0,785; rejeição 0,622 contra 0,105, r1). Com o mesmo N_F, o padrão difere em coerência (o pinhole borra 0,67 µm a
   1 mm e 13 µm a 19,25 mm) e no pixel (a letra tem 17 px, não 77): o recorte de ~22 px ampliado para 64 parece servir
   mais ao raw. Não investiguei a causa.
2. A 0,7 mm "como está" a camada e o rec_z0 rejeitam tudo, enquanto o raw quase não perde: o modelo de crops é o mais
   robusto à distância nesta repetição.
3. O α treinado (0,9758 mm) se afasta 2,4 % do calibrado (0,9999 mm), e isso decide o (b) literal (0,545) contra o
   por razão (0,913).
4. Profundidade de 50 µm: prop e rec_z0 perdem ~0,2 em F1 (a 1,0 mm, 50 µm é 5 % de z, como 1 mm no base).

## 2026-11-14, 17:40 — P2: pré-registro das cinco repetições, dos dois controles e do treino com 50 µm (responsável)

Escrito depois do checkpoint do piloto (r1) e da resposta do orientador ("1 - ok; 2 - faz os 2 antes de reescrever;
3 - ok", na íntegra em `PROTOCOLO_PILOTO_1MM.md`), e antes de rodar qualquer uma destas coisas. Receita de treino,
galeria, limiar na validação e métricas como em r1; nenhuma escolha no teste; o que sair é reportado.

### A. Repetições r2–r5 no conjunto do piloto (`bench_1mm`)

- `raw`, `prop` (`--alpha-extend 12`), `rec_z0`, `--no-aux`, exatamente como r1; avaliação no teste; as três linhas de
  robustez de r1 em cada repetição (0,7 mm como está; 0,7 mm recalibrado, literal e por razão; profundidade de 50 µm).
- **Critério (P0, sem mudança):** uma repetição conta a favor se F1(prop) − F1(raw) ≥ 0,10 **e** rejeição(prop) −
  rejeição(raw) ≥ 0,30; a tese se mantém com 4 ou 5 a favor em r1–r5. r1 já está lida: +0,049 e +0,373 (não conta a
  favor). Reporto por repetição, a média, o mínimo e o máximo das diferenças, e quantas cumprem cada condição.

### B. Controle do código (r1)

Pergunta: a melhora dos crops a 1,0 mm vem do gravador e da cena novos?

- **Referência igual com igual (código antigo):** o conjunto base como está em disco (`realistic`, gravador e cena
  antigos, 19,25 mm), treinado agora em r1 com a receita do piloto (`--no-aux`), modelos e resultados nas pastas da
  etapa. Os números do paper (treino com cenas auxiliares) ficam ao lado, só para referência.
- **Controle (código novo):** conjunto novo a 19,25 mm com a cena em unidades físicas (`FresnelLayout`, fator 1: fontes
  de 70 a 118 px, 8 letras por janela, borda e espaçamento do base), física do base (margem 1728, alcance 1024,
  profundidade 50 / 150 µm), gravado pelo caminho sobreamostrado com s = 2, depois de conferir em 4 cenas que (2, 4)
  passa na tolerância de 1 % a 19,25 mm. Nome `base_newrec`. Mesma receita (`--no-aux`, r1).
- **Leitura, fixada agora, só com os crops (`raw`):** seja R_ant o par (F1, rejeição) da referência e R_pil = (0,928;
  0,622) o do piloto. Se o controle ficar mais perto de R_ant que de R_pil nas duas métricas, o código novo reproduz
  o antigo e a melhora a 1,0 mm não é efeito do código. Se ficar mais perto de R_pil nas duas, é efeito do código.
  Se der uma de cada, é inconclusivo e roda-se o braço que separa as duas peças novas: as cenas antigas do base
  (máscaras no pixel) gravadas pelo caminho sobreamostrado.

### C. Controle da vizinhança (r1)

Pergunta: o crop piora a 1,0 mm quando as vizinhas ficam tão perto, em relação ao tamanho da letra, quanto no base?

- **Conjunto `bench_1mm_dense`:** as mesmas cenas do `bench_1mm` (mesmas sementes: as mesmas 40 309 letras anotadas,
  nas mesmas posições, com os mesmos materiais, profundidades, poeira, sessões e câmera) **mais** letras não anotadas
  que completam a densidade relativa do base: ≈ 154 letras por janela de 640 × 640 no total (8 × 19,25), dentro da
  janela e na faixa em volta, de todas as classes, sem sobrepor nenhuma outra (a regra de espaçamento do conjunto),
  sorteadas por um gerador separado para não mexer no resto da cena. Só as letras anotadas entram no treino e na
  avaliação, como as letras de fora da janela no base. Assim o treino e a avaliação têm o mesmo tamanho do piloto e
  a comparação é pareada letra a letra; a única diferença é a vizinhança.
  (O orientador aprovou "≈ 154 letras por janela"; anotar só as 8 de sempre é escolha minha, pelo motivo acima.)
- Gravador, s = 4, física e receita iguais às do piloto.
- **Leitura, fixada agora, só com os crops:** com R_ant e R_pil como em B, a vizinhança explica a melhora se, no
  conjunto denso, os crops ficarem mais perto de R_ant que de R_pil nas duas métricas; não explica se ficarem mais
  perto de R_pil nas duas; parcial se der uma de cada. Reporto também `prop` e `rec_z0` e as diferenças pareadas
  para o `bench_1mm`.

### D. Treino com 50 µm de profundidade (r1)

- **Conjunto `bench_1mm_depth50`:** o `bench_1mm` gravado de novo em todos os splits com `depth_std` = 50 µm e
  `depth_max` = 150 µm (mesmas sementes; o split de teste é o `bench_1mm_robust/depth50` já gravado).
- `raw`, `prop`, `rec_z0` treinados e avaliados nele em r1. Reporto ao lado: treinado com 2,6 µm e testado com 50 µm
  (já lido: 0,929 / 0,773 / 0,801 de F1), e treinado com 50 µm testado com 2,6 µm (o teste do `bench_1mm`).
- Sem critério: a pergunta é quanto do 0,2 de F1 perdido volta com o treino.

### Ordem e execução

Dois executores, um processo de GPU por vez cada um: (i) repetições r2–r5, referência do B e conjunto do D, com o
código que já existe; (ii) código e gravação dos dois conjuntos de controle (B e C). Nada é rodado de novo com outra
configuração depois de lido o teste; erro de código (não número decepcionante) para tudo e é reportado antes de
qualquer nova rodada.

## 2026-11-14, 17:57 — K1: as letras de enchimento do controle C (código, testes, conferência prévia) (execução, controles)

Commits `bca2f3a` (código e testes) e `6db31c6` (scripts). Arquivos: `holo_openset/sim/scene.py` (`FresnelLayout.fill_mean`,
`fill_letters`), `sim/generate.py` (contagens em `metadata.csv`), `tests/test_fill.py`,
`scripts/exp_resolucao/controls_1mm.sh`, `scripts/exp_resolucao/controls_checks.py`,
`scripts/exp_resolucao/oversampling_convergence.py` (`--n-scenes`, padrão 8, sem mudança no que já rodou).

### Desenho das letras de enchimento (`fill_mean`, padrão 0 = desligado)

- Parâmetro do layout físico (`--layout ... fill_mean=154`). Desligado, `params()` não escreve a chave: o
  `physics.json` de um conjunto existente regravado fica igual byte a byte.
- Gerador próprio: `random.Random(semente da cena + 900 000 000)` (`FILL_SEED`), usado depois das letras anotadas e
  das letras em volta da janela, antes da poeira; o gerador da cena não é tocado, então letras, materiais,
  profundidades, poeira, sessões e câmera não mudam. As letras de enchimento são acrescentadas no FIM da lista de
  objetos, com `kind = 'filler'`: nunca entram em `rows` (anotações, rótulos YOLO), nem nos mapas de verdade
  (`object_maps` só lê `kind == 'letter'`), nem em `n_outside`.
- Contagem, por região, contando as letras que a cena já tem: na janela, Poisson(154 × 640²/TILE = 154) menos as
  anotadas; na faixa do alcance, Poisson(154 × área da faixa / 640²) menos as letras em volta da janela (nunca
  abaixo de 0). Mesmo sorteio de Poisson que as letras em volta da janela já usam (`poisson`, aproximação normal
  acima de 50).
- Cada letra como as do conjunto: classe uniforme em todas as 26 (`outside_classes` quando houver, como as de fora),
  fonte, tamanho contínuo, rotação, material e profundidade com as mesmas leis (`material`); posição uniforme onde as
  do conjunto vão: na janela com a borda das anotadas, na faixa sem tocar a janela (± espaçamento), como as de fora.
  Nenhuma letra fica sobre a borda da janela (como no conjunto). Regra de espaçamento do conjunto na grade de
  ocupação. Escolha minha: a letra é sorteada uma vez e só a posição é sorteada de novo (até
  `max_attempts_per_letter` = 500); se não couber, é pulada e contada (`n_fill_skipped` no `metadata.csv`) — uma
  cena nunca é rejeitada por causa do enchimento (isso trocaria a semente e as letras anotadas).
- `metadata.csv` ganha `n_fill_window`, `n_fill_band`, `n_fill_skipped` só com o enchimento ligado.

### Testes (`tests/test_fill.py`, CPU, 11 s)

1. Desligado (`FresnelLayout()` e `fill_mean=0`): sha256 de quatro cenas (todos os objetos, rasters, posições,
   materiais, poeira, poeira do sensor, anotações) igual ao calculado com o código ANTES da mudança (`4a49578`).
2. Ligado: os objetos da cena sem enchimento estão todos lá, iguais e na mesma ordem; anotações iguais; enchimento
   só `filler`; dentro da janela com a borda ou fora da janela sem tocá-la; espaçamento entre quaisquer duas letras.
3. Contagem: em 40 cenas, letras na janela e na faixa com as médias de Poisson esperadas (4 erros-padrão).
4. `generate()` com e sem enchimento: `annotations.csv`, `dust.csv`, `sessions.csv`, `backgrounds.npy`, `labels/`,
   `objects/` idênticos byte a byte; hologramas diferentes.

`pytest`: 64 passam (56 + 8).

### Conferência prévia, antes de gravar

`controls_checks.py removed --ref bench_1mm --ids 0 300 --device cuda:5`: as cenas 0 (teste, 3 anotadas, 450 de
enchimento) e 300 (treino, 10 anotadas, 457) refeitas das sementes, gravadas SEM o enchimento como o `generate` grava
(mesma sessão, câmera, gerador de ruído, GPU): idênticas ao `holograms.npy` do `bench_1mm` (diferença máxima 0
níveis). Custo da cena com enchimento: ≈ 2,2–2,8 s num processo (460 letras; 60 % na rotação do raster mestre 16×),
contra 0,18 s sem.

Gravação: `bash scripts/exp_resolucao/controls_1mm.sh 5 dense_record` (tmux `res_ctrl_dense_record`, 17:51).


## 2026-11-14, 18:21 — P2-A: repetições r2–r5 do `bench_1mm` e o critério do P0 (execução)

Commits `47514f5` (script com a repetição como parâmetro), `0ec3790` (resumo), `28c0244` (resultados).
`pilot_1mm.sh` ganhou `REP=1..5` e o passo `rep` (train, evaluate, robust_a, robust_b, robust_depth50 da repetição);
nada que exista é refeito: o r1 não foi tocado (conferido por md5 de `robustness_bench_1mm.csv` e dos três json de r1
depois de rodar os passos com `REP=1`, que só imprimiram "exists" / "rows of r1 exist"; essas chamadas de checagem
acrescentaram linhas aos logs de r1). As gravações a 0,7 mm, os caches e o json da recalibração não dependem da
repetição e foram reaproveitados; o α treinado de cada repetição é o que muda na variante por razão.

Comando (tmux `res_pilot_reps`, GPU 5, um processo por vez):
`for R in 2 3 4 5; do REP=$R bash scripts/exp_resolucao/pilot_1mm.sh 5 rep; done` — 17:42 a 18:12; por repetição
424 / 473 / 442 / 443 s (treino 276–309 s, avaliação 43–52 s, robustez 17–58 s por passo). Resumo:
`python scripts/exp_resolucao/pilot_five_reps.py` → `results_exp_resolucao/pilot_five_reps.csv`,
`pilot_five_reps_robustness.csv` (e `_rows.csv`), `pilot_five_reps_alpha.csv`.

### As cinco repetições (teste; limiar da validação)

| rep | F1 raw / prop / rec_z0 | rejeição raw / prop / rec_z0 | prop − raw F1 | prop − raw rej. | rec_z0 − prop F1 / rej. |
|---|---|---|---|---|---|
| 1 | 0,9283 / 0,9770 / 0,9765 | 0,6224 / 0,9952 / 1,0000 | +0,0486 | +0,3728 | −0,0004 / +0,0048 |
| 2 | 0,9422 / 0,9736 / 0,9788 | 0,7437 / 1,0000 / 1,0000 | +0,0314 | +0,2563 | +0,0052 / 0,0000 |
| 3 | 0,9339 / 0,9770 / 0,9806 | 0,6998 / 0,9930 / 0,9914 | +0,0431 | +0,2932 | +0,0036 / −0,0016 |
| 4 | 0,9451 / 0,9800 / 0,9781 | 0,8288 / 0,9992 / 0,9992 | +0,0349 | +0,1704 | −0,0019 / 0,0000 |
| 5 | 0,9415 / 0,9763 / 0,9803 | 0,7545 / 1,0000 / 1,0000 | +0,0348 | +0,2455 | +0,0040 / 0,0000 |
| média | 0,9382 / 0,9768 / 0,9789 | 0,7299 / 0,9975 / 0,9981 | +0,0386 | +0,2676 | +0,0021 / +0,0007 |
| mín. | 0,9283 / 0,9736 / 0,9765 | 0,6224 / 0,9930 / 0,9914 | +0,0314 | +0,1704 | −0,0019 / −0,0016 |
| máx. | 0,9451 / 0,9800 / 0,9806 | 0,8288 / 1,0000 / 1,0000 | +0,0486 | +0,3728 | +0,0052 / +0,0048 |

Acurácia fechada: raw 0,9751–0,9780, prop 0,9967–0,9976, rec_z0 0,9983–0,9988; limiar raw 0,832–0,888, prop
0,992–0,994, rec_z0 0,990–0,992 (todas as colunas no csv).

**Critério do P0, aplicado mecanicamente:** F1(prop) − F1(raw) ≥ 0,10 em **0 de 5**; rejeição(prop) − rejeição(raw)
≥ 0,30 em **1 de 5** (r1); as duas em **0 de 5**. A regra pede 4 ou 5.

### Robustez nas cinco repetições (média / mín. / máx.; `pilot_five_reps_robustness.csv`)

| linha | F1 | rejeição |
|---|---|---|
| raw, base | 0,9382 / 0,9283 / 0,9451 | 0,7299 / 0,6224 / 0,8288 |
| raw, 0,7 mm como está | 0,9107 / 0,8965 / 0,9241 | 0,7428 / 0,6087 / 0,8375 |
| prop, 0,7 mm como está | 0,0150 / 0,0146 / 0,0153 | 1,0000 (todas) |
| rec_z0, 0,7 mm como está | 0,0150 / 0,0146 / 0,0153 | 1,0000 (todas) |
| prop, recalibrado literal | 0,5095 / 0,4558 / 0,5453 | 0,9988 / 0,9938 / 1,0000 |
| prop, recalibrado razão | 0,9137 / 0,8988 / 0,9296 | 0,9963 / 0,9821 / 1,0000 |
| rec_z0, recalibrado literal | 0,9629 / 0,9562 / 0,9683 | 0,9967 / 0,9852 / 1,0000 |
| rec_z0, recalibrado razão | 0,9639 / 0,9577 / 0,9693 | 0,9964 / 0,9844 / 1,0000 |
| raw, 50 µm como está | 0,9387 / 0,9288 / 0,9450 | 0,7384 / 0,6296 / 0,8329 |
| prop, 50 µm como está | 0,7842 / 0,7732 / 0,7997 | 0,9986 / 0,9961 / 1,0000 |
| rec_z0, 50 µm como está | 0,8225 / 0,8014 / 0,8410 | 0,9995 / 0,9984 / 1,0000 |

### α do prop (`pilot_five_reps_alpha.csv`; o calibrado recalculado na CPU nos mesmos 32 hologramas que `train()`
sorteou)

| rep | α calibrado | z calibrado | α treinado | z treinado | mudança |
|---|---|---|---|---|---|
| 1 | 0,0010587 | 0,99986 mm | 0,0010332 | 0,97582 mm | −2,40 % |
| 2 | 0,0010587 | 0,99986 mm | 0,0010290 | 0,97186 mm | −2,80 % |
| 3 | 0,0010587 | 0,99986 mm | 0,0010294 | 0,97221 mm | −2,77 % |
| 4 | 0,0010587 | 0,99986 mm | 0,0010291 | 0,97190 mm | −2,80 % |
| 5 | 0,0010557 | 0,99709 mm | 0,0010334 | 0,97605 mm | −2,11 % |

(r1–r4 sortearam os mesmos 32 hologramas: quase toda imagem tem uma letra vista, e o sorteio é sobre as imagens.)

## 2026-11-14, 18:21 — P2-B referência: o base em disco treinado em r1 com a receita do piloto (execução)

`bash scripts/exp_resolucao/reference_noaux.sh 5` (tmux `res_pilot_reference`, 18:12:41–18:19:31, 410 s; commits
`0ec3790` e `7694b72`). O script imprime os seis alvos antes de escrever e recusa rodar se `HOLO_MODELS`/`HOLO_RESULTS`
apontassem para `models/`/`results/` ou se um alvo existisse; os alvos foram
`models_exp_resolucao/realistic/{raw,prop,rec_z0}_r1.pt` e `results_exp_resolucao/eval/realistic/{raw,prop,rec_z0}_r1.json`.
`train --set realistic --flow <f> --rep 1 --no-aux` (o `prop` com a grade padrão: α calibrado 0,020411, o da bancada
0,020382, depois do treino 0,020255) e `evaluate --set realistic --flow <f> --rep 1`. O `rec_z0.npy` de `data/realistic`
só foi lido.

| r1, teste | F1 | rejeição | fechada | conhecidas | limiar |
|---|---|---|---|---|---|
| raw, agora (sem auxiliares) | 0,7742 | 0,0733 | 0,8791 | 0,8740 | 0,5598 |
| prop, agora | 0,9588 | 0,8688 | 0,9936 | 0,9538 | 0,9702 |
| rec_z0, agora | 0,9562 | 0,8615 | 0,9920 | 0,9497 | 0,9736 |
| raw, paper (com auxiliares) | 0,7853 | 0,1047 | 0,8844 | 0,8785 | 0,5558 |
| prop, paper | 0,9595 | 0,8519 | 0,9914 | 0,9559 | 0,9702 |
| rec_z0, paper | 0,9519 | 0,8357 | 0,9922 | 0,9460 | 0,9738 |

R_ant (referência do B, raw) = (0,7742; 0,0733).

**Pastas do paper:** comparei a listagem com data e tamanho de todos os arquivos de `data/realistic`, `models/`,
`results/` e `expected/` antes (17:44) e depois (18:19): nada mudou, salvo a data de `results/data_summary.json`
(17:47:30, conteúdo idêntico: o git não o vê modificado). Esse arquivo é reescrito por qualquer `paper tables` com
`HOLO_RESULTS` desligado, isto é, por `pytest` ou `reproduce check` (`tables.data_numbers`); às 17:47 eu não rodei
nenhum dos dois (o outro executor ou o responsável sim, presumo).

## 2026-11-14, 18:57 — P2-D: treino com 50 µm de profundidade (execução)

Commits `b43b815` (script `scripts/exp_resolucao/depth_training.sh` e tabela `depth_training.py`), `8cbe98b`
(resultados). Passos: `bash scripts/exp_resolucao/depth_training.sh 5 <passo>`, tmux `res_pilot_depth_*`, logs
`logs/exp_resolucao/depth_<passo>.log`.

- **Desvio / erro meu, parado a tempo:** a primeira tentativa usou `simulate like --like bench_1mm --name
  bench_1mm_depth50` sem `--split`, mas o `--split` do `simulate` tem padrão `test`: começou a gravar só as 800
  imagens de teste. Parei em 30 s (só os quadros em branco tinham sido escritos), apaguei `data/bench_1mm_depth50` e
  gravei chamando `generate(like=bench_1mm, split=None, phys=dict(depth_std=50e-6, depth_max=150e-6))` direto (não
  mexi em `cli.py`, que é do outro executor agora). Nada foi lido nem avaliado nesse meio-tempo.
- `record`: 18:20:37–18:46:05, 1528 s (GPU 5 dividida com a gravação do `bench_1mm_dense`); 8,7 GB com o
  `rec_z0.npy`. Conferido: 40 309 anotações iguais às do `bench_1mm` em todas as colunas a menos de `depth` e `z`;
  profundidades na razão exata 50/2,6 (desvio 49,97 µm); z − profundidade (a distância da sessão) igual;
  `metadata.csv` idêntico; o split de teste igual **pixel a pixel** ao `bench_1mm_robust/depth50` nas 800 imagens
  (também nas 13 escolhidas antes); a imagem 0 difere da do `bench_1mm`.
- `reconstruct` 74 s; `train` 318 s (prop: α calibrado 0,0010440 → 0,98601 mm; depois do treino 0,0010521 →
  0,99369 mm, +0,78 %); `evaluate` 50 s; `cross` 25 s: `experiment robustness --set bench_1mm_depth50
  --variants-root . --variants bench_1mm --flows raw prop rec_z0 --rep 1 --out robustness_bench_1mm_depth50` (modelos
  de 50 µm, galeria e limiar da validação do próprio conjunto, padrões de teste do `bench_1mm`; as anotações conferem).

`results_exp_resolucao/depth_training.csv` (r1, teste; a linha treinado 2,6 / testado 50 copiada de
`robustness_bench_1mm.csv`, sem recalcular):

| treinado / testado | F1 raw / prop / rec_z0 | rejeição raw / prop / rec_z0 |
|---|---|---|
| 2,6 µm / 2,6 µm | 0,9283 / 0,9770 / 0,9765 | 0,6224 / 0,9952 / 1,0000 |
| 2,6 µm / 50 µm | 0,9288 / 0,7732 / 0,8014 | 0,6296 / 0,9968 / 1,0000 |
| 50 µm / 50 µm | 0,9239 / 0,9767 / 0,9751 | 0,6047 / 0,9976 / 0,9944 |
| 50 µm / 2,6 µm | 0,9233 / 0,9836 / 0,9762 | 0,5950 / 0,9968 / 1,0000 |

### Conferências finais (P2)

- `env -u HOLO_RESULTS -u HOLO_MODELS python -m pytest -q`: 64 passam (os 56 de antes e os 8 do outro executor);
  `env -u HOLO_RESULTS -u HOLO_MODELS python -m holo_openset reproduce check`: 13/13.
- `data/realistic`, `models/`, `results/`, `expected/`: listagem com data e tamanho de cada arquivo igual à de
  17:44, salvo a data de `results/data_summary.json` (reescrito com o mesmo conteúdo por `paper tables`, isto é, por
  `pytest`/`reproduce check`; o git não vê mudança).
- Disco desta etapa: `data/bench_1mm_depth50` 8,7 GB; modelos `models_exp_resolucao/bench_1mm` 669 MB (15),
  `bench_1mm_depth50` 134 MB, `realistic` 134 MB.

## 2026-11-14, 19:43 — K2: controle C (vizinhança) rodado: `bench_1mm_dense` gravado, conferido, treinado e avaliado em r1 (execução, controles)

GPU 5 (H100, compartilhada), um processo de GPU por vez, 4 threads, 3 construtores de cena, tmux `res_ctrl_*`, logs
`logs/exp_resolucao/controls_<passo>.log`.

| passo | comando | parede |
|---|---|---|
| dense_record | `bash scripts/exp_resolucao/controls_1mm.sh 5 dense_record` | 5018 s |
| dense_verify | `... 5 dense_verify` (`controls_checks.py dense` + `bench_sanity.py`) | 338 s |
| dense_reconstruct | `... 5 dense_reconstruct` | 76 s |
| dense_train | `... 5 dense_train` (raw 96 s, prop 111 s, rec_z0 ≈ 110 s) | 318 s |
| dense_evaluate | `... 5 dense_evaluate` | 42 s |

O comando de gravação é o do `pilot_1mm.sh record` (`DEPTH=2.6 DENSITY=base`) com `fill_mean=154` a mais no
`--layout`. Disco: `data/bench_1mm_dense` 9,0 GB (com `rec_z0.npy`), modelos 134 MB.

### Conferências (`results_exp_resolucao/bench_1mm_dense_checks.json`, `bench_1mm_dense_sanity.json`)

- `annotations.csv`: **idêntico byte a byte** ao do `bench_1mm` (40 309 linhas; treino 28 227, validação 5711, teste
  6371; todas as 21 colunas iguais). Também idênticos: os 5000 rótulos YOLO, os 1600 mapas de verdade (`objects/`),
  `dust.csv`, `sessions.csv`, `backgrounds.npy`, e as colunas comuns de `metadata.csv`. `physics.json`: a única
  diferença é `layout_params.fill_mean = 154`.
- **O enchimento é a única diferença:** imagens 100 (treino) e 0 (teste) refeitas das sementes: sem o enchimento,
  iguais ao `holograms.npy` do `bench_1mm` (diferença máxima 0 níveis); com ele, iguais ao `holograms.npy` do
  `bench_1mm_dense` (0 níveis). O enchimento muda o holograma em 15,8–16,9 níveis rms.
- Letras por janela 640 × 640 (todas as 5000 imagens): anotadas 8,06 + enchimento 146,04 = **154,10** (dp 12,36;
  p5 / p50 / p95 = 134 / 154 / 175; mín. 116, máx. 205; treino 154,12, validação 154,21, teste 153,93). Na faixa do
  alcance, por área de 640 × 640: 7,97 (as de fora, como no piloto) → **153,84** com o enchimento. Nenhuma letra de
  enchimento deixou de caber (0 puladas).
- Área coberta (100 cenas refeitas; soma das caixas de tinta das letras na janela / área da janela, média por imagem):
  **10,54 %** no denso (anotadas: 0,56 %) contra **10,70 %** no base (`realistic`, das anotações); pela soma do lado
  maior ao quadrado, 12,23 % contra 12,38 %. O "≈ 11,6 %" do brief é a mediana do lado ao quadrado × 8 do base
  (77² × 8 / 640² = 11,58 %); as duas medidas por imagem dão 10,7 % e 12,4 %.
- Sanidade (só treino): lados de caixa e de tinta iguais aos do piloto (as mesmas letras); nível médio 99,63 (piloto
  101,49: mais letras cobrem mais área); quadros em branco 101,51; ruído refeito das sementes: média 0,002–0,006
  níveis, rms 2,069–2,081.
- Folha de contato `docs/exp_resolucao/img/bench_1mm_dense_examples.png` (mesmo estilo de `bench_1mm_examples.png`):
  janela cheia de padrões de anéis; as caixas anotadas são 3–18 entre ~150 letras.

### α da camada (prop, r1)

Calibrado (grade estendida 12 passos, 32 hologramas de treino): 0,001059 (precisão do log) → ≈ 1,000 mm. Depois do
treino: 0,0010366 → **0,9790 mm** (piloto: 0,0010332 → 0,9758 mm).

### Resultados de r1 (`results_exp_resolucao/eval/bench_1mm_dense/<fluxo>_r1.json`; teste lido uma vez)

| fluxo | F1 | rejeição | fechada | conhecidas | limiar | F1 − piloto | rejeição − piloto |
|---|---|---|---|---|---|---|---|
| raw | 0,7957 | 0,0797 | 0,9004 | 0,8947 | 0,5747 | −0,1326 | −0,5427 |
| prop | 0,9595 | 0,8994 | 0,9871 | 0,9499 | 0,9779 | −0,0174 | −0,0958 |
| rec_z0 | 0,9676 | 0,9517 | 0,9951 | 0,9538 | 0,9829 | −0,0089 | −0,0483 |

prop − raw no denso: F1 +0,1638, rejeição +0,8197.

### Regra de leitura do P2 (C), aplicada mecanicamente (só crops)

R_pil = (0,9283; 0,6224) (`eval/bench_1mm/raw_r1.json`); R_ant = (0,7742; 0,0733) (`eval/realistic/raw_r1.json`,
a referência sem auxiliares do P2-B, do outro executor). Controle C (raw): (0,7957; 0,0797). Distâncias: F1 0,0215
a R_ant contra 0,1326 a R_pil; rejeição 0,0064 contra 0,5427. **Mais perto de R_ant nas duas: pela regra, a
vizinhança explica a melhora.** (`results_exp_resolucao/controls.csv`, `controls_reading.json`.)
