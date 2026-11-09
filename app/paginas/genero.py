import pandas as pd
import plotly.express as px
import streamlit as st

from lib import cf, dados, ui
from lib.dados import q

a0, a1 = dados.periodo()
st.title("Mulheres na pesquisa sobre café")
st.caption(f"Participação de mulheres e homens da Embrapa nas autorias e na liderança de projetos · {a0}–{a1}")
st.info("Só pessoas da Embrapa identificadas pelo Observatório (autores externos chegam nos registros como "
        "“SOBRENOME, I.”). O gênero é **inferido do primeiro nome** (pacote genderBR, base IBGE Censo 2010), "
        "não declarado pela pessoa; nomes ambíguos ficam de fora. A página mostra **só números agregados** e "
        f"omite a proporção de grupos com menos de {cf.MIN_PESSOAS} pessoas com gênero atribuído.",
        icon=":material/info:")

d = cf.docs_facetas(a0, a1)
v = q("""select dp.doc_uid, dp.pessoa_id, dp.papel, g.genero from documento_pessoa dp
         join cf_pessoa_genero g using (pessoa_id) join documento d using (doc_uid) where d.ano between ? and ?""",
      (a0, a1)).merge(d[["doc_uid", "ano", "especie_rot", "temas", "grupos", "tipo_doc"]], on="doc_uid")
if v.empty:
    st.info("Sem pessoas identificadas com os filtros atuais.")
    st.stop()
aut = v[v.papel == "autor"]
G = {"mulher": "Mulheres", "homem": "Homens"}


def resumo(x: pd.DataFrame) -> dict:
    pes = x.drop_duplicates("pessoa_id")
    nm, nh = int((pes.genero == "mulher").sum()), int((pes.genero == "homem").sum())
    am, ah = int((x.genero == "mulher").sum()), int((x.genero == "homem").sum())
    return {"Pessoas (mulheres)": nm, "Pessoas (homens)": nh, "Autorias (mulheres)": am, "Autorias (homens)": ah,
            "% mulheres nas autorias": round(100 * am / (am + ah), 1) if (nm + nh) >= cf.MIN_PESSOAS and (am + ah) else None}


pes = v.drop_duplicates("pessoa_id")
pm, ph, pi = (int((pes.genero == g).sum()) for g in ("mulher", "homem", "indefinido"))
am, ah = int((aut.genero == "mulher").sum()), int((aut.genero == "homem").sum())
lid = v[v.papel == "lider"]
lm, lh = int((lid.genero == "mulher").sum()), int((lid.genero == "homem").sum())
pct = lambda a, b: f"{100 * a / (a + b):.0f}%" if (a + b) and (pm + ph) >= cf.MIN_PESSOAS else "—"
ui.kpis([("Mulheres entre as pessoas", pct(pm, ph)), ("Mulheres nas autorias", pct(am, ah)),
         ("Projetos liderados por mulheres", f"{lm} de {lm + lh}"), ("Pessoas sem gênero atribuído", pi)])


def barras(tab: pd.DataFrame, titulo: str, ordem=None):
    t = tab.dropna(subset=["% mulheres nas autorias"])
    if ordem is not None:
        t = t.reindex([o for o in ordem if o in t.index])
    else:
        t = t.sort_values("% mulheres nas autorias")
    if t.empty:
        st.caption("Grupos pequenos demais para mostrar.")
        return
    long = pd.DataFrame({"item": t.index, "Mulheres": t["% mulheres nas autorias"],
                         "Homens": 100 - t["% mulheres nas autorias"]}).melt("item", var_name="genero", value_name="pct")
    fig = px.bar(long, x="pct", y="item", color="genero", orientation="h", color_discrete_map=cf.CORES_GENERO,
                 labels={"pct": "% das autorias", "item": "", "genero": ""}, height=max(260, 30 * len(t) + 100),
                 category_orders={"item": list(t.index)})
    fig.update_layout(xaxis_range=[0, 100], legend=dict(orientation="h", y=-0.25))
    st.markdown(f"**{titulo}**")
    st.plotly_chart(fig, width="stretch")


t1, t2, t3, t4 = st.tabs(["Por espécie", "Ao longo do tempo", "Por tema", "Tabela"])
por_esp = pd.DataFrame({e: resumo(aut[aut.especie_rot == e]) for e in cf.ESPECIES.values()}).T
aut_per = aut.assign(periodo=pd.cut(aut.ano, [-1, 1999, 2009, 2019, 9999],
                                    labels=["até 1999", "2000–2009", "2010–2019", "2020 em diante"]))
por_per = pd.DataFrame({p: resumo(aut_per[aut_per.periodo == p]) for p in aut_per.periodo.cat.categories}).T
tm = cf.explode(aut, "temas", "TEM.")
por_tema = pd.DataFrame({t: resumo(tm[tm.item == t]) for t in tm.item.unique()}).T
with t1:
    barras(por_esp, "Mulheres nas autorias, por espécie", list(cf.ESPECIES.values()))
    st.caption("A pesquisa com canéfora concentra-se na Embrapa Rondônia; a diferença entre as espécies deve "
               "refletir a composição das equipes (hipótese em verificação).")
with t2:
    barras(por_per, "Mulheres nas autorias, por período", list(por_per.index))
with t3:
    barras(por_tema, "Mulheres nas autorias, por tema técnico")
with t4:
    st.dataframe(pd.concat({"Espécie": por_esp, "Período": por_per, "Tema": por_tema}), width="stretch")
    st.caption("Autoria = par pessoa × documento (uma pessoa conta uma vez por documento). Os filtros da barra "
               "lateral valem aqui.")
