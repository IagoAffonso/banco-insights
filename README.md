Project Overview

Objective
To develop a simple yet powerful web application that generates market intelligence and benchmarks for the Brazilian banking sector, offering:

Interactive dashboards built on Bacen data.
A quarterly newsletter with AI-generated insights on market trends and banking performance.

-------------------------------------------------------------------------------


Pipeline

1. Data Collection
Scripts to Fetch Data:
Automated scripts fetch data from the Bacen API for banking institutions and financial reports.
Data is stored as CSV files and a SQLite database for easy access and manipulation.

2. ETL Pipeline
Extract, Transform, and Load:
Combine multiple raw CSV files into a consolidated dataset.
Map CodInst values to corresponding NomeInstituicao using a JSON mapping file.
Store the processed data in both SQLite Database and CSV formats for further analysis.

3. Feature Engineering
Generate additional features and data scaling from the processed data for better insights, such as:
Market share calculations.
Performance benchmarks (e.g., ROE, efficiency ratios).
Banking sector trends over time.

4. Visual Identity Mapping
Assign unique colors to each NomeInstituicao based on the visual identity of the respective bank brands.
This color dictionary will enhance the visualization consistency across dashboards and charts.

5. Dashboard Development
Power BI Dashboard:
Create a detailed dashboard for banking sector analysis, including:
Market share breakdowns.
Benchmarking against competitors.
Histogram distributions of key metrics.
Historical performance trends.

6. Streamlit Web Application:
Embed the Power BI dashboard inside a Streamlit web app for broader accessibility.
Provide interactive elements for users to explore data insights.

7. Newsletter Integration
Add a subscription field in the Streamlit web app to collect email addresses for a quarterly newsletter.
Generate AI-driven banking insights with LLMs and human in the loop based on the dashboard and share them with subscribers.


-------------------------------------------------------------------------------

Planned Features:

Free Access: Offer the app as a free tool for banking industry professionals to explore market, performance and benchmarking intelligence.

AI-Generated Insights: Use large language models (LLMs) to generate key takeaways and trends from the data.

User Engagement: Enable newsletter subscriptions directly from the web app.

-------------------------------------------------------------------------------

Backlog Potential Features:

Clustering: Use machine learning models to cluster institutions based on their performance, portfolio and risk profiles.

Simulation: Predict and simulate profitability and risk based on credit portfolio business lines of revenue and market data powered by ML.

Forecasting: Use machine learning models to predict future trends and performance.

Identifying Key Drivers: Use machine learning models to identify the key drivers of performance and risk.

Risk and Return Frontiers: Use machine learning models to simulate the risk and return frontiers for different portfolios and strategies.


-------------------------------------------------------------------------------

Roadmap

Finalize the feature engineering script.
Create the visual identity mapping dictionary for NomeInstituicao.
Develop Power BI dashboard.
Build Streamlit app and embed the Power BI dashboard.
Publish the Streamlit app online.
Add newsletter integration to the web app.


-------------------------------------------------------------------------------

Contact

For inquiries, suggestions, or collaboration opportunities, feel free to reach out at:
Email: iaffonso@integrationconsulting.com
