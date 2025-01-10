def plot_market_share(df,feature='Quantidade de clientes com operações ativas', top_n=10, custom_selected_institutions=None, initial_year=None,drop_nubank=0):
    """
    Creates a stacked area plot showing the market share evolution over time for financial institutions for selected metric.

    Parameters:
    -----------
    df : pandas.DataFrame # Preloaded dataframe in the function #########
        Input dataframe containing the raw financial data with columns:
        - NomeRelatorio_Grupo_Coluna: The report category/metric name
        - AnoMes: Date column
        - NomeInstituicao: Institution name
        - Saldo: Balance/value column

    feature : str
        Feature name to analyze. Must be one of the keys in feature_name_dict.
        Examples: 'Carteira de Crédito Pessoa Física', 'Lucro Líquido', etc.

    top_n : int, optional (default=10)
        Number of top institutions to show separately in the plot.
        Remaining institutions will be grouped into "Others".

    custom_selected_institutions : list of str, optional (default=None)
        List of institution names to always include in the plot, regardless of their ranking.
        These will be shown in addition to the top institutions up to top_n.

    initial_year : int, optional (default=None)
        Starting year for the analysis. If provided, data before this year will be filtered out.

    drop_nubank : int, optional (default=0)
        Controls Nubank filtering:
        - 0: Keep both Nubank entities
        - 1: Drop "NU PAGAMENTOS S.A. - INSTITUIÇÃO DE PAGAMENTO"
        - 2: Drop "NUBANK"

    Returns:
    --------
    tuple:
        - plotly.graph_objects.Figure: Interactive plot showing market share evolution
        - pandas.DataFrame: Pivot table containing the market share data used in the plot,
                          with quarters as index and institutions as columns

    Notes:
    ------
    - The plot is a stacked area chart where each area represents an institution's market share
    - Market shares are calculated quarterly as: (institution_value / total_market_value) * 100
    - Institutions are sorted by their most recent market share
    - The plot includes hover information showing exact market share values
    - Legend names are truncated to 15 characters for better visualization

    """
    import plotly.graph_objects as go
    import pandas as pd

    # Dictionary mapping features to their full column names
    # Add more mappings as needed
    feature_name_dict = {
        'Quantidade de clientes com operações ativas':'Carteira de crédito ativa - quantidade de clientes e de operações_nagroup_Quantidade de clientes com operações ativas',
        'Carteira de Crédito Pessoa Física':'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_nagroup_Total da Carteira de Pessoa Física',
        'Carteira de Crédito Pessoa Jurídica':'Carteira de crédito ativa Pessoa Jurídica - por porte do tomador_nagroup_Total da Carteira de Pessoa Jurídica',
        'Carteira de Crédito Classificada':'Resumo_nagroup_Carteira de Crédito Classificada',
        'Receitas de Intermediação Financeira':'Demonstração de Resultado_Resultado de Intermediação Financeira - Receitas de Intermediação Financeira_Receitas de Intermediação Financeira \n(a) = (a1) + (a2) + (a3) + (a4) + (a5) + (a6)',
        'Rendas de Prestação de Serviços':'Demonstração de Resultado_Outras Receitas/Despesas Operacionais_Rendas de Prestação de Serviços \n(d1)',
        'Captações':'Resumo_nagroup_Captações',
        'Lucro Líquido':'Resumo_nagroup_Lucro Líquido',
        'Passivo Captacoes: Depósitos Total':'Passivo_Captações - Depósito Total_Depósito Total \n(a)',
        'Passivo Captacoes: Emissão de Títulos (LCI,LCA,LCF...)':'Passivo_Captações - Recursos de Aceites e Emissão de Títulos_Recursos de Aceites e Emissão de Títulos \n(c)',
        #### NEW ADDITIONS
        'Receita com Operações de Crédito':'Demonstração de Resultado_Resultado de Intermediação Financeira - Receitas de Intermediação Financeira_Rendas de Operações de Crédito \n(a1)',
        'Receita com Operações de Títulos e Valores Mobiliários':'Demonstração de Resultado_Resultado de Intermediação Financeira - Receitas de Intermediação Financeira_Rendas de Operações com TVM \n(a3)',
        'Receita com Operações de Câmbio':'Demonstração de Resultado_Resultado de Intermediação Financeira - Receitas de Intermediação Financeira_Resultado de Operações de Câmbio \n(a5)',
        }


    # Map the feature name and filter the dataframe
    feature_name = feature_name_dict[feature]
    df_filtered = df[df['NomeRelatorio_Grupo_Coluna'] == feature_name].copy()
    # Convert date columns BEFORE filtering by initial_year
    df_filtered['AnoMes'] = pd.to_datetime(df_filtered['AnoMes'])

    # Handle Nubank filtering
    if drop_nubank == 1:
        df_filtered = df_filtered[df_filtered['NomeInstituicao'] != "NU PAGAMENTOS S.A. - INSTITUIÇÃO DE PAGAMENTO"]
    elif drop_nubank == 2:
        df_filtered = df_filtered[df_filtered['NomeInstituicao'] != "NUBANK"]

    # Filter by initial_year if provided
    if initial_year:
        df_filtered = df_filtered[df_filtered['AnoMes'].dt.year >= initial_year]

    # Group by quarter and institution to get total saldo
    quarterly_data = df_filtered.groupby(['AnoMes_Q', 'NomeInstituicao'])['Saldo'].sum().reset_index()

    # Calculate total market size per quarter
    market_total = quarterly_data.groupby('AnoMes_Q')['Saldo'].sum().reset_index()

    # Merge total market size back to calculate market share
    quarterly_data = quarterly_data.merge(market_total, on='AnoMes_Q', suffixes=('', '_total'))
    quarterly_data['market_share'] = (quarterly_data['Saldo'] / quarterly_data['Saldo_total'] * 100)

    # Create pivot table for market share
    pivot_share = quarterly_data.pivot_table(
        index='AnoMes_Q',
        columns='NomeInstituicao',
        values='market_share',
        aggfunc='first'
    ).sort_index()

    # Get the last period's values to identify top institutions
    last_period = pivot_share.iloc[-1].sort_values(ascending=False)

    # Get top_n institutions first
    top_institutions = last_period.head(top_n).index.tolist()

    # If custom institutions are provided, ADD them to top_n (don't replace)
    if custom_selected_institutions and len(custom_selected_institutions) > 0:
        # Simply append custom institutions to top_n list
        selected_institutions = top_institutions.copy()  # Make a copy of top institutions
        for inst in custom_selected_institutions:
            if inst not in selected_institutions:  # Only add if not already in list
                selected_institutions.append(inst)
    else:
        # If no custom institutions, just use top_n
        selected_institutions = top_institutions

    # Separate other institutions
    other_institutions = [col for col in pivot_share.columns if col not in selected_institutions]

    # Create the final DataFrame for plotting
    plot_df_share = pivot_share[selected_institutions].copy()

    if other_institutions:
        plot_df_share['Others'] = pivot_share[other_institutions].sum(axis=1)

    # Sort all columns except 'Others' by the most recent period's values
    last_period_values = plot_df_share.iloc[-1]
    sorted_cols = last_period_values.drop('Others' if 'Others' in plot_df_share.columns else [], errors='ignore')\
                                  .sort_values(ascending=False).index.tolist()

    # Add 'Others' back as the last column if it exists
    if 'Others' in plot_df_share.columns:
        sorted_cols = sorted_cols + ['Others']

    # Apply the sorting
    plot_df_share = plot_df_share[sorted_cols]

    # Create figure
    fig = go.Figure()

    # Add market share traces (stacked area) in reverse order to stack largest at bottom
    for column in reversed(plot_df_share.columns):
        # Truncate institution name for legend
        legend_name = column[:15] + '...' if len(column) > 15 else column

        # Set color to grey for 'Others', default color scheme for the rest
        color = 'lightgrey' if column == 'Others' else None

        fig.add_trace(
            go.Scatter(
                x=plot_df_share.index.astype(str),
                y=plot_df_share[column],
                name=legend_name,  # Use truncated name in legend
                stackgroup='share',
                line=dict(color=color) if color else dict(),  # Apply color to line
                fillcolor=color,  # Apply color to fill area
                hovertemplate="%{x}<br>" +
                            "%{y:.1f}% market share<br>" +
                            f"Institution: {column}<extra></extra>"  # Keep full name in hover
            )
        )

    # Update layout
    fig.update_layout(
        height=600,
        title_text=f"Evolução Market Share - {feature}" +
                  (f" (Desde {initial_year})" if initial_year else ""),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            traceorder='reversed'  # Reverse legend order to match visual order
        ),
        #hovermode='x unified',
        yaxis_title="Market Share (%)",
        xaxis_title="Quarter"
    )

    #fig.show()

    #, plot_df_share

    return fig


#----------------------------------------------------------------------------


def plot_share_credit_modality(credit_data_df, modalities, initial_year=None, top_n=10, custom_selected_institutions=None, show_percentage=True):
    """
    Creates a stacked area plot showing the market share evolution over time for selected credit modalities.

    Parameters:
    -----------
     credit_data : pandas.DataFrame
        DataFrame containing credit data with columns:
        - NomeRelatorio_Grupo_Coluna: The report category/metric name
        - AnoMes: Date column (datetime)
        - AnoMes_Q: Quarter column (period)
        - NomeInstituicao: Institution name
        - Saldo: Balance/value column

    modalities : str or list
        Credit modality or list of modalities to analyze. Must be one of the valid modalities from
        modality_name_dict. Examples:
        - 'Veículos PF'
        - ['Veículos PF', 'Habitação PF']

    initial_year : int, optional (default=None)
        Starting year for the analysis. If provided, data before this year will be filtered out.

    top_n : int, optional (default=10)
        Number of top institutions to show separately in the plot.
        Remaining institutions will be grouped into "Others".

    custom_selected_institutions : list of str, optional (default=None)
        List of institution names to always include in the plot, regardless of their ranking.

    show_percentage : bool, optional (default=True)
        If True, shows values as percentage of total
        If False, shows absolute values (saldo)

    Returns:
    --------
    tuple:
        - plotly.graph_objects.Figure: Interactive plot showing credit modality share evolution
        - pandas.DataFrame: Pivot table containing the share data used in the plot
    """
    import plotly.graph_objects as go
    import pandas as pd

    # Dictionary mapping user-friendly names to full column names
    modality_name_dict = {
        # PF modalities
        'Total PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_nagroup_Total da Carteira de Pessoa Física',
        'Consignado PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Empréstimo com Consignação em Folha_Total',
        'Não Consignado PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Empréstimo sem Consignação em Folha_Total',
        'Veículos PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Veículos_Total',
        'Outros Créditos PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Outros Créditos_Total',
        'Habitação PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Habitação_Total',
        'Cartão de Crédito PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Cartão de Crédito_Total',
        'Rural PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Rural e Agroindustrial_Total',

        # PJ modalities
        'Total PJ': 'Carteira de crédito ativa Pessoa Jurídica - por porte do tomador_nagroup_Total da Carteira de Pessoa Jurídica',
        'Recebíveis PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Operações com Recebíveis_Total',
        'Comércio Exterior PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Comércio Exterior_Total',
        'Outros Créditos PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Outros Créditos_Total',
        'Infraestrutura PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Financiamento de Infraestrutura/Desenvolvimento/Projeto e Outros Créditos_Total',
        'Capital de Giro PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Capital de Giro_Total',
        'Investimento PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Investimento_Total',
        'Capital de Giro Rotativo PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Capital de Giro Rotativo_Total',
        'Rural PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Rural e Agroindustrial_Total',
        'Habitação PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Habitacional_Total',
        'Cheque Especial PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Cheque Especial e Conta Garantida_Total',

    }


    # Store credit_data_df as df
    df = credit_data_df

    # Convert modalities to list if single string
    if isinstance(modalities, str):
        modalities = [modalities]

    # Map user-friendly names to full column names
    mapped_modalities = [modality_name_dict[mod] for mod in modalities]

    # Convert date columns
    df = df.copy()
    df['AnoMes'] = pd.to_datetime(df['AnoMes'], format='%Y-%m-%d')
    df['AnoMes_Q'] = pd.PeriodIndex(df['AnoMes_Q'], freq='Q')

    # Filter dataframe for selected modalities
    df_filtered = df[df['NomeRelatorio_Grupo_Coluna'].isin(mapped_modalities)].copy()

    # Filter by initial_year if provided
    if initial_year:
        df_filtered = df_filtered[df_filtered['AnoMes'].dt.year >= initial_year]

    # Group by quarter and institution to get total saldo
    quarterly_data = df_filtered.groupby(['AnoMes_Q', 'NomeInstituicao'])['Saldo'].sum().reset_index()

    # Calculate values based on show_percentage parameter
    if show_percentage:
        # Calculate percentages
        market_total = quarterly_data.groupby('AnoMes_Q')['Saldo'].sum().reset_index()
        quarterly_data = quarterly_data.merge(market_total, on='AnoMes_Q', suffixes=('', '_total'))
        quarterly_data['value'] = (quarterly_data['Saldo'] / quarterly_data['Saldo_total'] * 100)
        value_suffix = "%"
        yaxis_title = "Market Share (%)"
    else:
        # Use absolute values
        quarterly_data['value'] = quarterly_data['Saldo']
        value_suffix = ""
        yaxis_title = "Portfolio Value (R$)"

    # Create pivot table
    pivot_share = quarterly_data.pivot_table(
        index='AnoMes_Q',
        columns='NomeInstituicao',
        values='value',
        aggfunc='first'
    ).sort_index()

    # Get the last period's values to identify top institutions
    last_period = pivot_share.iloc[-1].sort_values(ascending=False)

    # Get top_n institutions first
    top_institutions = last_period.head(top_n).index.tolist()

    # If custom institutions are provided, ADD them to top_n (don't replace)
    if custom_selected_institutions and len(custom_selected_institutions) > 0:
        # Simply append custom institutions to top_n list
        selected_institutions = top_institutions.copy()  # Make a copy of top institutions
        for inst in custom_selected_institutions:
            if inst not in selected_institutions:  # Only add if not already in list
                selected_institutions.append(inst)
    else:
        # If no custom institutions, just use top_n
        selected_institutions = top_institutions

    # Separate other institutions
    other_institutions = [col for col in pivot_share.columns if col not in selected_institutions]

    # Create the final DataFrame for plotting
    plot_df_share = pivot_share[selected_institutions].copy()

    if other_institutions:
        plot_df_share['Others'] = pivot_share[other_institutions].sum(axis=1)

    # Sort all columns except 'Others' by the most recent period's values
    last_period_values = plot_df_share.iloc[-1]
    sorted_cols = last_period_values.drop('Others' if 'Others' in plot_df_share.columns else [], errors='ignore')\
                                  .sort_values(ascending=False).index.tolist()

    # Add 'Others' back as the last column if it exists
    if 'Others' in plot_df_share.columns:
        sorted_cols = sorted_cols + ['Others']

    # Apply the sorting
    plot_df_share = plot_df_share[sorted_cols]



    # Create figure
    fig = go.Figure()

    # Add traces in reverse order (largest at bottom)
    for column in reversed(plot_df_share.columns):
        # Truncate institution name for legend
        legend_name = column[:15] + '...' if len(column) > 15 else column

        # Set color to grey for 'Others', default color scheme for the rest
        color = 'lightgrey' if column == 'Others' else None

        fig.add_trace(
            go.Scatter(
                x=plot_df_share.index.astype(str),
                y=plot_df_share[column],
                name=legend_name,  # Use truncated name in legend
                stackgroup='share',
                line=dict(color=color) if color else dict(),  # Apply color to line
                fillcolor=color,  # Apply color to fill area
                hovertemplate="%{x}<br>" +
                            f"%{{y:.1f}}{value_suffix}<br>" +
                            f"Institution: {column}<extra></extra>"  # Keep full name in hover
            )
        )

    # Create title text
    title_text = f"Market Share Credit Portfolio - {modalities}"
    title_text += f" (Since {initial_year})" if initial_year else ""
    title_text += " - Percentual" if show_percentage else " - Saldo Absoluto"

    # Update layout
    fig.update_layout(
        height=600,
        title_text=title_text,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            traceorder='reversed'
        ),
        yaxis_title=yaxis_title,
        xaxis_title="Quarter"
    )

    #fig.show(renderer="browser")

    # , plot_df_share

    return fig


#----------------------------------------------------------------------------


def plot_credit_portfolio(credit_data_df, select_institutions="All", initial_year=None, grouped=0, show_percentage=True):
    """
    Creates a stacked area plot showing credit portfolio breakdown by modalities.

    Parameters:
    -----------
     credit_data : pandas.DataFrame
        DataFrame containing credit data with columns:
        - NomeRelatorio_Grupo_Coluna: The report category/metric name
        - AnoMes: Date column (datetime)
        - AnoMes_Q: Quarter column (period)
        - NomeInstituicao: Institution name
        - Saldo: Balance/value column

    select_institutions : str or list, optional (default="All")
        "All" to show market-wide breakdown, or list of institution names to show their specific breakdown

    initial_year : int, optional (default=None)
        Starting year for the analysis. If provided, data before this year will be filtered out.

    grouped : int, optional (default=0)
        0: Shows detailed breakdown by modalities
        1: Shows only PF vs PJ breakdown

    show_percentage : bool, optional (default=True)
        If True, shows values as percentage of total
        If False, shows absolute values (saldo)

    Returns:
    --------
    tuple: (plotly.graph_objects.Figure, pandas.DataFrame)
    """
    # Import required libraries
    import plotly.graph_objects as go
    import pandas as pd

    # Dictionary of modalities

    # Dictionary mapping user-friendly names to full column names for detailed credit portfolio
    credit_portfolio = {
        'Consignado PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Empréstimo com Consignação em Folha_Total',
        'Não Consignado PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Empréstimo sem Consignação em Folha_Total',
        'Veículos PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Veículos_Total',
        'Outros Créditos PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Outros Créditos_Total',
        'Habitação PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Habitação_Total',
        'Cartão de Crédito PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Cartão de Crédito_Total',
        'Rural PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_Rural e Agroindustrial_Total',
        'Recebíveis PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Operações com Recebíveis_Total',
        'Comércio Exterior PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Comércio Exterior_Total',
        'Outros Créditos PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Outros Créditos_Total',
        'Infraestrutura PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Financiamento de Infraestrutura/Desenvolvimento/Projeto e Outros Créditos_Total',
        'Capital de Giro PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Capital de Giro_Total',
        'Investimento PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Investimento_Total',
        'Capital de Giro Rotativo PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Capital de Giro Rotativo_Total',
        'Rural PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Rural e Agroindustrial_Total',
        'Habitação PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Habitacional_Total',
        'Cheque Especial PJ': 'Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento_Cheque Especial e Conta Garantida_Total',
    }

    # Dictionary for grouped view (PF vs PJ only)
    credit_portfolio_grouped = {
        'Total PF': 'Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento_nagroup_Total da Carteira de Pessoa Física',
        'Total PJ': 'Carteira de crédito ativa Pessoa Jurídica - por porte do tomador_nagroup_Total da Carteira de Pessoa Jurídica'
    }

    # Select appropriate portfolio dictionary based on grouped parameter
    portfolio_dict = credit_portfolio_grouped if grouped else credit_portfolio

    # Load credit_data_df as store in df
    df = credit_data_df

    # Convert date columns to appropriate formats
    df['AnoMes'] = pd.to_datetime(df['AnoMes'])
    df['AnoMes_Q'] = pd.PeriodIndex(df['AnoMes_Q'], freq='Q')

    # Filter data by modalities and year
    df_filtered = df[df['NomeRelatorio_Grupo_Coluna'].isin(portfolio_dict.values())].copy()
    if initial_year:
        df_filtered = df_filtered[df_filtered['AnoMes'].dt.year >= initial_year]

    # Filter by specific institutions if requested
    if select_institutions != "All":
        if isinstance(select_institutions, str):
            select_institutions = [select_institutions]
        df_filtered = df_filtered[df_filtered['NomeInstituicao'].isin(select_institutions)]

    # Group data by quarter and modality
    quarterly_data = df_filtered.groupby(['AnoMes_Q', 'NomeRelatorio_Grupo_Coluna'])['Saldo'].sum().reset_index()

    # Calculate values based on show_percentage parameter
    if show_percentage:
        # Calculate percentages
        total_by_quarter = quarterly_data.groupby('AnoMes_Q')['Saldo'].sum().reset_index()
        quarterly_data = quarterly_data.merge(total_by_quarter, on='AnoMes_Q', suffixes=('', '_total'))
        quarterly_data['value'] = (quarterly_data['Saldo'] / quarterly_data['Saldo_total'] * 100)
        value_suffix = "%"
        yaxis_title = "Portfolio Share (%)"
    else:
        # Use absolute values
        quarterly_data['value'] = quarterly_data['Saldo']
        value_suffix = ""
        yaxis_title = "Portfolio Value (R$)"

    # Create pivot table for plotting
    pivot_data = quarterly_data.pivot_table(
        index='AnoMes_Q',
        columns='NomeRelatorio_Grupo_Coluna',
        values='value',
        aggfunc='first'
    ).sort_index()

    # Map column names back to friendly names
    reverse_dict = {v: k for k, v in portfolio_dict.items()}
    pivot_data.columns = [reverse_dict[col] for col in pivot_data.columns]

    # Sort columns by last period values
    last_period_values = pivot_data.iloc[-1].sort_values(ascending=False)
    pivot_data = pivot_data[last_period_values.index]

    # Create the figure
    fig = go.Figure()

    # Add traces for each modality in reverse order (largest at bottom)
    for column in reversed(pivot_data.columns):
        fig.add_trace(
            go.Scatter(
                x=pivot_data.index.astype(str),
                y=pivot_data[column],
                name=column,
                stackgroup='one',
                hovertemplate="%{x}<br>" +
                            f"%{{y:.1f}}{value_suffix}<br>" +
                            f"Modality: {column}<extra></extra>"
            )
        )

    # Create title text
    title_text = "Credit Portfolio Breakdown - "
    title_text += "Market Wide" if select_institutions == "All" else ", ".join(select_institutions)
    title_text += f" (Since {initial_year})" if initial_year else ""
    title_text += " - Percentual" if show_percentage else " - Saldo Absoluto"

    # Update layout
    fig.update_layout(
        height=600,
        title_text=title_text,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            traceorder='reversed'
        ),
        yaxis_title=yaxis_title,
        xaxis_title="Quarter"
    )

    #fig.show(renderer="browser")

    #, pivot_data

    return fig


#----------------------------------------------------------------------------

def plot_time_series(financial_metrics_df, df_fmp, control, list_institutions, metric_name, start_date=None, end_date=None):
    """
    Creates a time series plot for specific financial metrics across selected institutions.

    Parameters:
    -----------
    financial_metrics_df : DataFrame
        Raw financial metrics dataframe
    df_fmp : DataFrame
        Processed financial metrics dataframe
    control : str
        Type of value to plot ('Valores Absolutos', 'Valores Relativos por % da Receita Operacional', 'Valores Relativos por Cliente')
    list_institutions : list
        List of institution names to include in the plot
    metric_name : str
        Name of the metric to analyze
    start_date : str, optional
        Start date for filtering (YYYY-MM-DD format)
    end_date : str, optional
        End date for filtering (YYYY-MM-DD format)
    """
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd

    fig = go.Figure()

    if control == "Valores Absolutos":
        df = financial_metrics_df.copy()
        value_col = 'Saldo'
        name_col = 'NomeColuna'
        date_col = 'AnoMes'

    elif control == "Valores Relativos por % da Receita Operacional":
        df = df_fmp.copy()
        value_col = 'ValuePercentRevenue'
        name_col = 'Component'
        date_col = 'AnoMes'

    elif control == "Valores Relativos por Cliente":
        df = df_fmp.copy()
        value_col = 'ValuePerClient'
        name_col = 'Component'
        date_col = 'AnoMes'

    else:
        raise ValueError(f"Invalid control value: {control}")

    # Store data for return
    plot_data = []

    # Add a line for each institution
    for institution in list_institutions:
        # Filter for institution and metric
        mask = (df['NomeInstituicao'] == institution) & (df[name_col] == metric_name)
        inst_data = df[mask].copy()

        if len(inst_data) == 0:
            print(f"No data found for institution: {institution}")
            continue

        # Convert date and handle deprecation warning
        inst_data['Date'] = pd.to_datetime(inst_data[date_col].astype(str))

        # Apply date filters if provided
        if start_date:
            inst_data = inst_data[inst_data['Date'] >= start_date]
        if end_date:
            inst_data = inst_data[inst_data['Date'] <= end_date]

        # Sort by date
        inst_data = inst_data.sort_values('Date')

        # Store processed data
        plot_data.append(inst_data)

        # Create shortened institution name for legend
        short_name = institution[:15] + '...' if len(institution) > 15 else institution

        # Add the line
        fig.add_trace(go.Scatter(
            x=inst_data['Date'],
            y=inst_data[value_col],
            mode='lines+markers',
            name=short_name,
            line=dict(width=2),
            marker=dict(size=8)
        ))

    # Update layout
    value_type = {
        "Valores Absolutos": "Absolute Values",
        "Valores Relativos por % da Receita Operacional": "% of Operating Revenue",
        "Valores Relativos por Cliente": "Per Client"
    }

    fig.update_layout(
        title=f"{metric_name} - {control}",
        xaxis=dict(
            title="Date",
            tickformat="%b %Y",
            tickangle=45,
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)'
        ),
        yaxis=dict(
            title=value_type[control],
            tickformat=",.2f",
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.2)'
        ),
        height=500,
        width=800,
        showlegend=True,
        template='plotly_white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        )
    )

    return fig, plot_data

#----------------------------------------------------------------------------
