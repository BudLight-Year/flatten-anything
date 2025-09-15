"""
Setup configuration for Flatten Anything package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flatten-anything",
    version="1.0.1",
    author="Evan Cline",
    author_email="totallysweethobo@gmail.com",
    description="Stop writing custom parsers for every data format. Flatten anything.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BudLight-Year/flatten-anything",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    
    # Core dependencies - kept minimal
    install_requires=[
        "pandas>=1.0.0",
        "pyyaml>=5.3",
        "xmltodict>=0.12.0",
        "requests>=2.20.0",
    ],
    
    # Optional dependencies for specific formats
    extras_require={
        'parquet': ['pyarrow>=4.0.0'],
        'excel': ['openpyxl>=3.0.0'],
        'all': [
            'pyarrow>=4.0.0',
            'openpyxl>=3.0.0',
        ],
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.10.0',
            'black>=21.0',
            'flake8>=3.9.0',
        ],
    },
    
    keywords="flatten json csv parquet excel yaml xml data transformation etl ingest ingestion dot-notation",
    project_urls={
        "Bug Reports": "https://github.com/BudLight-Year/flatten-anything/issues",
        "Source": "https://github.com/BudLight-Year/flatten-anything",
        "Documentation": "https://github.com/BudLight-Year/flatten-anything#readme",
    },
)
