from services.scc_credentials_service import SccCredentialsService


def main():
    service = SccCredentialsService()
    service.load_or_prompt_credentials()
    api_token, base_url = service.get_credentials()
    print(f"API Token: {api_token}")
    print(f"Base URL: {base_url}")


if __name__ == "__main__":
    main()
