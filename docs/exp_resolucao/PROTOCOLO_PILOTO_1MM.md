# Piloto na distância certa (1,0 mm): aprovação e escolhas do orientador

> Instrução do orientador (Rodrigo), recebida em 2026-11-14 por volta das 15:40, em resposta ao Checkpoint Z
> (`CHECKPOINT_Z.md`) e à entrada Z9 do caderno. Copiada aqui na íntegra, sem alteração. É a aprovação explícita do
> Checkpoint Z **para o piloto** (opção 2); as cinco repetições dependem de um novo checkpoint (item 5).

Aprovado o piloto, com estas escolhas (fixadas agora, antes de rodar):

1. Distância nominal: 1,0 mm, que é o que o Sobieranski confirmou ("lamínula muito próxima do sensor, sem encostar porque aquece"). Mantém a variação de z por sessão como no base. O 0,7 mm entra só como teste de robustez, avaliado com os modelos de 1,0 mm, sem retreinar.

2. Tamanho dos objetos: o mesmo número de Fresnel do base. O base vai de 95 a 172 µm a 19,25 mm, ou seja, N_F de ~0,30 a 1,0; a 1 mm isso dá letras de ~22 a 39 µm. Assim o padrão é equivalente ao do base e o que muda é só coerência e pixel. Confere a conta e registra no caderno.

3. Simulador: grava com sobreamostragem (propaga numa grade mais fina e integra no pixel de 1,67 µm). Faz o teste de convergência: o resultado com 2× e com 4× de sobreamostragem tem de ser o mesmo; se não for, sobe até convergir.

4. Critério pré-registrado, escrito no caderno antes do teste: a tese central (o crop falha, a camada sobre o holograma inteiro recupera) se mantém se, em pelo menos 4 de 5 repetições, a prop ficar pelo menos 0,10 acima dos crops em F1 e pelo menos 0,30 acima em rejeição das não vistas, como no base e no small_near. Se não, reporta como está: a tese muda e a gente reescreve.

5. Piloto em r1 primeiro: crops, prop e rec_z0. Checkpoint comigo antes das 5 repetições.

6. O conjunto base de hoje fica no paper como "a geometria do CBMS 2024", para comparação com o trabalho anterior, e não como a bancada. Vale apresentar os conjuntos pelo número de Fresnel: o small_near (N_F ~0,72) já cai dentro da faixa do base e repete o resultado.

Sobre o texto do CBMS 2024: está na página 367: "The diffraction parameters used were λ = 385nm, z = 50k, pixel size of 1.67μm", sem unidade no z. Te mando o PDF.

---

## Resposta do orientador ao checkpoint do piloto (2026-11-14, ≈ 17:38), copiada na íntegra

As três decisões pedidas em `CHECKPOINT_PILOTO.md` eram: (1) rodar as outras quatro repetições; (2) rodar dois
controles em r1, pré-registrados (o do código e o da vizinhança); (3) treinar também com 50 µm de profundidade.
A resposta:

1 - ok
2 - faz os 2 antes de reescrever
3 - ok


---

## Resposta do orientador ao item 4 do relatório do piloto (2026-11-14, ≈ 21:20), copiada na íntegra

O item 4 das decisões pedidas em `RELATORIO_PILOTO_1MM.md` era: "Perguntar ao prof. Sobieranski a densidade típica
das amostras. É o parâmetro do simulador que ainda não tem fonte." A resposta:

Pode escolher, ele não lembra. E se essa pergunta tava no relatório, atualiza ele

(Os itens 1, 2, 3 e 5 do relatório não foram respondidos nesta mensagem.)
