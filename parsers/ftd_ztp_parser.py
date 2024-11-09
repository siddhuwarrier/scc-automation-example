import csv
import re
from typing import List, Optional

import questionary
from cdo_sdk_python.models.ztp_onboarding_input import ZtpOnboardingInput


class FtdZtpParser:
    def __init__(
        self, fmc_access_policy_uid: str, ftd_ztp_csv_file: Optional[str] = None
    ):
        if fmc_access_policy_uid is None:
            raise ValueError("fmc_access_policy_uid cannot be None")
        self.fmc_access_policy_uid = fmc_access_policy_uid
        self.ftd_ztp_csv_file = ftd_ztp_csv_file

    def get_ztp_onboarding_inputs(self) -> List[ZtpOnboardingInput]:
        if self.ftd_ztp_csv_file:
            return self._parse_csv()
        else:
            return self._prompt_ztp_details()

    def _parse_csv(self) -> List[ZtpOnboardingInput]:
        ztp_onboarding_inputs = []
        with open(self.ftd_ztp_csv_file, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                ztp_onboarding_inputs.append(
                    ZtpOnboardingInput(
                        name=row["name"],
                        serial_number=row["serial_number"],
                        admin_password=row["admin_password"],
                        licenses=row["licenses"].split(";"),
                        fmc_access_policy_uid=self.fmc_access_policy_uid,
                        device_group_uid=None,
                    )
                )
        return ztp_onboarding_inputs

    def _prompt_ztp_details(self) -> List[ZtpOnboardingInput]:
        ztp_onboarding_inputs = []

        onboard_ztp = questionary.confirm(
            "Do you want to onboard FTDs using Zero-Touch Provisioning?", default=True
        ).ask()
        if not onboard_ztp:
            return ztp_onboarding_inputs

        while True:
            name = questionary.text(
                "Device Name (A-Za-z0-9-_*):",
                validate=lambda text: bool(re.match(r"^[A-Za-z0-9-_*]+$", text)),
            ).ask()
            serial_number = questionary.text("Serial Number:").ask()
            should_enter_admin_password = questionary.confirm(
                "Enter admin password? You should not if the password is already set:",
                default=False,
            ).ask()
            if should_enter_admin_password:
                admin_password = questionary.password(
                    "Admin Password (no spaces):", validate=lambda text: " " not in text
                ).ask()
            else:
                admin_password = None
            licenses = questionary.checkbox(
                "Select licenses:",
                choices=["BASE", "CARRIER", "MALWARE", "THREAT", "URLFilter"],
                validate=lambda selected: len(selected) > 0,
            ).ask()

            ztp_onboarding_inputs.append(
                ZtpOnboardingInput(
                    name=name,
                    serial_number=serial_number,
                    admin_password=admin_password,
                    licenses=licenses,
                    fmc_access_policy_uid=self.fmc_access_policy_uid,
                    device_group_uid=None,
                )
            )

            add_another = questionary.confirm(
                "Add another FTD to onboard?", default=True
            ).ask()
            if not add_another:
                break

        return ztp_onboarding_inputs
