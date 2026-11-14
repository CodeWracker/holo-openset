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

## 5. Plano

Estado: `[ ]` a fazer, `[~]` em andamento, `[x]` feito (com commit), `[!]` bloqueado/aguardando o orientador.

### Fase Z: definir um z razoável (vem ANTES de A; ver 4a e `PROTOCOLO_Z.md`)

- [~] Z1. Unidade do z no código (gerador original e `sim/physics.py`), com trecho, no caderno — subagente "piloto".
- [~] Z2. Refazer a tabela do orientador (z = 19,25; 5; 2; 1 mm: borrão, corte, b_max) e explicar as diferenças
      (ele tem 278 ciclos/mm a 2 mm; o nosso modelo deu 266) — subagente "piloto".
- [~] Z3. Ferramenta E(f)/b_max para qualquer configuração (CSV de configurações → tabela) — subagente "piloto".
- [~] Z4. Levantamento de 8–15 bancadas lensless, valores com página → `docs/exp_resolucao/LEVANTAMENTO_Z.md`;
      PDFs em `../referencias/z/` (fora do git) — subagente "levantamento-z". Inclui o suplemento do artigo de 2015
      (Eq. S3: unidade do "k").
- [ ] Z5. Proposta de configuração + coerência com as resoluções reportadas + consequências (eu, com Z3 e Z4).
- [!] **Checkpoint Z**: mandar tudo ao orientador e **parar**; A só anda com a aprovação dele.

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

- [~] C-agora. Em paralelo (autorizado em `PROTOCOLO_Z.md`): leitura de [11], [13], [14] com frase exata e página;
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
