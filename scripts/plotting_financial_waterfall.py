import pandas as pd
import numpy as np
import plotly.graph_objects as go

#df_fmp = pd.read_csv("../data/financial_metrics_processed.csv")



# Filter and aggregate
def filter_agg (df_fmp,periods_list, institutions_list, chart_type, view_type):
    """

    Handles user data selection and aggreation and apply to dataframe

    df_fmp: dataframe financial metrics processed

    periods_list: Formatted as ['2024Q3']

    institutions_list: Formatted as ['NUBANK']

    view_types:
    ValueAbsolute
    ValuePercentRevenue
    ValuePerClient

    chart_type:
    revenue_buildup
    pl_decomposition
    intermediation_breakdown

    """

    # Step 1: Filter by institution and period
    df_fmp_f = df_fmp[df_fmp['NomeInstituicao'].isin(institutions_list)]
    df_fmp_f = df_fmp_f[df_fmp_f['AnoMes_Q'].isin(periods_list)]

    # Step 2: Retrieve Total Receita Operacional and Total Clientes for the filtered data
    total_revenue = df_fmp_f.loc[
        (df_fmp_f['ComponentType'] == 'store_receita_qtd_clientes') &
        (df_fmp_f['Component'] == 'Receita Operacional'),
        'ValueAbsolute'
    ].sum()

    total_clientes = df_fmp_f.loc[
        (df_fmp_f['ComponentType'] == 'store_receita_qtd_clientes') &
        (df_fmp_f['Component'] == 'Quantidade de clientes com operações ativas'),
        'ValueAbsolute'
    ].sum()


    # Step 3: Filter for specific chart_type (i.e. revenue buildup, pl_decomposition etc)
    df_fmp_f = df_fmp_f[df_fmp_f['ComponentType'].isin([chart_type])]


    # Step 4: Identify if multiple institutions or periods are present
    multiple_entities = len(df_fmp_f['NomeInstituicao'].unique()) > 1 or len(df_fmp_f['AnoMes_Q'].unique()) > 1

    # Conditional aggregation based on view_types

    if view_type == 'ValueAbsolute':
        # Simply sum ValueAbsolute across institutions and periods for plotting
        df_fmp_f_agg = df_fmp_f.drop(columns=['ValuePercentRevenue','ValuePerClient'])
        df_fmp_f_agg = df_fmp_f.groupby('Component').sum().reset_index()
        df_fmp_f_agg['Saldo'] = df_fmp_f_agg['ValueAbsolute']
        #print("✅ Calculated ValueAbsolute for all components.")

    elif view_type == 'ValuePercentRevenue':

        # Direct Calculation for a Single Institution and Period
        if not multiple_entities:
            df_fmp_f_agg = df_fmp_f.copy()
            df_fmp_f_agg['Saldo'] = df_fmp_f_agg['ValuePercentRevenue']
            print("✅ Calculating direct percentages for a single institution/period.")

        # Proper Weighted Calculation Using ValueAbsolute (Corrected Formula)
        else:
            # Sum the numerators separately for Components all institutions and periods
            sum_saldo_groupedby_component = df_fmp_f.groupby('Component')['ValueAbsolute'].sum()

            # Calculate the percentage of revenue as a standardized 'Saldo' column
            df_fmp_f_agg = (sum_saldo_groupedby_component / total_revenue) * 100
            df_fmp_f_agg = df_fmp_f_agg.reset_index(name='Saldo')
            print("✅ Calculating percentage based on total ValueAbsolute and ReceitaOperacional.")

        # Step 5: Validate the Results (Should Sum to 100% or 200%)
        total_percent = df_fmp_f_agg['Saldo'].sum()
        print(f"✅ Total Percent Revenue Calculated: {total_percent}%")
        if not (99.9 <= total_percent <= 200.1):
            print("⚠️ Warning: The percentages do not sum correctly!")


    elif view_type == 'ValuePerClient':


        # Direct Calculation for a Single Institution and Period
        if not multiple_entities:
            df_fmp_f_agg = df_fmp_f.copy()
            df_fmp_f_agg['Saldo'] = df_fmp_f_agg['ValuePerClient']
            print("✅ Calculating direct values for a single institution/period.")

        # Proper Weighted Calculation Using ValueAbsolute
        else:
            # Sum the numerators separately for Components all institutions and periods
            sum_saldo_groupedby_component = df_fmp_f.groupby('Component')['ValueAbsolute'].sum()

            # Calculate the average metric per customeras a standardized 'Saldo' column
            df_fmp_f_agg = (sum_saldo_groupedby_component / total_clientes)
            df_fmp_f_agg = df_fmp_f_agg.reset_index(name='Saldo')
            print("✅ Calculating metric per quarter per customer based on total ValueAbsolute and # Customers.")

    else:
        print("Invalid Selection")

    stored_params = [periods_list,institutions_list,chart_type,view_type]

    return (df_fmp_f_agg,stored_params)

#-------------------------------------------------------------------------------


def create_waterfall(df_fmp_f_agg, stored_params):
    """Creates a waterfall chart using Plotly with debugging prints."""

    # Import financial components for ordering and mapping
    try:
        from scripts.etl import initialize_financial_components
        components_dict = initialize_financial_components()
        #print("Components successfully imported.")
    except ImportError:
        print("Warning: Could not import initialize_financial_components. Using an empty dictionary.")
        components_dict = {}

    # Ensure the dictionary is populated
    if not components_dict:
        print("Warning: components_dict is empty. Labels and measures will be defaulted.")

    # Extracting stored parameters
    periods_list = stored_params[0]
    institutions_list = stored_params[1]
    chart_type = stored_params[2]
    view_type = stored_params[3]

    #print(f"Stored Parameters: {stored_params}")

    # Validate the chart type and access the correct nested dictionary
    if chart_type not in components_dict:
        print(f"Error: Chart type '{chart_type}' not found in components_dict.")
        return None, None

    # Fetch the correct component dictionary for the specified chart type
    chart_components = components_dict[chart_type]
    #print(f"Chart components loaded for: {chart_type}")

    # Order data according to the component dictionary
    data = df_fmp_f_agg

    data = df_fmp_f_agg.sort_values(
    by='Component',
    key=lambda col: col.map(lambda x: list(chart_components.keys()).index(x)
                            if x in chart_components else float('inf'))).reset_index(drop=True)



    # Testing
    # print(data.head(10))


    # Safe access to labels and measures
    labels = [chart_components.get(item, [item, ''])[0] for item in data['Component']]
    measures = [chart_components.get(item, [item, 'absolute'])[1] for item in data['Component']]

    # Debugging prints to verify label and measure creation
    #print(f"Generated Labels: {labels[:5]}")
    #print(f"Generated Measures: {measures[:5]}")

    import plotly.graph_objects as go

    # Improved title customization in Portuguese for the financial waterfall chart
    title_dict = {
        "revenue_buildup": "Breakdown da Receita",
        "pl_decomposition": "Breakdown do P&L",
        "intermediation_breakdown": "Breakdown do Resultado de Intermediação Financeira"
    }

    chart_type_dict = {
        "revenue_buildup": "Breakdown da Receita",
        "pl_decomposition": "Breakdown do P&L",
        "intermediation_breakdown": "Breakdown do Resultado de Intermediação Financeira"
    }

    #print(title_dict)

    # Portuguese translation for view types
    view_type_translation = {
        "ValueAbsolute": "Valor Absoluto",
        "ValuePercentRevenue": "% Receita Operacional",
        "ValuePerClient": "Por Cliente Trimestre"
    }



    # Build a dynamic title with fallback handling for unexpected keys
    title_chart = title_dict.get(chart_type, chart_type)

    title_view = view_type_translation.get(view_type, view_type)


    # Final title combining both elements and the institution list for clarity
    title = f"{title_chart} - {title_view} - {', '.join(institutions_list)}"



    # Configure the waterfall chart with corrected hover text (no duplication)
    # ✅ Configure the Plotly Waterfall Chart (Default Styling)
    fig = go.Figure(go.Waterfall(
        name=f"{title}",
        orientation="v",
        measure=measures,
        x=labels,
        y=data['Saldo'].round(2).values,
        text=[f"{x:,.0f}" for x in data['Saldo']],  # Rounded and formatted
        textfont=dict(size=10, family="OpenSans"),
        textposition="outside",
        connector=dict(mode="between", line=dict(color="rgb(200,200,200)", width=1))
    ))

    # ✅ Use Plotly's Default Font and Size
    fig.update_layout(
        title=f"{title}",
        showlegend=False,
        height=600,
        width=800,
        xaxis=dict(
            title="",
            tickangle=45,
            automargin=True,
        ),
        yaxis=dict(
            title="Value",
            tickformat=",",  # Thousand separator on the axis
        ),
        hovermode="closest"  # Hover shows all data for the same x-axis value
    )

    #print("Waterfall chart created successfully!")
    return fig, data




#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------

def plot_waterfall_agg(df_fmp, periods_list, institutions_list,chart_type,view_type):
    """Plot aggregated waterfall for a given period list, institution list, chart type and view type"""
    df_fmp_f_agg,stored_params = filter_agg (df_fmp, periods_list, institutions_list,chart_type,view_type)
    fig, data = create_waterfall(df_fmp_f_agg,stored_params)

    return fig, data
