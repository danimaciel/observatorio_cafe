import pandas as pd
import plotly.express as px
import streamlit as st

from lib import cf, dados, ui
from lib.dados import q

a0, a1 = dados.periodo()
st.title("O café na pesquisa da Embrapa")
st.caption(f"Publicações, projetos e soluções tecnológicas sobre café arábica e canéfora · {a0}–{a1}")

d = cf.docs_facetas(a0, a1)
pesq = q("""select count(distinct dp.pessoa_id) n from documento_pessoa dp join documento d using (doc_uid)
            where d.ano between ? and ?""", (a0, a1)).n[0]
ui.kpis([
    ("Projetos", int((d.tipo_doc == "projeto").sum())),
    ("Publicações", int((d.tipo_doc == "publicacao").sum())),
    ("Soluções tecnológicas", int((d.tipo_doc == "tecnologia").sum())),
    ("Pesquisadores com produção", int(pesq)),
    ("Unidades envolvidas", int(d.unidade_id.nunique())),
])
inf = 0 if cf.so_texto() else int(d.especie_inferida.sum())
st.caption(f"Acervo do café (busca por termos e por significado + classificador conferido numa amostra). "
           f"{inf:,} documentos têm espécie inferida; ligue “Só a espécie dita no texto” na barra lateral para "
           "vê-los como “não especificada”.".replace(",", "."))

ordem_esp = list(cf.ESPECIES.values())
t1, t2, t3, t4 = st.tabs(["Espécies", "Ao longo do tempo", "Temas técnicos", "Estados"])

with t1:
    s = d.groupby(["especie_rot", "tipo_doc"]).size().reset_index(name="n")
    s["tipo"] = s.tipo_doc.map(dados.TIPOS)
    fig = px.bar(s, y="especie_rot", x="n", color="tipo", orientation="h", category_orders={"especie_rot": ordem_esp},
                 color_discrete_map={dados.TIPOS[k]: v for k, v in dados.CORES_TIPO.items()},
                 labels={"n": "Documentos", "especie_rot": "", "tipo": ""}, height=320)
    st.plotly_chart(fig, width="stretch")
    niv = d.groupby(["especie_rot", "especie_nivel"]).size().unstack(fill_value=0).reindex(ordem_esp).fillna(0).astype(int)
    niv = niv.rename(columns=cf.NIVEIS_ESP)
    st.markdown("**De onde vem a espécie**")
    st.dataframe(niv, width="stretch")
    st.caption("Espécie pelo nome (ou nome científico) no texto, pela cultivar citada, ou inferida pelo estado do estudo "
               "(estados com ≥ 90% da produção de uma espécie na PAM/IBGE 2022–2024) ou pela unidade (≥ 30 documentos "
               "com espécie no texto, ≥ 90% de uma espécie). Proposta metodológica, em validação.")

with t2:
    s = d[d.ano >= 1975].groupby(["ano", "especie_rot"]).size().reset_index(name="n")
    fig = px.bar(s, x="ano", y="n", color="especie_rot", category_orders={"especie_rot": ordem_esp},
                 color_discrete_map=cf.CORES_ESP, labels={"ano": "Ano", "n": "Documentos", "especie_rot": ""})
    fig.update_layout(legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, width="stretch")
    st.caption("A partir de 1975. Projetos pelo ano de início. Os anos mais recentes ainda estão incompletos "
               "(publicações demoram a ser depositadas). Para o que cresce e o que cai, veja **Tendências**.")

with t3:
    x = cf.explode(d, "temas", "TEM.")
    s = x.groupby(["item", "especie_rot"]).doc_uid.nunique().reset_index(name="n")
    ordem = s.groupby("item").n.sum().sort_values(ascending=False).index.tolist()
    fig = px.bar(s, y="item", x="n", color="especie_rot", orientation="h",
                 category_orders={"item": ordem, "especie_rot": ordem_esp}, color_discrete_map=cf.CORES_ESP,
                 labels={"n": "Documentos", "item": "", "especie_rot": ""}, height=560)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Um documento pode ter mais de um tema; {int((d.temas.fillna('') == '').sum()):,} documentos ficaram "
               "sem tema. Temas provisórios, em validação (veja **Temas técnicos** e **Metodologia**).".replace(",", "."))

with t4:
    e = cf.doc_estado(tuple(d.doc_uid)).merge(d[["doc_uid", "especie_rot"]], on="doc_uid")
    s = e.groupby(["uf", "especie_rot"]).doc_uid.nunique().reset_index(name="n")
    ordem = s.groupby("uf").n.sum().sort_values(ascending=False).index.tolist()[:20]
    fig = px.bar(s[s.uf.isin(ordem)], x="uf", y="n", color="especie_rot",
                 category_orders={"uf": ordem, "especie_rot": ordem_esp}, color_discrete_map=cf.CORES_ESP,
                 labels={"uf": "", "n": "Documentos", "especie_rot": ""})
    st.plotly_chart(fig, width="stretch")
    sem = len(d) - e.doc_uid.nunique()
    st.caption(f"Estado citado no texto ou de município citado (20 estados com mais documentos). {sem:,} documentos "
               f"({100 * sem / max(len(d), 1):.0f}%) não citam estado. Para municípios, veja **Mapa**.".replace(",", "."))
