import csv
from typing import List
from cdo_sdk_python.models import UserInput
from email_validator import validate_email, EmailNotValidError
import questionary


class SccUsersParser:
    def __init__(self, users_csv_file: str):
        self.users_csv_file = users_csv_file

    def get_users(self) -> List[UserInput]:
        if self.users_csv_file:
            return self._parse_csv()
        else:
            return self._prompt_users()

    def _parse_csv(self) -> List[UserInput]:
        users = []
        with open(self.users_csv_file, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                users.append(
                    UserInput(
                        username=row["username"],
                        role=row["role"],
                        api_only_user=row["api_only_user"].lower() == "true",
                    )
                )
        return users

    @staticmethod
    def _prompt_users() -> List[UserInput]:
        users = []

        create_users = questionary.confirm(
            "Do you want to create users?", default=True
        ).ask()
        if not create_users:
            return users

        while True:
            api_only_user = questionary.confirm("API-only user?", default=True).ask()

            def validate_username(text):
                try:
                    if not api_only_user:
                        validate_email(text)
                    else:
                        if "@" in text:
                            raise EmailNotValidError(
                                "API-only user should not have an email address."
                            )
                    return True
                except EmailNotValidError as e:
                    return str(e)

            username = questionary.text("Username", validate=validate_username).ask()

            role = questionary.select(
                "Role",
                choices=[
                    "ROLE_SUPER_ADMIN",
                    "ROLE_ADMIN",
                    "ROLE_READ_ONLY",
                    "ROLE_EDIT_ONLY",
                    "ROLE_DEPLOY_ONLY",
                    "ROLE_VPN_SESSION_MANAGER",
                ],
            ).ask()

            users.append(
                UserInput(username=username, role=role, api_only_user=api_only_user)
            )

            create_another = questionary.confirm("Create another?", default=True).ask()

            if not create_another:
                break

        return users
