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


ENV = get_env("ENV", "production")

LIVEKIT_URL = must_have_env("LIVEKIT_URL")
LIVEKIT_API_KEY = must_have_env("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = must_have_env("LIVEKIT_API_SECRET")

S3_BUCKET = get_env("S3_BUCKET", "gymbo")
S3_REGION = get_env("S3_REGION", "ap-southeast-7")
S3_ENDPOINT = get_env(
    "S3_ENDPOINT", "http://localhost:9000" if ENV == "local" else None
)
S3_ACCESS_KEY = must_have_env("S3_ACCESS_KEY")
S3_SECRET = must_have_env("S3_SECRET")
