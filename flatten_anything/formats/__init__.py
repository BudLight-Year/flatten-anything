from .csv import ingest_csv
from .json import ingest_json
from .parquet import ingest_parquet
from .excel import ingest_excel
from .xml import ingest_xml
from .yaml import ingest_yaml
from .api import ingest_api

__all__ = [
    'ingest_csv',
    'ingest_json', 
    'ingest_parquet',
    'ingest_excel',
    'ingest_xml',
    'ingest_yaml',
    'ingest_api',
]
