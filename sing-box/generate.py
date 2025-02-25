import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from string import Template
from typing import Tuple

import requests


class NetworkUtils:
    @staticmethod
    def get_public_ip(url: str = "https://api.ipify.org") -> str:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            logging.error(f"Failed to get public IP: {e}")
            raise


class Commands:
    @staticmethod
    def run_docker_command(command: str) -> str:
        cmd = f"docker run --rm ghcr.io/sagernet/sing-box:latest {command}"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Run command failed: {e}")
            raise

    @staticmethod
    @cache
    def get_random_password() -> str:
        return Commands.run_docker_command("generate rand 16 --base64")

    @staticmethod
    @cache
    def get_uuid() -> str:
        return Commands.run_docker_command("generate uuid")

    @staticmethod
    @cache
    def get_certificate() -> Tuple[str, str]:
        result = Commands.run_docker_command(
            "generate tls-keypair www.mihoyo.com --months 12"
        )
        private_key, certificate = result.split("\n\n")
        return private_key.strip(), certificate.strip()


@dataclass
class ConfigFile:
    path: Path

    def read(self) -> str:
        try:
            return self.path.read_text()
        except IOError as e:
            logging.error(f"Failed to read {self.path}: {e}")
            raise

    def write(self, content: str) -> None:
        try:
            self.path.write_text(content)
        except IOError as e:
            logging.error(f"Failed to write {self.path}: {e}")
            raise


class ConfigGeneratorBase(ABC):
    def __init__(self, template_path: Path, output_path: Path):
        self.template = Template(ConfigFile(template_path).read())
        self.output_file = ConfigFile(output_path)

    @abstractmethod
    def get_config_data(self) -> dict[str, str]:
        pass

    def generate(self) -> None:
        try:
            config_data = self.get_config_data()
            escaped_data = {
                k: v.encode("unicode_escape").decode("utf-8")
                for k, v in config_data.items()
            }
            config = self.template.substitute(escaped_data)
            self.output_file.write(config)
        except Exception as e:
            logging.error(f"Config generation failed: {e}")
            raise


class ServerConfigGenerator(ConfigGeneratorBase):
    def get_config_data(self) -> dict[str, str]:
        password = Commands.get_random_password()
        uuid = Commands.get_uuid()
        private_key, certificate = Commands.get_certificate()
        return {
            "password": password,
            "uuid": uuid,
            "private_key": private_key,
            "certificate": certificate,
        }


class ClientConfigGenerator(ConfigGeneratorBase):
    def get_config_data(self) -> dict[str, str]:
        password = Commands.get_random_password()
        uuid = Commands.get_uuid()
        _, certificate = Commands.get_certificate()
        return {
            "server_address": NetworkUtils.get_public_ip(),
            "password": password,
            "uuid": uuid,
            "certificate": certificate,
        }


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    base_dir = Path(__file__).parent
    for config_type in ["server", "client"]:
        match config_type:
            case "server":
                generator_class = ServerConfigGenerator
            case "client":
                generator_class = ClientConfigGenerator
            case _:
                raise ValueError(f"Unknown config type: {config_type}")
        logging.debug(base_dir / config_type)
        generator = generator_class(
            template_path=base_dir / config_type / "config.tmpl.json",
            output_path=base_dir / config_type / "config.json",
        )
        generator.generate()


if __name__ == "__main__":
    main()
