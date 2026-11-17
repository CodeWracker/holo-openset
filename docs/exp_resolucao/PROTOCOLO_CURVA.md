# Instrução do orientador de 2026-11-15 (≈ 08:00): enquadramento novo, curva de densidade, escrita

Resposta do orientador ao relatório do piloto a 1,0 mm (`RELATORIO_PILOTO_1MM.md`), na íntegra. Vale junto com
`PROTOCOLO.md`, `PROTOCOLO_Z.md` e `PROTOCOLO_PILOTO_1MM.md`. Plano e progresso em `TODO.md` (Fase Q);
pré-registro e conferências em `CADERNO_CURVA.md`.

---

Ótimo relatório. Decisões e próximos passos (tudo pode começar hoje).

ENQUADRAMENTO NOVO DO PAPER
A tese passa a ser uma inversão da tese do CBMS 2024, contada com medição:
1. Open-set em holografia sem lente (rejeitar desconhecidos, cadastrar classes novas), com o protocolo estrito.
2. O caminho sem reconstrução, como a área e nós em 2024 propusemos (classificar o recorte do holograma bruto), funciona em conjunto fechado mas falha no open-set: mesmo esparso, os crops aceitam 27 % das não vistas (rejeição 0,730 contra 0,997, mesmo sinal nas 5 repetições; resultado observado, o critério não foi cumprido ali), e em amostra densa a rejeição cai a 0,08. O mecanismo é o padrão das vizinhas entrando no crop, não o vazamento do padrão da própria letra; corrige isso em todo o texto, inclusive na hipótese. Seo 2009 entra como precedente.
3. O que resolve é trazer de volta uma etapa de propagação (a camada, que é uma reconstrução aprendida que se calibra sozinha, ou a reconstrução calibrada, que empata com ela), e ela custa ~1 ms. O argumento de tempo para pular a reconstrução não se sustenta, começando pelo nosso de 2024.
4. A simulação idealizada esconde tudo isso. ESTE PONTO TEM QUE ESTAR MUITO CLARO NO TEXTO (detalhes abaixo).

EXPERIMENTOS (GPU, começa já)
a. Cinco repetições no denso.
b. Curva de densidade: os dois intermediários (15 e 69 letras por janela) e mais um nível acima do denso, perto de 300 objetos por mm² (~25 % da área), para mostrar onde a própria camada cai. Mede o diâmetro efetivo do nosso holograma e usa a razão de sobreposição como eixo da figura (F1 e rejeição contra sobreposição; crops, camada e reconstrução). Primeiro r1 em todos os níveis; depois cinco repetições onde as curvas se separam. Pré-registra antes de rodar o que conta como "caiu" (por exemplo, F1 0,10 abaixo do esparso do mesmo fluxo).
c. Treino com 50 µm de profundidade como padrão em todos os conjuntos de 1 mm. Justificativa: o canal microfluídico do Sobieranski 2015 tem 50 µm de altura (fita adesiva dupla face, materiais e métodos).
d. Distância: o 0,7 mm fica como teste de estresse (a lamínula encostaria). Acrescenta 0,9 e 1,1 mm com os modelos de 1,0 mm, com e sem recalibração sem rótulo. A necessidade de recalibrar e a perda de 0,05 da camada recalibrada contra a reconstrução entram no texto.

ESCRITA (enquanto a GPU roda, sem esperar a curva)
Seção nova, dedicada: "a simulação muda a resposta". Juntar num lugar só, com uma figura-resumo, as evidências que já temos:
- Idealizado contra bancada (Tabela 12): o Wiener vai de melhor (0,988) a 0,910, o ranking inverte, e o modelo treinado no idealizado cai a 0,358 na bancada.
- A distância: a 19,25 mm (a do CBMS 2024, confirmada no código) a fonte apaga as franjas finas e a redução 4× funcionaria; a 1 mm (a da bancada, confirmada pelo Sobieranski) não. Um parâmetro decidiu se havia ganho computacional.
- O tamanho relativo: o que manda é o número de Fresnel; a letra de 129 µm a 1 mm vira sombra, e na escala de célula o padrão volta.
- A densidade: com o mesmo Fresnel e o mesmo vazamento, só a densidade derruba o crop (controle C).
- A profundidade: treino com amostra plana perde 0,2 de F1 em amostra com 50 µm.
- A tabela de todos os parâmetros do simulador, cada um com valor e fonte.
Essa seção tem de aparecer também no abstract e na lista de contribuições, não só no meio dos resultados.

Também já pode escrever, sem esperar: o Related Work (o levantamento da parte C, se ainda não terminou) e a correção do mecanismo onde ele aparece.

Fica para depois da curva: abstract, resultados e conclusão. Manda o diff do LaTeX sem merge, como sempre.

---

## Como leio (responsável; o orientador pode corrigir)

- Os experimentos a–d e a escrita listada estão aprovados para começar. Não há checkpoint novo entre "r1 em todos os
  níveis" e "cinco repetições onde as curvas se separam": a regra do que é "se separam" fica pré-registrada
  (`CADERNO_CURVA.md`) e é aplicada mecanicamente.
- Continuam valendo: resultados em `results_exp_resolucao/`, escolhas só na validação, pré-registro datado antes de
  rodar, nada em `results/` nem `expected/`, números no texto só por macro, diff do LaTeX num branch, sem merge e
  sem push.
- Tom: o gerador original foi "evoluído"; o CBMS 2024 é trabalho nosso, corrigido com medição.

## Resposta do orientador à pergunta da lei de profundidade (2026-11-15, ≈ 08:45, pelo diálogo de perguntas)

Pergunta: "O "50 µm" que treinamos no piloto não é a altura do canal: é o padrão do simulador, uma normal com desvio
de 50 µm cortada em ±150 µm (faixa total de 300 µm). O artigo de 2015 dá 50 µm de altura TOTAL do canal ("DSA, 50 µm
for microchannel height"). Qual lei de profundidade vira o padrão de todos os conjuntos de 1 mm (a curva de densidade
só é gravada depois desta resposta)?"

Opções: "Uniforme nos 50 µm (Recomendado)" e "Normal, desvio 50 µm (±150 µm)".

Resposta: **"Uniforme nos 50 µm (Recomendado)"**. Registrada na entrada Q1 de `CADERNO_CURVA.md`.


## Resposta do orientador ao relatório da curva (2026-11-15, ≈ 13:30)

Na íntegra (os números respondem às seis perguntas da seção 8 de `RELATORIO_CURVA.md`):

> TB tem o artigo do HoloAtt-UNet 2026 q eu tenho q te mandar. O push vc pode mandar pro git e overleaf
>
> #1 me explica melhor e faz uma visualização disso pra eu entender
> #2 faça sua recomendação
> #3 deixa no todo do related works isso aí pra eu pegar e te mandar
> #4 o título PRECISA mudar?
> #5 corrija
> #6 pode mandar

## Complemento do orientador (2026-11-15, ≈ 13:34)

Na íntegra:

> Complementando:
>
> 1. Push: manda os branches pro GitHub, sem merge. No Overleaf, só depois que eu revisar o PDF (se o Overleaf estiver ligado na branch principal, não empurra a reescrita pra lá ainda).
>
> 2. Camada contra reconstrução: no denso (135 e 300 por mm²) a reconstrução rejeita mais em 5 de 5, e com a distância mudando ela fica 0,045 acima em 15 de 15. O abstract e a conclusão têm que dizer isso com todas as letras: a reconstrução calibrada é a melhor rota no denso e quando z muda; a camada é a alternativa que se calibra sozinha. Nada de vender a camada como superior.
>
> 3. As três frases que mudaram de sentido (fonte a 5 cm, feixe estreito, crops a 0,881 na geometria do CBMS 2024): entram com o sentido novo, sem suavizar.
>
> 4. Seção "a simulação muda a resposta": a profundidade agora é 0,02 dentro do canal de 50 µm (o 0,2 só no teste de estresse); usa o número certo. E acrescenta a distância como evidência: 10 % de erro em z derruba camada e reconstrução sem recalibração.
>
> 5. só r1: testa o bank_jit a 0,9 e 1,1 mm sem recalibrar. Ele foi feito pra tolerar drift; se aguentar, é uma vantagem real da camada sobre a reconstrução, e se não aguentar, a gente diz isso.

### O que cada item vira (leitura do responsável; Fase R do `TODO.md`)

- **Push:** `exp/distancia-autofocus` e `exp/resolucao-fonte` vão para o GitHub como branches, sem merge. O
  repositório do paper só tem o Overleaf como remoto, ligado ao `main`: nada é enviado para lá (nem os dois commits
  locais do `main`, nem `rewrite/inversion`) até o orientador revisar o PDF.
- **Pergunta 1 (a camada "cair"):** explicação e uma figura para o orientador; nenhum nível novo é gravado.
- **Pergunta 2 (letras pequenas a 2 mm):** o controle recomendado, pré-registrado na entrada Q2 de
  `CADERNO_CURVA.md` antes de rodar.
- **Pergunta 3 (levantamento):** lista do que falta (os .RIS e os PDFs bloqueados) na nota do Related Work; o
  orientador manda o artigo do HoloAtt-UNet 2026.
- **Pergunta 4 (título):** é pergunta; respondo com a minha opinião e não mudo o título sem a palavra dele.
- **Pergunta 5 (figura do quadro inteiro):** regenerar com a camada de propagação; autorizado mexer no arquivo de
  `expected/` que isso muda.
- **Complemento 2, 3 e 4:** ajustes de texto no branch `rewrite/inversion`.
- **Complemento 5:** banco focal (`bank_jit`) a 0,9 e 1,1 mm sem recalibrar, só r1; pré-registrado na entrada Q2.

## Resposta do orientador à entrega da Fase R (2026-11-15, ≈ 15:50)

Os números são os da lista "O que espera a sua palavra" da minha mensagem final da Fase R (1 Overleaf; 2 título;
3 nível mais denso; 4 banco focal; 5 coluna de 2 mm da tabela de tamanho; 6 frase-tese; 7 abstract; 8 diagrama;
9 arquivos que ele manda). Na íntegra:

> #2 ok
> #4 faz o que achar melhor
> #5 tempo de gpu não é um problema, faça o necessário pela qualidade da pesquisa
> #6 calma já leio
> #3 que figura?

### O que cada item vira (leitura do responsável; Fase S do `TODO.md`)

- **#2 (título):** aprovado o que recomendei: "Open-Set Recognition of Interference Patterns on Lensless Holograms:
  Why Crops of the Raw Hologram Fail, and What a Propagation Step Costs from a Window to the Whole Field of View".
  Troco no `rewrite/inversion`.
- **#3 (nível mais denso):** ele não tinha localizado a figura; reenviada (`docs/exp_resolucao/img/
  explica_regra_caiu.png`). A decisão continua dele. Para ele decidir com o dado na mão, meço quanto o gerador
  consegue colocar acima de 300 por mm² (sem gravar holograma nem treinar).
- **#4 (banco focal):** a decisão é minha. Decido completar o teste: cinco repetições, os bancos mais largos que o
  pacote já tem (treinados para ±12 %) e a recalibração do banco. Pré-registro na entrada Q3 de `CADERNO_CURVA.md`.
- **#5 (coluna de 2 mm):** refazer com o conjunto regravado, cinco repetições, os dez fluxos da tabela. A frase dele
  ("faça o necessário pela qualidade da pesquisa") eu leio como critério geral desta rodada: onde o que falta é
  tempo de GPU, faço a versão completa. Por ela, e por decisão minha, entra também um diagnóstico em r1 de por que
  o conjunto de 2 mm está fora da curva (dois controles), que o texto hoje declara como "não sabemos por quê".
  Se ele achar que passei do pedido, é só descartar: nada disso mexe no que já existe.
- **#6 (frase-tese):** ele vai ler. Não mexo na frase. #1, #7, #8, #9 seguem esperando.
- Continua valendo: nada no Overleaf antes da revisão dele; sem merge; pré-registro antes de rodar.

## Resposta do orientador à entrega da Fase S (2026-11-17, ≈ 11:35)

Os números são os da lista "O que espera a sua palavra" da minha mensagem final da Fase S (1 Overleaf; 2 nível
mais denso, 450 por mm², "rodo se você disser sim"; 3 duas frases que o resultado dos controles pede para
qualificar: contribuição (2) da introdução e a frase da conclusão, com a proposta "within the Fresnel numbers of our
standard sets"; 4 frase-tese; 5 pendentes: abstract, diagrama da bancada, arquivos que ele manda). Na íntegra:

> #2 pode rodar
> #3 faz

### O que cada item vira (leitura do responsável; Fase T do `TODO.md`)

- **#2 (nível mais denso):** gravo o nível de 450 por mm² da família padrão (514 letras por janela) e rodo crops,
  camada e reconstrução em cinco repetições, com as regras do Q0 sem mudança. Pré-registro na entrada Q5 de
  `CADERNO_CURVA.md`, antes de gravar. O resultado entra na curva (tabela, figura, 8.4) por macro.
- **#3 (as duas frases):** acrescento a oração de limite na contribuição (2) da introdução e na frase da conclusão,
  no `rewrite/inversion`. A frase-tese não é tocada.
- Nada sobre o #1: o Overleaf continua esperando a revisão dele. Nada sobre o #4 e o #5: seguem como estão.
- Continua valendo: sem merge; pré-registro antes de rodar; números no texto só por macro; PDF e diff no fim.
