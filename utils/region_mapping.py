from questionary import Choice

supported_regions = ["us", "eu", "aus", "apj", "in", "staging", "scale", "localhost"]
supported_regions_choices = [
    Choice(value="us", title="United States"),
    Choice(value="eu", title="Europe"),
    Choice(value="aus", title="Australia"),
    Choice(value="apj", title="Asia Pacific Japan"),
    Choice(value="in", title="India"),
    Choice(
        value="localhost",
        title="Localhost (Cisco Developers only): you need to be running the microservices you need and the public-api-gateway on http://localhost:3077",
    ),
    Choice(value="staging", title="Staging (Cisco Developers only)"),
    Choice(value="scale", title="Scale (Cisco Developers only)"),
]


def get_scc_url(region):
    if region not in supported_regions:
        raise ValueError(f"Region {region} is not supported")
    elif region == "localhost":
        return "http://localhost:3077"
    return f"https://{region}.manage.security.cisco.com/api/rest"
