supported_regions = ["us", "eu", "aus", "apj", "in", "staging", "scale"]


def get_scc_url(region):
    if region not in supported_regions:
        raise ValueError(f"Region {region} is not supported")
    return f"https://{region}.manage.security.cisco.com/api/rest"
