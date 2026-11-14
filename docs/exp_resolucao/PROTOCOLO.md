# Próxima etapa: reposicionar o paper e testar a resolução da fonte

> Instrução do orientador (Rodrigo), recebida em 2026-11-14 e copiada aqui na íntegra, sem alteração. É o protocolo
> desta etapa. O plano, o estado e as decisões ficam em `TODO.md`; os comandos e resultados em `CADERNO.md`.

Oi! O relatório revisado (commit `98fb304`) e o paper `b17b8df` fecharam a instrução anterior. Ficou muito bom: a explicação de `session_5` com os 8 sorteios e o Monte Carlo, a regra de ±3 % para o n* e a decomposição do que consertou o autofocus são exatamente o tipo de cuidado que o paper precisa. O texto que te mandei antes era a revisão antiga, de antes do relatório revisado; foi engano meu. Concordo com as duas diferenças que você apontou: a participação do detector de 95 % ou mais vale só em GPU, e o que conserta o ruído é a média 4 × 4, não a faixa estreita (a sua 7.5(ii) ficou melhor que a sugestão). Agora vem a próxima etapa, com três frentes, nesta ordem: (A) o piloto de um experimento novo, que pode dar o ganho de tempo real que queríamos; (B) a reescrita do paper com o enquadramento novo; (C) um parágrafo crítico sobre o argumento de velocidade da literatura. Todas as regras do protocolo anterior continuam valendo: resultados em pasta separada (`HOLO_RESULTS`), escolhas feitas só na validação, pré-registro no caderno com data antes de rodar o teste, nada escrito em `results/` nem `expected/`, e números no texto só por macro. Uma mudança: **desta vez, cada checkpoint precisa da minha aprovação explícita** antes da etapa seguinte.

---

## Por que mudamos o enquadramento

O seu relatório mostrou que o focal stack não tem vantagem de tempo legítima. Contra a busca barata (`rec_afc`) sobram 1,28× no front end e 1,01× fim a fim, e mesmo isso vem principalmente da escala por percentil dos canais, um detalhe de implementação. Então o paper deixa de vender tempo pelo front end. Ao mesmo tempo, os dados já têm três resultados positivos e um quarto possível:

1. **A propagation layer se autocalibra e iguala a reconstrução calibrada.** Um escalar α, achado em hologramas sem label, sem λ, Δ, z nem blank frame, dá F1 0,963 contra 0,964 de `rec_z0`, rejeição 0,924 contra 0,923 e discovery 0,74 contra 0,74. O α cai a 1,5 % da distância verdadeira. A rede só precisa de λz/Δ², e essa combinação é identificável a partir dos próprios dados. Há também um candidato a resultado positivo que ainda precisa de teste. No enrollment com 5 exemplos (Tabela 6 do paper), a `prop` aceita corretamente 0,674 contra 0,629 de `rec_z0`, 0,560 da busca barata e 0,546 da busca cega. Mas a rejeição das classes ainda ausentes é menor (0,878 contra 0,929). Faça a diferença pareada por repetição (`prop` menos cada fluxo de reconstrução, quantas de 5 com o mesmo sinal) **antes** de qualquer frase sobre isso.
2. **A simulação idealizada da literatura ordena os métodos errado.** No modelo ideal o Wiener é o melhor (0,988), e modelos treinados no ideal não transferem para a bancada (camada aprendida 0,358).
3. **O custo do reconhecimento é do detector, não da reconstrução.** O YOLO em tiles leva de 95 % a 98 % do tempo fim a fim em GPU e de 82 % a 94 % num core de CPU, nos fluxos baratos. O argumento de velocidade para pular a reconstrução não se sustenta quando medido (parte C).
4. **(A testar) A resolução certa é a da fonte, não a do sensor.** Como o gargalo é o detector, um ganho de tempo real precisa atacar o detector. É o experimento da parte A.

Um ponto do seu relatório muda a apresentação dos stacks. Os stacks largos (`bank_wide`, `bank_w2`) perdem rejeição das classes não vistas no base (0,826 e 0,838, contra 0,913–0,924 dos outros fluxos). Para um sistema open-set, isso é um custo sério. O stack que segue no paper é o de 5 (`bank_jit`), apresentado pelo que dispensa e pelo que tolera (F1 ≥ 0,94 até 6 % de desvio), não pelo tempo. Os largos ficam só na Tabela 11, com esse custo dito explicitamente.

---

## A. Experimento novo: processar na resolução que a fonte permite

### A.1 A ideia

O LED de 10 nm e o pinhole de 100 µm a 15 cm apagam quase todo o contraste acima de cerca de 70 ciclos/mm (Fig. 2b e eq. (5) do paper). O Nyquist do sensor de 1,67 µm é 299 ciclos/mm, ou seja, o sensor superamostra uns 4× em cada eixo (16× em pixels). O seu relatório já traz duas evidências a favor, e elas são a razão de este experimento valer a pena:

1. **A física prevê o limite que você mediu.** Com E(f) < 0,1 a partir de cerca de 72 ciclos/mm, b_max = ⌊1 / (2 × 1,67 µm × 72 mm⁻¹)⌋ = 4. Na validação do autofocus, reduzir 4× **baixou** o erro mediano de distância (31–43 µm contra 48 µm da busca cega), e reduzir 8× fez aparecerem de 5 % a 9 % de falhas grosseiras. O limite medido bate com o previsto.
2. **As altas frequências acima do envelope são só ruído.** Você mostrou que o que consertou o autofocus sob ruído foi tirá-las antes do ToG (só reduzir 4× já levou as falhas em `fullwell_500` de 70,6 % para 1,0 %). Se isso vale para o autofocus, pode valer para a rede.

**Hipótese H5 (tempo):** com o fator b escolhido pela física, o pipeline inteiro (detector, camada, embedding) roda em imagens b² vezes menores sem perder F1. Como o detector domina, o tempo fim a fim cai de forma parecida. **Hipótese H5b (robustez):** em `fullwell_500` e `beam_narrow`, o pipeline reduzido mantém ou melhora o F1 da resolução cheia, porque a redução tira o ruído que não carrega sinal.

Para referência, a minha estimativa (só para orientar, quem mede é você) é que o quadro reduzido 4× (cerca de 960 × 690) caiba em uma ou duas passadas do YOLO, em vez de 48 tiles, a partir dos 166,8 ms de hoje em GPU e 21,4 s num core de CPU. Atenção ao Amdahl de novo: depois da redução, ler o quadro e o blank frame (17,9 ms no seu run medido, em float32) pode virar o maior estágio. Por isso a A.3 pede para tratar a leitura.

### A.2 O fator b sai da física, não do teste

1. **Pelo modelo:** calcule E(f) da eq. (5) com os parâmetros da bancada (base: z = 19,25 mm; conjunto pequeno: z = 2 mm) e ache a frequência de corte f_c em que E cai abaixo de 0,1 (teste também 0,05). O fator máximo é b_max = ⌊1 / (2 Δ f_c)⌋.
2. **Às cegas, pelos dados:** calcule o espectro de potência médio por anel de `I/B` (e de `I` puro, sem blank frame) num conjunto de hologramas de treino. Ache onde ele encosta no piso de ruído e derive o b correspondente. Se os dois métodos concordarem, temos uma regra que não precisa de nenhum parâmetro óptico, na mesma linha da autocalibração do α. Isso fortalece muito a contribuição.
3. Registre o b escolhido no caderno **antes** de rodar o teste.

### A.3 Implementação

1. **Redução:** média b × b da imagem de 8 bits, como um binning. Guarde em float32 (ou em uint8 depois de arredondar, e anote qual dos dois). Redimensione as caixas por 1/b. Crie os conjuntos reduzidos como conjuntos novos (`data/realistic_b4`, por exemplo), sem sobrescrever nada.
2. **Pixel efetivo:** todo cálculo de frequência usa `b·Δ`. A função `freq_sq` já recebe o pixel desde o `afb`, então reaproveite. Há um teste de sanidade embutido: α = πλz/(NΔ)² não muda com a redução, porque NΔ é o mesmo. **O α calibrado nos dados reduzidos tem de sair igual ao da resolução cheia.** Se não sair, há um bug.
3. **Retreino:** a resolução muda, então treine tudo de novo nos dados reduzidos: YOLO e redes de embedding.
4. **Fluxos:** `raw`, `prop`, `bank_jit` e `rec_z0` (back-propagation no pixel reduzido). Use `rec_afc` como baseline de autofocus onde z variar. Com b = 4, a busca do `rec_afc` roda direto na imagem já reduzida, **sem** reduzir de novo: 8× no total já falhou na sua validação. Os stacks largos ficam de fora.
5. **Leitura e blank frame:** depois da redução, a leitura pesa. Leia o quadro em uint8, reduza logo após ler (é o equivalente ao binning do sensor) e mantenha o blank frame da sessão, já reduzido, em memória. Meça a leitura em todo fluxo, na mesma tabela dos outros estágios. Se algum estágio que hoje é desprezível (leitura, canais, embedding) passar a dominar depois da redução, reporte isso. É o resultado que diz quanto do ganho é real.
6. **Crops:** mantenha o RoI-align de 64 × 64 como referência. Teste também 32 × 32, que é mais barato e talvez suficiente com caixas de 11–31 px.
7. **YOLO no quadro inteiro:** compare uma passada com `imgsz` cobrindo o quadro reduzido inteiro contra tiles de 640 sobre o quadro reduzido. Teste também o modelo nano contra o atual.

### A.4 Pergunta secundária: detectar no bruto ou no refocado?

Um objeto em foco é compacto, enquanto o padrão bruto se espalha por centenas de pixels. Treine o YOLO também sobre a saída da propagação com α calibrado e ganho unitário (que não usa λ, Δ, z nem blank frame). Depois compare com o YOLO sobre o bruto reduzido: recall, falsos positivos, maior b tolerado e menor modelo que funciona. Se o refocado aguentar um detector menor ou uma redução maior, o paper ganha uma frase forte: **refocar primeiro é o que deixa o reconhecimento barato**. Se não aguentar, reporte assim mesmo; o ganho da redução continua valendo.

### A.5 Contraprova: objetos pequenos

Nos conjuntos `small_z0` e `small_near`, letras de 12–36 px viram 3–9 px com b = 4. A regra da física deve prever um b menor a 2 mm, onde o borrão do pinhole é dez vezes menor. **Rode os pequenos com o b que a regra der para cada distância**, não com 4. Se a regra acertar os dois regimes, ela é paramétrica de verdade, e não um número mágico.

### A.6 Métricas, critério e ordem

Métricas: as do protocolo (F1, rejeição, AUROC, enrollment com k = 5 e 20, discovery), mais o recall e os falsos positivos do detector, o F1 fim a fim nos quadros inteiros e o tempo por estágio (GPU e um core de CPU, mesma sessão de medição, regras da Seção 8 do protocolo). Reporte também **mm² por segundo por core de CPU**. É a métrica que conversa com o microscópio portátil e o uso point-of-care.

**Critério pré-registrado de resultado positivo:** com o b escolhido pela física (A.2), F1 open-set a até 0,01 da resolução cheia, e tempo fim a fim pelo menos 3× menor em GPU **e** em CPU, no mesmo run, com a leitura incluída. Para H5b, o critério é F1 em `fullwell_500` e `beam_narrow` igual ou maior que o da resolução cheia, em pelo menos 4 de 5 repetições. Se o F1 cair mais que 0,01, reporte a curva F1 × b × tempo e o ponto de equilíbrio. Isso também é resultado.

Ordem:

1. Piloto em r1, só janelas, b ∈ {1, 2, 4, 8}, fluxos `raw`, `prop` e `rec_z0`, nos conjuntos base, `fullwell_500` e `beam_narrow` (as variantes são regravadas das mesmas cenas, então dá para reduzi-las do mesmo jeito). **Checkpoint P1:** me mostre a curva F1 × b nos três conjuntos, o α calibrado em cada b e o b previsto pela física.
2. Com a minha aprovação, rode as cinco repetições, os quadros inteiros, os conjuntos pequenos e a pergunta A.4.
3. Sessão única de medição de tempo. **Checkpoint P2.**

---

## B. Reescrever o paper com o enquadramento novo

A versão `b17b8df` já fez a parte da distância: a busca estreita está na Seção 5.7 e nas Tabelas 5, 6 e 9, a resposta à RQ4 já diz que nenhuma rota é mais barata de um jeito que importe, e a fragilidade aparece atribuída à busca cega na resolução do sensor. O que falta é o enquadramento. Hoje o texto ainda é o da camada real: o abstract diz "close to but below", o "Which flow to use" diz que a reconstrução "generalises best to new classes", e a conclusão diz que o layer tem "weaker enrollment", o que a Tabela 6 contradiz para a `prop`. Faça isto só depois do checkpoint P2, para o texto já incorporar o resultado de A, positivo ou não. Trabalhe num branch do repositório LaTeX e me mande o diff; não faça merge.

1. **Título e abstract:** a manchete passa a ser o reconhecimento open-set no holograma bruto, com uma camada autocalibrada que iguala a reconstrução calibrada sem parâmetro óptico. Sem promessa de velocidade. O título atual ("...and What Reconstruction Costs from a Window to the Whole Field of View") põe o custo na manchete; proponha duas ou três alternativas centradas na camada autocalibrada. Se A der positivo, entra a frase de throughput (pela resolução da fonte, não pela camada).
2. **Contribuições (fim da Introdução):** os itens 1–3 da seção "Por que mudamos o enquadramento", mais o 4 se A der positivo, mais o simulador e o pacote aberto. A camada real e a complexa viram ablação. Escreva todas as notas "Prose to write" (Seções 5, 7.2, Discussion, Limitações) e apague as notas.
3. **RQ2, RQ3, "Which flow to use" e Conclusão:** reescreva com a `prop` como método proposto. A frase sobre enrollment só entra depois do teste pareado da seção de enquadramento, com o que ele mostrar, inclusive a rejeição menor das classes ausentes.
4. **Tabelas 10 e 11:** troque a linha de 5 % entre sessões por `frame_5` (800 sorteios), ou mantenha as duas com a nota do Monte Carlo: os 8 sorteios de `session_5` caíram no percentil 5 (`rec_z0`) e 2 (stack), e exageram o dano em cerca de 0,10 de F1. Hoje essa explicação só está numa nota "Prose to write".
5. **Stacks largos:** onde aparecerem, diga o custo em rejeição das classes não vistas.
6. **Conclusão e Limitações:** o mesmo enquadramento. Mantenha a limitação de que tudo é simulado.

---

## C. O parágrafo crítico: o argumento de velocidade da literatura

Isto é importante, então faça com cuidado. Muitos trabalhos motivam o reconhecimento sem reconstrução pela velocidade: a reconstrução seria iterativa, cara e incompatível com tempo real. Nós medimos estágio por estágio, e o argumento não se sustenta. O paper tem de dizer isso com clareza e firmeza. Mas o tom é de medição, não de ataque: nada de "mentem", "erram grosseiramente" ou adjetivos. O que derruba o argumento são os números. E **nós estamos incluídos**: o nosso CBMS 2024 [11] fez exatamente essa afirmação sem medir, e o texto diz isso explicitamente. Isso nos dá credibilidade e protege contra a acusação de atacar os outros.

### C.1 Levantamento (obrigatório antes de escrever)

A Seção 2 do paper ainda é só a lista de strings de busca. Então este levantamento é o Related Work inteiro, não só o parágrafo crítico: rode as strings S1–S7 no Scopus e na ScienceDirect, exporte em .RIS, remova duplicatas, faça a triagem e escreva a seção. Dentro disso:

1. Junte os trabalhos que **motivam** o caminho sem reconstrução pela velocidade ou pelo custo computacional.
2. Para cada um, leia o texto e anote no caderno a frase exata (com página) em que a afirmação aparece, e se o trabalho **mediu** o tempo da reconstrução contra o do classificador, com que baseline e em que hardware.
3. Só cite para essa afirmação um trabalho em que você achou a frase. Se um trabalho mediu direito, diga isso também. A crítica é a quem afirmou sem medir ou comparou com o pipeline completo de imagem limpa.
4. Comece pelo [11] (nosso), pelo [13] (Bravo-Frank et al.) e pelo [14] (Liu et al.), e confira o que cada um realmente diz antes de colocá-lo na lista.

### C.2 Onde entra

1. **Introdução:** uma ou duas frases logo depois de apresentar a linha sem reconstrução.
2. **Related Work:** o parágrafo completo (rascunho abaixo).
3. **Discussion:** uma frase de recomendação para a área.

### C.3 Rascunho do parágrafo (ajuste depois do levantamento)

Use as macros do `numbers_distancia.tex` e as novas que forem necessárias. Os nomes abaixo vêm do seu relatório; confira se existem.

```latex
\paragraph{The speed argument.} A recurring motivation for recognising patterns on the raw hologram is speed: numerical reconstruction is described as iterative and computationally expensive, and skipping it as what makes real-time analysis possible~[CITE: only works where the claim was found]. Our own earlier work made this argument~\cite{rockembach2024} without measuring it. We measured it here, stage by stage, from a $640\times640$ window to a full sensor frame of 29.4\,mm$^2$, and it does not hold. One reconstruction is one pair of Fourier transforms: \DistTimeRecZZeroFrontGpuBigMs~ms per full frame on one GPU, flat field and network input included, less than a focal stack of learned filters (\DistTimeBankJitFrontGpuBigMs~ms). The detector, which every route needs, costs \DistStageYoloTiledGpuBigMs~ms. What is expensive is repeating the reconstruction to produce a clean picture for a human observer---a blind autofocus over 114 distances, iterative twin-image removal, a focus for every object---and recognition needs none of it: twin-image removal and per-object focus do not change the open-set F1, and a search over $\pm$10\,\% of the nominal distance on the amplitude averaged $4\times4$ finds the distance \DistSearchBlindOverAfcGpu$\times$ faster than the blind search, with the same F1 and without its failures under noise.
```

Frase para a Discussion:

```latex
A claim that a reconstruction-free route is faster should therefore be measured, stage by stage and on the same hardware, against a single back-propagation at a calibrated or cheaply searched distance---not against the full pipeline of a clean reconstruction, and not without timing the detector that both routes share.
```

Se depois do levantamento algum trabalho tiver medido e mostrado ganho contra um baseline justo, o parágrafo tem de reconhecer isso e explicar a diferença (hardware, tamanho do objeto, tipo de detector). A força do parágrafo está em ser verificável.

---

## Entregáveis

1. Branch com o código de A, testes passando, `reproduce check` OK.
2. Caderno com o b previsto (pelos dois métodos), as escolhas datadas e os comandos.
3. CSVs, figuras (F1 × b × tempo, custo × F1 com e sem detector, mm²/s por core) e macros novas.
4. Tabela do levantamento C.1: trabalho, frase exata, página, mediu ou não, baseline usado.
5. Diff do LaTeX (B e C) para eu revisar, sem merge.
6. Um relatório curto como o anterior, incluindo a seção "o que deu errado".

Qualquer dúvida, pergunte antes de decidir. Valeu!
