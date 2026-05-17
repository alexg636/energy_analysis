from bge_bill_parser import BGEBillParser
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from glob import glob
from os import path
import pandas as pd


client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = client.write_api(write_options=SYNCHRONOUS)

# Extract all filenames
files = glob("test/*.pdf")
# parser = BGEBillParser()

def process_file(file_path:str):
    parser = BGEBillParser()
    parser.process_pdf(file_path)
    electric_data = parser.get_electric()
    gas_data = parser.get_gas()

    electric_data_df = pd.DataFrame([electric_data])
    gas_data_df = pd.DataFrame([gas_data])

    electric_data_df["billing_period_end"] = pd.to_datetime(electric_data_df["billing_period_end"])
    gas_data_df["billing_period_end"] = pd.to_datetime(gas_data_df["billing_period_end"])

    electric_data_df = electric_data_df.set_index("billing_period_end")
    gas_data_df = gas_data_df.set_index("billing_period_end")

    write_api.write(
    bucket=INFLUX_BUCKET,
    org=INFLUX_ORG,
    record=electric_data_df,
    data_frame_measurement_name="utility_bill",
    data_frame_tag_columns=["class"]
    )

    write_api.write(
    bucket=INFLUX_BUCKET,
    org=INFLUX_ORG,
    record=gas_data_df,
    data_frame_measurement_name="utility_bill",
    data_frame_tag_columns=["class"]
    )

    print(f"Successfully processed: {file_path}")
    # parser.clear()


for entry in files:
    process_file(entry)

client.close()