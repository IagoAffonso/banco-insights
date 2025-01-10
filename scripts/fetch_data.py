import os
import time
import requests
import logging
from pathlib import Path
from typing import List
import pandas as pd
import json


def download_historical_data(
    years: List[int],
    months: List[int],
    output_dir="data/data_raw_reports",
    base_url="https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata",
    endpoint_template="/IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)",
    tipo_instituicao=2,
    relatorio="T",
    data_format="text/csv",
    page_size=1000,
    timeout=30,
    max_retries=3
):
    """
    Automates downloading historical data from Bacen Relatorios API, with pagination, retries, and file logging.
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # Setup logging
    logging.basicConfig(filename=os.path.join(output_dir, "download.log"), level=logging.INFO)
    logging.info("Download process started.")

    # Iterate through years and months
    for year in years:
        for month in months:
            period = f"{year}{month:02d}"
            filename = f"data_{period}_Tipo{tipo_instituicao}_Relatorio{relatorio}.csv"
            filepath = os.path.join(output_dir, filename)

            logging.info(f"Downloading data for period {period}...")
            skip = 0
            retry_count = 0
            success = True
            first_page = True

            while True:
                try:
                    # Build endpoint with proper query parameters
                    endpoint = f"{endpoint_template}?@AnoMes={period}&@TipoInstituicao={tipo_instituicao}&@Relatorio='{relatorio}'"

                    # Set up parameters for pagination and format
                    params = {
                        "$top": page_size,
                        "$skip": skip,
                        "$format": data_format
                    }

                    # API Request
                    response = requests.get(base_url + endpoint, params=params, timeout=timeout)
                    response.raise_for_status()

                    # Process response text (skip headers for subsequent pages)
                    if skip > 0:
                        response_text = '\n'.join(response.text.split('\n')[1:])
                    else:
                        response_text = response.text

                    # Write/Append data to file
                    mode = 'w' if first_page else 'a'
                    with open(filepath, mode, encoding="utf-8") as f:
                        f.write(response_text)

                    # Check if pagination is complete
                    if len(response.text.strip()) == 0 or len(response.text.split('\n')) <= 2:  # Only headers or empty
                        break

                    # Increment for next page
                    skip += page_size
                    first_page = False

                    # Add delay between requests to avoid rate limiting
                    time.sleep(1)

                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        success = False
                        logging.error(f"Failed to download {period} after {max_retries} retries: {e}")
                        # Check if it's a server error (500)
                        if hasattr(e.response, 'status_code') and e.response.status_code == 500:
                            logging.error("Server returned 500 error. Stopping further downloads.")
                            print("Server returned 500 error. Stopping further downloads.")
                            return  # Early stop all downloads
                        break
                    logging.warning(f"Retrying {period}... ({retry_count}/{max_retries})")
                    time.sleep(5)  # Longer delay on errors

            # Log successful download
            if success:
                logging.info(f"Successfully downloaded: {filepath}")

    logging.info("Download process completed.")


################################################################################

def get_consolidated_institutions(
    years_list,
    months_list,
    output_dir="data",
    log_level=logging.INFO
):
    """
    Fetches institution data for multiple periods and consolidates them into a single mapping,
    keeping the most recent entry for each CodInst.
    """
    # 1. Setup
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = os.path.join(output_dir, "institutions_consolidation.log")
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logging.info("Starting institution data consolidation process")

    # 2. Data Collection
    # Initialize empty list to store all responses
    all_institutions = []

    # Endpoint for institutions data
    base_url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata"
    endpoint = "/IfDataCadastro(AnoMes=@AnoMes)"

    total_periods = len(years_list) * len(months_list)
    processed_periods = 0
    # 3. Iterate through periods
    for month in months_list:
        for year in years_list:
            period = f"{year}{month:02d}"
            processed_periods += 1

            logging.info(f"Processing period {period} ({processed_periods}/{total_periods})")

            parameters = {
                "@AnoMes": period,
                "$top": "100000",
                "$skip": "0",
                "$format": "json"
            }

            try:
                response = requests.get(base_url + endpoint, params=parameters)
                response.raise_for_status()

                data = response.json()
                if 'value' in data:
                    institutions_count = len(data['value'])
                    all_institutions.extend(data['value'])
                    logging.info(f"Successfully fetched {institutions_count} institutions for period {period}")
                else:
                    logging.warning(f"No 'value' key in response for period {period}")

            except requests.exceptions.RequestException as e:
                logging.error(f"Network error for period {period}: {str(e)}")
                continue
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error for period {period}: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error for period {period}: {str(e)}")
                continue

            time.sleep(0.5)

    if not all_institutions:
        logging.error("No data was collected. Exiting.")
        return None

    logging.info(f"Data collection complete. Processing {len(all_institutions)} total records")

    # Convert to DataFrame and process
    try:
        df = pd.DataFrame(all_institutions)
        df['Data'] = pd.to_numeric(df['Data'])
        df = df.sort_values('Data', ascending=False)

        initial_count = len(df)
        df = df.drop_duplicates(subset='CodInst', keep='first')
        final_count = len(df)

        logging.info(f"Removed {initial_count - final_count} duplicate institutions")

        # Save to JSON file
        output_path = os.path.join(output_dir, "consolidated_institutions.json")
        df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        logging.info(f"Successfully saved consolidated data to: {output_path}")

    except Exception as e:
        logging.error(f"Error during data processing: {str(e)}")
        return None

    logging.info(f"Process completed. Total unique institutions: {len(df)}")
    return df

# Example usage:
# years_list = list(range(2013, 2024+1))
# months_list = [3, 6, 9, 12]
# df = get_consolidated_institutions(years_list, months_list, base_url)


# Main
if __name__ == "__main__":
    years_list = list(range(2013, 2024+1))
    months_list = [3, 6, 9, 12]
    download_historical_data(years_list, months_list)
    get_consolidated_institutions(years_list, months_list)
