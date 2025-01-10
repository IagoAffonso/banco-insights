import streamlit as st
import requests
import json
import plotly.io as pio
import pandas as pd
import os

def load_institutions():
    """Load and cache the institutions list"""
    @st.cache_data  # Now we can use cache_data instead of cache
    def _load_institutions():
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "institutions_name_list.csv")
        df = pd.read_csv(file_path)
        return df['NomeInstituicao'].tolist()

    return _load_institutions()

def main():

    # Load institutions list
    institutions_list = load_institutions()

    st.title("Market Share Bancário 📊")

    # Sidebar for controls
    with st.sidebar:
        st.header("Configurações do Gráfico")

        # Market view selection based on feature_name_dict from plotting.py
        feature = st.selectbox(
            "Selecione a métrica:",
            options=[
                'Quantidade de clientes com operações ativas',
                'Carteira de Crédito Pessoa Física',
                'Carteira de Crédito Pessoa Jurídica',
                'Carteira de Crédito Classificada',
                'Receitas de Intermediação Financeira',
                'Rendas de Prestação de Serviços',
                'Captações',
                'Lucro Líquido',
                'Passivo Captacoes: Depósitos Total',
                'Passivo Captacoes: Emissão de Títulos (LCI,LCA,LCF...)',
                'Receita com Operações de Crédito',
                'Receita com Operações de Títulos e Valores Mobiliários',
                'Receita com Operações de Câmbio'
            ],
            help="Selecione a métrica para análise de market share"
        )

        # Number of top institutions
        top_n = st.number_input(
            "Top N instituições:",
            min_value=1,
            max_value=50,
            value=10,
            help="Número de maiores instituições a serem exibidas separadamente"
        )

        # Initial year filter - Let's debug the value being sent
        initial_year = st.number_input(
            "Ano inicial:",
            min_value=2014,
            max_value=2024,
            value=2014,
            help="Filtrar dados a partir deste ano"
        )

        # When sending to the API, we can still make it optional
        api_initial_year = initial_year if initial_year != 2014 else None

        # Nubank handling - Let's add debug info
        drop_nubank = st.radio(
            "Tratamento Nubank:",
            options=[
                "Manter ambas entidades",
                "Remover NU PAGAMENTOS",
                "Remover NUBANK"
            ],
            index=0,
            help="O Nubank está registrado no Bacen como duas entidades distintas, uma Instituição de Pagamento (Cartões e Conta de pagamento) e uma Instituição Financeira (Crédito e RDBs). Escolha como tratar as diferentes entidades do Nubank"
        )
        # Convert radio selection to numeric value
        drop_nubank_value = {"Manter ambas entidades": 0,
                           "Remover NU PAGAMENTOS": 1,
                           "Remover NUBANK": 2}[drop_nubank]

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
    #st.subheader(f"Evolução do Market Share - {feature}")

    try:
        # Call the API with explicit parameter handling
        params = {
            "feature": feature,
            "top_n": top_n,
            "initial_year": api_initial_year,
            "drop_nubank": drop_nubank_value,
        }

        # Only add custom_selected_institutions if it's not empty
        if custom_institutions:
            params["custom_selected_institutions"] = custom_institutions


    # Local host version http://localhost:8000
    # GCP version https://bacen-api-522706975081.europe-west1.run.app
        response = requests.get(
            "https://bacen-api-522706975081.europe-west1.run.app/plot/market_share",
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
        - O gráfico mostra a evolução temporal da participação de mercado das instituições financeiras
        - As áreas são empilhadas, somando 100% do mercado em cada período
        - Instituições menores são agrupadas em "Others" para melhor visualização

        ### Notas Metodológicas
        - Dados fonte: Bacen (IF.data)
        - Frequência: Trimestral
        - Market Share calculado como: (valor_instituição / valor_total_mercado) * 100
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Market Share Bancário",
        page_icon="📊",
        layout="wide"
    )
    main()
