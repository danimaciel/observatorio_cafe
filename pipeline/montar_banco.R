# Monta data/observatorio_cafe.duckdb: o banco do Observatório de Pesquisa da Embrapa recortado para o café.
#
# Entradas (pasta-irmã "observatorio de P&D Embrapa", só leitura):
#   data/processed/observatorio_app.duckdb      banco do app do Observatório
#   Cafe/data/recorte/recorte_docs.parquet      acervo do café e facetas (alvo arq_recorte do pipeline do café)
#   Cafe/ref/taxonomia_v1.csv                   taxonomia (espécies, cultivares, temas, grupos de temas)
#
# Uso (de dentro desta pasta):  Rscript pipeline/montar_banco.R
# O banco tem o MESMO esquema do Observatório (as páginas herdadas funcionam sem mudança), só com os documentos
# do acervo do café, mais tabelas cf_* com as facetas do café.
#
# Gênero: cf_pessoa_genero guarda o gênero inferido do primeiro nome (genderBR 1.4.0, IBGE Censo 2010, limiar
# 0,9) das pessoas identificadas. O banco é privado (release de repositório privado); o app só mostra números
# agregados, com supressão de grupos pequenos, e nunca o gênero ao lado de um nome.

OBS <- normalizePath(file.path("..", "observatorio de P&D Embrapa"), winslash = "/", mustWork = TRUE)
CAFE <- file.path(OBS, "Cafe")
ORIGEM <- file.path(OBS, "data", "processed", "observatorio_app.duckdb")
DESTINO <- file.path("data", "observatorio_cafe.duckdb")
REC <- file.path(CAFE, "data", "recorte")

dir.create("data", showWarnings = FALSE)
if (file.exists(DESTINO)) file.remove(DESTINO)
con <- DBI::dbConnect(duckdb::duckdb(DESTINO, shared_home = FALSE))
on.exit(DBI::dbDisconnect(con, shutdown = TRUE))
ex <- function(sql) invisible(DBI::dbExecute(con, sql))
ex(sprintf("attach '%s' as src (read_only)", ORIGEM))

# --- recorte e facetas -------------------------------------------------------------------------------
ex(sprintf("create table cf_doc as select * from read_parquet('%s/recorte_docs.parquet')", REC))
tax <- readr::read_csv(file.path(CAFE, "ref", "taxonomia_v1.csv"), show_col_types = FALSE,
                       col_types = readr::cols(.default = "c"))
DBI::dbWriteTable(con, "cf_taxonomia", as.data.frame(tax))
ex("create table cf_doc_tema as
    select doc_uid, 'TEM.' || unnest(string_split(temas, '+')) tema from cf_doc where temas is not null and temas <> ''")
ex("create table cf_doc_grupo as
    select doc_uid, 'GRP.' || unnest(string_split(grupos, '+')) grupo from cf_doc where grupos is not null and grupos <> ''")
# tema principal e grupo por documento (um registro por documento, como doc_tema do Observatório)
ex("create table cf_tema_grupo as
    select f.doc_uid, 'TEM.' || split_part(f.temas, '+', 1) tema_id, t.grupo macro_id
    from cf_doc f left join cf_taxonomia t on t.no_id = 'TEM.' || split_part(f.temas, '+', 1)
    where f.temas is not null and f.temas <> ''")

# --- tabelas do Observatório, recortadas ----------------------------------------------------------------
por_doc <- c("documento", "documento_unidade", "documento_pessoa", "doc_pessoa", "doc_tema", "doc_bioma",
             "doc_estado", "doc_municipio", "doc_desafio", "documento_keyword", "aresta_unidade",
             "aresta_pessoa", "publicacao")
for (t in por_doc)
  ex(sprintf("create table %s as select * from src.%s where doc_uid in (select doc_uid from cf_doc)", t, t))
ex("create table similaridade as select * from src.similaridade
    where origem_uid in (select doc_uid from cf_doc) and destino_uid in (select doc_uid from cf_doc)")
ex("create table doc_link as select * from src.doc_link where origem_uid in (select doc_uid from cf_doc)")
ex("create table pessoa_tecnologia as select * from src.pessoa_tecnologia
    where tecnologia_uid in (select doc_uid from cf_doc)")
ex("create table pessoa as
    select p.* exclude (n_obras, n_projetos_lider),
           coalesce(o.n_obras, 0) n_obras, coalesce(o.n_projetos_lider, 0) n_projetos_lider
    from src.pessoa p join (
      select dp.pessoa_id,
             count(distinct case when d.tipo_doc <> 'projeto' then dp.doc_uid end) n_obras,
             count(distinct case when d.tipo_doc = 'projeto' and dp.papel ilike '%lider%' then dp.doc_uid end) n_projetos_lider
      from documento_pessoa dp join documento d using (doc_uid) group by 1) o using (pessoa_id)")
ex("create table tema as
    with n as (select t.tema_id, d.tipo_doc, count(*) n from doc_tema t join documento d using (doc_uid) group by all),
         m as (select t.macro_id tema_id, d.tipo_doc, count(*) n from doc_tema t join documento d using (doc_uid) group by all),
         c as (select tema_id,
                      sum(n) filter (where tipo_doc = 'projeto') n_projeto,
                      sum(n) filter (where tipo_doc = 'publicacao') n_publicacao,
                      sum(n) filter (where tipo_doc = 'tecnologia') n_tecnologia
               from (select * from n union all select * from m) group by 1)
    select s.* exclude (n_projeto, n_publicacao, n_tecnologia),
           coalesce(c.n_projeto, 0) n_projeto, coalesce(c.n_publicacao, 0) n_publicacao,
           coalesce(c.n_tecnologia, 0) n_tecnologia
    from src.tema s join c using (tema_id)")
for (t in c("desafio", "unidade", "unidade_localizacao", "municipio_centroide", "proximidade_unidade"))
  ex(sprintf("create table %s as select * from src.%s", t, t))

# --- gênero inferido das pessoas identificadas (uso só em agregados) -----------------------------------
pes <- DBI::dbGetQuery(con, "select pessoa_id, nome_exibicao from pessoa")
g <- genderBR::get_gender(pes$nome_exibicao)
pes$genero <- ifelse(g %in% "Female", "mulher", ifelse(g %in% "Male", "homem", "indefinido"))
DBI::dbWriteTable(con, "cf_pessoa_genero", pes[, c("pessoa_id", "genero")])

ex(sprintf("create table meta as select exportacao, '%s' gerado_em, arquivos_truncados,
            'Café (arábica e canéfora)' recorte from src.meta", format(Sys.time(), "%Y-%m-%d")))
ex("detach src")
ex("checkpoint")

print(DBI::dbGetQuery(con, "select d.tipo_doc, f.especie, count(*) n from cf_doc f join documento d using (doc_uid)
                            group by all order by all"))
print(DBI::dbGetQuery(con, "select genero, count(*) n from cf_pessoa_genero group by 1"))
