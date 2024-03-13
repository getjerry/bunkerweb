#!/usr/bin/env python3

from os import getenv, sep
from os.path import join
from pathlib import Path
from sys import exit as sys_exit, path as sys_path
from threading import Lock
from traceback import format_exc

for deps_path in [join(sep, "usr", "share", "bunkerweb", *paths) for paths in (("deps", "python"), ("utils",), ("api",), ("db",))]:
    if deps_path not in sys_path:
        sys_path.append(deps_path)

from Database import Database  # type: ignore
from common_utils import get_integration  # type: ignore
from logger import setup_logger  # type: ignore
from API import API  # type: ignore

LOGGER = setup_logger("Lets-encrypt.auth", getenv("LOG_LEVEL", "INFO"))
status = 0

try:
    # Get env vars
    token = getenv("CERTBOT_TOKEN", "")
    validation = getenv("CERTBOT_VALIDATION", "")
    integration = get_integration()

    LOGGER.info(f"Detected {integration} integration")

    # Cluster case
    if integration in ("Docker", "Swarm", "Kubernetes", "Autoconf"):
        db = Database(LOGGER, sqlalchemy_string=getenv("DATABASE_URI", None))
        lock = Lock()

        with lock:
            instances = db.get_instances()

        LOGGER.info(f"Sending challenge to {len(instances)} instances")
        for instance in instances:
            api = API(f"http://{instance['hostname']}:{instance['port']}", host=instance["server_name"])
            sent, err, status, resp = api.request("POST", "/lets-encrypt/challenge", data={"token": token, "validation": validation})
            if not sent:
                status = 1
                LOGGER.error(f"Can't send API request to {api.endpoint}/lets-encrypt/challenge : {err}")
            elif status != 200:
                status = 1
                LOGGER.error(f"Error while sending API request to {api.endpoint}/lets-encrypt/challenge : status = {resp['status']}, msg = {resp['msg']}")
            else:
                LOGGER.info(f"Successfully sent API request to {api.endpoint}/lets-encrypt/challenge")

    # Linux case
    else:
        root_dir = Path(sep, "var", "tmp", "bunkerweb", "lets-encrypt", ".well-known", "acme-challenge")
        root_dir.mkdir(parents=True, exist_ok=True)
        root_dir.joinpath(token).write_text(validation, encoding="utf-8")
except:
    status = 1
    LOGGER.error(f"Exception while running certbot-auth.py :\n{format_exc()}")

sys_exit(status)
