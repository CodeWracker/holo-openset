# Antes da parte A: definir um z razoável

> Instrução do orientador (Rodrigo), recebida em 2026-11-14 por volta das 13:15, depois de `PROTOCOLO.md`, e copiada
> aqui na íntegra, sem alteração. Ela muda a ordem: a parte A fica suspensa até o Checkpoint Z.

## Antes da parte A: definir um z razoável

Uma mudança de ordem: **segura a parte A (redução) até fecharmos isto.** O resto (parte C, Related Work, e o teste pareado do enrollment) pode andar em paralelo.

### O problema

O z = 19,25 mm do simulador vem de ler o "z = 50k" da rotina como 50 000 λ. Mas o artigo de 2015 (Sobieranski et al., Light Sci Appl 4:e346) diz que "the distance between sample and electronic detector is as small as possible", sem dar número. E ele precisa de 49 quadros com super-resolução de pixel para chegar a 1,55 µm, o que só faz sentido se o holograma tiver detalhe mais fino que o pixel, ou seja, z pequeno. A legenda da Fig. 2 diz "z = [30k, 45k, 60k, 70k] (k = ×1000), conforme a Eq. (S3)", e a unidade não está no texto principal.

Isso importa porque a parte A depende inteiramente de z. Pelas minhas contas com a eq. (5) (LED de 10 nm, pinhole de 100 µm a 15 cm, corte em E < 0,1):

| z | borrão da fonte | corte do contraste | b_max |
|---|---|---|---|
| 19,25 mm | 12,8 µm | 73 ciclos/mm | 4 |
| 5 mm | 3,3 µm | 170 ciclos/mm | 1 |
| 2 mm | 1,3 µm | 278 ciclos/mm | 1 |
| 1 mm | 0,7 µm | 397 ciclos/mm | 1 |

O Nyquist do sensor é 299 ciclos/mm. Com a amostra a poucos mm, o sensor subamostra o holograma, e a redução não se aplica. Refaça essas contas para conferir.

Não estamos reproduzindo uma bancada exata, e sim simulando uma bancada razoável. Então o z certo é o que a literatura de microscopia lensless on-chip sustenta, com referência.

### O que fazer

1. **Unidade do z no código.** Confira no gerador original (o da Manu, que já temos) e no nosso `sim/physics.py` como o z entra no kernel de Fresnel, e se o "50k" é mesmo 50 000 λ. Anote no caderno com o trecho de código.
2. **Levantamento.** Junte de 8 a 15 trabalhos de holografia in-line sem lente com LED e pinhole e sensor CMOS de pixel de 1–2 µm (comece pelo grupo do Ozcan: Mudanyali 2010 Lab Chip, Bishara 2010, Greenbaum 2012 Nat Methods; e pelo próprio Sobieranski 2015). Monte uma tabela com: referência, λ e largura de banda, diâmetro do pinhole, distância pinhole–amostra (L), distância amostra–sensor (z), pixel, se usa super-resolução de pixel, e a resolução reportada. Só entra na tabela valor que esteja escrito no artigo, com página.
3. **Proposta de configuração.** Com a tabela, proponha um z (e, se for o caso, D e L) razoável para a bancada simulada, com as referências que o sustentam. Confira a coerência: o E(f) dessa configuração tem de ser compatível com as resoluções reportadas (com e sem super-resolução).
4. **Consequências, sem regravar nada.** Calcule o E(f) e o b_max da configuração proposta e escreva o que muda: se o conjunto base a 19,25 mm vira uma "configuração distante" e o `small_near` (2 mm) fica mais perto do realista; se a parte A vale e com que b; e o que teria de ser regravado e retreinado. **A decisão de regravar fica comigo.**

### O que o Sobieranski confirmou (para usar no texto)

- **Inclinação:** não havia na bancada. Havia só pequenas deformidades do material, ou seja, variações locais de profundidade. Isso já é o spread de profundidade por objeto que simulamos e que não custa nada. O experimento de inclinação vira uma frase no paper.
- **Iluminação:** brilho da fonte e shutter do sensor eram ajustados à mão, então a iluminação e a exposição variam por sessão. Isso justifica o blank frame e o perfil de feixe por sessão do simulador.
- **Aquisição:** na super-resolução, a fonte era deslocada à mão para cada um dos 49 quadros, e um conjunto levava muito tempo. O tempo de processamento só pesa no uso com quadro único: o sensor entrega 3,2 quadros por segundo (312 ms por quadro), a GPU já acompanha (~0,2 s por quadro) e um core de CPU não (~24 s). Qualquer argumento de velocidade tem de ser enquadrado assim.
- **Hologramas reais:** não vai ter. Tudo continua simulado, e a limitação continua no paper.

**Checkpoint Z:** me mande a tabela do levantamento, a unidade do z no código e a proposta de configuração com as consequências. Só depois disso a parte A anda.

---

## Atualização do orientador (2026-11-14, ≈ 13:50), copiada na íntegra

Atualização: o Sobieranski confirmou que a lamínula fica muito próxima do sensor, só não encosta porque o sensor aquece. Então z é da ordem de 1 mm, não 19,25 mm. No levantamento, o foco passa a ser fechar esse número (lamínula + vidro do sensor + folga), com referências.

Consequências pra já: a parte A (redução 4×) não se aplica a essa distância (b_max = 1), então fica suspensa. Na proposta do checkpoint Z, inclui também o que muda se o conjunto base for regravado na distância certa: quais conclusões precisam ser checadas de novo (principalmente o espalhamento do padrão para fora do crop e a vantagem da camada sobre os crops) e o custo de regravar e retreinar. O small_near (2 mm) já dá uma prévia. E anota que o aquecimento do sensor torna plausível o drift de z durante a sessão (walk_05).

---

## Segunda atualização do orientador (2026-11-14, ≈ 14:10), copiada na íntegra

Mais uma coisa para ter em mente, porque define como vamos contar a história no paper e no resumo para o Sobieranski.

O Sobieranski acha que o setup físico "nem precisaria" na simulação, e que é comum só simular e declarar os parâmetros. Concordamos com a segunda parte: vamos fixar e declarar todos os parâmetros, cada um com referência. Mas a linha do paper é que a simulação faz parte do método, porque esses valores mudam as conclusões. Temos duas evidências e precisamos delas bem apresentadas:

1. Idealizado contra bancada (Tabela 12): o Wiener vai de melhor (0,988) a pior (0,910), o ranking inverte, e o modelo treinado no idealizado não transfere (0,358). Já existe; só precisa de uma figura clara.

2. A distância amostra–sensor: ele confirmou que a lamínula fica muito perto do sensor (sem encostar porque aquece), então z é da ordem de 1 mm, não 19,25 mm. A 19,25 mm a fonte apaga as franjas finas e a redução 4× funcionaria; a ~1 mm não. Um parâmetro decidiu se havia ganho computacional.

No checkpoint Z, além da tabela do levantamento e da proposta de z, traga:
- uma tabela com todos os parâmetros do simulador, o valor e a fonte de cada um (artigo, datasheet ou suposição nossa);
- uma comparação base (19,25 mm) contra small_near (2 mm) nas métricas principais (F1 e rejeição de crops, prop e rec_z0) e no quanto o padrão vaza para fora do crop, para mostrar o efeito de z antes de regravar;
- uma figura simples de "o que muda com o setup", que sirva tanto para o paper quanto para o resumo ao Sobieranski.

Ele também confirmou: sem inclinação (só deformidades locais pequenas), brilho por shutter e ganho analógico ajustados à mão, LED UV de 385 nm (M385L2, 10 nm FWHM no datasheet).

No texto, o gerador da Manu foi "evoluído", não "estava errado"; e o CBMS 2024 é trabalho nosso que corrigimos com medição.

