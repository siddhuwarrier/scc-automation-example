import requests
from cdo_sdk_python import ApiClient, InventoryApi, DevicePage

from models.fmc import (
    CdFmcAccessPolicy,
    CdFmcAccessRule,
    Urls,
    SourceNetworks,
    UrlCategoryWithReputation,
    UrlCategory,
    NetworkObject,
)


class CdFmcApiService:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.inventory_api = InventoryApi(api_client)

        manager_page: DevicePage = self.inventory_api.get_device_managers(
            limit="1", offset="0", q="deviceType:CDFMC"
        )
        if len(manager_page.items) != 1:
            raise RuntimeError("CDFMC not found")
        self.cdfmc_domain_uid = manager_page.items[0].fmc_domain_uid

    def create_default_access_policy(self):

        policy = CdFmcAccessPolicy(name="MSP Access Policy", default_action="BLOCK")
        url = (
            f"{self.api_client.configuration.host}/v1/cdfmc/api/fmc_config/v1/domain/"
            f"{self.cdfmc_domain_uid}/policy/accesspolicies"
        )
        headers = {
            "Authorization": f"Bearer {self.api_client.configuration.access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=policy.__dict__)
        response.raise_for_status()
        return response.json()["id"]

    def block_gambling(self, access_policy_uid: str):
        gambling_category_id: str = self._get_gambling_category_id()
        any_ipv4_obj_id: str = self._get_any_ipv4_network_object()

        url = (
            f"{self.api_client.configuration.host}/v1/cdfmc/api/fmc_config/v1/domain/"
            f"{self.cdfmc_domain_uid}/policy/accesspolicies/{access_policy_uid}/accessrules"
        )
        headers = {
            "Authorization": f"Bearer {self.api_client.configuration.access_token}",
            "Content-Type": "application/json",
        }
        access_rule = CdFmcAccessRule(
            name="Block Gambling",
            action="BLOCK",
            enabled=True,
            urls=Urls(
                url_categories_with_reputation=[
                    UrlCategoryWithReputation(
                        reputation="TRUSTED_AND_UNKNOWN",
                        category=UrlCategory(
                            name="Gambling",
                            id=gambling_category_id,
                        ),
                    )
                ]
            ),
            source_networks=SourceNetworks(
                objects=[
                    NetworkObject(
                        type="NetworkGroup",
                        overridable=False,
                        id=any_ipv4_obj_id,
                        name="any-ipv4",
                    )
                ]
            ),
        )

        response = requests.post(url, headers=headers, json=access_rule.to_dict())
        response.raise_for_status()

        return response.json()

    def _get_any_ipv4_network_object(self) -> str:
        url = f"{self.api_client.configuration.host}/v1/cdfmc/api/fmc_config/v1/domain/{self.cdfmc_domain_uid}/object/networks?filter=nameOrValue%3Aany-ipv4"
        headers = {
            "Authorization": f"Bearer {self.api_client.configuration.access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data["paging"]["count"] != 1:
            raise RuntimeError(
                "Expected exactly one network object with name 'any-ipv4'"
            )

        return data["items"][0]["id"]

    def _get_gambling_category_id(self) -> str:
        url = f"{self.api_client.configuration.host}/v1/cdfmc/api/fmc_config/v1/domain/{self.cdfmc_domain_uid}/object/urlcategories?limit=200"
        headers = {
            "Authorization": f"Bearer {self.api_client.configuration.access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        url_categories = response.json()["items"]

        gambling_categories = [
            category for category in url_categories if category["name"] == "Gambling"
        ]
        return gambling_categories[0]["id"]
