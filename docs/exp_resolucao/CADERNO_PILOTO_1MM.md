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
