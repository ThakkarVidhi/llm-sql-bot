import os
import json
from dotenv import load_dotenv
load_dotenv()

class Config:
    DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')
    MODEL_PATH = os.getenv('MODEL_PATH')
    TEMPERATURE = float(os.getenv('TEMPERATURE'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS'))
    TOP_P = float(os.getenv('TOP_P'))
    N_CTX = int(os.getenv('N_CTX'))
    TABLES_NAME = os.getenv('TABLES_NAME')
    TABLES = TABLES_NAME.split(',')
    DB_USER_NAME = os.getenv('DB_USER_NAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_HOST = os.getenv('DB_HOST')
    TARGET_DIALECT = os.getenv('TARGET_DIALECT')
    DEFAULT_DIALECT = os.getenv('DEFAULT_DIALECT')
    DB_URI = DB_CONNECTION_STRING.format(
        username=DB_USER_NAME,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        host=DB_HOST
    )

    @staticmethod
    def load_examples(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)