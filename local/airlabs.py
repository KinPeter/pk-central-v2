import os
import requests
from dotenv import load_dotenv

load_dotenv()

airlabs_api_key = os.getenv("AIRLABS_API_KEY")


def get_base_url(api_name):
    return f"https://airlabs.co/api/v9/{api_name}?api_key={airlabs_api_key}&"


# response = requests.get(f"{get_base_url("countries")}continent=SA")
response = requests.get(f"{get_base_url("airports")}country_code=HU")

print(response.json()["response"])
