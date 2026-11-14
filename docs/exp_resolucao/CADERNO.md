# Caderno: processar na resolução que a fonte permite

Registro de comandos, resultados e decisões da etapa descrita em `PROTOCOLO.md`. Plano e estado em `TODO.md`.
Regras: resultados em `results_exp_resolucao/`; escolhas só na validação; o que vai ao teste é registrado aqui, com
data, antes de rodar; nada em `results/` nem `expected/`.

## 2026-11-14, 13:05 — Abertura (responsável)

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

## 2026-11-14, 13:10 — T0: teste pareado do enrollment (piloto)

- Onde: container da DGX, CPU, `source scripts/exp_resolucao/env.sh`. Comando:
  `python scripts/exp_resolucao/enroll_paired.py` (0,3 s). Lê só `results/eval/realistic/<fluxo>_r{1..5}.json`
  (as avaliações estritas do paper; nada foi rodado de novo). Saída: `results_exp_resolucao/enroll_paired.csv`
  (uma linha por camada × reconstrução × métrica, com a diferença de cada repetição).
- Métricas: as seis da tabela de enrollment do paper (`tab_enroll`) e as três `world5_*` que faltam (rank-1,
  rejeição das ausentes, acerto nas vistas). "Nova aceita" é `world*_new_class_acc`: a classe nova é aceita e
  correta. "Ausentes" são as 2 classes não vistas que continuam fora da galeria.
- Diferença pareada: valor da camada menos valor da reconstrução na mesma repetição. A contagem entre parênteses
  é quantas das 5 repetições têm o sinal da média (um empate exato em zero não conta).

Médias por fluxo (5 repetições):

| métrica | `prop` | `bank_jit` | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|---|---|
| k = 5, nova aceita | 0,674 | 0,654 | 0,629 | 0,546 | 0,560 | 0,573 | 0,627 |
| k = 20, nova aceita | 0,843 | 0,859 | 0,850 | 0,831 | 0,835 | 0,820 | 0,833 |
| todos, nova aceita | 0,937 | 0,943 | 0,931 | 0,929 | 0,929 | 0,931 | 0,943 |
| k = 20, rank-1 da nova | 0,880 | 0,896 | 0,872 | 0,856 | 0,856 | 0,854 | 0,886 |
| k = 20, rejeição das ausentes | 0,878 | 0,922 | 0,929 | 0,918 | 0,917 | 0,877 | 0,951 |
| k = 20, acerto nas vistas | 0,958 | 0,958 | 0,959 | 0,962 | 0,961 | 0,959 | 0,958 |
| k = 5, rank-1 da nova | 0,711 | 0,716 | 0,672 | 0,607 | 0,618 | 0,662 | 0,677 |
| k = 5, rejeição das ausentes | 0,918 | 0,915 | 0,949 | 0,926 | 0,924 | 0,876 | 0,955 |
| k = 5, acerto nas vistas | 0,958 | 0,959 | 0,959 | 0,962 | 0,961 | 0,959 | 0,958 |

`prop` menos cada fluxo de reconstrução: média da diferença pareada [mín, máx] (repetições com o sinal da média, de 5):

| métrica | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|
| k = 5, nova aceita | +0,046 [-0,077; +0,139] (3) | +0,128 [+0,011; +0,277] (5) | +0,114 [-0,001; +0,278] (4) | +0,101 [-0,059; +0,294] (4) | +0,047 [-0,036; +0,142] (3) |
| k = 20, nova aceita | -0,007 [-0,057; +0,040] (2) | +0,012 [-0,032; +0,060] (3) | +0,009 [-0,019; +0,036] (3) | +0,023 [-0,014; +0,051] (4) | +0,010 [-0,023; +0,069] (2) |
| todos, nova aceita | +0,006 [-0,017; +0,030] (4) | +0,008 [-0,004; +0,012] (4) | +0,008 [-0,003; +0,014] (4) | +0,005 [-0,006; +0,018] (4) | -0,006 [-0,028; +0,010] (4) |
| k = 20, rank-1 da nova | +0,008 [-0,027; +0,050] (3) | +0,025 [+0,008; +0,061] (5) | +0,024 [+0,005; +0,038] (5) | +0,026 [-0,009; +0,076] (4) | -0,005 [-0,037; +0,038] (3) |
| k = 20, rejeição das ausentes | -0,052 [-0,189; +0,008] (3) | -0,040 [-0,148; +0,064] (3) | -0,039 [-0,116; +0,060] (3) | +0,000 [-0,061; +0,061] (3) | -0,073 [-0,183; +0,000] (4) |
| k = 20, acerto nas vistas | -0,000 [-0,006; +0,009] (3) | -0,003 [-0,008; +0,004] (4) | -0,003 [-0,008; +0,004] (4) | -0,001 [-0,005; +0,005] (3) | +0,001 [-0,007; +0,009] (3) |
| k = 5, rank-1 da nova | +0,039 [-0,064; +0,145] (3) | +0,104 [+0,019; +0,229] (5) | +0,093 [+0,003; +0,222] (5) | +0,049 [-0,010; +0,107] (4) | +0,034 [-0,054; +0,144] (4) |
| k = 5, rejeição das ausentes | -0,031 [-0,087; +0,008] (3) | -0,008 [-0,093; +0,064] (2) | -0,006 [-0,099; +0,060] (2) | +0,042 [-0,036; +0,248] (3) | -0,037 [-0,121; +0,000] (4) |
| k = 5, acerto nas vistas | -0,000 [-0,006; +0,009] (3) | -0,004 [-0,008; +0,004] (4) | -0,003 [-0,008; +0,004] (4) | -0,001 [-0,005; +0,005] (3) | +0,000 [-0,007; +0,008] (3) |

`bank_jit` menos cada fluxo de reconstrução: média da diferença pareada [mín, máx] (repetições com o sinal da média, de 5):

| métrica | `rec_z0` | `rec_af` | `rec_afc` | `rec_edf` | `rec_twin` |
|---|---|---|---|---|---|
| k = 5, nova aceita | +0,025 [-0,063; +0,086] (3) | +0,107 [-0,026; +0,211] (4) | +0,094 [-0,025; +0,212] (4) | +0,080 [-0,045; +0,258] (4) | +0,026 [-0,022; +0,105] (4) |
| k = 20, nova aceita | +0,009 [-0,037; +0,056] (3) | +0,028 [-0,028; +0,061] (4) | +0,024 [-0,027; +0,057] (4) | +0,039 [-0,025; +0,071] (4) | +0,026 [-0,059; +0,076] (4) |
| todos, nova aceita | +0,012 [-0,004; +0,045] (3) | +0,014 [-0,015; +0,038] (4) | +0,013 [-0,014; +0,038] (4) | +0,011 [-0,003; +0,033] (4) | +0,000 [-0,014; +0,011] (2) |
| k = 20, rank-1 da nova | +0,024 [-0,022; +0,052] (4) | +0,040 [+0,010; +0,069] (5) | +0,040 [+0,011; +0,089] (5) | +0,042 [+0,009; +0,099] (5) | +0,010 [-0,019; +0,040] (3) |
| k = 20, rejeição das ausentes | -0,007 [-0,109; +0,107] (4) | +0,004 [-0,121; +0,073] (4) | +0,006 [-0,132; +0,071] (3) | +0,045 [-0,057; +0,248] (2) | -0,028 [-0,079; +0,004] (3) |
| k = 20, acerto nas vistas | -0,000 [-0,004; +0,004] (3) | -0,003 [-0,006; +0,000] (4) | -0,003 [-0,006; -0,000] (5) | -0,000 [-0,003; +0,001] (3) | +0,001 [-0,002; +0,005] (3) |
| k = 5, rank-1 da nova | +0,044 [-0,006; +0,087] (4) | +0,110 [+0,019; +0,169] (5) | +0,098 [+0,019; +0,162] (5) | +0,054 [+0,000; +0,099] (4) | +0,039 [+0,003; +0,144] (5) |
| k = 5, rejeição das ausentes | -0,034 [-0,126; +0,022] (4) | -0,011 [-0,113; +0,067] (3) | -0,010 [-0,119; +0,093] (3) | +0,038 [-0,060; +0,285] (2) | -0,041 [-0,079; +0,012] (4) |
| k = 5, acerto nas vistas | +0,000 [-0,004; +0,005] (2) | -0,003 [-0,006; +0,001] (4) | -0,003 [-0,006; +0,001] (4) | -0,000 [-0,002; +0,002] (3) | +0,001 [-0,002; +0,005] (2) |


- O que os números dizem, sem interpretação: com k = 5, a `prop` aceita mais classes novas que todas as
  reconstruções na média, mas contra `rec_z0` e `rec_twin` só em 3 de 5 repetições, e contra `rec_z0` a diferença
  vai de −0,077 a +0,139. A rejeição das ausentes com k = 20 é menor na `prop` que em `rec_z0` (−0,052, 3 de 5,
  mínimo −0,189), `rec_af`, `rec_afc` e `rec_twin` (−0,073, 4 de 5); contra `rec_edf` é igual na média.
