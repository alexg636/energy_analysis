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

    def get_electric(self):
        return dict(sorted(self.electric_details.items()))
    
    def get_gas(self):
        return dict(sorted(self.gas_details.items()))
    
    def process_pdf(self, bill_path:str, bill_page:int):
        self.bill_path = bill_path
        with pdfplumber.open(self.bill_path) as pdf:
            page = pdf.pages[bill_page]
            table = page.extract_tables()
            self.electric_details_tbl = table[0]
            self.gas_details_tbl = table[1]

        # Extract fields
        self._extract_electric()
        self._extract_gas()


    # Private Methods
    def _extract_electric(self):
        for item in self.electric_details_tbl:
            row = (item[0] or "").splitlines()
            for entry in row:
                self._extract_billing_period(self.electric_details, entry)
                self._extract_total_kwh(self.electric_details, entry)
                self._extract_total_price(self.electric_details, entry)
                self._extract_supply(self.electric_details, row, entry)
                self._extract_customer_chg(self.electric_details, entry)
                self._extract_empower(self.electric_details, entry)
                self._extract_distribution(self.electric_details, entry)
                self._extract_md_svc(self.electric_details, entry)
                self._extract_env(self.electric_details, entry)
                self._extract_franchise(self.electric_details, entry)

    def _extract_gas(self):
        for item in self.gas_details_tbl:
            row = (item[0] or "").splitlines()
            for entry in row:
                self._extract_billing_period(self.gas_details, entry)
                self._extract_total_therms(self.gas_details, entry)
                self._extract_therm_units(self.gas_details, entry)
                self._extract_therm_factor(self.gas_details, entry)
                self._extract_total_price(self.gas_details, entry)
                self._extract_supply(self.gas_details, row, entry)
                self._extract_customer_chg(self.gas_details, entry)
                self._extract_empower(self.gas_details, entry)
                self._extract_distribution(self.gas_details, entry)

    ## Field Extraction methods below
    def _extract_billing_period(self, output_dict:dict, entry:str):
        if "BillingPeriod" in entry:
            date_pattern = r'[A-Z][a-z]{2}\d{1,2},\d{4}'
            dates = re.findall(date_pattern, entry)
            output_dict["billing_period_start"] = self._format_date(dates[0])
            output_dict["billing_period_end"] = self._format_date(dates[1])

    ## Total kWHs
    def _extract_total_kwh(self, output_dict:dict, entry:str):
        if "Current - Previous" in entry:
            output_dict["total_kWh"] = float(entry.split("= ")[1])
    ## Total therms
    def _extract_total_therms(self, output_dict:dict, entry:str):
        if "Units x Factor" in entry:
            output_dict["total_therms"] = float(entry.split(" ")[-1])
    ## Total therm units
    def _extract_therm_units(self, output_dict:dict, entry:str):
        if "thermsused" in entry:
            output_dict["units"] = float(entry.split(" ")[2])

    ## Therm factor
    def _extract_therm_factor(self, output_dict:dict, entry:str):
        if "thermsused" in entry:
            output_dict["therm_factor"] = float(entry.split(" ")[3])

    ## Total Price
    def _extract_total_price(self, output_dict:dict, entry:str):
        if "TOTAL" in entry:
            output_dict["total_price"] = float(re.search(r"\$(\d+\.\d+)", entry).group(1))
    
    ## Supply
    def _extract_supply(self, output_dict:dict, row:list, entry:str):
        if output_dict["class"] == "electric":
            filter = ["ELECTRICSUPPLY", "BGEELECTRICDELIVERY"]
            pattern = r"(\d+(?:\.\d+)?)kWh"
        if output_dict["class"] == "gas":
            filter = ["GASSUPPLY", "BGEGASDELIVERY"]
            pattern = r"(\d+(?:\.\d+)?)therms"

        if filter[0] in entry:
            indices = [i for i, target in enumerate(row) if filter[0] in target or filter[1] in target]
            number_rates = indices[1] - indices[0] - 1
            for i in range(0,number_rates):
                # Skip first entry b/c it's an anchor
                search_idx = row[i+1]
                rate_key = f"supply_{i}_rate"
                rate_energy_key = f"supply_{i}_energy"
                rate_price_key = f"supply_{i}_price"

                # Skips first entry
                output_dict[rate_energy_key] = float(re.search(pattern, search_idx).group(1))
                output_dict[rate_key] = float(re.search(r"x\s*(\.\d+)", search_idx).group(1))
                output_dict[rate_price_key] = search_idx.split(" ")[-1]
    
    ## Customer Charge
    def _extract_customer_chg(self, output_dict:dict, entry:str):
        if "CustomerCharge" in entry:
            output_dict["delivery_cust_price"] = entry.split(" ")[1]
    ## EmPower MD Charge
    def _extract_empower(self, output_dict:dict, entry:str):
        if "EmPowerMDChg" in entry:
            output_dict["delivery_empower_md_rate"] = float(re.search(r"x\s*(\.\d+)", entry).group(1))
            output_dict["delivery_empower_md_price"] = entry.split(" ")[-1]
    ## Distribution Charge
    def _extract_distribution(self, output_dict:dict, entry:str):
        if "DistributionChg" in entry:
            output_dict["delivery_distribution_rate"] = float(re.search(r"x\s*(\.\d+)", entry).group(1))
            output_dict["delivery_distribution_price"] = entry.split(" ")[-1]
    
    ## Maryland Universal Service Program
    def _extract_md_svc(self, output_dict:dict, entry:str):
        if "MDUniversalSvcProg" in entry:
            output_dict["md_svc_prog_fee_price"] = entry.split(" ")[1]
    ## Environmental Surcharge
    def _extract_env(self, output_dict:dict, entry:str):
        if "EnvirSrchg" in entry:
            output_dict["env_surchg_fee_rate"] = float(re.search(r"x\s*(\.\d+)", entry).group(1))
            output_dict["env_surchg_fee_price"] = entry.split(" ")[-1]
    ## Franchise Tax
    def _extract_franchise(self, output_dict:dict, entry:str):
        if "FranchiseTax" in entry:
            output_dict["franchise_tax_rate"] = float(re.search(r"x\s*(\.\d+)", entry).group(1))
            output_dict["franchise_tax_price"] = entry.split(" ")[-1]


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
            output_dict["delivery_empower_md_price"] = 0
            output_dict["md_svc_prog_fee_price"] = 0
            output_dict["env_surchg_fee_rate"] = 0
            output_dict["env_surchg_fee_price"] = 0
            output_dict["franchise_tax_rate"] = 0
            output_dict["franchise_tax_price"] = 0
        
        if filter == "GAS":
            output_dict["class"] = "gas"
            output_dict["billing_period_start"] = "1970-01-01"
            output_dict["billing_period_end"] = "1970-01-01"
            output_dict["units"] = 0
            output_dict["total_therms"] = 0
            output_dict["therm_factor"] = 0
            output_dict["total_price"] = 0
            output_dict["supply_0_rate"] = 0
            output_dict["supply_0_energy"] = 0
            output_dict["supply_0_price"] = 0
            output_dict["delivery_cust_price"] = 0
            output_dict["delivery_distribution_rate"] = 0
            output_dict["delivery_distribution_price"] = 0
            output_dict["delivery_empower_md_rate"] = 0
            output_dict["delivery_empower_md_price"] = 0

    # Function returns standard date output; Jun22,2025 -> 2025-06-22
    def _format_date(self, input_date:str):
        # Expects abbreviated month name
        date_obj = datetime.strptime(input_date, "%b%d,%Y")
        return date_obj.strftime("%Y-%m-%d")