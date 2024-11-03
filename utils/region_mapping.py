from questionary import Choice

supported_regions = ["us", "eu", "aus", "apj", "in", "staging", "scale"]
supported_regions_choices = [
    Choice(value="us", title="United States"),
    Choice(value="eu", title="Europe"),
    Choice(value="aus", title="Australia"),
    Choice(value="apj", title="Asia Pacific Japan"),
    Choice(value="in", title="India"),
]


def get_scc_url(region):
    if region not in supported_regions:
        raise ValueError(f"Region {region} is not supported")
    return f"https://{region}.manage.security.cisco.com/api/rest"
