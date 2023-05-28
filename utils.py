import json


def get_cookie_dict(cookies: str) -> dict:
    result = {}

    pairs = cookies.split('; ')
    for pair in pairs:
        items = pair.split("=")
        key = items[0]

        if len(items) == 2:
            value = items[1]
        else:
            value = "=".join(items[1:])

        result[key] = value

    return result


def get_headers_from_nodejs_fetch_string(fetch: str) -> dict:
    data = fetch.split('"headers": ')[1].split(',\n  "body"')[0]
    headers = json.loads(data)
    return headers


def get_headers_from_firefox_headers_dump(dump: str) -> dict:
    result = {}

    pairs = [x for x in dump.split('\n') if x and ":" in x]
    for pair in pairs:
        items = pair.split(": ")
        key = items[0]

        if len(items) == 2:
            value = items[1]
        else:
            value = ": ".join(items[1:])

        result[key] = value

    return result