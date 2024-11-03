# services/scc_credentials_service.py
import os
import yaml
from services.token_validation_service import TokenValidationService
from utils.interactive_cli import get_region_and_api_token
from utils.region_mapping import get_scc_url


class SccCredentialsService:
    def __init__(
        self, config_file_path="~/.cisco-security.yaml", region=None, api_token=None
    ):
        self.config_file_path = os.path.expanduser(config_file_path)
        self.region = region
        self.api_token = api_token
        self.base_url = None

    def load_or_prompt_credentials(self):
        if self.region and self.api_token:
            self.map_region_to_base_url()
            if not TokenValidationService(
                self.base_url, self.api_token
            ).validate_token():
                raise ValueError("The provided API token is invalid.")
        else:
            if not os.path.exists(self.config_file_path):
                self.prompt_and_save_credentials()
            else:
                self.load_credentials()

            if not TokenValidationService(
                self.base_url, self.api_token
            ).validate_token():
                print(
                    "The API token in ~/.cisco-security.yaml is invalid. Please re-enter your credentials."
                )
                self.prompt_and_save_credentials()

    def prompt_and_save_credentials(self):
        self.region, self.api_token = get_region_and_api_token()
        config = {"scc.region": self.region, "scc.api-token": self.api_token}
        with open(self.config_file_path, "w") as file:
            yaml.safe_dump(config, file)
        self.map_region_to_base_url()

    def load_credentials(self):
        with open(self.config_file_path, "r") as file:
            config = yaml.safe_load(file)
        self.region = config.get("scc.region")
        self.api_token = config.get("scc.api-token")
        if not self.region or not self.api_token:
            raise ValueError(
                "Both 'scc.region' and 'scc.api-token' must be specified in the configuration file."
            )
        self.map_region_to_base_url()

    def map_region_to_base_url(self):
        self.base_url = get_scc_url(self.region)
        if not self.base_url:
            raise ValueError(f"Invalid region specified: {self.region}")

    def get_credentials(self):
        return self.api_token, self.base_url
