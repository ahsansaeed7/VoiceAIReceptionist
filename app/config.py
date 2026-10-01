import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

CALCOM_API_KEY = os.environ.get("CALCOM_API_KEY")
CALCOM_EVENT_TYPE_ID = os.environ.get("CALCOM_EVENT_TYPE_ID")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
