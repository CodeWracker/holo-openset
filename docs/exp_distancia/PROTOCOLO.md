# Protocolo de experimentos: quando o focal stack economiza tempo de verdade

**Projeto:** Open-Set Recognition of Interference Patterns on Raw Lensless Holograms (paper "nature_openset_microscopy", código em `holo-openset`)
**Responsável pela execução:** estagiário(a) de mestrado
**Orientação:** Rodrigo Ferraz Souza
**Versão do código de partida:** commit `9488fce` de `github.com/CodeWracker/holo-openset` (2 nov. 2026)

Este documento é o pré-registro dos experimentos: ele diz o que queremos saber, o que esperamos, o que conta como resposta e como medir. Leia inteiro antes de escrever qualquer linha de código. Se algo aqui contradisser o código ou o paper, pare e pergunte, não "conserte" por conta própria.

---

## 1. Por que estes experimentos existem

### 1.1 A história em três parágrafos

Em 2024 publicamos no CBMS (Rockembach et al.) que reconhecer padrões direto no holograma bruto, com um YOLO, seria mais rápido que o fluxo clássico de reconstruir e depois classificar. Aquele ganho nunca foi medido, e ao evoluir a pesquisa vimos que ele não se sustenta. Uma reconstrução numérica é um par de FFTs e custa cerca de 1 ms num quadro inteiro de 10 MP em GPU, contra cerca de 222 ms do detector, que roda nos dois fluxos de qualquer jeito. O que custa caro no fluxo clássico é repetir a reconstrução: autofocus com 114 candidatos, remoção da twin image com 50 passes, foco por objeto. Além disso, aqueles dados de 2024 (parte real do campo, letras opacas num plano, janela periódica, z fixo e conhecido) não exigiam nenhuma dessas repetições. O "fluxo clássico caro" era um espantalho.

O paper novo (RQ4, Seção 7.4, Tabelas 8 e 9) já corrige isso e diz explicitamente que a camada aprendida não é mais barata que uma reconstrução calibrada. Mas ele também mostra um resultado que pode virar um ganho de tempo legítimo: o **focal stack aprendido** (`bank_jit` e variantes mais largas) troca o autofocus por K pares de FFT, sem λ, Δ, z nem blank frame, e não quebra sob ruído, como o autofocus quebra. No front end de um quadro inteiro são 3,5 ms contra 123,7 ms em GPU, e 5,3 s contra 238,7 s num core de CPU (Tabela 8).

O problema é que, na simulação atual, a distância z é fixa dentro de cada sessão de 100 imagens. Um revisor vai dizer, com razão: "faça o autofocus uma vez por sessão e reutilize". Isso custa 123,7 ms / 100 ≈ 1,2 ms por quadro e mataria a vantagem de tempo. O fluxo "autofocus em todo holograma" da Tabela 9 seria, nesse cenário, o mesmo tipo de espantalho de 2024. **Estes experimentos existem para descobrir em que condições o ganho de tempo do focal stack é real, medido contra o melhor baseline razoável, e para que o paper diga exatamente isso, nem mais nem menos.**

### 1.2 A regra que vale acima de todas

Qualquer resultado é publicável. Se o focal stack não tiver vantagem de tempo legítima em nenhum cenário plausível, isso é um resultado e vai para o paper. O seu trabalho é medir com honestidade, não fazer o método proposto ganhar. Concretamente:

1. Todo baseline deve ser a melhor versão razoável dele, não a mais cara.
2. Todo hiperparâmetro (largura do stack, faixa do autofocus, intervalo de refoco etc.) é escolhido no split de validação, nunca no de teste.
3. Toda comparação de tempo é reportada duas vezes: só o front end e fim a fim com o detector.
4. Nada é extrapolado: tempo que aparece numa tabela foi medido.

---

## 2. O que você precisa saber antes de começar

### 2.1 A física mínima

O microscópio de referência (Sobieranski et al., 2015; `docs/EQUIPMENT.md`) é um LED UV de 385 nm atrás de um pinhole de 100 µm a 15 cm, a amostra numa lâmina, e um sensor CMOS de 3840 × 2748 pixels de 1,67 µm (29,4 mm²) lido em 8 bits. Não há lente. O sensor grava a intensidade da interferência entre a luz espalhada por cada objeto e a onda que passa direto. Cada objeto vira um conjunto de anéis concêntricos que se espalham muito além dele (Fig. 2 do paper).

Três parâmetros entram numa reconstrução: o comprimento de onda λ e o pixel Δ são do equipamento e fixos; **a distância z da amostra ao sensor é da amostra**. Ela depende da espessura da lâmina e da lamínula e de como a lâmina foi montada, e muda de uma montagem para outra muito mais que a profundidade de campo (≈ 30 µm). O valor nominal é z₀ = 50 000 λ = 19,25 mm.

Reconstruir é dividir o holograma pelo blank frame da sessão (`sqrt(I/B)`), e propagar de volta por −z com o kernel de Fresnel (um par de FFTs; `reconstruct.backprop`). Se z estiver errado, a imagem sai desfocada. O **autofocus** cego (`reconstruct.autofocus`) reconstrói em 73 distâncias entre 0,2 z₀ e 2,1 z₀, depois em 41 em torno da melhor, e fica com a mais nítida pelo coeficiente de Tamura do gradiente (ToG). São 114 reconstruções por holograma. A Fig. 3 do paper mostra a curva.

### 2.2 Os fluxos comparados

Todos os fluxos usam a mesma rede (ResNet18 + MLP, embedding de 128 dimensões, galeria com limiares calibrados) e o mesmo localizador YOLO. Só muda o que a rede recebe (`holo_openset/flows.py`):

| fluxo | o que a rede recebe | precisa de |
|---|---|---|
| `raw` | o holograma | nada |
| `learned` | camada de Fourier real aprendida (ablação) | nada |
| `prop` | camada com a fase da propagação, um escalar α calibrado nos hologramas | nada |
| `bank_jit` | focal stack: 5 distâncias em ±5 % de α, treinado com jitter de 5 % na distância | nada |
| `bank_wide` | 7 distâncias em ±12 %, jitter 12 % | nada |
| `bank_w2` | 9 distâncias em ±12 %, jitter 12 % | nada |
| `rec_z0` | back-propagation em z₀ (o que a bancada faz) | λ, Δ, z₀, B |
| `rec_af` | back-propagation na distância do autofocus de cada holograma | λ, Δ, B |
| `rec_edf` | foco por objeto (25 reconstruções em ±1,2 % do foco) | λ, Δ, B |
| `rec_twin` | autofocus + 50 passes de remoção da twin image | λ, Δ, B |

O focal stack é, na prática, um autofocus amortizado. O α é calibrado uma vez, sem labels, e a tolerância à distância vem do jitter no treino. Por isso o custo dele por quadro é fixo (K pares de FFT), aconteça o que acontecer com z.

### 2.3 Os números de referência que você vai reencontrar

Tempo por estágio (Tabela 8; GPU = H100, mínimo de 20 repetições; CPU = um core, mediana):

| estágio | GPU janela (ms) | GPU quadro (ms) | CPU janela (ms) | CPU quadro (s) |
|---|---|---|---|---|
| back-propagation (1 rec.) | 0,2 | 1,0 | 22,0 | 2,19 |
| propagation layer (`prop`) | 0,3 | 1,1 | 9,7 | 1,76 |
| focal stack, 5 distâncias | 0,3 | 3,5 | 53,3 | 5,28 |
| autofocus (114 rec.) | 4,9 | 123,7 | 7422,8 | 238,73 |
| foco por objeto (25 a mais) | 1,7 | 48,2 | 1492,5 | 51,02 |
| twin removal (50 passes) | 8,5 | 85,8 | 1632,4 | 198,17 |
| YOLO em tiles | 13,0 | 221,7 | 1331,0 | 52,79 |
| embedding ResNet18 | 2,2 | 2,4 | 170,2 | 2,04 |

Open-set F1 sob mudança da aquisição (Tabela 10, média de 5 splits, modelos do conjunto base):

| gravação | `prop` | `bank_jit` | `rec_z0` | `rec_af` |
|---|---|---|---|---|
| base | 0,96 | 0,96 | 0,96 | 0,96 |
| distância entre sessões 2 % | 0,94 | 0,96 | 0,94 | 0,96 |
| distância entre sessões 5 % | 0,75 | 0,84 | 0,75 | 0,96 |
| shot noise, full well 500 e⁻ | 0,96 | 0,96 | 0,95 | 0,77 |
| feixe estreito (0,9–1,3) | 0,88 | 0,88 | 0,96 | 0,43 |
| spread de profundidade 300 µm | 0,96 | 0,96 | 0,96 | 0,96 |

Focal stacks mais largos (Tabela 11): 7/±12 %/12 % chega a 0,952 no base e 0,944 com drift de 5 %; 9/±12 %/12 % chega a 0,952 e 0,944. O stack do paper (5/±5 %/5 %) dá 0,963 e 0,839.

Guarde dois fatos destas tabelas, porque eles definem o desenho dos experimentos. Primeiro, o autofocus ganha quando z varia e perde quando há ruído ou iluminação ruim. Segundo, **um spread de profundidade por objeto de 300 µm (desvio padrão) não custa nada a nenhum fluxo**: a rede tolera bem centenas de micrômetros de desfoco local. Isso importa para o experimento de inclinação (E4).

### 2.4 Amdahl: por que o ganho fim a fim é pequeno

O detector roda em todo fluxo e custa cerca de 222 ms por quadro em GPU. Trocar o autofocus (124 ms) pelo stack (3,5 ms) leva o fluxo de cerca de 0,43 s para 0,29 s por quadro (Tabela 9), cerca de 1,5×. Em CPU a razão é maior (algo como 5×) porque o autofocus em CPU custa minutos. Sempre reporte os dois: front end sozinho e fim a fim. Um ganho de 35× no front end e de 1,5× fim a fim são verdadeiros ao mesmo tempo, e o leitor precisa dos dois.

### 2.5 O protocolo de avaliação que você não pode quebrar

O protocolo estrito do paper (Seção 6; `holo_openset/evaluate.py`) é o que torna os números comparáveis:

1. **Cinco repetições** r1–r5, cada uma deixa cinco das 26 letras como nunca vistas (`holo_openset/partitions/`). Todo número é média ± desvio padrão sobre as cinco.
2. **Split por sessão**: treino, validação e teste usam sessões diferentes (35/7/8 de 50). A amostra de teste nunca foi montada no treino.
3. **O limiar é calibrado só na validação, só com classes vistas** (FRR de 5 % sobre pares genuínos) e congelado antes de olhar o teste.
4. **Robustez**: os modelos, galerias e limiares são os do conjunto base. Só os hologramas de teste mudam. Um sistema calibrado numa aquisição encontra outra.
5. As classes nunca vistas nunca entram em treino, seleção de modelo ou calibração.

Métricas principais: AUROC (vistas contra nunca vistas), rejeição das nunca vistas, acurácia das vistas e **open-set F1**, que é a métrica-resumo das tabelas. Para o autofocus, reporte também o erro de distância |z_af − z_verdadeiro| (mediana e percentil 90), que você obtém do `autofocus.csv` sem rede nenhuma.

---

## 3. Perguntas, hipóteses e critérios de decisão

Escrevemos aqui o que esperamos antes de rodar. Se o resultado contrariar a expectativa, ótimo: é por isso que medimos.

**Q1. No cenário atual (z fixo por sessão de 100 imagens), o focal stack tem vantagem de tempo sobre o melhor autofocus razoável?**
H1: não. Um autofocus feito uma vez por sessão e reutilizado (`rec_afs`) deve dar o mesmo F1 que `rec_af` (≈ 0,96 em `session_5`) a um custo por quadro próximo de `rec_z0`. Se H1 se confirmar, o paper não pode vender ganho de tempo nesse cenário, e escreveremos isso.

**Q2. Quando a distância muda a cada quadro, o ganho aparece?**
H2: sim, dentro de limites. Com z mudando por quadro, `rec_afs` cai para o nível de `rec_z0`, `rec_af` mantém cerca de 0,96, e um stack largo (`bank_wide` ou `bank_w2`) fica a cerca de 0,02 de `rec_af` com front end dezenas de vezes mais barato. A pergunta quantitativa é a seguinte: a partir de quantos quadros por montagem n o autofocus por sessão passa a ser mais barato que o stack? Com os números da Tabela 8 e autofocus cego de 114 candidatos, n* = T_af / (T_stack − T_backprop) ≈ 123,7 / (3,5 − 1,0) ≈ 50 em GPU e ≈ 238,7 / (5,28 − 2,19) ≈ 77 num core de CPU. Com um autofocus mais barato, n* cai muito. Você vai medir isso.

**Q3. Quanto o autofocus pode ficar mais barato e mais robusto sem perder acurácia?**
H3: bastante. A faixa cega de 0,2–2,1 z₀ é exagerada para uma bancada com lâminas conhecidas, a imagem pode ser reduzida antes do autofocus (o LED já elimina o conteúdo acima de cerca de 70 ciclos/mm, enquanto o Nyquist é 299), e o ToG pode ser estabilizado contra ruído. Se um autofocus barato e robusto chegar perto do stack em custo e o superar em acurácia, a vantagem do stack encolhe e o paper deve dizer isso. Este experimento existe porque o próprio Discussion do paper admite que o critério de nitidez foi o elo fraco.

**Q4. Uma lâmina inclinada cria variação local de z que o autofocus global não resolve?**
H4: só com inclinações grandes. Como a rede tolera 300 µm de spread de profundidade, a inclinação só deve importar quando a variação de z no quadro chegar a cerca de ±0,5–1 mm. Com meia largura de quadro de 3,2 mm, isso é uma inclinação de cerca de 9° a 17°, que é implausível para uma lâmina apoiada no sensor. Esperamos um resultado negativo na faixa plausível (≤ 2°). O experimento serve para encontrar o limiar e descartar o argumento com dados. É o de menor prioridade.

**O que conta como "ganho de tempo legítimo"** (critério que vai para o paper): num cenário cuja plausibilidade física sabemos justificar, o focal stack tem F1 a até 0,02 do melhor fluxo convencional e front end mais barato que **o mais barato** dos fluxos convencionais que atingem esse F1, medido na mesma máquina, no mesmo run, em GPU e em CPU. Se o critério valer só em parte (por exemplo, só para n < n*), o paper diz exatamente a condição.

---

## 4. Mapa do código

```text
holo_openset/
  sim/physics.py      parâmetros da aquisição (dataclass Physics) e o modelo direto: propagação, intensidade, LED, câmera
  sim/scene.py        cenas (letras, poeira, defeitos da câmera) e sessões (z, feixe) — tudo com sementes
  sim/generate.py     escreve os conjuntos em data/; "like" regrava as mesmas cenas com outra física
  sim/variants.py     os conjuntos de robustez: nome -> sobrescritas de Physics
  reconstruct.py      flat field, backprop, autofocus, foco por objeto, twin removal, caches rec_<método>.npy
  model.py, train.py  camada de Fourier (real, complexa, prop, bank) e treino
  flows.py            os fluxos comparados e de onde cada um lê suas imagens
  evaluate.py         o protocolo estrito
  experiments/        robustness.py, full_frames.py, timing.py, e2e.py ...
  paths.py            onde se lê e escreve (variáveis HOLO_DATA, HOLO_MODELS, HOLO_RESULTS ...)
  cli.py              linha de comando: python -m holo_openset <comando>
docs/                 REPRODUCIBILITY.md, DATA.md, EQUIPMENT.md — leia os três
results/, expected/   resultados e tabelas do paper (NÃO escreva aqui)
```

---

## 5. Etapa 0: preparação e reprodução (obrigatória antes de qualquer mudança)

### 5.1 Ambiente

Siga a seção Installation do `README.md`: Python 3.11, CUDA 12, `environment.yml` e `requirements-lock.txt` (o ambiente exato do paper). Cada comando usa **um** dispositivo, `--device cpu` ou `--device cuda:N`. No servidor DGX compartilhado, confira com `nvidia-smi` qual GPU está livre e use só ela.

```bash
conda env create -n holo-openset -f environment.yml
conda activate holo-openset
pip install -r requirements-lock.txt
pytest                                       # ~20 s, CPU
python -m holo_openset reproduce check       # esperado: 11/11 files identical to expected/
```

### 5.2 Branch, pastas e registro

Trabalhe num branch próprio (`git checkout -b exp/distancia-autofocus`). Nunca faça commit de dados ou modelos (o `.gitignore` já exclui `data/`, `models/`, `logs/`, `output/`). **Todos os resultados novos vão para uma pasta separada**, para não tocar nos CSVs que geram as tabelas do paper:

```bash
export HOLO_RESULTS=$PWD/results_exp_distancia
```

Coloque essa linha no seu `~/.bashrc` do projeto ou no início de todo script. Mantenha um caderno de laboratório (`docs/exp_distancia/CADERNO.md`) com data, commit, comando exato, GPU usada, carga do servidor e o que você observou. Se um número sair estranho, a primeira pergunta será "qual comando gerou isso?".

### 5.3 Dados e modelos

```bash
python -m holo_openset reproduce download    # ~20 GB do Zenodo: modelos, conjunto base, quadros inteiros
python -m holo_openset reproduce verify-data # checksums
```

Os modelos de todos os fluxos da Seção 2.2 (inclusive `bank_jit`, `bank_wide`, `bank_w2`) e os localizadores YOLO das cinco repetições estão no registro do Zenodo. **Você não precisa treinar nada para os experimentos principais.**

### 5.4 Teste de sanidade: reproduzir uma linha do paper

Antes de mudar o código, reproduza a linha "distância entre sessões 5 %" da Tabela 10 para quatro fluxos. Isso valida o seu ambiente e ensina o caminho completo: simular, reconstruir, avaliar.

```bash
python -m holo_openset simulate variant session_5 --device cuda:0
python -m holo_openset reconstruct --set variants/session_5 --methods z0 af --device cuda:0
python -m holo_openset reconstruct --set realistic --methods z0 af --device cuda:0   # se os caches do base não existirem
python -m holo_openset experiment robustness --device cuda:0 --variants base session_5 --flows prop bank_jit rec_z0 rec_af
```

Critério: F1 de cada fluxo a até 0,01 dos valores da Tabela 10 (base: 0,96 para os quatro; `session_5`: 0,75, 0,84, 0,75, 0,96). Compare também com `results/robustness.csv` do repositório, linha a linha. Se não bater, pare e me procure. Não siga adiante com um pipeline que não reproduz o paper.

Rode também o `timing` em GPU e em CPU com as configurações do paper e anote a razão entre os seus tempos e os da Tabela 8. Máquinas diferentes dão tempos diferentes, mas as **razões entre estágios** devem ficar parecidas.

```bash
python -m holo_openset experiment timing --device cuda:0 --rep 1
python -m holo_openset experiment timing --device cpu --rep 1 --sizes 640x640     # o quadro inteiro em CPU leva horas: só no fim
```

**Checkpoint 0:** me mostre a reprodução da linha `session_5`, a razão dos tempos e o caderno. Só depois mexa no código.

---

## 6. Mudanças de código

### 6.1 Invariantes que não podem quebrar

Este é o ponto onde estagiários mais erram em simuladores com sementes, então leia com calma. Os conjuntos de robustez são as **mesmas cenas** do teste do base, regravadas com outra física. O `robustness.py` verifica isso com um `assert` sobre caixas e classes. As cenas são reproduzidas porque cada sorteio vem de um `random.Random(semente)` numa ordem fixa. Se você acrescentar um sorteio no meio dessa sequência, todas as cenas seguintes mudam e o pareamento com o base se perde. Por isso:

1. Todo parâmetro novo de `Physics` tem um valor padrão que **desliga** o efeito e deixa o conjunto base idêntico bit a bit.
2. Todo sorteio novo (z por quadro, azimute da inclinação) usa um `random.Random` **próprio**, com uma semente derivada que não colide com as existentes. Nunca use o `rng` da cena nem o da sessão.
3. Depois das mudanças: `pytest`, `reproduce check` (11/11) e regenerar `variants/session_5` com o código novo e comparar o `holograms.npy` com o da Etapa 0 (deve ser idêntico, ou dentro do arredondamento de GPU que o REPRODUCIBILITY.md descreve, 0,02 % dos pixels).
4. Caches e logs novos nunca sobrescrevem os existentes. Atenção: `build_caches` sempre escreve `autofocus.csv`. Se você rodar `reconstruct --methods afs` sem mudar isso, vai apagar o log de autofocus do conjunto base, que o `fidelity` usa. Faça os métodos novos escreverem `autofocus_<método>.csv`.

### 6.2 Distância por quadro (para E2)

Em `sim/physics.py`, acrescente ao `Physics`:

```python
frame_z_std: float = 0.0     # relativo; z de cada imagem ~ z_sessão (1 + N(0, frame_z_std)), independente por imagem
frame_z_walk: float = 0.0    # relativo; passo de um passeio aleatório de z dentro da sessão (drift lento)
```

Em `sim/generate.py`, no laço por imagem de `generate()` e de `full_frames()`, **depois** de construir a cena, copie a sessão e altere só o z dessa imagem:

```python
ses = dict(sessions[s])
if phys.frame_z_std > 0:
    r = random.Random(seed * 1_000_000 + i + 800_000_000)      # semente própria: não toca na cena
    ses['z'] = ses['z'] * (1 + phys.frame_z_std * r.gauss(0.0, 1.0))
if phys.frame_z_walk > 0:
    ses['z'] = ses['z'] * (1 + walk[s][i % per_session])        # walk pré-calculado por sessão com random.Random(seed*1000 + s + 600_000)
```

O `metadata.csv` e o `annotations.csv` devem gravar o z **da imagem** (o `_rows` já soma `ses['z'] + depth`, então basta passar a `ses` modificada). O `Holograms.true_z` lê o z do `metadata.csv`, então o erro do autofocus por imagem sai certo automaticamente. O blank frame continua um por sessão, como na bancada: ele é gravado antes da amostra e só depende de z pelo borrão do pinhole, que é desprezível.

Em `sim/variants.py`, acrescente:

```python
'frame_2': ('distance per frame (%)', 2, dict(frame_z_std=0.02)),
'frame_5': ('distance per frame (%)', 5, dict(frame_z_std=0.05)),
'walk_05': ('distance drift per frame (%)', 0.5, dict(frame_z_walk=0.005)),   # após 100 quadros, desvio ~5 %
```

Note que `frame_5` tem a mesma distribuição marginal de z que `session_5`, mas com 800 sorteios em vez de 8 (o teste tem 8 sessões). Isso tem um efeito colateral útil: os números de `session_5` da Tabela 10 se apoiam em apenas 8 valores de z, e `frame_5` dá uma estimativa muito mais estável do comportamento de `rec_z0` e dos stacks sob drift. Reporte as duas e comente a diferença.

### 6.3 Inclinação da lâmina (para E4)

A simulação já propaga cada objeto pela sua própria profundidade (superposição de primeira ordem, `physics.scattered_field`). Uma lâmina inclinada é, nessa aproximação, um termo de profundidade proporcional à posição. Acrescente ao `Physics` `tilt_deg: float = 0.0` e, em `generate.py`, depois da cena e antes de gravar:

```python
def apply_tilt(sc, phys, seed_s):
    if phys.tilt_deg == 0:
        return
    phi = random.Random(seed_s + 650_000).uniform(0, 2 * math.pi)      # azimute por sessão, semente própria
    t = math.tan(math.radians(phys.tilt_deg))
    H, W = phys.canvas
    for o in sc['objects'] + sc['dust']:                                # letras, letras de fora e poeira das lâminas
        h, w = o['mask'].shape
        r = ((o['x'] + w / 2 - W / 2) * math.cos(phi) + (o['y'] + h / 2 - H / 2) * math.sin(phi)) * PIXEL
        o['depth'] += t * r
    letters = [o for o in sc['objects'] if o['kind'] == 'letter']
    for row, o in zip(sc['rows'], letters):                             # a anotação guarda a profundidade nova
        row['depth'] = o['depth']
```

A poeira do sensor não inclina, porque está no sensor. O termo de inclinação é somado depois do sorteio do spread de profundidade e não é cortado por `depth_max`. Confira que a ordem de `sc['rows']` e das letras em `sc['objects']` é a mesma (no `make_scene` atual, é). A inclinação só faz sentido nos quadros inteiros, porque numa janela de 1,07 mm a variação de z é seis vezes menor.

Hoje o `simulate full` escreve sempre em `data/full_frames`, e `experiment full_frames` e `timing` sempre leem de lá. **Acrescente um argumento `--name`** (saída em `data/full_frames_<name>`) e um `--frames-set` nos dois experimentos. Sem isso você vai sobrescrever os quadros do paper.

### 6.4 Novos baselines de autofocus (para E1, E2 e E3)

Em `reconstruct.py`, generalize `autofocus(a, z0)` para aceitar a faixa e o número de candidatos (`lo`, `hi`, `n_coarse`, `n_fine`), um fator de redução `bin` e um critério. Depois crie estes métodos de cache:

| método | o que faz | reconstruções por quadro |
|---|---|---|
| `afs` | autofocus cego no primeiro quadro de cada sessão (ou mediana dos k primeiros; k ∈ {1, 3} escolhido na validação), z reutilizado no resto da sessão | 114·k / n + 1 |
| `afM` | refoco a cada M quadros dentro da sessão (M escolhido na validação, para `walk_05`) | 114 / M + 1 |
| `afn` | autofocus de faixa estreita: [0,85, 1,15] z₀, por exemplo 15 + 11 candidatos | ~26 + 1 |
| `afb` | autofocus sobre a amplitude reduzida 2× ou 4× por média, z aplicado na imagem inteira | 114 em imagem 4–16× menor + 1 |
| `afr` | autofocus com critério robusto: ToG calculado só onde o blank frame é > 20 % do máximo, sobre o campo suavizado (gaussiana σ = 1–2 px) | 114 + 1 |

Três cuidados de implementação. Primeiro, `freq_sq` usa a constante global `PIXEL`. Na versão reduzida o pixel passa a ser `bin × PIXEL`, então a função precisa receber o pixel como argumento, ou o z encontrado sai errado por um fator de bin². Teste isso com um holograma de z conhecido antes de usar. Segundo, `afs` e `afM` dependem da ordem das imagens dentro da sessão. Os ids são contíguos por sessão (`i // per_session`), então "primeiro quadro" é o de menor id da sessão naquele split. Terceiro, combinações são permitidas (por exemplo `afn` + `afb` + `afr`), mas cada uma é um fluxo, e quanto mais fluxos você testar, maior a chance de achar um por sorte. Escolha as combinações na validação e leve ao teste só as que forem decididas antes.

Em `flows.py`, cada método novo vira um fluxo que **reutiliza o modelo do `rec_af`**, porque a rede foi treinada com reconstruções em foco e só a forma de achar z muda:

```python
'rec_afs': dict(mode='none', fourier='learned', rec='afs', weights='rec_af'),
```

Para isso, `experiments/common.model()` e `paths.weights()` precisam usar `FLOWS[flow].get('weights', flow)`. Numa repetição (r1), treine também um modelo próprio para o melhor método novo (`python -m holo_openset train --flow rec_afn --rep 1 --device cuda:0`) e confira que o F1 não muda mais que 0,01. Se mudar, reporte e use modelos próprios para todos.

Para medir o tempo, inclua esses métodos e os stacks `bank_wide` e `bank_w2` no dicionário `stages` de `experiments/timing.py`. Hoje ele só tem `prop`, `bank`, `bank_jit`, `bank_w1` e `bank_w3`.

### 6.5 Validação também para as variantes

O `simulate variant` grava só o split de teste. Para escolher k, M, a faixa estreita e os parâmetros do critério robusto **sem olhar o teste**, você precisa das mesmas variantes no split de validação. Acrescente `--split` ao comando e grave em `data/variants_val/<nome>`. A escolha usa o erro de distância do autofocus (que não precisa de rede nem de labels de classe) e, se necessário, o F1 com as classes vistas na validação.

**Checkpoint 1:** me mostre o diff, os testes de invariância (seção 6.1, item 3) passando, e um holograma de `frame_5` e um de `tilt` lado a lado com o base.

---

## 7. Os experimentos

Rode tudo primeiro numa repetição (r1) como piloto. Só quando o piloto fizer sentido, rode as cinco.

### E1. O baseline honesto: autofocus por sessão (prioridade 1)

**Objetivo:** responder a Q1, ou seja, matar ou confirmar o espantalho da Tabela 9.

**Conjuntos:** base, `session_2`, `session_5`, `fullwell_500`, `beam_narrow` (janelas), e os 40 quadros inteiros do paper.

**Fluxos:** `rec_z0`, `rec_af`, `rec_afs`, `prop`, `bank_jit`, `bank_wide`, `bank_w2`.

```bash
for s in realistic variants/session_2 variants/session_5 variants/fullwell_500 variants/beam_narrow; do
  python -m holo_openset reconstruct --set $s --methods afs --device cuda:0
done
python -m holo_openset experiment robustness --device cuda:0 \
  --variants base session_2 session_5 fullwell_500 beam_narrow \
  --flows rec_z0 rec_af rec_afs prop bank_jit bank_wide bank_w2
```

**O que reportar:** F1, rejeição e AUROC por fluxo e conjunto (média ± dp de 5 repetições). Erro de distância do `afs` contra o do `af`. Custo por quadro amortizado, que é T_af × k / n + T_backprop, com n = 100 e os tempos **medidos** na Etapa 0. Diga explicitamente que o custo amortizado é uma soma de tempos medidos, não uma medida de ponta a ponta.

**Resultado esperado:** `rec_afs` ≈ `rec_af` em todos os conjuntos com z por sessão, inclusive `session_5`, a um custo próximo de `rec_z0`. Sob `fullwell_500` e `beam_narrow`, `rec_afs` herda a fragilidade do autofocus, só que agora o erro é de uma sessão inteira: um autofocus ruim no primeiro quadro estraga 100 imagens. Olhe a variância entre sessões e reporte-a.

### E2. Distância que muda a cada quadro (prioridade 1)

**Objetivo:** responder a Q2. Este é o cenário em que o ganho de tempo pode ser legítimo.

**Plausibilidade (escreva isto no relatório):** z muda por quadro quando cada quadro é uma montagem nova, como numa triagem de muitas lâminas, com uma imagem por amostra num aparelho point-of-care. Também muda quando a plataforma desliza a amostra, ou quando há drift térmico ou mecânico lento (`walk_05`). O caso independente por quadro (`frame_2`, `frame_5`) é o limite em que cada montagem rende um quadro só (n = 1). O passeio aleatório é o caso intermediário, em que refocar a cada M quadros é a resposta convencional sensata.

**Conjuntos:** `frame_2`, `frame_5`, `walk_05` (janelas, split de teste; e as versões de validação para escolher M e k). Depois, 40 quadros inteiros com `frame_z_std=0.05` (`simulate full --name frame5 --set-physics frame_z_std=0.05`, depois de implementar o `--name`).

**Fluxos:** `rec_z0`, `rec_af`, `rec_afs`, `rec_afM` (só no `walk_05`), o melhor autofocus barato de E3, `prop`, `bank_jit`, `bank_wide`, `bank_w2`.

```bash
python -m holo_openset simulate variant frame_2 frame_5 walk_05 --device cuda:0
for v in frame_2 frame_5 walk_05; do
  python -m holo_openset reconstruct --set variants/$v --methods z0 af afs afM --device cuda:0
done
python -m holo_openset experiment robustness --device cuda:0 --variants base frame_2 frame_5 walk_05 \
  --flows rec_z0 rec_af rec_afs rec_afM prop bank_jit bank_wide bank_w2
python -m holo_openset experiment full_frames --device cuda:0 --frames-set full_frames_frame5 \
  --flows rec_z0 rec_af rec_afs bank_jit bank_wide bank_w2
```

**O que reportar:**

1. A tabela F1 × fluxo × conjunto, como na Tabela 10.
2. O erro de distância de cada autofocus.
3. A curva de custo por quadro em função de n (quadros por montagem), de n = 1 a n = 100, para `rec_afs` com o autofocus cego e com o melhor autofocus barato, contra as retas horizontais dos stacks. O ponto de cruzamento é n*. Faça a curva em GPU e em CPU (um core), com os tempos medidos no quadro inteiro.
4. O gráfico custo × F1 no quadro inteiro, como a Fig. 12c, com e sem detector.

**Resultado esperado:** em `frame_5`, `rec_afs` cai para perto de `rec_z0` (≈ 0,75), `rec_af` mantém ≈ 0,96, e os stacks largos ficam em ≈ 0,94. A vantagem de tempo do stack existe para n < n*. O número que importa para o paper é n* com o melhor autofocus barato, não com o cego.

### E3. Um autofocus mais barato e mais robusto (prioridade 2, mas comece cedo)

**Objetivo:** responder a Q3, e garantir que E2 compare o stack com o melhor autofocus razoável.

Este experimento é barato porque **a primeira metade não precisa de rede**: o erro de distância sai direto do `autofocus_<método>.csv`. Faça assim:

1. **Na validação** (base e variantes de validação de `frame_5`, `fullwell_500` e `beam_narrow`), varra a faixa de busca, o número de candidatos, o fator de redução (1, 2, 4) e os parâmetros do critério robusto. Meça o erro de distância (mediana e p90) e o tempo. Escolha **no máximo três** configurações: a mais barata com erro mediano ≤ 50 µm (o erro do autofocus atual, Seção 7.5 do paper), a mais robusta sob ruído, e a combinação das duas, se ela existir.
2. **Congele as três** e escreva-as no caderno com a data.
3. **No teste**, rode as três como fluxos (`rec_afn`, `rec_afb`, `rec_afr` ou combinações), com o modelo de `rec_af`, em base, `session_5`, `frame_5`, `fullwell_500` e `beam_narrow`, e meça o tempo no quadro inteiro.

**Justificativa física do `afb`, para o relatório:** o LED de 10 nm e o pinhole de 100 µm deixam pouco contraste acima de cerca de 70 ciclos/mm (Fig. 2b do paper). Reduzir a imagem 4× leva o Nyquist de 299 para cerca de 75 ciclos/mm, logo quase nada do que a bancada grava é perdido. Confira isso medindo o erro de distância, não confie no argumento.

**O que muda no paper:** se um autofocus barato chegar a, por exemplo, 20 ms por quadro em GPU sem perder F1, a vantagem do stack sobre ele cai de cerca de 35× para cerca de 6× no front end, e n* cai para perto de 10. Se o critério robusto recuperar o F1 sob `fullwell_500` e `beam_narrow`, a frase "o stack não é enganado pelo ruído como o autofocus" precisa virar "como o autofocus com o critério de Tamura". Qualquer um desses resultados é importante e vai para o paper.

### E4. Lâmina inclinada (prioridade 3)

**Objetivo:** responder a Q4. Como explicado na Seção 3, esperamos um resultado negativo na faixa plausível. O objetivo é encontrar o limiar e documentá-lo.

**Conjuntos:** 40 quadros inteiros para cada θ ∈ {0°, 1°, 2°, 5°, 10°, 15°}. A variação de z na borda do quadro é ±3,2 mm × tan θ: cerca de ±56 µm a 1°, ±112 µm a 2°, ±280 µm a 5°, ±560 µm a 10° e ±860 µm a 15°.

**Fluxos:** `rec_z0`, `rec_af` (autofocus global do quadro), `rec_edf` com faixa larga (foco por objeto em ±6 % com 49 passos, que é a resposta convencional para z local e já existe no código, só com faixa maior), `bank_jit`, `bank_wide`, `bank_w2`.

**Plausibilidade:** pergunte ao prof. Sobieranski qual a inclinação plausível da montagem na bancada dele e registre a resposta. Se ele não souber, use ≤ 2° como faixa plausível e diga no relatório que é suposição.

**O que reportar:** F1 fim a fim × θ para cada fluxo e o custo de cada um. Se nada degradar até 2°, escreva isso em uma frase e não insista. Se algo degradar só em θ ≥ 10°, reporte como limite da simulação, não como vantagem do método.

### E5. Medição final de tempo (prioridade 1, no fim)

Depois que os fluxos de E1–E3 estiverem fixos, rode **numa única sessão de medição**, na mesma máquina e na mesma GPU, o `timing` (janela e quadro inteiro, GPU e um core de CPU) e o `full_frames` (fim a fim por estágio) para todos os fluxos que vão para o paper. As razões entre estágios só são comparáveis dentro de um mesmo run (Seção 6.4 do paper: o servidor estava com carga de cerca de 230 em 224 cores, e a carga muda os tempos em até 1,4×).

---

## 8. Regras de medição de tempo

1. **GPU:** use uma GPU que ninguém esteja usando (confira com `nvidia-smi` antes e depois e anote). O `timing.py` sincroniza o dispositivo antes e depois de cada chamada e reporta mínimo e mediana de 20 repetições. Numa GPU saturada, toda chamada custa os mesmos poucos milissegundos, qualquer que seja o tamanho da imagem (REPRODUCIBILITY.md). Se isso acontecer, o run não vale.
2. **CPU:** um core, `--threads 1`, tempo de CPU do processo (`process_time`), mediana. Anote a carga do servidor (`uptime`) no começo e no fim.
3. **Warm-up:** o `measure()` já descarta a primeira chamada (cria os planos de FFT). Não remova isso.
4. **O que entra no tempo de cada fluxo:** ler o quadro e o blank frame, normalizar, front end (reconstrução ou camada), canais, embedding de todas as caixas e busca na galeria. O detector aparece em coluna separada e no total. Para `afs` e `afM`, o custo do autofocus é dividido pelos quadros que o reutilizam, e isso é dito na legenda.
5. **Nada é extrapolado:** se um estágio não foi medido no quadro inteiro, ele não aparece na tabela do quadro inteiro.

---

## 9. Estatística e apresentação

1. Média ± desvio padrão sobre as cinco repetições r1–r5, como no paper. As comparações entre fluxos são pareadas (mesmas cenas, mesma repetição). Para dizer que dois fluxos diferem, mostre a diferença por repetição e quantas das cinco têm o mesmo sinal.
2. Negrito só pela regra do paper: mais de 0,05 abaixo do base.
3. Tabelas no formato das Tabelas 10 e 11, e figuras no estilo de `holo_openset/paper/style.py` (as Figs. 12 e 16 são o modelo). As figuras saem de scripts versionados, nunca de planilha.
4. Os números que forem para o texto saem como macros LaTeX num arquivo próprio (`results_exp_distancia/numbers_distancia.tex`), no mesmo estilo de `expected/numbers.tex`, para eu integrar ao paper sem digitar número nenhum.

---

## 10. O que não fazer

1. Não escreva em `results/` nem em `expected/` e não sobrescreva `data/full_frames`, `data/realistic/autofocus.csv` ou qualquer cache existente.
2. Não escolha k, M, faixa, fator de redução, critério ou largura do stack olhando o teste. Se você olhou o teste por engano, anote no caderno e me avise. Isso acontece, e esconder é que é grave.
3. Não retreine os modelos do base para "ajudar" um fluxo, a não ser na checagem de E3 descrita na Seção 6.4, e então para todos os fluxos comparados.
4. Não compare tempos de runs diferentes nem de máquinas diferentes na mesma tabela.
5. Não edite o texto do paper (`main.tex` e seções). Escreva os resultados no relatório e nas macros. A integração e o enquadramento são meus.
6. Não reporte só o front end. Toda tabela de tempo tem a coluna fim a fim.
7. Não descarte uma repetição ou uma sessão porque o resultado "ficou estranho". Investigue, reporte, e me pergunte.

---

## 11. Entregáveis

1. Branch `exp/distancia-autofocus` com o código, testes passando e `reproduce check` em 11/11.
2. `docs/exp_distancia/CADERNO.md` com todos os comandos e observações.
3. `results_exp_distancia/` com os CSVs (`robustness.csv`, `full_frames*.csv`, `timing_*.csv`, `autofocus_*.csv` copiados) e `numbers_distancia.tex`.
4. Um relatório curto (`docs/exp_distancia/RELATORIO.md`, no máximo umas 6 páginas) com: a resposta a Q1–Q4 em uma frase cada, as tabelas e figuras, o n* em GPU e CPU com o melhor autofocus, a plausibilidade física de cada cenário, e uma seção "o que isso muda no paper" com sugestões de frase. Diga também o que deu errado e o que você não conseguiu testar.

### Ordem e checkpoints

| etapa | conteúdo | checkpoint |
|---|---|---|
| 0 | ambiente, download, reprodução da linha `session_5`, timing de referência | 0: reprodução bate com o paper |
| 1 | código (6.2–6.5) e testes de invariância | 1: diff revisado, base idêntico |
| 2 | E1 completo; E3 parte 1 (validação, sem rede) | 2: H1 respondida; configurações de E3 congeladas |
| 3 | E2 (janelas e quadros); E3 parte 2 (teste) | 3: n* e gráfico custo × F1 |
| 4 | E4; E5 (medição final única); relatório | 4: relatório e macros |

Em cada checkpoint, traga o caderno e os números brutos, não só os gráficos.

---

## 12. Checklist antes de entregar

- [ ] `pytest` e `reproduce check` passam no commit final.
- [ ] O conjunto base gerado com o código novo é idêntico ao do Zenodo (`verify-data`).
- [ ] Todos os resultados novos estão em `results_exp_distancia/`, e `results/` está intocado (`git status`).
- [ ] Toda escolha de hiperparâmetro tem data no caderno anterior ao primeiro run no teste.
- [ ] Toda tabela de tempo tem front end e fim a fim, GPU e CPU, de um único run de medição.
- [ ] O custo amortizado de `afs` e `afM` está identificado como soma de tempos medidos.
- [ ] Cada cenário tem um parágrafo de plausibilidade física.
- [ ] O relatório diz o que **não** foi confirmado.
