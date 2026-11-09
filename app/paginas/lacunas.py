import pandas as pd
import plotly.express as px
import streamlit as st

from lib import cf, dados

a0, a1 = dados.periodo()
st.title("Lacunas")
st.caption(f"Onde há pouco conhecimento, ou conhecimento que ainda não virou entrega · {a0}–{a1}")
st.info("Lacuna aqui é **pouca produção registrada** num cruzamento, não necessariamente falta de pesquisa: "
        "parte da produção pode não estar no repositório, e alguns cruzamentos fazem pouco sentido "
        "(ex.: canéfora em estado onde quase só se cultiva arábica).", icon=":material/lightbulb:")

d = cf.docs_facetas(a0, a1)
tm = cf.explode(d, "temas", "TEM.")
ESCALA = [cf.COR["creme"], cf.COR["ouro"], cf.COR["azul"]]
t1, t2, t3 = st.tabs(["Espécie × tema", "Estado × tema", "Pesquisa × entrega"])

with t1:
    m = tm.groupby(["item", "especie_rot"]).doc_uid.nunique().unstack(fill_value=0)
    m = m.reindex(columns=[c for c in cf.ESPECIES.values() if c in m.columns])
    m = m.loc[m.sum(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(m, text_auto=True, aspect="auto", color_continuous_scale=ESCALA,
                    labels={"color": "Documentos", "x": "", "y": ""}, height=200 + 28 * len(m))
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, width="stretch")
    ar, ca = cf.ESPECIES["arabica"], cf.ESPECIES["canefora"]
    if ar in m and ca in m:
        r = pd.DataFrame({"Arábica": m[ar], "Canéfora": m[ca]})
        r["Canéfora por 100 de arábica"] = (100 * r["Canéfora"] / r["Arábica"].where(r["Arábica"] > 0)).round(0)
        st.markdown("**Equilíbrio entre as espécies por tema**")
        st.dataframe(r.sort_values("Canéfora por 100 de arábica"), width="stretch")
        st.caption("Para comparar: a canéfora responde por cerca de 40% da produção brasileira de café (PAM/IBGE "
                   "2022–2024). Temas com poucos documentos de canéfora por 100 de arábica podem indicar lacunas.")

with t2:
    e = cf.doc_estado(tuple(d.doc_uid))
    et = e.merge(tm[["doc_uid", "item"]], on="doc_uid")
    top = e.uf.value_counts().head(12).index
    m = et[et.uf.isin(top)].groupby(["item", "uf"]).doc_uid.nunique().unstack(fill_value=0).reindex(columns=top)
    m = m.loc[m.sum(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(m, text_auto=True, aspect="auto", color_continuous_scale=ESCALA,
                    labels={"color": "Documentos", "x": "", "y": ""}, height=200 + 28 * len(m))
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, width="stretch")
    st.caption("Estado citado no texto ou de município citado (12 estados com mais documentos). Documentos sem "
               "estado no texto ficam de fora.")

with t3:
    st.markdown("**Quanto da pesquisa já virou solução tecnológica?** Por tema e por espécie, "
                "publicações e projetos comparados com soluções tecnológicas.")
    por = st.radio("Por", ["Tema técnico", "Espécie"], horizontal=True)
    base = tm if por == "Tema técnico" else d.assign(item=d.especie_rot)
    t = base.groupby(["item", "tipo_doc"]).doc_uid.nunique().unstack(fill_value=0)
    for c in dados.TIPOS:
        if c not in t:
            t[c] = 0
    t = t[(t.publicacao + t.projeto) >= 10]
    t["publicações por solução"] = (t.publicacao / t.tecnologia.where(t.tecnologia > 0)).round(1)
    t = t.sort_values(["tecnologia", "publicacao"], ascending=[True, False])
    fig = px.scatter(t.reset_index(), x="publicacao", y="tecnologia", size="projeto", text="item",
                     labels={"publicacao": "Publicações", "tecnologia": "Soluções tecnológicas", "projeto": "Projetos"},
                     color_discrete_sequence=[cf.COR["verde"]], height=520, size_max=40)
    fig.update_traces(textposition="top center", textfont_size=10)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(t.rename(columns=dados.TIPOS), width="stretch")
    st.caption("Muita publicação e nenhuma solução pode indicar conhecimento ainda não transformado em entrega "
               "para o produtor — ou soluções que não estão no portal. O tamanho do ponto é o número de projetos.")
