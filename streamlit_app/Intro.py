import streamlit as st
import pandas as pd
import os


def save_suggestion(name, email, company, message):
    data = {
        'Nome': [name],
        'Email': [email],
        'Empresa': [company],
        'Mensagem': [message]
    }
    df = pd.DataFrame(data)
    file_path = os.path.join('streamlit_app', 'data', 'suggestions.csv')
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    if os.path.exists(file_path):
        df.to_csv(file_path, mode='a', header=False, index=False)
    else:
        df.to_csv(file_path, index=False)


def main():
    st.title("🏦 Banco Insight 🏦")

    st.markdown(
        """
        ## Bem-vindo ao Painel de Inteligência do Mercado Bancário Brasileiro

        Explore insights poderosos sobre o setor bancário brasileiro com mais de **2 mil** instituições financeiras reguladas pelo Bacen.

        ---

        #### 🚀 Serviços Disponíveis
        - 📊 **Market Share por Instituição Financeira**: Compare diferentes métricas de participação de mercado.
        - 💰 **Market Share por Segmento de Crédito**: Análise por modalidade de crédito.
        - 💳 **Carteira de Crédito por IF**: Visualize a composição detalhada da carteira de crédito de cada IF.
        - 📑 **DREs - Demonstrações Financeiras**: Análise de demonstrativos financeiros.
        - 📈 **Séries Temporais**: Comparativo de evolução histórica de métricas financeiras e operacionais por IFs.

        ---

        #### 🔄 Roadmap
        - 🏗️ **Benchmarks**: Comparativos setoriais como mediana, quartis, decis, peer groups e rankings.
        - 🎯 **Modelos de Segmentação (Clustering)**
        - 🤖 **Modelos de Machine Learning & AI**
        - 🤖 **BancoInsightsGPT**

        ---

        #### 📝 Como Utilizar
        1. **Navegue pelo menu lateral.**
        2. **Escolha os parâmetros de análise.**
        3. **Explore os painéis interativos.**

        
        """
    )



    # Suggestions Section with form
    st.markdown("---")
    st.markdown("### 💡 Envie Suas Sugestões")
    st.info(
        "📢 **O Banco Insight está em evolução!**\n\n"
        "📬 Envie suas ideias e sugestões de melhorias.\n\n")
    with st.form("suggestion_form"):
        name = st.text_input("Nome")
        email = st.text_input("Email")
        company = st.text_input("Empresa")
        message = st.text_area("Mensagem")
        submitted = st.form_submit_button("Enviar Mensagem")

        if submitted:
            save_suggestion(name, email, company, message)
            st.success("Obrigado pela mensagem! Sua sugestão foi registrada com sucesso.")

    # Newsletter Section with enhanced visuals
    st.markdown("---")
    st.markdown("### 📫 Newsletter")
    st.info(
        "🔔 **Assine nossa newsletter trimestral para receber insights exclusivos do mercado!**\n\n"
        "🔨 *Funcionalidade em desenvolvimento.*"
    )





if __name__ == "__main__":
    st.set_page_config(
        page_title="Banco Insight",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
