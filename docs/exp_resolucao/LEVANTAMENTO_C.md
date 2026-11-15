# Levantamento C.1: o argumento de velocidade da literatura

Levantamento feito em 2026-11-14 para a parte C do `PROTOCOLO.md` (item C.1), com o complemento em índices abertos de 2026-11-15 (seção 1b; **Scopus e ScienceDirect não foram rodados**). É uma revisão narrativa, sem fluxo PRISMA. Toda frase atribuída a um trabalho foi copiada do texto, com a página. Onde o texto não estava acessível, o item aparece como "somente resumo" e não é citado entre aspas.

Convenções:

- As citações estão no idioma original. Nos PDFs de duas colunas, a extração do `gs` cola palavras e intercala colunas. Restaurei só os espaços e as hifenizações de fim de linha e retirei os números de referência. Onde juntei texto de duas colunas, isso está indicado.
- "Pág." é a página impressa do PDF lido. Para textos obtidos como JATS do PubMed Central (sem paginação), indico a seção e o parágrafo.
- Todos os arquivos baixados ficam em `/home/jovyan/compartilhado/ralph/openset-microscopy/referencias/c/<chave>/`, um diretório por arquivo, com um `provenance.json` (URL, data, licença). Ficam fora do git.

---

## 1. Buscas no PubMed

**Serviço:** NCBI E-utilities (`esearch` + `efetch`, `db=pubmed`), sem chave de API, `tool=litsearch`, sem e-mail, no máximo 3 requisições por segundo. **Data:** 2026-11-14 (16:26 UTC).

**Filtro de ano:** a nota de `02-related.tex` não fala em filtro de ano. Por isso rodei cada string duas vezes: sem filtro e com `AND ("2020"[dp] : "3000"[dp])`. Os registros salvos são os da busca sem filtro, e o recorte a partir de 2020 sai do campo de data.

**Strings:** são as versões PubMed de `02-related.tex`, copiadas sem alteração. A nota tem também uma S8 (*simulation realism*). Rodei a S8 junto com as outras e a registro à parte, porque a tarefa pedia S1 a S7. A tradução do PubMed (`QueryTranslation`) está em `pubmed/runs.json`.

| String | Tema | Registros (todos os anos) | Registros ≥ 2020 | Observação |
|---|---|---:|---:|---|
| S1 | raw-hologram recognition | 2 | 0 | Os dois são de 2013 e 2018 |
| S2 | deep learning on holograms | 70 | 61 | |
| S3 | open set in holography | 8 | 8 | Quase tudo fora do tema (HoloLens, córtex...) |
| S4 | open set in microscopy | 13 | 12 | Quase tudo fora do tema |
| S5 | learned Fourier layers | 2 | 1 | O PubMed avisa `QuotedPhraseNotFound` para `"learnable Fourier"` e `"Fourier layer"`. As duas frases não existem no índice e foram ignoradas |
| S6 | learned reconstruction and autofocus | 41 | 37 | |
| S7 | cost and full field of view | 77 | 49 | |
| *S8* | *simulation realism (extra)* | *8* | *4* | |
| **Total** | | **221 registros** | | |
| **Após deduplicação (PMID, DOI, título normalizado)** | | **207 trabalhos** | **160** | |

Contagem por string depois da deduplicação, em `merged/counts.json`: S1 2/0, S2 70/61, S3 8/8, S4 13/12, S5 2/1, S6 40/36, S7 76/48, S8 8/4.

**Arquivos:**

- `referencias/c/pubmed/S<n>/` contém `esearch_all.xml`, `esearch_2020.xml`, `records.xml` (PubMed XML bruto), `records.medline`, `records.ris`, `ids_all.txt` e `ids_2020.txt`.
- `referencias/c/pubmed/runs.json` guarda as strings como rodadas, a data e as contagens.
- `referencias/c/merged/` contém `merged.csv`, `merged.ris`, `counts.json` e `screening.csv`.

**Verificação pedida pela nota ("as buscas recuperam Rockembach, Bravo-Frank, Liu e Sedaghat?"):** no PubMed, nenhum dos quatro é recuperado.

- Rockembach (CBMS/IEEE) e Bravo-Frank (*npj Biosensing* 2024) não estão indexados no PubMed. A consulta por DOI retorna 0.
- Liu (PMID 34612985) está indexado, mas o resumo diz *clustering*, e não *classif\*/recogni\*/detect\**. A S1 não o pega.
- Sedaghat (PMID 40919199) diz *novelty detector*/*novelty assessment*, e não *"novelty detection"*. A S3 não o pega.
- Também escapam: Sanborn et al. 2023 (PMID 36710508), que escreve *digital inline holography* sem hífen e *machine learning*, e Matthews et al. 2024 (PMID 38669245), que faz *tracking*.

Sugestão para a versão final das strings, sem rodar nada antes da aprovação:

- S1: acrescentar `cluster*`, `identif*`, `unreconstructed`, `"raw diffraction"` e `"directly from"`.
- S2: acrescentar `"inline hologra*"` (sem hífen) e `"machine learning"`.
- S3: trocar `"novelty detection"` por `novelty`.
- S5: a busca não funciona no PubMed (ver acima).

**Mesclagem e deduplicação.** Script: `holo-openset/scripts/exp_resolucao/refs_merge.py`, só biblioteca padrão. Como rodar:

```bash
python3 -I scripts/exp_resolucao/refs_merge.py /home/jovyan/compartilhado/ralph/openset-microscopy/referencias/c
```

- O script lê todo `*.ris` em `pubmed/`, `scopus/` e `sciencedirect/`. A string sai do primeiro `S<n>` no caminho do arquivo, por exemplo `scopus/S3.ris` ou `sciencedirect/S3.ris`.
- Agrupa por DOI, PMID ou título normalizado, de forma transitiva.
- Escreve `merged.csv`, `merged.ris` e `counts.json`.
- Carrega as decisões de triagem de `merged/screening.csv` quando a chave coincide.
- Exporte cada string do Scopus e da ScienceDirect uma vez só, **sem** o filtro de ano. O script conta o recorte ≥ 2020 sozinho.
- Testei com um RIS falso do Scopus (CRLF, DOI em URL e maiúsculas). O registro duplicado foi fundido.

---

## 1b. Complemento em índices abertos (2026-11-15)

> **Scopus e ScienceDirect NÃO foram rodados.** Não temos credencial nem chave da Elsevier, e os `.RIS` pedidos ao
> orientador não chegaram: em 2026-11-15 as pastas `referencias/c/scopus/` e `referencias/c/sciencedirect/` estão
> vazias. O que segue é um **complemento declarado**, não um substituto: as mesmas strings em dois índices abertos
> que não pedem chave nem identificação. Quando os `.RIS` chegarem, basta colocá-los nessas pastas (`S<n>` no nome,
> sem filtro de ano) e rodar `refs_merge.py` de novo; as decisões de triagem já tomadas são mantidas.

**Serviços e data (2026-11-15, ≈ 08:20–08:30 UTC):**

- **OpenAlex**, `GET /works?filter=title_and_abstract.search:<string>`, paginação por cursor, 200 por página.
  Usei a **forma ScienceDirect** de cada string (palavras sem curinga). O OpenAlex aplica radicalização (stemming)
  por conta própria e aceita AND/OR e frases entre aspas; a tradução que ele fez de cada consulta está na resposta
  (`meta.x_query`), salva nas páginas.
- **Semantic Scholar**, `GET /graph/v1/paper/search/bulk` (título e resumo). Usei a **forma Scopus** de cada string,
  com AND como `+` e OR como `|`, e mantive os curingas de palavra única (`hologra*`, `classif*`...). Este índice não
  expande curinga dentro de frase (testei: `"digital holograph*"` devolve o mesmo que `"digital holographic"`), então
  troquei cada frase com curinga pelas suas formas explícitas (`"raw hologram" | "raw holograms"`, `"digital
  holography" | "digital holographic"`, `"neural network" | "neural networks"`, `"unknown class" | "unknown
  classes"`, `"Fourier layer" | "Fourier layers"`, `"in-line holography" | "in-line holographic" | "in-line
  hologram" | "in-line holograms"`). As strings exatas estão no script.
- **Crossref** não tem busca booleana; não rodei as strings nele. Usei-o só para conferir os metadados (DOI, ano,
  volume, páginas) das entradas novas do `main.bib` (`referencias/c/crossref_meta_2026-11-15/`).
- **Nada identificador foi enviado:** User-Agent genérico (`Mozilla/5.0 (X11; Linux x86_64)`), sem e-mail, sem
  `mailto`, sem chave. A resposta do OpenAlex sugere que um agente peça uma chave enviando o e-mail do usuário; não fiz
  isso (a cota anônima bastou: 16 requisições).
- Uma requisição por vez, com 3 s de pausa; um 504 do OpenAlex na S3 foi repetido (a pasta vazia foi apagada antes).

**Script:** `holo-openset/scripts/exp_resolucao/refs_open_search.py` (só biblioteca padrão), rodado de fora das pastas
de download com `python3 -I`:

```bash
python3 -I scripts/exp_resolucao/refs_open_search.py fetch openalex S1 ../referencias/c/openalex/S1
python3 -I scripts/exp_resolucao/refs_open_search.py to-ris openalex ../referencias/c/openalex/S1
# idem com s2 -> ../referencias/c/semanticscholar/S<n>; depois:
python3 -I scripts/exp_resolucao/refs_merge.py ../referencias/c
```

**Arquivos:** `referencias/c/openalex/S<n>/` e `referencias/c/semanticscholar/S<n>/`, cada um com `page_*.json`
(resposta bruta), `query.json` (string, URLs, data, total informado), `records.ris` e `records.csv` (com resumo, para
a triagem). `refs_merge.py` passou a ler as duas pastas novas.

| String | OpenAlex (todos / ≥ 2020) | Semantic Scholar (todos / ≥ 2020) | PubMed (todos / ≥ 2020) | Trabalhos após deduplicação nas três fontes (todos / ≥ 2020) |
|---|---:|---:|---:|---:|
| S1 | 27 / 22 | 28 / 19 | 2 / 0 | 35 / 25 |
| S2 | 142 / 122 | 223 / 178 | 70 / 61 | 259 / 212 |
| S3 | 26 / 22 | 54 / 43 | 8 / 8 | 62 / 50 |
| S4 | 37 / 33 | 61 / 39 | 13 / 12 | 79 / 54 |
| S5 | 20 / 18 | 18 / 15 | 2 / 1 | 23 / 21 |
| S6 | 97 / 84 | 183 / 153 | 41 / 37 | 204 / 172 |
| S7 | 194 / 122 | 236 / 128 | 77 / 49 | 291 / 168 |
| *S8 (extra)* | *4 / 4* | *21 / 10* | *8 / 4* | *22 / 11* |
| **Registros** | **547** | **824** | **221** | **1592 registros → 918 trabalhos (668 a partir de 2020)** |

Nenhuma consulta foi truncada (o total informado bateu com o salvo em todas). Pela fonte (`merged/merged.csv`): 711
trabalhos novos em relação ao PubMed; 301 só no Semantic Scholar, 132 só no OpenAlex, 278 nos dois.

**Verificação de recuperação (a mesma da nota de `02-related.tex`):**

- Rockembach 2024 (CBMS/IEEE): **recuperado** (OpenAlex e Semantic Scholar, S1 e S2). O PubMed não o recuperava.
- Delli Priscoli 2021 (IEEE JSTQE), Cotter 2021 e Guo 2021 (L&O Methods): recuperados.
- Bravo-Frank 2024, Liu 2021 e Sedaghat 2025: **continuam fora**, pelos mesmos motivos de vocabulário já descritos na
  seção 1 (as strings, não os índices). A sugestão de ajuste das strings continua valendo e não foi aplicada.

**Triagem (2026-11-15).** Li os 711 títulos novos. Para os 60 sinalizados li o resumo (de `records.csv`). Incluí 37
(decisão, motivo e acesso em `merged/screening.csv`); os outros 674 ficaram "não-incluído" (fora do escopo de C.1:
holografia de exibição, segurança, IoT, metrologia, física de altas energias, microscopia não holográfica...). Total
na triagem conjunta: 56 incluídos em 918.

**Textos completos baixados (cada um numa pasta nova, `provenance.json` com URL e data):**

| Pasta | Trabalho | Resultado |
|---|---|---|
| `hifcrepr2026/` | Pirone et al. 2026, J. Phys. Photonics 8:025040 | PDF (IOP, CC BY), lido inteiro |
| `microplastic2021/` | Zhu et al. 2021, J. Phys. Photonics 3:024013 | PDF (IOP, CC BY), lido por busca de termos e nas passagens citadas |
| `planktonraw2022_archimer/`, `planktonraw2022_pdf/` | Scherrer et al. 2022, LNCS 13483:25–39 | página e PDF da versão do autor (Archimer, Ifremer), lido inteiro |
| `seo2010_pmc/` | Seo et al. 2010, Anal. Chem. 82:4621–4627 (ref. [37] de Isikman 2012) | JATS do PMC (manuscrito NIH), lido nas seções de resultados e métodos |
| `holoattunet2026/` | Song et al. 2026 (HoloAtt-UNet), Measurement 289:122543 | **bloqueado** (Optica Open: desafio anti-bot); não contornei |
| `planktonraw2021_hal/` | Scherrer et al. 2021 (versão HAL) | **bloqueado** (desafio anti-bot) |
| `rbcfcn2021/` | JBO 26:036001 (2021) | **bloqueado** (SPIE: desafio anti-bot) |
| `cotter2021_mit_c/`, `cotter2021_mit_pdf/` | Cotter et al. 2021 | página do DSpace obtida; o PDF deu **HTTP 429** de novo (terceira tentativa no total); não insisti |
| `dellipriscoli2021_d/`, `lenslessdet2024_ieeepj/` | Delli Priscoli 2021; IEEE Photonics J. 2024 | **HTTP 502** do IEEE |

**O que o complemento cobre e o que não cobre:**

- *Cobre:* títulos e resumos indexados no OpenAlex e no Semantic Scholar, que incluem IEEE, Optica (OE, BOE, AO, JOSA,
  anais DH/COSI), SPIE, Elsevier, Wiley, IOP, MDPI, Springer, além de arXiv/bioRxiv/SSRN e repositórios. Foi o que
  trouxe o CBMS, o JSTQE e os anais de conferência que o PubMed não indexa.
- *Não cobre:* (i) as palavras-chave de autor e o vocabulário controlado que o `TITLE-ABS-KEY` do Scopus e o campo
  "Title, abstract or author-specified keywords" da ScienceDirect consultam; (ii) resumos que esses índices não têm
  (muitos registros da Elsevier vêm sem resumo no OpenAlex e no Semantic Scholar: por exemplo Opt. Commun. 2026
  133421 e 133563 e Opt. Laser Technol. 2025 113813, triados só pelo título); (iii) a sintaxe exata do Scopus (o
  OpenAlex radicaliza sozinho, o Semantic Scholar não expande curinga em frase); (iv) a cobertura completa da
  ScienceDirect, que indexa o texto dos periódicos da Elsevier. **As contagens acima não são as do Scopus nem as da
  ScienceDirect e não devem ser descritas como tais.**

---

## 2. Os três trabalhos de partida

A numeração foi conferida no PDF compilado (`latex_final/main.pdf`, estilo `unsrt`): [11] = `rockembach`, [13] = `bravofrank2024`, [14] = `Liu:21`.

### [11] Rockembach, Souza, von Wangenheim, Sobieranski, CBMS 2024, pp. 364–369, doi:10.1109/CBMS61543.2024.00067

> *Atualizado em 2026-11-14 com o texto completo.* A primeira versão desta entrada foi escrita só com a p. 364 e dizia que a medição "não é verificável (pp. 365–369 inacessíveis)" e que o artigo não usa "iterative". As duas coisas mudaram: o texto completo foi lido (pp. 364–369) e a palavra "iterative" aparece na p. 365. O trabalho é dos próprios autores e é descrito aqui de forma neutra: ele afirma o custo sem medi-lo, e o nosso artigo o complementa com a medição.

- **Acesso:** primeira versão: o Semantic Scholar aponta uma cópia verde no Repositório Institucional da UFSC (TCC de M. Rockembach, handle 123456789/262148, "Open Access"). O arquivo (`rockembach2024/TCC_FolhaDeRosto_ManoellaRockembach.pdf`) tem só cinco páginas: capa, folha de rosto, ficha, folha de aprovação e a primeira página do artigo (p. 364). **Agora:** o PDF completo (6 pp., 364–369) está em `rockembach2024_full/rockembach2024_cbms.pdf`, baixado do IEEE Xplore pela licença institucional da UFSC (o rodapé de cada página diz "Authorized licensed use limited to: UNIVERSIDADE FEDERAL DE SANTA CATARINA"). O diretório não tem `provenance.json`. O texto de cada página foi extraído com `gs` (`rockembach2024_cbms_p1.txt` … `p6.txt`; página do PDF 1 = p. 364). A Tabela I e as Figs. 4–5 foram conferidas na imagem da página.
- **Frases sobre o custo da reconstrução (todas as que há no artigo):**
  - p. 364 (resumo): "Those patterns, called holograms, carry volumetric information regarding the inspected sample, requiring complex numerical methods to make them distinguishable as occurs in a conventional bright-field microscopic image."
  - p. 364 (resumo): "However, for many applications, the real-time analysis of holograms is computationally expensive due to the nature of numerical diffraction methods to reconstruct the signals into visual information."
  - p. 364 (resumo): "To mitigate this problem, in this paper we investigate the use of deep learning approaches to classify those interference patterns, directly from the raw holograms, without the requirement of phase-recovering methods for diffraction."
  - p. 364 (resumo): "The obtained results demonstrated the feasibility of the proposed approach to properly classify samples with 96.8% of precision, directly from the holographic interference patterns, avoiding the need for computationally expensive diffraction methods."
  - p. 365 (Introdução, coluna esquerda): "The iterative and complex procedure for reconstruction usually makes real-time applications unfeasible, and in many cases the analysis of DIHM setups is restricted to asynchronous trials."
  - p. 365 (Introdução, coluna direita): "The obtained results demonstrated the feasibility of the CNN's to properly classify interference patterns, avoiding the requirement of the time-expensive numerical diffracting methods."
  - p. 368 (IV-C): "The models showed strong capabilities to correctly detect the holograms, demonstrating that YOLO is suitable for the task of classification with no reconstruction by numerical diffraction."
  - p. 369 (Final Remarks): "This work demonstrated the promising possibilities of neural network assisted DIHM as a resourceful tool for hologram classification that does not require any additional preprocessing (hologram reconstruction) used in traditional workflows. This process significantly reduces processing time and computational resources, and combined with the simple and highly compact hardware, can be further enhanced as a low cost portable microscopy tool for real-life settings."
  - p. 369 (Final Remarks), os próprios autores deixam o tempo real para depois: "To evaluate the possibility of real-time, high-accuracy, affordable microscopy device for large scale usage, the workflow described in this study needs to be assessed on a non simulated context."
- **"Iterative":** aparece uma vez, na p. 365 ("The iterative and complex procedure for reconstruction..."). O método de difração que o próprio artigo descreve (Seção III-A, p. 366, Eq. 3) é uma convolução de Fresnel feita com um par de transformadas de Fourier, sem iteração, e é o mesmo usado para gerar os dados.
- **Mediu?** **Não mediu a reconstrução nem a inferência.** O único tempo do artigo é o de treino (p. 368): "In terms of training time, the analysed models were trained on Google Colab platform, with a T4 GPU using the same dataset described by section IV-A. YOLOv8 was the fastest model to train, taking 46min 21s to train with the best result observed at epoch 118, followed by YOLOv5 with 1h 7min 43s of training time and best results observed at epoch 298. Finally, YOLOv9 took 2h 3min 49s with the best result observed at epoch 110." A frase da p. 369 ("significantly reduces processing time and computational resources") não traz número e não tem medição que a sustente. Isso confirma o que o protocolo (C, parágrafo de abertura) dizia.
- **Dados (Seção IV-A, pp. 367–368):**
  - Geração: "The dataset used in our work was generated using the Fresnel convolutional method previously described in the Section III-A, implemented in Matlab."
  - Objetos e parâmetros: "For this purpose, we used as objects to be imaged 26 capitalized letters having the same font properties, with spatial resolution of 640x640 pixels, randomly translated in the image, with rigid rotations. The diffraction parameters used were λ = 385nm, z = 50k, pixel size of 1.67μm, and an output image resolution with the same resolution of its input (640x640 pixels). After processing, a total of 200 holograms were generated, as demonstrated in the Figure 4." O z não tem unidade no texto; a leitura z = 5·10⁴ λ = 19,25 mm é nossa (`03b-bench.tex`). Cada imagem tem várias letras (Fig. 4, p. 368).
  - Aumento e divisão (p. 368): "The techniques for data augmentation used were: Horizontal and Vertical flip, cropping zoom in a rage of 0% to 30% and rotation between -15° and +15°. The final dataset was finally composed by 520 images, with a 92% to 8% split between training and validation sets, respectively." A anotação e o aumento foram feitos no Roboflow (nota 3). O texto não diz se o aumento foi aplicado antes ou depois da divisão. Não há conjunto de teste separado: os resultados são do conjunto de validação (legenda da Tabela I), o mesmo em que a melhor época foi escolhida.
- **Tarefa, modelos e resultados:** é **detecção** com classificação em 26 classes, conjunto **fechado**. p. 367: "Our approach uses YOLOv5, YOLOv8 (both from Ultralytics), and the new YOLOv9 to detect objects in raw computer-generated holograms." Métricas descritas: precision, recall, mAP50 e mAP50-95 (p. 367). A Tabela I (p. 368) só traz mAP50 por classe, com 277 instâncias na validação: "all" 0,983 (YOLOv5), 0,986 (YOLOv8), 0,981 (YOLOv9). Os 96,8 % de *precision* do YOLOv8 aparecem só no resumo (p. 364) e na Introdução (p. 365: "the YOLOv8 model presented 96.8 percent of precision"); nenhuma tabela ou frase da Seção IV traz esse número.
- **Limitação de conjunto fechado, nas palavras dos autores (p. 369):** "CNN models can only confidently classify the specific objects it is trained for, and its performance may be compromised when used on data outside the scope of its training." e "...it's necessary to retrain it on new labeled data when there are changes in the target subject or the image acquisition settings, the z-distance for instance."
- **Detector:** o próprio YOLO localiza e classifica as letras na imagem de 640 × 640 (caixas na Fig. 5, p. 369). Não há estágio separado de recorte.
- **Baseline e hardware:** não há rota com reconstrução, nem para tempo nem para acerto. Hardware: só o do treino (Colab, T4).

### [13] Bravo-Frank, Zende, Feng, Mesyngier, Pachpute, Hong, *npj Biosensing* 1:8 (2024), doi:10.1038/s44328-024-00008-9

- **Acesso:** PDF da editora, CC BY 4.0. A cópia que estava em `OLD-WRONG-projeto-e-testes/.research/papers/` foi copiada para `bravofrank2024/`. O rodapé diz "corrected publication 2025". Li o texto inteiro (8 pp.).
- **O trabalho não faz a afirmação sobre a reconstrução.** A palavra *reconstruct* aparece só na legenda da Fig. 2 (p. 3: "...accompanied by the corresponding reconstructed images at 10 and 20 µm away from the in-focused plane..."). Em nenhum lugar a reconstrução é dita lenta, cara ou iterativa, e nenhuma rota com reconstrução é comparada. O "real-time" do título vem da cascata de detectores:
  - p. 6: "This two-step approach of employing YOLOv8n followed by YOLOv8 not only minimizes computational resources but also reduces total processing time, enabling real-time performance for efficient and effective particle detection."
  - p. 6: "Using our current hardware, our processing framework can analyze holograms in real-time for particle concentrations up to 350 particles/µL, about one particle every three frames."
  - p. 2: "In response, our study proposes a DL approach specifically designed to augment DIH's capabilities, enabling real-time, precise detection of individual bacteria."
- **Mediu?** Não há tempos. O hardware de processamento não é informado ("our current hardware"). A câmera grava a 100 quadros/s (p. 5).
- **Detector:** todo o pipeline é detector + classificador (YOLOv8n → YOLOv8 → HRNet). Não há o que comparar.
- **Ponto que afeta o Related Work, não o parágrafo C:** o sistema tem uma classe "unknown" por limiar de confiança (p. 3: "...an additional class 'unknown', is used to classify particles with confidences below the FPR threshold of our known classes.") e afirma ter isolado uma partícula não vista (p. 5: "This adaptability was evident in our experiments where our system successfully identified and isolated an unfamiliar particle (conglomerate) during spiked tests."). A frase de `02-related.tex` "both are closed-set" precisa dessa ressalva: há rejeição por limiar, sem galeria nem enrollment.
- **Trabalho seguinte do mesmo grupo, que faz a afirmação:** ver Bravo-Frank et al. 2025 (diálise peritoneal) na tabela.

### [14] Liu, Thevar, Takahashi, Burns, Yamada, Sangekar, Lindsay, Watson, Thornton, *JOSA A* 38(10):1570–1580 (2021), doi:10.1364/JOSAA.424271

- **Acesso:** *Accepted Author Manuscript*, aberto pela licença de AM da Optica depois do embargo de 12 meses (Crossref: `OA_License_v1#AM`). A cópia que estava em `OLD-WRONG.../papers/` foi copiada para `liu2021/`. As páginas abaixo são as do manuscrito, numeradas 1–13 no cabeçalho; a página do PDF é essa mais 1, por causa da folha de capa. A paginação da versão publicada (1570–1580) não foi conferida. Li o texto inteiro.
- **Frases:**
  - p. 1 (resumo): "However, the process of reconstructing holograms is computationally intensive and cannot easily keep up with the rate of data acquisition on low-power sensor platforms."
  - p. 1 (resumo): "Directly clustering raw holograms takes less than 0.1 second per image using a low-power CPU board. This represents a three-order of magnitude reduction in processing time compared to clustering of reconstructed holograms, and makes it possible to interpret targets in real time on low-power sensor platforms."
  - pp. 1–2 (Introdução): "However, hologram reconstruction is a computationally intensive process. It becomes more expensive when the distance to the target is not known prior to reconstruction, since hologram reconstruction needs to go through the whole recording volume to detect the focal plane."
  - p. 2: "Although efforts have been made to speed up this process using field-programmable gate arrays (FPGAs) and parallel processing using graphics cards, these methods significantly increase the cost, power consumption and complexity of embedded sensing platforms."
  - p. 7: "This has significant implications for in situ applications as it avoids the large computational overhead needed to reconstruct holograms."
  - p. 7: "The biggest cost is in the reconstruction of the holograms, which takes more than 13 times the combined training time."
  - p. 7: "However, reconstructing each hologram on the same lower-power CPU board takes ~14 s per image, which forms significant bottleneck for real-time clustering of reconstructed holograms."
  - p. 9 (Conclusões): "A three-order gain in computational efficiency can be achieved by directly interpreting raw holograms compared to reconstructed holograms using the same processing hardware."
- **Mediu? Sim, no mesmo hardware.** Tabela 5 (p. 8), teste numa placa Intel Atom:
  - reconstrução para teste: 226 240 s;
  - clustering para teste: 1472 s (bruto) e 1477 s (reconstruído);
  - para 16 000 imagens, isso dá cerca de 14,1 s por imagem para a reconstrução e cerca de 0,09 s para o clustering.
- **Baseline:**
  - p. 4: espectro angular com autofocus pelo método de [38], "to automatically detect the focused reconstruction across the entire recording distance range", acelerado com `mpi4py-fft` e `multiprocessing`.
  - Nota da Tabela 5: "image size: 227 × 227; reconstruction distance range: 10 – 60 mm with step 0.1 mm; no manual operation included."
  - Ou seja, o baseline é uma **varredura cega de 501 distâncias por recorte**, e não uma retropropagação única.
- **Hardware (p. 4):** "The low-power CPU board used to run the proposed models had an Intel Atom processor E3940 @ 3.60 GHz × 4 with 8 GB RAM". O treino foi feito num i9-9900K com RTX 2080.
- **Detector:** não entra. p. 3: "Each hologram is cropped to 300 × 300 pixels around the target". Os recortes são dados prontos, e nem a rota bruta nem a reconstruída cronometram a localização.
- **O que realmente comparou:** clustering de um recorte bruto contra autofocus cego de 501 distâncias mais clustering do recorte, na mesma CPU de baixo consumo, sem detector.
- **Conta minha, não do artigo:** 14 s ÷ 501 ≈ 28 ms por distância (propagação + métrica de foco) por recorte de 227 × 227 no Atom. Com a distância conhecida ou buscada numa faixa estreita, uma retropropagação custaria da ordem do próprio clustering (cerca de 90 ms), e não 150 vezes mais. É uma estimativa e não deve ir para o texto como número de Liu.

---

## 3. Tabela C.1

"Afirma" quer dizer que achei no texto a frase em que a reconstrução é dita lenta, cara ou iterativa, ou em que pulá-la dá velocidade ou tempo real. "Mediu" quer dizer que o trabalho cronometrou a reconstrução contra o próprio método. Os anos anteriores a 2020 estão marcados com †.

### 3a. Texto completo lido

| Trabalho (DOI) | Frase exata | Pág. | Afirma? | Mediu? | Baseline | Hardware | O que realmente comparou |
|---|---|---|---|---|---|---|---|
| Rockembach et al. 2024 [11] (10.1109/CBMS61543.2024.00067) | "However, for many applications, the real-time analysis of holograms is computationally expensive due to the nature of numerical diffraction methods to reconstruct the signals into visual information." | 364 (também p. 365: "The iterative and complex procedure for reconstruction usually makes real-time applications unfeasible..."; p. 369: "This process significantly reduces processing time and computational resources...") | Sim (iterativa, p. 365) | Não. Só tempo de treino (T4/Colab: 46 min a 2 h 4 min); nenhum tempo de inferência ou de reconstrução | Nenhum | Google Colab, T4 (só treino) | Nada contra a reconstrução. YOLOv5/v8/v9 em hologramas sintéticos de letras (26 classes, validação). *Atualizado em 2026-11-14 com o texto completo; antes: "Não verificável (pp. 365–369 inacessíveis)"* |
| Bravo-Frank et al. 2024 [13] (10.1038/s44328-024-00008-9) | Nenhuma sobre reconstrução. O tempo real vem da cascata: "This two-step approach of employing YOLOv8n followed by YOLOv8 not only minimizes computational resources but also reduces total processing time, enabling real-time performance..." | 6 | **Não** | Não (sem números de tempo) | Nenhum | Não informado | Nada. Não há rota com reconstrução |
| Liu et al. 2021 [14] (10.1364/JOSAA.424271) | "However, reconstructing each hologram on the same lower-power CPU board takes ~14 s per image, which forms significant bottleneck for real-time clustering of reconstructed holograms." | 7 (AM) | Sim | **Sim**, mesmo hardware | Espectro angular + autofocus cego de 10–60 mm em passos de 0,1 mm (501 distâncias) por recorte de 227 × 227 | Intel Atom E3940, 4 núcleos | Clustering do recorte bruto (0,09 s) contra varredura de 501 distâncias + clustering (14 s). Sem detector |
| Kim et al. 2018† (10.1038/s41598-018-35274-x) | "This iterative algorithm is computationally intensive, either incurring long processing time or requiring high-end resources (e.g., a high-performance graphical processing unit server) for faster results." (também p. 1: "However, extensive computation is required to reconstruct object images...") | 2 | Sim (iterativa) | Não. Só o próprio pipeline: "it took 7.7 seconds to process the whole FOV image (3000 × 3500 pixels, the number of cell candidates: 100)" (p. 8) | Recuperação de fase iterativa, citada e não cronometrada | GTX 1080 Ti citada para o treino; hardware dos 7,7 s não informado | Nada contra a reconstrução. Os 7,7 s incluem o detector de candidatos (gradiente) |
| Song et al. 2025, HoloNet (10.1063/5.0246495) | "However, the complexity of diffraction images (holograms) produced by LDIH presents challenges for human interpretation and requires time-consuming computational reconstruction, often leading to artifacts and information loss." | Resumo (JATS/PMC). Também Introdução §3: "This process requires substantial computational resources..." | Sim | Não (só tempo de treino entre redes) | Recuperação de fase iterativa (Rayleigh–Sommerfeld + otimização), usada só para gerar rótulos | n/i | Nada contra a reconstrução. Achado útil: classificar no bruto deu mais acerto que no reconstruído (Results §[14]) |
| Xu et al. 2025, plâncton (10.3390/s25072325) | "However, the recording and reconstruction of digital holography require a strictly controlled laboratory environment and time-consuming iterative computation, respectively, which impede its application in marine plankton imaging." | 1 | Sim (iterativa) | Só o próprio pipeline: "The average reconstruction time for each image is 0.0130 s, the recognition time is 0.0147 s, and the total processing time is only 0.0277 s." | Não cronometrou a reconstrução iterativa nem o PSDH | Core i7-12700H + RTX 3060 | Reconstrução aprendida (A-Unet) contra YOLOv5. **O detector custa mais que a reconstrução** (14,7 contra 13,0 ms) |
| Moon et al. 2025, cardiomiócitos (10.1364/BOE.542362) | "For one hologram, the reconstruction process itself in the existing methods takes at least three times longer than the process of tracking the contraction-relaxation motion-speed profile using optical flow in the proposed method." | Resumo (JATS/PMC; BOE 16:398–414) | Sim | Só o próprio método (0,234 s/quadro, Discussão §[45]). A reconstrução vem de números de outros artigos (0,667 s, 1,93 s, 0,707 s) | Tempos publicados por outros (inclui autofocus e unwrapping) | Não informado | Outro hardware e outro pipeline. Não é reconhecimento (é dinâmica) |
| Aharoni et al. 2025, citometria off-axis (10.1117/1.JBO.30.1.016007) | "...followed by a phase unwrapping algorithm to solve 2π ambiguities, which is a time-consuming process that can be performed in tens of frames per second, rather than thousands of frames per second as required in imaging flow cytometry." | Introdução §[7] (JATS/PMC) | Sim | Só a própria inferência (Tabela 1: 0,00585 s para 1 projeção, 0,0591 s para 10) | Recuperação de fase off-axis + unwrapping, citada | Tesla T4 (Colab) | Nada contra a reconstrução. Holografia off-axis |
| Sanborn et al. 2023 (10.1002/bit.28338; lido no arXiv 2301.09638) | "However, conventional DIH has several issues related to data processing, such as high computational cost and low signal-to-noise ratio due to noises from cross interference between particle signals, which limits its widespread adoption as an in situ tool." | 3 (arXiv) | Sim | Só o próprio pipeline: "processing over 40 frames per second (a single image in 0.025 seconds)" (p. 11) | O de Guo et al. 2021, citado: "involves intensive image preprocessing even without reconstruction which takes 1.6 – 2.5 seconds" (p. 10) | V100 + TensorRT (p. 4) | YOLO no bruto contra o pré-processamento de outro artigo, sem reconstrução. Diz que o custo restante é a detecção/segmentação (p. 3) |
| Bravo-Frank et al. 2025, diálise peritoneal (10.1016/j.ijpharm.2025.125373; lido no arXiv 2411.00901) | "...is hindered by the traditional numerical approaches used for hologram processing and inference, being both computationally, and resource intensive." | 3 (arXiv) | Sim | Não (sem tempos) | — | Não informado | **O próprio pipeline "real-time" reconstrói dois planos**: "these enhanced images are reconstructed into additional focal planes at z = 6 µm and 12 µm ... using a Fresnel diffraction kernel" (pp. 5–6), antes do YOLOv8n |
| Molani et al. 2026 (10.1038/s41598-026-61176-4) | "Common reconstruction techniques, such as numerical back-propagation and iterative methods often suffer from noise and are computationally intensive, especially with submicron particles or densely populated samples." e "These approaches simplify the processing pipeline, reduce computational load and enable real-time or near-real-time analysis." | 2 | Sim, **incluindo a retropropagação** | Não (não há tempos no artigo) | — | — | Nada. Afirmação de revisão |
| Terbe et al. 2022 (10.3390/s22218366) | "Although there are phase recovery algorithms, these are iterative, computationally expensive procedures." | 1 | Só sobre a recuperação de fase | Mediu só 2D contra 3D-CNN (treino: 10 min contra 1 h 30 min; V100) | — | V100 | Não pula a reconstrução: classifica a reconstrução e um volume refocado |
| Matthews et al. 2024 (10.1371/journal.pone.0301182) | "Digital holographic microscopy (DHM) is a well-established, but computationally intensive method for obtaining three-dimensional cell tracks from video microscopy data." | 1 | Sim | **Sim**, mesmo CPU (Tabela 2, p. 11): YOLOv5n 149 ms/quadro contra "Standard DHM on Desktop CPU" 1658 ms/quadro | Pilha de retropropagação Rayleigh–Sommerfeld + Gouy phase para localizar em 3D (p. 5) | Xeon de 4 núcleos (também RTX 3060: 10,5 ms; Jetson Nano: 74,6 ms) | Detector no bruto contra pilha completa de refoco para rastreamento 3D. É rastreamento, não reconhecimento |
| Liu et al. 2025, OAH-Net (10.1364/BOE.547292) | "Consequently, the speed of hologram reconstruction has become the primary bottleneck, limiting DHM's clinical feasibility for applications requiring rapid turnaround times." | Introdução §[4] (JATS/PMC) | Sim | **Sim**: "The inference speed is under 3 ms/frame ... (1536 × 2048 pixels)". Discussão: "reduces the holographic reconstruction time by up to 97% (excluding downstream data analysis)" | Pacote comercial (Ovizio) | RTX 4090, lote 1, JIT | Reconstrução aprendida contra a comercial. O YOLOv8 (3,5 ms, número citado) custa o mesmo que a reconstrução. Holografia off-axis |
| Rivenson et al. 2018† (10.1038/lsa.2017.141) | "...requiring fewer measurements in addition to being computationally faster." | 1 | Sim | **Sim** (Tabela p. 5): rede 6,45 s contra multialtura iterativa 23,20–47,43 s (N = 2–8) por cerca de 1 mm² | Recuperação de fase iterativa multialtura | GPU de laptop | Imagem limpa contra imagem limpa. Dos 6,45 s, "3.34 s for the preprocessing stages ... pixel super-resolution, auto-focusing and free space back-propagation" |
| Chen et al. 2022, FIN (10.1038/s41377-022-00949-8) | "For the case of M=3, FIN is ~9.3-fold faster than RH-M and ~27.3-fold faster than MH-PR, which highlights the computational efficiency of our network." | 5 | Sim | **Sim** (Tabela 1); "~1 mm² sample area within 0.04 sec" (p. 7) | Multialtura iterativa (MH-PR) e outra rede | RTX 2080 Ti | Imagem limpa contra imagem limpa |
| Seo et al. 2009† (10.1039/b813943a; lido no JATS do PMC, manuscrito NIH, sem páginas) | "In our approach, there is no such digital reconstruction, and the detected holographic lensfree image is simply analyzed by a pattern recognition algorithm to classify different cell types on the chip. [...] Therefore, numerically and computationally our approach is much simpler and faster since high spatial resolution is not of interest for this work." Também em "Theory behind Holographic-LUCAS": "This step involves straightforward pattern recognition algorithms, and therefore is numerically much simpler and faster than the solution of the inverse wave problem." | Seção "Discussions" (e apêndice "Theory") | Sim | **Não** mediu tempo de processamento (o único tempo é o da captura, "within less than 0.3 seconds", Introdução) | A reconstrução de alta resolução do DIHM com magnificação de franja de 20–30×, descrita, não cronometrada | — | *Acrescentado em 2026-11-15.* É o precedente mais antigo do argumento e também da queda por densidade (seção 4, "Densidade") |
| Seo et al. 2010† (10.1021/ac1007915; JATS do PMC, manuscrito NIH) | Sem a afirmação. Sobre o custo da reconstrução: "Because FFT is used, the presented recoveries are also quite fast, in terms of digital computation time, with a convergence time of less than a few seconds, using, for example, a 1.6 GHz CPU with a Pentium processor. We also achieved a >40× improvement in our computation time using a graphics processing unit (GPU) (CUDA-enabled NVIDIA GeForce GTX 285), which achieved an image reconstruction time of <1 s, up to an image size of ~20 megapixels." | "Experimental Methods", subseção "Digital Reconstruction and Phase Recovery from Holographic Images" | Não (reconstrói) | Mediu a própria reconstrução | — | CPU de 1,6 GHz; GTX 285 | *Acrescentado em 2026-11-15.* Já em 2010 a reconstrução por FFT de ≈ 20 MP levava menos de 1 s numa GPU. Não está claro se o "<1 s" é da retropropagação (método 1) ou da recuperação de fase (método 2, "convergence"); o texto do paper diz só "FFT-based reconstructions" |
| Scherrer et al. 2022 (10.1007/978-3-031-20837-9_3; versão do autor no Archimer, pp. 1–15 = pp. 25–39 publicadas) | "However, this iterative and time-consuming step must be performed at each frame of a video, which makes it difficult to support real-time processing." (resumo); "conventional algorithms [5] used to search each object's focus plane and remove twin image artifacts are iterative and computationally intensive and therefore not always compatible with real-time processing." | 1 e 2 (versão do autor) | Sim (iterativa) | Só o próprio detector: YOLOv5s 4 ms, YOLOv5x 14 ms por holograma de 512 × 512 (Tabela 1, p. 11); YOLOv5s+SORT 44 FPS (Tabela 2, p. 12) | Nenhuma reconstrução cronometrada; o "baseline" de acerto é a função de transmissão perfeita t0, não uma reconstrução | i7 2,9 GHz + GTX 2060 | *Acrescentado em 2026-11-15.* Hologramas **simulados**, 13 objetos por imagem "randomly placed without overlapping" (p. 6), objetos só de amplitude, onda plana, z = 0,8 mm fixo (pp. 6–7); conjunto fechado de 13 classes |
| Zhu et al. 2021 (10.1088/2515-7647/abf250) | "However, traditional digital holography usually requires post-processing steps, which is time-consuming and may not achieve the final object detection performance." | 1 (resumo) | Sim | Só entre redes: "decision time" = treino + teste (Tabela 2) | Outras redes e trabalhos anteriores do grupo, nenhuma reconstrução | TITAN V | *Acrescentado em 2026-11-15.* Microplásticos, conjunto fechado |
| Pirone et al. 2026 (10.1088/2515-7647/ae79c2) | "Some HIFC approaches even utilize raw holograms for classification rather than reconstructed phase images. This is advantageous for high-speed analysis, as it eliminates the computational overhead of the holographic reconstruction pipeline, including zeroth and twin order filtering, refocusing, and phase unwrapping, thus dramatically reducing processing cost." | 2 | Sim (como motivação da literatura) | **Sim, estágio por estágio, mesma máquina** (Tabela 2, p. 6): demodulação (um filtro no domínio de Fourier) 0,0177 s; refoco pela busca do coeficiente de Tamura 0,3975 s; desembrulhamento 0,0444 s; classificação do bruto 0,0527 s (18 IPS) contra a do campo demodulado 0,0289 s (34 IPS). Acerto: bruto 89,62 %, demodulado 90,12 %, refocado 93,87 %, fase 95,87 % (teste, binário) | O pipeline completo off-axis, e as reconstruções aprendidas (refoco por regressão 0,0767 s; UNET ponta a ponta 0,0473 s, Tabela 4, p. 9) | Xeon W7-2475X + RTX 4000 Ada, MATLAB | *Acrescentado em 2026-11-15.* **Medição a favor do nosso argumento:** classificar o campo demodulado (um passo de Fourier) é **mais rápido** que classificar o bruto, porque a entrada é menor (p. 7: "Interestingly, this is faster than directly classifying raw holograms"), e mais acertado; o gargalo é a busca do foco ("the refocusing stage is the main bottleneck", p. 7). Off-axis, ROIs de 512 × 512 com uma célula cada (p. 4); a detecção das células não é cronometrada |
| Göröcs et al. 2018† (10.1038/s41377-018-0067-0) | "The major computational operations are (1) segmentation of the full FOV hologram for object detection (~70 ms), (2) holographic autofocusing and reconstruction (~12 ms/object), and (3) transfer ... and saving of the images on an internal solid-state drive (~10–20 ms per object)." e "The deep learning-based phase-recovery step is currently the most intensive part of our algorithm, with a runtime of ~250 ms/object." (duas colunas juntadas) | 7 | Não afirma (reconstrói) | **Sim, estágio por estágio** | — | GTX 1080 | **Medição a favor do nosso argumento:** autofocus + retropropagação (12 ms/objeto) custam menos que a detecção (70 ms por quadro) e muito menos que a recuperação de fase para imagem limpa (250 ms/objeto) |

### 3b. Lidos, sem a afirmação (não entram na lista "afirma")

| Trabalho (DOI) | O que diz | Pág. |
|---|---|---|
| Sedaghat et al. 2025, HoloMoA (10.3389/fmicb.2025.1640252) | Usa a reconstrução: o resumo diz "using reconstructed phase images as input to a Convolutional Recurrent Neural Network (CRNN)". Não fala em velocidade da reconstrução | 1 |
| Mallery et al. 2026, CTC (10.1038/s44328-026-00084-z) | Detecção em hologramas brutos de campo inteiro (HR-Net em heatmap), "real-time", TensorRT. Não compara com reconstrução | 1, 8 |
| Paquin et al. 2022, colônias (10.1371/journal.pdig.0000122) | Motiva o não-reconstruído por evitar estimar a distância e "having to produce multiple reconstructions at different heights" (Introdução §[11], JATS). Não fala em tempo | — |
| Cugmas et al. 2026, pólen (10.1038/s41598-026-36618-8) | Gerchberg–Saxton com 200 iterações para classificação visual por especialistas. Sem tempos | 2–3 |
| Liao et al. 2019, CNN quantizada em FPGA (10.3390/s19235103); Vaghashiya et al. 2022 (10.3390/bios12030144); Baik et al. 2023 (10.3390/bios13120993) | Imagem de sombra lens-free, sem reconstrução. Não comparam com reconstrução (o de 2019 dá 17,9 fps no FPGA) | — |
| Chen et al. 2021, QIMS (10.21037/qims-21-16) | Classifica imagens reconstruídas (espectro angular + autofocus). Sem afirmação | — |

### 3c. Somente resumo (não citar entre aspas)

| Trabalho (DOI) | Acesso | O que o resumo diz (paráfrase) |
|---|---|---|
| Guo et al. 2021 (10.1002/lom3.10402) | Wiley, sem acesso aberto | Afirma que a reconstrução numérica é cara e lenta e impede o monitoramento em tempo real, e que a CNN no padrão de interferência a elimina. Segundo Sanborn (p. 10), o pré-processamento de Guo leva 1,6–2,5 s por imagem |
| Cotter et al. 2021 (10.1002/lom3.10438) | AM no DSpace do MIT; o download recebeu HTTP 429 duas vezes | **Mediu:** detecta o padrão no bruto e reconstrói só uma janela, com busca de distância (de 1000 para 31 reconstruções). Gasta 1 % do tempo da reconstrução completa |
| Delli Priscoli et al. 2021 (10.1109/JSTQE.2021.3059532) | CC BY, mas o IEEE devolveu HTTP 502 | Afirma que a recuperação de fase pode ser muito demorada e classifica células no holograma bruto (off-axis) |
| Zhang et al. 2022, Raw3dNet (10.1364/OE.470324) | Optica, aberto, mas a página serve um desafio JS ao cliente | Câmera lensless com máscara (não é holografia). Afirma que a reconstrução custa tempo e computação e reconhece gestos no vídeo bruto |
| Wu et al. 2023 (10.1364/BOE.490199) | Optica; o PMC só tem o resumo | **Mediu:** reconstrução por rede mais de 10 000 vezes mais rápida que a iterativa (deconvolução variante no espaço), mais de 25 fps |
| Yagoda-Aharoni et al. 2026 (10.1002/cytoa.70008) | Wiley, CC BY-NC, mas HTTP 403 | 0,44 ms por detecção + classificação, mais de 10 vezes mais rápido que o YOLOv8n. Compara com detector, não com reconstrução |
| Zhang et al. 2022, OSNet, AO 61:B111 (10.1364/AO.444856) | Sem acesso aberto | Coordenadas 3D direto do holograma, "improved processing speed" |
| Han et al. 2025 (10.1021/acs.analchem.5c05447) | Sem acesso aberto | Afirma que os algoritmos generativos de reconstrução têm inferência lenta |
| Kim et al. 2021, Holo-SpeckleNet (10.1016/j.jhazmat.2020.124637) | Sem acesso aberto | Mede concentração de material particulado direto do speckle, sem pós-processamento demorado |
| O'Connor et al. 2020, Douglass et al. 2022 e Gupta et al. 2025, SRPE lensless (10.1364/OE.405563; 10.1364/OE.469199; 10.1364/OE.546326) | Optica, desafio JS | Classificação sem reconstrução com codificação por difusor. O de 2022 fala em economia computacional ao recortar a assinatura |
| *Acrescentados em 2026-11-15 (complemento aberto):* | | |
| Song et al. 2026, HoloAtt-UNet (10.1016/j.measurement.2026.122543) | Optica Open: desafio anti-bot | Do holograma bruto a máscaras de partículas de nuvem, evitando a reconstrução em vários planos. **Diz ter medido:** 479 vezes mais rápido que o algoritmo convencional em CPU e cerca de 60 vezes mais rápido que o convencional acelerado em GPU. Sem o texto, não sei o baseline (quantos planos) nem se a detecção entra. **Prioridade para o orientador baixar** |
| Zhang et al. 2021, plâncton (10.1016/j.optlastec.2021.106979) | Elsevier | Afirma que a reconstrução exige "time-consuming iterative calculations" e classifica o bruto com transferência de aprendizado (≈ 92 %) |
| "Holographic Classifier", INDIN 2020 (10.1109/INDIN45582.2020.9442146; autores não conferidos) | IEEE | Afirma que desembrulhar, filtrar e refocar "costs a lot of time"; detecção de microplásticos no bruto |
| JBO 26:036001 (2021), contagem de hemácias por FCN (10.1117/1.JBO.26.3.036001) | SPIE: desafio anti-bot | Afirma que a análise pela fase é ineficiente pela complexidade da reconstrução; U-Net no bruto, > 288 células/s em 200 × 200 µm |
| Tese IYTE 2019, viabilidade celular no bruto (sem DOI) | Repositório | Afirma que a reconstrução "requires intense computational work" |
| Delli Priscoli et al. 2021 (10.1109/JSTQE.2021.3059532) | IEEE: HTTP 502 de novo | (já listado acima) |
| Opt. Lasers Eng. 2019, contagem no bruto off-axis (10.1016/j.optlaseng.2019.02.010; autores não conferidos) | Elsevier | Detecção e contagem de objetos de fase no bruto **off-axis**, acerto de até 100 % com até 2,1·10³ células/mm², comparado com a contagem visual sobre a fase desembrulhada. O resumo não faz a afirmação de tempo. Ver a seção 5, item 12 |
| Reconstruction-free com ViT, Opt. Commun. 2026 (10.1016/j.optcom.2026.133421) e preprint SSRN (10.2139/ssrn.6057112) | Elsevier; SSRN não tentado | Só o título ("High-throughput holographic sensing: A reconstruction-free framework via Vision Transformer foundation models") |

### 3d. Resumo dos números

- **Afirmam, com a frase localizada no texto completo: 13.** São eles [11] Rockembach, [14] Liu, Kim 2018, Song 2025, Xu 2025, Moon 2025, Aharoni 2025, Sanborn 2023, Bravo-Frank 2025, Molani 2026, Terbe 2022 (só sobre a recuperação de fase), Matthews 2024 e OAH-Net 2025. Os dois de reconstrução aprendida contra a iterativa (Rivenson 2018, FIN 2022) também afirmam, mas comparam imagem limpa com imagem limpa.
- **Mediram contra uma reconstrução no mesmo hardware: 3.**
  - Liu: varredura de 501 distâncias, sem detector.
  - Matthews: pilha de refoco para rastreamento 3D.
  - OAH-Net: pacote comercial; a reconstrução é aprendida.
- Mais 3 medições sólidas em tarefa de imagem: Rivenson e FIN contra a iterativa; Göröcs estágio por estágio.
- **Mediram só o próprio pipeline ou compararam com números de outros artigos: 5.** Kim, Xu, Aharoni, Sanborn, Moon.
- **Não mediram nada: 5.** Song, Molani, Bravo-Frank 2025, Terbe (que não trata da reconstrução) e [11] (só tempo de treino). *Atualizado em 2026-11-14 com o texto completo; antes: "4 + 1 ... mais [11], que não é verificável".*
- **Chamam a reconstrução de iterativa:** Kim 2018, Xu 2025, Terbe 2022 (recuperação de fase) e [11] (p. 365). *Linha acrescentada em 2026-11-14.*
- **Não fazem a afirmação: 9.** [13] Bravo-Frank 2024, Sedaghat, Mallery, Paquin, Cugmas, os três de sombra lens-free e Chen 2021 (QIMS).
- **Somente resumo: 12 registros** (10 linhas na tabela 3c). Desses, 8 estão em acesso aberto mas não puderam ser baixados: Cotter, Delli Priscoli, Raw3dNet, Wu 2023, Yagoda-Aharoni e os três SRPE.

**Atualização de 2026-11-15 (complemento aberto e textos novos):**

- **Afirmam, com a frase localizada no texto completo: 17** (os 13 acima mais Seo 2009, Scherrer 2022, Zhu 2021 e
  Pirone 2026, este como motivação atribuída à literatura).
- **Chamam a reconstrução de iterativa:** acrescentar Scherrer 2022 (resumo e p. 2).
- **Mediram estágio por estágio, a favor do nosso argumento: 2** (Göröcs 2018 e Pirone 2026). Pirone é o caso mais
  próximo do nosso: na mesma máquina, um passo no domínio de Fourier (a demodulação) custa menos que a própria
  classificação, e classificar depois dele é mais rápido que classificar o bruto; o que custa é a busca do foco.
- **Mediram só o próprio pipeline:** acrescentar Scherrer 2022 (só o detector) e Seo 2010 (só a reconstrução).
- **Não mediram:** acrescentar Seo 2009 e Zhu 2021 (este só "decision time" entre redes).
- **Somente resumo, novos: 7 linhas** (fim da tabela 3c), entre eles HoloAtt-UNet 2026, que diz ter medido contra a
  reconstrução em vários planos e cujo texto foi bloqueado.

---

## 4. Material por tema (para o Related Work)

Legenda: **[TC]** texto completo lido; **[TC-parcial]** texto completo baixado e só lido por busca de termos; **[R]** somente resumo (não citar). O acesso aparece entre parênteses.

**S1 – reconhecimento no holograma bruto**
- *2026-11-15:* [TC] Seo 2009† (PMC): reconhecimento por correlação com biblioteca, sem reconstrução; precedente da densidade. [TC] Scherrer 2022 (Archimer): YOLOv5 + SORT em hologramas simulados de plâncton, 13 classes, sem sobreposição. [TC] Zhu 2021 (IOP): microplásticos no bruto. [TC] Pirone 2026 (IOP): seis representações, do bruto à fase, com tempo e acerto. [R] HoloAtt-UNet 2026; [R] Zhang 2021 (OLT); [R] INDIN 2020; [R] JBO 2021; [R] OLEN 2019 (off-axis, denso).
- [TC] Rockembach 2024 (IEEE Xplore, licença UFSC; texto completo desde 2026-11-14, antes só a p. 364): YOLOv5/v8/v9 detectam e classificam letras sintéticas (26 classes, Fresnel em Matlab, várias letras por imagem de 640 × 640) no bruto, fechado. Os autores apontam a limitação de conjunto fechado e o retreino quando muda o alvo ou o z (p. 369).
- [TC] Bravo-Frank 2024 (editora): YOLOv8n → YOLOv8 → HRNet em hologramas de bactérias em fluxo, com classe "unknown" por limiar.
- [TC] Bravo-Frank 2025 (arXiv): mesmo grupo, com dois planos reconstruídos na entrada do YOLOv8n.
- [TC] Liu 2021 (AM): autoencoder + SOM, clustering no bruto, comparável ao reconstruído.
- [TC] Kim 2018† (editora): VGG19 + MLP em recortes brutos de células com microesferas.
- [TC] Song 2025 (PMC): HoloNet, rede de núcleos grandes para hologramas brutos; o bruto rende mais que o reconstruído.
- [TC] Sanborn 2023 (arXiv): YOLOv5 no holograma realçado, plâncton e leveduras.
- [TC] Matthews 2024 (PLOS): YOLOv5 no bruto para rastreamento 3D de *E. coli*; a profundidade sai do tamanho da caixa.
- [TC] Mallery 2026 (editora): HR-Net no holograma bruto de campo inteiro, células tumorais circulantes.
- [TC] Paquin 2022 (PMC): CNN + RNN em time-lapse lens-free não reconstruído.
- [TC] Aharoni 2025 (PMC): MobileNet em projeções off-axis brutas.
- [TC] Molani 2026 (editora): simulador de hologramas brutos e limites de detecção por IA.
- [R] Guo 2021; [R] Delli Priscoli 2021; [R] Cotter 2021 (detecção no bruto + reconstrução local).
- Adjacentes, de outra modalidade: [R] Raw3dNet, câmera com máscara; [R] SRPE de Javidi; [TC] imagem de sombra lens-free (Liao 2019, Vaghashiya 2022, Baik 2023).

**S2 – deep learning em hologramas (sobre a reconstrução)**
- [TC] Terbe 2022 (MDPI): 3D-CNN sobre um volume refocado contra 2D.
- [TC] Chen 2021 (QIMS): CNNs em reconstruções lensless.
- [TC] Göröcs 2018† (editora): citômetro portátil, reconstrução + recuperação de fase aprendida + classificação.
- [TC] Xu 2025 (MDPI): A-Unet + YOLOv5.
- [TC] Cugmas 2026 (editora): Gerchberg–Saxton para classificação visual.
- [TC-parcial] Perlemoine 2026 (PMC): colônias em ágar.
- [R] HoloSea plâncton 2021 (10.1186/s12862-021-01839-0); [R] microplásticos (10.1364/AO.403366); [R] Karenia brevis (10.1016/j.hal.2023.102401).

**S3 – open set em holografia**
- *2026-11-15:* nada novo sobre holograma bruto. Só títulos: anomalia em citometria holográfica (Opt. Commun. 2026, 133563) e OOD em DHM off-axis (Opt. Laser Technol. 2025, 113813), ambos sem resumo nos índices.
- [TC] Sedaghat 2025: HoloMoA, detecção de mecanismo novo com rede siamesa **sobre fases reconstruídas**. A frase de `02-related.tex` sobre "latent representation" deve dizer que a entrada é a fase reconstruída.
- [TC] Bravo-Frank 2024: "unknown" por limiar.
- [R] Pastore et al. 2020 (10.1038/s41598-020-68662-3): plâncton sem anotação com detecção de anomalia. Não conferi se as imagens são holográficas.
- Ay 2022 e Pouliquen 2024 (já no `main.bib`, hologramas de segurança) não foram relidos agora.
- O PubMed não trouxe mais nada relevante: os outros 6 da S3 são ruído.

**S4 – open set em microscopia**
- *2026-11-15:* [R] OpenGram, bactérias em Gram (IJCNN 2023, 10.1109/IJCNN54540.2023.10191073); [R] Open-Set Plankton Recognition (ECCV W 2025, arXiv 2503.11318). Nenhum é holográfico. Citados no Related Work só como existência, sem números.
- [R] ARTiMiS (10.1021/acs.est.5c06078): classificadores fechados falham com partículas novas.
- [R] "foundation model zoo" para busca por similaridade de células (10.3389/fonc.2025.1480384).
- [R] PathoSafe, rejeição OOD em biossensores (10.3390/bios16090518).
- O resto da S4 é ruído.

**S5 – camadas de Fourier aprendidas**
- *2026-11-15:* [R] Ekec & Teğin 2026 (OE 34:34757): FNO para câmera sem lente com difusor, motivado por o modelo direto ser uma multiplicação no domínio da frequência; [R] PSF-Net (SPIE 2024), FNO para reconstrução de hologramas de partículas.
- [TC] Terbe 2022, p. 7, propõe como trabalho futuro exatamente filtros de Fourier aprendíveis com campo receptivo global: "A hologram can be represented as a complex image (containing the amplitude and phase information naturally) that can be processed in the Fourier space by element-wise multiplication with learnable filter matrices which have a global receptive field." **Isso é um antecedente direto da nossa camada e deve ser citado na contribuição.**
- [TC] FIN 2022: módulos SPAF que operam no domínio da frequência para reconstrução.
- [R] FNO para holografia computacional 4K (10.1038/s41467-025-62997-z).
- A S5 quase não funciona no PubMed (ver a seção 1).

**S6 – reconstrução e autofocus aprendidos**
- [TC] Rivenson 2018†; [TC] FIN 2022; [TC] OAH-Net 2025.
- [R] Wu 2023 (tempo real lensless); [R] autofocus com transformer pequeno (10.1364/OE.458948); [R] base aberta de DLHM para autofocus (10.1364/AO.507412); [R] rede de remoção de imagem gêmea (10.1364/OE.505440); [R] multifoco automático (10.1364/OE.586494).

**S7 – custo e campo de visão inteiro**
- [TC] Göröcs 2018† (tempos por estágio); [TC] Matthews 2024 (CPU, Jetson e Raspberry Pi); [TC] Liu 2021 (CPU de baixo consumo).
- [R] Cotter 2021; [R] GEOMScope (10.1002/lpor.202100072); [R] Wirtinger flow acelerado (10.3390/cells11131999); [R] HoloBio em tempo real (10.1371/journal.pcbi.1013928).
- `sobieranski2015portable` (já no `main.bib`).

**S8 (extra) – realismo da simulação**
- *2026-11-15:* [TC] Scherrer 2022 (objetos só de amplitude, onda plana, z fixo, sem sobreposição; pp. 6–7); [R] HoloCel 2026 (MDPI, hologramas de células gerados); [R] coerência espacial em reconstrução sem lente (OL 2026, arXiv 2607.15765); [R] efeito de aproximações do modelo na reconstrução in-line (SPIE 2022, HAL).
- [TC] Molani 2026; [R] efeitos de coerência em DIHM (10.1364/JOSAA.25.002459); [R] coerência e resolução (10.1364/OE.26.000242).

---

## 5. O que contradiz ou ajusta o rascunho da C.3

1. **Chave bibliográfica:** o rascunho usa `\cite{rockembach2024}`, mas a chave no `main.bib` é `rockembach`.
2. **[13] não serve para a afirmação.** Bravo-Frank 2024 não diz que a reconstrução é lenta e não compara com ela; o "real-time" é da cascata de detectores. Quem faz a afirmação é o trabalho seguinte do mesmo grupo (Bravo-Frank 2025), e esse pipeline "real-time" **inclui duas reconstruções de Fresnel** antes do YOLO. Isso reforça o nosso ponto.
3. **[14] mediu, no mesmo hardware, e o parágrafo precisa reconhecer isso.** O ganho de três ordens de grandeza é real contra o baseline que Liu escolheu: autofocus cego de 501 distâncias por recorte numa CPU Atom, sem detector. Cabe na categoria "contra o pipeline completo", com a diferença explicada (busca cega contra distância conhecida ou buscada numa faixa estreita).
4. **Matthews 2024 mediu um ganho de cerca de 11 vezes na mesma CPU** contra uma pilha completa de refoco (rastreamento 3D). É outro caso legítimo contra a pilha, que o parágrafo deve citar como medido.
5. **Medições independentes a favor do argumento:**
   - Göröcs 2018: autofocus + reconstrução custam cerca de 12 ms por objeto; a detecção, cerca de 70 ms por quadro; a recuperação de fase para imagem limpa, cerca de 250 ms por objeto (GTX 1080).
   - Xu 2025: YOLOv5 14,7 ms contra reconstrução aprendida 13,0 ms.
   - OAH-Net: YOLOv8 3,5 ms (número citado) contra menos de 3 ms de reconstrução.
   - Nos pipelines medidos pelos próprios autores, o detector custa tanto ou mais que a reconstrução.
6. **"Described as iterative":** vale para Kim 2018, Xu 2025, Terbe 2022 (recuperação de fase) e Rockembach (p. 365: "The iterative and complex procedure for reconstruction usually makes real-time applications unfeasible..."). Liu e Song falam em "computationally expensive/intensive", sem "iterative". Molani 2026 é o caso mais direto: chama de "computationally intensive" até a "numerical back-propagation". *Atualizado em 2026-11-14 com o texto completo; antes, Rockembach estava entre os que não usam "iterative".*
7. **Dois pontos para o Related Work fora do parágrafo C:** Terbe 2022 antecipa a camada de Fourier aprendível (S5), e HoloMoA trabalha sobre a fase reconstruída (S3).
8. **Detalhe numérico:** a instrução falava em "cerca de 1 ms por quadro". A macro `\DistTimeRecZZeroFrontGpuBigMs` vale 2,9 (front end com flat field e entrada da rede). O texto da C.3 já usa a macro.
9. **[11] com o texto completo (acrescentado em 2026-11-14):** a frase da C.3 "Our own earlier work made this argument ... without measuring it" se confirma: o artigo afirma o custo (pp. 364, 365, 369), chama a reconstrução de iterativa (p. 365) e só mede tempo de treino (p. 368). A própria conclusão diz que o tempo real ainda precisa ser avaliado fora da simulação (p. 369). O nosso texto o complementa com a medição. Dois cuidados de redação: (a) o artigo é de **detecção** (YOLO, várias letras por imagem), o que casa com "convolutional detectors" em `01-intro.tex`; (b) o "z = 50k" do artigo não tem unidade, e a leitura 5·10⁴ λ é nossa.
10. **Seo 2009 faz as duas coisas (acrescentado em 2026-11-15):** é o precedente da queda por densidade (fórmula da
    razão de sobreposição; 10 % abaixo de 671 células/µL; acurácia mantida até ≈ 3000 células/µL, sobreposição
    ≥ 37 % acima disso; seção "Discussions") **e** já fazia o argumento de velocidade, sem medir ("numerically and
    computationally our approach is much simpler and faster", mesma seção). Entrou nas duas partes do Related Work.
11. **Isikman 2012 não diz, na frase, que a contagem até 0,4 milhão de células/µL foi feita na reconstrução**
    (seção III.A: "The counting error is <5% for cell densities up to ~0.4 Million cells/μL"; a legenda da Fig. 5a
    mostra contagem "in the hologram domain (pink curve) and the reconstructed image domain (blue curve)"). A fonte
    primária, a ref. [37] dela, é Seo et al. 2010 (Anal. Chem. 82:4621), que li no PMC: "we measured the density of
    RBCs based on automated counting of digitally reconstructed cell images [...] the reconstructed cell images
    yielded an absolute error rate of <5%, up to a cell density of ~0.4 × 10⁶ cells/μL", e "all of the lens-free RBC
    holograms are completely overlapping (because of a high cell density of ~0.4 × 10⁶/μL)" (Results and
    Discussion). No paper cito as duas (`seo2010`, `isikman2012`) para a frase "com reconstrução".
12. **Contraexemplo possível, só pelo resumo:** um trabalho de 2019 (Opt. Lasers Eng., tabela 3c) conta objetos de
    fase no bruto **off-axis** com acerto de até 100 % até 2,1·10³ células/mm², bem acima das nossas densidades. No
    off-axis com objetiva o padrão de cada célula não se espalha como no in-line sem lente, então não contradiz o
    mecanismo; mas, sem o texto, não entra no paper.
13. **Pirone 2026 é a medição independente mais próxima da nossa** (off-axis, mesma máquina, estágio por estágio):
    o passo no domínio de Fourier é barato e até acelera a classificação; o caro é a busca do foco. Entrou no
    parágrafo, com a ressalva de que é off-axis e de que a detecção não é cronometrada.

---

## 6. Pendências e o que não pude verificar

- **Scopus e ScienceDirect:** sem credencial nem chave. Os `.RIS` devem ir para `referencias/c/scopus/` e `referencias/c/sciencedirect/`, com `S<n>` no nome e sem filtro de ano; depois basta rodar `refs_merge.py`. O que eles devem trazer e o PubMed não cobre:
  - IEEE: o CBMS de Rockembach; Delli Priscoli (JSTQE).
  - *npj Biosensing* 2024 (Bravo-Frank).
  - *Limnology & Oceanography: Methods* (Guo, Cotter).
  - Periódicos Elsevier de óptica (Opt. Lasers Eng., Opt. Commun.) e anais SPIE/Optica (DH&3D).
  - Os trabalhos de Hong et al. sobre partículas 3D (Shao et al. 2020, *Opt. Express*, citado por Sanborn e Molani).
  - Altman & Grier 2020 (CATCH).
- ~~**[11] pp. 365–369:** sem acesso aberto. A confirmação de que o trabalho não mediu depende dos autores.~~ *Resolvido em 2026-11-14:* o texto completo veio do IEEE Xplore (licença UFSC) e foi lido; o trabalho não mediu (ver a seção 2). Falta só o `provenance.json` em `referencias/c/rockembach2024_full/`.
- **Abertos, mas bloqueados para o cliente automático:**
  - Optica (OE/BOE/AO sem corpo no PMC): Raw3dNet, Wu 2023, SRPE.
  - IEEE (Delli Priscoli), DSpace do MIT (Cotter, HTTP 429), Wiley (Yagoda-Aharoni).
  - Não insisti nem contornei. Uma pessoa com navegador consegue baixar todos.
- **Referências 7–9 de Liu** (reconstrução em FPGA e CUDA) não foram lidas. Elas mediram reconstrução acelerada e podem dar outro número de custo de reconstrução.
- **Hannel et al. 2018** (arXiv 1804.06885, localização por CNN contra ajuste de Lorenz–Mie, mediu em CPU, GPU e Raspberry Pi): baixado (`hannel2018_arxiv/`), mas só lido por busca de termos. Não entrou na tabela.
- **Paginação:** Liu foi lido no AM (a paginação da versão publicada não foi conferida). Sanborn e Bravo-Frank 2025 foram lidos no arXiv (a paginação difere da versão publicada). Os textos via PMC não têm página.
- **Triagem:** os 207 registros do PubMed foram triados por título e, para os sinalizados, pelo resumo. As decisões estão em `referencias/c/merged/screening.csv`: 28 incluídos, 179 "não incluído".
- **2026-11-15:** a triagem dos 711 trabalhos novos do complemento aberto está no mesmo arquivo (37 incluídos; total
  56 em 918). Scopus e ScienceDirect **continuam sem rodar**; o que o complemento não cobre está na seção 1b.
  Abertos mas bloqueados ao cliente automático, novos: HoloAtt-UNet (Optica Open), a versão HAL de Scherrer, JBO
  2021 (SPIE), Cotter (MIT, 429 pela terceira vez), Delli Priscoli e IEEE Photonics J. 2024 (IEEE, 502). Não contornei
  nenhum desafio.

---

## 7. O Related Work reescrito (2026-11-15) e a fonte de cada afirmação

Branch `rewrite/related-work` do repositório LaTeX, `sections/02-related.tex`. Uma linha por afirmação sobre outro
trabalho; "TC" = texto completo lido; "R" = só resumo (descrito sem aspas e sem "mediu").

| Afirmação no paper | Fonte (onde está a frase) |
|---|---|
| Seo 2009 classificou células pela textura do holograma, sem reconstrução (citação entre aspas) | TC, PMC3931575, "Discussions": "In our approach, there is no such digital reconstruction, and the detected holographic lensfree image is simply analyzed by a pattern recognition algorithm" |
| Kim 2018: células marcadas com microesferas | TC, Sci. Rep. 8:17003 (tabela 3a; seção 4) |
| Delli Priscoli 2021: linhagens de neuroblastoma em holograma de microscópio | R (resumo do JSTQE) |
| Zhu 2021: microplásticos | TC, J. Phys. Photonics 3:024013, resumo e Introdução |
| Scherrer 2022 e Sanborn 2023: plâncton | TC (Archimer; arXiv 2301.09638) |
| Bravo-Frank 2024: bactérias em líquidos estéreis; cascata; classe "unknown" por limiar (p. 3) | TC, npj Biosensing 1:8, p. 3: "an additional class 'unknown', is used to classify particles with confidences below the FPR threshold of our known classes" |
| Matthews 2024: micróbios rastreados em 3D | TC, PLOS ONE 19:e0301182 |
| Song 2025: células de câncer de mama; bruto classifica melhor que reconstruído | TC (PMC), Results, §[14]: "raw diffraction images provided more efficient features for cell classification than reconstructed images" |
| CBMS 2024: YOLO detecta e classifica 26 letras em hologramas simulados 640 × 640; conjunto fechado; validação; "can only confidently classify the specific objects it is trained for" (p. 369) | TC, pp. 367–369 (seção 2 deste documento) |
| Liu 2021: clustering do bruto comparável ao do reconstruído | TC (AM), resumo e Tabela 4 |
| Pirone 2026: acerto cresce a cada estágio da reconstrução (Tabela 2); ROIs de 512 × 512 com uma célula (p. 4) | TC, Tabela 2 p. 6; p. 4: "each of which contains a single snapshot of a cell"; p. 11: "classification accuracy increases monotonically with reconstruction completeness" |
| Scherrer 2022: "without overlapping", só amplitude, onda plana, z = 0,8 mm (pp. 6–7 da versão do autor) | TC, pp. 6–7 (seção 3a) |
| Cotter 2021: extração sem reconstruir o holograma inteiro, em hologramas com alvos esparsos | R (resumo: "extract targets from holograms where target distribution is relatively sparse without reconstruction of the full hologram") |
| Seo 2009: fórmula da sobreposição, 671 células/µL, ≈ 3000 células/µL, "≥37 %" (aspas) | TC, "Discussions" (seção 5, item 10) |
| Com reconstrução, < 5 % de erro até ≈ 0,4·10⁶ células/µL, hologramas completamente sobrepostos | TC, Seo 2010 (PMC2892055), "Results and Discussion"; Isikman 2012, III.A (seção 5, item 11) |
| Rivenson 2018, Wu 2018, FIN 2022, OAH-Net 2025 reconstroem | TC (Rivenson, FIN, OAH-Net); Wu 2018 já estava no texto antigo, não relido |
| Göröcs 2018 classifica após reconstrução e recuperação de fase; Terbe 2022 classifica reconstruções e volumes refocados com 3D-CNN; HoloMoA usa fase reconstruída numa rede recorrente | TC (tabela 3a; seção 3b; HoloMoA, resumo: "using reconstructed phase images as input to a Convolutional Recurrent Neural Network") |
| Lista dos que afirmam o argumento | TC, tabela 3a: Seo 2009, Kim 2018, Liu 2021, Zhu 2021, Scherrer 2022, Sanborn 2023, Matthews 2024, Song 2025, Xu 2025, Bravo-Frank 2025, Molani 2026, Pirone 2026 |
| "iterative": Kim, Scherrer, Xu | TC: Kim p. 2; Scherrer resumo e p. 2; Xu p. 1 |
| Molani inclui a retropropagação entre as técnicas caras | TC, p. 2: "Common reconstruction techniques, such as numerical back-propagation and iterative methods often suffer from noise and are computationally intensive" |
| Bravo-Frank 2024 não faz a afirmação; o tempo real vem da cascata; Bravo-Frank 2025 reconstrói dois planos de Fresnel antes do detector | TC, 2024 p. 6; 2025 arXiv pp. 5–6: "these enhanced images are reconstructed into additional focal planes at z = 6 µm and 12 µm ... using a Fresnel diffraction kernel" |
| CBMS 2024: "computationally expensive" (p. 364), "iterative and complex" (p. 365), "significantly reduces processing time and computational resources" (p. 369); só tempo de treino; Eq. 3 é convolução de Fresnel com um par de FFTs; tempo real deixado para um contexto não simulado (p. 369) | TC, seção 2 deste documento |
| Liu 2021: ≈ 14 s por recorte contra < 0,1 s; 501 distâncias de 10 a 60 mm; sem localização cronometrada (Tabela 5) | TC, Tabela 5 e nota b; p. 7 |
| Matthews 2024: 149 ms contra 1658 ms por quadro, mesma CPU (Tabela 2); pilha de refoco para 3D | TC, Tabela 2 (p. 11), p. 5 |
| Rivenson 2018 e FIN 2022 comparam recuperação de fase aprendida com a iterativa multialtura | TC, Rivenson tabela p. 5; FIN Tabela 1 |
| Göröcs 2018: ≈ 70 ms por quadro para detectar, ≈ 12 ms por objeto para autofocus + reconstrução, ≈ 250 ms por objeto para a recuperação de fase (p. 7, GPU) | TC, p. 7 (GTX 1080) |
| Xu 2025: reconstrução aprendida 13,0 ms, YOLO 14,7 ms | TC: "The average reconstruction time for each image is 0.0130 s, the recognition time is 0.0147 s" |
| Pirone 2026: demodulação 0,018 s, busca do foco 0,40 s, demodulado 34 contra 18 imagens/s porque o campo é menor (Tabela 2) | TC, Tabela 2 (p. 6) e p. 7 |
| Seo 2010: reconstruções por FFT de ≈ 20 MP em menos de 1 s numa GPU | TC, "Experimental Methods" (seção 3a; ressalva sobre qual método) |
| Open set em microscopia: bactérias em Gram (OpenGram) e plâncton, não holográficos | R (resumos) |
| HoloMoA: novidade de mecanismo de ação, rede siamesa, fase reconstruída | TC (resumo e Métodos) |
| "in the indexes we searched we found no open-set recognition on raw lensless holograms" | Triagem das strings S3/S4 nos três índices (seções 1, 1b e 4) |
| FNO para câmeras sem lente com difusor (Ekec & Teğin 2026) | R (resumo) |
| Terbe 2022, p. 7, filtros de Fourier aprendíveis como trabalho futuro (aspas) | TC, p. 7: "A hologram can be represented as a complex image ... that can be processed in the Fourier space by element-wise multiplication with learnable filter matrices which have a global receptive field" |

Números nossos no parágrafo, todos por macro: `\TBackpropGpuBigMs`, `\TBackpropCpuBigS`,
`\DistTimeRecZZeroFrontGpuBigMs`, `\DistTimePropFrontGpuBigMs`, `\TYoloTiledGpuBigMs`, `\TYoloTiledCpuBigS`,
`\FullDetectPctMinFloor`, `\FocusBlindN`, `\TAutofocusGpuBigMs`, `\TTwinGpuBigMs`, `\TBlindOverNarrowGpuBig`.
