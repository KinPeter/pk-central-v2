import os


def get_allowed_origins() -> list[str]:
    pk_env = os.getenv("PK_ENV", "prod").lower()

    allow_origins = [
        "https://p-kin.com",
        "https://www.p-kin.com",
        "https://api.p-kin.com",
        "https://start.p-kin.com",
        "https://startv4.p-kin.com",
        "https://tripz.p-kin.com",
        "https://stuff.p-kin.com",
        "https://rddit.p-kin.com",
    ]

    if pk_env == "dev":
        allow_origins.append("http://localhost:5499")

    return allow_origins
