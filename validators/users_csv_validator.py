import csv
import os
import re


class UsersCsvValidator:
    VALID_ROLES = {
        "ROLE_SUPER_ADMIN",
        "ROLE_ADMIN",
        "ROLE_READ_ONLY",
        "ROLE_EDIT_ONLY",
        "ROLE_DEPLOY_ONLY",
        "ROLE_VPN_SESSION_MANAGER",
    }

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
        username = row.get("username")
        role = row.get("role")
        api_only_user = row.get("api_only_user", "").lower() == "true"

        if not username or not role:
            return False

        if api_only_user and re.match(r"[^@]+@[^@]+\.[^@]+", username):
            return False
        if not api_only_user and not re.match(r"[^@]+@[^@]+\.[^@]+", username):
            return False

        if role not in self.VALID_ROLES:
            return False

        return True
