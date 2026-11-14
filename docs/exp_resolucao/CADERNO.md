# Caderno: processar na resolução que a fonte permite

Registro de comandos, resultados e decisões da etapa descrita em `PROTOCOLO.md`. Plano e estado em `TODO.md`.
Regras: resultados em `results_exp_resolucao/`; escolhas só na validação; o que vai ao teste é registrado aqui, com
data, antes de rodar; nada em `results/` nem `expected/`.

## 2026-11-14, 12:20 — Abertura (responsável)

- Branch `exp/resolucao-fonte`, criado de `exp/distancia-autofocus` (`4e44f3a`).
- Hipóteses e critério: os do protocolo (H5, H5b, A.6), copiados em `TODO.md`, Seção 1. Nada foi rodado ainda.
- Decisões de desenho tomadas antes de rodar (R1–R7 de `TODO.md`): em particular, a imagem reduzida é guardada em
  uint8 depois de arredondar (o blank frame reduzido em float32); o piloto é r1, janelas, caixas anotadas,
  b ∈ {1, 2, 4, 8}, `raw`, `prop`, `rec_z0`, base + `fullwell_500` + `beam_narrow`, crop 64 × 64.
- **O fator b que vale para o critério sai da física (A.2) e será escrito aqui, com data, antes de qualquer avaliação
  no split de teste.** O piloto mede o F1 de teste nos quatro valores de b porque o protocolo pede a curva; nenhuma
  escolha é feita com ela. Tudo o que ainda for escolhido (tamanho do crop, armazenamento, detector) sai da
  validação.
- A partir daqui o caderno é escrito pelo subagente "piloto"; eu acrescento as minhas revisões em entradas marcadas
  "(responsável)".
