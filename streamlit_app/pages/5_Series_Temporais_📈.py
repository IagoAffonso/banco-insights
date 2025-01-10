import streamlit as st
import requests
import plotly.io as pio
import pandas as pd
import os

@st.cache_data
def load_institutions():
    """Load and cache the institutions list"""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "..", "data", "institutions_name_list.csv")
    df = pd.read_csv(file_path)
    return df['NomeInstituicao'].tolist()

@st.cache_data
def load_metrics():
    """Load and cache the metrics list"""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "..", "data", "metric_names.csv")
    df = pd.read_csv(file_path, escapechar='\\')
    return df['metric_name'].tolist()


def main():
    st.title("Séries Temporais 📈")
    st.markdown("""
    ### Análise de Séries Temporais de Dados Financeiros Bancários
    Compare métricas financeiras entre diferentes instituições ao longo do tempo.
    """)

    # Load institutions list
    institutions_list = load_institutions()

    # Load metrics list
    metrics_list = load_metrics()

    # Sidebar controls
    with st.sidebar:
        st.header("Configurações da Análise")

        # Select visualization type
        control = st.radio(
            "Tipo de Visualização:",
            options=[
                "Valores Absolutos",
                "Valores Relativos por % da Receita Operacional",
                "Valores Relativos por Cliente"
            ],
            help="Escolha como você quer visualizar os dados"
        )

        # Select metric with autocomplete
        metric_name = st.selectbox(
            "Métrica:",
            options=metrics_list,
            help="Selecione a métrica financeira para análise",
            index=23,
            placeholder="Digite para buscar..."
        )

        # Date range selection
        st.subheader("Período de Análise")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Data Inicial",
                value=pd.to_datetime("2020-01-01"),
                min_value=pd.to_datetime("2014-01-01"),
                max_value=pd.to_datetime("2024-12-31"),
                help="Selecione a data inicial para análise"
            )
        with col2:
            end_date = st.date_input(
                "Data Final",
                value=pd.to_datetime("2024-12-31"),
                min_value=pd.to_datetime("2014-01-01"),
                max_value=pd.to_datetime("2024-12-31"),
                help="Selecione a data final para análise"
            )

        # Institution selection
        st.subheader("Seleção de Instituições")
        selected_institutions = st.multiselect(
            "Selecione as Instituições:",
            options=institutions_list,
            default=["ITAU", "BRADESCO", "SANTANDER", "NUBANK"],
            help="Escolha as instituições para comparação",
            placeholder="Digite para buscar..."
        )

        # Show selected institutions count
        if selected_institutions:
            st.info(f"✓ {len(selected_institutions)} instituições selecionadas")

    # Main content area
    if not selected_institutions:
        st.warning("⚠️ Por favor, selecione pelo menos uma instituição para análise.")
        return

    try:
        # Call the API
        params = {
            "control": control,
            "list_institutions": selected_institutions,
            "metric_name": metric_name,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }

        response = requests.get(
            "https://bacen-api-522706975081.europe-west1.run.app/plot/time_series",
            params=params
        )

        if response.status_code == 200:
            fig_json = response.json()["figure_json"]
            fig = pio.from_json(fig_json)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Erro na API: {response.status_code}")
            st.error("Detalhes do erro:")
            try:
                error_details = response.json()
                st.json(error_details)
            except:
                st.error(response.text)

    except Exception as e:
        st.error(f"Erro ao conectar com a API: {str(e)}")
        st.error(f"Erro completo: {e.__class__.__name__}: {str(e)}")

    # Add explanatory text
    with st.expander("ℹ️ Sobre esta análise"):
        st.markdown("""
        ### Interpretação do Gráfico
        - O gráfico mostra a evolução temporal das métricas selecionadas para cada instituição
        - Permite comparação direta entre diferentes instituições
        - Disponível em três formatos:
          - **Valores Absolutos**: Valores nominais das métricas
          - **Valores Relativos por % da Receita Operacional**: Métricas como percentual da receita
          - **Valores Relativos por Cliente**: Métricas por cliente da instituição

        ### Notas Metodológicas
        - Dados fonte: Bacen (IF.data)
        - Frequência: Trimestral
        - Período disponível: 2014 - presente
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Séries Temporais",
        page_icon="📈",
        layout="wide"
    )
    main()
