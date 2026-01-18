import streamlit as st
import pandas as pd
import plotly as px
import unicodedata

st.set_page_config(
    page_title="Dashboard END",
    layout="wide"
)

# =====================================================
# BOTÃO DE ATUALIZAÇÃO DE DADOS
# =====================================================
if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.sidebar.success("Dados atualizados com sucesso!")

# =====================================================
# FUNÇÃO PARA NORMALIZAR NOMES DE COLUNAS
# =====================================================
def normalizar_colunas(df):
    df = df.copy()
    novas_cols = []
    for col in df.columns:
        col_norm = (
            unicodedata.normalize("NFKD", col)
            .encode("ASCII", "ignore")
            .decode("utf-8")
            .upper()
            .strip()
            .replace(" ", "_")
        )
        novas_cols.append(col_norm)
    df.columns = novas_cols
    return df

# =====================================================
# CARGA DOS DADOS
# =====================================================
@st.cache_data
def carregar_dados():
    planejado = pd.read_excel(
        "dados/dados.planejado.xlsx",
        engine="openpyxl"
    )
    realizado = pd.read_excel(
        "dados/dados.realizado.xlsx",
        engine="openpyxl"
    )

    planejado = normalizar_colunas(planejado)
    realizado = normalizar_colunas(realizado)

    return planejado, realizado


planejado, realizado = carregar_dados()

# =====================================================
# SIDEBAR – NAVEGAÇÃO
# =====================================================
pagina = st.sidebar.radio(
    "📄 Navegação",
    [
        "Resumo END",
        "Detalhamento END",
        "Condições Físicas"
    ]
)

# =====================================================
# FILTROS GLOBAIS
# =====================================================
st.sidebar.header("🔎 Filtros")

lista_un = sorted(planejado["UN"].dropna().astype(str).unique())
lista_un = [un for un in lista_un if un != "82"]

lista_tipo = sorted(planejado["TIPO"].dropna().astype(str).unique())
lista_tag = sorted(planejado["TAG"].dropna().astype(str).unique())
lista_zr = sorted(planejado["NOTA_ZR"].dropna().astype(str).unique())
lista_servico = sorted(planejado["SERVICO"].dropna().astype(str).unique())

filtro_un = st.sidebar.multiselect("UNIDADE REPLAN", lista_un, default=lista_un)
filtro_tipo = st.sidebar.multiselect("Tipo de Permutador", lista_tipo, default=lista_tipo)
filtro_tag = st.sidebar.multiselect("TAG PERMUTADOR", lista_tag, default=lista_tag)
filtro_zr = st.sidebar.multiselect("NOTA ZR", lista_zr, default=lista_zr)
filtro_servico = st.sidebar.multiselect("SERVIÇO", lista_servico, default=lista_servico)

# =====================================================
# APLICAÇÃO DOS FILTROS
# =====================================================
planejado_f = planejado[
    (planejado["UN"].astype(str).isin(filtro_un)) &
    (planejado["TIPO"].astype(str).isin(filtro_tipo)) &
    (planejado["TAG"].astype(str).isin(filtro_tag)) &
    (planejado["NOTA_ZR"].astype(str).isin(filtro_zr)) &
    (planejado["SERVICO"].astype(str).isin(filtro_servico))
]

realizado_f = realizado[
    realizado["TAG"].isin(planejado_f["TAG"])
]

# =====================================================
# ENSAIOS END
# =====================================================
ensaios = {
    "ME": ("ME", "ME_REAL"),
    "LP": ("LP", "LP_REAL"),
    "US": ("US", "US_REAL"),
    "PM": ("PM", "PM_REAL"),
    "IRIS": ("QUANT_IRIS", "IRIS_REAL"),
    "Réplica": ("REPLICA_METALOGRAFICA", "REPLICA_METALOGRAFICA"),
    "Corrente Parasita": ("QUANT_CP", "CP_REAL"),
}

# =====================================================
# PÁGINA 1 – RESUMO END
# =====================================================
if pagina == "Resumo END":
    st.title("📊 Resumo Geral – END")

    colunas = st.columns(len(ensaios))
    dados_rosca = []

    for i, (ensaio, (col_p, col_r)) in enumerate(ensaios.items()):
        plan = planejado_f[col_p].fillna(0).sum()
        real = realizado_f[col_r].fillna(0).sum()

        colunas[i].metric(ensaio, int(plan), delta=int(real))

        dados_rosca.append({"Status": "Planejado", "Quantidade": plan})
        dados_rosca.append({"Status": "Realizado", "Quantidade": real})

    df_rosca = pd.DataFrame(dados_rosca)

    fig = px.pie(
        df_rosca,
        names="Status",
        values="Quantidade",
        hole=0.5,
        title="Planejado × Realizado – END"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Matriz END – Serviços Planejados")

    matriz_end = planejado_f[
        ["UN", "TAG", "NOTA_ZR", "SERVICO"]
    ].drop_duplicates()

    st.dataframe(matriz_end.sort_values(["UN", "TAG"]), use_container_width=True)

# =====================================================
# PÁGINA 2 – DETALHAMENTO END
# =====================================================
if pagina == "Detalhamento END":
    st.title("🧾 Detalhamento – END")

    cols = st.columns(3)
    cols2 = st.columns(3)
    cols3 = st.columns(1)
    grid = cols + cols2 + cols3

    for i, (ensaio, (col_p, col_r)) in enumerate(ensaios.items()):
        plan = planejado_f[col_p].fillna(0).sum()
        real = realizado_f[col_r].fillna(0).sum()

        df_graf = pd.DataFrame({
            "Status": ["Planejado", "Realizado"],
            "Quantidade": [plan, real]
        })

        fig = px.pie(df_graf, names="Status", values="Quantidade", hole=0.55, title=ensaio)
        grid[i].plotly_chart(fig, use_container_width=True)

# =====================================================
# PÁGINA 3 – CONDIÇÕES FÍSICAS
# =====================================================
if pagina == "Condições Físicas":
    st.title("🧩 Condições Físicas")

    col_kpi = st.columns(3)

    subst_prev = planejado_f["SUBST_FEIXE"].fillna(0).sum()
    subst_real = realizado_f["SUBST_FEIXE_REAL"].fillna(0).sum()

    usin_prev = planejado_f["USINAGEM"].fillna(0).sum()
    usin_real = realizado_f["USINAGEM_REAL"].fillna(0).sum()

    retub_prev = (planejado_f["RETUB"].fillna(0) > 0).sum()
    retub_real = (realizado_f["RETUB_REAL"].fillna(0) > 0).sum()

    col_kpi[0].metric("Substituição do Feixe", int(subst_prev), delta=int(subst_real))
    col_kpi[1].metric("Usinagem", int(usin_prev), delta=int(usin_real))
    col_kpi[2].metric("Retubagem", int(retub_prev), delta=int(retub_real))

    st.subheader("📋 Matriz – Condições Físicas")

    matriz_cf = planejado_f[
        ["UN", "TAG", "NOTA_ZR", "SERVICO"]
    ].drop_duplicates()

    st.dataframe(matriz_cf.sort_values(["UN", "TAG"]), use_container_width=True)

