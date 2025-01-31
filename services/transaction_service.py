import time

from cdo_sdk_python import TransactionsApi, CdoTransaction


class TransactionService:
    def __init__(self, api_client):
        self.transactions_api: TransactionsApi = TransactionsApi(api_client)

    def wait_for_transaction_to_finish(
        self, transaction_uid: str, time_to_wait_between_retries_seconds: int = 5
    ) -> CdoTransaction:
        transaction: CdoTransaction = self.transactions_api.get_transaction(
            transaction_uid
        )
        while transaction.cdo_transaction_status not in [
            "DONE",
            "ERROR",
        ]:
            time.sleep(time_to_wait_between_retries_seconds)
            transaction = self.transactions_api.get_transaction(transaction_uid)

        if transaction.cdo_transaction_status == "ERROR":
            raise RuntimeError(
                f"Transaction {transaction_uid} failed: {transaction.transaction_details}"
            )
        return transaction
