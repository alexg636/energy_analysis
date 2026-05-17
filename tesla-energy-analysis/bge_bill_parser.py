import pdfplumber
import pandas as pd
from datetime import datetime
import re


class BGEBillParser:
    def __init__(self):
        self.electric_details = {}
        self.gas_details = {}

        # Initialize dictionaries
        self._init_details("ELECTRIC", self.electric_details)
        self._init_details("GAS", self.gas_details)
    
        # Initialize tables by parsing PDF
        self.electric_details_tbl = []
        self.gas_details_tbl = []

    # Public Methods
    
    def process_pdf(self, bill_path:str, bill_page:int):
        self.bill_path = bill_path
        with pdfplumber.open(self.bill_path) as pdf:
            page = pdf.pages[bill_page]
            table = page.extract_tables()
            self.electric_details_tbl = table[0]
            self.gas_details_tbl = table[1]

        _extract_electric()
        _extract_gas()



    # Private Methods
    def _init_details(self, filter:str, output_dict:dict):
        if filter == "ELECTRIC":
            output_dict["class"] = "electric"
            # UNIX Epoch as placeholder
            output_dict["billing_period_start"] = "1970-01-01"
            output_dict["billing_period_end"] = "1970-01-01"
            output_dict["total_kWh"] = 0
            output_dict["total_price"] = 0
            output_dict["supply_0_rate"] = 0
            output_dict["supply_0_energy"] = 0
            output_dict["supply_0_price"] = 0
            output_dict["delivery_cust_price"] = 0
            output_dict["delivery_distribution_rate"] = 0
            output_dict["delivery_distribution_price"] = 0
            output_dict["delivery_empower_md_rate"] = 0
            output_dict["deliver_empower_md_price"] = 0
            output_dict["md_svc_prog_fee_price"] = 0
            output_dict["env_surchg_fee_rate"] = 0
            output_dict["env_surchg_fee_price"] = 0
            output_dict["franchise_tax_rate"] = 0
            output_dict["franchise_tax_price"] = 0
        
        if filter == "GAS":
            output_dict["class"] = "gas"
            output_dict["billing_period_start"] = "1970-01-01"
            output_dict["billing_period_end"] = "1970-01-01"
            output_dict["total_therms"] = 0
            output_dict["therm_factor"] = 0
            output_dict["total_price"] = 0
            output_dict["supply_0_rate"] = 0
            output_dict["supply_0_energy"] = 0
            output_dict["supply_0_price"] = 0
            output_dict["delivery_cust_price"] = 0
            output_dict["gas_supply_0_rate"] = 0
            output_dict["gas_supply_0_rate"] = 0

    # Function returns standard date output; Jun22,2025 -> 2025-06-22
    def _format_date(input_date:str):
        # Expects abbreviated month name
        date_obj = datetime.strptime(input_date, "%b%d,%Y")
        return date_obj.strftime("%Y-%m-%d")
    
