# Caderno de laboratório: distância, autofocus e focal stack

Protocolo: `docs/exp_distancia/PROTOCOLO.md`. Branch `exp/distancia-autofocus`, partindo de `9488fce` (main).
Todos os comandos rodam da raiz do repositório, depois de `source scripts/exp_distancia/env.sh`
(resultados em `results_exp_distancia/`, logs em `logs/exp_distancia/`, 4 threads por processo).

Máquina: DGX H100 compartilhada (6 × H100 80 GB via MPS, 224 CPUs). Horários em BRT (UTC−3).

---

## 2026-11-13 — Etapa 0: preparação e reprodução

### Ambiente

- Código: `9488fce`, árvore limpa. Ambiente do paper já instalado em `../.envbuild/holo-openset`
  (Python 3.11.18, PyTorch 2.5.1+cu121, o `requirements-lock.txt`); usei esse em vez de criar outro conda.
- Carga do servidor às 11:46: `load average 400.68, 398.14, 390.15`; as seis GPUs a 100 % de utilização e
  56–76 GB ocupados por outros usuários (MPS, sem reserva). **Não há GPU livre.** Isso não afeta acurácia, mas
  invalida medições de tempo em GPU (regra 8.1 do protocolo); ver "Timing de referência" abaixo.

### Desvios do protocolo nesta etapa

1. **`reproduce download` não funciona**: `holo_openset/reproduce.py` tem `ZENODO_RECORD = None` (o registro ainda
   não foi publicado). Usei os tars do registro que estão em `../.envbuild/zenodo/` (os mesmos que serão publicados),
   conferidos um a um contra `checksums/zenodo.sha256` (9/9 OK) e desempacotados em `data/` e `models/`, que é
   exatamente o que o `download` faz.
2. **`reproduce check` é 12/12, não 11/11**: hoje são 11 tabelas + `numbers.tex`. O texto do protocolo (e do
   README, "ten tables") está uma tabela atrasado.
3. **`reproduce check` depende do que está em `models/`**: a macro `\NModels` conta os `.pt` em disco. Com só
   `models/realistic` desempacotado deu 110 e o check falhou (11/12, `numbers.tex`); com os quatro conjuntos de
   modelos em disco (ou com nenhum) dá 240 e passa. Não é um problema dos resultados, mas quem desempacotar só
   parte do registro vê o check falhar.
4. `paper tables` (e portanto `reproduce check`) **regrava `results/data_summary.json`** quando o conjunto base
   está em disco, mesmo sendo só leitura em espírito. O conteúdo regravado é idêntico (`git status` limpo), mas é
   uma escrita em `results/` que o protocolo proíbe; fica registrado.

### Comandos

```bash
git checkout -b exp/distancia-autofocus                       # a partir de 9488fce
# tars locais do registro, conferidos contra checksums/zenodo.sha256 e desempacotados em data/ e models/
pytest -q                                                     # 11 passed
python -m holo_openset reproduce check                        # 12/12 files identical to expected/
python -m holo_openset reproduce verify-data                  # 10 files match, 0 differ, 64 not on disk
bash scripts/exp_distancia/etapa0_sanity.sh cuda:4            # tmux expdist; log em logs/exp_distancia/etapa0_sanity.log
```
