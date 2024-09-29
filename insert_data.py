""" Script to insert records into a PostgreSQL database """
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from datetime import datetime
import math

load_dotenv()
# Get environment variables
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Create the database engine
engine = create_engine(DATABASE_URL)


class DataInserter:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def parse_value(value):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def insert_data_from_csv(self, table_name, csv_file_path):
        df = pd.read_csv(csv_file_path)

        # Apply value parsing
        df = df.map(self.parse_value)

        # Generate SQL for data insertion
        columns = ', '.join(df.columns)
        values = ', '.join([f":{col}" for col in df.columns])
        insert_sql = text(
            f'INSERT INTO {table_name} ({columns}) VALUES ({values})')

        # Insert each row of data
        for idx, row in df.iterrows():
            try:
                self.session.execute(insert_sql, row.to_dict())
            except SQLAlchemyError as e:
                print(f"Error in row {idx + 2}: {row.to_dict()}")
                self.session.rollback()
                raise e

    def insert_data(self, data_folder):
        tables = ['donantes', 'proveedores', 'ingreso_egreso']

        try:
            for table in tables:
                csv_file_path = os.path.join(data_folder, f'{table}.csv')
                self.insert_data_from_csv(table, csv_file_path)

            # Commit the changes
            self.session.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.session.rollback()
        finally:
            # Close the session
            self.session.close()

        print("Data insertion complete.")


def main():
    data_folder = 'data/processed_data'
    Session = sessionmaker(bind=engine)
    session = Session()

    inserter = DataInserter(session)
    inserter.insert_data(data_folder)


if __name__ == "__main__":
    main()
