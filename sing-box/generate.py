import functools
import logging
import string
import subprocess
from typing import Tuple, Union

import requests


def load(path: str) -> string.Template:
    try:
        with open(path, "r") as f:
            tmpl = string.Template(f.read())
            return tmpl
    except IOError as e:
        logging.error(f"Error reading config from {path}: {e}")
        raise


def dump(path: str, data: str) -> None:
    try:
        with open(path, "w") as f:
            f.write(data)
    except IOError as e:
        logging.error(f"Error writing config to {path}: {e}")
        raise


def generate_config(template: string.Template, config_info: dict) -> str:
    try:
        logging.debug(template.get_identifiers())
        logging.debug(config_info)
        logging.debug({k: repr(v)[1:-1] for k, v in config_info.items()})
        logging.debug(
            {
                k: v.encode("unicode_escape").decode("utf-8")
                for k, v in config_info.items()
            }
        )
        config_info = {
            k: v.encode("unicode_escape").decode("utf-8")
            for k, v in config_info.items()
        }
        return template.substitute(config_info)
    except Exception as e:
        logging.error(f"Error generating config: {e}")
        raise


def generate_server_config(template: string.Template) -> str:
    config_info = {
        "password": get_random_data("password"),
        "uuid": get_random_data("uuid"),
        "private_key": get_random_data("certificate")[0],
        "certificate": get_random_data("certificate")[1],
    }
    return generate_config(template, config_info)


def generate_client_config(template: string.Template) -> str:
    config_info = {
        "server_address": get_public_ip(),
        "password": get_random_data("password"),
        "uuid": get_random_data("uuid"),
        "certificate": get_random_data("certificate")[1],
    }
    return generate_config(template, config_info)


def print_config(config: dict) -> None:
    queue = [(config, "config")]
    kv = []
    while queue:
        node, prefix = queue.pop()
        if isinstance(node, list):
            for i, item in enumerate(node):
                queue.append((item, f"{prefix}[{i}]"))
        elif isinstance(node, dict):
            for key, value in node.items():
                queue.append((value, f'{prefix}["{key}"]'))
        else:
            kv.insert(0, f"{prefix} = {node}")

    logging.debug("\n".join(kv))


@functools.cache
def get_public_ip(url: str = "https://ipinfo.io/ip") -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        logging.error(f"Error fetching public IP: {e}")
        raise


@functools.cache
def get_random_data(type: str) -> Union[str, Tuple[str, str]]:
    COMMANDS = {
        "shell": "docker run --rm -it -v .:/etc/sing-box/ --entrypoint bash ghcr.io/sagernet/sing-box:latest",
        "prefix": "docker run --rm ghcr.io/sagernet/sing-box:latest",
        "check": "check -c config.json",
        "format": "format -w -c config.json",
        "rand": "generate rand 16 --base64",
        "uuid": "generate uuid",
        "certificate": f'generate tls-keypair {"www.mihoyo.com"} --months {12}',
    }

    match type:
        case "uuid":
            cmd = f"{COMMANDS['prefix']} {COMMANDS['uuid']}"
        case "password":
            cmd = f"{COMMANDS['prefix']} {COMMANDS['rand']}"
        case "certificate":
            cmd = f"{COMMANDS['prefix']} {COMMANDS['certificate']}"
        case _:
            cmd = f"{COMMANDS['prefix']} --help"

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logging.error(f"Error running command '{cmd}': {result.stderr}")
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    data = result.stdout.strip()
    match type:
        case "certificate":
            private_key, certificate = data.split("\n\n")
            return private_key.strip(), certificate.strip()
        case _:
            return data


def main():
    def process_config(d: dict) -> None:
        try:
            template = load(d["template"])
            config = d["method"](template)
            dump(d["output"], config)
        except Exception as e:
            logging.error(f"An error occurred while processing {d}: {e}")

    SERVER = {
        "template": "server/config.tmpl.json",
        "output": "server/config.json",
        "method": generate_server_config,
    }
    CLIENT = {
        "template": "client/config.tmpl.json",
        "output": "client/config.json",
        "method": generate_client_config,
    }
    process_config(SERVER)
    process_config(CLIENT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
