import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
APP_ID = os.getenv("AEON_APP_ID")
SECRET_KEY = os.getenv("AEON_SECRET_KEY")
BASE_URL = os.getenv("AEON_BASE_URL", "https://sbx-crypto-payment-api.aeon.xyz")

# Telegram Bot Configuration
TG_TOKEN = os.getenv("TG_TOKEN")
TMA_URL = os.getenv("TMA_URL", "https://tma.anycraft.io/")
API_URL = os.getenv("API_URL", "https://api.anycraft.io/api/v1/")

# Telegram Channel Links
COMMUNITY_LINK = os.getenv("COMMUNITY_LINK", "https://t.me/anycraft_community")
CHAT_EN_LINK = os.getenv("CHAT_EN_LINK", "https://t.me/anycraft_chat_en")
CHAT_RU_LINK = os.getenv("CHAT_RU_LINK", "https://t.me/anycraft_chat_ru")
SITE_LINK = os.getenv("SITE_LINK", "https://anycraft.io")

# Environment settings
PRODUCTION = os.getenv("PRODUCTION", "true").lower() == "true"
IS_RC = os.getenv("IS_RC", "false").lower() == "true"

# Authorized users for testing
AUTHORIZED_USERS = [
    327090911,  # danikula
    12390,      # Alex_mm3
    376061527,  # alshund
    180986213,  # collapserage
    7271210433, # anycrafter
    5171688020, # Ello4kaludoedka
    41800908,   # ala_mel
    118658613,  # str117117 (M X)
    428099563,  # OxMkindly
    5712793143, # Phil
]
