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
- [!] P5. **CHECKPOINT DO PILOTO ENTREGUE (17:30): `docs/exp_resolucao/CHECKPOINT_PILOTO.md` + PDF + folha de
      exemplos. PARADO, aguardando o orientador.** Decisões pedidas: (1) rodar as outras quatro repetições (≈ 8 min
      cada, sem regravar; recomendo); (2) dois controles em r1, pré-registrados: letras do base a 19,25 mm com o
      gravador e a cena novos (controle do código) e o conjunto de 1 mm com a densidade relativa do base, ≈ 154
      letras por janela (controle da vizinhança); (3) treinar também com 50 µm de profundidade. **Nada disso roda
      sem a resposta dele.** Não investiguei por que os crops melhoraram (candidatos: coerência, vizinhas mais
      longe, código novo; o `small_near` não fecha com os dois primeiros).
- [x] C-extra. (feito, `bed038c`) CBMS 2024 lido inteiro; entrada [11] de `LEVANTAMENTO_C.md` atualizada. O artigo
      afirma o custo da reconstrução em várias frases, usa "iterative" uma vez (p. 365), **não mede** tempo de
      reconstrução nem de inferência (só tempo de treino no Colab, T4, p. 368), é detecção com YOLOv5/v8/v9 em
      conjunto fechado de 26 letras (mAP50 0,986 do v8 na Tabela I; os 96,8 % de precisão só aparecem no resumo), sem
      conjunto de teste e sem baseline de reconstrução; os próprios autores adiam o tempo real (p. 369). Para a parte
      B: `02-related.tex` descreve [11] como classificação (é detecção); a leitura "z = 50k = 5·10⁴ λ" é nossa (pelo
      código); a descrição do conjunto público em `03b-bench.tex` não se confere pelo texto do artigo, só pelo
      código do gerador. Tom: trabalho nosso, corrigido por medição.

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
