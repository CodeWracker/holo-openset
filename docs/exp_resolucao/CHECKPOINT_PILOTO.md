# Checkpoint do piloto a 1,0 mm (repetição 1)

2026-11-14. Piloto aprovado em `PROTOCOLO_PILOTO_1MM.md`; pré-registro, escolhas e execução em
`CADERNO_PILOTO_1MM.md`. Só a repetição 1 foi treinada. As cinco repetições dependem da sua aprovação.

## 1. Resultado

**Em r1, a camada fica 0,049 acima dos crops em F1 e 0,373 acima em rejeição das não vistas.** A condição de
rejeição do critério (≥ 0,30) é cumprida; a de F1 (≥ 0,10) não é. O critério vale para cinco repetições e não foi
aplicado a r1 sozinho, mas com os crops em 0,928 a diferença de F1 não passa de 0,072 nem com uma camada perfeita.

| fluxo (r1, teste) | F1 open-set | rejeição das não vistas | acerto em conjunto fechado |
|---|---|---|---|
| crops do holograma (`raw`) | 0,928 | 0,622 | 0,978 |
| camada de propagação (`prop`) | 0,977 | 0,995 | 0,998 |
| reconstrução em z₀ (`rec_z0`) | 0,977 | 1,000 | 0,998 |
| `prop` − `raw` | +0,049 | +0,373 | |
| `rec_z0` − `prop` | −0,000 | +0,005 | |

O que mudou em relação ao base foi o crop, que ficou muito melhor. Os conjuntos pelo número de Fresnel, todos em r1
para comparar igual com igual:

| conjunto | z₀ | N_F (p5 / p50 / p95) | padrão fora do crop | F1 `raw` / `prop` / `rec_z0` | rejeição `raw` / `prop` / `rec_z0` |
|---|---|---|---|---|---|
| base (geometria do CBMS 2024) | 19,25 mm | 0,31 / 0,56 / 1,00 | 59 / 51 / 39 % | 0,785 / 0,960 / 0,952 | 0,105 / 0,852 / 0,836 |
| `small_near` | 2,0 mm | 0,20 / 0,71 / 1,60 | 76 / 49 / 28 % | 0,794 / 0,971 / 0,971 | 0,097 / 0,942 / 0,962 |
| piloto (`bench_1mm`) | 1,0 mm | 0,30 / 0,55 / 0,98 | 61 / 55 / 39 % | 0,928 / 0,977 / 0,977 | 0,622 / 0,995 / 1,000 |

O piloto tem o mesmo número de Fresnel e o mesmo vazamento do base, como planejado. Mesmo assim os crops sobem de
0,785 para 0,928 em F1 e de 0,105 para 0,622 em rejeição. A camada e a reconstrução também sobem, e continuam
empatadas entre si.

## 2. Robustez (modelos de r1, sem retreinar)

| condição do teste | `raw` F1 / rejeição | `prop` F1 / rejeição | `rec_z0` F1 / rejeição |
|---|---|---|---|
| 1,0 mm (o conjunto do piloto) | 0,928 / 0,622 | 0,977 / 0,995 | 0,977 / 1,000 |
| 0,7 mm, como está | 0,897 / 0,609 | 0,015 / 1,000 | 0,015 / 1,000 |
| 0,7 mm, distância recalibrada sem rótulo (literal) | – | 0,545 / 1,000 | 0,956 / 1,000 |
| 0,7 mm, recalibrada sem rótulo (por razão) | – | 0,913 / 0,999 | 0,958 / 1,000 |
| profundidade de 50 µm, como está | 0,929 / 0,630 | 0,773 / 0,997 | 0,801 / 1,000 |

- **A 0,7 mm sem recalibrar, a camada e a reconstrução rejeitam tudo.** Os crops quase não mudam.
- **A recalibração sem rótulo recupera.** Em 32 hologramas de validação ela achou 0,701 mm (o certo é 0,700). A
  leitura literal do pré-registro (o α calibrado substitui o treinado) dá 0,545 na camada, porque o treino tinha
  deslocado o α em −2,4 % e a substituição desfaz isso. A variante por razão, declarada antes de rodar, mantém o
  deslocamento e dá 0,913.
- **Com 50 µm de espalhamento de profundidade, a camada e a reconstrução perdem cerca de 0,2 de F1** e ficam abaixo
  dos crops em F1 (0,77 e 0,80 contra 0,93), mantendo a rejeição. A 1 mm, 50 µm é 1,7 vez a profundidade de campo.
  Os modelos foram treinados com 2,6 µm; não sei quanto um treino com 50 µm recuperaria.

## 3. O que foi feito

- **Conjunto:** 5000 imagens em 50 sessões (3500 / 700 / 800), 40 309 letras, 8 por janela, lado da letra de 21 a
  39 µm (p5–p95; 12,8 a 23,3 px), z₀ = 1,0 mm com a variação por sessão do base, profundidade de 2,6 µm. Exposição e
  ruído iguais aos do base (nível médio 101,5; ruído de 2,1 níveis de cinza). Exemplos em `img/bench_1mm_examples.png`.
- **Gravador sobreamostrado:** o campo é calculado numa grade mais fina e integrado em cada pixel; a letra é definida
  em unidades físicas e cai em qualquer posição em relação aos pixels. O caminho antigo (fator 1) continua idêntico
  bit a bit; `pytest` 56 testes, `reproduce check` 13/13.
- **Convergência:** 2× contra 4× difere de 1,1 a 1,8 % do padrão e não passa na tolerância de 1 %. 4× contra 8×
  difere de 0,2 a 0,5 % e passa, a 1,0 e a 0,7 mm. O conjunto foi gravado com 4×.
- **Correção antes de gravar:** a poeira fora do plano da amostra passou a ser propagada pela sua distância real em
  cada comprimento de onda. Isso mudou as gravações em 1 a 5 % do padrão.
- **Tempo e disco:** 32 minutos de GPU no total (17 da gravação) e 13,4 GB.

## 4. Como leio (interpretação minha)

- **O que se mantém em r1:** o crop rejeita 62 % dos padrões não vistos, contra 99,5 a 100 % da camada e da
  reconstrução. A parte open-set da tese continua, com diferença menor que no base (+0,37 contra +0,75).
- **O que não se mantém em r1:** "o crop falha". No reconhecimento das classes conhecidas o crop acerta 97,8 %.
- **O que aparece de novo a 1 mm:** os fluxos de distância fixa são frágeis à distância e à profundidade, e o crop
  não. A camada só acompanha a distância se for recalibrada, e a recalibração precisa preservar o ajuste do treino.

## 5. O que eu não sei

Não investiguei por que os crops melhoraram. Nada foi rodado de novo depois de ler o teste. Candidatos:

- **Coerência:** o borrão da fonte é 0,67 µm a 1 mm contra 12,8 µm a 19,25 mm (2 % do tamanho da letra contra 10 %).
- **Vizinhas mais longe:** com 8 letras por janela, as letras ficam 4,4 vezes mais afastadas em relação ao próprio
  tamanho, e o crop pega menos padrão das outras.
- **Código novo:** gravador e definição de cena são novos. O `small_near`, gravado com o código antigo, tem
  coerência e espaçamento parecidos e os crops ficam em 0,794 / 0,097. Isso não fecha com os dois candidatos acima.

## 6. Decisões que preciso de você

1. **Rodar as cinco repetições?** São mais quatro, cerca de 8 minutos cada, sem regravar nada. Recomendo: é o que
   permite aplicar o seu critério.
2. **Rodar dois controles antes de reescrever?** Recomendo os dois, pré-registrados, só em r1.
   - *Controle do código:* as letras do base a 19,25 mm gravadas com o gravador e a cena novos. Se os crops voltarem
     a ≈ 0,78 / 0,10, a melhora a 1 mm é física; se não, é efeito do código novo.
   - *Controle da vizinhança:* o conjunto de 1 mm com a densidade relativa do base (≈ 154 letras por janela), para
     ver se o crop cai quando as vizinhas se aproximam.
3. **Treinar também com 50 µm de profundidade?** Diria se a perda de 0,2 de F1 é da física ou do treino com amostra
   plana. É uma gravação (≈ 17 min) e três treinos.

## 7. Ressalvas

- É uma repetição. No base, r1 e a média de cinco diferem em 0,07 na rejeição da camada e em 0,09 na da reconstrução.
- O borrão da imagem do pinhole é calculado para a distância da amostra em todos os planos, e a dispersão das letras
  fora do plano usa o comprimento de onda central. São aproximações herdadas, pequenas a 2,6 µm.
- A 0,7 mm, com os vidros do simulador, a lamínula encosta na janela do sensor.
- A rejeição na validação não informa sobre classes não vistas (as "desconhecidas" da validação foram treinadas).

Arquivos: `results_exp_resolucao/eval/bench_1mm/*_r1.json`, `robustness_bench_1mm.csv`, `sets_by_fresnel.csv`,
`recal_bench_1mm_z07.json`, `oversampling_convergence.csv`, `pattern_in_crop_bench_1mm_summary.csv`.
