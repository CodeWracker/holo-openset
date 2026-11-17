# TODO: resolução da fonte, reposicionamento do paper e argumento de velocidade

Arquivo de plano e progresso desta etapa. **Se você perdeu o contexto, leia este arquivo inteiro e depois
`PROTOCOLO.md` (a instrução do orientador, na íntegra) antes de qualquer coisa.** Atualizado e commitado a cada
passo. Comandos e resultados ficam em `CADERNO.md`. A etapa anterior (distância/autofocus e integração no paper)
está fechada e documentada em `docs/exp_distancia/` (`TODO.md`, `RELATORIO.md`, cadernos).

## 1. O pedido (2026-11-14, à tarde)

Instrução inteira em `PROTOCOLO.md`. Resumo: três frentes, nesta ordem.

- **A. Experimento novo:** processar na resolução que a fonte permite (reduzir a imagem b × b; b sai da física, não
  do teste). Hipóteses H5 (tempo: pipeline inteiro em imagens b² vezes menores sem perder F1) e H5b (robustez sob
  `fullwell_500` e `beam_narrow`). Ordem: (1) piloto em r1, só janelas, b ∈ {1, 2, 4, 8}, fluxos `raw`, `prop`,
  `rec_z0`, conjuntos base, `fullwell_500`, `beam_narrow` → **Checkpoint P1**; (2) cinco repetições, quadros
  inteiros, conjuntos pequenos, pergunta A.4 (detectar no bruto ou no refocado); (3) sessão única de tempo →
  **Checkpoint P2**.
- **B. Reescrever o paper** com o enquadramento novo (camada autocalibrada como manchete; sem promessa de
  velocidade), **só depois do P2**, num branch do repositório LaTeX, entregando o diff, sem merge.
- **C. Parágrafo crítico** sobre o argumento de velocidade da literatura, com levantamento obrigatório antes
  (strings S1–S7 no Scopus e na ScienceDirect, .RIS, triagem; frase exata e página de cada trabalho citado).

Palavras do orientador que mandam em tudo: "**desta vez, cada checkpoint precisa da minha aprovação explícita** antes
da etapa seguinte" e "Qualquer dúvida, pergunte antes de decidir".

Critério pré-registrado (A.6): com o b da física, F1 open-set a até 0,01 da resolução cheia **e** tempo fim a fim
pelo menos 3× menor em GPU e em CPU, no mesmo run, com a leitura incluída. H5b: F1 em `fullwell_500` e `beam_narrow`
igual ou maior que o da resolução cheia em pelo menos 4 de 5 repetições. Se o F1 cair mais que 0,01: curva
F1 × b × tempo e ponto de equilíbrio.

## 2. Regras que valem o tempo todo

- Modo de trabalho pedido pelo orientador: subagentes Opus 5.5 (effort high) executam; o modelo principal planeja,
  revisa e garante a consistência. Um único escritor por arquivo de caderno.
- **Parar em cada checkpoint (P1, P2) e só seguir com aprovação explícita do orientador.** Notificação de subagente
  ou de sistema não é aprovação.
- Resultados novos só em `results_exp_resolucao/` (`HOLO_RESULTS`); nada em `results/` nem `expected/`; conjuntos
  reduzidos como conjuntos novos em `data/` (nada sobrescrito); modelos novos fora de `models/`.
- Escolhas só na validação; pré-registro datado no caderno antes de rodar o teste; nenhum fluxo/conjunto novo no
  teste sem registrar antes; não descartar repetição "estranha"; tempos de runs diferentes nunca na mesma tabela;
  toda tabela de tempo com a coluna fim a fim e, aqui, com a leitura medida.
- Números no texto do paper só por macro. Nomes internos fora do texto do paper. Legenda explica cada painel.
- Commits: sem linha de atribuição nenhuma; um por unidade lógica; mensagens em inglês. **Nunca dar push nem merge
  sem confirmação do orientador** (GitHub e Overleaf).
- DGX: poucas threads por processo, total de threads prontas < ~64, jobs longos em `tmux` com checkpoint, subir
  jobs aos poucos, nada em `/tmp`.
- `pytest` e `reproduce check` com `env -u HOLO_RESULTS` têm de continuar verdes (37 testes, 13/13) a cada commit de
  código.

## 3. Onde as coisas estão

- Código: `/home/jovyan/compartilhado/ralph/openset-microscopy/holo-openset`, branch **`exp/resolucao-fonte`**,
  criado de `exp/distancia-autofocus` (`4e44f3a`), que continua sem merge em `main` e sem push (decisão pendente do
  orientador). Documentos desta etapa: `docs/exp_resolucao/{PROTOCOLO,TODO,CADERNO}.md`.
- Paper: `../latex-openset-microscopy`, `main` em `b17b8df`, 2 commits à frente do Overleaf, sem push.
- Compilar o paper: `XDG_CACHE_HOME=/home/jovyan/privado/.persist/.cache /home/jovyan/privado/.persist/bin/tectonic
  --keep-logs -o <dir no scratchpad> main.tex`.

## 4. Decisões de desenho (minhas, tomadas antes de rodar; o orientador pode reverter)

- R1. Branch novo a partir do branch do estudo anterior, porque o experimento usa `rec_afc`, os conjuntos de
  distância e os geradores integrados.
- R2. Pastas: `results_exp_resolucao/` (resultados), `models_exp_resolucao/` (modelos), conjuntos
  `data/realistic_b{2,4,8}` e variantes reduzidas em pasta própria, `logs/exp_resolucao/`,
  `scripts/exp_resolucao/env.sh`.
- R3. A imagem reduzida é guardada em **uint8 depois de arredondar** (o protocolo deixa escolher e pede para anotar):
  é o que uma câmera de 8 bits com binning entregaria, é o caso desfavorável para o pipeline reduzido (o
  arredondamento joga fora parte do ganho de ruído da média) e não muda nenhum caminho do código. O blank frame
  reduzido fica em float32, como o original. Se o F1 cair em b = 4, a versão float32 entra como checagem, escolhida
  na validação.
- R4. Piloto exatamente como o protocolo define: r1, janelas, caixas anotadas, b ∈ {1, 2, 4, 8}, `raw`, `prop`,
  `rec_z0`, base + `fullwell_500` + `beam_narrow`, crop 64 × 64, mesma receita de treino (cenas auxiliares de r1
  reduzidas do mesmo jeito).
- R5. b = 1 é o modelo de r1 do paper (sem retreino); o caminho novo do código com b = 1 tem de reproduzir os números
  de r1 que já existem (sanidade).
- R6. O piloto mostra F1 de teste porque b é fixado antes pela física (A.2) e registrado no caderno; qualquer outra
  escolha (tamanho do crop, tipo de armazenamento, detector) é feita na validação.
- R7. Antes de qualquer frase sobre enrollment: diferença pareada por repetição de `prop` menos cada fluxo de
  reconstrução (pedido na seção de enquadramento); entra no relatório do P1.

## 4a. MUDANÇA DE ORDEM (2026-11-14, ≈ 13:15): a parte A está SUSPENSA até o Checkpoint Z

Instrução nova do orientador, na íntegra em `PROTOCOLO_Z.md`: "**segura a parte A (redução) até fecharmos isto.** O
resto (parte C, Related Work, e o teste pareado do enrollment) pode andar em paralelo." Motivo: o z = 19,25 mm do
simulador vem de ler o "z = 50k" da rotina da bancada como 50 000 λ; o artigo de 2015 diz só que a distância é "as
small as possible" e usa 49 quadros com super-resolução de pixel, o que pede z pequeno; e o b da parte A depende
inteiramente de z (a poucos mm o sensor subamostra o holograma e a redução não se aplica).

**Checkpoint Z** (precisa da aprovação explícita dele antes de A andar): mandar (1) a unidade do z no código, com o
trecho (gerador original "da Manu" e `sim/physics.py`); (2) a tabela do levantamento de 8–15 bancadas lensless com
LED + pinhole + CMOS de 1–2 µm (referência, λ e banda, pinhole, L, z, pixel, super-resolução, resolução), só com
valores escritos no artigo e com página; (3) a proposta de configuração (z e, se for o caso, D e L) com as
referências e a conferência de coerência do E(f) com as resoluções reportadas; (4) as consequências sem regravar
nada (E(f) e b_max da proposta; base a 19,25 mm como "configuração distante"; `small_near` mais perto do realista;
se a parte A vale e com que b; o que teria de ser regravado e retreinado). **A decisão de regravar é dele.**

Fatos confirmados pelo prof. Sobieranski, para o texto (parte B): sem inclinação na bancada (só deformidades locais
= o spread de profundidade que já simulamos; o experimento de inclinação vira uma frase); brilho da fonte e shutter
ajustados à mão por sessão (justifica blank frame e perfil de feixe por sessão); na super-resolução a fonte era
deslocada à mão para cada um dos 49 quadros; o tempo de processamento só pesa no uso com quadro único: o sensor
entrega 3,2 quadros/s (312 ms por quadro), a GPU acompanha (≈ 0,2 s por quadro) e um core de CPU não (≈ 24 s);
não haverá hologramas reais, e a limitação continua no paper.

Estado da parte A no momento da suspensão (13:18): o subagente "piloto" tinha feito e commitado o teste pareado de
enrollment (`88b5ed9`), o b pela física (`c7e87e3`, `6781b8c`: b = 4 no base pelos dois métodos; b = 1 a 2 mm) e o
comando de redução (`eb5dedf`), e estava construindo os conjuntos reduzidos (`tmux res_build`). Nenhum treino e
nenhuma avaliação de teste de conjunto reduzido. Mandei parar e passar para as tarefas Z1–Z3.

## 4b. ATUALIZAÇÃO (2026-11-14, ≈ 13:50): z é da ordem de 1 mm

Palavras do orientador (na íntegra no fim de `PROTOCOLO_Z.md`): o prof. Sobieranski confirmou que a lamínula fica
muito próxima do sensor, só não encosta porque o sensor aquece; "z é da ordem de 1 mm, não 19,25 mm". Consequências:

- O levantamento passa a ter como foco **fechar esse número** (lamínula + vidro do sensor + folga), com referências.
- **A parte A (redução 4×) não se aplica a essa distância (b_max = 1) e fica suspensa.**
- A proposta do Checkpoint Z inclui também: o que muda se o conjunto base for regravado na distância certa; quais
  conclusões precisam ser checadas de novo (principalmente o espalhamento do padrão para fora do crop e a vantagem da
  camada sobre os crops); o custo de regravar e retreinar. `small_near` (2 mm) já dá uma prévia.
- Anotar: o aquecimento do sensor torna plausível o drift de z durante a sessão (`walk_05`).
- A decisão de regravar continua sendo dele.

## 4c. SEGUNDA ATUALIZAÇÃO (2026-11-14, ≈ 14:10): como contar a história, e mais três itens no Checkpoint Z

Na íntegra no fim de `PROTOCOLO_Z.md`. Linha do paper: **a simulação faz parte do método, porque os valores dos
parâmetros mudam as conclusões**; todos os parâmetros são fixados e declarados, cada um com referência. Duas
evidências a apresentar bem: (1) idealizado × bancada (Tabela 12: Wiener de melhor, 0,988, a pior, 0,910; ranking
inverte; modelo treinado no idealizado não transfere, 0,358) — "só precisa de uma figura clara"; (2) a distância
amostra–sensor: a 19,25 mm a fonte apaga as franjas finas e a redução 4× funcionaria; a ≈ 1 mm não — "um parâmetro
decidiu se havia ganho computacional".

O Checkpoint Z passa a levar também:
- **tabela de todos os parâmetros do simulador**, com valor e fonte de cada um (artigo, datasheet ou suposição nossa);
- **comparação base (19,25 mm) × `small_near` (2 mm)**: F1 e rejeição de crops, `prop` e `rec_z0`, e quanto o padrão
  vaza para fora do crop;
- **uma figura simples "o que muda com o setup"**, que sirva para o paper e para o resumo ao prof. Sobieranski.

Confirmado pelo prof. Sobieranski: sem inclinação (só deformidades locais pequenas); brilho por shutter e ganho
analógico ajustados à mão; LED UV de 385 nm (M385L2, 10 nm FWHM no datasheet).

Tom do texto (vale para B e C): o gerador da Manu foi "**evoluído**", não "estava errado"; o CBMS 2024 é trabalho
nosso que **corrigimos com medição**.

## 5. Plano

Estado: `[ ]` a fazer, `[~]` em andamento, `[x]` feito (com commit), `[!]` bloqueado/aguardando o orientador.

### Fase Z: definir um z razoável (vem ANTES de A; ver 4a e `PROTOCOLO_Z.md`)

- [x] Z1. (feito, caderno e `07d513e`) Unidade do z no código (gerador original e `sim/physics.py`), com trecho, no caderno — subagente "piloto".
- [x] Z2. (feito, `results_exp_resolucao/envelope_z.csv`) Refazer a tabela do orientador (z = 19,25; 5; 2; 1 mm: borrão, corte, b_max) e explicar as diferenças
      (ele tem 278 ciclos/mm a 2 mm; o nosso modelo deu 266) — subagente "piloto".
- [x] Z3. (feito: `holo_openset/sim/envelope.py`, `scripts/exp_resolucao/envelope_table.py --configs <csv> --out <csv>`)
      Ferramenta E(f)/b_max para qualquer configuração (CSV de configurações → tabela) — subagente "piloto".
- [x] Z4. (feito, `7a5dcf6`: `LEVANTAMENTO_Z.md`, 710 linhas; `results_exp_resolucao/envelope_candidates.csv`)
      Levantamento de 8–15 bancadas lensless, valores com página → `docs/exp_resolucao/LEVANTAMENTO_Z.md`;
      PDFs em `../referencias/z/` (fora do git) — subagente "levantamento-z". Inclui o suplemento do artigo de 2015
      (Eq. S3: unidade do "k").
- [x] Z6. (feito: `2cf9d00`…`9b93a95`) Consequências (subagente "piloto", sem regravar conjunto nem treinar): prévia com `small_near`;
      fração do padrão dentro do crop contra z para os tamanhos de letra do base e dos pequenos; se o simulador grava
      direito a ≈ 1 mm (amostragem, faixa do α, spread de profundidade relativo, faixas do autofocus); inventário e
      custo de regravar e retreinar; configurações candidatas na ferramenta do envelope.
- [x] Z7. (feito: `7ca6da0`, `PARAMETROS.md`: 45 parâmetros; 6 artigo, 2 datasheet, 2 comunicação pessoal, 35
      suposição nossa) Tabela de todos os parâmetros do simulador com valor e fonte (`docs/exp_resolucao/PARAMETROS.md` + csv) —
      subagente "levantamento-z" (retomado), que leu o artigo de 2015, o suplemento e as folhas de dados.
- [x] Z8. (feito: `6d2914f`, `results_exp_resolucao/setup_comparison.csv`, `img/fig_setup.{pdf,png}`) Comparação base × `small_near` (métricas + vazamento do padrão) e a figura "o que muda com o setup" —
      subagente "piloto", junto com Z6.
- [x] Z5. (feito: `docs/exp_resolucao/CHECKPOINT_Z.md`, `18d67a3`) Proposta de configuração + coerência com as resoluções reportadas + consequências (eu, com Z3 e Z4).
- [x] **Checkpoint Z**: entregue (`18d67a3`) e **aprovado para o piloto** em 2026-11-14, ≈ 15:40
      (`PROTOCOLO_PILOTO_1MM.md`, na íntegra). A parte A (redução) continua sem sentido a ≈ 1 mm (b_max = 1).

### Fase P: piloto na distância certa (1,0 mm) — EM ANDAMENTO (ver `PROTOCOLO_PILOTO_1MM.md`, `CADERNO_PILOTO_1MM.md`)

Escolhas do orientador (fixadas antes de rodar): z₀ = 1,0 mm (0,7 mm só como robustez, com os modelos de 1,0 mm, sem
retreinar); letras com o mesmo N_F do base (fator 0,22792: fontes 15,95–26,89 px, caixas ≈ 13–23,5 px = 22–39 µm);
gravação sobreamostrada com teste de convergência 2× contra 4×; critério da tese: em ≥ 4 de 5 repetições, prop − crops
≥ 0,10 em F1 **e** ≥ 0,30 em rejeição das não vistas; primeiro só r1 (`raw`, `prop`, `rec_z0`); **checkpoint com ele
antes das 5 repetições**; no paper o base vira "a geometria do CBMS 2024" e os conjuntos são apresentados pelo N_F.
Escolhas minhas (ele pode reverter; estão no P0 do caderno do piloto): tolerância da convergência = 1 % do rms do
padrão, a 1,0 e a 0,7 mm, grava-se com o menor s tal que (s, 2s) passa; robustez a 0,7 mm em duas leituras, (a) como
está e (b) distância e α recalibrados sem rótulo em 32 hologramas de validação a 0,7 mm, pesos intactos; nome do
conjunto `bench_1mm`; 5000 imagens em 50 sessões, como os conjuntos pequenos; poeira, fonte, feixe e sensor iguais ao
base.

- [x] P0. Pré-registro no caderno do piloto (`15bfea7`), antes de qualquer código.
- [x] P1. Respostas do orientador (≈ 16:25, pelo diálogo): **8 letras por janela** (como no base e no `small_near`) e
      **profundidade 2,6 µm rms (máx. 7,8), com 50 µm como robustez sem retreinar**. Registrado no caderno do piloto,
      entrada P1 (`6c90557`), junto com as minhas decisões: s = 4, margem 394 / alcance 233, receita de treino do
      paper sem mudança, leitura (b) literal como principal e a variante por razão ao lado, poeira coincidente a
      0,7 mm declarada.
- [x] P2. Subagente "simulador": S1–S3 feitos (`c1092ff`, `629424d`, `77b29f7`, `28539f7`, `2c9e3d4`): gravador
      sobreamostrado (`Physics.oversample`; s = 1 bit a bit igual), cena em unidades físicas (`FresnelLayout`,
      raster mestre 16×), convergência: (2, 4) falha (1,04–1,78 %), (4, 8) passa (≤ 0,46 %) → **s = 4**;
      `scripts/exp_resolucao/pilot_1mm.sh <GPU> <passo>`; pytest 54, `reproduce check` 13/13 (conferi eu). Revisei o
      diff de `sim/physics.py`: achei que a poeira fora do plano da amostra era pré-propagada só no comprimento de
      onda central (a 1 mm isso deixa a poeira a 2 mm nítida demais) e mandei corrigir no caminho fino (R1).
- [x] P3. (feito, `2eb3fec`…`1f2680d`; caderno do piloto R1–R5) Correção do plano de poeira (cada plano propaga
      z + profundidade em cada comprimento de onda; mudou as gravações em 1–5 % do padrão; (4, 8) continua
      passando); conferência cruzada com `fine_recording` (7e-15); **piloto em r1 rodado**: `data/bench_1mm`
      (5000 imagens, 8,7 GB), `data/bench_1mm_robust/{z07,z07_val,depth50}`, modelos em `models_exp_resolucao/`,
      resultados em `results_exp_resolucao/eval/bench_1mm/*_r1.json` e `robustness_bench_1mm.csv`.
      **r1 (teste): raw 0,928 / 0,622; prop 0,977 / 0,995; rec_z0 0,977 / 1,000 (F1 / rejeição). prop − raw: +0,049
      F1 (abaixo de 0,10) e +0,373 rejeição (acima de 0,30).** Robustez: 0,7 mm como está → prop e rec_z0 rejeitam
      tudo (F1 0,015), raw 0,897; recalibrado sem rótulo: prop 0,545 (literal) / 0,913 (por razão), rec_z0 0,956 /
      0,958; profundidade 50 µm → prop 0,773, rec_z0 0,801, raw 0,929. α calibrado 0,9999 mm, depois do treino
      0,9758 mm (−2,4 %). Conferi os números nos arquivos, pytest 56, `reproduce check` 13/13 (com `HOLO_RESULTS` e
      `HOLO_MODELS` fora do ambiente).
- [x] P4. (feito) Vazamento no conjunto novo: 61 / 55 / 39 % (p5 / p50 / p95), igual ao do base (59 / 51 / 39 %);
      `results_exp_resolucao/sets_by_fresnel.csv` (conjuntos pelo N_F, média de 5 e r1).
- [x] P5. Checkpoint do piloto entregue (17:30, `CHECKPOINT_PILOTO.md`, `2e095eb`) e respondido às ≈ 17:38:
      **"1 - ok; 2 - faz os 2 antes de reescrever; 3 - ok"** (na íntegra no fim de `PROTOCOLO_PILOTO_1MM.md`).
- [~] P6. Pré-registro P2 no caderno do piloto (17:40) e execução, com dois subagentes lançados ≈ 17:50:
      **"repeticoes"** (o do simulador, retomado): A = r2–r5 no `bench_1mm` com as linhas de robustez; referência do
      controle B (`realistic`, `--no-aux`, r1, modelos/resultados nas pastas da etapa); D = `bench_1mm_depth50`
      (todos os splits com 50 / 150 µm) treinado e avaliado em r1, mais as avaliações cruzadas.
      **"controles"** (novo): B = `base_newrec` (cena física, fator 1, 19,25 mm, s = 2) e C = `bench_1mm_dense`
      (as cenas do `bench_1mm` + letras não anotadas até ≈ 154 por janela), r1; script próprio
      (`scripts/exp_resolucao/controls_1mm.sh`), sem tocar em `pilot_1mm.sh`.
      Leituras fixadas no P2: critério do orientador nas cinco repetições; controles lidos pelos crops, "mais perto
      de R_ant ou de R_pil" nas duas métricas.
      **18:58 — "repeticoes" terminou e eu conferi nos JSON** (`eval/bench_1mm/*_r?.json`, `eval/realistic/*_r1.json`,
      `eval/bench_1mm_depth50/*_r1.json`):
      - **A, critério do orientador: 0 de 5 repetições cumprem as duas condições** (F1 ≥ 0,10: 0 de 5; rejeição
        ≥ 0,30: 1 de 5, só r1). Médias de 5: raw 0,938 / 0,730; prop 0,977 / 0,997; rec_z0 0,979 / 0,998; prop − raw
        +0,039 F1 (0,031 a 0,049) e +0,268 rejeição (0,170 a 0,373). Tabelas: `pilot_five_reps{,_robustness,_alpha}.csv`.
        Robustez média de 5: 0,7 mm como está prop/rec 0,015; recalibrado por razão prop 0,914, rec 0,964; 50 µm como
        está prop 0,784, rec 0,823, raw 0,939.
      - **Referência do controle B** (`realistic`, `--no-aux`, r1): raw 0,774 / 0,073 (R_ant); prop 0,959 / 0,869;
        rec_z0 0,956 / 0,862. Tirar as cenas auxiliares quase não muda o base.
      - **D** (treinado com 50 µm, r1): testado em 50 µm prop 0,977 / 0,998, rec_z0 0,975 / 0,994, raw 0,924 / 0,605;
        testado em 2,6 µm prop 0,984, rec_z0 0,976. A perda de 0,2 de F1 era do treino com amostra plana.
      **20:42 — "controles" terminou e eu conferi nos JSON** (`eval/{base_newrec,bench_1mm_dense}/*_r1.json`,
      `controls.csv`, `controls_reading.json`); entrada P3 do caderno do piloto (`bee10e2`):
      - **B (código):** `base_newrec` crops 0,763 / 0,061 (camada 0,960 / 0,867; rec 0,957 / 0,840): mais perto de
        R_ant nas duas → **o código novo reproduz o antigo.** Desvio declarado: fator mestre 4 (piloto 16), s = 2.
      - **C (vizinhança):** `bench_1mm_dense` (as mesmas 40 309 letras anotadas + enchimento até 154 por janela,
        10,5 % de área coberta) crops 0,796 / 0,080; camada 0,960 / 0,899; rec 0,968 / 0,952: mais perto de R_ant nas
        duas → **a vizinhança explica a melhora dos crops.** Pareado denso − esparso: crops −0,133 / −0,543; camada
        −0,017 / −0,096; rec −0,009 / −0,048.
      pytest 64, `reproduce check` 13/13; pastas do paper intactas (só `results/data_summary.json` reescrito com o
      mesmo conteúdo pelo `reproduce check`).
- [x] P6 concluído. Relatório completo: `docs/exp_resolucao/RELATORIO_PILOTO_1MM.md` (PDF no scratchpad,
      `entrega/relatorio_piloto_1mm.pdf`), enviado ao orientador às 20:43.
- [ ] P7. **PARADO, esperando o orientador.** Decisões pedidas no relatório (seção 9 depois da atualização das
      21:25): (1) como a tese muda (minha recomendação: condicionada à densidade; amostra densa → o crop falha e a
      camada recupera, a 1,0 como a 19,25 mm; esparsa → o crop reconhece as conhecidas e a vantagem fica na rejeição
      das não vistas, 0,997 contra 0,730); (2) cinco repetições no conjunto denso (4 × ≈ 8 min); (3) gravar os dois
      níveis intermediários de densidade em r1 (15 e 69 letras por janela; ≈ 70 min de gravação no total) e medir o
      diâmetro efetivo do nosso holograma; (4) começar a parte B. **Nada disso roda sem a resposta dele; qualquer
      rodada nova pede pré-registro no caderno do piloto antes.**
      **Respondido às ≈ 21:20 (só o antigo item 4): "Pode escolher, ele não lembra. E se essa pergunta tava no
      relatório, atualiza ele"** (na íntegra em `PROTOCOLO_PILOTO_1MM.md`). Feito: entrada P4 do caderno do piloto
      (`2f8ccaf`): a densidade fica suposição nossa e vira eixo, 7 a 135 objetos/mm² (8 a 154 letras por janela),
      com dois níveis intermediários nos pontos de Seo et al. 2009 (13 e 60 por mm² = 15 e 69 letras por janela);
      relatório atualizado (seção 8 nova; a pergunta ao professor saiu das decisões) e reenviado; nota no fim de
      `PARAMETROS.md`.
      **Para as partes B e C:** Seo et al. 2009 (Lab Chip, 10.1039/b813943a, seção "Discussions") já relata que o
      reconhecimento sobre o holograma cru, sem reconstrução, perde acurácia quando os hologramas se sobrepõem
      (fórmula da razão de sobreposição; 10 % a 671 células/µL, ≥ 37 % a 3000 células/µL com canal de 20 µm). É
      precedente do que os controles mostraram: citar. Isikman et al. 2012 (seção III.A): com reconstrução, até
      0,4 milhão de células/µL. Textos em `../referencias/z/{seo2009,isi2012}/efetch.xml`.
- [x] C-extra. (feito, `bed038c`) CBMS 2024 lido inteiro; entrada [11] de `LEVANTAMENTO_C.md` atualizada. O artigo
      afirma o custo da reconstrução em várias frases, usa "iterative" uma vez (p. 365), **não mede** tempo de
      reconstrução nem de inferência (só tempo de treino no Colab, T4, p. 368), é detecção com YOLOv5/v8/v9 em
      conjunto fechado de 26 letras (mAP50 0,986 do v8 na Tabela I; os 96,8 % de precisão só aparecem no resumo), sem
      conjunto de teste e sem baseline de reconstrução; os próprios autores adiam o tempo real (p. 369). Para a parte
      B: `02-related.tex` descreve [11] como classificação (é detecção); a leitura "z = 50k = 5·10⁴ λ" é nossa (pelo
      código); a descrição do conjunto público em `03b-bench.tex` não se confere pelo texto do artigo, só pelo
      código do gerador. Tom: trabalho nosso, corrigido por medição.

### Fase Q: enquadramento novo, curva de densidade, distância e escrita (instrução de 2026-11-15, `PROTOCOLO_CURVA.md`)

**Se você perdeu o contexto: leia `PROTOCOLO_CURVA.md` e `CADERNO_CURVA.md` (Q0, Q1, …) antes de qualquer coisa.**
Tudo desta fase foi aprovado para começar. Não há checkpoint entre "r1 em todos os níveis" e "cinco repetições onde
as curvas se separam": a regra está no Q0 e é aplicada mecanicamente. Entrega final: relatório da curva + diff do
LaTeX (branch `rewrite/inversion`), sem merge e sem push.

Enquadramento (palavras dele, resumidas): a tese é uma **inversão da tese do CBMS 2024**, contada com medição:
(1) open-set em holografia sem lente, protocolo estrito; (2) o caminho sem reconstrução funciona em conjunto fechado
e falha no open-set (esparso: rejeição 0,730 contra 0,997, critério não cumprido ali; denso: 0,08); **mecanismo = o
padrão das vizinhas entrando no crop, não o vazamento do padrão da própria letra** (corrigir em todo o texto,
inclusive na hipótese); Seo 2009 é precedente; (3) o que resolve é uma etapa de propagação (a camada ou a
reconstrução calibrada), ≈ 1 ms; o argumento de tempo não se sustenta, começando pelo nosso de 2024; (4) **a
simulação idealizada esconde tudo isso**: seção dedicada, que aparece no abstract e nas contribuições.

Executores (Opus, high), lançados às ≈ 08:15 (IDs internos em `scratchpad/agentes.md`, fora do git):

- [x] Q-a. (feito e conferido por mim nos json) **Cinco repetições no denso do piloto** (`dense_five_reps.csv`): crops
      0,793 / 0,096; camada 0,965 / 0,934; reconstrução 0,970 / 0,967 (F1 / rejeição, média de 5). Camada − crops
      +0,173 / +0,838; limiares do P0: **5 de 5** nos dois. Reconstrução − camada +0,005 / +0,032.
      **Diâmetro efetivo** (`hologram_diameter_summary.json`): D_rms convergiu; D = 111,8 µm (3,8 × o lado da
      letra); sobreposição 0,24 / 0,40 / 0,905 / 0,995 / 1,000 nos cinco níveis.
- [x] Q-c. **Lei de profundidade: o orientador escolheu "Uniforme nos 50 µm"** (≈ 08:45; Q1 do `CADERNO_CURVA.md`,
      `9315c0c`): ±25 µm, profundidade = 25 µm · erf(g/√2). A lei larga (`bench_1mm_depth50`) vira teste de estresse.
- [x] Q-b. (feita às 11:34 e conferida por mim: refiz a tabela e as regras do Q0 a partir dos 75 json; 0 diferenças
      contra `density_curve.csv`; pytest 72, `reproduce check` 13/13) **Curva de densidade, família padrão, cinco
      repetições em todos os níveis** (a regra "se separam" deu sim nos quatro níveis em r1). F1 / rejeição, média
      de 5, níveis 7 / 13 / 60 / 135 / 300 por mm² (sobreposição 0,242 / 0,405 / 0,907 / 0,995 / 1,000):
      crops 0,937/0,714; 0,922/0,612; 0,855/0,260; 0,789/0,089; 0,668/0,031 (acerto fechado 0,976 → 0,770);
      camada 0,975/0,983; 0,974/0,993; 0,972/0,975; 0,957/0,864; 0,942/0,743;
      reconstrução 0,977/0,996; 0,978/0,993; 0,973/0,967; 0,972/0,976; 0,960/0,895.
      **Regra "caiu" (≥ 4 de 5):** crops em rejeição a partir de 60/mm² e em F1 a partir de 135/mm²; **camada e
      reconstrução não caem em nenhum nível** (maior queda da camada, no 343: −0,033 F1, −0,239 rejeição; por
      repetição 0,135–0,292). Descritivo: nos dois níveis mais densos a reconstrução rejeita mais que a camada em
      5 de 5 (+0,111, +0,152). Pelo Q0: reportar que a camada não caiu e **não gravar nível novo sem perguntar**.
      **Conjuntos antigos no eixo:** geometria de CBMS 2024 D = 447 µm, sobreposição 0,988 (π D² σ 4,43): cai na
      curva; letras pequenas a 2 mm D = 157,5 µm, sobreposição 0,42, crops 0,793/0,153: **não cai na curva**
      (previsão do Q1 falha ali; o executor atribuiu a cenas auxiliares, mas `pipeline.py:107` treina os conjuntos
      pequenos com `--no-aux`: a explicação dele está errada e não há explicação). `curve_alpha.csv`: α calibrado
      0,994–1,000 mm; o treino desloca −3,2 % no esparso e −1,6 % no mais denso.
- [x] Q-d1. (feito e conferido) **Distância com os modelos do piloto** (`distance_tests.csv`): a 0,9 / 1,1 mm sem
      recalibrar a camada cai a 0,221 / 0,081 e a reconstrução a 0,138 / 0,160 de F1 (rejeitam tudo); crops 0,948 /
      0,925. Recalibrado por razão: camada 0,929 / 0,915; reconstrução 0,979 / 0,976. Reconstrução − camada
      recalibradas: +0,050 / +0,051 / +0,061 a 0,7 / 0,9 / 1,1 mm (15 de 15 positivas). Distância achada a menos de
      0,35 %.
- [x] Q-d2. (feito às 10:00 e conferido por mim nas linhas por repetição) **Distância e profundidade com os cinco
      modelos do nível 8 da família padrão** (`distance_tests_u50.csv`, `depth_tests.csv`; caderno do executor, D2).
      Nível 8 da família padrão a 1,0 mm (F1 / rejeição, média de 5): crops 0,937 / 0,714; camada 0,975 / 0,983
      (mínimo de rejeição 0,937, em r3); reconstrução 0,977 / 0,996. Camada − crops: +0,038 F1, +0,269 rejeição.
      **Distância, sem recalibrar**, 0,9 / 1,1 mm: camada 0,426 / 0,289; reconstrução 0,249 / 0,303 (rejeição
      ≥ 0,993; acerto das conhecidas 0,15–0,29); crops 0,946 / 0,923. **Recalibrado por razão**: camada 0,919 /
      0,932 / 0,930 e reconstrução 0,964 / 0,978 / 0,975 a 0,7 / 0,9 / 1,1 mm; reconstrução − camada +0,045 /
      +0,046 / +0,044 (15 de 15 positivas, 0,034–0,058); a 1,0 mm empatam (+0,002). Literal: camada 0,67–0,73.
      Distância achada por razão a −0,78 % / −0,38 % / −0,20 % da verdadeira (grade com passo de 0,27 %).
      **Profundidade (F1 da camada / reconstrução):** treino plano → teste padrão 0,958 / 0,971, isto é, −0,019 /
      −0,008 contra o teste plano (5 de 5 negativas); treino padrão → teste plano 0,979 / 0,976 (nada perde);
      treino padrão → lei larga 0,858 / 0,865 (−0,116 / −0,112); treino plano → lei larga 0,784 / 0,823 (o −0,19
      do piloto). Crops não mudam com a profundidade (|Δ| ≤ 0,004). **Consequência para o texto: na lei padrão
      (canal de 50 µm) treinar com amostra plana custa 0,02, não 0,2; o 0,2 é da lei larga (teste de estresse).
      Dizer isso ao orientador: a frase dele "treino com amostra plana perde 0,2 de F1 em amostra com 50 µm"
      vale para a lei larga, não para a que ele escolheu.**
- [x] Q-w1 / Q-w2, primeira passada (feita): seção `06b-simulation.tex` (figura de 5 painéis, tabela de 49 linhas,
      228 macros `\Res…` por `scripts/exp_resolucao/paper_resolucao.py` e `fig_simulation.py`), introdução nova,
      mecanismo corrigido em 03/04/06; `02-related.tex` inteiro, 25 entradas novas no bib, complemento do
      levantamento em OpenAlex e Semantic Scholar (918 trabalhos, 56 incluídos; Scopus/ScienceDirect NÃO rodados),
      `TEXTO_C_PROPOSTAS.md`. **Juntei os dois em `rewrite/inversion`** (worktree `../latex-wt-inversion`, `24f1303`;
      compila, 39 páginas). Li os três textos.
- [x] Q-w3. (feito ≈ 09:35 e revisado; `rewrite/inversion` em `192eca5`, código `6734984`) **Segunda passada do
      escritor da simulação, no worktree de integração:** as duas geometrias coerentes em 03b/03; frase do mecanismo
      em 07/08/abstract; Sobieranski é coautor (saiu "personal communication"; virou "the bench (not reported in the
      article)"); ajustes da minha revisão; subseção 8.6 da distância com macros `\ResDist…`. Pontos que ficaram
      para a terceira passada: `07-discussion` limitação (i) ainda chama 19,25 mm de distância da bancada; macro do
      acerto das conhecidas na 8.6; `05-protocol` diz "bit by bit on the same build" (não mexi; avisar).
- [x] Q-w4. (feita ≈ 10:13 e revisada por mim: li 8.4–8.6, a introdução, a limitação (i), a tabela de profundidade
      e a figura) **Terceira passada, parte 1 (o que não depende da curva):** o gerador toma a família padrão
      (`curve_u50_L*`) como a família de 1 mm do paper (esparso = `curve_u50_L008`; denso = `curve_u50_L154` quando
      existir; até lá o denso do piloto com `\ResDenseFallback`, um `\todo` visível); `\ResPilot…` para a margem
      registrada; 8.5 (profundidade) final com `depth_tests.csv` e Tabela 14 gerada (`tab_depth.tex`); 8.6
      (distância) com os modelos padrão, acerto das conhecidas, 15 de 15, empate a 1,0 mm; limitação (i) com as
      duas geometrias; painel (e) com as três leis; macros `\ResCurve…`, painel (d) no eixo do Q1 e
      `fig_density_curve.py` prontos para quando `density_curve.csv` existir. Código `9294972`, `78feeb1`; LaTeX
      `9867457`, `0a297fa`, `93ded85`, `18e289e` (40 páginas, sem referência indefinida).
      Pendências dela: (1) `\ResAlphaZCalibMm` sai por ora do `z_ref` dos json de recalibração (validação); pedi ao
      executor da densidade um `curve_alpha.csv` (α calibrado e treinado por nível e repetição) e o gerador deve
      passar a usá-lo; a frase "training moved the scalar by …" saiu da 8.6 até lá; (2) Fresnel e fração fora do
      crop continuam medidos nas letras do piloto (mesmas letras; dizer se necessário).
- [x] Q-w5. (feita 11:37–11:54 e revisada por mim: li abstract, 06 inteiro, 8.4, discussão, conclusão e a prosa
      nova do método; conferi a calibração do α contra `train.calibrate_alpha`) **Terceira passada, parte 2 e
      fecho:** gerador com a família padrão completa (denso = 135/mm²; α de `curve_alpha.csv`; `tab_curve.tex`;
      `fig_density_curve`; conjuntos antigos no eixo); 8.4 final com a curva; resultados reescritos para as cinco
      RQ (método proposto = camada de propagação; camadas real/complexa = ablações; RQ4 em torno do argumento de
      tempo; RQ5 remete às 8.5/8.6); abstract e conclusão novos; discussão no que contradizia; prosa da camada de
      propagação no método (era um `\todo`; não estava na lista do orientador, avisado no relatório); vocabulário
      do protocolo. Três frases mudaram de sentido com os números da camada de propagação (fonte a 5 cm: cai com as
      reconstruções; feixe estreito: custa mais à camada; crops em conjunto fechado na geometria de CBMS 2024:
      0,881). **Minhas correções de revisão** (`5c6c171`, `53ede2f`): depois de recalibrar a reconstrução fica à
      frente em F1 (+0,045), não em rejeição; acerto fechado dos crops no abstract; "perto da curva"; "base set"
      restante. `rewrite/inversion` em `53ede2f`: 37 commits a partir do `main`, 41 páginas, 0 referências
      indefinidas, 0 overfull. `\todo` que restam: letras pequenas a 2 mm (orientador), nota do levantamento,
      declarações finais.
- [x] Q-rev. (feito) Todas as devoluções revisadas: números refeitos a partir dos arquivos por repetição, pytest 72,
      `reproduce check` 13/13, diffs de código lidos, nada em `results/` nem `expected/`.
- [x] Q-fim. (entregue às ≈ 11:58) `RELATORIO_CURVA.md` (+ PDF), PDF do paper e diff `main..rewrite/inversion` em
      `scratchpad/entrega/` (`relatorio_curva.pdf`, `paper_inversao_53ede2f.pdf`,
      `latex_main..rewrite-inversion_53ede2f.diff`), enviados ao orientador. **Sem merge, sem push.**
      **PARADO, esperando o orientador:** (1) nível mais denso para a camada "cair" ou basta o descritivo; (2) letras
      pequenas a 2 mm: manter, investigar (controle: regravar com o gravador sobreamostrado, r1) ou tirar;
      (3) .RIS do Scopus/ScienceDirect e os quatro PDFs; (4) escolhas a reverter (curva na 8.4 e não na RQ1; lugar
      da seção; prosa do método; título); (5) regenerar a figura do quadro inteiro com a camada de propagação (muda
      `expected/`); (6) push/merge. Nada novo roda sem a resposta dele e sem pré-registro.

### Fase R: resposta ao relatório da curva (2026-11-15, ≈ 13:30 e ≈ 13:34; `PROTOCOLO_CURVA.md`, fim)

Pré-registro: entrada Q2 de `CADERNO_CURVA.md` (13:37), antes de rodar.

- [x] **R-push.** (13:39) `exp/distancia-autofocus` e `exp/resolucao-fonte` para o GitHub, como branches, SEM merge.
  Commits posteriores desta fase: enviar de novo no fim (`git push origin exp/resolucao-fonte`).
  Overleaf: NADA (o remoto do paper é só o Overleaf, ligado ao `main`); só depois de o orientador revisar o PDF.
- [x] **R-S.** (14:26, conferido por mim contra `eval/small_near*/` e refazendo a interpolação e as distâncias)
  Controle das letras pequenas a 2 mm, r1: **a amostragem não explica.** Crops: referência 0,791 / 0,118; regravado
  (s = 2, raster mestre 16) 0,799 / 0,120; curva na mesma sobreposição (r1, interpolado) 0,907 / 0,514; distâncias
  0,008 / 0,002 ao antigo e 0,108 / 0,394 à curva. Camada 0,963 / 0,895 → 0,973 / 0,978; reconstrução 0,978 / 0,987
  → 0,973 / 0,954. D novo 165,7 µm, sobreposição 0,456. A gravação nativa a 2 mm difere da convergida em 4,8–5,8 %
  do rms do padrão ((2, 4): 0,6–0,8 %). Não testado: tamanho em pixels, faixa de N_F, distância, lei de
  profundidade. Mudança no pacote: comprimentos opcionais no `FresnelLayout` (`64e9e94`, 6 testes novos). Cache
  `rec_z0.npy` e `autofocus.csv` criados em `data/small_near` (nenhum arquivo existente mudou; hashes no D7).
  Tabela: `results_exp_resolucao/small_near_control.csv`. FALTA: texto (8.4, onde o conjunto é descrito,
  limitação vii).
- [x] **R-J.** (13:46, conferido por mim contra `eval/curve_u50_L008/bank_jit_r1.json` e
  `robustness_curve_u50_L008_bank_jit.csv`) Banco focal, r1: **não aguenta** pela regra do Q2. F1 0,981 a 1,0 mm;
  0,650 a 0,9 mm (−0,330) e 0,678 a 1,1 mm (−0,303); rejeição 0,994 / 0,997; acerto em fechado 0,972 / 0,973;
  acerto das conhecidas 0,506 / 0,530 (o que cai é o limiar, não a separação). Sem recalibrar ele cai menos que a
  camada (0,399 / 0,301) e a reconstrução (0,226 / 0,268); fica 0,32 / 0,29 abaixo da reconstrução recalibrada.
  A 0,7 mm rejeita tudo. Planos depois do treino: 0,970–1,029 mm (o banco estreitou). Tabela:
  `results_exp_resolucao/bank_jit_distance.csv`; caderno: D3 de `CADERNO_CURVA_DISTANCIA.md`. FALTA: pôr no texto
  (8.6 e limitação iii), por macro, dizendo que é uma repetição.
- [x] **R-txt.** (feito e revisado; R-J já no texto; falta só o parágrafo de R-S) Texto no `rewrite/inversion` (executor da escrita):
  (a) abstract e conclusão dizem com todas as letras: a reconstrução calibrada é a melhor rota no denso e quando z
  muda; a camada é a alternativa que se calibra sozinha; nada de vender a camada como superior (conferir intro e
  discussão);
  (b) as três frases que mudaram de sentido (fonte a 5 cm, feixe estreito, crops a 0,881 em conjunto fechado na
  geometria do CBMS 2024) sem suavizar;
  (c) seção da simulação: profundidade 0,02 dentro do canal (0,2 só no estresse) em todo lugar, figura-resumo
  incluída; distância como evidência (10 % de erro em z derruba camada e reconstrução sem recalibrar), também na
  figura-resumo, no abstract e nas contribuições;
  (d) nota do Related Work vira lista do que o orientador vai mandar (.RIS do Scopus e do ScienceDirect; PDFs do
  HoloAtt-UNet 2026, Cotter 2021, Delli Priscoli 2021, JBO 26:036001);
  (e) figura do quadro inteiro com a camada de propagação (muda `expected/`: autorizado para isso).
- [x] **R-viz.** (13:45, conferido: placar e quedas refeitos por mim a partir de `density_curve_reps.csv`)
  `docs/exp_resolucao/img/explica_regra_caiu.png` (+ `.pdf`), script `scripts/exp_resolucao/explain_fall_rule.py`,
  commit `231e53e`. Enviada ao orientador com a explicação.
- [x] **R-titulo.** (respondido às 13:42; ele ainda não escolheu) Responder: o título atual ainda fala em "Learnable Fourier Layer"; dar opinião e opções, não
  mudar sem a palavra dele.
- [x] **R-rev.** (feito; ver o diário) Conferir cada devolução contra os arquivos; depois de R-S e R-J, pôr os resultados no texto
  (macros), compilar, mandar PDF + diff. Sem merge, sem Overleaf.

### Fase S: resposta à entrega da Fase R (2026-11-15, ≈ 15:50; `PROTOCOLO_CURVA.md`, fim)

Resposta dele: "#2 ok / #4 faz o que achar melhor / #5 tempo de gpu não é um problema, faça o necessário pela
qualidade da pesquisa / #6 calma já leio / #3 que figura?". Pré-registro: entrada Q3 de `CADERNO_CURVA.md` (15:58,
commit `b97121d`), antes de rodar. GPUs: 0, 1, 2 (executor da densidade), 3 e 5 (executor da distância); a 4 está
ocupada por outro processo. Jobs em tmux, com retomada, poucos threads, um a cada 1–2 min.

- [x] **S-fig.** (15:54) Figura do item 3 reenviada (`docs/exp_resolucao/img/explica_regra_caiu.png`). A decisão
  do nível mais denso continua dele.
- [x] **S-titulo.** (16:03; paper `0bc6e5a`; compila em 45 páginas, 0 indefinidas, 0 overfull; o abstract continua na página 1) Título novo no `rewrite/inversion` (`main.tex`, linha 43): "Open-Set Recognition of Interference
  Patterns on Lensless Holograms: Why Crops of the Raw Hologram Fail, and What a Propagation Step Costs from a
  Window to the Whole Field of View". Conferir outros lugares que repetem o título.
- [x] **S-C.** (17:00, conferido por mim contra os 50 json de `eval/small_near_newrec/` e os de `results/eval/
  small_near`) **A coluna refeita confirma a do paper; a previsão valeu** (nenhum F1 médio muda mais de 0,02; o
  maior: crops +0,013). F1 novo / do paper: crops 0,806 / 0,793 (rejeição 0,191 / 0,153; fechado 0,896 / 0,888);
  camada real 0,951 / 0,944; complexa 0,949 / 0,955; Wiener 0,964 / 0,966; camada de propagação 0,973 / 0,972
  (rejeição 0,985 / 0,963); banco (5) 0,970 / 0,977; banco (7) 0,974 / 0,972; reconstrução 0,974 / 0,974 (rejeição
  0,985 / 0,969); autofoco 0,975 / 0,977; autofoco + gêmea 0,977 / 0,976. Tabela:
  `small_near_newrec_five_reps.csv`. A 19,25 mm a amostragem do sensor basta para as letras pequenas (par (1, 2)
  máx. 0,79 %; nativa contra s = 2: 0,5–0,8 %): nada regravado. FALTA: texto (escritor, parte 2, acionado).
  (Texto original do item:) Coluna de 2 mm: dez fluxos × r1–r5 no `small_near_newrec` (47 treinos novos),
  tabela ao lado da coluna do paper; conferência nativa contra convergida a 19,25 mm para as letras pequenas.
- [x] **S-D (cinco repetições, Q4).** (17:18, conferido por mim contra `eval/small_near_ctl{N,P}/*_r[1-5].json`,
  refazendo R_curva(k) e as distâncias) **D-N volta para a curva em 5 de 5: a faixa de N_F explica. D-P fica com o
  conjunto em 5 de 5: a profundidade não explica.** Crops, média de cinco: D-N 0,925 / 0,625 (curva 0,915 / 0,578;
  conjunto 0,806 / 0,191); D-P 0,810 / 0,208. Camada / reconstrução: D-N 0,972 / 0,963 e 0,973 / 0,961; D-P 0,974 /
  0,994 e 0,973 / 0,996 (o 0,849 de rejeição da reconstrução no D-N em r1 não se repete: 0,96–1,00 em r2–r5).
  Arquivos: `small_near_factors_five_reps.csv`, `_reading.json`. Commits do executor: `f6a3f7c` (D13), `6a00346`,
  `a6b8010` (D14). Texto: escritor, parte 3, acionado. O que segue é o registro do r1:
- [x] **S-D (r1).** (17:00, r1 conferido por mim contra `eval/small_near_ctl{N,P}/` e refazendo a interpolação)
  **r1: a faixa de N_F explica, a lei de profundidade não; as duas previsões valeram.** D-N (fontes × 0,3223; N_F
  0,295 / 0,544 / 0,979; sobreposição 0,451): crops 0,916 / 0,530, R_curva 0,908 / 0,516, R_reg 0,799 / 0,120;
  camada 0,976 / 0,990; reconstrução 0,961 / 0,849 (estranho, sem critério). D-P (uniforme ±25 µm): crops 0,803 /
  0,136; camada 0,978 / 0,997; reconstrução 0,974 / 0,998. Estratos (modelo de crops r1 do regravado): as não
  vistas são aceitas em todo estrato (rejeição 0,05–0,21); as conhecidas pequenas (12–22 px) acertam 0,713 contra
  0,971 e 0,996. Arquivos: `small_near_factors.csv`, `_reading.json`, `small_near_newrec_strata.csv`.
  **Q4 (17:00, `273c558`): os dois controles vão a cinco repetições** (levantei a minha trava do Q3 só para r2–r5;
  leitura de cinco fixada antes; aviso o orientador na entrega). RODANDO (executor da densidade). FALTA: conferir
  `small_near_factors_five_reps.csv`; texto (escritor, parte 3: 8.4, limitação vii, e a frase do mecanismo com o
  limite de N_F; NÃO mexer na frase-tese).
  (Texto original do item:) Dois controles em r1 para o conjunto fora da curva: D-N (faixa de N_F da
  família padrão) e D-P (lei de profundidade padrão); leitura estratificada do modelo de crops que já existe.
- [x] **S-L.** (17:00, conferido contra `curve_feasibility_dense.csv`, 20 cenas) A 450 por mm² (514 por janela) o
  gerador coloca quase tudo (512 por janela; 0,75 % do enchimento pulado; 34 % da área coberta). A 675 por mm²
  satura em ≈ 656 por janela (≈ 575 por mm²; 15 % pulado; 42 % coberta). Vai para o orientador decidir o #3.
  (Texto original do item:) Quanto o gerador coloca a 450 e 675 por mm² (sem holograma, sem treino).
- [x] **S-J.** (16:34, conferido por mim: médias, veredito e diferenças refeitos a partir de `eval/curve_u50_L008/
  bank*_r*.json`, `robustness_curve_u50_L008_banks_*.csv` e `distance_tests_u50_rows.csv`; batem com
  `banks_distance.csv`) **Nenhum banco aguenta a mudança de 10 % pela regra** (≥ 4 de 5): `bank_jit` 0 de 5,
  `bank_wide` 0 de 5 (falha só a 0,9 mm, quedas de 0,104–0,131; passa a 1,1 mm nas cinco), `bank_w2` 2 de 5,
  `bank_w3` 0 de 5. F1 médio de cinco, 1,0 / 0,9 / 1,1 mm como está: `bank_jit` 0,979 / 0,575 / 0,579; `bank_wide`
  0,977 / 0,860 / 0,909; `bank_w2` 0,976 / 0,867 / 0,892; `bank_w3` 0,979 / 0,609 / 0,703 (o jitter pesa mais que a
  largura). Rejeição ≥ 0,987 em tudo (o que cai é o acerto das conhecidas: o limiar). Como estão, os bancos de
  jitter 12 % ficam 0,09–0,10 abaixo da reconstrução recalibrada (0 de 10). Recalibrados por razão: 0,955–0,965;
  0,013–0,019 abaixo da reconstrução recalibrada (0–1 de 10) e 0,026–0,032 acima da camada recalibrada (10 de 10).
  Preço a 1,0 mm: nenhum (±0,004). Frase pré-fixada que vale: (i) "o banco focal não dispensa a recalibração".
  Commits do executor: `8262cae`, `ad8b6d7`, `dc9c62c`, `1ae4b79`, `64a821f`. Caderno: D4, D5 de
  `CADERNO_CURVA_DISTANCIA.md`. FALTA: texto (8.6, RQ5, "Which flow to use", limitação iii), por macro.
  (Texto original do item:) Banco focal: `bank_jit` r2–r5; `bank_wide`, `bank_w2`, `bank_w3` r1–r5; como
  estão a 0,9 / 1,1 mm (0,7 estresse); recalibração dos bancos por razão. Regra: aguenta em ≥ 4 de 5.
- [x] **S-txt.** (feito em três partes e revisado por mim; paper `3924d18`) (escritor, depois dos resultados) Tabela de tamanho com a coluna nova; números das letras pequenas
  a 2 mm fora da tabela; 8.6 e limitação (iii) com o banco em cinco repetições; 8.4 e limitação (vii) com o
  diagnóstico; macros no `paper_resolucao.py`. NÃO mexer na frase-tese (o orientador ainda vai ler).
- [x] **S-rev.** (feito; ver o diário) Conferir cada devolução contra os arquivos; `pytest` + `reproduce check`; compilar; PDF + diff;
  `git push origin exp/resolucao-fonte` (só GitHub, sem merge); mensagem final. Overleaf: NADA.

Continuam esperando a palavra dele: revisão do PDF (→ Overleaf), nível mais denso (#3), frase-tese (#6), abstract
de ≈ 450 palavras, os dois pontos do diagrama da bancada, e os arquivos que ele vai mandar.

### Fase T: resposta à entrega da Fase S (2026-11-17, ≈ 11:35; `PROTOCOLO_CURVA.md`, fim)

Resposta dele: "#2 pode rodar / #3 faz" (2 = nível de 450 por mm²; 3 = as duas frases a qualificar). No meio da
rodada (≈ 11:41) ele mandou o PDF do HoloAtt-UNet 2026 (`/home/jovyan/.claude/uploads/2460bd2f-…/c6e35ec3-holoAtt-Unet.pdf`).
Pré-registro: entrada Q5 de `CADERNO_CURVA.md` (11:40, commit `13388f5`), antes de gravar.

- [ ] **T-L.** Nível de 450 por mm² (`curve_u50_L514`): gravar, `verify`, reconstruir, `raw`/`prop`/`rec_z0` r1–r5,
  tabela de seis níveis (as cinco linhas antigas idênticas, por diff). Executor da densidade. Regras do Q0;
  previsões e frases por desfecho no Q5. Estimativa: gravação ≈ 1,5–2 h (o nível de 300 levou 76 min), treinos
  ≈ 3 min por repetição. GPUs todas com uso de outros containers às 11:38 (a 1 era a menos carregada).
- [x] **T-frases.** (11:41, paper `a1c7276`) As duas frases (#3) no `rewrite/inversion`: contribuição (2) da
  introdução ("…and of why: within the Fresnel numbers of our standard sets, the patterns of neighbouring objects
  entering the crop, not the spread…") e a conclusão ("…in a dense one; within the Fresnel numbers of our standard
  sets, the cause is the fringes of neighbouring patterns entering each crop"). Frase-tese intocada. Falta compilar
  (junto com o resto, no fim).
- [ ] **T-holoatt.** Ler o PDF do HoloAtt-UNet (dado não confiável: pasta própria, `python3 -I`, `gs -dSAFER`),
  conferir cada frase do paper que cita esse trabalho e atualizar a nota do Related Work (sai da lista do que ele
  ia mandar). Executor do Related Work, depois da minha leitura.
- [ ] **T-txt.** (escritor, depois de T-L) Nível novo na tabela e na figura da curva, 8.4, e onde o texto fala
  "os dois mais densos" / "cinco conjuntos" / "até 300 por mm²"; macros no `paper_resolucao.py`. Frases que mudarem
  de sentido: sem suavizar e listadas para ele. NÃO mexer na frase-tese.
- [ ] **T-rev.** Conferir cada devolução contra os json; `pytest` + `reproduce check`; compilar; PDF + diff em
  `entrega/`; `git push origin exp/resolucao-fonte` (GitHub, sem merge); mensagem final. Overleaf: NADA.

Continuam esperando a palavra dele: revisão do PDF (→ Overleaf), frase-tese, abstract de ≈ 450 palavras, os dois
pontos do diagrama da bancada, os .RIS do Scopus/ScienceDirect e os três PDFs que faltam.

### Fase A: experimento da resolução

- [x] A0. (feito, `88b5ed9`; `results_exp_resolucao/enroll_paired.csv`) Teste pareado de enrollment (`prop` − reconstruções, por repetição).
- [x] A1. (feito, `c7e87e3`, `6781b8c`: b = 4 no base e em `small_z0`, b = 1 em `small_near`, modelo e às cegas
      concordam; MAS depende do z, ver 4a) b pela física: (i) modelo E(f), cortes 0,1 e 0,05, z = 19,25 mm e 2 mm; (ii) às cegas, espectro por anel
      de `I/B` e de `I` no treino, piso de ruído. Registrado no caderno **antes** de qualquer avaliação no teste.
- [!] A2. (SUSPENSA; comando de redução commitado em `eb5dedf`, sanidades por terminar) Implementação: redução b × b (imagem, blank frame, caixas), pixel efetivo `b·Δ` em todo cálculo de
      frequência, sanidade do α (igual em todo b), testes; b = 1 idêntico ao de hoje.
- [!] A3. (SUSPENSO, nada treinado nem avaliado) Piloto (r1): conjuntos reduzidos, α por b, 9 modelos (3 fluxos × b ∈ {2, 4, 8}), avaliação estrita no base
      e robustez em `fullwell_500` e `beam_narrow`; curva F1 × b.
- [!] **Checkpoint P1**: mostrar curva F1 × b nos três conjuntos, α em cada b, b previsto pela física (dois métodos),
      teste pareado de enrollment. **Parar e esperar aprovação explícita.**
- [ ] A4. (só com aprovação) cinco repetições; `bank_jit`; `rec_afc` onde z varia; quadros inteiros com YOLO
      retreinado (uma passada × tiles; nano × atual); crop 32 × 32; leitura em uint8 com redução logo após ler e
      blank frame reduzido em memória; conjuntos pequenos com o b da regra para cada distância; pergunta A.4 (YOLO
      no refocado).
- [ ] A5. Sessão única de tempo (GPU e um core de CPU, leitura incluída; mm²/s por core).
- [!] **Checkpoint P2**: relatório curto com "o que deu errado". Parar e esperar aprovação.

### Fase C: levantamento e parágrafo crítico (ordem: depois de B no texto, mas o levantamento é pré-requisito)

- [x] C-agora. (feito: `1c792f9` `LEVANTAMENTO_C.md`, `b1ff802` `scripts/exp_resolucao/refs_merge.py`) Em paralelo (autorizado em `PROTOCOLO_Z.md`): leitura de [11], [13], [14] com frase exata e página;
      strings S1–S7 no PubMed (E-utilities) com exportação e deduplicação; triagem; tabela em
      `docs/exp_resolucao/LEVANTAMENTO_C.md`; PDFs em `../referencias/c/` — subagente "levantamento-c".
- [!] C0. **Pergunta ao orientador (feita às 13:10, sem resposta ainda):** as strings S1–S7 têm de rodar no Scopus e na ScienceDirect com exportação
      .RIS; eu não tenho credencial nem chave de API da Elsevier. Ou ele exporta os .RIS, ou fornece a chave
      (dev.elsevier.com) para rodar daqui.
- [ ] C1. Triagem; tabela (trabalho, frase exata, página, mediu ou não, baseline, hardware), começando por [11],
      [13], [14].
- [ ] C2. Related Work inteiro + parágrafo "The speed argument" + frases da Introdução e da Discussion.

### Fase B: reescrita do paper (só depois do P2)

- [ ] B1. Branch no repositório LaTeX; título (2–3 alternativas) e abstract; contribuições; notas "Prose to write"
      escritas e apagadas; RQ2, RQ3, "Which flow to use", Conclusão com `prop` como método proposto; Tabelas 10 e 11
      (`frame_5` × `session_5`); custo dos stacks largos em rejeição; limitações.
- [ ] B2. Diff para o orientador revisar, sem merge.

### Entregáveis finais (protocolo)

1. Branch com o código de A, testes passando, `reproduce check` OK. 2. Caderno com o b previsto pelos dois métodos,
escolhas datadas e comandos. 3. CSVs, figuras (F1 × b × tempo; custo × F1 com e sem detector; mm²/s por core) e
macros novas. 4. Tabela do levantamento C.1. 5. Diff do LaTeX (B e C), sem merge. 6. Relatório curto com "o que deu
errado".

## 6. Diário (mais recente embaixo)

- 2026-11-14, 13:05: instrução recebida e copiada em `PROTOCOLO.md`; branch `exp/resolucao-fonte` criado; este
  arquivo e a abertura do caderno escritos; subagente "piloto" (Opus, high) disparado para A0–A3. Próximo passo meu:
  revisar o que ele devolver, montar o material do P1 e **parar para aprovação**.

- 2026-11-14, 13:25: **parte A suspensa** por instrução nova (seção 4a; `PROTOCOLO_Z.md`). Subagente "piloto"
  redirecionado para Z1–Z3; disparados "levantamento-z" (Z4) e "levantamento-c" (C em paralelo). Próximo passo meu:
  juntar Z1–Z4, montar a proposta (Z5) e **parar no Checkpoint Z**.
- 2026-11-14, 13:45: subagente "piloto" devolveu. **Parte A parada** (commits `02efd17`, `34634ea`): nada treinado,
  nenhum teste de conjunto reduzido avaliado; em disco só `data/realistic_b1` e `data/variants_val_b1/*` (b = 1,
  idênticos aos originais); `pytest` 46 passam, `reproduce check` 13/13.
  **Z1:** no gerador original (`OLD-WRONG-projeto-e-testes/data/matlab_generation/run_z.m`, linha 9:
  `CV_FR_focus(im, 1.67e-6, 1.67e-6, -385e-9 * 50000, 385e-9)`; kernel em `CV_FR_focus.m` linha 37) e no nosso
  `sim/physics.py` (linha 46: `Z0 = 385e-9 * 50000`), z está em metros: "50k" = 50 000 λ = 19,25 mm. O suplemento
  do artigo de 2015 diz "We used z×λ to compute the distance between the object and the detector plane… For HR
  holograms, a scale factor k is applied to up-sampling the distance z": três leituras possíveis, nenhuma escolhida
  (z×λ no pixel de 1,67 µm = 19,25 mm; ou valor aplicado a imagens super-resolvidas, o que daria 4,8 / 2,1 / 0,39 mm
  para fator 2 / 3 / 7; ou só parâmetro de simulação). As resoluções USAF do suplemento (2,76 µm com 1 quadro;
  2,19 com 9; 1,55 com 49) pedem, pelo envelope, z ≤ 4,3 / 2,8 / 1,3 mm; a 19,25 mm o envelope só deixa 6,9 µm.
  **Z2:** os números do orientador (73, 170, 278, 397 ciclos/mm) são o nosso modelo SEM o termo da abertura do pixel;
  com ele (convenção da `eq:envelope` do paper): 72,4 / 167,6 / 266,4 / 362,2; b_max 4 / 1 / 1 / 1; o corte passa do
  Nyquist (299) para z ≤ 1,56 mm; termo dominante: imagem do pinhole a 19,25 mm, largura de banda de 5 mm para baixo.
  Convenção de L: o paper diz pinhole a 15 cm do SENSOR; com L = 15 cm − z o corte a 19,25 mm cai para 66,8.
  **Avisos dele:** `data/realistic/aux/r1_rec_z0.npy` não existe mais (as reconstruções auxiliares do treino de
  `rec_z0`); a banda de 10 nm é suposição nossa; o limiar 0,1 é convenção.
  Aguardando: "levantamento-z" (tabela das bancadas e proposta) e "levantamento-c". Depois: avaliar as configurações
  candidatas com `envelope_table.py`, escrever a proposta e as consequências, e **parar no Checkpoint Z**.
- 2026-11-14, 13:50: **atualização do orientador: z ≈ 1 mm** (seção 4b). "levantamento-z" redirecionado para fechar o
  número (lamínula + vidro do sensor + folga); "piloto" recebe Z6 (consequências e custo, sem regravar nem treinar).
- 2026-11-14, 14:05: **"levantamento-z" devolveu** (`7a5dcf6`). Conferi por amostragem duas citações nos arquivos
  baixados (Bishara 2011, "placed directly atop the protective glass of the image sensor, i.e., approximately
  z ≈ 0.7 mm"; folha de dados MT9J003, "Borosilicate glass 0.4 thickness. Refractive index ... 1.5255 @ 546 nm"):
  batem. Resultado:
  - **Orçamento da distância** (pilha A = amostra na face interna de uma lamínula 1½ virada para o sensor):
    lamínula 0,16/0,17/0,19 mm (ISO 8255-1:2011) + folga de ar 0,05/0,2/0,5 (sem fonte: comunicação pessoal) + vidro
    do sensor 0,4 mm (n = 1,5255) + folga vidro–chip 0,125 ± 0,05 (folha de dados MT9J003): geométrica
    0,69 / **0,90** / 1,27 mm; efetiva em ar (soma de t/n) 0,49 / **0,70** / 1,06 mm. Pilha B (amostra sobre lâmina
    de 1 mm): efetiva 1,01 / 1,25 / 1,63. Pilha C (sem vidro do sensor): 0,13 / 0,21 / 0,43.
  - **Proposta dele:** z = 0,7 mm efetivo (≈ 0,9 geométrico), faixa 0,5–1,1; alternativas 1,0 mm (redondo) e
    1,25 mm (lâmina). D = 100 µm e pinhole a 15 cm do SENSOR ficam (nada no levantamento pede mudar).
  - **Unidade no artigo de 2015:** o suplemento diz "We used z×λ to compute the distance…", então 50k = 50 000 λ é a
    leitura certa da unidade; o que descarta 19,25 mm é a física (resoluções 2,76 / 2,19 / 1,55 µm) e, talvez, a
    escala de z nas imagens super-resolvidas (50 000 λ / 49 = 0,39 mm; inferência, não fato).
  - Literatura on-chip com vidro do sensor: z ≈ 0,7–1 mm (Bishara 2010, 2011; Greenbaum & Ozcan 2012), até 2 mm
    (Mudanyali 2010, Tseng 2010); fontes a 3–10 cm; pinholes/fibras de 50–150 µm; banda 2–30 nm.
  - **Sem fonte lida:** a banda de 10 nm do LED (o artigo nomeia o Thorlabs M385L2 e não dá a banda; a página do
    catálogo bloqueou o acesso); o modelo do sensor (o artigo diz só "Aptina 10 megapixel"; MT9J003 é inferência pela
    área óptica 6,413 × 4,589 mm); a folga de ar; deriva térmica de z (só o aquecimento em si tem fonte: Greenbaum
    2012, "above 40 °C after continuous operation").
  - **Erros achados em documentos nossos:** `docs/EQUIPMENT.md` tem "100 mm" de pinhole (vem da versão PMC do
    artigo; o PDF diz 100 µm) e cita mal Greenbaum 2012; o pinhole fica a 15 cm do sensor, não da amostra.
  - Várias linhas da tabela citam seção de manuscrito PMC, sem número de página (o PMC não tem páginas): avisar o
    orientador, que pediu página.
  - Não acessados: Isikman 2011 PNAS, Repetto 2004, McLeod & Ozcan 2016 (sem cópia aberta).
  Aguardando: Z6 do "piloto" (consequências; já commitou a prévia dos três conjuntos, `2cf9d00`) e "levantamento-c".
- 2026-11-14, 14:10: segunda atualização do orientador (seção 4c): mais três itens no Checkpoint Z (tabela de
  parâmetros com fonte; comparação base × `small_near`; figura "o que muda com o setup") e o tom do texto. Z7 para o
  "levantamento-z", Z8 para o "piloto".
- 2026-11-14, 14:20: **"levantamento-c" devolveu** (`b1ff802`, `1c792f9`; `docs/exp_resolucao/LEVANTAMENTO_C.md`;
  downloads em `../referencias/c/`). Resultado:
  - [11] Rockembach 2024 (nosso CBMS): só a p. 364 está acessível (via TCC no repositório da UFSC). Frases: "the
    real-time analysis of holograms is computationally expensive due to the nature of numerical diffraction methods
    to reconstruct the signals into visual information" e "avoiding the need for computationally expensive
    diffraction methods". Não diz "iterative". Se mediu: não verificável (pp. 365–369 fora de acesso) — **pedir ao
    orientador o PDF ou a confirmação**.
  - [13] Bravo-Frank 2024: **não faz a afirmação** (o "real-time" vem da cascata de YOLOs; sem tempos nem hardware).
    Tem classe "unknown" por limiar: a frase "both are closed-set" de `02-related.tex` precisa de ressalva. O trabalho
    seguinte do grupo (2025, diálise peritoneal) faz a afirmação e reconstrói dois planos de Fresnel dentro do
    pipeline "real-time".
  - [14] Liu 2021: afirma e **mediu no mesmo hardware** (Intel Atom: ≈ 14 s por imagem de reconstrução contra ≈ 0,09 s
    de clustering), mas o baseline é autofocus cego de 501 distâncias e não há detector.
  - Tabela: 13 trabalhos com a frase localizada; 3 mediram contra reconstrução no mesmo hardware (Liu, Matthews 2024,
    OAH-Net 2025), 5 mediram só o próprio pipeline, 4 não mediram, [11] não verificável; 9 lidos sem a afirmação;
    12 só com resumo (não citáveis entre aspas). Göröcs 2018 mediu estágio por estágio (detecção ≈ 70 ms por quadro;
    autofocus + reconstrução ≈ 12 ms por objeto): medição independente a favor do nosso argumento. Molani 2026 chama
    a própria back-propagation de "computationally intensive".
  - PubMed (S1–S8, com e sem ≥ 2020): 221 registros, 207 após deduplicação, 160 com ≥ 2020; 28 incluídos na triagem.
    Nenhum dos trabalhos de controle é recuperado pelo PubMed (strings precisam de ajuste; ver o documento).
  - Ajustes ao rascunho C.3: a chave é `rockembach` (não `rockembach2024`); [13] não entra como quem afirma; dizer que
    Liu e Matthews mediram e contra o quê; "iterative" só em Kim, Xu e Terbe; Terbe 2022 propõe filtros de Fourier
    aprendíveis como trabalho futuro (antecedente direto da nossa camada, para o Related Work).
  - Pendente: .RIS de Scopus/ScienceDirect (pastas `../referencias/c/{scopus,sciencedirect}/`, `S<n>` no nome, sem
    filtro de ano; depois `python3 -I scripts/exp_resolucao/refs_merge.py <pasta>`); 8 textos abertos que os
    servidores recusaram a cliente automático; paginação de Liu (manuscrito aceito) e de dois lidos no arXiv.
  Ainda rodando: Z6/Z8 ("piloto") e Z7 ("levantamento-z").
- 2026-11-14, 14:05: **CHECKPOINT Z ENTREGUE — PARADO, AGUARDANDO APROVAÇÃO EXPLÍCITA DO ORIENTADOR.**
  Documento: `docs/exp_resolucao/CHECKPOINT_Z.md` (PDF enviado no chat, com a figura `img/fig_setup.png`).
  Conteúdo: unidade do z (metros; 50k = 50 000 λ; confirmado pelo suplemento); levantamento de 15 bancadas;
  orçamento de z (geométrico 0,69/0,90/1,27 mm; efetivo 0,49/0,70/1,06); proposta z₀ = 0,7 mm efetivo (alternativa
  1,0 mm), D e L mantidos, banda 10 nm agora com fonte (tabela da Thorlabs arquivada em 2015-05-04, conferida por mim);
  45 parâmetros com fonte; comparação dos três conjuntos; vazamento do padrão contra z; consequências; custo; três
  opções (1 não regravar; 2 piloto na distância certa, minha recomendação; 3 regravar tudo).
  Achados que mudam o que está em jogo: (i) letras do base a ≈ 1 mm vazam só 1–5 % do padrão para fora do crop: a
  premissa central do paper não vale ali e nenhum conjunto existente cobre esse regime; `small_near` NÃO é prévia
  dele (vaza 49 %, como o base de hoje); (ii) o simulador calcula o campo no passo do pixel e descarta a faixa
  299–414 ciclos/mm: gravar a ≈ 1 mm pede sobreamostragem 2–3× (código novo); (iii) a 0,7 mm o α sai da faixa de
  `calibrate_alpha`, a profundidade de campo cai para ≈ 29 µm, a média 4 × 4 da busca estreita corta sinal, a
  variação entre montagens (≈ 0,1 mm) passa da faixa da busca estreita.
  Decisões pedidas ao orientador: (a) z₀ 0,7 ou 1,0 mm efetivo; (b) opção 1, 2 ou 3; (c) tamanho dos objetos na
  configuração próxima; (d) perguntar ao prof. Sobieranski folga, lado da lamínula e modelo do sensor.
  Pendências paralelas dele: .RIS de Scopus/ScienceDirect; páginas 365–369 do [11].
  **Não fazer nada da parte A, nem gravar, nem treinar, até a resposta dele.** Parte C: levantamento pronto
  (`LEVANTAMENTO_C.md`); a escrita do Related Work e do parágrafo espera o texto (B) e os .RIS.
- **2026-11-14, 15:30 — pergunta do orientador depois do Checkpoint Z (NÃO é aprovação).** Ele perguntou qual era a
  distância do CBMS 2024 (1, 2 ou 19 mm) e disse que, pelo que viu, a 1 mm "não tem nenhuma perturbação de
  holografia", o que "destrói completamente o artigo". Respondido (caderno, Z9): (i) CBMS 2024 = 19,25 mm, pelo
  código do gerador (`microscopia2/data/cbms2024/matlab_generation/run_z.m`, md5 igual ao da Manu); o texto do artigo
  não foi conferido (só temos a p. 364, que não dá o número); (ii) a 1 mm o holograma some só para objetos grandes:
  quem decide é o número de Fresnel; letra de 129 µm → 2 % fora do crop, 47 µm → 27 %, 25 µm → 60 %, 15 µm → 90 %; a
  letra do base a 19,25 mm equivale a uma de 29 µm a 1 mm. Figura `img/pattern_size_at_1mm.png`, script
  `scripts/exp_resolucao/fig_size_at_1mm.py`. Minha leitura: o paper não cai, mas o conjunto base não é a geometria
  da bancada; o teste que decide é o piloto da opção 2 com objetos de ≈ 15–40 µm a 0,7–1 mm (simulador
  sobreamostrado). **Continua PARADO: sem aprovação do Checkpoint Z, nada de gravar nem treinar.**
- **2026-11-14, ≈ 15:40–16:00 — PILOTO APROVADO.** O orientador aprovou o piloto com seis escolhas (na íntegra em
  `PROTOCOLO_PILOTO_1MM.md`) e mandou o PDF do CBMS 2024 (p. 367: "λ = 385nm, z = 50k, pixel size of 1.67μm", sem
  unidade). Feito por mim: protocolo salvo (`13f350e`), pré-registro P0 no caderno novo `CADERNO_PILOTO_1MM.md`
  (`15bfea7`), dois subagentes lançados (simulador; CBMS completo), duas perguntas feitas a ele (densidade de letras;
  espalhamento de profundidade). Ver a Fase P do plano. **Próximo passo ao voltar: ler o relatório do subagente do
  simulador, revisar o diff (s = 1 idêntico? `reproduce check` 13/13? pytest?), registrar as respostas do orientador
  como entrada P1 do caderno do piloto, e só então mandar gravar o conjunto.**
- **2026-11-14, 17:30 — CHECKPOINT DO PILOTO ENTREGUE. PARADO.** r1 a 1,0 mm: os crops ficaram muito melhores que
  no base (0,928 / 0,622 contra 0,785 / 0,105), a camada e a reconstrução empatam em 0,977 e ≈ 1,0 de rejeição. A
  condição de F1 do critério (≥ 0,10) não é cumprida em r1 (+0,049; com raw em 0,928 o teto é 0,072); a de rejeição
  é (+0,373). A 1 mm os fluxos de distância fixa quebram com 0,7 mm sem recalibrar e perdem ≈ 0,2 de F1 com 50 µm de
  profundidade; os crops não. **Próximo passo ao voltar: ler a resposta do orientador ao checkpoint do piloto (ver
  P5); só então rodar repetições ou controles, com pré-registro no caderno do piloto antes.** A parte B (reescrita)
  depende do resultado das cinco repetições: se o critério falhar, "a tese muda e a gente reescreve" (palavras dele).
- **2026-11-14, 17:40 — orientador aprovou as quatro repetições, os dois controles ("antes de reescrever") e o
  treino com 50 µm.** Pré-registro P2 escrito antes de rodar; dois subagentes em execução (ver P6).
- **2026-11-14, 18:58 — cinco repetições, referência do B e treino com 50 µm prontos e conferidos; critério: 0 de 5.**
  Os crops a 1 mm ficam em 0,938 / 0,730 (média de 5); a camada passa por +0,039 de F1 e +0,268 de rejeição. Falta o
  subagente dos controles (C gravando até ≈ 19:20, depois treino; depois B). **Próximo passo ao voltar: esperar o
  relatório dele, conferir, escrever o relatório do piloto completo e mandar. Nada de reescrita antes do pedido.**
- **2026-11-14, 20:43 — RELATÓRIO DO PILOTO COMPLETO ENTREGUE. PARADO.** Critério do orientador: 0 de 5 (camada −
  crops +0,039 F1, +0,268 rejeição). Controles (r1): o código novo a 19,25 mm reproduz o base; com a densidade
  relativa do base a 1,0 mm os crops voltam a 0,796 / 0,080 e a camada fica +0,164 / +0,820 acima. Leitura minha: o
  que derruba o crop é o padrão das vizinhas, não o vazamento do próprio padrão nem a distância. Treino com 50 µm
  recupera a perda de profundidade. **Próximo passo ao voltar: ler a resposta do orientador às cinco decisões da
  seção 8 de `RELATORIO_PILOTO_1MM.md` (ver P7). Sem resposta, não rodar nada nem reescrever.**
- **2026-11-14, 21:25 — o orientador deixou a densidade conosco ("Pode escolher, ele não lembra").** Escolha (P4 do
  caderno do piloto): eixo de 7 a 135 objetos/mm², níveis intermediários de Seo 2009 (15 e 69 letras por janela),
  ainda não gravados. Relatório atualizado e reenviado. **Continua PARADO: as decisões 1 a 4 da seção 9 do relatório
  (tese, cinco repetições no denso, níveis intermediários, parte B) não foram respondidas.**
- **2026-11-15, ≈ 08:00 — o orientador respondeu ao relatório do piloto** (`PROTOCOLO_CURVA.md`, na íntegra):
  enquadramento novo (inversão da tese do CBMS 2024), experimentos a–d aprovados para começar hoje, escrita em
  paralelo. Feito por mim até 08:15: protocolo salvo (`3a3c80e`), pré-registro Q0 no caderno novo `CADERNO_CURVA.md`
  (`15c7107`), branches `rewrite/{inversion,sim-section,related-work}` e dois worktrees no repositório LaTeX,
  quatro executores lançados (Fase Q). **Próximo passo ao voltar: (1) ver se o orientador respondeu a pergunta da lei
  de profundidade e escrever o Q1 antes de qualquer gravação da curva; (2) ler as devoluções dos executores e
  revisar; (3) mandar a fase 2 ao "densidade" e ao "distância".**
- **2026-11-15, 08:53 — fase 1 conferida, lei de profundidade respondida, fase 2 em curso.** Denso 5 de 5; D = 112 µm;
  d1 feita; primeira passada da escrita junta em `rewrite/inversion`. Rodando: "densidade" (lei uniforme, família
  `curve_u50_*`, curva), "distância" (espera o nível 8, depois d2 e profundidade), escritor da simulação (segunda
  passada). **Pendências para o orientador (dizer no próximo relato):** .RIS do Scopus/ScienceDirect; PDF do
  HoloAtt-UNet (Optica Open, bloqueado) e de Cotter 2021, Delli Priscoli 2021, JBO 2021; se as strings de busca
  entram no paper; o conjunto de letras pequenas a 2 mm (crops 0,793 / 0,153 com densidade só ≈ 2,6 × a do esparso:
  ver o acréscimo do Q1); lugar da seção nova (depois dos resultados ou depois de 03b). **Próximo passo ao voltar:
  ler as devoluções; conferir `density_curve.csv` contra os json e as regras do Q0; terceira passada da escrita
  (painel d no eixo do Q1, parágrafos de densidade, profundidade e distância, depois abstract, resultados e
  conclusão); relatório curto e diff para o orientador, sem merge.**
- **2026-11-15, 10:02 — d2 e profundidade conferidas; curva gravando.** O executor da distância terminou (commits
  até `940fc78`); refiz as médias e as diferenças pareadas a partir de `robustness_curve_u50_L008_dist.csv`,
  `robustness_depth_from_*.csv` e dos json de `eval/curve_u50_L008`: tudo bate com a tabela dele. O da densidade
  ainda grava (às 10:00: L343 em 4000/5000, L154 em 3750/5000; L015 e L069 por gravar; depois r1 em todos, regra do
  Q0, r2–r5). Achado a dizer ao orientador: na lei padrão o treino plano perde 0,02, não 0,2 (ver Q-d2). O gerador
  de macros ainda toma o piloto plano (`bench_1mm`) como "o esparso": a terceira passada troca para a família
  padrão. **Próximo passo ao voltar: ler a devolução do escritor (parte 1) e a do executor da densidade; conferir
  `density_curve.csv` contra os json e a regra do Q0; mandar a parte 2 da escrita; relatório curto e diff, sem
  merge.**
- **2026-11-15, 10:15 — parte 1 da terceira passada revisada.** (As horas "10:15" e "10:20" que escrevi antes
  estavam adiantadas: o executor da distância terminou às ≈ 09:58 e mandei a parte 1 às ≈ 10:03.) Rascunho do
  relatório em `RELATORIO_CURVA.md` (seções 2, 4 e 5 conferidas; 1, 3, 6–8 por escrever; ainda não commitado).
  Li a seção de resultados inteira para a encomenda da parte 2 (Q-w5). **Próximo passo ao voltar: esperar a
  devolução do executor da densidade (r1 em todos os níveis → mandar a parte 2 ao escritor; depois r2–r5, figura,
  D das geometrias que já existem, `curve_alpha.csv`); conferir contra os json e a regra do Q0; relatório e diff.**
- **2026-11-15, 11:40 — curva completa e conferida; parte 2 da escrita em curso.** Nada mais roda na GPU. Falta:
  (1) revisar a devolução do escritor (parte 2) lendo abstract, 06, 8.4, conclusão e o PDF; (2) terminar
  `RELATORIO_CURVA.md` (seções 1, 3, 6, 7, 8) e commitar; (3) mandar ao orientador o relatório, o diff
  `main..rewrite/inversion` e o PDF, sem merge nem push. **Perguntas para ele (no relatório):** nível mais denso
  para a camada "cair" pela regra, ou basta o descritivo; o que fazer com as letras pequenas a 2 mm no eixo
  (manter com a frase honesta, investigar com um controle, tirar); .RIS do Scopus/ScienceDirect e PDFs bloqueados;
  lugar da seção e título do paper; push/merge.
- **2026-11-15, 11:58 — etapa da curva entregue.** Relatório, PDF do paper e diff enviados; tudo commitado
  localmente nos dois repositórios, nada enviado ao GitHub nem ao Overleaf. **Próximo passo ao voltar: ler a resposta
  do orientador às seis perguntas da seção 8 de `RELATORIO_CURVA.md`; não rodar nem mesclar nada antes.**
- **2026-11-15, 13:38 — o orientador respondeu ao relatório da curva (duas mensagens, na íntegra no fim de
  `PROTOCOLO_CURVA.md`).** Fase R aberta acima; pré-registro Q2 escrito antes de rodar. Decisões dele: GitHub sem
  merge e nada no Overleaf até ele revisar o PDF; controle das letras pequenas a 2 mm; figura do quadro inteiro
  com a camada de propagação; texto sem vender a camada como superior; banco focal a 0,9 e 1,1 mm só em r1.
  **Próximo passo ao voltar: ver as devoluções dos executores (densidade: R-S; distância: R-J; escrita: R-txt;
  figura: R-viz), conferir contra os arquivos, integrar no texto, compilar e mandar PDF + diff.**
- **2026-11-15, 13:42 — push do código feito; quatro executores lançados** (R-S, R-J, R-txt, R-viz; IDs em
  `scratchpad/agentes.md`). GPUs combinadas: densidade 4–5, distância 6, figura do quadro inteiro 7. **Próximo passo
  ao voltar: esperar as devoluções, conferir cada uma contra os arquivos; depois mandar ao executor da escrita os
  resultados de R-S e R-J para o texto; compilar; PDF + diff ao orientador; push final só do código.** Resposta do
  título (R-titulo): o trecho "with a Learnable Fourier Layer" é o que envelhece; propor opções, não mudar sozinho.
- **2026-11-15, 13:47 — R-viz e R-J prontos e conferidos; R-S e R-txt em curso.** Erro meu: mandei os executores
  para as GPUs 6 e 7, que não existem (o container tem 0–5); o da distância usou a 3, sem efeito em número. O
  executor da densidade parou com duas perguntas (parâmetros opcionais no `FresnelLayout` para escrever as leis do
  `SmallLayout`; cache `rec_z0` em `data/small_near`): respondi sim às duas, com condições (padrão inalterado
  provado por testes; nenhum arquivo existente alterado). Referência parcial do controle S (r1): crops 0,791 / 0,118,
  camada 0,963 / 0,895. **Próximo passo ao voltar: devolução da escrita (revisar; depois mandar R-J e R-S para o
  texto), devolução do controle S (conferir, aplicar a leitura do Q2), compilar, PDF + diff, push do código.**
- **2026-11-15, 13:50 — R-txt (a–e) revisado e aprovado; paper em `dfd2d42`, 44 páginas, 0 indefinidas, 0 overfull.**
  O escritor fez: abstract e conclusão com a reconstrução como a melhor rota no denso e quando z muda; as três
  frases sem suavizar (a tese virou "fails in the open set, and holds in the closed set only when the sample is
  sparse": avisar o orientador); seção 8 com cinco parâmetros e painel (f) do erro de distância; profundidade 0,02
  no canal; nota do Related Work como lista do que ele manda; figura do quadro inteiro com a camada de propagação
  (**nenhum arquivo de `expected/` mudou**; `reproduce check` 13/13 e `pytest` 72 segundo ele: REFAZER eu mesmo no
  fim, depois que o executor da densidade terminar de mexer em `scene.py`). Ajuste meu: "by a tenth or more" nas
  três frases da comparação recalibrada (as 15 incluem 0,7 mm). O abstract tem ≈ 420 palavras: avisar.
  Em curso: escritor pondo R-J no texto (8.6, RQ2 "The focal stack", limitação iii); executor da densidade em R-S.
  **Próximo passo ao voltar: revisar a devolução do escritor (R-J); esperar R-S, conferir, aplicar a leitura do Q2,
  mandar ao escritor; testes; compilar; PDF + diff; push do código (só GitHub).**
- **2026-11-15, 13:52 — PDF intermediário e diff enviados ao orientador** (`scratchpad/entrega/paper_inversao_28f9158.pdf`,
  `latex_53ede2f..28f9158.diff`): R-txt e R-J no texto (8.6, RQ2, limitação iii). Testes refeitos por mim: `pytest`
  78 (72 + 6 novos do `FresnelLayout`), `reproduce check` 13/13. Código enviado de novo ao GitHub
  (`exp/resolucao-fonte`, sem merge). Overleaf: nada. O abstract cabe na página 1, com ≈ 450 palavras (avisar).
  Falta: R-S (gravando em tmux `res_S_record`; convergência a 2,0 mm passou com s = 2, máx. 0,80 %). **Próximo passo
  ao voltar: devolução do R-S → conferir contra `eval/small_near*/` e `small_near_control.csv`, aplicar a leitura do
  Q2, mandar ao escritor o parágrafo (8.4 e limitação vii; tirar o `\todo` das letras pequenas), compilar, PDF +
  diff finais, push do código, mensagem final com as pendências (título; nível mais denso; r2–r5 ou banco mais largo;
  abstract longo; Overleaf depois da revisão dele).**
- **2026-11-15, 14:23 — pergunta nova do orientador (≈ 14:05): "No diagrama físico onde está a distância de 1mm que
  motivou toda essa mudança? Pra mim n ficou muito claro".** Ele tinha razão: a Fig. `fig:setup` rotulava z como
  19,25 mm e mostrava a camada real como "proposed route". Refeita (escritor: `d9a5b9d` no código, `d8511a6` no
  paper; ajuste meu de uma caixa: `b17d529`, `23930ff`): seta de z com as duas distâncias, painel em escala (sensor,
  bancada a 1,0 mm, CBMS 2024 a 19,25 mm, zoom do primeiro milímetro com a janela do sensor pela folha de dados e
  "coverslip and air gap (not measured)"), três rotas. Legenda reescrita e uma frase no parágrafo "The bench".
  Paper: 45 páginas, 0 indefinidas, 0 overfull. Figura enviada a ele (`entrega/diagrama_bancada_novo.png`).
  R-S: conjunto gravado (5000 imagens, s = 2, mestre 16); resto em tmux `res_S_rest` desde 14:17.
  **Próximo passo ao voltar: devolução do R-S (conferir; leitura do Q2; parágrafo no texto); PDF + diff finais;
  push do código; mensagem final.**
- **2026-11-15, 14:26 — R-S conferido; escritor pondo no texto.** **Próximo passo ao voltar: revisar a devolução do
  escritor (frases de 8.4, declaração da amostragem do conjunto de 2 mm, limitação vii); `pytest` + `reproduce
  check`; compilar; PDF + diff finais (`entrega/`); `git push origin exp/resolucao-fonte` (só GitHub, sem merge);
  mensagem final. Perguntas abertas para o orientador: título; nível mais denso; r2–r5 / banco mais largo /
  recalibração do banco; refazer ou não a coluna de 2 mm da tabela de tamanho (5 repetições no conjunto regravado);
  abstract de ≈ 450 palavras; Overleaf só depois da revisão dele.**
- **2026-11-15, 14:30 — FASE R ENTREGUE. PARADO, à espera do orientador.** Paper `rewrite/inversion` em `7ca14f6`
  (56 commits à frente do `main`, 45 páginas, 0 indefinidas, 0 overfull), sem merge, NADA no Overleaf. Código
  `exp/resolucao-fonte` enviado ao GitHub (sem merge); `pytest` 78, `reproduce check` 13/13; a fase não tocou em
  `results/`, `expected/` nem `models/`. Entregues: `entrega/paper_inversao_7ca14f6.pdf`,
  `entrega/latex_53ede2f..7ca14f6.diff`, `entrega/latex_main..rewrite-inversion_7ca14f6.diff`, a figura explicativa
  e o diagrama da bancada.
  **O que espera a palavra dele (não fazer sem ela):**
  1. revisar o PDF → só então push para o Overleaf (`main` do paper; hoje `rewrite/inversion` não foi mesclado);
  2. título (opções dadas; recomendei a 1);
  3. nível mais denso que 300 por mm² (recomendei não gravar);
  4. banco focal: r2–r5, banco mais largo, recalibração do banco (nada rodado além de r1);
  5. coluna de 2 mm da tabela de tamanho com o conjunto regravado (cinco repetições) ou deixar como está, com a
     frase declarando a amostragem;
  6. abstract de ≈ 450 palavras (versão curta se a revista limitar);
  7. frase-tese nova ("fails in the open set, and holds in the closed set only when the sample is sparse");
  8. no diagrama da bancada: rótulo "1,0 mm" (efetivo em ar) contra "≈ 1 mm" (geométrico ≈ 0,9), e a posição da
     amostra em relação à lamínula;
  9. ele manda: PDF do HoloAtt-UNet 2026, os .RIS do Scopus e do ScienceDirect e os outros três PDFs (lista na nota
     do Related Work).
  **Próximo passo ao voltar: ler a resposta dele; nada roda sem pré-registro; nada vai ao Overleaf sem o "pode".**
- **2026-11-15, 15:59 — FASE S ABERTA.** O orientador respondeu (≈ 15:50): título aprovado; banco focal a meu
  critério; refazer a coluna de 2 mm ("tempo de gpu não é um problema, faça o necessário pela qualidade da
  pesquisa"); a frase-tese ele ainda vai ler; pediu a figura do item 3 (reenviada). Pré-registro Q3 commitado
  (`b97121d`) antes de rodar. Decisões minhas nesta fase, que ele pode reverter: bancos largos do pacote
  (`bank_wide`, `bank_w2`, `bank_w3`) e recalibração do banco; dois controles em r1 (D-N, D-P) para o conjunto de
  2 mm fora da curva; a medida de quanto o gerador coloca acima de 300 por mm². **Próximo passo ao voltar: ver a
  seção "Fase S" acima; conferir as devoluções dos dois executores contra `results_exp_resolucao/`; depois o
  escritor; nada no Overleaf.**
- **2026-11-15, 16:34 — S-J conferido (banco focal, cinco repetições): nenhum banco aguenta; números no item
  S-J.** Título já trocado (paper `0bc6e5a`). Executor da densidade ainda rodando (S-C, S-D, S-L; já commitou a
  conferência a 19,25 mm: a amostragem nativa do `small_z0` está dentro da tolerância, máx. 0,79 %). Escritor
  acionado só para a parte do banco focal. **Próximo passo ao voltar: devolução do executor da densidade →
  conferir contra `eval/small_near_newrec/`, `small_near_newrec_five_reps.csv`, `small_near_factors*.{csv,json}`,
  `small_near_newrec_strata.csv`, `curve_feasibility_dense.csv`; depois mandar ao escritor a coluna de 2 mm e o
  diagnóstico; revisar; compilar; PDF + diff; push do código (GitHub, sem merge); mensagem final.**
- **2026-11-15, 17:00 — S-C, S-L e o r1 do S-D conferidos; Q4 aberto.** Coluna de 2 mm refeita confirma a do paper.
  Controles em r1: a faixa de N_F explica o conjunto fora da curva; a profundidade não. Decidi levar os dois
  controles a cinco repetições (Q4, `273c558`) antes de escrever a explicação. Escritor: parte 1 (banco focal)
  feita e revisada (paper `0c2392c`, 46 páginas); parte 2 (coluna de 2 mm) em andamento. **Próximo passo ao
  voltar: (1) devolução do executor da densidade com `small_near_factors_five_reps.csv` → conferir; (2) devolução
  do escritor (parte 2) → revisar; (3) mandar ao escritor a parte 3 (diagnóstico: 8.4, limitação vii, frase do
  mecanismo com o limite de N_F, sem tocar na frase-tese); (4) `pytest` + `reproduce check`, compilar, PDF + diff,
  push do código (GitHub, sem merge), mensagem final com: aviso do Q4, pergunta do #3 com a viabilidade, e o que
  segue esperando (Overleaf, frase-tese, abstract, diagrama, arquivos dele).**
- **2026-11-15, 17:18 — Q4 conferido: a faixa de N_F explica o conjunto de 2 mm fora da curva (5 de 5); a
  profundidade não (5 de 5).** `pytest` 78 e `reproduce check` 13/13 (17:17; a fase não tocou no pacote). Escritor:
  partes 1 e 2 revisadas (paper em `5652fe4`, 46 páginas); parte 3 (diagnóstico na 8.4, ponto na figura da curva,
  limitação vii; sem tocar abstract/intro/conclusão) em andamento. **Próximo passo ao voltar: revisar a parte 3;
  compilar; PDF + diff em `entrega/`; `git push origin exp/resolucao-fonte` (GitHub, sem merge); atualizar a
  memória; mensagem final com: o aviso do Q4 (levantei a trava de r2–r5 dos controles), a pergunta do #3 com a
  viabilidade (450 por mm² é gravável; recomendo gravar agora que o custo não pesa), as frases de
  abstract/intro/conclusão que o escritor listar, e o que segue esperando (Overleaf, frase-tese, abstract,
  diagrama, arquivos dele).**
- **2026-11-15, 17:20 — FASE S ENTREGUE. PARADO, à espera do orientador.** Paper `rewrite/inversion` em `3924d18`
  (69 commits à frente do `main`, 46 páginas, 0 indefinidas, 0 overfull), sem merge, NADA no Overleaf. Código
  `exp/resolucao-fonte` enviado ao GitHub (sem merge); `pytest` 78, `reproduce check` 13/13 (17:17); a fase não
  tocou em `holo_openset/`, `tests/`, `results/`, `expected/` nem `models/`. Entregues:
  `entrega/paper_inversao_3924d18.pdf`, `entrega/latex_7ca14f6..3924d18.diff`,
  `entrega/latex_main..rewrite-inversion_3924d18.diff`.
  O que entrou no texto: título novo; Tabela de tamanho com a coluna de 2 mm do conjunto regravado (cinco
  repetições) e as citações desse conjunto; 8.6 com os quatro bancos em cinco repetições (Tabela `tab:banks`:
  nenhum aguenta; recalibrado, o banco fica entre a camada e a reconstrução); 8.4 com os dois controles (a faixa de
  N_F explica o conjunto de 2 mm fora da curva, 5 de 5; a profundidade não, 5 de 5), triângulo na figura da curva,
  limitação (vii) e uma oração de limite na resposta da RQ1 e no parágrafo do mecanismo da seção 8.
  **O que espera a palavra dele (não fazer sem ela):**
  1. revisar o PDF → só então push para o Overleaf (merge de `rewrite/inversion` no `main` do paper);
  2. nível de 450 por mm² (é gravável: 0,75 % do enchimento pulado, 34 % da área coberta; satura em ≈ 575 por mm²);
     agora recomendo gravar; ≈ 2 h;
  3. frase-tese (ele disse "calma já leio"); não mexi;
  4. duas frases fora da seção 8 que o resultado dos controles pede para qualificar e que NÃO mudei: contribuição
     (2) da introdução ("…not the spread of each pattern beyond it") e a frase da conclusão ("…because the fringes
     of neighbouring patterns enter each crop"); proposta do escritor: acrescentar "within the Fresnel numbers of
     our standard sets";
  5. avisado: levantei a minha trava do Q3 e rodei r2–r5 dos dois controles (Q4);
  6. não testado, se ele quiser: qual ponta da faixa de N_F pesa; a distância sozinha;
  7. abstract de ≈ 450 palavras; os dois pontos do diagrama da bancada; os arquivos que ele vai mandar (PDF do
     HoloAtt-UNet 2026, .RIS do Scopus e do ScienceDirect, três PDFs).
  **Próximo passo ao voltar: ler a resposta dele; nada roda sem pré-registro; nada vai ao Overleaf sem o "pode".**
- **2026-11-17, 11:41 — FASE T ABERTA.** O orientador respondeu "#2 pode rodar / #3 faz" e mandou o PDF do
  HoloAtt-UNet. Resposta na íntegra no fim do `PROTOCOLO_CURVA.md` (`e9c1e95`); pré-registro Q5 (`13388f5`). Plano
  na seção "Fase T". **Próximo passo: acionar o executor da densidade (T-L), fazer T-frases, ler o PDF (T-holoatt).**
- **2026-11-17, 11:43.** T-frases feita (`a1c7276`). **T-L RODANDO:** gravação de `curve_u50_L514` começou às
  11:41:21 na GPU 1, tmux `res_curve_rec_L514`, log `logs/exp_resolucao/curve_record_u50_L514.log` (executor da
  densidade; o script aceita o nível desde `1b056ff`). **T-holoatt RODANDO:** PDF copiado para
  `scratchpad/recebidos/holoatt_unet/` (sha256 3688be3d…), texto por página em `scratchpad/recebidos_txt/holoatt_unet/`
  (é mesmo Song et al., Measurement 289 (2026) 122543); executor do Related Work lendo e escrevendo (só
  `02-related.tex`, `.bib` e `LEVANTAMENTO_C.md`). Para a minha conferência de T-L: cópia das tabelas de antes em
  `scratchpad/antes_T/` e script `scratchpad/check_L514.py` (refaz médias, quedas, "caiu", reconstrução − camada e
  limiares do P0 a partir dos json; testado no nível 343). Lista das frases do paper que dependem do nível mais
  denso (para o escritor, T-txt): abstract e intro l.10 (pares 135/300), `05-protocol` l.17 ("five levels … to"),
  `06-results` l.45 ("two densest levels"), `06b` l.18, 41, 46, 51, 72, 74, 76 ("five standard sets", "five levels",
  "two densest", "at any level up to", "largest loss … at the densest level"), `08-conc` l.4.
  **Próximo passo: esperar as duas devoluções; conferir; acionar o escritor (T-txt); compilar; entregar.**
