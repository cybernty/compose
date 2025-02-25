import functools
import logging
import string
import subprocess
from typing import Tuple, Union

import requests


class ConfigGenerator:
    def __init__(self, template_path: str, output_path: str):
        self.template_path = template_path
        self.output_path = output_path
        self.template = self.load_template()

    def load_template(self) -> string.Template:
        try:
            with open(self.template_path, "r") as f:
                tmpl = string.Template(f.read())
                return tmpl
        except IOError as e:
            logging.error(f"Error reading config from {self.template_path}: {e}")
            raise

    def dump_config(self, data: str) -> None:
        try:
            with open(self.output_path, "w") as f:
                f.write(data)
        except IOError as e:
            logging.error(f"Error writing config to {self.output_path}: {e}")
            raise

    def generate_config(self, config_info: dict) -> str:
        try:
            logging.debug(self.template.get_identifiers())
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
            return self.template.substitute(config_info)
        except Exception as e:
            logging.error(f"Error generating config: {e}")
            raise

    def generate_specific_config(self) -> dict:
        raise NotImplementedError("Subclasses must implement this method")

    def process_config(self) -> None:
        try:
            config_info = self.generate_specific_config()
            config = self.generate_config(config_info)
            self.dump_config(config)
        except Exception as e:
            logging.error(
                f"An error occurred while processing {self.template_path}: {e}"
            )

    @staticmethod
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

    @staticmethod
    @functools.cache
    def get_public_ip(url: str = "https://ipinfo.io/ip") -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            logging.error(f"Error fetching public IP: {e}")
            raise

    @staticmethod
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


class ServerConfigGenerator(ConfigGenerator):
    def generate_specific_config(self) -> dict:
        return {
            "password": self.get_random_data("password"),
            "uuid": self.get_random_data("uuid"),
            "private_key": self.get_random_data("certificate")[0],
            "certificate": self.get_random_data("certificate")[1],
        }


class ClientConfigGenerator(ConfigGenerator):
    def generate_specific_config(self) -> dict:
        return {
            "server_address": self.get_public_ip(),
            "password": self.get_random_data("password"),
            "uuid": self.get_random_data("uuid"),
            "certificate": self.get_random_data("certificate")[1],
        }


def main():
    server_generator = ServerConfigGenerator(
        "server/config.tmpl.json", "server/config.json"
    )
    client_generator = ClientConfigGenerator(
        "client/config.tmpl.json", "client/config.json"
    )

    server_generator.process_config()
    client_generator.process_config()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
