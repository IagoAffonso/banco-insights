# Imports
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd
from typing import List, Optional, Union
from google.cloud import storage
import os
import json
from google.oauth2 import service_account
import logging


################
# Use relative import of plotting functions
from scripts.plotting import plot_market_share, plot_share_credit_modality, plot_credit_portfolio, plot_time_series
from scripts.plotting_financial_waterfall import plot_waterfall_agg, create_waterfall, filter_agg


# Add logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

####################### Initialize FastAPI app
app = FastAPI()

#######################

def get_credentials():
    """Get credentials from service account file"""
    if os.path.exists('key.json'):
        return service_account.Credentials.from_service_account_file('key.json')
    return None



def load_gcs_data(bucket_name, file_name):
    """Load data from Google Cloud Storage"""
    try:
        logger.info(f"Attempting to load {file_name} from bucket {bucket_name}")

        credentials = get_credentials()

        if credentials:
            logger.info("Using local service account credentials")
            client = storage.Client(credentials=credentials)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(file_name)

            # Download to temporary file
            temp_file = f"/tmp/{file_name}"
            blob.download_to_filename(temp_file)

            # Read with pandas
            df = pd.read_csv(temp_file)

            # Clean up
            os.remove(temp_file)

            logger.info(f"Successfully loaded {file_name} with shape {df.shape}")
            return df
        else:
            logger.info("Using default Cloud Run credentials")
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(file_name)

            # Download to temporary file
            temp_file = f"/tmp/{file_name}"
            blob.download_to_filename(temp_file)

            # Read with pandas
            df = pd.read_csv(temp_file)

            # Clean up
            os.remove(temp_file)

            logger.info(f"Successfully loaded {file_name} with shape {df.shape}")
            return df

    except Exception as e:
        error_msg = f"Error loading {file_name} from {bucket_name}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)



################################
# Load dataframes from GCS
# Global variables to store dataframes
bucket_name = 'bacen-project-data'
try:
    # Load main dataframes
    df_market_metrics = load_gcs_data(bucket_name, 'market_metrics.csv')
    credit_data_df = load_gcs_data(bucket_name, 'credit_data.csv')
    df_fmp = load_gcs_data(bucket_name, 'financial_metrics_processed.csv')
    financial_metrics_df = load_gcs_data(bucket_name, 'financial_metrics.csv')

    # Load additional credit dataframes
    #df_cred_pf = load_gcs_data(bucket_name, 'cred_pf.csv')
    #df_cred_pj = load_gcs_data(bucket_name, 'cred_pj.csv')



    logger.info("All dataframes loaded and processed successfully")

except Exception as e:
    error_msg = f"Failed to load or process dataframes: {str(e)}"
    logger.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)


#app = FastAPI()

# Global variables to store dataframes
#df_market_metrics = pd.read_csv('../data/market_metrics.csv')
#credit_data_df = pd.read_csv('../data/credit_data.csv')
#df_fmp = pd.read_csv('../data/financial_metrics_processed.csv')
#financial_metrics_df = pd.read_csv('../data/financial_metrics.csv')

#df_cred_pf = pd.read_csv('../data/cred_pf.csv')
#df_cred_pj = pd.read_csv('../data/cred_pj.csv')

#Translation dictionaries to portuguese
view_type_reverse = {
    "Valor Absoluto": "ValueAbsolute",
    "% Receita Operacional": "ValuePercentRevenue",
    "Por Cliente Trimestre": "ValuePerClient"
}

chart_type_reverse = {
    "Breakdown da Receita": "revenue_buildup",
    "Breakdown do P&L": "pl_decomposition",
    "Breakdown do Resultado de Intermediação Financeira": "intermediation_breakdown"
}


# NO LONGER NEEDED , WILL BREAK THE CODE. Convert date columns for all dataframes
#for df in [df_market_metrics, df_cred_pf, df_cred_pj, credit_data_df, df_fmp]:
    # Convert AnoMes from '2014-12-01' format
    #df['AnoMes'] = pd.to_datetime(df['AnoMes'], format='%Y-%m-%d')

    # Convert AnoMes_Q from '2014Q4' format
    #df['AnoMes_Q'] = pd.PeriodIndex(df['AnoMes_Q'], freq='Q')



# Define a root `/` endpoint
@app.get('/')
def index():
    return {'Hello': "Welcome to BACEN Insights API",
            'status': 'ok'}


#------------------------------

#Plotting endpoints


@app.get("/plot/market_share")
def get_market_share_plot(
    feature: str = Query(default='Quantidade de clientes com operações ativas'),
    top_n: int = Query(default=10),
    initial_year: Optional[int] = Query(default=None,description='Ano inicial para plotagem'),
    drop_nubank: int = Query(default=0),
    custom_selected_institutions: Optional[List[str]] = Query(default=None)
):
    try:
        # Ensure custom_selected_institutions is None or a list
        if custom_selected_institutions == []:
            custom_selected_institutions = None

        # Call the imported function
        fig = plot_market_share(
            df=df_market_metrics,
            feature=feature,
            top_n=top_n,
            initial_year=initial_year,
            drop_nubank=drop_nubank,
            custom_selected_institutions=custom_selected_institutions
        )

        fig_json = fig.to_json()
        return {"figure_json": fig_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/plot/share_credit_modality")
def api_plot_share_credit_modality(
    modalities: List[str] = Query(
        default=["Total PF", "Total PJ"],
        description="List of credit modalities to analyze",
        examples=["Rural PF", "Rural PJ"],
        openapi_extra={
            "valid_options": [
                "Total PF", "Consignado PF", "Não Consignado PF", "Veículos PF",
                "Outros Créditos PF", "Habitação PF", "Cartão de Crédito PF", "Rural PF",
                "Total PJ", "Recebíveis PJ", "Comércio Exterior PJ", "Outros Créditos PJ",
                "Infraestrutura PJ", "Capital de Giro PJ", "Investimento PJ",
                "Capital de Giro Rotativo PJ", "Rural PJ", "Habitação PJ", "Cheque Especial PJ"
            ]
        }
    ),
    initial_year: Optional[int] = Query(default=None,description='Ano inicial para plotagem'),
    top_n: int = Query(default=10,description='Top n instituições a serem plotadas'),
    custom_selected_institutions: Optional[List[str]] = Query(
        default=None,
        description='Plot selected institutions',
        openapi_extra={
            "examples": ["ITAU", "BRADESCO", "SANTANDER"],
        }
    ),
    show_percentage: bool = Query(default=True,description='Show percentage of total')
):
    fig = plot_share_credit_modality(
        credit_data_df=credit_data_df,
        modalities=modalities,
        initial_year=initial_year,
        top_n=top_n,
        custom_selected_institutions=custom_selected_institutions,
        show_percentage=show_percentage
    )

    fig_json = fig.to_json()

    return {"figure_json": fig_json}



@app.get("/plot/credit_portfolio")
def api_plot_credit_portfolio(
    select_institutions: List[str] = Query(
        default=["All"],
        description="Institution(s) to analyze. Use ['All'] for market-wide breakdown or list of institution names",
        examples=["All"],
        openapi_extra={
            "examples": [
                ["All"],
                ["ITAU"],
                ["ITAU", "BRADESCO", "SANTANDER"]
            ]
        }
    ),
    initial_year: Optional[int] = Query(
        default=None,
        description="Starting year for the analysis",
        examples=2020
    ),
    grouped: int = Query(
        default=0,
        description="0: Shows detailed breakdown by modalities, 1: Shows only PF vs PJ breakdown",
        ge=0,
        le=1
    ),
    show_percentage: bool = Query(
        default=True,
        description="If True, shows values as percentage of total. If False, shows absolute values"
    )
):
    # Convert ["All"] to "All" string for the plotting function
    if len(select_institutions) == 1 and select_institutions[0] == "All":
        select_institutions = "All"

    fig = plot_credit_portfolio(
        credit_data_df=credit_data_df,
        select_institutions=select_institutions,
        initial_year=initial_year,
        grouped=grouped,
        show_percentage=show_percentage
    )

    fig_json = fig.to_json()
    return {"figure_json": fig_json}

#------------------------------

@app.get("/plot/dre_waterfall")
def api_plot_dre_waterfall(
    chart_type: str = Query(
        default='Breakdown da Receita',
        description='Tipo do gráfico',
        enum=list(chart_type_reverse.keys())
    ),
    view_type: str = Query(
        default='Valor Absoluto',
        description='Tipo de visualização',
        enum=list(view_type_reverse.keys())
    ),
    periods_list: List[str] = Query(default=['2024Q3'], description='Lista de períodos'),
    institutions_list: List[str] = Query(default=['ITAU'], description='Lista de instituições'),
):
    try:
        # Translate the Portuguese names to internal English names
        internal_chart_type = chart_type_reverse[chart_type]
        internal_view_type = view_type_reverse[view_type]

        # Call the original function with translated parameters
        fig, data = plot_waterfall_agg(
            df_fmp=df_fmp,
            periods_list=periods_list,
            institutions_list=institutions_list,
            chart_type=internal_chart_type,
            view_type=internal_view_type
        )

        return {"figure_json": fig.to_json()}

    except Exception as e:
        print(f"Error in api_plot_dre_waterfall: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#------------------------------

@app.get("/plot/time_series")
def get_time_series_plot(
    control: str = Query(
        ...,  # This means the parameter is required
        description="Tipo de valor a ser visualizado",
        enum=[
            "Valores Absolutos",
            "Valores Relativos por % da Receita Operacional",
            "Valores Relativos por Cliente"
        ]
    ),
    list_institutions: List[str] = Query(
        ...,  # This means the parameter is required
        description=" Lista de instituicoes a serem visualizadas",
        examples=["ITAU", "BRADESCO"]
    ),
    metric_name: str = Query(
        ...,  # This means the parameter is required
        description="Nome da métrica analisada (e.g., ROE, ROA, Lucro Líquido)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Data início para filtro (YYYY-MM-DD format)",
        examples="2020-01-01"
    ),
    end_date: Optional[str] = Query(
        None,
        description="Data fim para filtro (YYYY-MM-DD format)",
        examples="2023-12-31"
    )
):
    """
    Generate a time series plot for financial metrics across selected institutions.
    """
    try:
        fig, plot_data = plot_time_series(
            financial_metrics_df=financial_metrics_df,
            df_fmp=df_fmp,
            control=control,
            list_institutions=list_institutions,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date
        )

        return {"figure_json": fig.to_json()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
