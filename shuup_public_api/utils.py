import re


def convert_to_secure_url(url):
    regex = '^(http?)://'
    return re.sub(regex, 'https://', url)
