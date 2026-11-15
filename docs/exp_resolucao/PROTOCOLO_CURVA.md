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
