from setuptools import setup, find_packages

setup(
    name="bacen-insights",  # More specific name based on your project
    version="1.0.0",  # Match the version in __init__.py
    author="Iago Affonso",
    author_email="iagoaffonso21@gmail.com",
    description="API for Brazilian Central Bank (BACEN) data analysis and visualization",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'pandas',
        'plotly',
        'uvicorn',
        # Add other dependencies your project needs
    ],
    python_requires='>=3.7',  # Specify minimum Python version
)
