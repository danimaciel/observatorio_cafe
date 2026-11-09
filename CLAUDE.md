# Observatório do Café (app Streamlit) — instruções para o Claude

App no molde do Observatório das Florestas (`../observatorio_florestas`) e do Observatório de Pesquisa da Embrapa.
O método, a taxonomia, os números e o estado do projeto ficam na pasta `../observatorio de P&D Embrapa/Cafe`
(leia `Cafe/CLAUDE.md` e `Cafe/estado.md` primeiro).

- Fluxo: pipeline do café (`Cafe/_targets.R`, alvo `arq_recorte`) → `Rscript pipeline/montar_banco.R` → app.
- Testes: `python -m pytest tests -q` (14 páginas × 3 filtros). Launch "observatorio-cafe", porta 8507.
- Tabelas próprias `cf_*`; filtros globais em `app/lib/dados.py` (FILTROS, `_sql_filtro`); facetas em `app/lib/cf.py`.
- Gênero: `cf_pessoa_genero` só no banco privado; o app mostra só agregados (mínimo de 10 pessoas por grupo,
  `cf.MIN_PESSOAS`) e nunca ao lado de nomes.
- `data/` e `*.duckdb` nunca vão para o git (LGPD). Publicação: código público + banco em release privada +
  Streamlit Cloud (token e secrets feitos pela usuária; perguntar antes se já foram feitos).
