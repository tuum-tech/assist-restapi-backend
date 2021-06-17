import json
from decouple import config

BRAND_NAME = "Assist REST API"

SECRET_KEY = config('SECRET_KEY', default="assist-restapi-secret-key", cast=str)

PRODUCTION = config('PRODUCTION', default=False, cast=bool)

LOG_LEVEL = "DEBUG"

DEBUG = True

CRON_INTERVAL = config('CRON_INTERVAL', default=100, cast=int)
CRON_INTERVAL_V2 = config('CRON_INTERVAL_V2', default=10, cast=int)

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
SERVICE_STATUS_COMPLETED = "Completed"
SERVICE_STATUS_CANCELLED = "Cancelled"

DID_SIDECHAIN_RPC_URL = config('DID_SIDECHAIN_RPC_URL', default="http://api.elastos.io:20606", cast=str)

DID_SIDECHAIN_RPC_URL_ETH = config('DID_SIDECHAIN_RPC_URL_ETH', default="https://api-testnet.elastos.io/newid",
                                   cast=str)
DID_CONTRACT_ADDRESS = config('DID_CONTRACT_ADDRESS', default="0x8b2324fd40a74843711C9B48BC968A5FAEdd4Ef0", cast=str)
DID_CHAIN_ID = config('DID_CHAIN_ID', default=23, cast=int)

# Service Types
SERVICE_DIDPUBLISH = "did_publish"
SERVICE_MEDIAUPLOAD = "media_upload"  # Unused service

# Service Limits
SERVICE_DIDPUBLISH_DAILY_LIMIT = config("DID_PUBLISH_DAILY_LIMIT", default=5, cast=int)


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
    """
    wallets = []
    i = 1
    while True:
        wallet = config("WALLET{0}_ETH".format(i), default=None)
        if not wallet:
            break
        else:
            wallets.append({
                "index": i,
                "wallet": wallet
            })
        i += 1
    """
    # TEMPORARY SOLUTION
    wallets = [{"address": "bf98b9e5d8928c6ba7f4042dcfdaa3fcd814353f", "id": "bb9ca163-fdc1-4dea-886b-83542fdae020",
                "version": 3, "crypto": {"cipher": "aes-128-ctr",
                                         "ciphertext": "bf8ce2283f647d3e4b465b9b91f530762cbf6f9f45b035e454b66ae8710c836f",
                                         "cipherparams": {"iv": "09532875f31328ee5081ceea424056ad"}, "kdf": "scrypt",
                                         "kdfparams": {"dklen": 32, "n": 262144, "p": 1, "r": 8,
                                                       "salt": "abc0ae042ffdc31e5f226dfb08e9d2491b9f439c6c1413b64530c41de3aa66ce"},
                                         "mac": "0a5dcc4515d00c6a68b407af47bcd0bcc4d3dc57cc9a4c82ef50012ccb483b05"}},
               {"address": "284b5c872ed38f556a032bfba35697cbd8a92dfc", "id": "cd6aca37-f1b3-45b2-b34d-01b623a58dd0",
                "version": 3, "crypto": {"cipher": "aes-128-ctr",
                                         "ciphertext": "2342ad0beeee064e79188fb82462b93a5d9362fb972af2a7dc12f4413d7a767c",
                                         "cipherparams": {"iv": "68c56057cd3316395f55fd750f44bb05"}, "kdf": "scrypt",
                                         "kdfparams": {"dklen": 32, "n": 262144, "p": 1, "r": 8,
                                                       "salt": "f99fd47de058ef961a377da2e4420aa13748ced384875cd4d461081196028a41"},
                                         "mac": "21daf1bb67fdf7bb97178d4ec78fc946c286539614504b4a2fe0e1e673c687fa"}},
               {"address": "b10f3dcaf6e30c768fc62d005f19c28c56070353", "id": "f80072bb-46ce-4a89-af11-915488d263d3",
                "version": 3, "crypto": {"cipher": "aes-128-ctr",
                                         "ciphertext": "45caddfb7b00eb00608a7aff454580051e3516e266b72b053dd926ffa16b5710",
                                         "cipherparams": {"iv": "d247c802a971ef563a3d0dc0a7c5759f"}, "kdf": "scrypt",
                                         "kdfparams": {"dklen": 32, "n": 262144, "p": 1, "r": 8,
                                                       "salt": "8cc1687234de453f25ab455847ce4a99c6e7b7fd12832232ae6179ecb49e0677"},
                                         "mac": "a1c6ffa238bde2d0491c5b8c48598013aa3d8c0b757cd9cddcdc00596290a08e"}},
               {"address": "ba3d887eceb26352fa08c733e99cde1daf840621", "id": "952da5a0-1cba-4bc3-89d6-7032dfdd254b",
                "version": 3, "crypto": {"cipher": "aes-128-ctr",
                                         "ciphertext": "c31187aaba3e080f43502ed5c9b367417f2fa425713cf53dc80efb024dffdf03",
                                         "cipherparams": {"iv": "fa3e61517faacd65906cb52b8d0cad87"}, "kdf": "scrypt",
                                         "kdfparams": {"dklen": 32, "n": 262144, "p": 1, "r": 8,
                                                       "salt": "7928b17899da1178f4dfb2b29f66a30b77f44eb3c0c7c07371d96865e59661c6"},
                                         "mac": "6106444fe3d664ddcd2ac05e9ce299494befe4537e4ff61fb10f4ef095ae71a6"}},
               {"address": "1a5aafb994c6b485241a1f53589896dc86e8eaf5", "id": "6efb9119-9be3-4784-8f6b-0a325c3fca48",
                "version": 3, "crypto": {"cipher": "aes-128-ctr",
                                         "ciphertext": "83464af8f3f32d2639998c75441b486f2d8ec24e12aa168a8891c83628ed0dff",
                                         "cipherparams": {"iv": "eeedeb84ceebfc7843d581882d3f4ebe"}, "kdf": "scrypt",
                                         "kdfparams": {"dklen": 32, "n": 262144, "p": 1, "r": 8,
                                                       "salt": "5233bc07fc544623660fbd250b397940820d566691bbd2f0f304f70def457ef9"},
                                         "mac": "b92648d30cd6b34e988866871d5ce2d69c3f9bf20b585eeda7971dda91f793d7"}}]

    return wallets


# Retrieve wallet details
WALLETS = get_wallets()
NUM_WALLETS = len(WALLETS)

WALLETSV2 = get_walletsV2()
NUM_WALLETSV2 = len(WALLETSV2)

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
RATE_LIMIT_CREATE_DID = 100
# Rate limit for all other APIs(10K calls per minute)
RATE_LIMIT_CALLS = 10000
RATE_LIMIT_PERIOD = 60
