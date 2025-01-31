import sys
from typing import List

import questionary
from cdo_sdk_python import (
    InventoryApi,
    ApiClient,
    FtdCreateOrUpdateInput,
    ZtpOnboardingInput,
    CdoTransaction,
    Device,
    FtdRegistrationInput,
    DevicePage,
)
from rich.console import Console
from rich.progress import SpinnerColumn, TextColumn, Progress, TaskID

from services.transaction_service import TransactionService


class InventoryApiService:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.inventory_api = InventoryApi(api_client)
        self.transaction_service = TransactionService(api_client)
        self.console = Console()

    def onboard_ftd_device(self, ftd_input: FtdCreateOrUpdateInput):
        device: Device = self.create_ftd_device(ftd_input)
        self.console.print(
            "Paste the following CLI key into the FTD terminal:"
            f"\n{'=' * 10}\n"
            f"{device.cd_fmc_info.cli_key}"
            f"\n{'=' * 10}"
        )
        while True:
            answer = questionary.confirm(
                "Have you pasted the CLI key into the FTD terminal?", default=False
            ).ask()
            if answer:
                break
        return self.register_ftd_device_with_scc(device)

    def create_ftd_device(self, ftd_input: FtdCreateOrUpdateInput) -> Device:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            create_ftd_task_id: TaskID = progress.add_task(
                f"Generating configure manager CLI commands for FTD {ftd_input.name}...",
                start=True,
            )
            transaction: CdoTransaction = self.inventory_api.create_ftd_device(
                ftd_input
            )
            return self._get_device_after_transaction_finished(
                transaction, progress, create_ftd_task_id
            )

    def register_ftd_device_with_scc(self, device: Device) -> Device:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            register_ftd_task_id: TaskID = progress.add_task(
                f"Registering FTD {device.name} with Security Cloud Control...",
                start=True,
            )
            transaction: CdoTransaction = (
                self.inventory_api.finish_onboarding_ftd_device(
                    FtdRegistrationInput(ftd_uid=device.uid)
                )
            )
            return self._get_device_after_transaction_finished(
                transaction, progress, register_ftd_task_id
            )

    def onboard_ftd_ztp_device(self, ztp_onboarding_input: ZtpOnboardingInput):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            onboard_ftd_task_id: TaskID = progress.add_task(
                f"Onboarding FTD {ztp_onboarding_input.name}...", start=True
            )
            transaction: CdoTransaction = (
                self.inventory_api.onboard_ftd_device_using_ztp(ztp_onboarding_input)
            )
            try:
                self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=transaction.transaction_uid
                )
                # workaround for https://jira-eng-rtp3.cisco.com/jira/browse/LH-87581
                devicePage: DevicePage = self.inventory_api.get_devices(
                    q=f"name:{ztp_onboarding_input.name}"
                )
                if len(devicePage.items) != 1:
                    raise RuntimeError(
                        f"Could not find device with name {ztp_onboarding_input.name}"
                    )
            except RuntimeError as e:
                progress.update(task_id=onboard_ftd_task_id, description=f"Error:{e}")
                sys.exit(1)
            finally:
                progress.stop_task(task_id=onboard_ftd_task_id)
            return devicePage.items[0]

    def _get_device_after_transaction_finished(
        self, transaction: CdoTransaction, progress: Progress, task_id: TaskID
    ) -> Device:
        try:
            finished_transaction: CdoTransaction = (
                self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=transaction.transaction_uid
                )
            )
            device: Device = self.inventory_api.get_device(
                device_uid=finished_transaction.entity_uid
            )
        except RuntimeError as e:
            progress.update(task_id=task_id, description=f"Error:{e}")
            sys.exit(1)
        finally:
            progress.stop_task(task_id=task_id)

        return device

    def get_devices(self, q: str = None) -> List[Device]:
        devices: List[Device] = []
        count: int = 0
        offset: int = 0
        limit: int = 200
        while True:
            device_page: DevicePage = self.inventory_api.get_devices(
                limit=str(limit), offset=str(offset), q=q
            )
            devices.extend(device_page.items)
            count = device_page.count
            offset += limit
            if len(devices) >= count:
                break

        return devices
