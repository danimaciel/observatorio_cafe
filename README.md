# Observatório do Café

O Observatório de Pesquisa da Embrapa recortado para o **café** (arábica e canéfora): quem faz o quê
(unidades, pessoas, redes), o que cresce e o que cai, onde estão as lacunas e como as mulheres participam
da pesquisa. Mesmo molde do Observatório das Florestas Plantadas.

## Recorte

- **Acervo** = documentos do Observatório com café (camada de produtos, termos em português, inglês e espanhol) ou
  semanticamente próximos (SBERT), filtrados por um classificador treinado numa amostra de 387 documentos
  pré-rotulados (pasta `Cafe` do Observatório). Conferência por especialistas pendente.
- Facetas próprias: **espécie** (texto, cultivar ou inferida pelo estado/unidade, marcada), **19 temas técnicos em
  5 grupos** (proposta a referendar) e **gênero** (inferido do primeiro nome, genderBR; só agregados).

## Páginas

- **Café:** Visão geral · Tendências (dois períodos comparados) · Lacunas (espécie × tema, estado × tema,
  pesquisa × entrega) · Mulheres na pesquisa (agregado, com supressão de grupos com menos de 10 pessoas).
- **Quem faz:** Produção e colaboração · Unidades · Redes · Mapa · Pesquisadores (herdadas do Observatório).
- **Conteúdo:** Temas técnicos (taxonomia do café) · Temas automáticos (BERTopic do Observatório, contados no
  recorte) · Programação · Documentos.
- Filtros globais na barra lateral (período, espécie, "só a espécie dita no texto", grupo de temas, tema) valem
  para **todas** as páginas: as tabelas por documento são sombreadas por views temporárias (`app/lib/dados.py`).

## Como rodar

```
# 1. no Observatório: pipeline do café gera o recorte (alvo arq_recorte)
#    (pasta "observatorio de P&D Embrapa/Cafe", PowerShell) targets::tar_make()
# 2. aqui: monta o banco
Rscript pipeline/montar_banco.R
# 3. app
streamlit run app/app.py
# testes (todas as páginas, com e sem filtro)
python -m pytest tests -q
```

Visual: cores da identidade da Embrapa Café (sem marca), em `app/lib/ui.py::estilo_cafe` e `.streamlit/config.toml`.

## Privacidade

O banco (`data/observatorio_cafe.duckdb`) tem a base de pessoas e o gênero inferido de cada pessoa
identificada; **nunca vai para o git** e é publicado só numa release de repositório privado. O app mostra gênero
apenas em números agregados e nunca ao lado de um nome.

## Publicação

- Código (público): https://github.com/danimaciel/observatorio_cafe
- Dados (privado): https://github.com/danimaciel/observatorio_cafe_dados — Releases `dados-AAAA-MM` com
  `observatorio_cafe.duckdb`.
- App no Streamlit Community Cloud: arquivo principal `app/app.py`; secrets:

```toml
[dados]
repo = "danimaciel/observatorio_cafe_dados"
tag = "dados-2026-10"
arquivo = "observatorio_cafe.duckdb"
token = "<token fine-grained com leitura de Contents no repositório de dados>"
```

Vitrine estática: https://danimaciel.github.io/observatorio-cafe/ (repositório danimaciel/observatorio-cafe).
