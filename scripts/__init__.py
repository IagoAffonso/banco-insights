"""
BACEN Insights Scripts
---------------------
Collection of data processing and visualization functions for Brazilian Central Bank (BACEN) data.
"""

__version__ = "1.0.0"
__author__ = "Iago Affonso"
__email__ = "iagoaffonso21@gmail.com"

# Import main functions from modules
from .plotting import (
    plot_market_share,
    plot_share_credit_modality,
    plot_credit_portfolio
)

from .etl import (
    combine_csv_files,
    transform_data,
    make_cred_pf_df,
    make_cred_pj_df,
    make_market_metrics_df,
    save_to_sqlite
)

from .fetch_data import (
    download_historical_data,
    get_consolidated_institutions
)

# Define what should be available when using "from scripts import *"
__all__ = [
    # Plotting functions
    'plot_market_share',
    'plot_share_credit_modality',
    'plot_credit_portfolio',

    # ETL functions
    'combine_csv_files',
    'transform_data',
    'make_cred_pf_df',
    'make_cred_pj_df',
    'make_market_metrics_df',
    'save_to_sqlite',

    # Data fetching functions
    'download_historical_data',
    'get_consolidated_institutions'
]
