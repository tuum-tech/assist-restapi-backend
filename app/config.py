# -*- coding: utf-8 -*-
import json

from decouple import config

BRAND_NAME = "Assist REST API"

SECRET_KEY = config('SECRET_KEY', default="assist-restapi-secret-key", cast=str)

PRODUCTION = config('PRODUCTION', default=False, cast=bool)

LOG_LEVEL = "DEBUG"

DEBUG = True

CRON_INTERVAL = config('CRON_INTERVAL', default=100, cast=int)
CRON_INTERVAL_V2 = config('CRON_INTERVAL_V2', default=8, cast=int)

REQUEST_TIMEOUT = 30

MONGO = {
    "DATABASE": config('MONGO_DATABASE', default="assistdb", cast=str),
    "HOST": config('MONGO_HOST', default="localhost", cast=str),
    "PORT": config('MONGO_PORT', default=27017, cast=int),
    "USERNAME": config('MONGO_USERNAME', default="mongoadmin", cast=str),
    "PASSWORD": config('MONGO_PASSWORD', default="mongopass", cast=str)
}
if PRODUCTION:
    MONGO_CONNECT_HOST = "mongodb+srv://" + MONGO['USERNAME'] + ":" + MONGO['PASSWORD'] + "@" + \
                         MONGO['HOST'] + "/?retryWrites=true&w=majority"
else:
    MONGO_CONNECT_HOST = "mongodb://" + MONGO['USERNAME'] + ":" + MONGO['PASSWORD'] + "@" + \
                         MONGO['HOST'] + ":" + str(MONGO['PORT']) + "/?authSource=admin"

SERVICE_STATUS_PENDING = "Pending"
SERVICE_STATUS_PROCESSING = "Processing"
SERVICE_STATUS_QUARANTINE = "Quarantined"
SERVICE_STATUS_REJECTED = "Rejected"
SERVICE_STATUS_COMPLETED = "Completed"
SERVICE_STATUS_CANCELLED = "Cancelled"

DID_SIDECHAIN_RPC_URL = config('DID_SIDECHAIN_RPC_URL', default="http://api.elastos.io:20606", cast=str)

DID_SIDECHAIN_RPC_URL_ETH = config('DID_SIDECHAIN_RPC_URL_ETH', default="https://api.elastos.io/eid",
                                   cast=str)
DID_CONTRACT_ADDRESS = config('DID_CONTRACT_ADDRESS', default="0x46E5936a9bAA167b3368F4197eDce746A66f7a7a", cast=str)
DID_CHAIN_ID = config('DID_CHAIN_ID', default=22, cast=int)

# Service Types
SERVICE_DIDPUBLISH = "did_publish"
SERVICE_MEDIAUPLOAD = "media_upload"  # Unused service

# Service Limits
SERVICE_DIDPUBLISH_DAILY_LIMIT = config("DID_PUBLISH_DAILY_LIMIT", default=10, cast=int)


def get_wallets():
    wallets = []
    i = 1
    while True:
        address = config("WALLET{0}_ADDRESS".format(i), default=None)
        private_key = config("WALLET{0}_PRIVATE_KEY".format(i), default=None)
        public_key = config("WALLET{0}_PUBLIC_KEY".format(i), default=None)
        if not address:
            break
        else:
            wallet = {
                "address": address,
                "private_key": private_key,
                "public_key": public_key
            }
            wallets.append(wallet)
        i += 1
    return wallets


def get_walletsV2():
    wallets = []
    i = 1
    while True:
        wallet = config("WALLET{0}_ETH".format(i), default=None)
        if not wallet:
            break
        wallets.append(wallet)
        i += 1
    return wallets


# Retrieve wallet details
WALLETS = get_wallets()
NUM_WALLETS = len(WALLETS)

WALLETSV2 = get_walletsV2()
NUM_WALLETSV2 = len(WALLETSV2)
WALLETSV2_PASS = config('WALLET_ETH_PASS', default="", cast=str)

EMAIL = {
    "SENDER": config('EMAIL_SENDER', default="test@test.com", cast=str),
    "SMTP_SERVER": config('EMAIL_SMTP_SERVER', default="smtp.example.com", cast=str),
    "SMTP_PORT": config('EMAIL_SMTP_PORT', default="", cast=str),
    "SMTP_USERNAME": config('EMAIL_SMTP_USERNAME', default="support@example.com", cast=str),
    "SMTP_PASSWORD": config('EMAIL_SMTP_PASSWORD', default="password", cast=str),
    "SMTP_TLS": config('EMAIL_SMTP_TLS', default=False, cast=bool),
}

SLACK_TOKEN = config('SLACK_TOKEN', default="slack-token", cast=str)

# Rate limit for creating/updating DIDs(100 calls per minute)
RATE_LIMIT_CREATE_DID = 1000
# Rate limit for all other APIs(10K calls per minute)
RATE_LIMIT_CALLS = 10000
RATE_LIMIT_PERIOD = 60
