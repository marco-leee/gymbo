"""MongoDB connection settings from environment.

- ``MONGODB_URI`` or ``MONGO_URI`` (fallback): full connection string (optional query params).
- ``MONGODB_DATABASE``: database name (default ``gymbo``).
- ``MONGODB_AUTH_SOURCE``: if set and URI has no ``authSource=``, it is appended (e.g. ``gymbo`` for users created with ``use gymbo`` and ``db.createUser``, or ``admin`` if the user lives in ``admin``).
- ``MONGODB_USE_TRANSACTIONS``: default ``0``. Set ``1`` only for replica set / sharded deployments; standalone mongod raises IllegalOperation for transactions.

Example (user scoped to ``gymbo`` DB)::

    export MONGODB_URI='mongodb://gymbo:gymbo@localhost:27017'
    export MONGODB_AUTH_SOURCE=gymbo
    export MONGODB_USE_TRANSACTIONS=0
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class MongoSettings:
    uri: str
    database: str
    use_transactions: bool


def load_mongo_settings() -> MongoSettings:
    uri = os.environ.get("MONGODB_URI") or os.environ.get(
        "MONGO_URI", "mongodb://gymbo:gymbo@localhost:27017"
    )
    auth_source = os.environ.get("MONGODB_AUTH_SOURCE", "admin").strip()
    if auth_source and "authSource=" not in uri:
        sep = "&" if "?" in uri else "?"
        uri = f"{uri}{sep}authSource={auth_source}"

    database = os.environ.get("MONGODB_DATABASE", "gymbo")
    # Standalone mongod (typical Docker) does not support transactions; use replica set + true, or 0 locally.
    tx_raw = os.environ.get("MONGODB_USE_TRANSACTIONS", "0").lower()
    use_transactions = tx_raw not in ("0", "false", "no", "off")
    return MongoSettings(uri=uri, database=database, use_transactions=use_transactions)
