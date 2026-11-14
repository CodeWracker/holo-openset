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

- [ ] B1. Runs (subagente "integração-runs"; caderno próprio em `docs/exp_distancia/CADERNO_INTEGRACAO.md`):
      simular as 28 variantes que faltam (teste); caches `rec_afc` nelas; caches `rec_edf`/`rec_twin` em
      `frame_2`/`frame_5`/`walk_05`; `robustness` em `results/` (`rec_afc` × 33 conjuntos; fluxos do paper × 3
      conjuntos novos); oráculo nos 3 conjuntos; `evaluate` e `e2e` de `rec_afc`; `full_frames` (um run, todos os
      fluxos do paper + `rec_afc`); promover os csv de tempo da E5 e o erro de distância (`focus_error`) para
      `results/`.
- [ ] B2. Geradores do paper (`style.py`, `tables.py`, `figures.py`): `rec_afc` no `ORDER`, linha da busca em
      `tab_stages`, linhas/coluna novas em `tab_robustness`, macros; figuras que usam `ORDER`
      (`fig_robustness`, `fig_cost`); `pipeline.py` (jobs novos), `reproduce.py`/`expected/` (incluir
      `numbers_distancia.tex`), testes, README/docs. `pytest` e `reproduce check` verdes.
- [ ] B3. Revisão minha: diff de B1/B2, números das tabelas novas contra `results_exp_distancia/`.

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

