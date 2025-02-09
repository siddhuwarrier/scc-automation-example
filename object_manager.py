import click
from click_option_group import optgroup, AllOptionGroup

from commands.add_ips_to_object_group import add_ips_to_object_group
from services.scc_credentials_service import SccCredentialsService
from utils.region_mapping import supported_regions


@click.group()
@optgroup.group("API Credentials", cls=AllOptionGroup)
@optgroup.option(
    "--region",
    help="The region for the API.",
    type=click.Choice(supported_regions),
)
@optgroup.option("--api-token", type=str, help="The API token.")
@click.pass_context
def cli(ctx: any, api_token: str, region: str) -> None:
    credentials_service = SccCredentialsService(region=region, api_token=api_token)
    credentials_service.load_or_prompt_credentials()
    retrieved_api_token, base_url = credentials_service.get_credentials()
    ctx.obj["base_url"] = base_url
    ctx.obj["api_token"] = retrieved_api_token


cli.add_command(add_ips_to_object_group)

if __name__ == "__main__":
    cli(obj={})
