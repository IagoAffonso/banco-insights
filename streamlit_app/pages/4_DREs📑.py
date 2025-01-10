import streamlit as st
import requests
import plotly.io as pio
import os
import json
import pandas as pd


def load_institutions_periods():
    """Load and cache the institutions list and periods list"""
    @st.cache_data  # Now we can use cache_data instead of cache
    def _load_institutions():
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, "..", "data", "institutions_name_list.csv")
        df = pd.read_csv(file_path)
        return df['NomeInstituicao'].tolist()

    @st.cache_data  # Cache the periods list
    def _load_periods():
        # Generate all quarters from 2013 to 2024
        periods = [
            f"{year}Q{quarter}"
            for year in range(2013, 2024 + 1)
            for quarter in range(1, 4 + 1)
        ]
        # Remove 2024Q4 as it's not available yet
        periods.remove("2024Q4")
        # Sort in reverse chronological order
        periods.sort(reverse=True)
        return periods

    return _load_institutions(), _load_periods()


def main():

    # Load institutions list
    institutions_list, available_periods = load_institutions_periods()



    st.title("📑 Demonstrações de Resultado")

    st.markdown("""
    ### Análise de DRE das Instituições Financeiras
    """)

    # Create columns for filters
    col1, col2 = st.columns(2)

    with col1:
        # Chart Type Selection
        chart_type = st.selectbox(
            "Tipo de Análise",
            options=[
                "Breakdown da Receita",
                "Breakdown do P&L",
                "Breakdown do Resultado de Intermediação Financeira"
            ],
            help="Selecione o tipo de análise financeira"
        )

        # View Type Selection
        view_type = st.selectbox(
            "Tipo de Visualização",
            options=[
                "Valor Absoluto",
                "% Receita Operacional",
                "Por Cliente Trimestre"
            ],
            help="Selecione como os valores devem ser apresentados"
        )

    with col2:
        # Period Selection (assuming we have this data available)
        # You might want to fetch this from your API or database

        periods = st.multiselect(
            "Períodos",
            options=available_periods,
            default=["2024Q3"],
            help="Selecione um ou mais períodos para análise"
        )

        # Institution Selection
        # You might want to fetch this from your API or database
        available_institutions = institutions_list
        institutions = st.multiselect(
            "Instituições",
            options=available_institutions,
            default=["NUBANK"],
            help="Selecione uma ou mais instituições para análise"
        )

    # Only proceed if all selections are made
    if chart_type and view_type and periods and institutions:
        try:
            params={
                    "chart_type": chart_type,
                    "view_type": view_type,
                    "periods_list": periods,
                    "institutions_list": institutions
                }

            print("Sending request with parameters:", params)

            # Call the API
            response = requests.get(
                "https://bacen-api-522706975081.europe-west1.run.app/plot/dre_waterfall",
                params=params
            )

            if response.status_code == 200:
                # Parse the JSON response
                figure_json = response.json()["figure_json"]
                fig = pio.from_json(figure_json)

                # Display the plot
                st.plotly_chart(fig, use_container_width=True)


            else:
                st.error(f"Error: Unable to fetch data. Status code: {response.status_code}")

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
    else:
        st.info("Por favor, selecione todos os filtros para visualizar o gráfico.")

    # Add explanatory text
    with st.expander("ℹ️ Sobre esta análise"):
        st.markdown("""
        ### Interpretação do Gráfico

        ##### Tipos de Análise

        ##### Breakdown da Receita
        - Demonstra a composição da receita operacional total
        - Inclui receitas de intermediação financeira, serviços, e outras receitas operacionais
        - Permite visualizar as principais fontes de receita da instituição

        ##### Breakdown do P&L
        - Apresenta a construção do resultado final (lucro ou prejuízo)
        - Parte da receita operacional total
        - Deduz custos, despesas e impostos
        - Mostra o impacto de cada componente no resultado final

        ##### Breakdown do Resultado de Intermediação Financeira
        - Foca especificamente no resultado das operações financeiras
        - Inclui receitas de crédito, títulos e valores mobiliários
        - Deduz despesas de captação e provisões
        - Demonstra a eficiência da atividade principal do banco

        ##### Tipos de Visualização

        ##### Valor Absoluto
        - Apresenta os valores em reais (R$)
        - Útil para análise de magnitude e escala das operações

        ##### % Receita Operacional
        - Mostra cada componente como percentual da receita operacional total
        - Facilita comparações entre instituições de diferentes portes
        - Permite análise de eficiência e margens

        ##### Por Cliente Trimestre
        - Normaliza os valores pelo número de clientes ativos
        - Útil para comparar eficiência operacional entre instituições
        - Indica receita/custo médio por cliente

        #### Notas Metodológicas
        - Dados fonte: Bacen (IF.data)
        - Frequência: Trimestral
        - Valores consolidados por instituição
        - Possibilidade de análise multi-período e multi-instituição
        """)


if __name__ == "__main__":
    st.set_page_config(
        page_title="DRE Analysis",
        page_icon="📑",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
