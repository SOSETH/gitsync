import re

regex = re.compile("^(https://)([^:]+):([^@]+)(@.*)$")


def filter_url(url: str) -> str:
    matches = regex.match(url)
    if matches is None:
        return url
    else:
        groups = matches.groups()
        return groups[0] + '*****:*****' + groups[3]
