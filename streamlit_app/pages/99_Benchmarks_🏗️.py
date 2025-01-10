import streamlit as st

def main():
    st.title("Benchmarks 📊")

    # Create a centered container for the message
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="
            padding: 20px;
            border: 2px solid #f0f2f6;
            border-radius: 10px;
            text-align: center;
            background-color: #f8f9fa;
            margin: 50px 0;">
            <div style="font-size: 50px; margin-bottom: 20px;">
                🏗️
            </div>
            <h2 style="color: #0066cc; margin-bottom: 10px;">
                Página em Construção
            </h2>
            <p style="color: #666666; font-size: 16px;">
                Estamos trabalhando para trazer análises comparativas ainda mais detalhadas do setor bancário.
            </p>
            <p style="color: #666666; font-size: 14px; margin-top: 20px;">
                Em breve: Análise de quartis, medianas, peers, rankings e outros benchmarks setoriais.
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Benchmarks",
        page_icon="🏗️",
        layout="wide"
    )
    main()
