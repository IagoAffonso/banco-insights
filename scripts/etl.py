import pandas as pd
import os
import json
import sqlite3
from pathlib import Path

def combine_csv_files(input_dir="../data/data_raw_reports",
                      output_file="../data/consolidated_reports.csv"):
    """
    Combines multiple CSV files in the specified directory into a single DataFrame.

    Parameters:
        input_dir (str): Directory containing the CSV files. Default is "data/data_raw_reports".
        output_file (str, optional): Path to save the combined CSV file. Default is "data/consolidated_reports.csv".

    Returns:
        pd.DataFrame: Combined DataFrame from all CSV files and saved as csv to output_file.
    """

    # Initialize an empty list to hold DataFrames
    combined_data = []

    # Iterate over all files in the input directory
    for file in os.listdir(input_dir):
        if file.endswith('_Tipo2_RelatorioT.csv'):
            # Read each CSV file into a DataFrame
            df = pd.read_csv(os.path.join(input_dir, file))
            combined_data.append(df)

    # Combine all DataFrames into a single DataFrame
    combined_df = pd.concat(combined_data, ignore_index=True)

    # Remove duplicates identical rows
    combined_df = combined_df.drop_duplicates()

    # Save the combined DataFrame to a CSV file if output_file is provided
    if output_file:
        combined_df.to_csv(output_file, encoding='utf-8', index=False)
        print(f"Combined data saved to {output_file}")

    return combined_df



def transform_data(
    input_data_path="../data/consolidated_reports.csv",
    output_data_path="../data/consolidated_cleaned.csv"
):
    # Load the data
    df = pd.read_csv(input_data_path, dtype={'CodInst': str}, encoding='utf-8')

    # Convert Saldo from Brazilian format (comma as decimal separator) to decimal
    df['Saldo'] = df['Saldo'].str.replace(',', '.').astype(float)
    df['Saldo'] = df['Saldo'].round(2)

    # Convert AnoMes to datetime and create new columns for month and quarter
    df['AnoMes'] = pd.to_datetime(df['AnoMes'].astype(str), format='%Y%m')
    df['AnoMes_M'] = df['AnoMes'].dt.to_period('M')
    df['AnoMes_Q'] = df['AnoMes'].dt.to_period('Q')
    df['AnoMes_Y'] = df['AnoMes'].dt.to_period('Y')

    # Drop NaN Saldo
    df = df[df['Saldo'].notna()]

    #Replace all NaN values in 'Grupo'to 'nagroup'
    df['Grupo'] = df['Grupo'].fillna('nagroup')

    # Convert CodInst to string
    df['CodInst'] = df['CodInst'].astype(str)

    # Pad values to 8 digits
    df['CodInst'] = df['CodInst'].str.zfill(8)

    # Create a columns appending NomeRelatorio, Grupo & NomeColuna
    df['NomeRelatorio_Grupo_Coluna'] = df['NomeRelatorio'] + '_' + df['Grupo'] + '_' + df['NomeColuna']

    # Load consolidated_institutions.json to add NomeInstituicao to the dataframe
    consolidated_institutions = pd.read_json("../data/consolidated_institutions.json")
    #Filter the dictionary for only CodInst and NomeInstituicao
    consolidated_institutions = consolidated_institutions[['CodInst','NomeInstituicao']]

    # Enforce CodInst to string in both dataframes
    df['CodInst'] = df['CodInst'].astype(str)
    consolidated_institutions['CodInst'] = consolidated_institutions['CodInst'].astype(str)


    # Add NomeInstituicao to df
    df = df.merge(consolidated_institutions, on='CodInst', how='left')


    # Save the transformed data to a CSV file
    df.to_csv(output_data_path, encoding='utf-8', index=False)
    print(f"Transformed data saved to {output_data_path}")


    return df


#----------------------------------------------------------------------------

def make_cred_pf_df(
    input_data_path="../data/consolidated_cleaned.csv",
    output_data_path="../data/cred_pf.csv"
):
    """
    Filter the complete dataset to only the features related to Totals of PF credit (report 11)
    and save the filtered data as a smaller csv file.

    Parameters:
        input_data_path (str): Path to input CSV file. Default "../data/consolidated_cleaned.csv"
        output_data_path (str): Path to save filtered CSV file. Default "../data/cred_pf.csv"

    Returns:
        pd.DataFrame: DataFrame containing only credit data for individuals (PF), filtered for:
            - Report number 11 (Carteira de crédito ativa Pessoa Física)
            - Only total values ('Total da Carteira de Pessoa Física', 'Total')
    """
    # Load the data from input_data_path
    df_clean = pd.read_csv(input_data_path, dtype={'CodInst': str}, encoding='utf-8')

    # Filter for PF Credit report (11) and keep only totals
    cred_pf_df = df_clean[df_clean['NumeroRelatorio'] == 11]
    cred_pf_df = cred_pf_df[cred_pf_df['NomeColuna'].isin(['Total da Carteira de Pessoa Física', 'Total'])]

    # Save the filtered data to CSV
    cred_pf_df.to_csv(output_data_path, encoding='utf-8', index=False)
    print(f"PF Credit data saved to {output_data_path}")

    return cred_pf_df

#----------------------------------------------------------------------------

def make_cred_pj_df(
    input_data_path="../data/consolidated_cleaned.csv",
    output_data_path="../data/cred_pj.csv"
):
    """
    Filter the complete dataset to only the features related to PJ credit (report 13)
    and save the filtered data as a smaller csv file.

    Parameters:
        input_data_path (str): Path to input CSV file. Default "../data/consolidated_cleaned.csv"
        output_data_path (str): Path to save filtered CSV file. Default "../data/cred_pj.csv"

    Returns:
        pd.DataFrame: DataFrame containing only credit data for companies (PJ), filtered for:
            - Report number 13 (Carteira de crédito ativa Pessoa Jurídica)
            - Only total values ('Total da Carteira de Pessoa Jurídica', 'Total')
    """
    # Load the data from input_data_path
    df_clean = pd.read_csv(input_data_path, dtype={'CodInst': str}, encoding='utf-8')

    # Filter for PJ Credit report (13,14) and keep only totals
    cred_pj_df = df_clean[df_clean['NumeroRelatorio'].isin([13,14])]
    cred_pj_df = cred_pj_df[cred_pj_df['NomeColuna'].isin(['Total da Carteira de Pessoa Jurídica', 'Total','Grande','Média','Pequena','Micro'])]

    # Save the filtered data to CSV
    cred_pj_df.to_csv(output_data_path, encoding='utf-8', index=False)
    print(f"PJ Credit data saved to {output_data_path}")

    return cred_pj_df

#----------------------------------------------------------------------------

def make_credit_data_df(cred_pf_df_path="../data/cred_pf.csv", cred_pj_df_path="../data/cred_pj.csv",output_path="../data/credit_data.csv"):

    # Load data
    cred_pf_df = pd.read_csv(cred_pf_df_path)
    cred_pj_df = pd.read_csv(cred_pj_df_path)

    # Combine dataframes
    df = pd.concat([cred_pf_df, cred_pj_df])

    # Save to CSV
    df.to_csv(output_path, encoding='utf-8', index=False)
    print(f"Credit data saved to {output_path}")

    return df


#----------------------------------------------------------------------------


def make_market_metrics_df(
    input_data_path="../data/consolidated_cleaned.csv",
    output_data_path="../data/market_metrics.csv"
):
    """
    Filter the complete dataset to only the features available for market share analysis
    save the filtered data as a smaller csv file for easier/faster processing

    Parameters:
        input_data_path (str): Path to input CSV file. Default "../data/consolidated_cleaned.csv"
        output_data_path (str): Path to save filtered CSV file. Default "../data/market_metrics.csv"

    Returns:
        pd.DataFrame: DataFrame containing only the following market metrics for each institution:
            - Quantidade de clientes com operações ativas
            - Carteira de Crédito Pessoa Física
            - Carteira de Crédito Pessoa Jurídica
            - Carteira de Crédito Classificada
            - Receitas de Intermediação Financeira
            - Rendas de Prestação de Serviços
            - Captações
            - Lucro Líquido
            - Passivo Captacoes: Depósitos Total
            - Passivo Captacoes: Emissão de Títulos (LCI,LCA,LCF...)
    """
    # Load the data from input_data_path
    df_clean = pd.read_csv(input_data_path, dtype={'CodInst': str}, encoding='utf-8')

    # Dictionary mapping features to their full column names
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

    # Get list of values in feature_name_dict
    feature_long = feature_name_dict.values()

    # Filter the dataframe for all values in feature_long list
    market_metrics_df = df_clean[df_clean['NomeRelatorio_Grupo_Coluna'].isin(feature_long)]

    # Save the filtered data to a CSV file
    market_metrics_df.to_csv(output_data_path, encoding='utf-8', index=False)
    print(f"Transformed data saved to {output_data_path}")

    return market_metrics_df

#----------------------------------------------------------------------------

def make_financial_metrics_df(
    input_data_path="../data/consolidated_cleaned.csv",
    output_data_path="../data/financial_metrics.csv"
):
    """
        Generate financial metrics dataset for each institution and period.

        Parameters:
        -----------
        df_cleaned : pandas.DataFrame
            Input dataframe containing the raw financial data

        Returns:
        --------
        pandas.DataFrame
            DataFrame with financial metrics per institution and period
    """

    import pandas as pd
    # Load data
    df_cleaned = pd.read_csv(input_data_path)
    # Filter for DRE Report
    df_dre = df_cleaned[df_cleaned['NumeroRelatorio'].isin([4])]
    # Filter for Resumo Report
    df_resumo = df_cleaned[df_cleaned['NumeroRelatorio'].isin([1])]
    # Filter for Clientes Report
    df_clientes = df_cleaned[df_cleaned['NumeroRelatorio'].isin([10])]

    #######################################################

    # Within DRE, calculate Receita Operacional

    # Create a new dataframe with the calculated Receita Operacional
    group_cols = [col for col in df_dre.columns if col not in [
        'NomeColuna',
        'Saldo',
        'Grupo',
        'Conta',
        'DescricaoColuna',
        'NomeRelatorio_Grupo_Coluna'
    ]]

    # Calculate Receita Operacional
    receita_operacional = df_dre[df_dre['NomeColuna'].isin([
        'Receitas de Intermediação Financeira \n(a) = (a1) + (a2) + (a3) + (a4) + (a5) + (a6)',
        'Rendas de Prestação de Serviços \n(d1)',
        'Rendas de Tarifas Bancárias \n(d2)',
        'Outras Receitas Operacionais \n(d7)'
    ])].groupby(group_cols)['Saldo'].sum().reset_index()

    # Add constant values for NomeColuna and dependencies
    receita_operacional['NomeColuna'] = 'Receita Operacional'
    receita_operacional['Grupo'] = 'Calculated'
    receita_operacional['Conta'] = 'Calculated'
    receita_operacional['DescricaoColuna'] = 'Receita Intermediação Financeira + Rendas de Prestação de Serviços + Rendas de Tarifas Bancárias + Outras Receitas Operacionais'
    receita_operacional['NomeRelatorio_Grupo_Coluna'] = 'Calculated_Receita Operacional'

    # Append to original dataframe
    df_dre = pd.concat([df_dre, receita_operacional], ignore_index=True)

    #######################################################
    # Create grouping columns list
    group_cols = [col for col in df_resumo.columns if col not in [
        'NomeColuna',
        'Saldo',
        'Grupo',
        'Conta',
        'DescricaoColuna',
        'NomeRelatorio_Grupo_Coluna'
    ]]

    # Create pivot table to make calculations easier
    df_pivot = df_resumo.pivot_table(
        index=group_cols,
        columns='NomeColuna',
        values='Saldo',
        aggfunc='first'
    ).reset_index()

    # Calculate ROA and ROE
    ratios = df_pivot.copy()
    ratios['ROA'] = ratios['Lucro Líquido'] / ratios['Ativo Total']
    ratios['ROE'] = ratios['Lucro Líquido'] / ratios['Patrimônio Líquido']

    # Melt the ratios back to long format
    ratios_melted = pd.melt(
        ratios,
        id_vars=group_cols,
        value_vars=['ROA', 'ROE'],
        var_name='NomeColuna',
        value_name='Saldo'
    )

    # Add the additional columns
    ratios_melted['Grupo'] = 'Calculated'
    ratios_melted['Conta'] = 'Calculated'
    ratios_melted['DescricaoColuna'] = ratios_melted['NomeColuna'].map({
        'ROA': 'Return on Assets (Lucro Líquido / Ativo Total)',
        'ROE': 'Return on Equity (Lucro Líquido / Patrimônio Líquido)'
    })
    ratios_melted['NomeRelatorio_Grupo_Coluna'] = 'Calculated_' + ratios_melted['NomeColuna']

    # Append to original dataframe
    df_resumo = pd.concat([df_resumo, ratios_melted], ignore_index=True)

    # Filter for active clients only
    df_clientes = df_clientes[df_clientes['NomeColuna'] == 'Quantidade de clientes com operações ativas']


    # Create financial metrics dataframe appending df_dre and df_resumo already with the calculated metrics + df_clientes for the number of clients.
    financial_metrics_df = pd.concat([df_dre, df_resumo,df_clientes], ignore_index=True)

    # Save the filtered data to a CSV file
    financial_metrics_df.to_csv(output_data_path, encoding='utf-8', index=False)
    print(f"Transformed data saved to {output_data_path}")

    return financial_metrics_df


#----------------------------------------------------------------------------

def initialize_financial_components():
    """
    Initialize dictionaries containing the financial component definitions for different waterfall charts.

    Returns:
    --------
    dict: Dictionary containing three component mappings:
        - revenue_buildup: Components for revenue build-up chart
        - pl_decomposition: Components for P&L breakdown chart
        - intermediation_breakdown: Components for financial intermediation breakdown
    """
    # Define aggregation buckets
    revenue_aggregations = {
        'Outras Receitas Intermediação': [
            'Rendas de Operações de Arrendamento Mercantil \n(a2)',
            'Rendas de Operações com Instrumentos Financeiros Derivativos \n(a4)',
            'Resultado de Operações de Câmbio \n(a5)',
            'Rendas de Aplicações Compulsórias \n(a6)'
        ]
    }

    # Define components for build-up waterfall with aggregations
    revenue_buildup = {
        'Rendas de Operações de Crédito \n(a1)':
            ['Receita de Crédito', 'relative'],
        'Rendas de Operações com TVM \n(a3)':
            ['Receita TVM', 'relative'],
        'Outras Receitas Intermediação':
            ['Outras Rec. Intermediação', 'relative'],
        'Rendas de Prestação de Serviços \n(d1)':
            ['Receita Serviços', 'relative'],
        'Rendas de Tarifas Bancárias \n(d2)':
            ['Receita Tarifas', 'relative'],
        'Outras Receitas Operacionais \n(d7)':
            ['Outras Receitas Operacionais', 'relative'],
        'Receita Operacional':
            ['Receita Operacional Total', 'total']
    }

    # Define components for decomposition waterfall
    pl_decomposition = {
        'Receita Operacional':
            ['Receita Operacional', 'relative'],
        'Despesas de Intermediação Financeira \n(b) = (b1) + (b2) + (b3) + (b4) + (b5)':
            ['Despesas Intermediação', 'relative'],
        'Despesas de Pessoal \n(d3)':
            ['Despesas Pessoal', 'relative'],
        'Despesas Administrativas \n(d4)':
            ['Despesas Admin', 'relative'],
        'Despesas Tributárias \n(d5)':
            ['Despesas Tribut', 'relative'],
        'Outras Despesas Operacionais \n(d8)':
            ['Outras Despesas', 'relative'],
        'Lucro Líquido \n(j) = (g) + (h) + (i)':
            ['Lucro Líquido', 'total']
    }

    # Define components for intermediation breakdown
    intermediation_breakdown = {
        'Receitas de Intermediação Financeira \n(a) = (a1) + (a2) + (a3) + (a4) + (a5) + (a6)':
            ['Receita Intermediação', 'relative'],
        'Despesas de Captação \n(b1)':
            ['Despesas Captação', 'relative'],
        'Despesas de Obrigações por Empréstimos e Repasses \n(b2)':
            ['Despesas Empréstimos', 'relative'],
        'Despesas de Operações de Arrendamento Mercantil \n(b3)':
            ['Despesas Arrend.', 'relative'],
        'Resultado de Operações de Câmbio \n(b4)':
            ['Resultado Câmbio', 'relative'],
        'Resultado de Provisão para Créditos de Difícil Liquidação \n(b5)':
            ['Provisão Créditos Difícil Liquidação', 'relative'],
        'Resultado de Intermediação Financeira \n(c) = (a) + (b)':
            ['Resultado Intermediação', 'total']
    }

    return {
        'revenue_buildup': revenue_buildup,
        'pl_decomposition': pl_decomposition,
        'intermediation_breakdown': intermediation_breakdown,
        'revenue_aggregations': revenue_aggregations
    }

#----------------------------------------------------------------------------




def process_financial_metrics2(
    input_data_path="../data/financial_metrics.csv",
    output_data_path="../data/financial_metrics_processed.csv"
):
    """
    Processes financial metrics for banking data to create pre-calculated values
    suitable for waterfall charts and financial performance analysis.

    Parameters:
    -----------
    input_data_path : str
        Path to the input CSV file containing raw financial metrics.
    output_data_path : str
        Path to save the processed financial metrics CSV file.

    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the processed financial metrics with the following:
        - Absolute financial values for each component.
        - Percentage of revenue for each component.
        - Per-client metrics.
    """
    # Load data with low_memory=False to avoid DtypeWarning
    df = pd.read_csv(input_data_path, dtype={
        'AnoMes': str,
        'AnoMes_M': str,
        'AnoMes_Q': str,
        'Grupo': str,
        'Conta': str
    }, low_memory=False)

    # Convert AnoMes to datetime for proper sorting
    df['AnoMes'] = pd.to_datetime(df['AnoMes'])
    #Reasign AnoMes_Q as period Q datatype
    df['AnoMes_Q'] = df['AnoMes'].dt.to_period('Q')


    # Filter out rows where revenue or number of clients is insufficient
    # Compute the sums per institution and period
    revenue_check = (
        df[df['NomeColuna'] == 'Receita Operacional']
        .groupby(['NomeInstituicao', 'AnoMes_Q', 'AnoMes'])['Saldo'].sum()
    )
    clients_check = (
        df[df['NomeColuna'] == 'Quantidade de clientes com operações ativas']
        .groupby(['NomeInstituicao', 'AnoMes_Q', 'AnoMes'])['Saldo'].sum()
    )

    # Identify valid records where both revenue and client counts are sufficient
    valid_entries = (revenue_check > 1) & (clients_check > 1)
    valid_entries = valid_entries[valid_entries].index

    # Filter the main dataset based on valid entries
    df = df[df.set_index(['NomeInstituicao', 'AnoMes_Q', 'AnoMes']).index.isin(valid_entries)]

    # Define aggregation buckets for combining multiple components into summary metrics
    AGGREGATION_BUCKETS = {
        'Outras Receitas Intermediação': [
            'Rendas de Operações de Arrendamento Mercantil \n(a2)',
            'Rendas de Operações com Instrumentos Financeiros Derivativos \n(a4)',
            'Resultado de Operações de Câmbio \n(a5)',
            'Rendas de Aplicações Compulsórias \n(a6)'
        ]
    }

    # Define the components to be included in different types of waterfall charts
    COMPONENTS = {
        'revenue_buildup': [
            'Rendas de Operações de Crédito \n(a1)',
            'Rendas de Operações com TVM \n(a3)',
            'Outras Receitas Intermediação',
            'Rendas de Prestação de Serviços \n(d1)',
            'Rendas de Tarifas Bancárias \n(d2)',
            'Outras Receitas Operacionais \n(d7)',
            'Receita Operacional'
        ],
        'pl_decomposition': [
            'Receita Operacional',
            'Despesas de Intermediação Financeira \n(b) = (b1) + (b2) + (b3) + (b4) + (b5)',
            'Despesas de Pessoal \n(d3)',
            'Despesas Administrativas \n(d4)',
            'Despesas Tributárias \n(d5)',
            'Outras Despesas Operacionais \n(d8)',
            'Lucro Líquido \n(j) = (g) + (h) + (i)'
        ],
        'store_receita_qtd_clientes': [
            'Receita Operacional',
            'Quantidade de clientes com operações ativas'
        ],
        'intermediation_breakdown': [
            'Receitas de Intermediação Financeira \n(a) = (a1) + (a2) + (a3) + (a4) + (a5) + (a6)',
            'Despesas de Captação \n(b1)',
            'Despesas de Obrigações por Empréstimos e Repasses \n(b2)',
            'Despesas de Operações de Arrendamento Mercantil \n(b3)',
            'Resultado de Operações de Câmbio \n(b4)',
            'Resultado de Provisão para Créditos de Difícil Liquidação \n(b5)',
            'Resultado de Intermediação Financeira \n(c) = (a) + (b)'
        ]
    }

    # Create separate DataFrames for clients and revenue
    clients_df = df[
        df['NomeColuna'] == 'Quantidade de clientes com operações ativas'
    ].copy()

    revenue_df = df[
        df['NomeColuna'] == 'Receita Operacional'
    ].copy()

    # Convert filtered data into dictionaries for faster lookup by institution and period
    clients_dict = clients_df.set_index(['NomeInstituicao', 'AnoMes_Q','AnoMes'])['Saldo'].to_dict()
    revenue_dict = revenue_df.set_index(['NomeInstituicao', 'AnoMes_Q','AnoMes'])['Saldo'].to_dict()

    # Initialize an empty list to store the results of the data processing for each institution and period
    results = []
    # Group data by institution, quarterly period, and monthly period
    for (inst, period, anomes), group in df.groupby(['NomeInstituicao', 'AnoMes_Q','AnoMes']):
        # Convert the group's values to a dictionary for easier processing base metrics
        metrics = group.set_index('NomeColuna')['Saldo'].to_dict()

        # Group data by institution, quarterly period, and monthly period
        for agg_name, components in AGGREGATION_BUCKETS.items():
            metrics[agg_name] = sum(metrics.get(comp, 0) for comp in components)

        # Get number of active clients and revenue using dictionary lookup per period
        num_clients = float(clients_dict.get((inst, period, anomes), 1))
        receita_op = float(revenue_dict.get((inst, period, anomes), 1))

        # Calculate all three formats for each component
        # Process each financial component and calculate absolute, percentage, and per-client metrics

        for component_type, components in COMPONENTS.items():
            for comp in components:
                value = float(metrics.get(comp, 0))

                # Calculate metrics
                # Calculate the percentage of revenue if revenue is non-zero

                if receita_op > 1:
                    percent_revenue = (value / receita_op) * 100
                else:
                    percent_revenue = 0

                # Calculate the value per client if clients exist
                if num_clients > 1:
                    per_client = value / num_clients
                else:
                    per_client = 0

                # Append the calculated metrics to the results list
                results.append({
                    'NomeInstituicao': inst,
                    'AnoMes_Q': period,
                    'AnoMes': anomes,
                    'ComponentType': component_type,
                    'Component': comp,
                    'ValueAbsolute': value,
                    'ValuePercentRevenue': percent_revenue,
                    'ValuePerClient': per_client,
                    'NumClients': num_clients,
                    'ReceitaOperacional': receita_op
                })

    # Convert to DataFrame
    result_df = pd.DataFrame(results)

    # Save processed data
    result_df.to_csv(output_data_path, index=False)
    print(f"Processed data saved to {output_data_path}")

    return result_df

#----------------------------------------------------------------------------


def save_to_sqlite(db_path="../data/bacen_data.db", additional_files=None):
    """
    Saves multiple data files to a SQLite database.

    Parameters:
        db_path (str): Path to the SQLite database file.
        additional_files (dict, optional): Dictionary of additional files to save
            in format {'table_name': 'file_path'}

    Returns:
        None
    """
    # Default files to save
    default_files = {
        'consolidated_reports': '../data/consolidated_cleaned.csv',
        'institutions': '../data/consolidated_institutions.json',
        'credit_pf': '../data/cred_pf.csv',
        'credit_pj': '../data/cred_pj.csv',
        'market_metrics': '../data/market_metrics.csv'
    }

    # Combine default_files with any additional files
    files_to_save = default_files.copy()
    if additional_files:
        files_to_save.update(additional_files)

    # Connect to SQLite database (create if it doesn't exist)
    conn = sqlite3.connect(db_path)

    try:
        # Process each file
        for table_name, file_path in files_to_save.items():
            if not Path(file_path).exists():
                print(f"Warning: File {file_path} not found, skipping...")
                continue

            # Read the file based on its extension
            if file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:  # csv files
                df = pd.read_csv(file_path, dtype={'CodInst': str}, encoding='utf-8')

            # Save DataFrame to SQLite table
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"Data from {file_path} saved to table '{table_name}'")

    finally:
        conn.close()
        print(f"All data saved to database {db_path}")


#----------------------------------------------------------------------------

# Make the script runnable
if __name__ == "__main__":
    # Step 1: Combine all raw CSV files into one consolidated report
    combined_df = combine_csv_files()

    # Step 2: Transform data to clean version
    clean_df = transform_data()

    # Step 3: Create specialized datasets
    cred_pf_df = make_cred_pf_df()
    cred_pj_df = make_cred_pj_df()
    market_metrics_df = make_market_metrics_df()

    # Step 4: Create financial_metrics_df (when implemented)
    financial_metrics_df = make_financial_metrics_df()

    # Step 5: Save all data to SQLite
    save_to_sqlite()

    print("ETL process completed successfully!")
