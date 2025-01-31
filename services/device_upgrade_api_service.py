import sys
from typing import List
from wsgiref.simple_server import software_version

from cdo_sdk_python import (
    ApiClient,
    DeviceUpgradesApi,
    FtdVersionsPage,
    FtdVersion,
    AsaCompatibleVersionsResponse,
    AsaCompatibleVersion,
    UpgradeFtdDeviceInput,
    CdoTransaction,
    UpgradeAsaDeviceInput,
)
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskID
from rich.table import Table

from services.transaction_service import TransactionService


class DeviceUpgradeApiService:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.device_upgrade_api = DeviceUpgradesApi(api_client)
        self.transaction_service = TransactionService(api_client)

    def get_compatible_ftd_versions(self, ftd_uid: str) -> List[FtdVersion]:
        ftd_versions_page: FtdVersionsPage = (
            self.device_upgrade_api.get_compatible_ftd_versions(device_uid=ftd_uid)
        )
        return ftd_versions_page.items

    def upgrade_ftd(self, ftd_uid: str, ftd_version: FtdVersion) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            upgrade_ftd_task_id: TaskID = progress.add_task(
                f"Upgrading FTD {ftd_uid} to {ftd_version.software_version}...",
                start=True,
            )
            try:
                cdo_transaction: CdoTransaction = (
                    self.device_upgrade_api.upgrade_ftd_device(
                        device_uid=ftd_uid,
                        upgrade_ftd_device_input=UpgradeFtdDeviceInput(
                            upgrade_package_uid=ftd_version.upgrade_package_uid
                        ),
                    )
                )
                self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=cdo_transaction.transaction_uid
                )
            except RuntimeError as e:
                progress.update(task_id=upgrade_ftd_task_id, description=f"Error: {e}")
                sys.exit(1)
            finally:
                progress.stop_task(task_id=upgrade_ftd_task_id)

    def get_compatible_asa_versions(self, asa_uid: str) -> List[AsaCompatibleVersion]:
        asa_compatible_versions_response: AsaCompatibleVersionsResponse = (
            self.device_upgrade_api.get_asa_upgrade_versions(device_uid=asa_uid)
        )
        return asa_compatible_versions_response.items

    def upgrade_asa(
        self, asa_uid: str, upgrade_asa_device_input: UpgradeAsaDeviceInput
    ) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            message = f"Upgrading ASA {asa_uid} to"
            if upgrade_asa_device_input.software_version:
                message += (
                    f" software version: {upgrade_asa_device_input.software_version}"
                )
            if upgrade_asa_device_input.asdm_version:
                if upgrade_asa_device_input.software_version:
                    message += " and"
                message += f" ASDM version: {upgrade_asa_device_input.asdm_version}"
            upgrade_asa_task_id: TaskID = progress.add_task(
                message,
                start=True,
            )
            try:
                cdo_transaction: CdoTransaction = (
                    self.device_upgrade_api.upgrade_asa_device(
                        device_uid=asa_uid,
                        upgrade_asa_device_input=upgrade_asa_device_input,
                    )
                )
                self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=cdo_transaction.transaction_uid
                )
            except RuntimeError as e:
                progress.update(task_id=upgrade_asa_task_id, description=f"Error: {e}")
                sys.exit(1)
            finally:
                progress.stop_task(task_id=upgrade_asa_task_id)

    def print_ftd_versions(self, versions: List[FtdVersion]) -> None:
        table = Table(title="Compatible FTD versions")

        table.add_column("Version", justify="center")
        table.add_column("Upgrade Package UID", justify="center")
        table.add_column("Suggested Release", justify="center")

        for version in versions:
            table.add_row(
                version.software_version,
                version.upgrade_package_uid,
                "Yes" if version.is_suggested_version else "No",
            )

        console = Console()
        console.print(table)

    def print_asa_versions(self, versions: List[AsaCompatibleVersion]) -> None:
        table = Table(title="Compatible ASA versions")

        table.add_column("Software Version", justify="center")
        table.add_column("ASDM Version", justify="center")

        for version in versions:
            table.add_row(
                version.software_version,
                version.asdm_version,
            )

        console = Console()
        console.print(table)
