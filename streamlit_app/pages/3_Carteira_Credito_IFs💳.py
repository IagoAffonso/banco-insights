import streamlit as st
import requests
import json
import plotly.io as pio
import pandas as pd
import os

def load_institutions():
    """Load and cache the institutions list"""
    @st.cache_data
    def _load_institutions():
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "institutions_name_list.csv")
        df = pd.read_csv(file_path)
        return df['NomeInstituicao'].tolist()

    return _load_institutions()

def main():
    # Load institutions list
    institutions_list = load_institutions()

    st.title("Carteira de Crédito por IF 📊")

    # Sidebar for controls
    with st.sidebar:
        st.header("Configurações do Gráfico")

        # Institution selection
        st.markdown("### Seleção de Instituições")
        analysis_scope = st.radio(
            "Escopo da Análise:",
            options=["Mercado Total", "Instituições Específicas"],
            help="Escolha entre análise do mercado total ou instituições específicas"
        )

        if analysis_scope == "Instituições Específicas":
            selected_institutions = st.multiselect(
                "Selecione as instituições:",
                options=institutions_list,
                default=["ITAU", "BRADESCO", "SANTANDER"],
                help="Digite para buscar instituições específicas",
                placeholder="Digite para buscar..."
            )

            # Show selected institutions count
            if selected_institutions:
                st.info(f"✓ {len(selected_institutions)} instituições selecionadas")
        else:
            selected_institutions = "All"

        # Initial year filter
        initial_year = st.number_input(
            "Ano inicial:",
            min_value=2014,
            max_value=2024,
            value=2014,
            help="Filtrar dados a partir deste ano"
        )

        # When sending to the API, make it optional
        api_initial_year = initial_year if initial_year != 2014 else None

        # Grouping option
        grouped = st.radio(
            "Nível de Detalhamento:",
            options=["Detalhado por Modalidade", "Agrupado (PF vs PJ)"],
            help="Escolha o nível de detalhamento da análise",
            index=0
        )
        # Convert to API parameter (0 or 1)
        grouped_param = 1 if grouped == "Agrupado (PF vs PJ)" else 0

        # Show percentage toggle
        show_percentage = st.toggle(
            "Mostrar em percentual",
            value=True,
            help="Exibir valores em percentual do total ou valores absolutos"
        )

    # Main content area
    st.subheader("Composição da Carteira de Crédito" +
                 (" - Mercado Total" if selected_institutions == "All"
              else f" - {', '.join(selected_institutions)}"))

    try:
        # Call the API with parameters
        params = {
            "select_institutions": selected_institutions,
            "initial_year": api_initial_year,
            "grouped": grouped_param,
            "show_percentage": show_percentage
        }

        response = requests.get(
            "https://bacen-api-522706975081.europe-west1.run.app/plot/credit_portfolio",
            params=params
        )

        if response.status_code == 200:
            fig_json = response.json()["figure_json"]
            fig = pio.from_json(fig_json)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"API Error: {response.status_code}")
            st.error("Response Text:")
            try:
                error_details = response.json()
                st.json(error_details)
            except:
                st.error(response.text)

    except Exception as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.error(f"Full error: {e.__class__.__name__}: {str(e)}")

    # Add explanatory text
    with st.expander("ℹ️ Sobre esta análise"):
        st.markdown("""
        ### Interpretação do Gráfico
        - O gráfico apresenta a composição da carteira de crédito ao longo do tempo
        - As áreas empilhadas mostram a proporção de cada modalidade de crédito
        - A análise pode ser feita para o mercado total ou instituições específicas

        ### Modalidades de Crédito

        #### Visão Agrupada
        - **Pessoa Física (PF)**: Total das operações de crédito para pessoas físicas
        - **Pessoa Jurídica (PJ)**: Total das operações de crédito para empresas

        #### Visão Detalhada

        **Pessoa Física (PF)**
        - **Consignado**: Empréstimos com desconto em folha
        - **Não Consignado**: Empréstimos pessoais sem garantia
        - **Veículos**: Financiamento de veículos
        - **Habitação**: Financiamento imobiliário
        - **Cartão de Crédito**: Operações de cartão de crédito
        - **Rural**: Crédito rural e agroindustrial
        - **Outros**: Demais modalidades PF

        **Pessoa Jurídica (PJ)**
        - **Recebíveis**: Antecipação de recebíveis
        - **Capital de Giro**: Financiamento de capital de giro
        - **Capital de Giro Rotativo**: Linhas rotativas de capital de giro
        - **Investimento**: Financiamento de investimentos
        - **Infraestrutura**: Financiamento de projetos de infraestrutura
        - **Comércio Exterior**: Financiamento de importação/exportação
        - **Rural**: Crédito rural e agroindustrial
        - **Habitação**: Financiamento imobiliário PJ
        - **Outros**: Demais modalidades PJ

        ### Notas Metodológicas
        - Dados fonte: Bacen (IF.data)
        - Frequência: Trimestral
        - Valores podem ser visualizados em termos percentuais ou absolutos
        - Na visão percentual: (valor_modalidade / valor_total_carteira) * 100
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Carteira de Crédito por IF",
        page_icon="💳",
        layout="wide"
    )
    main()
