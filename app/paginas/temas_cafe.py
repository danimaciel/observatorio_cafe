import pandas as pd
import plotly.express as px
import streamlit as st

from lib import cf, dados, ui
from lib.dados import q

a0, a1 = dados.periodo()
st.title("Temas técnicos")
st.caption(f"19 temas da taxonomia do café, em 5 grupos ao longo da cadeia · {a0}–{a1}")

temas = cf.temas()
d = cf.docs_facetas(a0, a1)
b = cf.explode(d, "temas", "TEM.")
b["no_id"] = "TEM." + b.temas
b = b.merge(temas[["no_id", "grupo"]], on="no_id")
b["grupo_rot"] = b.grupo.map(cf.rotulo)

s = b.groupby(["item", "grupo_rot", "tipo_doc"]).doc_uid.nunique().reset_index(name="n")
s["tipo"] = s.tipo_doc.map(dados.TIPOS)
ordem = s.groupby("item").n.sum().sort_values(ascending=False).index.tolist()
fig = px.bar(s, y="item", x="n", color="tipo", orientation="h", category_orders={"item": ordem},
             color_discrete_map={dados.TIPOS[k]: v for k, v in dados.CORES_TIPO.items()},
             hover_data={"grupo_rot": True}, height=560,
             labels={"n": "Documentos", "item": "", "tipo": "", "grupo_rot": "Grupo de temas"})
st.plotly_chart(fig, width="stretch")
st.caption("Tema atribuído por termos da taxonomia (no título ou palavras-chave, ou repetidos no texto, ou "
           "confirmados pelos documentos rotulados mais próximos); nos documentos da amostra, pelo rótulo. "
           "Um documento pode ter mais de um tema. Acerto médio provisório: F1 0,63 (veja **Metodologia**).")

sel = st.selectbox("Escolha um tema para ver o detalhe", ordem, index=None, placeholder="Tema técnico")
if sel:
    info = temas.set_index("rotulo_pt").loc[sel]
    sub = b[b.item == sel]
    st.subheader(sel)
    st.caption(f"Grupo: **{cf.rotulo(info.grupo)}**" + (f" · {info.descricao_pt}" if isinstance(info.descricao_pt, str) else ""))
    u1 = sub.drop_duplicates("doc_uid")
    cont = u1.tipo_doc.value_counts()
    ui.kpis([("Projetos", int(cont.get("projeto", 0))), ("Publicações", int(cont.get("publicacao", 0))),
             ("Soluções tecnológicas", int(cont.get("tecnologia", 0))), ("Unidades", int(sub.unidade_id.nunique()))])
    t1, t2, t3, t4 = st.tabs(["Evolução", "Espécies", "Unidades", "Documentos"])
    with t1:
        e = u1.groupby(["ano", "tipo_doc"]).size().reset_index(name="n")
        e["tipo"] = e.tipo_doc.map(dados.TIPOS)
        st.plotly_chart(px.bar(e, x="ano", y="n", color="tipo",
                               color_discrete_map={dados.TIPOS[k]: v for k, v in dados.CORES_TIPO.items()},
                               labels={"ano": "Ano", "n": "Documentos", "tipo": ""}), width="stretch")
    with t2:
        e = u1.especie_rot.value_counts().reindex(list(cf.ESPECIES.values())).fillna(0).reset_index()
        e.columns = ["especie", "n"]
        st.plotly_chart(px.bar(e, x="especie", y="n", color="especie", color_discrete_map=cf.CORES_ESP,
                               labels={"especie": "", "n": "Documentos"}).update_layout(showlegend=False),
                        width="stretch")
    with t3:
        u = u1.groupby("unidade_id").size().reset_index(name="n")
        u["unidade"] = u.unidade_id.map(dados.rotulo_unidade)
        ui.tabela_navegavel(u.sort_values("n", ascending=False)[["unidade_id", "unidade", "n"]], "unidade",
                            "unidade_id", "tcf_unid", altura=360, colunas={"unidade": "Unidade", "n": "Documentos"})
    with t4:
        docs = u1.sort_values("ano", ascending=False).assign(tipo=lambda x: x.tipo_doc.map(dados.TIPOS),
                                                            unidade=lambda x: x.unidade_id.map(dados.rotulo_unidade))
        ui.tabela_navegavel(docs[["doc_uid", "tipo", "ano", "titulo", "especie_rot", "unidade"]], "doc", "doc_uid",
                            "tcf_docs", altura=420, colunas={"tipo": "Tipo", "ano": "Ano", "titulo": "Título",
                                                             "especie_rot": "Espécie", "unidade": "Unidade"})
