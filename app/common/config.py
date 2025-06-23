from app.common.environment import PkCentralEnv


def get_allowed_origins(env: PkCentralEnv) -> list[str]:
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

    if env.PK_ENV == "dev":
        allow_origins.append("http://localhost:5499")

    return allow_origins
