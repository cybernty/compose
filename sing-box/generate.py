import functools
import json
import requests
import subprocess
import logging

server_template_path = "server/template.json"
client_template_path = "client/template.json"
server_config_path = "server/config.json"
client_config_path = "client/config.json"


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        data = json.load(f)
    return data


def dump_config(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def generate_server_config(template: dict) -> dict:
    config = template.copy()
    passwd = get_random_data("password")
    uuid = get_random_data("uuid")
    private_key, certificate = get_random_data("certificate")

    print_config(config)
    config["inbounds"][0]["password"] = passwd
    config["inbounds"][1]["users"][0]["uuid"] = uuid
    config["inbounds"][2]["users"][0]["password"] = passwd
    config["inbounds"][3]["users"][0]["password"] = passwd
    config["inbounds"][4]["users"][0]["password"] = passwd
    config["inbounds"][5]["password"] = passwd
    config["inbounds"][6]["users"][0]["uuid"] = uuid
    config["inbounds"][7]["users"][0]["uuid"] = uuid
    config["inbounds"][7]["users"][0]["password"] = passwd
    config["inbounds"][7]["tls"]["certificate"] = certificate
    config["inbounds"][6]["tls"]["certificate"] = certificate
    config["inbounds"][3]["tls"]["certificate"] = certificate
    config["inbounds"][2]["tls"]["certificate"] = certificate
    config["inbounds"][7]["tls"]["key"] = private_key
    config["inbounds"][6]["tls"]["key"] = private_key
    config["inbounds"][3]["tls"]["key"] = private_key
    config["inbounds"][2]["tls"]["key"] = private_key

    return config


def generate_client_config(template: dict) -> dict:
    config = template.copy()
    public_ip = get_public_ip()
    passwd = get_random_data("password")
    uuid = get_random_data("uuid")
    _, certificate = get_random_data("certificate")

    print_config(config)
    config["outbounds"][1]["server"] = public_ip
    config["outbounds"][1]["password"] = passwd
    config["outbounds"][2]["server"] = public_ip
    config["outbounds"][2]["uuid"] = uuid
    config["outbounds"][3]["server"] = public_ip
    config["outbounds"][3]["password"] = passwd
    config["outbounds"][4]["password"] = passwd
    config["outbounds"][5]["server"] = public_ip
    config["outbounds"][5]["password"] = passwd
    config["outbounds"][6]["server"] = public_ip
    config["outbounds"][6]["uuid"] = uuid
    config["outbounds"][7]["server"] = public_ip
    config["outbounds"][7]["uuid"] = uuid
    config["outbounds"][7]["password"] = passwd
    config["outbounds"][8]["server"] = public_ip
    config["outbounds"][8]["password"] = passwd
    config["outbounds"][8]["tls"]["certificate"] = certificate
    config["outbounds"][7]["tls"]["certificate"] = certificate
    config["outbounds"][6]["tls"]["certificate"] = certificate
    config["outbounds"][3]["tls"]["certificate"] = certificate

    return config


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
    return requests.get(url).text


@functools.cache
def get_random_data(type: str) -> str | tuple[str, str]:
    cmds = {
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
            cmd = f"{cmds['prefix']} {cmds['uuid']}"
        case "password":
            cmd = f"{cmds['prefix']} {cmds['rand']}"
        case "certificate":
            cmd = f"{cmds['prefix']} {cmds['certificate']}"
        case _:
            cmd = f"{cmds['prefix']} --help"

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
    )

    match type:
        case "certificate":
            private_key, certificate = (
                result.stdout.decode("utf-8").strip().split("\n\n")
            )
            return (private_key.strip(), certificate.strip())
        case _:
            return result.stdout.decode("utf-8").strip()


def main():
    server_template = load_config(server_template_path)
    server_config = generate_server_config(server_template)
    dump_config(server_config_path, server_config)

    client_template = load_config(client_template_path)
    client_config = generate_client_config(client_template)
    dump_config(client_config_path, client_config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
