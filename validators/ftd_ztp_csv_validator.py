import csv
import os
import re


class FtdZtpCsvValidator:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file

    def validate(self) -> bool:
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV file {self.csv_file} does not exist.")

        with open(self.csv_file, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not self._validate_row(row):
                    return False
        return True

    def _validate_row(self, row: dict) -> bool:
        name = row.get("name")
        serial_number = row.get("serial_number")
        licenses = row.get("licenses")
        admin_password = row.get("admin_password")

        if not name or not re.match(r"^[A-Za-z0-9-_*]+$", name):
            print(f"Invalid name {name}")
            return False

        if not serial_number:
            return False

        if not licenses or not all(
            license in ["BASE", "CARRIER", "MALWARE", "THREAT", "URLFilter"]
            for license in licenses.split(";")
        ):
            return False

        if not admin_password or " " in admin_password:
            return False

        return True
