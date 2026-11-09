"""Observatório do Café — ponto de entrada.

O Observatório de Pesquisa da Embrapa recortado para o café (arábica e canéfora), com leituras por espécie,
tema técnico e participação de mulheres. Executar na raiz do projeto:  streamlit run app/app.py
"""

import streamlit as st

from lib import cf, dados, ui

st.set_page_config(page_title="Observatório do Café", page_icon=":material/coffee:", layout="wide")
ui.estilo_cafe()

paginas = {
    "Café": [
        st.Page("paginas/centro.py", title="Visão geral", icon=":material/coffee:", url_path="visao", default=True),
        st.Page("paginas/tendencias.py", title="Tendências", icon=":material/trending_up:", url_path="tendencias"),
        st.Page("paginas/lacunas.py", title="Lacunas", icon=":material/grid_view:", url_path="lacunas"),
        st.Page("paginas/genero.py", title="Mulheres na pesquisa", icon=":material/diversity_3:", url_path="genero"),
    ],
    "Quem faz": [
        st.Page("paginas/embrapa.py", title="Produção e colaboração", icon=":material/account_balance:",
                url_path="embrapa"),
        st.Page("paginas/unidades.py", title="Unidades", icon=":material/apartment:", url_path="unidades"),
        st.Page("paginas/redes.py", title="Redes", icon=":material/hub:", url_path="redes"),
        st.Page("paginas/mapa.py", title="Mapa", icon=":material/map:", url_path="mapa"),
        st.Page("paginas/pesquisadores.py", title="Pesquisadores", icon=":material/person_search:",
                url_path="pesquisadores"),
    ],
    "Conteúdo": [
        st.Page("paginas/temas_cafe.py", title="Temas técnicos", icon=":material/eco:", url_path="temas_tecnicos"),
        st.Page("paginas/temas.py", title="Temas automáticos", icon=":material/category:", url_path="temas"),
        st.Page("paginas/programacao.py", title="Programação", icon=":material/flag:", url_path="programacao"),
        st.Page("paginas/documentos.py", title="Documentos", icon=":material/description:", url_path="documentos"),
    ],
    "Sobre": [
        st.Page("paginas/metodologia.py", title="Metodologia", icon=":material/menu_book:", url_path="metodologia"),
    ],
}
pg = st.navigation(paginas)

with st.sidebar:
    st.markdown('<div class="cf-marca"><span>Observatório</span>do Café</div>', unsafe_allow_html=True)
    st.caption("Pesquisa da Embrapa sobre café arábica e canéfora")
    a0, a1 = dados.faixa_anos()
    if "periodo" not in st.session_state:
        st.session_state["periodo"] = (a0, a1)   # período completo: mesmos números do funil e do site
    st.slider("Período", min_value=a0, max_value=a1, key="periodo",
              help="Projetos pelo ano de início; publicações e tecnologias pelo ano.")
    st.markdown("**Recorte**")
    st.multiselect("Espécie", list(cf.ESPECIES), key="f_especie", format_func=cf.ESPECIES.get, placeholder="Todas")
    st.toggle("Só a espécie dita no texto", key="f_so_texto",
              help="Desligado: inclui a espécie inferida pelo estado do estudo (PAM/IBGE) ou pela unidade. "
                   "Ligado: a espécie inferida conta como “não especificada”.")
    g = cf.grupos()
    st.multiselect("Grupo de temas", g.no_id.tolist(), key="f_grupo", format_func=cf.rotulo, placeholder="Todos")
    t = cf.temas().sort_values("rotulo_pt")
    st.multiselect("Tema técnico", t.no_id.tolist(), key="f_tema", format_func=cf.rotulo, placeholder="Todos")
    if dados.chave_filtro():
        st.caption("Os filtros valem para todas as páginas.")
    m = dados.meta()
    st.caption(f"Dados: exportação {m['exportacao']} · recorte gerado em {m['gerado_em']}")

pg.run()
