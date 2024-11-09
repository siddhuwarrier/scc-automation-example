import csv
import os


class FtdCsvValidator:
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
        is_virtual = row.get("virtual", "").lower() == "true"
        performance_tier = row.get("performance_tier")
        licenses = row.get("licenses")

        if not name:
            return False

        if is_virtual:
            if performance_tier not in [
                "FTDv5",
                "FTDv10",
                "FTDv20",
                "FTDv30",
                "FTDv50",
            ]:
                return False
            if not licenses or not all(
                l in ["BASE", "CARRIER", "MALWARE", "THREAT", "URLFilter"]
                for l in licenses.split(";")
            ):
                return False

        return True
