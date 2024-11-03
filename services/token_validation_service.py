from cdo_sdk_python import Configuration, UsersApi, ApiClient, ApiException


class TokenValidationService:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.api_token = api_token

    def validate_token(self):
        configuration = Configuration(host=self.base_url, access_token=self.api_token)
        with ApiClient(configuration) as api_client:
            api_instance = UsersApi(api_client)
            try:
                api_instance.get_token()
            except ApiException as e:
                return False
        return True
