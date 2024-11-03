import sys

import jwt
import questionary
from cdo_sdk_python import Configuration


from utils.region_mapping import supported_regions, supported_regions_choices


def validate_region(region: str) -> bool:
    return region in supported_regions


def validate_api_token(api_token: str) -> bool:
    try:
        jwt.decode(api_token, options={"verify_signature": False})
        return True
    except jwt.InvalidTokenError:
        return False


def get_region_and_api_token():
    try:
        region = questionary.select(
            "Select the region:", choices=supported_regions_choices
        ).ask()

        if not validate_region(region):
            raise f"Invalid region specified: {region}"

        while True:
            try:
                api_token = questionary.password("Enter the API token:").ask()
                if validate_api_token(api_token):
                    break
                print("Invalid API token. Please try again.")
            except KeyboardInterrupt:
                exit(1)

        return region, api_token
    except KeyboardInterrupt:
        exit(1)
