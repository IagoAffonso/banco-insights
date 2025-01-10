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

    st.title("Market Share Linhas de Crédito 📈")

    # Sidebar for controls
    with st.sidebar:
        st.header("Configurações do Gráfico")

        # Credit modalities selection
        modalities = st.multiselect(
            "Selecione as modalidades de crédito:",
            options=[
                "Total PF", "Consignado PF", "Não Consignado PF", "Veículos PF",
                "Outros Créditos PF", "Habitação PF", "Cartão de Crédito PF", "Rural PF",
                "Total PJ", "Recebíveis PJ", "Comércio Exterior PJ", "Outros Créditos PJ",
                "Infraestrutura PJ", "Capital de Giro PJ", "Investimento PJ",
                "Capital de Giro Rotativo PJ", "Rural PJ", "Habitação PJ", "Cheque Especial PJ"
            ],
            default=["Total PF", "Total PJ"],
            help="Selecione uma ou mais modalidades de crédito para análise"
        )

        # Number of top institutions
        top_n = st.number_input(
            "Top N instituições:",
            min_value=1,
            max_value=50,
            value=10,
            help="Número de maiores instituições a serem exibidas separadamente"
        )

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

        # Show percentage toggle
        show_percentage = st.toggle(
            "Mostrar em percentual",
            value=True,
            help="Exibir valores em percentual do total ou valores absolutos"
        )

        # Custom institutions selection
        st.markdown("### Instituições Específicas")
        custom_institutions = st.multiselect(
            "Buscar e selecionar instituições:",
            options=institutions_list,
            default=None,
            help="Digite para buscar instituições específicas",
            placeholder="Digite para buscar..."
        )

        # Add a note about the search functionality
        st.caption("💡 Digite o nome da instituição para filtrar as opções")

        # Show selected institutions count
        if custom_institutions:
            st.info(f"✓ {len(custom_institutions)} instituições selecionadas")

    # Main content area
    #st.subheader(f"Evolução do Market Share - {', '.join(modalities)}")

    try:
        # Call the API with parameters
        params = {
            "modalities": modalities,
            "top_n": top_n,
            "initial_year": api_initial_year,
            "show_percentage": show_percentage,
        }

        # Only add custom_selected_institutions if it's not empty
        if custom_institutions:
            params["custom_selected_institutions"] = custom_institutions

        response = requests.get(
            "https://bacen-api-522706975081.europe-west1.run.app/plot/share_credit_modality",
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
        - O gráfico mostra a evolução temporal da participação de mercado das instituições financeiras em modalidades específicas de crédito
        - As áreas são empilhadas, somando 100% do mercado em cada período
        - Instituições menores são agrupadas em "Others" para melhor visualização

        ### Modalidades de Crédito
        #### Pessoa Física (PF)
        - **Total PF**: Carteira total de crédito para pessoas físicas
        - **Consignado**: Empréstimos com desconto em folha
        - **Não Consignado**: Empréstimos pessoais sem garantia
        - **Veículos**: Financiamento de veículos
        - **Habitação**: Financiamento imobiliário
        - **Cartão de Crédito**: Operações de cartão de crédito
        - **Rural**: Crédito rural e agroindustrial

        #### Pessoa Jurídica (PJ)
        - **Total PJ**: Carteira total de crédito para pessoas jurídicas
        - **Recebíveis**: Antecipação de recebíveis
        - **Comércio Exterior**: Financiamento de importação/exportação
        - **Infraestrutura**: Financiamento de projetos de infraestrutura
        - **Capital de Giro**: Financiamento de capital de giro
        - **Investimento**: Financiamento de investimentos

        ### Notas Metodológicas
        - Dados fonte: Bacen (IF.data)
        - Frequência: Trimestral
        - Market Share calculado como: (valor_instituição / valor_total_mercado) * 100
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Market Share por Segmento de Crédito",
        page_icon="💰",
        layout="wide"
    )
    main()
