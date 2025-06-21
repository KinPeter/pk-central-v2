import os


class PkCentralEnv:
    def __init__(
        self,
        root_path: str,
        mongodb_uri: str,
        mongodb_name: str,
        jwt_secret: str,
        login_code_expiry: str,
        token_expiry: str,
        notification_email: str,
        emails_allowed: str,
        email_host: str,
        email_user: str,
        email_pass: str,
        proxy_airlabs_airlines_url: str,
        proxy_airlabs_airports_url: str,
        proxy_location_reverse_url: str,
        proxy_deepl_translate_url: str,
        airlabs_api_key: str,
        location_iq_api_key: str,
        open_weather_map_api_key: str,
        unsplash_api_key: str,
        deepl_api_key: str,
        strava_client_id: str,
        strava_client_secret: str,
        gemini_api_key: str,
        reddit_client_id: str,
        reddit_client_secret: str,
        reddit_user: str,
        reddit_password: str,
        reddit_user_agent: str,
        pk_env: str,
    ):
        self.ROOT_PATH = root_path
        self.MONGODB_URI = mongodb_uri
        self.MONGODB_NAME = mongodb_name
        self.JWT_SECRET = jwt_secret
        self.LOGIN_CODE_EXPIRY = login_code_expiry
        self.TOKEN_EXPIRY = token_expiry
        self.NOTIFICATION_EMAIL = notification_email
        self.EMAILS_ALLOWED = emails_allowed
        self.EMAIL_HOST = email_host
        self.EMAIL_USER = email_user
        self.EMAIL_PASS = email_pass
        self.PROXY_AIRLABS_AIRLINES_URL = proxy_airlabs_airlines_url
        self.PROXY_AIRLABS_AIRPORTS_URL = proxy_airlabs_airports_url
        self.PROXY_LOCATION_REVERSE_URL = proxy_location_reverse_url
        self.PROXY_DEEPL_TRANSLATE_URL = proxy_deepl_translate_url
        self.AIRLABS_API_KEY = airlabs_api_key
        self.LOCATION_IQ_API_KEY = location_iq_api_key
        self.OPEN_WEATHER_MAP_API_KEY = open_weather_map_api_key
        self.UNSPLASH_API_KEY = unsplash_api_key
        self.DEEPL_API_KEY = deepl_api_key
        self.STRAVA_CLIENT_ID = strava_client_id
        self.STRAVA_CLIENT_SECRET = strava_client_secret
        self.GEMINI_API_KEY = gemini_api_key
        self.REDDIT_CLIENT_ID = reddit_client_id
        self.REDDIT_CLIENT_SECRET = reddit_client_secret
        self.REDDIT_USER = reddit_user
        self.REDDIT_PASSWORD = reddit_password
        self.REDDIT_USER_AGENT = reddit_user_agent
        self.PK_ENV = pk_env


def load_environment() -> PkCentralEnv:
    root_path = os.getenv("ROOT_PATH")
    if not root_path:
        raise ValueError("Missing required environment variable: ROOT_PATH")

    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("Missing required environment variable: MONGODB_URI")

    mongodb_name = os.getenv("MONGODB_NAME")
    if not mongodb_name:
        raise ValueError("Missing required environment variable: MONGODB_NAME")

    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise ValueError("Missing required environment variable: JWT_SECRET")

    login_code_expiry = os.getenv("LOGIN_CODE_EXPIRY")
    if not login_code_expiry:
        raise ValueError("Missing required environment variable: LOGIN_CODE_EXPIRY")

    token_expiry = os.getenv("TOKEN_EXPIRY")
    if not token_expiry:
        raise ValueError("Missing required environment variable: TOKEN_EXPIRY")

    notification_email = os.getenv("NOTIFICATION_EMAIL")
    if not notification_email:
        raise ValueError("Missing required environment variable: NOTIFICATION_EMAIL")

    emails_allowed = os.getenv("EMAILS_ALLOWED")
    if not emails_allowed:
        raise ValueError("Missing required environment variable: EMAILS_ALLOWED")

    email_host = os.getenv("EMAIL_HOST")
    if not email_host:
        raise ValueError("Missing required environment variable: EMAIL_HOST")

    email_user = os.getenv("EMAIL_USER")
    if not email_user:
        raise ValueError("Missing required environment variable: EMAIL_USER")

    email_pass = os.getenv("EMAIL_PASS")
    if not email_pass:
        raise ValueError("Missing required environment variable: EMAIL_PASS")

    proxy_airlabs_airlines_url = os.getenv("PROXY_AIRLABS_AIRLINES_URL")
    if not proxy_airlabs_airlines_url:
        raise ValueError(
            "Missing required environment variable: PROXY_AIRLABS_AIRLINES_URL"
        )

    proxy_airlabs_airports_url = os.getenv("PROXY_AIRLABS_AIRPORTS_URL")
    if not proxy_airlabs_airports_url:
        raise ValueError(
            "Missing required environment variable: PROXY_AIRLABS_AIRPORTS_URL"
        )

    proxy_location_reverse_url = os.getenv("PROXY_LOCATION_REVERSE_URL")
    if not proxy_location_reverse_url:
        raise ValueError(
            "Missing required environment variable: PROXY_LOCATION_REVERSE_URL"
        )

    proxy_deepl_translate_url = os.getenv("PROXY_DEEPL_TRANSLATE_URL")
    if not proxy_deepl_translate_url:
        raise ValueError(
            "Missing required environment variable: PROXY_DEEPL_TRANSLATE_URL"
        )

    airlabs_api_key = os.getenv("AIRLABS_API_KEY")
    if not airlabs_api_key:
        raise ValueError("Missing required environment variable: AIRLABS_API_KEY")

    location_iq_api_key = os.getenv("LOCATION_IQ_API_KEY")
    if not location_iq_api_key:
        raise ValueError("Missing required environment variable: LOCATION_IQ_API_KEY")

    open_weather_map_api_key = os.getenv("OPEN_WEATHER_MAP_API_KEY")
    if not open_weather_map_api_key:
        raise ValueError(
            "Missing required environment variable: OPEN_WEATHER_MAP_API_KEY"
        )

    unsplash_api_key = os.getenv("UNSPLASH_API_KEY")
    if not unsplash_api_key:
        raise ValueError("Missing required environment variable: UNSPLASH_API_KEY")

    deepl_api_key = os.getenv("DEEPL_API_KEY")
    if not deepl_api_key:
        raise ValueError("Missing required environment variable: DEEPL_API_KEY")

    strava_client_id = os.getenv("STRAVA_CLIENT_ID")
    if not strava_client_id:
        raise ValueError("Missing required environment variable: STRAVA_CLIENT_ID")

    strava_client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    if not strava_client_secret:
        raise ValueError("Missing required environment variable: STRAVA_CLIENT_SECRET")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("Missing required environment variable: GEMINI_API_KEY")

    reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    if not reddit_client_id:
        raise ValueError("Missing required environment variable: REDDIT_CLIENT_ID")

    reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not reddit_client_secret:
        raise ValueError("Missing required environment variable: REDDIT_CLIENT_SECRET")

    reddit_user = os.getenv("REDDIT_USER")
    if not reddit_user:
        raise ValueError("Missing required environment variable: REDDIT_USER")

    reddit_password = os.getenv("REDDIT_PASSWORD")
    if not reddit_password:
        raise ValueError("Missing required environment variable: REDDIT_PASSWORD")

    reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
    if not reddit_user_agent:
        raise ValueError("Missing required environment variable: REDDIT_USER_AGENT")

    pk_env = os.getenv("PK_ENV")
    if not pk_env:
        raise ValueError("Missing required environment variable: PK_ENV")

    return PkCentralEnv(
        root_path=root_path,
        mongodb_uri=mongodb_uri,
        mongodb_name=mongodb_name,
        jwt_secret=jwt_secret,
        login_code_expiry=login_code_expiry,
        token_expiry=token_expiry,
        notification_email=notification_email,
        emails_allowed=emails_allowed,
        email_host=email_host,
        email_user=email_user,
        email_pass=email_pass,
        proxy_airlabs_airlines_url=proxy_airlabs_airlines_url,
        proxy_airlabs_airports_url=proxy_airlabs_airports_url,
        proxy_location_reverse_url=proxy_location_reverse_url,
        proxy_deepl_translate_url=proxy_deepl_translate_url,
        airlabs_api_key=airlabs_api_key,
        location_iq_api_key=location_iq_api_key,
        open_weather_map_api_key=open_weather_map_api_key,
        unsplash_api_key=unsplash_api_key,
        deepl_api_key=deepl_api_key,
        strava_client_id=strava_client_id,
        strava_client_secret=strava_client_secret,
        gemini_api_key=gemini_api_key,
        reddit_client_id=reddit_client_id,
        reddit_client_secret=reddit_client_secret,
        reddit_user=reddit_user,
        reddit_password=reddit_password,
        reddit_user_agent=reddit_user_agent,
        pk_env=pk_env,
    )
