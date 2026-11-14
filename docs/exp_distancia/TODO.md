# TODO: fechar o estudo de distância/autofocus e levar para o código e o paper

Arquivo de plano e progresso. **Se você perdeu o contexto, leia este arquivo inteiro antes de qualquer coisa.**
Ele é atualizado a cada etapa concluída (e commitado junto). O caderno (`CADERNO.md`) continua sendo o registro
detalhado de comandos e resultados; aqui fica só o plano, o estado e as decisões.

## 1. O pedido (2026-11-14)

Depois de ler `RELATORIO.md`, o orientador (Rodrigo) colou uma revisão do relatório e pediu, com as palavras dele:

> "Atualiza o projeto de código e latex depois de fazer o que faltou"

e, em seguida:

> "E registra o que vc ta fazendo e planejando num TODO pq seu contexto é pequeno e vive compactando, então pra vc
> não se perder tem que ter um arquivo de registro dos planos e progresso que seja claro pra vc se encontrar mesmo que
> esqueça tudo que tava fazendo"

A revisão colada (texto de quem escreveu o protocolo) aceita o resultado e lista:

**O que conferir antes de aceitar ("o que faltou")**

1. `frame_5` contra `session_5` não foi comentado e o protocolo pedia. Mesma distribuição de z, mas `rec_z0` dá 0,865
   em `frame_5` e 0,753 em `session_5`; o stack, 0,924 contra 0,839. Hipótese: `session_5` tem só 8 sorteios de z
   (as 8 sessões de teste) e saíram desfavoráveis; então a coluna de 5 % da Tabela 10 do paper exagera o dano.
   Pede os 8 valores de z do `sessions.csv` da variante.
2. A vantagem que sobra (1,28×) é detalhe de implementação: vem dos "canais" (escala por percentil com
   `torch.quantile`, 1,78 ms em GPU), que só o fluxo convencional paga; idem os 15 ms de leitura do blank frame da
   Tabela 7. Nenhum desses números deve virar argumento no paper.
3. O n\* em CPU é instável (denominador ≈ 0,1 s, diferença de dois tempos de ≈ 2,4 s). Dizer que o stack custa o
   mesmo que uma reconstrução, sem ponto de cruzamento preciso.
4. A busca barata assume z₀ conhecido com ±13 % de folga. O paper precisa dizer essa suposição.
5. Desvios de processo (checkpoints sem aprovação, runs por agente interrompido): revisar o diff do branch antes de
   qualquer número ir para o paper, principalmente o RNG por quadro e a inclinação (pareamento das cenas).
6. Ambiguidade A/B do critério: adotar a leitura A (mesma tolerância de 0,02 dos dois lados).

**O que muda no paper**

- RQ4: nenhuma rota é mais barata de um jeito que importe; o custo é o detector (> 95 % do tempo fim a fim nos
  fluxos baratos). O argumento de tempo do stack sai das contribuições.
- Seção 7.5(ii) e "Which flow to use": trocar "ruído e iluminação quebram o autofocus" por "quebram a busca cega
  na resolução do sensor". A busca reduzida e estreita (`rec_afc`) entra como baseline na Tabela 3. Trocar ou
  complementar a coluna `session_5` com `frame_5`.
- O que sobra do stack: dispensa λ, Δ, z e blank frame, tolera drift dentro do jitter, ganha um pouco sob shot
  noise forte (+0,013, 5/5); perde 0,08 sob feixe estreito e ≈ 0,03 nos quadros inteiros.

## 2. Regras que valem o tempo todo

- Modo de trabalho pedido pelo orientador: subagentes Opus 5.5 (effort high) executam; o modelo principal planeja,
  revisa e garante a consistência. Um único escritor no caderno por vez.
- Commits: sem nenhuma linha de atribuição (nem `Co-Authored-By`, nem `Claude-Session`) no repositório de código;
  um commit por unidade lógica; mensagens em inglês (convenção do repo). **Nunca dar push sem confirmação do
  orientador** (nem no GitHub, nem no Overleaf).
- DGX: poucas threads por processo (≤ 4–16), total de threads prontas < ~64, jobs longos em `tmux` com checkpoint,
  subir jobs um a cada 1–2 min, nada em `/tmp` (usar o scratchpad da sessão ou `privado`).
- Estudo pré-registrado: não escolher nada olhando o teste; nenhum fluxo/conjunto novo no teste sem registrar antes
  no caderno o que e por quê; não comparar tempos de runs ou máquinas diferentes na mesma tabela; toda tabela de
  tempo com a coluna fim a fim; não descartar repetição/sessão "estranha".
- Paper: um só pipeline (`holo_openset`), nada de nomes internos (E12 etc.) no texto; legenda de figura explica
  cada painel; nunca afirmar bit-exato entre builds.
- Ambiente: `source scripts/exp_distancia/env.sh`; `pytest` e `reproduce check` com `env -u HOLO_RESULTS`.

## 3. Onde as coisas estão

- Código: `/home/jovyan/compartilhado/ralph/openset-microscopy/holo-openset`, branch `exp/distancia-autofocus`
  (saiu de `9488fce` = `main`), só local. Relatório `docs/exp_distancia/RELATORIO.md`, caderno `CADERNO.md`,
  protocolo `PROTOCOLO.md`, resultados `results_exp_distancia/`, gerador `holo_openset/paper/distance.py`,
  regeneração `bash scripts/exp_distancia/relatorio.sh`.
- Paper: `/home/jovyan/compartilhado/ralph/openset-microscopy/latex-openset-microscopy` (Overleaf, branch `main`,
  último commit `de1c95a` de 2026-11-02; seções em `sections/*.tex`). Até aqui a regra era não editar as seções; o
  pedido de hoje ("atualiza o projeto de código e latex") muda isso para esta tarefa.

## 4. Plano

Estado: `[ ]` a fazer, `[~]` em andamento, `[x]` feito (com commit).

### Fase A: o que faltou (conferências e análise)

- [x] A1. `frame_5` × `session_5`: os 8 z de teste, F1 por sessão × desvio, quanto a amostra de 8 exagera.
- [x] A2. Revisão do diff do branch (RNG por quadro, inclinação, pareamento das cenas) + checagens empíricas.
      Leitura feita por mim em 2026-11-14 (`sim/generate.py`, `reconstruct.py`): o jitter por quadro, o drift e a
      inclinação usam geradores próprios (`+800_000_000`, `+600_000`, `+650_000`), o ruído da câmera mantém a
      semente do base, o blank frame fica o da sessão, e `robustness.py` já afirma (`assert`) que as anotações de
      cada variante são as do base. Nada errado na leitura. Falta a checagem empírica (subagente "análise").
- [x] A3. n\*: sensibilidade do denominador (GPU e CPU); reescrever como "custa o mesmo", sem cruzamento preciso.
- [x] A4. "Canais" e leitura do blank frame como detalhe de implementação: conta do front end sem os canais, com a
      ressalva de que escala fixa não foi testada; tirar o 1,28× das frases sugeridas.
- [x] A5. Suposição de z₀ conhecido a ±13 %: no relatório e no paper.
- [x] A6. Leitura A do critério como principal (gerador, macros, relatório).
- [~] A7. Relatório e caderno atualizados com A1–A6 (feito, commits `ea592c8`…`bd0092c`); falta o PDF novo
      para o orientador (gerar no fim, com `relatorio_pdf/build.sh` do scratchpad ou equivalente).

### Decisões de desenho (tomadas em 2026-11-14, depois de ler o paper e os geradores)

- D1. Numeração do paper local (= Overleaf, `de1c95a`): Tabela 3 = `tab:main`, 8 = `tab:stages`, 9 = `tab:full`,
  10 = `tab:robustness`, 11 = `tab:stack`; Seção 7 = Results (7.4 = RQ4, 7.5 = RQ5); "Which flow to use" está em
  `07-discussion.tex`. A prosa do `prop`/stack ainda é nota `\todo` (04-method:62, 06-results:62).
- D2. Nomes no paper: `rec_af` = "blind autofocus", `rec_afc` = "narrow autofocus". `rec_afc` vira fluxo do paper
  (depois de `rec_af` no `ORDER`), usando o modelo de `rec_af` (sem treino novo).
- D3. Tabela 10: coluna nova `rec_afc` nas 33 linhas (precisa simular as 28 variantes que não estão em
  `data/variants`) e 3 linhas novas (`frame_2`, `frame_5`, `walk_05`) para todos os fluxos.
- D4. Tempo: `results/timing_{gpu,cpu}.csv` passam a ser os da sessão E5 (cobre todos os estágios do paper e
  `autofocus_afc`); `tab_stages` ganha a linha da busca reduzida; `tab_full` vem de um run novo de quadros inteiros
  com todos os fluxos do paper + `rec_afc`.
- D5. Macros do estudo (`\Dist…`) entram no paper como segundo arquivo, `figures/paper/numbers_distancia.tex`
  (`\input` no `main.tex`), gerado por `python -m holo_openset paper distance`. Teste de consistência entre
  `results/` e `results_exp_distancia/` nas linhas comuns.
- D6. LaTeX: commit de assets e commit de texto separados; **sem push**. Texto: só o que a revisão lista (ver C2).
- D7. Leitura A do critério é a principal.
- D8. Não fazer: experimento de escala fixa, "busca barata a cada M", `full_frames` em CPU, reempacotar Zenodo
  (ficam listados como pendência do orientador).

### Fase B: projeto de código

- [x] B1. (FEITO, commits `18112a7`…`9b0c71e`) Runs (subagente "integração-runs"; caderno próprio em `docs/exp_distancia/CADERNO_INTEGRACAO.md`):
      simular as 28 variantes que faltam (teste); caches `rec_afc` nelas; caches `rec_edf`/`rec_twin` em
      `frame_2`/`frame_5`/`walk_05`; `robustness` em `results/` (`rec_afc` × 33 conjuntos; fluxos do paper × 3
      conjuntos novos); oráculo nos 3 conjuntos; `evaluate` e `e2e` de `rec_afc`; `full_frames` (um run, todos os
      fluxos do paper + `rec_afc`); promover os csv de tempo da E5 e o erro de distância (`focus_error`) para
      `results/`.
- [x] B2. (FEITO; fase 2: commits `fae1cdc`, `5ee85a4`, `821f985`, `09406bf`, `c0dabe0`, `49c3f06`, `6be9587`,
      `135fa4a`, `592403d`) (fase 1, código, FEITA: commits `08031fa`, `fd90020`, `644c750`, `cba99f0`, `e880564`, `8138b79`,
      `080729b`; fase 2 pendente) Geradores do paper (`style.py`, `tables.py`, `figures.py`): `rec_afc` no `ORDER`, linha da busca em
      `tab_stages`, linhas/coluna novas em `tab_robustness`, macros; figuras que usam `ORDER`
      (`fig_robustness`, `fig_cost`); `pipeline.py` (jobs novos), `reproduce.py`/`expected/` (incluir
      `numbers_distancia.tex`), testes, README/docs. `pytest` e `reproduce check` verdes.
- [x] B3. (feito 2026-11-14: `pytest` 37 passam, `reproduce check` 13/13, rodados por mim) Revisão minha: diff de B1/B2, números das tabelas novas contra `results_exp_distancia/`.

### Fase C: projeto LaTeX (`latex-openset-microscopy`, sem push)

- [ ] C1. Assets: `figures/paper/tables/*.tex`, `numbers.tex`, `numbers_distancia.tex`, figuras regeneradas;
      cabeçalhos/legendas dos floats (`tab:main`, `tab:stages`, `tab:full`, `tab:robustness`, `fig:robustness`,
      `fig:cost`); `\input` das macros novas no `main.tex`. Um commit.
- [ ] C2. Texto (outro commit), só o que a revisão lista:
      - 04-method (flows): definir o "narrow autofocus" e dizer a suposição (z₀ conhecido a ±13 %).
      - 05-protocol (Time): a frase da carga do servidor (era load ≈ 230) conforme a sessão E5.
      - 06-results RQ4: resposta mais simples (nenhuma rota é mais barata de um jeito que importe; detector > 95 %
        do tempo); busca uma vez por montagem; números de tempo novos.
      - 06-results RQ5 (i)/(ii) e "Answer to RQ5": "quebram a busca cega na resolução do sensor", `frame_5` ao lado
        de `session_5` (8 sorteios).
      - 07-discussion: "The question about image size", "Which flow to use", limitação (iii)/(v).
      - 00-abstract e 08-conc: as frases "noise that misleads the autofocus".
      - notas `\todo` do `prop`/stack: o que sobra do stack (sem argumento de tempo).
- [ ] C3. Compilar com `tectonic`, conferir macros indefinidas e números do texto.

### Fim

- [ ] Mensagem final ao orientador: o que mudou, onde, o que ficou para ele decidir (push nos dois repositórios,
      merge do branch em `main`, Zenodo, nomes "blind/narrow autofocus", troca da sessão de tempo).

## 4b. Especificação das edições de texto do paper (C2), rascunho de 2026-11-14

Regra: mexer só nas frases abaixo, mantendo a voz do texto; todo número por macro (`\Rob…`, `\Full…`, `\T…` de
`numbers.tex`; `\Dist…` de `numbers_distancia.tex`); fechar os números depois dos resultados de A e B. A prosa do
`prop`/stack continua sendo do orientador (notas `\todo`); eu só atualizo as notas.

- `04-method.tex`, lista de fluxos (linhas 119–125): o item "autofocus" passa a "**blind autofocus**" (73 + 41
  candidatos em [0,2; 2,1] z₀, no holograma na resolução do sensor); item novo "**narrow autofocus**": mesmo
  critério, 7 candidatos em ±10 % de z₀ e 11 em volta do melhor (logo dentro de ±13 %), sobre a amplitude média de
  4 × 4 pixels (18 reconstruções de 1/16 dos pixels), configuração escolhida na validação antes do teste, usa a rede
  do blind autofocus (só a distância muda), precisa de z₀ a ±13 %. Frase final "The reconstruction flows need…":
  acrescentar a suposição. Nota `\todo` na contagem "eight flows" da introdução (não mudar o número: a prosa do
  `prop`/stack ainda não entrou).
- `05-protocol.tex`: (Data, robustness sets) acrescentar a distância sorteada por imagem (2 e 5 %) e o drift lento
  dentro da sessão (passeio aleatório, 0,5 % por imagem); "their own autofocus" → os dois. (Time) trocar a frase da
  carga ≈ 230 pela da sessão nova (carga 59–89; a anterior era cerca de 2× mais lenta, uniformemente): conferir os
  números com o caderno de integração.
- `06-results.tex`:
  - RQ1, última frase do 1º parágrafo ("searching the distance changes almost nothing… \RecAfFone"): pode ganhar
    `\RecAfcFone`; opcional.
  - RQ4, 1º parágrafo: depois de "The autofocus (114 of them) takes…": a busca não precisa ser tão longa (narrow:
    18 reconstruções de 1/16 dos pixels, X ms por quadro em GPU e Y s em CPU, N× menos), e com a distância fixa na
    sessão ela é paga uma vez por sessão (F1 igual ao da busca em todo quadro: macros `\Dist…`).
  - RQ4, "On a whole acquisition": números do narrow autofocus (`\FullRecAfc…`).
  - RQ4, "Answer to RQ4": mais simples — nenhuma rota é mais barata de um jeito que importe; o detector leva mais
    de 95 % do tempo de todo fluxo que não repete a reconstrução (macro nova de participação do detector).
  - RQ5 (i): `frame_5`/`frame_2`/`walk_05` ao lado de `session_5` (que são 8 sorteios): texto conforme o achado A1.
  - RQ5 (ii): "Noise and illumination break the **blind** autofocus": a fragilidade é da busca cega na resolução do
    sensor (falhas grosseiras 70 % e 74 %); o mesmo critério na amplitude reduzida 4 × 4 e em ±13 % falha em 1,8 %
    e 0,2 % e mantém `\RobFullwellFiveZeroZeroRecAfc` e `\RobBeamNarrowRecAfc`. Sai a frase "The step that
    protects the conventional route… is the most fragile one under noise".
  - "Answer to RQ5": tirar "noise or illumination that mislead the autofocus" como caso em que o ranking vira;
    fica a fonte que borra as franjas; ruído e feixe estreito enganam só a busca cega.
  - Cabeçalho e legenda da Tabela 10 (coluna "narrow AF", linhas novas), legendas de `tab:main`, `tab:stages`,
    `tab:full`, `fig:robustness`, `fig:cost` (isso é C1).
  - "Fidelity of the reconstruction": erro mediano do narrow ao lado do blind (macro `\Dist…`).
  - Nota `\todo` da linha 62 (prosa do stack): acrescentar o que sobra do stack — sem λ, Δ, z nem blank frame;
    tolera drift dentro do jitter; +0,013 sob shot noise forte (5/5); −0,08 sob feixe estreito contra o narrow AF;
    ≈ −0,03 nos quadros inteiros para os stacks largos; **nenhum argumento de tempo**.
- `07-discussion.tex`: "The question about image size" (última frase sobre o autofocus: frágil só quando cego na
  resolução do sensor; estreito e reduzido custa 78× menos e não é frágil); "Which flow to use" ("add the autofocus,
  with a criterion that the noise… cannot fool—on our data the sharpness criterion was the weakest link" → o elo
  fraco era a busca cega, não o critério; buscar uma vez por montagem; "as the autofocus is" → "as the blind
  autofocus is"); Limitations: item novo com a suposição de z₀ a ±13 %; (v) tempos: sessão nova.
- `00-abstract.tex`: "robust to camera noise that misleads the autofocus" → "…that misleads a blind autofocus
  (a narrow search on a reduced image is not misled)".
- `08-conc.tex`: "the distance of the sample and the noise of the camera decide between a fixed and an autofocused
  reconstruction" → a distância decide; o ruído quebra só a busca cega.

## 5. Diário (mais recente embaixo)

- 2026-11-14, manhã: PDF do relatório enviado (commit `13d738b`: frases da Seção 4 em bloco de código).
- 2026-11-14: pedido acima recebido; este arquivo criado; começando a leitura do paper e dos geradores para
  detalhar as Fases B e C.
- 2026-11-14: paper e geradores lidos; decisões D1–D8 acima; entrada de pré-registro dos runs novos no caderno;
  subagentes "análise" (Fase A) e "integração-runs" (B1) disparados em paralelo.
- 2026-11-14: especificação das edições de texto (seção 4b) escrita enquanto os subagentes rodam.
- 2026-11-14, 09:15: estado e próximos passos, para retomar depois de uma compactação:
  - Rodando em segundo plano: subagente "análise" (Fase A; dono de `paper/distance.py`, `RELATORIO.md`,
    `CADERNO.md`, `results_exp_distancia/`, `tests/test_core.py`; GPU 5) e subagente "integração-runs" (B1; dono de
    `results/`, `data/variants/` novos, `CADERNO_INTEGRACAO.md`; GPUs 0–4; jobs em `tmux` com prefixo `integ_`).
    Cada um devolve um relatório final para mim; nenhum mexe neste arquivo.
  - Quando "análise" terminar: revisar o diff e os números dela (A1: os 8 z, previsto × medido; A3: regra do n\*;
    A6: leitura A), marcar a Fase A aqui, e disparar o subagente "geradores" (B2), que herda `paper/distance.py` e
    os testes. B2 só mexe em `sim/variants.py` e `pipeline.py` depois que B1 terminar (B1 usa `VARIANTS` para saber
    o que simular).
  - Quando "integração-runs" terminar: revisar (linhas antigas de `results/` intactas, coincidência com
    `results_exp_distancia/`, sanidade da re-simulação, run de quadros inteiros único), mandar B2 regenerar
    tabelas/figuras/macros, `expected/`, `pytest`, `reproduce check`.
  - Depois: Fase C (LaTeX) com a especificação da seção 4b, fechando os números com os resultados.
  - Compilar o paper: `cd ../latex-openset-microscopy && XDG_CACHE_HOME=/home/jovyan/privado/.persist/.cache
    /home/jovyan/privado/.persist/bin/tectonic --keep-logs -o <dir de saída no scratchpad> main.tex` (a linha de
    base de hoje compila sem referência indefinida).
- 2026-11-14, 10:20: **Fase A concluída** pelo subagente "análise" (commits `ea592c8`, `3ada8fe`, `66ec0bd`,
  `4cc6914`, `a043ff4`, `53e9154`, `60486cc`, `2143bf9`, `1c8b70d`, `8124325`, `bd0092c`) e revisada por mim. Achados:
  - A1: os 8 z de `session_5` são −10,4, +4,8, −2,2, +11,4, −1,3, +0,8, −0,7, −10,7 % (rms 6,9 %, percentil 95);
    previsto por `frame_5` para esses 8: `rec_z0` 0,745 (medido 0,753), stack 0,825 (0,839); a linha de 5 % do
    paper exagera o dano em ≈ 0,10 (`rec_z0`, `prop`) e 0,08 (stack). Macros `\DistSessFive…`.
  - A2: pareamento confirmado (anotações, z recomputado das sementes, azimute da inclinação; `tilt0` bit a bit igual
    aos quadros regravados com o código do paper neste build).
  - A3: regra ±3 %/fator 2; só o stack de 5 em CPU vira "≈ same cost"; GPU no limite (2,0–3,9 e 155–304).
    Assimetrias não corrigidas: 0,36 ms de conversão não cobrados; `embed` medido com o modelo de 3 canais.
  - A6: leitura A principal (1 de 24); B fica como alternativa (2 de 24).
  - Detector > 95 % só em GPU (CPU 82–94 %): o texto do paper diz "on a GPU".
  - `pytest` 24 passam e 1 falha, `reproduce check` 9/12: esperado enquanto `expected/` não for refeito (B2).
  Próximo: disparar "geradores" (B2, fase 1: código); "integração-runs" (B1) continua rodando (`tmux integ_*`).
- 2026-11-14, 10:30: subagente "geradores" (B2) disparado na **fase 1 (só código)**: `rec_afc` no `ORDER`
  ("narrow autofocus"; `rec_af` vira "blind autofocus"), linhas/coluna novas das tabelas, macros novas
  (participação do detector em GPU, razão cega/estreita), `numbers_distancia.tex` como asset do paper e no
  `reproduce check`, testes de consistência em `tests/test_paper_integration.py`, docs. Ele para ao fim da fase 1 e
  devolve um relatório. **Fase 2 (regenerar tudo, `expected/`, figuras, `pipeline.py`, `sim/variants.py`) só começa
  com uma mensagem minha, depois que "integração-runs" (B1) terminar** — mandar por `SendMessage` ao mesmo agente,
  para ele manter o contexto.
- 2026-11-14, 10:35: **B2 fase 1 concluída** ("geradores"): `rec_afc` no `ORDER` de `tables.py` (única fonte),
  nomes "blind autofocus"/"narrow autofocus" (curtos "blind AF"/"narrow AF"), linha `autofocus_afc` em `tab_stages`,
  3 linhas + coluna em `tab_robustness`, macros novas (`TBlindOverNarrow{Gpu,Cpu}Big`, `FullDetectPct<Flow>`,
  `FullDetectPctMin[Floor|Flow|Of]`, `FocusBlind…`, `FocusNarrow…`; `TLayerBank*` virou `TLayerBankJit*`),
  `paper distance` lê `results_exp_distancia/` por conta própria (`HOLO_DIST_RESULTS`), entrega
  `numbers_distancia.tex` em `$HOLO_PAPER`, opção `--no-figures`; `reproduce check` cobre os dois arquivos de macros
  (13 itens); testes novos em `tests/test_paper_integration.py`; docs. `pytest`: 33 passam, 1 falha (`expected/`
  velho, esperado), 1 pulado (run novo de quadros inteiros).
  Minhas decisões sobre as perguntas dele (mandar na mensagem da fase 2):
  - linha do stack em `tab_stages` usa `layer_bank_jit`: **aceito**;
  - Wiener entra no conjunto do mínimo da participação do detector: **aceito**;
  - `rec_twin` passa a "blind autofocus + twin removal": **sim**;
  - linhas comuns de robustez: iguais (1e-12) nos conjuntos novos e nas de `rec_afc`; ≤ 0,01 nas outras (as do paper
    vêm dos conjuntos publicados, de outro build; diferença máxima vista 0,0023 em F1): **aceito**, e o paper diz;
  - `paper` sem argumento continua `tables figures` (sem `distance`): **aceito**;
  - `checksums/data.sha256`: **não** rodar `write-data-sums`; acrescentar só os 3 conjuntos novos;
  - patch da fase 2 (não aplicado) em `scratchpad/geradores/phase2/phase2_pipeline_variants.patch`: os 3 conjuntos
    passam para `VARIANTS`; `pipeline.py` ganha `rec_afc` (caches `afc`, `eval_rec_afc_r*`, flows nos
    experimentos); 583 jobs.
  Zenodo: nada a reempacotar (os tars só têm base, ideal, small, full frames e modelos).
- 2026-11-14, 10:40: subagente "latex" disparado para **rascunhar** as edições do paper num clone de rascunho
  (`scratchpad/latex_work`, branch `integration-draft`, dois commits: floats e prosa), sem tocar o repositório real.
  Ele devolve cada trecho antigo/novo para eu revisar. A aplicação no repositório real só depois da fase 2 de B2
  (assets finais). B1 ainda roda: 23 de 35 conjuntos simulados às 10:31 (≈ 3 min por conjunto), depois a coluna de
  `rec_afc`, o oráculo, o run de quadros inteiros e `focus_battery.csv`.
- 2026-11-14, 10:55: **rascunho do LaTeX devolvido e revisado por mim.** Clone:
  `scratchpad/latex_work`, branch `integration-draft`, commits `46e5fdd` (floats + `\input` de
  `numbers_distancia`) e `301e4d4` (prosa); diffs trecho a trecho em `scratchpad/latex_work/../passages.md`
  (na raiz do scratchpad da sessão: `passages.md`, `full_diff.patch`, `standins.tex`, `build.sh`, `out/main.pdf`).
  Compila com assets provisórios, 31 páginas, sem referência indefinida; `tab:robustness` (13 colunas) precisou de
  `\shrinkfit` (≈ 92 %).
  Pontos em que ele seguiu os dados contra a minha especificação (aceitos): (1) estreitar a faixa na resolução do
  sensor ainda falha (66,9 % / 21,9 % na validação); o que conserta é a média 4 × 4 (ruído) e média + faixa (feixe
  estreito) — o texto diz "blind search at the resolution of the sensor", não "frágil só quando cega"; (2) a CPU do
  run antigo era 1,95–3,34× mais lenta, não uniforme.
  Mandei a rodada 1 de revisão (R1–R9) ao mesmo agente: rótulo "blind autofocus + twin removal"; parágrafo de
  tempo com literais (carga entre 59 e 89; run antigo ≈ 230, duas a três vezes mais lento, desigual); "every flow
  that does not repeat the reconstruction on the whole frame"; frase do que removeu as falhas (validação); legenda
  de `tab:stages` sem "such as"; rótulos "distance per image"; RQ5 (iv) com o valor do narrow; nota `\todo` em
  "generalises best to new classes".
  **Para a fase 2 de B2 (além das decisões já listadas):** macro `\DistGrossPct` (= 1) em `distance.py`; rótulos de
  exibição "distance per image (%)" e "distance drift per image (%)" em `tables.py`; célula do flat field em GPU na
  janela imprime "0.0" (0,03 ms): dar 2 casas quando < 0,05; `rec_twin` = "blind autofocus + twin removal".
  **Pendências para avisar o orientador (fora da lista de edições):** "within the depth of field" com erro mediano
  de ≈ 50 µm contra profundidade de campo ≈ 30 µm (`03b-bench`); "its embedding generalises best to new classes"
  contradito por `tab:enroll` para `prop`/stack; `tab:stack`/`fig:stack` chamam de "drift" a distância entre sessões
  (8 sorteios); razões 2,6×/1,3×/2,3× da legenda de `tab:stages` vêm de medições antigas.
  Itens CHECK-AFTER-RUNS do rascunho (resolver com os números finais): F1/tempo de `rec_afc` nos quadros inteiros;
  "few tens of milliseconds" da leitura do blank frame (o run do estudo deu ≈ 15 ms); participação do detector
  ≥ 95 % com `rec_afc`; "0.04" = twin − learned; `rec_afc` em `session_5`, `fullwell_500`, `beam_narrow` e no resto
  da bateria (a 0,01 de `rec_z0`/`rec_af`, menos onde os dois falham).
  Runs (B1) às 10:52: 35 conjuntos simulados; caches `rec_afc` em andamento (`tmux integ_afc`); faltam robustez 3a,
  oráculo, quadros inteiros, `focus_battery.csv`.
- 2026-11-14, 11:10: rodada 1 de revisão do LaTeX aplicada no clone (commits novos `26e867b` floats, `6e9a258`
  prosa, sobre `46e5fdd` e `301e4d4`); compila. Macros que o rascunho usa e ainda faltam: `\DistGrossPct`,
  `\FullRecAfc{ComputeMs,TotalS,Fone}`, `\Rob{SessionFive,FullwellFiveZeroZero,BeamNarrow,SourceFivecm}RecAfc`;
  para a nota `\todo` de enrollment: `\PropEnroll{Five,All}`, `\BankJitEnroll{Five,All}` (pedir a B2 na fase 2:
  macros de enrollment para todos os fluxos). CHECK novo (9): `\RobSourceFivecmRecAfc` tem de ser um colapso
  (≈ 0,5 ou menos) ou a frase de RQ5 (iv) muda.
  Falta: B1 terminar → fase 2 de B2 → aplicar o rascunho no repositório real com os assets finais.
- 2026-11-14, 11:50: **B1 concluído** ("integração-runs") e revisado por mim.
  - Conferi por fora: todas as linhas antigas de `results/robustness.csv` (2278), `e2e.csv` (50) e `oracle.csv`
    (330) continuam lá; a maior mudança é 1,1e-16 (o `save()` reescreve o csv e mexe no último dígito). O run novo
    de quadros inteiros reproduz a acurácia antiga dos dez fluxos (maior mudança 9e-5 em F1).
  - `rec_afc` na bateria (5 repetições): acompanha a melhor entre `rec_z0` e `rec_af` nos 36 conjuntos; maior perda
    −0,0012 (`laser`); `fullwell_500` 0,949, `beam_narrow` 0,959, `session_5` 0,964, `source_5cm` 0,518 (colapso,
    como `rec_z0` 0,514 e `rec_af` 0,418). Nenhum conjunto com perda > 0,02.
  - Linhas novas (F1): `frame_5` `rec_z0` 0,865, `prop` 0,865, stack 0,924, `learned` 0,886, `wiener` 0,814,
    `rec_af`/`rec_afc` 0,964; oráculo (det) 0,67–0,70.
  - Quadros inteiros (um run, GPU 3 a 0 % antes e depois, 11:34–11:40): `rec_afc` F1 0,9752 (det), busca 2,04 ms,
    fim a fim 199,9 ms (`rec_z0` 198,7; `raw` 179; `rec_af` 322; `rec_twin` 407); detecção 171 ms; leitura
    ≈ 20 ms nos fluxos de reconstrução contra ≈ 3 ms nos de camada (o texto "few tens of milliseconds" tem de mudar).
  - Erro de distância na bateria (`results/focus_battery.csv`): a busca estreita erra mais em `depth_300` (23 % de
    falhas grosseiras), `band_40` (12 %), `source_5cm` (7 %), `pinhole_200` (5 %), sem perder F1.
  - Desvios dele, aceitos: correção em `experiments/oracle.py` (rótulos via `ALL`); caches `rec_edf`/`rec_twin` do
    base refeitos neste build (não existiam mais); detecções YOLO refeitas para o `e2e` (uma falsa detecção a menos
    em r1); condição extra de load < 120 para o run de tempo; coluna `value` dos 3 conjuntos novos gravada como
    `2.0`/`5.0` (nenhum gerador lê).
  - Disco: +53,5 GB em `compartilhado`.
  **B2 fase 2 disparada** (mensagem ao agente "geradores"): aplicar o patch de `sim/variants.py`/`pipeline.py`,
  `\DistGrossPct`, macros de enrollment para todos os fluxos, rótulos de exibição "per image", formato do flat
  field, `rec_twin` = "blind autofocus + twin removal", regenerar tabelas/figuras/macros em `output/paper/`,
  `expected/`, `reproduce check` 13/13, `pytest` verde, docs, checksums dos 3 conjuntos novos.
  Depois: mandar o agente "latex" aplicar o rascunho (4 commits no clone) no repositório real com os assets finais,
  resolver os CHECK-AFTER-RUNS e compilar; eu reviso o diff final; PDF novo do relatório; mensagem final.
- 2026-11-14, 12:10: **B2 fase 2 concluída e conferida por mim** (`pytest` 37 passam, sem falha nem pulo;
  `reproduce check` 13/13). Assets finais em `output/paper/` (`numbers.tex` 807 macros, `numbers_distancia.tex`
  1916, 11 tabelas, 15 figuras). Nenhuma macro existente que não seja de tempo mudou de valor; 85 macros de tempo
  mudaram (sessão E5 e run novo de quadros inteiros); 143 macros novas; `TLayerBank*` → `TLayerBankJit*`.
  Valores para o texto: `rec_afc` nos quadros inteiros F1 0,975, cálculo 5,2 ms, total 0,20 s (`rec_z0` 0,20;
  `learned` 0,18; cega 0,32; twin 0,41); leitura 20 ms (reconstruções) contra 3 ms (camadas); participação mínima do
  detector 95,1 % (dada pelo narrow autofocus); `source_5cm` 0,52. Fila do paper: 583 jobs, 35 conjuntos de
  robustez. `checksums/data.sha256` ganhou os 3 conjuntos novos; as 32 variantes antigas em disco foram
  re-simuladas neste build e não batem mais com os checksums publicados (explicado em `docs/DATA.md`).
  Olhei `fig_cost` e `fig_stack` regeneradas: legíveis, com o marcador aberto do narrow AF e linha de chamada.
  **Agente "latex" disparado para aplicar o rascunho no repositório real** (dois commits: assets + floats; prosa),
  resolver os CHECK-AFTER-RUNS com os valores finais (o "few tens of milliseconds" vira macros de leitura),
  acrescentar a frase do build em 05-protocol e compilar. Falta depois: eu revisar o diff final do paper; PDF novo
  do relatório; atualizar a memória; mensagem final.

