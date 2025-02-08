from dotenv import load_dotenv
import os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(dotenv_path=os.path.join(root_path, ".env"))


def must_have_env(env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        raise ValueError(f"Missing environment variable {env_name}")

    return value


def get_env(env_name: str, default: str = None) -> str:
    return os.getenv(env_name, default)


LIVEKIT_URL = must_have_env("LIVEKIT_URL")
LIVEKIT_API_KEY = must_have_env("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = must_have_env("LIVEKIT_API_SECRET")
