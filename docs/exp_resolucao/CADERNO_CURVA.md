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
