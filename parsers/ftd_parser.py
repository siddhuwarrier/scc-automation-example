import csv
from typing import List

import questionary
from cdo_sdk_python import FtdCreateOrUpdateInput


class FtdParser:
    def __init__(self, fmc_access_policy_uid: str, ftd_csv_file: str = None):
        self.fmc_access_policy_uid = fmc_access_policy_uid
        self.ftd_csv_file = ftd_csv_file

    def get_ftds_to_onboard(
        self,
    ) -> List[FtdCreateOrUpdateInput]:
        if self.ftd_csv_file:
            return self._parse_csv()
        else:
            return self._prompt_ftd_details()

    def _parse_csv(self) -> List[FtdCreateOrUpdateInput]:
        ftd_credentials = []
        with open(self.ftd_csv_file, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                licenses = row["licenses"].split(";")
                virtual = row["virtual"].lower() == "true"
                performance_tier = row.get("performance_tier")
                ftd_credentials.append(
                    FtdCreateOrUpdateInput(
                        name=row["name"],
                        licenses=licenses,
                        virtual=virtual,
                        performance_tier=performance_tier,
                        fmc_access_policy_uid=self.fmc_access_policy_uid,
                        device_type="CDFMC_MANAGED_FTD",
                    ),
                )
        return ftd_credentials

    def _prompt_ftd_details(self) -> List[FtdCreateOrUpdateInput]:
        ftd_inputs = []

        get_ftd_details = questionary.confirm(
            "Do you want to onboard FTDs using the configure manager cli to the new tenant?",
            default=True,
        ).ask()
        if not get_ftd_details:
            return ftd_inputs

        while True:
            name = questionary.text("FTD Name:").ask()

            licenses = questionary.checkbox(
                "Select licenses (use space to select multiple):",
                choices=["BASE", "CARRIER", "MALWARE", "THREAT", "URLFilter"],
                validate=lambda selected: len(selected) > 0,
            ).ask()

            virtual = questionary.confirm("Is the FTD virtual?", default=False).ask()

            performance_tier = None
            if virtual:
                performance_tier = questionary.select(
                    "Select performance tier:",
                    choices=["FTDv5", "FTDv10", "FTDv20", "FTDv30", "FTDv50"],
                ).ask()

            ftd_inputs.append(
                FtdCreateOrUpdateInput(
                    name=name,
                    licenses=licenses,
                    virtual=virtual,
                    performance_tier=performance_tier,
                    fmc_access_policy_uid=self.fmc_access_policy_uid,
                    device_type="CDFMC_MANAGED_FTD",
                ),
            )

            create_another = questionary.confirm(
                "Add another FTD to onboard?", default=True
            ).ask()

            if not create_another:
                break

        return ftd_inputs
