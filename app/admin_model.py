from fasthtml.common import *
from database import db, backup_database
import pandas as pd
from io import BytesIO
import os

tables = db.t

def get_column_headers(table):
    data_class = tables[table].dataclass()
    columns = [k for k in data_class.__dict__.keys() if not k.startswith("_")]
    return columns

def get_column_and_its_type(table):
    data_class = tables[table].dataclass()
    return data_class.__dict__["__annotations__"]

def parse_primary_key(table: str, primary_key: str):
    if table != "modes":
        return int(primary_key)
    return primary_key

def get_table_records(table_name: str):
    return db.q(f"SELECT * FROM {table_name}")

def get_record(table: str, primary_key):
    return tables[table][primary_key]

def update_record_model(table: str, primary_key, data: dict):
    tables[table].update(data, primary_key)

def delete_record_model(table: str, primary_key):
    tables[table].delete(primary_key)

def insert_record_model(table: str, data: dict):
    tables[table].insert(data)

def get_backup_files(backup_dir="data/backup"):
    if not os.path.exists(backup_dir):
        return []
    files = [f for f in os.listdir(backup_dir) if f.endswith(".db")]
    return sorted(files, reverse=True)

def create_backup_model(backup_dir="data/backup"):
    return backup_database(backup_dir)

def export_table_csv(table: str):
    df = pd.DataFrame(tables[table](), columns=get_column_and_its_type(table).keys())
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, header=True)
    csv_buffer.seek(0)
    return csv_buffer

def process_csv_preview(table: str, file_content: bytes):
    imported_df = pd.read_csv(BytesIO(file_content)).fillna("")
    columns = imported_df.columns.tolist()
    records = imported_df.to_dict(orient="records")
    return columns, records

def process_csv_import(table: str, file_content: bytes):
    data = pd.read_csv(BytesIO(file_content)).to_dict("records")
    for record in data:
        tables[table].upsert(record)