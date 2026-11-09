"""Facetas do café (tabelas cf_* do banco): rótulos, cores e consultas comuns."""

import pandas as pd
import streamlit as st

from lib import dados
from lib.dados import q

ESPECIES = {"arabica": "Arábica", "canefora": "Canéfora", "ambas": "As duas", "nao_especificada": "Não especificada"}
NIVEIS_ESP = {"1_texto": "nome no texto", "2_cultivar": "cultivar citada", "3_estado": "inferida pelo estado",
              "4_unidade": "inferida pela unidade", "nao_especificada": "—"}
# cores da identidade visual da Embrapa Café
COR = {"azul": "#122840", "verde": "#1B5C4A", "ouro": "#BF9859", "marrom": "#4A3728", "creme": "#FAF7F0",
       "canefora": "#8A5A2B", "cinza": "#A9A39A"}
CORES_ESP = {"Arábica": COR["verde"], "Canéfora": COR["canefora"], "As duas": COR["ouro"], "Não especificada": COR["cinza"]}
CORES_GRUPO = ["#1B5C4A", "#8A5A2B", "#BF9859", "#122840", "#6E8B3D", "#7A4E9C", "#5B6B61"]
CORES_GENERO = {"Mulheres": COR["verde"], "Homens": COR["ouro"]}
MIN_PESSOAS = 10   # abaixo disso, a página de gênero não mostra a proporção (evita identificar pessoas)


@st.cache_data(show_spinner=False)
def taxonomia() -> pd.DataFrame:
    return dados.conexao().cursor().execute("select * from cf_taxonomia").df()


def rotulo(no_id: str) -> str:
    t = taxonomia().set_index("no_id")
    return str(t.rotulo_pt.get(no_id, no_id))


def grupos() -> pd.DataFrame:
    t = taxonomia()
    return t[(t.faceta == "grupo") & (t.nivel.astype(str) != "0")][["no_id", "rotulo_pt"]].reset_index(drop=True)


def temas() -> pd.DataFrame:
    t = taxonomia()
    return t[(t.faceta == "tema") & (t.nivel.astype(str) != "0")][["no_id", "rotulo_pt", "grupo", "descricao_pt"]]


def rotulo_grupo(no_id: str) -> str:
    return rotulo(no_id)


def cores_grupos() -> dict:
    return {r: CORES_GRUPO[i % len(CORES_GRUPO)] for i, r in enumerate(grupos().rotulo_pt)}


def so_texto() -> bool:
    return bool(st.session_state.get("f_so_texto"))


def docs_facetas(a0: int, a1: int) -> pd.DataFrame:
    """Um registro por documento do recorte (respeita o filtro global), com facetas do café.
    `especie_vis` segue a opção "só o que o texto diz": nela, a espécie inferida vira "não especificada"."""
    d = q("""select d.doc_uid, d.tipo_doc, d.ano, d.ano_fim, d.unidade_id, d.titulo, f.especie, f.especie_nivel,
                    f.especie_inferida, f.temas, f.grupos
             from documento d join cf_doc f using (doc_uid) where d.ano between ? and ?""", (a0, a1))
    d["especie_vis"] = d.especie.where(~(d.especie_inferida & so_texto()), "nao_especificada")
    d["especie_rot"] = d.especie_vis.map(ESPECIES)
    return d


def explode(d: pd.DataFrame, col: str, prefixo: str) -> pd.DataFrame:
    """Uma linha por documento × item (temas ou grupos, separados por "+"), com o rótulo em `item`."""
    x = d.dropna(subset=[col])
    x = x[x[col] != ""]
    x = x.assign(**{col: x[col].str.split("+")}).explode(col)
    return x.assign(item=(prefixo + x[col]).map(rotulo))


def doc_estado(doc_uids) -> pd.DataFrame:
    return q("select doc_uid, uf from doc_estado where list_contains(?, doc_uid)", (list(doc_uids),))
