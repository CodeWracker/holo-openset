# Caderno da curva de densidade e dos testes de distância a 1,0 mm

Etapa pedida pelo orientador em 2026-11-15 (`PROTOCOLO_CURVA.md`, na íntegra). Este arquivo tem só as entradas do
responsável (pré-registros Q0, Q1, … e conferências). Os executores escrevem nos cadernos próprios:
`CADERNO_CURVA_DENSIDADE.md` e `CADERNO_CURVA_DISTANCIA.md`. O piloto que veio antes está em
`CADERNO_PILOTO_1MM.md`.

## 2026-11-15, 08:11 — Q0: pré-registro dos experimentos a, b e d (responsável)

Escrito depois da instrução do orientador e antes de rodar qualquer coisa desta etapa. Receita de treino
(`--no-aux`; `prop` com `--alpha-extend 12`), galeria, limiar tirado da validação, métricas (F1 open-set e
rejeição das não vistas, split de teste), janelas com as caixas anotadas e fluxos (`raw`, `prop`, `rec_z0`)
como no piloto. Nenhuma escolha é feita no teste. Cada teste é lido uma vez. O que sair é reportado, e nenhuma
repetição é descartada. Nada é rodado de novo com outra configuração depois de lido o teste; erro de código (não
número decepcionante) para tudo e é reportado antes de qualquer nova rodada.

### a. Cinco repetições no conjunto denso do piloto (`bench_1mm_dense`, profundidade de 2,6 µm)

- r2–r5 exatamente como r1 (já lida: crops 0,796 / 0,080; camada 0,960 / 0,899; reconstrução 0,968 / 0,952).
- Reporto por repetição, a média, o mínimo e o máximo: os três fluxos, camada − crops, reconstrução − camada.
- Os limiares do critério do P0 (camada − crops ≥ 0,10 em F1 **e** ≥ 0,30 em rejeição, em pelo menos 4 de 5
  repetições) são aplicados a este conjunto de forma descritiva: quantas repetições cumprem cada condição.

### b. Curva de densidade

- **Família:** conjuntos a 1,0 mm com as mesmas letras anotadas do piloto (mesmas sementes; 40 309 letras, 8 por
  janela) e a lei de profundidade padrão desta etapa (item c da instrução; **a lei exata fica para a entrada Q1,
  antes de gravar**, porque depende de uma pergunta ao orientador: ver "O que ainda não está decidido"). A única
  diferença entre os níveis é o número de letras de enchimento, não anotadas (`fill_mean`, entrada K1 do caderno do
  piloto). Gravador (s = 4), física e receita do piloto.
- **Níveis** (total de letras por janela de 640 × 640 = 1,142 mm²; objetos por mm²): 8 (7; sem enchimento), 15 (13),
  69 (60), 154 (135), **343 (300; ≈ 23,5 % de área coberta pela soma das caixas de tinta)**. O último é o nível
  novo "perto de 300 objetos por mm² (~25 % da área)".
- **Densidade reportada:** a obtida (letras na janela contadas no `metadata.csv`), não o alvo. Se mais de 5 % das
  letras de enchimento de um nível não couberem (`n_fill_skipped`), declaro e o nível entra com a densidade obtida.
- **Ordem:** r1 em todos os níveis; depois r2–r5 nos níveis onde as curvas se separam (regra abaixo).
- **"Caiu" (fixado agora).** Um fluxo *caiu em F1* num nível se o seu F1 ali ficar pelo menos **0,10** abaixo do
  F1 do mesmo fluxo no nível esparso (8 letras por janela) da mesma família e da mesma repetição. *Caiu em
  rejeição* se a rejeição das não vistas ficar pelo menos **0,30** abaixo, na mesma comparação. São os dois
  limiares do critério do P0. Com r1 só, a leitura é provisória. Com cinco repetições, o fluxo caiu num nível se
  a condição valer em pelo menos 4 de 5. "Onde a própria camada cai" é o primeiro nível (em densidade crescente)
  em que a camada caiu em F1 ou em rejeição; reporto as duas separadamente.
- **"As curvas se separam" (fixado agora).** Um nível recebe r2–r5 se, em r1, valer pelo menos uma: (i) camada −
  crops ≥ 0,10 em F1; (ii) camada − crops ≥ 0,30 em rejeição; (iii) algum fluxo caiu (em F1 ou em rejeição) nesse
  nível. O nível esparso recebe r2–r5 de qualquer jeito, porque é a referência do "caiu".
- **Se a camada não cair no nível mais denso**, reporto "não caiu até a densidade obtida". Nenhum nível novo é
  gravado sem perguntar ao orientador.
- Em cada nível com cinco repetições reporto também os limiares do P0 (camada − crops ≥ 0,10 e ≥ 0,30 em pelo
  menos 4 de 5), de forma descritiva.

### Diâmetro efetivo do holograma e razão de sobreposição (eixo da figura)

- **Fórmula** (Seo et al. 2009, "Discussions"): razão de sobreposição = 1 − exp(−π D² σ), com σ a densidade em área
  (objetos por mm²; no artigo, altura do canal × concentração) e D o diâmetro efetivo do holograma. Seo dá
  D ≈ 50 µm "(RMS)" para as células deles e não define a medida.
- **Medida:** 260 letras isoladas (10 de cada classe), com tamanho, rotação e material sorteados pelas leis do
  conjunto (semente fixa), no plano da amostra (profundidade 0), z = 1,0 mm, gravadas pelo mesmo caminho (s = 4),
  sem ruído, sem poeira, sem vizinhas. Padrão p = I/B − 1; energia e = p². Nenhum dado de teste entra.
- **Três números por letra**, todos em torno do centroide da energia:
  1. *D_rms* = 2√2 · sqrt(Σ e r² / Σ e) (segundo momento, convenção D4σ: devolve o diâmetro de um disco uniforme),
     integrado num disco de raio R; reporto R = 96, 128, 192 e 256 px.
  2. *D_vis* = 2 × o raio a partir do qual a média azimutal de sqrt(e) fica abaixo do ruído do conjunto (2,07 % do
     nível médio: 2,1 níveis de cinza em 101,5) e não volta a passar dele.
  3. *D_86* = diâmetro do disco que contém 86,5 % da energia dentro de R = 256 px.
- **Qual vai no eixo (regra fixada agora):** D_rms com R = 192 px, se D_rms(256) diferir dele em até 5 %
  (convergiu). Se não convergir, D_vis. Os três entram na tabela.
- **D do conjunto:** D_ef² = média, sobre pares de letras da amostra, de ((D_i + D_j)/2)² (dois hologramas se
  sobrepõem quando a distância entre os centros é menor que a soma dos raios).
- **O eixo não muda nenhuma conclusão:** com D fixo, a razão de sobreposição é função crescente da densidade; trocar
  a definição de D só renomeia o eixo. Por isso a figura leva também a densidade (objetos por mm²) num segundo eixo,
  e "caiu" é definido por nível, não pelo valor da sobreposição. A escala do eixo é escolhida depois de medir D e
  antes de ler qualquer teste novo.
- A comparação com os limiares de Seo (10 % e 37 %) é só descritiva: as medidas de D podem não ser a mesma.

### d. Distância: 0,9 e 1,1 mm (0,7 mm fica como teste de estresse)

- **Conjuntos de teste:** como o de 0,7 mm do piloto (`bench_1mm_robust/z07` e `z07_val`: as cenas de teste do
  conjunto e 32 hologramas de validação, regravados na outra distância), agora a 0,9 e a 1,1 mm.
- **Linhas, em cada distância:** crops, camada e reconstrução como estão (modelos, galeria e limiar de 1,0 mm, sem
  retreinar); camada e reconstrução com a distância recalibrada sem rótulo nos 32 hologramas de validação. A
  recalibração **por razão** (mantém o deslocamento que o treino deu ao α) é a variante principal, como foi
  declarado antes de rodar a 0,7 mm; a literal entra ao lado.
- **Modelos, em duas rodadas:** (d1) os cinco modelos do piloto (`bench_1mm`, amostra plana), já, para ficar na
  mesma tabela das linhas de 0,7 mm que existem; (d2) os cinco modelos da família padrão (item c), nível esparso,
  quando existirem, com os conjuntos de teste a 0,7, 0,9 e 1,1 mm gravados com a lei de profundidade padrão. O texto
  do paper usa (d2); (d1) fica como resultado do piloto.
- **Sem critério de passa ou não passa.** Reporto, por distância e por repetição: a perda sem recalibrar
  (como está − 1,0 mm), o que a recalibração recupera, a distância que a recalibração achou, e reconstrução
  recalibrada − camada recalibrada por razão (a 0,7 mm, com os modelos do piloto: 0,964 − 0,914 = 0,05 de F1).

### O que ainda não está decidido (pergunta ao orientador, antes de gravar a família padrão)

O "50 µm" do treino do piloto (`bench_1mm_depth50`) é o padrão do simulador: a profundidade de cada objeto é
sorteada de uma normal com desvio de 50 µm, cortada em ±150 µm (faixa total de 300 µm). O artigo de 2015 diz
"double-sided adhesive film (DSA, 50 µm for microchannel height)": 50 µm é a altura total do canal. As duas leis
não são a mesma, e a escolha muda todas as gravações da curva. A resposta entra na entrada Q1, antes de gravar.
O item a, a medida do diâmetro e a rodada (d1) não dependem dela.

## 2026-11-15, 08:51 — Q1: a lei de profundidade padrão, o eixo da figura e o que roda na fase 2 (responsável)

Escrito antes de gravar qualquer conjunto da curva e antes de ler qualquer teste da família padrão. Já lidos nesta
etapa (fase 1, tudo pré-registrado no Q0): as cinco repetições do `bench_1mm_dense`, a rodada d1 da distância e a
medida do diâmetro (que não usa teste).

### A lei de profundidade (resposta do orientador)

Pergunta feita pelo diálogo às ≈ 08:25, com as duas opções do fim do Q0. Resposta dele: **"Uniforme nos 50 µm
(Recomendado)"**. Fica assim:

- **Lei padrão da família de 1 mm:** a profundidade de cada objeto é uniforme na altura do canal, ±25 µm em torno
  da distância da sessão (desvio de 14,4 µm). Fonte: Sobieranski et al. 2015, materiais e métodos, "double-sided
  adhesive film (DSA, 50 µm for microchannel height)". A distância da sessão passa a ser a do meio do canal
  (suposição nossa).
- **Implementação:** o mesmo único sorteio normal g por objeto que hoje vira `depth_std · g` (cortado) passa a
  virar 25 µm · erf(g/√2), que é uniforme em ±25 µm. O fluxo de sorteios não muda: as cenas ficam as mesmas e as
  letras ficam pareadas uma a uma com as do piloto. Vale para as letras anotadas, as de fora da janela e as de
  enchimento. A poeira continua nos planos fixos dos vidros. Desligada (padrão), nada muda.
- **O que vira o conjunto já treinado** (`bench_1mm_depth50`: normal com desvio de 50 µm, cortada em ±150 µm):
  teste de estresse, com esse nome. Não é mais "o padrão".
- **A perda do treino com amostra plana é medida de novo nesta lei** (linhas abaixo). O 0,2 de F1 do piloto foi
  medido na lei larga.

### A família padrão e a ordem

- Conjuntos `curve_u50_L008`, `_L015`, `_L069`, `_L154`, `_L343` (letras por janela), todos com a lei acima,
  as mesmas 40 309 letras anotadas, gravador, física e receita do piloto. O nível 8 é gravado de novo (é o
  `bench_1mm` com a lei nova).
- O nível 8 é gravado primeiro e recebe logo r1–r5 (pelo Q0 ele recebe r2–r5 de qualquer jeito), para liberar a
  rodada d2 da distância. Depois r1 nos outros quatro níveis, a tabela de r1, e r2–r5 nos níveis que a regra do Q0
  indicar. Nada do Q0 muda ("caiu", "se separam", densidade obtida, nenhum nível novo sem perguntar).

### O eixo da figura (fixado agora, depois de medir D e antes de ler teste da família)

- Medida (fase 1, `hologram_diameter_summary.json`): D_rms convergiu (R = 192 e 256 px diferem em 0,17 %), então,
  pela regra do Q0, **D = D_rms(192) = 111,8 µm** (D_86 = 114,9 µm; D_vis = 159,3 µm). É 3,8 vezes o lado médio da
  letra.
- Com esse D a razão de sobreposição é 0,24 / 0,40 / 0,905 / 0,995 / 1,000 nos cinco níveis (7 / 13 / 60 / 135 /
  300 por mm²). Em escala linear os dois níveis mais densos caem no mesmo ponto.
- **Eixo x:** a razão de sobreposição em escala log–log complementar, isto é, o número médio de vizinhas
  sobrepostas (π D² σ, o expoente da fórmula de Seo) em escala logarítmica. As marcas mostram a razão de
  sobreposição de cada nível. Um segundo eixo, em cima, mostra a densidade (objetos por mm²). Painéis: F1 e
  rejeição das não vistas; curvas de crops, camada e reconstrução; r1 em todos os níveis e média com mínimo e
  máximo onde houver cinco repetições.
- **Observação sem teste novo:** pela medida, já no nível esparso 24 % dos hologramas se sobrepõem. O limiar de
  10 % de Seo fica abaixo do nosso nível mais esparso. Isso é descritivo: a medida de D de Seo não é definida no
  artigo.

### Os conjuntos que já existem no mesmo eixo (acréscimo meu, descritivo)

O escritor da seção da simulação apontou que o conjunto de letras pequenas a 2 mm tem crops a 0,793 / 0,153 com uma
densidade relativa só ≈ 2,6 vezes a do esparso. A densidade em objetos por mm² não compara geometrias diferentes; a
razão de sobreposição compara, porque D cresce com a distância. Por isso meço D com o mesmo script e a mesma
definição (D_rms em R = 192 px, ou o R equivalente em relação ao tamanho do padrão, com a conferência de
convergência) para a geometria do CBMS 2024 (19,25 mm) e para o conjunto de letras pequenas a 2 mm, cada um pelo seu
próprio caminho de gravação, e ponho esses conjuntos no eixo com os resultados que já existem. Não é teste novo e
não entra em nenhum critério. **Previsão registrada antes de medir e antes de ler a curva:** se a sobreposição é a
variável certa, conjuntos com sobreposição parecida têm crops parecidos, qualquer que seja a distância. Se não
tiverem, reporto assim.

### d2 e as linhas de profundidade (com os cinco modelos do nível 8 da família padrão)

- **Distância (d2):** teste e 32 hologramas de validação do nível 8 regravados a 0,7 (estresse), 0,9 e 1,1 mm com a
  lei padrão; linhas como no d1 (como está; recalibrado literal; recalibrado por razão, a principal).
- **Profundidade, sem critério:** (i) os cinco modelos do piloto (amostra plana) testados no teste do nível 8 da
  família padrão; (ii) os cinco modelos da família padrão testados no teste plano do piloto; (iii) os cinco modelos
  da família padrão testados no teste da lei larga (o estresse). Reporto ao lado das linhas que já existem.

### Correção a uma frase minha do P4 do caderno do piloto

Escrevi que Isikman et al. 2012 contam "com reconstrução" até ≈ 0,4 milhão de células por µL. A frase do artigo não
diz em que domínio a contagem foi feita (a legenda da Fig. 5a mostra os dois). A fonte primária da contagem com
reconstrução e hologramas sobrepostos é Seo et al. 2010 (Anal. Chem.), lida pelo escritor do Related Work.

## 2026-11-15, 13:37 — Q2: pré-registro do controle das letras pequenas a 2 mm e do banco focal sob mudança de distância (responsável)

Pedidos do orientador de ≈ 13:30 e ≈ 13:34 (`PROTOCOLO_CURVA.md`, na íntegra). Escrito antes de qualquer gravação,
treino ou leitura de teste destes dois itens. Valem as regras de sempre: pastas da etapa (`HOLO_RESULTS`,
`HOLO_MODELS`), escolhas só na validação, cada teste lido uma vez por modelo, nada em `results/`.

### S. Controle da amostragem no conjunto de letras pequenas a 2 mm (r1)

Pergunta: o conjunto `small_near` foi gravado na amostragem nativa do sensor, e os de 1 mm pelo caminho
sobreamostrado. Isso explica por que os crops dele se comportam como num nível denso (0,793 / 0,153, cinco
repetições) com sobreposição de só 0,42?

- **Referência igual com igual:** o `small_near` como está em disco, treinado agora em r1 nas pastas da etapa, com a
  receita que o pacote usa para esse conjunto (`--no-aux`), nos três fluxos (`raw`, `prop`, `rec_z0`). Os números
  do paper ficam ao lado, só para referência.
- **Controle:** conjunto novo `small_near_newrec`, com as leis do `small_near` (tamanhos, número de letras por
  janela, borda e espaçamento, 2,0 mm, a física, a profundidade, o ruído e a poeira do próprio conjunto) escritas em
  unidades físicas e gravadas pelo caminho sobreamostrado, como foi feito no controle B do piloto para o conjunto
  base. Os fatores de sobreamostragem e do raster mestre saem da mesma conferência de convergência do piloto
  (4 cenas sem ruído, tolerância de 1 %), a 2,0 mm. Mesma receita, r1, três fluxos.
- **Medidas sem leitura de teste, antes dos treinos:** (i) a diferença entre a gravação nativa e a convergida nas
  4 cenas da conferência (quanto a amostragem nativa erra a 2 mm); (ii) o diâmetro efetivo D medido de novo no
  caminho novo, com a mesma definição, e a sobreposição recalculada.
- **Leitura, fixada agora, só com os crops (`raw`):** seja R_ant o par (F1, rejeição) da referência e R_curva o par
  dos crops da família padrão na mesma sobreposição, em r1, por interpolação linear em log(π D² σ) entre os dois
  níveis que cercam o valor do controle. Se o controle ficar mais perto de R_curva que de R_ant nas duas métricas,
  a amostragem nativa explica o desvio; nesse caso a coluna das letras pequenas a 2 mm do paper teria de ser
  refeita, e eu pergunto antes de refazer. Se ficar mais perto de R_ant nas duas, a amostragem não explica, o
  conjunto continua fora da curva e o texto continua dizendo que não sabemos por quê. Uma de cada: inconclusivo;
  reporto e não rodo outro braço sem perguntar.
- Camada e reconstrução entram na tabela ao lado, sem critério.

### J. Banco focal (`bank_jit`) a 0,9 e 1,1 mm sem recalibrar (só r1, por decisão do orientador)

Pergunta dele: o banco foi feito para tolerar deriva da distância. Ele aguenta um erro de 10 % em z sem
recalibrar? Se aguentar, é uma vantagem real da camada sobre a reconstrução; se não, dizemos isso.

- **Modelo:** `bank_jit` com a receita do paper, sem mudar nenhum hiperparâmetro (cinco propagações em ±5 % de α,
  treino com jitter de 5 % na distância), treinado no nível esparso da família padrão (`curve_u50_L008`), r1,
  `--no-aux`, α calibrado sem rótulo como na camada. Seleção e limiar na validação de 1,0 mm.
- **Testes:** o teste do nível esparso a 1,0 mm (referência) e os testes de d2 regravados a 0,9 e a 1,1 mm, como
  estão: modelo, galeria e limiar de 1,0 mm. O de 0,7 mm entra à parte, como estresse, fora da regra.
- **Regra "aguenta", fixada agora, por analogia com o "caiu" do Q0:** numa distância deslocada, o banco aguenta se
  o F1 dele ficar menos de 0,10 abaixo e a rejeição menos de 0,30 abaixo dos valores dele próprio a 1,0 mm. Ele
  aguenta a mudança de distância se aguentar a 0,9 e a 1,1 mm. É uma repetição só: o resultado é descritivo.
- **Ao lado, do mesmo r1 e já em arquivo:** camada e reconstrução como estão, camada recalibrada por razão e
  reconstrução recalibrada. Reporto também a diferença do banco, como está, para a reconstrução recalibrada em cada
  distância, e o preço do banco a 1,0 mm (banco − camada e banco − reconstrução). Sem limiar para essas diferenças.
- **O que não rodo sem perguntar:** r2–r5; um banco mais largo ou com mais jitter (a mudança de 10 % está fora da
  faixa de ±5 % em que ele foi treinado); a recalibração do banco.

## 2026-11-15, 15:58 — Q3: pré-registro da coluna de 2 mm refeita, do banco focal completo e do diagnóstico do conjunto fora da curva (responsável)

Resposta do orientador de ≈ 15:50 (`PROTOCOLO_CURVA.md`, na íntegra): "#4 faz o que achar melhor" e "#5 tempo de
gpu não é um problema, faça o necessário pela qualidade da pesquisa". Escrito antes de qualquer gravação, treino ou
leitura de teste destes itens. Valem as regras de sempre: pastas da etapa (`HOLO_RESULTS`, `HOLO_MODELS`), escolhas
só na validação, cada teste lido uma vez por modelo, nada em `results/`, `expected/` nem `models/`.

### C. Coluna das letras pequenas a 2 mm com o conjunto regravado (cinco repetições; pedido dele)

- **Conjunto:** `small_near_newrec` como está em disco (gravado no Q2-S, grade 2 vezes mais fina que o pixel, raster
  mestre 16). Não é regravado.
- **Fluxos:** os dez da tabela de tamanho (`SMALL_FLOWS` do pipeline: `raw`, `learned`, `complex`, `wiener`, `prop`,
  `bank_jit`, `bank_w3`, `rec_z0`, `rec_af`, `rec_twin`), com a receita que o pacote usa para os conjuntos de letras
  pequenas (`--no-aux`, `pipeline.py`), r1 a r5. Os três modelos de r1 que já existem (`raw`, `prop`, `rec_z0`) não
  são treinados de novo nem relidos.
- **O que reporto:** média de cinco por fluxo, ao lado da coluna do paper (conjunto gravado na amostragem do sensor,
  em `results/`), e a diferença por fluxo. Não há critério: é a mesma medida num registro mais fiel.
  **Previsão registrada:** nenhum fluxo muda o F1 médio em mais de 0,02 e a ordem das rotas não muda (crops muito
  abaixo; rotas com propagação juntas). Se mudar mais que isso, reporto com destaque.
- **No texto (decisão de escrita minha; o orientador pode reverter):** a coluna "small, 2 mm" passa a ser a do
  conjunto regravado, e os números das letras pequenas a 2 mm citados fora da tabela (quadrados da figura da curva,
  8.4, RQ5) passam a ser os dele, com cinco repetições. O conjunto antigo continua em `results/` (pipeline do pacote
  intocado) e é citado uma vez, como o registro na amostragem do sensor que dá a mesma leitura (ou não, se não der).
- **Medida ao lado, sem leitura de teste:** a mesma conferência (nativa contra convergida, 4 cenas sem ruído) para
  as letras pequenas a 19,25 mm (`small_z0`), para declarar a amostragem da outra coluna. Se a gravação nativa
  ficar dentro da tolerância de 1 % do piloto, a legenda diz isso. Se passar, a coluna de 19,25 mm recebe o mesmo
  tratamento (regravação e cinco repetições), pela mesma frase do orientador; aviso antes de disparar.

### J2. Banco focal: completar o teste (decisão minha, pelo "#4 faz o que achar melhor")

O teste J do Q2 foi uma repetição e só do banco do paper (±5 %), que não aguentou. Ficaram três perguntas que um
revisor faz: vale nas cinco repetições? um banco treinado para a mudança aguenta? e o banco recalibrado sem rótulo
fecha a diferença para a reconstrução recalibrada?

- **(a) `bank_jit`, r2 a r5**, mesmo procedimento do teste J (nível esparso da família padrão, `--no-aux`,
  `--alpha-extend 12`, seleção e limiar na validação de 1,0 mm; testes de d2 a 0,9 e 1,1 mm como estão; 0,7 mm à
  parte, como estresse).
- **(b) Bancos mais largos que o pacote já tem, sem criar hiperparâmetro:** `bank_wide` (7 planos em ±12 %, jitter
  de 12 %) e `bank_w2` (9 planos em ±12 %, jitter de 12 %), os dois treinados para uma faixa que contém a mudança de
  10 %; e `bank_w3` (7 planos em ±12 %, jitter de 5 %; é o "focal stack (7)" da tabela de tamanho), que separa a
  largura dos planos do jitter. r1 a r5, mesma receita e mesmos testes. O `bank_w1` (±8 %) não cobre a mudança e não
  roda. Os 0,7 mm (30 %) ficam fora da faixa de todos: estresse, fora da regra.
- **Regra, a mesma do Q2-J, agora com cinco repetições:** numa repetição, o banco aguenta se, a 0,9 e a 1,1 mm, o F1
  dele ficar menos de 0,10 abaixo e a rejeição menos de 0,30 abaixo dos valores dele próprio a 1,0 mm. Um banco
  **aguenta a mudança de distância** se aguentar em pelo menos 4 de 5 repetições.
- **O que reporto para a pergunta do orientador ("vantagem real sobre a reconstrução"):** para cada banco, por
  repetição e na média: o preço a 1,0 mm (banco − reconstrução, banco − camada); o banco como está contra a
  reconstrução como está e contra a reconstrução recalibrada a 0,9 e 1,1 mm, com a contagem de sinais (k de 10
  comparações). Sem limiar para essas diferenças. As frases possíveis, fixadas agora: (i) nenhum banco aguenta →
  "o banco focal não dispensa a recalibração"; (ii) um banco largo aguenta → "um banco treinado para ±12 % dispensa
  a recalibração numa mudança de 10 %, ao preço de X a 1,0 mm, e fica Y abaixo/acima da reconstrução recalibrada";
  em nenhum caso a camada é vendida como superior à reconstrução calibrada (instrução do orientador de 13:34).
- **(c) Recalibração do banco sem rótulo**, pelo procedimento "por razão" da camada (`recalibrate_distance.py`: a
  razão entre o α achado nos 32 hologramas sem rótulo da distância nova e o da validação de 1,0 mm multiplica todos
  os planos; o resto como na linha recalibrada da camada), para os quatro bancos, r1 a r5, a 0,9, 1,1 e 0,7 mm.
  Reporto ao lado da camada e da reconstrução recalibradas, com a diferença para a reconstrução recalibrada e a
  contagem de sinais (k de 15, como no d2). Sem critério. Se o procedimento não se aplicar ao banco sem mudar o
  pacote, o executor para e me diz.
- **O que não rodo sem perguntar:** bancos com hiperparâmetros novos; outro nível de densidade; os conjuntos de
  19,25 mm.

### D. Por que as letras pequenas a 2 mm estão fora da curva: dois controles em r1 (decisão minha, pela frase do #5)

O texto diz hoje "We do not know why this set is off the curve". O Q2-S descartou a amostragem. O que já está em
disco, antes de rodar qualquer coisa (`sets_by_fresnel.csv`, `depth_training.csv`):

- o conjunto de 2 mm tem números de Fresnel de 0,20 a 1,60 (p5–p95), contra 0,30 a 0,98 na família padrão; a fração
  do padrão de cada letra fora do próprio crop vai a 0,76 nas letras menores, contra 0,61;
- a 1,0 mm, esparso, treinar e testar os crops com a lei larga de profundidade (a do conjunto de 2 mm) dá 0,924 /
  0,605, contra 0,928 / 0,622 com a amostra plana (r1): a lei de profundidade, sozinha, não derrubou os crops.

**Controles (cada um muda uma coisa em relação ao `small_near_newrec`; mesma gravação convergida, mesma receita,
r1, fluxos `raw`, `prop`, `rec_z0`):**

- **D-N (faixa do número de Fresnel):** os tamanhos das letras passam a ser os que dão, a 2,0 mm, a faixa de N_F da
  família padrão (as fontes do conjunto base vezes √(2,0 / 19,25) = 0,3223); o resto igual (8 ± 3 letras por janela,
  borda e espaçamento, física, profundidade, ruído, poeira).
- **D-P (lei de profundidade):** a lei do conjunto (normal, desvio de 50 µm, cortada em ±150 µm) trocada pela
  padrão (uniforme no canal de 50 µm); o resto igual.
- Para cada controle meço D e a sobreposição com o mesmo script e calculo R_curva na sobreposição do próprio
  controle (interpolação em log(π D² σ), r1), como no Q2-S.

**Leitura, fixada agora, só com os crops:** seja R_reg o par (F1, rejeição) do `small_near_newrec` em r1 (0,799 /
0,120). Se o controle ficar mais perto de R_curva que de R_reg nas duas métricas, o fator trocado explica o desvio;
mais perto de R_reg nas duas, não explica; uma de cada, inconclusivo. **Previsão registrada:** D-N volta para a
curva e D-P não. Se D-N explicar, existe uma segunda forma de os crops falharem além dos vizinhos (o padrão da
própria letra saindo do crop quando N_F é baixo), e a frase do paper "a causa não é o padrão sair do crop" tem de
ganhar o limite em que foi medida (os N_F da família padrão). Nesse caso escrevo a proposta de frase e aponto para o
orientador; é uma repetição, descritivo.

**Leitura estratificada, sem modelo novo (descritiva):** com o modelo de crops de r1 do `small_near_newrec` e o
limiar dele, a aceitação das conhecidas e a rejeição das não vistas por terço de tamanho da letra e por haver ou
não o centro de outro holograma a menos de D. É uma segunda passada no mesmo teste, com o mesmo modelo e o mesmo
limiar; não escolhe nada.

**O que não rodo sem perguntar:** r2–r5 dos controles; outros fatores (a distância sozinha).

### L. Quanto o gerador consegue colocar acima de 300 por mm² (medida para a decisão do orientador sobre o #3)

Sem gravar holograma e sem treinar: o mesmo teste de `curve_feasibility_343.csv` para 514 e 771 letras por janela
(450 e 675 por mm²): letras pedidas, colocadas, puladas e área coberta nas mesmas cenas. Só informa a decisão dele;
nenhum nível novo é gravado sem a palavra dele.

## 2026-11-15, 16:59 — Q4: os dois controles do conjunto de 2 mm passam a cinco repetições (responsável)

**O que saiu do Q3-D em r1 (conferido por mim contra `eval/small_near_ctl{N,P}/` e refazendo a interpolação):**
com a faixa de N_F da família padrão (D-N) os crops voltam para a curva (0,916 / 0,530, contra R_curva 0,908 / 0,516
e R_reg 0,799 / 0,120); com a lei de profundidade padrão (D-P) não saem do lugar (0,803 / 0,136). As duas previsões
registradas valeram. Na mesma repetição, a reconstrução do D-N rejeitou 0,849 (0,954 no conjunto regravado), sem
critério para isso.

**Mudança de plano, escrita antes de rodar:** no Q3 escrevi que não rodaria r2–r5 dos controles sem perguntar. Levanto
essa trava para r2–r5 e só para ela, porque (i) o resultado do D-N vai sustentar uma frase do paper que explica um
desvio, e uma repetição é menos do que o paper usa em todo o resto; (ii) a rejeição da reconstrução no D-N em r1
pede as outras repetições para saber se é da repetição ou do conjunto; (iii) o orientador escreveu às ≈ 15:50 "tempo
de gpu não é um problema, faça o necessário pela qualidade da pesquisa". Aviso a ele na entrega. Os outros fatores
(a distância sozinha; qual ponta da faixa de tamanhos pesa) continuam sem rodar.

- **O que roda:** r2 a r5 de `raw`, `prop` e `rec_z0` em `small_near_ctlN` e `small_near_ctlP`, mesma receita
  (`--no-aux`), pastas da etapa. Os modelos de r1 não são retreinados nem relidos.
- **Leitura com cinco repetições, fixada agora, só com os crops:** na repetição k, R_reg(k) é o par (F1, rejeição)
  dos crops do `small_near_newrec` nessa repetição e R_curva(k) o dos crops da família padrão na sobreposição do
  controle, nessa repetição (interpolação em log(π D² σ) entre os níveis 15 e 69). O controle "volta para a curva"
  na repetição k se ficar mais perto de R_curva(k) que de R_reg(k) nas duas métricas. **O fator explica o desvio**
  se isso acontecer em ≥ 4 de 5 repetições; **não explica** se, em ≥ 4 de 5, o controle ficar mais perto de R_reg(k)
  nas duas; o resto é inconclusivo. Reporto também as médias de cinco e as distâncias médias.
- **Sem critério, ao lado:** camada e reconstrução dos dois controles, média de cinco, mínimo e máximo, contra as do
  `small_near_newrec` (0,973 / 0,985 e 0,974 / 0,985, cinco repetições).
- **Previsão registrada:** D-N explica em ≥ 4 de 5; D-P não explica em ≥ 4 de 5; a rejeição de 0,849 da reconstrução
  no D-N não se repete na média (palpite, sem critério).

## 2026-11-17, 11:40 — Q5: pré-registro do nível de 450 por mm² da curva de densidade (responsável)

Escrito depois do "#2 pode rodar" do orientador (≈ 11:35; `PROTOCOLO_CURVA.md`, fim) e antes de gravar o conjunto.
Nenhum holograma deste nível existe; o que existe é a medida do gerador sem holograma (Q3-L,
`curve_feasibility_dense.csv`: a 514 letras por janela ele coloca 512,3; 0,75 % do enchimento pulado; 34,2 % da área
coberta).

### O que é gravado e o que roda

- **Conjunto:** `curve_u50_L514`, o sexto nível da família padrão: as mesmas 40 309 letras anotadas, as mesmas
  sementes, a lei de profundidade padrão (uniforme em ±25 µm), gravador (s = 4), física e receita da família
  (`density_curve.sh`, com `LEVEL=514` aceito; nenhuma outra mudança no caminho de gravação). A única diferença para
  os outros níveis é `fill_mean=514`.
- **Conferência antes de qualquer treino** (passo `verify`, como nos outros níveis): anotações, rótulos, mapas,
  poeira, sessões e quadros em branco idênticos aos do nível esparso; gravações sem o enchimento idênticas às do
  esparso; letras por janela, enchimento pulado e área coberta. Se a conferência falhar, para tudo e é reportado.
- **Densidade reportada:** a obtida (contada no `metadata.csv`), não o alvo. Se mais de 5 % do enchimento for
  pulado, declaro (regra do Q0). A sobreposição do nível sai da fórmula do Q0 com D = 111,8 µm.
- **Fluxos e repetições:** `raw`, `prop` (`--alpha-extend 12`) e `rec_z0`, `--no-aux`, **r1 a r5 direto**. Desvio
  declarado da ordem do Q0 (r1 primeiro, r2–r5 onde "as curvas se separam"): os outros cinco níveis já têm cinco
  repetições, a regra deu sim em todos com folga, e o nível só entra na curva com cinco. As cinco rodam e são
  reportadas qualquer que seja o r1; nenhuma é descartada; cada teste é lido uma vez.
- **Nada mais roda neste nível:** nem bancos, nem distância, nem profundidade, nem os outros fluxos. Os cinco níveis
  que existem não são regravados nem retreinados; as linhas deles em `density_curve.csv` têm de sair idênticas às
  de hoje (confiro por diff).

### Regras (as do Q0, sem mudança)

- **"Caiu":** o fluxo caiu em F1 no nível se ficar ≥ 0,10 abaixo do F1 dele mesmo no nível esparso, na mesma
  repetição; caiu em rejeição se a rejeição das não vistas ficar ≥ 0,30 abaixo, na mesma comparação; com cinco
  repetições, caiu se a condição valer em ≥ 4 de 5. F1 e rejeição são reportados separados.
- **Descritivo, ao lado:** reconstrução − camada em F1 e em rejeição (média e em quantas de 5 é positiva); os
  limiares do P0 (camada − crops ≥ 0,10 em F1 e ≥ 0,30 em rejeição em ≥ 4 de 5); acerto em conjunto fechado dos
  três fluxos; o α calibrado e o treinado da camada (`curve_alpha.csv`).

### Previsões registradas (antes de gravar)

Referência, média de cinco no nível de 300 por mm²: crops 0,668 / 0,031; camada 0,942 / 0,743 (queda de rejeição
contra o esparso 0,239; por repetição 0,135–0,292, isto é, 0 de 5 cruzam a linha de 0,30); reconstrução 0,960 /
0,895.

1. **Crops:** F1 médio abaixo de 0,668 e rejeição média ≤ 0,05; acerto em fechado abaixo de 0,770.
2. **Camada:** cai em rejeição (≥ 4 de 5) e **não** cai em F1. É palpite, e a linha de rejeição está perto: espero
   rejeição média entre 0,60 e 0,70 (queda de 0,28 a 0,38) e F1 médio entre 0,91 e 0,935.
3. **Reconstrução:** não cai em nenhuma das duas; rejeição média ≥ 0,80; rejeita mais que a camada em 5 de 5.

### O que o texto diz em cada desfecho (fixado agora)

- **A camada cai em rejeição e a reconstrução não:** "a camada cai em rejeição a 450 por mm², o primeiro nível em
  que isso acontece; a reconstrução não cai em nenhum nível gravado". Reforça, sem mudar, a frase "a reconstrução
  calibrada é a melhor rota no denso".
- **A camada não cai:** "não cai até 450 por mm²", com a contagem das repetições e a queda média, e a informação de
  que o gerador satura perto de 575 por mm². Nenhum nível novo é gravado sem perguntar ao orientador.
- **As duas caem (em F1 ou em rejeição):** é dito assim, e toda frase que afirma que a etapa de propagação resolve
  o open-set ganha o limite de densidade (abstract, contribuição (3), conclusão, discussão). Frase que mudar de
  sentido entra com o sentido novo, sem suavizar, e vai listada para o orientador. A frase-tese não é tocada.
- **Contagem entre os limites (2 ou 3 de 5):** pela regra "não caiu"; reporto a contagem e as quedas por repetição.
- Em qualquer desfecho o nível entra na tabela e na figura da curva, com a densidade obtida, e nada é rodado de
  novo com outra configuração depois de lido o teste.
