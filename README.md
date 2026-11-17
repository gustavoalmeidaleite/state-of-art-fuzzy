# Estado da arte: lógica fuzzy e fuzzy aplicado ao transplante renal

Levantamento feito em 17/11/2026 para o Time 1 (Lógica Fuzzy) do projeto HLAGyn (CEIA/UFG), que estratifica o risco de
perda do enxerto renal com regras fuzzy interpretáveis.

## Conteúdo

| Arquivo | O que é |
|---|---|
| [CATALOGO.md](CATALOGO.md) | Catálogo dos 109 trabalhos, em ordem de relevância dentro de cada seção, com a situação do PDF |
| `catalogo.csv` / `catalogo.json` | Os mesmos dados em formato tabular; o JSON traz o resumo de cada artigo |
| `pdfs/` | 38 PDFs baixados (cópias de acesso aberto), nomeados pelo código do catálogo (A01, B04…) |
| `scripts/` | `lista.py` (lista curada, relevância e notas) e `monta_catalogo.py` (metadados, download e geração do catálogo) |

Seções do catálogo: **A** fuzzy aplicado ao transplante renal e de órgãos (36), **B** estado da arte do fuzzy em geral (60)
e **C** contexto não fuzzy: extração de regras e predição em transplante renal (13).

## Como foi feito

- Busca no OpenAlex (cerca de 70 consultas em inglês e português) e na web, mais os trabalhos já citados no código do projeto.
- Triagem e ordenação por título e resumo. **Os artigos não foram lidos na íntegra**; as notas e a síntese abaixo
  descrevem o que o título e o resumo dizem.
- Download só de cópias de acesso aberto (editora, PubMed Central, arXiv, repositórios). Dos 71 sem PDF, 36 são de
  acesso aberto cujo site recusou o download automático e 35 são pagos ou sem cópia aberta; o catálogo distingue os dois casos.

## Síntese

**Fuzzy em transplante renal.** A literatura é pequena e concentrada em **alocação e priorização**, não em prognóstico:

- Sistemas especialistas fuzzy para atribuir o rim: Yuan et al. (2001, 2002), FORAS (Gündoğar et al., 2005) e Labib (2004).
- A linha de Taherkhani: critérios de alocação ponderados por Delphi e AHP fuzzy (2019) e o FISKA (2022), um sistema Mamdani
  cujas regras foram geradas com árvore de decisão e conferidas por especialistas.
- Dujmović (2025): lógica graduada (LSP) para prioridade em transplante de órgãos.
- TSFAM (Dzieran et al., 2024–2026): memória associativa fuzzy que representa o julgamento do cirurgião na aceitação de rins difíceis de alocar.
- Fora da alocação: apoio à decisão fuzzy para a função renal no pós-transplante (Improta et al., 2019), ANFIS para nível de
  ciclosporina (Gören et al., 2008), escore de compatibilidade doador–receptor (Yellanki, 2012–2013) e decisão multicritério
  com extensões de conjuntos fuzzy (2022–2024).

**Lacuna.** A busca não encontrou nenhum sistema fuzzy baseado em regras para prever perda ou sobrevida do enxerto renal
publicado entre 2023 e 2025. As revisões de IA em transplante renal listam o fuzzy entre os métodos, mas os modelos de
prognóstico recentes são de aprendizado de máquina convencional (seção C).

**Fuzzy em geral.** Os trabalhos recentes giram em torno de interpretabilidade e explicabilidade:

- Revisões de 2024–2025 que situam os modelos fuzzy baseados em regras dentro do aprendizado de máquina interpretável
  (Pickering et al., 2025; Zhang et al., 2025; Lu et al., 2024) e o livro de Alonso et al. (2021).
- Sistemas autoexplicáveis com explicações factuais e contrafactuais (Stepin et al., 2024) e regras fuzzy geradas a partir
  de SHAP, de causalidade ou de modelos tabulares de fundação (2024–2026).
- Uso clínico: neuro-fuzzy inicializado por árvore de decisão (Chen et al., 2020), FIS com regras interpretáveis para
  diagnóstico (Cao et al., 2024), árvores probabilísticas fuzzy (Capitoli et al., 2025), comparação de 16 classificadores
  fuzzy em 12 bases médicas (Czmil, 2023) e as dez dicas de modelagem fuzzy biomédica (Chicco et al., 2023).
- Neuro-fuzzy profundo e classificadores TSK interpretáveis; sistemas intervalares tipo-2; florestas e árvores fuzzy.
- Ferramentas em Python: Simpful, pyFUME, Ex-Fuzzy.

## Pendências

- **Saha (2012)**, citado no código do projeto (curvas triangulares e trapezoidais, min-max, centro de gravidade), não foi localizado.
- **Dujmović (2025)** foi identificado como os dois trabalhos de LSP para prioridade em transplante (A08 e A09); ambos são pagos.
- 13 PDFs são cópias abertas sem licença Creative Commons explícita (arXiv, repositórios institucionais, acesso gratuito
  da editora): A17, A27, A32, A33, B14, B18, B21, B36, B40, B49, C02, C03 e C06. A coluna `licenca` do CSV registra a licença de cada um.
