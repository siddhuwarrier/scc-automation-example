import sys
from idlelib.pyparse import trans
from typing import List

from cdo_sdk_python import (
    ApiClient,
    CommandsApi,
    CommandLineInterfaceApi,
    InventoryApi,
    CliCommandInput,
)
from rich.progress import TaskID, Progress, SpinnerColumn, TextColumn

from services.transaction_service import TransactionService


class CliApiService:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.inventory_api = InventoryApi(
            api_client
        )  # this will change with the next release to the CommandLineInterfaceApi
        self.cli_api = CommandLineInterfaceApi(api_client=api_client)
        self.transaction_service = TransactionService(api_client)

    def execute_command_and_get_result(
        self, device_uids: List[str], command: str
    ) -> str:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            execute_cli_task: TaskID = progress.add_task(
                f"Executing command {command} on ASA devices {device_uids}...",
                start=True,
            )
            try:
                transaction = self.inventory_api.execute_cli_command(
                    CliCommandInput(device_uids=device_uids, script=command)
                )
                transaction = self.transaction_service.wait_for_transaction_to_finish(
                    transaction.transaction_uid
                )
                cli_result = self.cli_api.get_cli_result(
                    cli_result_uid=transaction.entity_uid
                )

                if cli_result.error_msg is not None:
                    progress.update(
                        task_id=execute_cli_task,
                        description=f"Error:{cli_result.error_msg}",
                    )
            except RuntimeError as e:
                progress.update(task_id=execute_cli_task, description=f"Error:{e}")
                sys.exit(1)
            finally:
                progress.stop_task(task_id=execute_cli_task)

        return cli_result.result
