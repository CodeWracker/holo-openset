# Caderno do piloto na distância certa (1,0 mm)

Caderno do piloto aprovado em `PROTOCOLO_PILOTO_1MM.md` (instrução do orientador, na íntegra). Entradas em ordem de
tempo, a mais recente embaixo, com a hora real do relógio. Quem escreve: o responsável (planejamento, pré-registro,
revisão) e o agente que executa (marcado "(execução)"). O caderno anterior da etapa é `CADERNO.md`.

## 2026-11-14, 15:50 — P0: pré-registro do piloto (responsável)

Escrito antes de qualquer código do piloto, de qualquer gravação e de qualquer treino. Nada foi rodado.

### O que o orientador fixou (itens 1–6 de `PROTOCOLO_PILOTO_1MM.md`)

1. Distância nominal z₀ = 1,0 mm; variação de z por sessão como no base (`session_z_std` = 0,005, relativa). O
   0,7 mm entra só como robustez, com os modelos de 1,0 mm, sem retreinar.
2. Letras com o mesmo número de Fresnel do base.
3. Gravação com sobreamostragem (campo numa grade mais fina, integração no pixel de 1,67 µm) e teste de convergência
   2× contra 4×.
4. Critério da tese central (abaixo).
5. Primeiro só r1, com crops (`raw`), camada de propagação (`prop`) e reconstrução em z₀ (`rec_z0`). Checkpoint com
   o orientador antes das cinco repetições.
6. No paper, o conjunto base de hoje passa a ser "a geometria do CBMS 2024", e os conjuntos são apresentados pelo
   número de Fresnel.

### Conferência da conta do item 2

N_F = (lado/2)² / (λ z), com λ = 385 nm, pixel 1,67 µm, lado = maior lado da caixa da letra
(`annotations.csv` do base, todos os splits: p5 / p50 / p95 = 57 / 77 / 103 px; mínimo e máximo 46 e 140 px).

| | lado no base (19,25 mm) | N_F | lado a 1,0 mm com o mesmo N_F |
|---|---|---|---|
| p5 | 57 px = 95,2 µm | 0,306 | 12,99 px = 21,7 µm |
| p50 | 77 px = 128,6 µm | 0,558 | 17,55 px = 29,3 µm |
| p95 | 103 px = 172,0 µm | 0,998 | 23,48 px = 39,2 µm |
| mín. | 46 px = 76,8 µm | 0,199 | 10,48 px = 17,5 µm |
| máx. | 140 px = 233,8 µm | 1,844 | 31,91 px = 53,3 µm |

A conta do orientador fecha: N_F de 0,31 a 1,00 no base (p5–p95), letras de 21,7 a 39,2 µm a 1,0 mm. O fator é
√(1,0 / 19,25) = 0,22792 nos comprimentos. Em tamanho de fonte: 70–118 px no base → 15,95–26,89 px a 1,0 mm.

`small_near` (letras pequenas a 2 mm): lado p5 / p50 / p95 = 15 / 27,75 / 42 px, N_F = 0,20 / 0,70 / 1,60. A mediana
(0,70; o orientador escreveu ≈ 0,72) cai dentro da faixa do base; a faixa dele é mais larga que a do base.

### O texto do CBMS 2024 (conferido no PDF que o orientador mandou às 15:44)

`referencias/c/rockembach2024_full/rockembach2024_cbms.pdf`, p. 367, seção "A. Dataset of Synthetic Holograms":
"The diffraction parameters used were λ = 385nm, z = 50k, pixel size of 1.67μm, and an output image resolution with
the same resolution of its input (640x640 pixels). After processing, a total of 200 holograms were generated". O z vem
sem unidade; o código do gerador dá 50 000 λ = 19,25 mm (`CADERNO.md`, Z1 e Z9). Fecha a pendência do Z9.

### Critério pré-registrado da tese central (item 4, palavras do orientador)

"a tese central (o crop falha, a camada sobre o holograma inteiro recupera) se mantém se, em pelo menos 4 de 5
repetições, a prop ficar pelo menos 0,10 acima dos crops em F1 e pelo menos 0,30 acima em rejeição das não vistas,
como no base e no small_near. Se não, reporta como está: a tese muda e a gente reescreve."

Como leio, para não haver escolha depois:
- **Métricas:** as mesmas das tabelas do paper e de `setup_comparison.csv`: `novel_open_macro_f1` (F1) e
  `novel_unknown_rejection` (rejeição das não vistas), no split de teste, com o limiar escolhido na validação.
- **Fluxos:** `prop` contra `raw` (crops do holograma), na mesma repetição (pareado).
- **Regra:** uma repetição conta a favor só se cumprir as **duas** condições (F1(prop) − F1(raw) ≥ 0,10 **e**
  rejeição(prop) − rejeição(raw) ≥ 0,30). A tese se mantém com 4 ou 5 repetições a favor em r1–r5.
- **O piloto em r1 não decide o critério.** Ele mostra uma repetição; o critério só é aplicado depois das cinco, que
  dependem do checkpoint (item 5).
- Referência: no base as diferenças médias são +0,183 (F1) e +0,820 (rejeição), 5 de 5; no `small_near`, +0,179 e
  +0,810, 5 de 5 (`results_exp_resolucao/setup_comparison.csv`).
- `rec_z0` é reportado ao lado, sem critério: ele diz se a reconstrução com a distância conhecida continua empatada
  com a camada.

### Teste de convergência da sobreamostragem (item 3): definição e tolerância (minha escolha)

- **O que se compara:** a mesma cena física gravada com fator s e com fator 2s (s = 1 é o simulador de hoje; depois
  2, 4, 8…), sem ruído nem quantização (`full_well` = 0, `read_noise` = 0, `prnu` = 0, `bits` = 0), com tudo o mais do
  conjunto (fonte, feixe, poeira, pixel). A cena tem de ser a mesma para todo s: a letra é definida em unidades
  físicas (tamanho, rotação, posição com resolução abaixo do pixel) e amostrada em cada grade.
- **Medida:** em cada cena, rms(I_s − I_2s) na janela, dividido pelo rms do padrão de I_2s (I_2s menos a gravação da
  mesma sessão sem objetos). Oito cenas a 1,0 mm e oito a 0,7 mm (o teste de robustez usa o mesmo gravador).
- **Tolerância:** "o mesmo" = no máximo **1 %** em todas as cenas. Reporto também a diferença em níveis de cinza de
  8 bits e em relação ao ruído de uma gravação (para dizer se ela ficaria abaixo do ruído).
- **Regra:** grava-se com o menor s tal que (s, 2s) passa, a 1,0 mm e a 0,7 mm. Se (2, 4) não passar, testa-se
  (4, 8), e assim por diante.
- O teste é feito na imagem, antes de qualquer modelo. Não retreino modelos para comparar fatores.

### Robustez a 0,7 mm (item 1): como será avaliada

- Cenas do split de teste do conjunto de 1,0 mm gravadas de novo com z₀ = 0,7 mm (mesmas sementes), com o mesmo
  gravador sobreamostrado. Modelos de r1 treinados a 1,0 mm, sem retreinar.
- **(a) Como está (o que o orientador pediu):** os modelos e a distância nominal de 1,0 mm, sem mudar nada.
- **(b) Recalibrado sem rótulo (acréscimo meu, reportado à parte):** a distância usada por `rec_z0` e o α da camada
  reestimados pela calibração sem rótulo que o método já tem (`calibrate_alpha`, critério de Tamura, em 32 hologramas
  do split de **validação** gravado a 0,7 mm); os pesos não mudam. A faixa de busca de hoje começa em 0,944 mm e não
  contém 0,7 mm: para estes conjuntos o limite inferior é estendido, com o mesmo passo relativo, antes de rodar. O
  padrão do código não muda.

### O que fica igual ao base e o que muda no conjunto de 1,0 mm

- Igual: fonte (385 nm, 10 nm, pinhole de 100 µm a 15 cm), feixe, poeira (densidades, planos a +1,0 mm e −0,2 mm da
  amostra, janela do sensor a 0,5 mm dos pixels: os três continuam do lado certo com z₀ = 1,0 mm), sensor (PRNU, poço
  de 6000 e⁻, exposição, ruído de leitura, 8 bits), material das letras, rotações, fontes, 5000 imagens em 50 sessões
  de 100, splits por sessão, protocolo open-set e classes de cada repetição.
- Muda: z₀ (1,0 mm), tamanho das letras (fator 0,22792), gravação sobreamostrada, margem e alcance do campo simulado
  (o padrão se espalha menos em pixels; a margem é conferida por medida).
- **Em aberto, perguntado ao orientador antes de gravar:** quantas letras por janela e o espalhamento de profundidade
  por objeto (ver P1).
