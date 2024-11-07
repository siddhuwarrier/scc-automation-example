import sys
from typing import List

from cdo_sdk_python import (
    ApiClient,
    MSPApi,
    MspCreateTenantInput,
    CdoTransaction,
    UserInput,
    MspAddUsersToTenantInput,
    UserPage,
    ApiTokenInfo,
    Configuration,
    TransactionsApi,
)
from cdo_sdk_python.models.msp_managed_tenant import MspManagedTenant
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskID

from services.transaction_service import TransactionService


class MspApiService:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.msp_api = MSPApi(api_client)
        self.transaction_service = TransactionService(api_client)
        self.console = Console()

    def create_tenant(self, tenant_name: str, display_name: str) -> MspManagedTenant:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            create_tenant_task_id: TaskID = progress.add_task(
                "Creating tenant...", start=True
            )
            transaction: CdoTransaction = self.msp_api.create_tenant(
                MspCreateTenantInput(
                    **{"tenant_name": tenant_name, "display_name": display_name}
                )
            )
            try:
                finished_transaction: CdoTransaction = (
                    self.transaction_service.wait_for_transaction_to_finish(
                        transaction_uid=transaction.transaction_uid
                    )
                )
                msp_managed_tenant: MspManagedTenant = (
                    self.msp_api.get_msp_managed_tenant(
                        tenant_uid=finished_transaction.entity_uid
                    )
                )
            except RuntimeError as e:
                progress.update(task_id=create_tenant_task_id, description=f"Error:{e}")
                sys.exit(1)
            finally:
                progress.stop_task(task_id=create_tenant_task_id)

        return msp_managed_tenant

    def provision_cdfmc_on_msp_managed_tenant(
        self,
        msp_managed_tenant: MspManagedTenant,
        msp_managed_tenant_api_token: str,
        should_wait_for_cdfmc_to_be_active: bool = False,
    ) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            provision_cdfmc_task_id: TaskID = progress.add_task(
                "Provisioning cdFMC...", start=True
            )
            transaction: CdoTransaction = (
                self.msp_api.provision_cd_fmc_for_tenant_in_msp_portal(
                    msp_managed_tenant.uid
                )
            )
            try:
                # wait for the transaction on the MSP portal to finish
                transaction = self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=transaction.transaction_uid
                )
                # if we should wait for the cdFMC provisioning transaction on the managed tenant to finish, do that
                if should_wait_for_cdfmc_to_be_active:
                    transaction = TransactionsApi(self.api_client).get_transaction(
                        transaction.transaction_uid
                    )
                    target_transaction_uid = transaction.transaction_details.get(
                        "TRANSACTION_UID_IN_TARGET_TENANT"
                    )
                    with ApiClient(
                        Configuration(
                            host=self.api_client.configuration.host,
                            access_token=msp_managed_tenant_api_token,
                        )
                    ) as tenant_api_client:
                        tenant_transaction_service = TransactionService(
                            tenant_api_client
                        )
                        tenant_transaction_service.wait_for_transaction_to_finish(
                            transaction_uid=target_transaction_uid
                        )
            except RuntimeError as e:
                progress.update(
                    task_id=provision_cdfmc_task_id, description=f"Error:{e}"
                )
                sys.exit(1)
            finally:
                progress.stop_task(task_id=provision_cdfmc_task_id)

    def generate_managed_tenant_api_token(
        self, msp_managed_tenant: MspManagedTenant, username: str
    ) -> str:
        user_page: UserPage = self.msp_api.get_users_in_tenant_in_msp_portal(
            msp_managed_tenant.uid, limit="1", offset="0", q=f"name:{username}"
        )
        if len(user_page.items) != 1:
            raise RuntimeError(
                f"User {username} not found in tenant {msp_managed_tenant.display_name} ({msp_managed_tenant.region})"
            )
        user_uid: str = user_page.items[0].uid

        api_token_info: ApiTokenInfo = (
            self.msp_api.generate_api_token_for_user_in_tenant(
                msp_managed_tenant.uid, user_uid
            )
        )

        return api_token_info.api_token

    def create_users(
        self, users: List[UserInput], msp_managed_tenant: MspManagedTenant
    ) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            add_users_to_tenant_task_id: TaskID = progress.add_task(
                f"Creating {len(users)} users in tenant {msp_managed_tenant.display_name} ({msp_managed_tenant.region})...",
                start=True,
            )
            transaction: CdoTransaction = (
                self.msp_api.add_users_to_tenant_in_msp_portal(
                    msp_managed_tenant.uid, MspAddUsersToTenantInput(**{"users": users})
                )
            )
            try:
                self.transaction_service.wait_for_transaction_to_finish(
                    transaction_uid=transaction.transaction_uid
                )
            except RuntimeError as e:
                progress.update(
                    task_id=add_users_to_tenant_task_id, description=f"Error:{e}"
                )
                sys.exit(1)
            finally:
                progress.stop_task(task_id=add_users_to_tenant_task_id)
