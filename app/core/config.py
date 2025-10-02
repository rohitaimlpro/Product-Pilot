import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")

settings = Settings()
