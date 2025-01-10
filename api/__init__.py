"""
BACEN Insights API
-----------------
API for Brazilian Central Bank (BACEN) data analysis and visualization.
Provides market share analysis, credit portfolio insights, and financial metrics.
"""

# Import the FastAPI app
from .simple import app

__version__ = "1.0.0"
__author__ = "Iago Affonso"
__email__ = "iagoaffonso21@gmail.com"

# Package-level configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000



def start_server():
    import uvicorn
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)

if __name__ == "__main__":
    start_server()
