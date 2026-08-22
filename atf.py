import asyncio
import json
import random
import re
import sys
import time
import uuid
import inspect

from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import parse_qs

import httpx
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich import box
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import RequestWebViewRequest
from telethon.tl.types import KeyboardButtonWebView


# ==============================================================
# PATH
# ==============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "config.json"
QUERY_PATH = BASE_DIR / "queries.txt"
SESSIONS_DIR = BASE_DIR / "sessions"
DATA_DIR = BASE_DIR / "data"


# ==============================================================
# DEFAULT CONFIG
# ==============================================================

DEFAULT_CONFIG = {
    "telegram": {
        "api_id": 224069,
        "api_hash": "f2ddfd53867f28a3b6b98e80fa010e9d"
    },

    "bot": {
        "username": "ATF_AIRDROP_bot",
        "base_url": "https://atfminers.asloni.online",
        "webapp_url": "https://atfminers.asloni.online/miner/index.html"
    },

    "cycle": {
        "interval_seconds": 3600,
        "task_verify_wait": 35,
        "boost_target_hours": 24,
        "max_boosts": 36,
        "boost_delay": 10,
        "task_wait_threshold_minutes": 12,
        "request_timeout": 30,
        "retry_count": 3
    },

    "tasks": {
        "repeatable": [
            "website_visit",
            "youtube_like_comment",
            "twitter_retweet",
            "telegram_react_latest"
        ],

        "one_time": [
            "youtube_subscribe",
            "twitter_follow",
            "telegram_join",
            "telegram_join_fa"
        ],

        "telegram_channels": {
            "telegram_join": "AI_TRADING_FOREX",
            "telegram_join_fa": "ATFFARSI"
        }
    }
}


# ==============================================================
# CONFIG
# ==============================================================

def load_config() -> dict:

    if not CONFIG_PATH.exists():

        CONFIG_PATH.write_text(
            json.dumps(
                DEFAULT_CONFIG,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        print("=" * 80)
        print("config.json belum ditemukan.")
        print("config.json lengkap telah dibuat otomatis.")
        print()
        print(f"Lokasi : {CONFIG_PATH}")
        print()
        print("Isi API ID dan API HASH Telegram terlebih dahulu.")
        print("=" * 80)

        sys.exit(0)

    try:

        cfg = json.loads(
            CONFIG_PATH.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as e:

        print(
            f"config.json tidak valid: {e}"
        )

        sys.exit(1)

    def merge_defaults(
        target,
        defaults
    ):

        for key, value in defaults.items():

            if key not in target:

                target[key] = value

            elif isinstance(
                value,
                dict
            ) and isinstance(
                target[key],
                dict
            ):

                merge_defaults(
                    target[key],
                    value
                )

    merge_defaults(
        cfg,
        DEFAULT_CONFIG
    )

    CONFIG_PATH.write_text(
        json.dumps(
            cfg,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return cfg


CFG = load_config()


# ==============================================================
# CONFIG VARIABLES
# ==============================================================

API_ID = int(
    CFG["telegram"]["api_id"]
)

API_HASH = str(
    CFG["telegram"]["api_hash"]
)

BOT_USERNAME = str(
    CFG["bot"]["username"]
).lstrip("@")

BASE_URL = str(
    CFG["bot"]["base_url"]
).rstrip("/")

WEBAPP_URL = str(
    CFG["bot"].get(
        "webapp_url",
        f"{BASE_URL}/miner/index.html"
    )
)

REPEATABLE_TASKS = list(
    CFG["tasks"].get(
        "repeatable",
        []
    )
)

ONE_TIME_TASKS = list(
    CFG["tasks"].get(
        "one_time",
        []
    )
)

TELEGRAM_CHANNELS = dict(
    CFG["tasks"].get(
        "telegram_channels",
        {}
    )
)

TASK_VERIFY_WAIT = int(
    CFG["cycle"].get(
        "task_verify_wait",
        35
    )
)

REQUEST_TIMEOUT = int(
    CFG["cycle"].get(
        "request_timeout",
        30
    )
)

RETRY_COUNT = int(
    CFG["cycle"].get(
        "retry_count",
        3
    )
)

BOOST_DELAY = int(
    CFG["cycle"].get(
        "boost_delay",
        10
    )
)


# ==============================================================
# DIRECTORY
# ==============================================================

SESSIONS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

if not QUERY_PATH.exists():

    QUERY_PATH.write_text(
        "",
        encoding="utf-8"
    )


# ==============================================================
# DEVICE
# ==============================================================

DEVICES = [
    (
        "Samsung Galaxy S22",
        "SM-S908B",
        "Android 13",
        "Chrome/120.0.0.0"
    ),

    (
        "Samsung Galaxy S23",
        "SM-S916B",
        "Android 14",
        "Chrome/121.0.0.0"
    ),

    (
        "Google Pixel 7",
        "Pixel 7",
        "Android 14",
        "Chrome/119.0.0.0"
    ),

    (
        "OnePlus 11",
        "CPH2451",
        "Android 13",
        "Chrome/120.0.0.0"
    ),

    (
        "Xiaomi 13",
        "2211133G",
        "Android 14",
        "Chrome/121.0.0.0"
    ),

    (
        "Samsung Galaxy A54",
        "SM-A546B",
        "Android 13",
        "Chrome/118.0.0.0"
    )
]


def get_device(
    account_id: str
):

    try:

        num = int(
            account_id.split("_")[-1]
        )

    except Exception:

        num = 0

    return DEVICES[
        num % len(DEVICES)
    ]


def get_user_agent(
    account_id: str
):

    model, code, android, chrome = get_device(
        account_id
    )

    return (
        f"Mozilla/5.0 "
        f"(Linux; {android}; {code}) "
        f"AppleWebKit/537.36 "
        f"(KHTML, like Gecko) "
        f"{chrome} Mobile Safari/537.36"
    )


# ==============================================================
# TIME FORMAT
# ==============================================================

def format_duration(seconds):
    try:
        seconds = max(0, int(seconds))
    except Exception:
        seconds = 0

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ==============================================================
# DASHBOARD (4-SLOT TABLE + LIVE BOOST MONITOR)
# ==============================================================

class Dashboard:

    def __init__(self):

        self.rows = {}
        self.accounts = []
        self.lock = asyncio.Lock()
        self._console = Console()
        self._live = None
        self._started = False

    def register(self, account_id):
        if account_id not in self.rows:
            self.rows[account_id] = {
                "account": {
                    "activity": "ACCOUNT",
                    "status": "WAIT",
                    "detail": "Menunggu inisialisasi...",
                    "order": 1
                },
                "activity": {
                    "activity": "MINING",
                    "status": "WAIT",
                    "detail": "Belum ada aktivitas",
                    "order": 2
                },
                "boost_live": {
                    "activity": "BOOST LIVE",
                    "status": "WAIT",
                    "detail": "Menunggu boost...",
                    "order": 3
                },
                "next_cycle": {
                    "activity": "NEXT CYCLE",
                    "status": "WAIT",
                    "detail": "Menunggu cycle...",
                    "order": 3
                }
            }

    def start(self):
        if self._started:
            return

        self._live = Live(
            self.build_table(),
            console=self._console,
            refresh_per_second=4,
            screen=True,
            transient=False,
        )
        self._live.start(refresh=True)
        self._started = True

    def stop(self):
        if self._live is not None:
            try:
                self._live.stop()
            finally:
                self._live = None
                self._started = False

    async def update(
        self,
        account_id,
        activity,
        status,
        detail,
        row_key=None
    ):
        async with self.lock:
            self.register(account_id)

            activity_upper = str(activity).upper()

            if row_key is None:
                if activity_upper == "ACCOUNT":
                    target_key = "account"
                elif activity_upper == "NEXT CYCLE":
                    target_key = "next_cycle"
                else:
                    target_key = "activity"
            else:
                target_key = row_key

            order = (
                1 if target_key == "account"
                else 4 if target_key == "next_cycle"
                else 3 if target_key == "boost_live"
                else 2
            )

            self.rows[account_id][target_key] = {
                "activity": activity,
                "status": status,
                "detail": detail,
                "order": order
            }

            self.render()

    def build_table(self):
        table = Table(
            title="📊 ATF MINING BOT DASHBOARD",
            box=box.ROUNDED,
            border_style="bright_blue",
            header_style="bold white on blue",
            expand=True,
            show_lines=True,
        )

        table.add_column("ACCOUNT", style="bold cyan", min_width=11, no_wrap=True)
        table.add_column("ACTIVITY", style="bold white", min_width=18, no_wrap=True)
        table.add_column("STATUS", min_width=12, no_wrap=True)
        table.add_column("DETAIL", ratio=1, no_wrap=True)

        status_styles = {
            "SUCCESS": "bold green",
            "SUCCESSFUL": "bold green",
            "READY": "bold green",
            "OK": "bold green",
            "JOINED": "bold green",
            "DONE": "bold green",
            "START": "bold yellow",
            "RUNNING": "bold yellow",
            "REQUEST": "yellow",
            "RESPONSE": "green",
            "WAIT": "bold yellow",
            "SKIP": "dim yellow",
            "CACHE": "cyan",
            "FETCH": "cyan",
            "SAVED": "cyan",
            "MISS": "yellow",
            "RETRY": "bold magenta",
            "BUSY": "bold magenta",
            "INPUT": "bold yellow",
            "CLAIM": "bold yellow",
            "REFRESH": "cyan",
            "FAILED": "bold red",
            "ERROR": "bold red",
            "INVALID": "bold red",
        }

        for account in self.accounts:
            account_rows = self.rows.get(account, {})

            slots = [
                account_rows.get("account", {"activity": "ACCOUNT", "status": "WAIT", "detail": "-"}),
                account_rows.get("activity", {"activity": "MINING", "status": "WAIT", "detail": "-"}),
                account_rows.get("boost_live", {"activity": "BOOST LIVE", "status": "WAIT", "detail": "-"}),
                account_rows.get("next_cycle", {"activity": "NEXT CYCLE", "status": "WAIT", "detail": "-"})
            ]

            for slot_idx, row in enumerate(slots):
                status = str(row.get("status", "-")).upper()
                status_style = status_styles.get(status, "white")
                
                detail = str(row.get("detail", "-")).replace("\n", " ").replace("\r", " ").strip()
                if len(detail) > 75:
                    detail = detail[:72] + "..."

                acc_display = str(account) if slot_idx == 0 else ""

                table.add_row(
                    acc_display,
                    str(row.get("activity", "-")),
                    f"[{status_style}]{status}[/{status_style}]",
                    detail,
                )

        return table

    def render(self):
        if not self._started or self._live is None:
            return

        self._live.update(
            self.build_table(),
            refresh=True
        )


DASHBOARD = Dashboard()


async def activity(
    account_id,
    activity_name,
    status,
    detail,
    row_key=None
):

    await DASHBOARD.update(
        account_id,
        activity_name,
        status,
        detail,
        row_key=row_key
    )


# ==============================================================
# QUERY CACHE
# ==============================================================

def load_queries():

    result = {}

    if not QUERY_PATH.exists():

        return result

    try:

        lines = QUERY_PATH.read_text(
            encoding="utf-8"
        ).splitlines()

    except Exception:

        return result

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if "|" not in line:
            continue

        account_id, query = line.split(
            "|",
            1
        )

        account_id = account_id.strip()

        query = query.strip()

        if account_id and query:

            result[
                account_id
            ] = query

    return result


def save_query(
    account_id,
    query
):

    queries = load_queries()

    queries[
        account_id
    ] = query

    lines = []

    for account in sorted(
        queries
    ):

        lines.append(
            f"{account}|{queries[account]}"
        )

    temp = QUERY_PATH.with_suffix(
        ".tmp"
    )

    temp.write_text(
        "\n".join(lines)
        + (
            "\n"
            if lines
            else ""
        ),
        encoding="utf-8"
    )

    temp.replace(
        QUERY_PATH
    )


def remove_query(
    account_id
):

    queries = load_queries()

    if account_id not in queries:

        return

    del queries[
        account_id
    ]

    lines = [

        f"{account}|{queries[account]}"

        for account in sorted(
            queries
        )
    ]

    QUERY_PATH.write_text(
        "\n".join(lines)
        + (
            "\n"
            if lines
            else ""
        ),
        encoding="utf-8"
    )


# ==============================================================
# QUERY VALIDATION / TRANSPORT SAFETY
# ==============================================================

def is_query_transport_unsafe(query):

    if not isinstance(query, str):
        return True

    query = query.strip()

    if not query:
        return True

    if any(ord(char) > 127 for char in query):
        return True

    lowered = query.lower()
    if "user={" in lowered:
        return True

    if "user=" not in lowered:
        return True

    return False


# ==============================================================
# STATE
# ==============================================================

@dataclass
class AccountState:

    account_id: str

    last_mining_claim_ts: int = 0

    last_balance: float = 0.0

    last_level: int = 0

    one_time_done: list = field(
        default_factory=list
    )

    task_last_claim: dict = field(
        default_factory=dict
    )

    cycles_run: int = 0

    last_run_ts: int = 0


class StateManager:

    def __init__(
        self,
        base_dir
    ):

        self.base_dir = base_dir

        self.base_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def load(
        self,
        account_id
    ):

        path = (
            self.base_dir
            / f"{account_id}.json"
        )

        if path.exists():

            try:

                data = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

                return AccountState(
                    **data
                )

            except Exception:

                pass

        return AccountState(
            account_id=account_id
        )

    def save(
        self,
        state
    ):

        path = (
            self.base_dir
            / f"{state.account_id}.json"
        )

        temp = path.with_suffix(
            ".tmp"
        )

        temp.write_text(
            json.dumps(
                asdict(state),
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        temp.replace(
            path
        )


# ==============================================================
# ATF CLIENT
# ==============================================================

class ATFClient:

    def __init__(
        self,
        account_id
    ):

        self.account_id = account_id

        self.tg = None

        self.http = None

        self.init_data_raw = None

        self.user_obj = None

        self.tg_id = None

        self.tma_token = None

        self._referer = WEBAPP_URL

        self.device_id = str(
            uuid.uuid4()
        )

    # ==========================================================
    # TELEGRAM CONNECT
    # ==========================================================

    async def connect(
        self,
        require_login=True
    ):

        model, code, android, chrome = get_device(
            self.account_id
        )

        self.tg = TelegramClient(

            str(
                SESSIONS_DIR
                / self.account_id
            ),

            API_ID,

            API_HASH,

            device_model=model,

            system_version=android,

            app_version="10.5.2",

            lang_code="en",

            system_lang_code="en-US"
        )

        last_error = None

        for attempt in range(
            RETRY_COUNT
        ):

            try:

                await self.tg.connect()

                last_error = None

                break

            except Exception as e:

                last_error = e

                await asyncio.sleep(
                    2 + attempt * 2
                )

        if last_error:

            raise RuntimeError(
                f"Telegram connect failed: {last_error}"
            )

        authorized = (
            await self.tg.is_user_authorized()
        )

        if not authorized:

            if not require_login:

                return False

            await activity(
                self.account_id,
                "TELEGRAM LOGIN",
                "INPUT",
                "Session belum ada — login Telegram diperlukan",
                row_key="activity"
            )

            await self.tg.disconnect()

            await self.login_new_telegram()

            return True

        me = await self.tg.get_me()

        await activity(
            self.account_id,
            "TELEGRAM SESSION",
            "OK",
            f"Session aktif | "
            f"@{me.username or '-'} | "
            f"ID={me.id}",
            row_key="activity"
        )

        return True

    # ==========================================================
    # NEW TELEGRAM LOGIN
    # ==========================================================

    async def login_new_telegram(self):

        model, code, android, chrome = get_device(
            self.account_id
        )

        self.tg = TelegramClient(

            str(
                SESSIONS_DIR
                / self.account_id
            ),

            API_ID,

            API_HASH,

            device_model=model,

            system_version=android,

            app_version="10.5.2",

            lang_code="en",

            system_lang_code="en-US"
        )

        await self.tg.connect()

        phone = input(
            f"\nNomor Telegram untuk "
            f"{self.account_id}: "
        ).strip()

        if not phone:

            raise RuntimeError(
                "Nomor Telegram kosong"
            )

        await self.tg.send_code_request(
            phone
        )

        code_input = input(
            "Kode OTP Telegram: "
        ).strip()

        try:

            await self.tg.sign_in(
                phone=phone,
                code=code_input
            )

        except SessionPasswordNeededError:

            password = input(
                "Password 2FA Telegram: "
            )

            await self.tg.sign_in(
                password=password
            )

        me = await self.tg.get_me()

        await activity(
            self.account_id,
            "TELEGRAM LOGIN",
            "SUCCESS",
            f"@{me.username or '-'} | ID={me.id}",
            row_key="activity"
        )

    # ==========================================================
    # CLOSE
    # ==========================================================

    async def close(self):

        if self.http:

            try:
                await self.http.aclose()
            except Exception:
                pass

            self.http = None

        if self.tg:

            try:
                await self.tg.disconnect()
            except Exception:
                pass

            self.tg = None

    # ==========================================================
    # FETCH WEBAPP QUERY
    # ==========================================================

    async def fetch_webapp_query(self):

        if not self.tg:
            raise RuntimeError("Telegram client belum connect")

        bot = await self.tg.get_entity(BOT_USERNAME)

        def find_webview(messages):
            for msg in messages:
                if not msg.reply_markup:
                    continue
                for row in msg.reply_markup.rows:
                    for button in row.buttons:
                        if isinstance(button, KeyboardButtonWebView):
                            return button
            return None

        messages = await self.tg.get_messages(bot, limit=20)
        button = find_webview(messages)

        if button is None:
            await self.tg.send_message(bot, "/start")
            await asyncio.sleep(2)
            messages = await self.tg.get_messages(bot, limit=20)
            button = find_webview(messages)

        if button is None:
            raise RuntimeError("Tombol WebView tidak ditemukan")

        result = await self.tg(
            RequestWebViewRequest(
                peer=bot,
                bot=bot,
                platform="android",
                from_bot_menu=False,
                url=button.url
            )
        )

        url = result.url
        self._referer = url[:500]

        if "#" not in url:
            raise RuntimeError("WebView URL tidak memiliki fragment")

        fragment = url.split("#", 1)[1]
        params = parse_qs(fragment)

        if "tgWebAppData" not in params:
            raise RuntimeError("tgWebAppData tidak ditemukan")

        raw = params["tgWebAppData"][0]
        qs = parse_qs(raw)

        if "user" not in qs:
            raise RuntimeError("Data user Telegram tidak ditemukan")

        try:
            user_obj = json.loads(qs["user"][0])
        except Exception as e:
            raise RuntimeError(f"JSON user Telegram tidak valid: {e}")

        if not isinstance(user_obj, dict) or not user_obj.get("id"):
            raise RuntimeError("Data user Telegram tidak valid")

        if is_query_transport_unsafe(raw):
            raise RuntimeError("Query WebView berada dalam format decoded/non-ASCII")

        self.init_data_raw = raw
        self.user_obj = user_obj
        self.tg_id = int(self.user_obj["id"])

        return raw

    # ==========================================================
    # HTTP HEADERS
    # ==========================================================

    def make_headers(self):

        return {

            "Content-Type":
                "application/json",

            "Accept":
                "application/json, text/plain, */*",

            "X-Requested-With":
                "XMLHttpRequest",

            "X-Telegram-Init-Data":
                self.init_data_raw or "",

            "User-Agent":
                get_user_agent(
                    self.account_id
                ),

            "Origin":
                BASE_URL,

            "Referer":
                self._referer,

            "Accept-Language":
                "en-US,en;q=0.9"
        }

    # ==========================================================
    # HTTP BODY
    # ==========================================================

    def make_body(
        self,
        extra=None
    ):

        body = {

            "initData":
                self.init_data_raw,

            "request_id":
                str(uuid.uuid4()),

            "device_id":
                self.device_id
        }

        if extra:

            body.update(
                extra
            )

        return body

    # ==========================================================
    # POST
    # ==========================================================

    async def post(
        self,
        action,
        payload=None,
        show_activity=False
    ):

        if self.http is None:

            self.http = httpx.AsyncClient(

                http2=True,

                timeout=httpx.Timeout(
                    REQUEST_TIMEOUT,
                    connect=15
                )
            )

        url = (
            f"{BASE_URL}/index.php"
            f"?action={action}"
            f"&t={int(time.time() * 1000)}"
        )

        if show_activity:

            await activity(
                self.account_id,
                f"API {action.upper()}",
                "REQUEST",
                "Mengirim request...",
                row_key="activity"
            )

        last_error = None

        for attempt in range(
            RETRY_COUNT
        ):

            try:

                response = await self.http.post(

                    url,

                    json=self.make_body(
                        payload
                    ),

                    headers=self.make_headers()
                )

                try:

                    data = response.json()

                except Exception:

                    data = {

                        "status":
                            "error",

                        "message":
                            response.text[:500]
                    }

                data[
                    "_http_status"
                ] = response.status_code

                if show_activity:

                    await activity(
                        self.account_id,
                        f"API {action.upper()}",
                        "RESPONSE",
                        f"HTTP {response.status_code}",
                        row_key="activity"
                    )

                return data

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.RemoteProtocolError
            ) as e:

                last_error = e

                if show_activity:

                    await activity(
                        self.account_id,
                        f"API {action.upper()}",
                        "RETRY",
                        f"Attempt {attempt + 1}/"
                        f"{RETRY_COUNT}",
                        row_key="activity"
                    )

                if attempt < RETRY_COUNT - 1:

                    await asyncio.sleep(
                        3 * (
                            attempt + 1
                        )
                    )

            except Exception as e:

                last_error = e

                break

        return {

            "status":
                "error",

            "message":
                str(last_error),

            "_is_conn_err":
                True
        }

    # ==========================================================
    # AUTH INVALID
    # ==========================================================

    def is_auth_invalid(
        self,
        data
    ):

        if not isinstance(
            data,
            dict
        ):

            return False

        status = str(
            data.get(
                "status",
                ""
            )
        ).lower()

        message = str(
            data.get(
                "message",
                ""
            )
        ).lower()

        combined = (
            status
            + " "
            + message
        )

        keywords = [

            "invalid init",

            "invalid telegram",

            "invalid tg",

            "invalid token",

            "expired",

            "unauthorized",

            "not authenticated",

            "authentication failed",

            "auth failed",

            "signature",

            "tgwebapp",

            "initdata",

            "ascii",

            "codec",

            "encode",

            "unicode",

            "init data"
        ]

        return any(
            keyword in combined
            for keyword in keywords
        )

    # ==========================================================
    # LOGIN WITH QUERY
    # ==========================================================

    async def login_with_query(
        self,
        query
    ):

        self.init_data_raw = query

        try:
            qs = parse_qs(query)
            if "user" in qs:
                self.user_obj = json.loads(qs["user"][0])
                self.tg_id = int(self.user_obj["id"])
        except Exception as e:
            return {
                "status": "error",
                "message": f"Query Telegram tidak bisa dibaca: {e}"
            }

        if not self.tg_id:
            return {
                "status": "error",
                "message": "Telegram user tidak bisa dibaca"
            }

        if is_query_transport_unsafe(query):
            return {
                "status": "error",
                "message": "Cached WebApp query memiliki format tidak aman"
            }

        return await self.post(
            "login",
            {
                "tg_id": self.tg_id,
                "username": self.user_obj.get("username", "")
            }
        )

    # ==========================================================
    # LOGIN
    # ==========================================================

    async def login(self):

        queries = load_queries()
        cached_query = queries.get(self.account_id)

        # ======================================================
        # CACHE HIT
        # ======================================================

        if cached_query:
            await activity(
                self.account_id,
                "WEBAPP QUERY",
                "CACHE",
                "Menggunakan query tersimpan",
                row_key="activity"
            )

            if is_query_transport_unsafe(cached_query):
                await activity(
                    self.account_id,
                    "WEBAPP QUERY",
                    "INVALID",
                    "Format query cache lama - refresh diperlukan",
                    row_key="activity"
                )
                remove_query(self.account_id)
                cached_query = None
            else:
                try:
                    data = await self.login_with_query(cached_query)
                except Exception as e:
                    data = {"status": "error", "message": str(e)}

                if data.get("status") == "success":
                    if data.get("tma_session_token"):
                        self.tma_token = data["tma_session_token"]

                    user = data.get("user") or {}
                    balance = float(user.get("mined_balance", 0) or 0)

                    await activity(
                        self.account_id,
                        "LOGIN",
                        "SUCCESS",
                        f"Query valid | Balance={balance:.4f} ATF",
                        row_key="activity"
                    )
                    return data

                message = str(data.get("message", "unknown"))
                await activity(
                    self.account_id,
                    "WEBAPP QUERY",
                    "INVALID",
                    f"Query cache gagal: {message[:50]}",
                    row_key="activity"
                )
                remove_query(self.account_id)

        else:
            await activity(
                self.account_id,
                "WEBAPP QUERY",
                "MISS",
                "Mengambil WebView baru...",
                row_key="activity"
            )

        # ======================================================
        # FETCH NEW QUERY + LOGIN
        # ======================================================

        max_refresh_attempts = 2
        last_data = None
        last_error = None

        for refresh_index in range(max_refresh_attempts):

            if refresh_index == 0:
                status = "FETCH"
                detail = "Mengambil WebView Telegram..."
            else:
                status = "RETRY"
                detail = f"Mengambil WebView ulang ({refresh_index + 1}/{max_refresh_attempts})"

            await activity(
                self.account_id,
                "WEBAPP QUERY",
                status,
                detail,
                row_key="activity"
            )

            try:
                query = await self.fetch_webapp_query()

                if not query:
                    raise RuntimeError("Query WebView kosong")

                if is_query_transport_unsafe(query):
                    raise RuntimeError(
                        "Query WebView tidak aman"
                    )

                save_query(self.account_id, query)

                await activity(
                    self.account_id,
                    "WEBAPP QUERY",
                    "SAVED",
                    "Query baru disimpan",
                    row_key="activity"
                )

                try:
                    data = await self.login_with_query(query)
                except Exception as e:
                    data = {"status": "error", "message": str(e)}

                last_data = data

                if data.get("status") == "success":
                    if data.get("tma_session_token"):
                        self.tma_token = data["tma_session_token"]

                    user = data.get("user") or {}
                    balance = float(user.get("mined_balance", 0) or 0)

                    await activity(
                        self.account_id,
                        "LOGIN",
                        "SUCCESS",
                        f"Query baru valid | Balance={balance:.4f} ATF",
                        row_key="activity"
                    )
                    return data

                message = str(data.get("message", "unknown"))
                last_error = message
                remove_query(self.account_id)

                if refresh_index < max_refresh_attempts - 1:
                    await activity(
                        self.account_id,
                        "WEBAPP QUERY",
                        "RETRY",
                        f"Login gagal: {message[:50]}",
                        row_key="activity"
                    )
                    await asyncio.sleep(2)

            except Exception as e:
                last_error = str(e)
                remove_query(self.account_id)

                if refresh_index < max_refresh_attempts - 1:
                    await activity(
                        self.account_id,
                        "WEBAPP QUERY",
                        "RETRY",
                        f"Fetch gagal: {last_error[:50]}",
                        row_key="activity"
                    )
                    await asyncio.sleep(2)

        if last_data and last_data.get("status") != "success":
            message = str(last_data.get("message", last_error or "unknown"))
        else:
            message = last_error or "unknown"

        raise RuntimeError(
            f"Login API gagal: {message}"
        )

    # ==========================================================
    # MINING
    # ==========================================================

    async def claim_mining(
        self,
        preview
    ):

        return await self.post(
            "claim",
            {
                "tg_id":
                    self.tg_id,

                "claim_preview":
                    round(
                        preview,
                        4
                    )
            }
        )

    async def get_math_challenge(
        self,
        scope="start_mine"
    ):

        return await self.post(
            "get_math_challenge",
            {
                "tg_id":
                    self.tg_id,

                "scope":
                    scope
            }
        )

    async def start_mine(
        self,
        challenge_id,
        answer
    ):

        return await self.post(
            "start_mine",
            {
                "tg_id":
                    self.tg_id,

                "math_challenge_id":
                    challenge_id,

                "math_answer":
                    answer
            }
        )

    async def activate_boost(
        self,
        display_preview=0
    ):

        return await self.post(
            "activate_boost",
            {
                "tg_id":
                    self.tg_id,

                "display_preview":
                    round(
                        display_preview,
                        4
                    )
            }
        )

    def solve_math(
        self,
        question
    ):

        match = re.match(
            r"\s*(-?\d+)\s*([+\-*x×])\s*(-?\d+)",
            str(question)
        )

        if not match:

            return None

        a = int(
            match.group(1)
        )

        op = match.group(2)

        b = int(
            match.group(3)
        )

        if op == "+":

            return a + b

        if op == "-":

            return a - b

        return a * b

    async def start_mining_only(
        self
    ):

        challenge = await self.get_math_challenge(
            "start_mine"
        )

        if challenge.get(
            "status"
        ) != "success":

            return {
                "status":
                    "error",

                "step":
                    "get_math",

                "data":
                    challenge
            }

        answer = self.solve_math(
            challenge.get(
                "question",
                ""
            )
        )

        if answer is None:

            return {
                "status":
                    "error",

                "step":
                    "parse_math",

                "question":
                    challenge.get(
                        "question",
                        ""
                    )
            }

        result = await self.start_mine(
            challenge[
                "challenge_id"
            ],
            str(answer)
        )

        if result.get(
            "status"
        ) != "success":

            return {
                "status":
                    "error",

                "step":
                    "start_mine",

                "data":
                    result
            }

        return {
            "status":
                "success",

            "start_mine":
                result
        }

    async def claim_mining_with_restart(
        self,
        preview
    ):

        claim = await self.claim_mining(
            preview
        )

        if claim.get(
            "status"
        ) != "success":

            return {
                "status":
                    "error",

                "step":
                    "claim",

                "data":
                    claim
            }

        challenge = await self.get_math_challenge(
            "start_mine"
        )

        if challenge.get(
            "status"
        ) != "success":

            return {
                "status":
                    "error",

                "step":
                    "get_math",

                "data":
                    challenge,

                "claim":
                    claim
            }

        answer = self.solve_math(
            challenge.get(
                "question",
                ""
            )
        )

        if answer is None:

            return {
                "status":
                    "error",

                "step":
                    "parse_math",

                "question":
                    challenge.get(
                        "question",
                        ""
                    ),

                "claim":
                    claim
            }

        start = await self.start_mine(
            challenge[
                "challenge_id"
            ],
            str(answer)
        )

        if start.get(
            "status"
        ) != "success":

            return {
                "status":
                    "error",

                "step":
                    "start_mine",

                "data":
                    start,

                "claim":
                    claim
            }

        return {
            "status":
                "success",

            "claim":
                claim,

            "start_mine":
                start
        }

    # ==========================================================
    # BOOST (SERVER-DRIVEN / REALTIME LIVE DISPLAY)
    # ==========================================================

    async def boost_until_target(
        self,
        user,
        target_hours=24,
        max_boosts=846,
        progress_callback=None
    ):
        """
        MAX SPEED / MAX BOOST.

        Tidak memakai target_hours sebagai stop condition.
        Server menentukan kapan activate_boost berhenti.
        progress_callback mengirim status realtime ke dashboard.
        """
        result = {
            "boosts_done": 0,
            "target_reached": False,
            "server_stopped": False,
            "errors": [],
            "last_freeze": 0,
            "last_status": "READY",
            "last_reason": "",
        }

        current_user = dict(user or {})
        max_boosts = max(0, int(max_boosts))

        async def emit(status, **data):
            result["last_status"] = status
            if "reason" in data:
                result["last_reason"] = str(data["reason"])

            payload = {
                "status": status,
                "boosts_done": result["boosts_done"],
                "max_boosts": max_boosts,
                "freeze": result["last_freeze"],
                "reason": result["last_reason"],
                **data,
            }

            if progress_callback:
                try:
                    value = progress_callback(payload)
                    if inspect.isawaitable(value):
                        await value
                except Exception:
                    pass

        if max_boosts <= 0:
            await emit("DONE", reason="max_boosts=0")
            return result

        await emit(
            "RUNNING",
            boost_no=1,
            next_boost=0,
            reason=f"Memulai Max Speed | limit={max_boosts}"
        )

        for index in range(max_boosts):
            boost_no = index + 1

            preview = float(
                current_user.get("pending_reward")
                or current_user.get("unclaimed_reward")
                or current_user.get("mined_unclaimed")
                or current_user.get("unclaimed")
                or current_user.get("pending_balance")
                or 0
            )

            await emit(
                "RUNNING",
                boost_no=boost_no,
                next_boost=0,
                reason=f"Mengirim activate_boost #{boost_no}/{max_boosts}"
            )

            try:
                response = await self.activate_boost(preview)
            except Exception as exc:
                reason = str(exc)
                result["last_status"] = "ERROR"
                result["last_reason"] = reason
                result["errors"].append(reason)
                await emit(
                    "ERROR",
                    boost_no=boost_no,
                    next_boost=0,
                    reason=reason
                )
                break

            if not isinstance(response, dict):
                reason = "Response server bukan JSON object"
                result["server_stopped"] = True
                result["last_status"] = "STOP"
                result["last_reason"] = reason
                result["errors"].append(reason)
                await emit(
                    "STOP",
                    boost_no=boost_no,
                    next_boost=0,
                    reason=reason
                )
                break

            status = str(response.get("status", "")).lower()

            new_freeze = int(
                response.get("mining_freezes_at")
                or current_user.get("mining_freezes_at")
                or 0
            )
            result["last_freeze"] = new_freeze

            if status != "success":
                reason = (
                    response.get("message")
                    or response.get("error")
                    or response.get("detail")
                    or response.get("reason")
                    or f"Server status={status or 'unknown'}"
                )
                result["server_stopped"] = True
                result["last_status"] = "STOP"
                result["last_reason"] = str(reason)
                await emit(
                    "STOP",
                    boost_no=boost_no,
                    next_boost=0,
                    reason=str(reason)
                )
                break

            result["boosts_done"] += 1
            current_user["mining_freezes_at"] = new_freeze
            current_user["pending_reward"] = response.get(
                "pending_reward",
                preview
            )

            await emit(
                "SUCCESS",
                boost_no=boost_no,
                next_boost=BOOST_DELAY,
                reason=f"Boost #{boost_no}/{max_boosts} berhasil"
            )

            abuse_watch = response.get("abuse_watch") or {}
            ban_until = int(
                abuse_watch.get("temporary_ban_until") or 0
            )

            if ban_until > 0:
                reason = f"Temporary ban sampai {ban_until}"
                result["server_stopped"] = True
                result["last_status"] = "STOP"
                result["last_reason"] = reason
                await emit(
                    "STOP",
                    boost_no=boost_no,
                    next_boost=0,
                    reason=reason
                )
                break

            if boost_no >= max_boosts:
                reason = f"Max boost {max_boosts} tercapai"
                result["last_status"] = "DONE"
                result["last_reason"] = reason
                await emit(
                    "DONE",
                    boost_no=boost_no,
                    next_boost=0,
                    reason=reason
                )
                break

            for remaining in range(int(BOOST_DELAY), 0, -1):
                await emit(
                    "WAIT",
                    boost_no=boost_no,
                    next_boost=remaining,
                    reason=(
                        f"Boost #{boost_no} sukses | "
                        f"boost berikutnya dalam {remaining:02d}s"
                    )
                )
                await asyncio.sleep(1)

        return result

    async def start_task(
        self,
        task_id
    ):

        return await self.post(
            "start_task",
            {
                "tg_id":
                    self.tg_id,

                "task_id":
                    task_id,

                "client_started_at":
                    int(time.time())
            }
        )

    async def claim_task(
        self,
        task_id
    ):

        return await self.post(
            "claim_task",
            {
                "tg_id":
                    self.tg_id,

                "task_id":
                    task_id
            }
        )

    # ==========================================================
    # TELEGRAM CHANNEL
    # ==========================================================

    async def join_channel(
        self,
        channel
    ):

        try:

            entity = await self.tg.get_entity(
                channel
            )

            await self.tg(
                JoinChannelRequest(
                    entity
                )
            )

            return True

        except Exception as e:

            if "already" in str(
                e
            ).lower():

                return True

            return False


# ==============================================================
# ACCOUNT CYCLE
# ==============================================================

async def run_account_cycle(
    account_id,
    state_mgr
):

    state = state_mgr.load(
        account_id
    )

    client = ATFClient(
        account_id
    )

    try:

        # ======================================================
        # TELEGRAM
        # ======================================================

        await client.connect(
            require_login=True
        )

        # ======================================================
        # API LOGIN
        # ======================================================

        login = await client.login()

        if login.get(
            "status"
        ) != "success":

            raise RuntimeError(
                login.get(
                    "message",
                    "Login API gagal"
                )
            )

        user = login.get(
            "user"
        )

        if not user:

            raise RuntimeError(
                "Response login tidak memiliki user"
            )

        cooldowns = login.get(
            "task_cooldowns",
            {}
        ) or {}

        balance_before = float(
            user.get(
                "mined_balance",
                0
            )
            or 0
        )

        pending = float(
            user.get("pending_reward") 
            or user.get("unclaimed_reward") 
            or user.get("mined_unclaimed") 
            or user.get("unclaimed") 
            or user.get("pending_balance") 
            or 0
        )

        level = int(
            user.get(
                "miner_level",
                0
            )
            or 0
        )

        # ======================================================
        # ACCOUNT READY (BARIS PERTAMA)
        # ======================================================

        await activity(
            account_id,
            "ACCOUNT",
            "READY",
            f"Bal={balance_before:.4f} ATF | Lvl={level}",
            row_key="account"
        )

        # ======================================================
        # MINING (SLOT AKTIVITAS)
        # ======================================================

        now = int(
            time.time()
        )

        mining_freezes_at = int(
            user.get(
                "mining_freezes_at",
                0
            )
            or 0
        )

        cycle_frozen = (
            mining_freezes_at > 0
            and now >= mining_freezes_at
        )

        cycle_near_freeze = (
            mining_freezes_at > 0
            and (
                mining_freezes_at
                - now
            ) <= 1800
        )

        mining_never_started = (
            mining_freezes_at == 0
            and pending == 0
        )

        should_claim = (
            cycle_frozen
            or cycle_near_freeze
            or pending > 5
        )

        if mining_never_started:

            await activity(
                account_id,
                "MINING",
                "START",
                "Mining belum pernah dimulai",
                row_key="activity"
            )

            result = await client.start_mining_only()

            if result.get(
                "status"
            ) == "success":

                await activity(
                    account_id,
                    "MINING",
                    "SUCCESS",
                    "Mining berhasil dimulai",
                    row_key="activity"
                )

            else:

                await activity(
                    account_id,
                    "MINING",
                    "FAILED",
                    f"Start mining gagal: {result.get('step', 'unknown')}",
                    row_key="activity"
                )

        elif should_claim:

            await activity(
                account_id,
                "MINING",
                "CLAIM",
                f"Pending={pending:.4f} ATF",
                row_key="activity"
            )

            result = await client.claim_mining_with_restart(
                pending
            )

            if result.get(
                "status"
            ) == "success":

                amount = float(
                    result[
                        "claim"
                    ].get(
                        "claimed_amount",
                        0
                    )
                    or 0
                )

                state.last_mining_claim_ts = now

                await activity(
                    account_id,
                    "MINING",
                    "SUCCESS",
                    f"+{amount:.4f} ATF",
                    row_key="activity"
                )

                # Refresh user
                login = await client.login()

                if login.get(
                    "status"
                ) == "success":

                    user = login[
                        "user"
                    ]

            else:

                await activity(
                    account_id,
                    "MINING",
                    "FAILED",
                    str(
                        result.get(
                            "step",
                            "unknown"
                        )
                    ),
                    row_key="activity"
                )

        else:

            await activity(
                account_id,
                "MINING",
                "SKIP",
                f"Mining aktif | Pending={pending:.4f} ATF",
                row_key="activity"
            )

        # ======================================================
        # BOOST (SLOT AKTIVITAS & REALTIME PROGRESS CALLBACK)
        # ======================================================

        if user.get(
            "last_mining_start"
        ) and not cycle_frozen:

            await activity(
                account_id,
                "BOOST",
                "RUNNING",
                "Memulai Max Speed server-driven...",
                row_key="activity"
            )

            async def boost_progress(info):
                status = str(info.get("status", "WAIT"))
                boost_no = int(info.get("boost_no", 0) or 0)
                max_b = int(info.get("max_boosts", 0) or 0)
                remaining = int(info.get("next_boost", 0) or 0)
                freeze = int(info.get("freeze", 0) or 0)
                reason = str(info.get("reason", "") or "")

                freeze_str = format_duration(max(0, freeze - int(time.time()))) if freeze > 0 else "-"

                if status == "WAIT":
                    detail = (
                        f"Boost #{boost_no}/{max_b} OK | "
                        f"Next={remaining:02d}s | "
                        f"Freeze={freeze_str}"
                    )
                elif status == "RUNNING":
                    detail = (
                        f"Boost #{boost_no}/{max_b} RUNNING | "
                        f"Freeze={freeze_str} | {reason}"
                    )
                elif status == "SUCCESS":
                    detail = (
                        f"Boost #{boost_no}/{max_b} SUCCESS | "
                        f"Freeze={freeze_str} | "
                        f"Next={remaining:02d}s"
                    )
                elif status == "STOP":
                    detail = (
                        f"STOP | {reason} | "
                        f"Freeze={freeze_str}"
                    )
                elif status == "ERROR":
                    detail = f"ERROR | {reason}"
                elif status == "DONE":
                    detail = (
                        f"DONE | {reason} | "
                        f"Total={info.get('boosts_done', 0)} | "
                        f"Freeze={freeze_str}"
                    )
                else:
                    detail = reason

                await DASHBOARD.update(
                    account_id,
                    "BOOST LIVE",
                    status,
                    detail,
                    row_key="boost_live"
                )

            boost = await client.boost_until_target(
                user,
                target_hours=float(
                    CFG["cycle"].get(
                        "boost_target_hours",
                        24
                    )
                ),
                max_boosts=int(
                    CFG["cycle"].get(
                        "max_boosts",
                        846
                    )
                ),
                progress_callback=boost_progress
            )

            if boost["boosts_done"] > 0:
                await activity(
                    account_id,
                    "BOOST",
                    "SUCCESS",
                    f"Selesai {boost['boosts_done']}x boost | Reason={boost.get('last_reason', '-')}",
                    row_key="activity"
                )
            else:
                await activity(
                    account_id,
                    "BOOST",
                    "SKIP",
                    f"Boost selesai tanpa aksi | {boost.get('last_reason', '-')}",
                    row_key="activity"
                )

        else:

            await activity(
                account_id,
                "BOOST",
                "SKIP",
                "Mining belum membutuhkan boost",
                row_key="activity"
            )

        # ======================================================
        # ONE-TIME TASK (SLOT AKTIVITAS)
        # ======================================================

        for task_id in ONE_TIME_TASKS:

            if task_id in state.one_time_done:

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "SKIP",
                    f"{task_id} sudah selesai",
                    row_key="activity"
                )

                continue

            if task_id in TELEGRAM_CHANNELS:

                channel = TELEGRAM_CHANNELS[
                    task_id
                ]

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "JOIN",
                    f"{task_id} -> {channel}",
                    row_key="activity"
                )

                joined = await client.join_channel(
                    channel
                )

                if not joined:

                    await activity(
                        account_id,
                        "ONE-TIME TASK",
                        "FAILED",
                        f"{task_id} | gagal join {channel}",
                        row_key="activity"
                    )

                    continue

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "JOINED",
                    f"{task_id} -> {channel}",
                    row_key="activity"
                )

                await asyncio.sleep(
                    2
                )

            await activity(
                account_id,
                "ONE-TIME TASK",
                "START",
                task_id,
                row_key="activity"
            )

            start = await client.start_task(
                task_id
            )

            if start.get(
                "status"
            ) == "busy":

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "BUSY",
                    task_id,
                    row_key="activity"
                )

                continue

            await asyncio.sleep(
                TASK_VERIFY_WAIT
            )

            claim = await client.claim_task(
                task_id
            )

            message = str(
                claim.get(
                    "message",
                    ""
                )
            ).lower()

            if claim.get(
                "status"
            ) == "success":

                if task_id not in state.one_time_done:

                    state.one_time_done.append(
                        task_id
                    )

                state.task_last_claim[
                    task_id
                ] = int(
                    time.time()
                )

                reward = claim.get(
                    "reward",
                    0
                )

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "SUCCESS",
                    f"{task_id} | +{reward} ATF",
                    row_key="activity"
                )

            elif (
                "already" in message
                or "invalid" in message
            ):

                if task_id not in state.one_time_done:

                    state.one_time_done.append(
                        task_id
                    )

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "DONE",
                    f"{task_id} | {message[:45]}",
                    row_key="activity"
                )

            else:

                await activity(
                    account_id,
                    "ONE-TIME TASK",
                    "FAILED",
                    f"{task_id} | {message[:45]}",
                    row_key="activity"
                )

            state_mgr.save(
                state
            )

            await asyncio.sleep(
                2
            )

        # ======================================================
        # REPEATABLE TASK (SLOT AKTIVITAS)
        # ======================================================

        wait_threshold = int(
            CFG["cycle"].get(
                "task_wait_threshold_minutes",
                12
            )
        )

        for task_id in REPEATABLE_TASKS:

            now = int(
                time.time()
            )

            cooldown = int(
                cooldowns.get(
                    task_id,
                    0
                )
                or 0
            )

            if cooldown > now:

                minutes_left = (
                    cooldown
                    - now
                ) // 60

                if (
                    minutes_left
                    <= wait_threshold
                ):

                    await activity(
                        account_id,
                        "REPEAT TASK",
                        "WAIT",
                        f"{task_id} | {minutes_left}m",
                        row_key="activity"
                    )

                    await asyncio.sleep(
                        max(
                            1,
                            cooldown
                            - now
                            + 2
                        )
                    )

                else:

                    await activity(
                        account_id,
                        "REPEAT TASK",
                        "SKIP",
                        f"{task_id} | CD {minutes_left}m",
                        row_key="activity"
                    )

                    continue

            task_label = {
                "website_visit": "Visit website",
                "youtube_like_comment": "YouTube like/comment",
                "twitter_retweet": "Twitter retweet",
                "telegram_react_latest": "React to latest post",
            }.get(task_id, task_id)

            await activity(
                account_id,
                "REPEAT TASK",
                "START",
                f"{task_label} -> {task_id}",
                row_key="activity"
            )

            start = await client.start_task(
                task_id
            )

            if start.get(
                "status"
            ) == "busy":

                await activity(
                    account_id,
                    "REPEAT TASK",
                    "BUSY",
                    task_id,
                    row_key="activity"
                )

                continue

            await asyncio.sleep(
                TASK_VERIFY_WAIT
            )

            claim = await client.claim_task(
                task_id
            )

            if claim.get(
                "status"
            ) == "success":

                reward = claim.get(
                    "reward",
                    0
                )

                state.task_last_claim[
                    task_id
                ] = int(
                    time.time()
                )

                await activity(
                    account_id,
                    "REPEAT TASK",
                    "SUCCESS",
                    f"{task_id} | +{reward} ATF",
                    row_key="activity"
                )

            else:

                await activity(
                    account_id,
                    "REPEAT TASK",
                    "FAILED",
                    f"{task_label} -> {task_id}",
                    row_key="activity"
                )

            state_mgr.save(
                state
            )

            await asyncio.sleep(
                2
            )

        # ======================================================
        # FINAL BALANCE (BARIS PERTAMA & SLOT AKTIVITAS)
        # ======================================================

        await activity(
            account_id,
            "BALANCE",
            "REFRESH",
            "Mengambil saldo terbaru...",
            row_key="activity"
        )

        final_login = await client.login()

        if final_login.get(
            "status"
        ) != "success":

            raise RuntimeError(
                "Gagal refresh saldo"
            )

        final_user = final_login[
            "user"
        ]

        balance_after = float(
            final_user.get(
                "mined_balance",
                0
            )
            or 0
        )

        level_after = int(
            final_user.get(
                "miner_level",
                0
            )
            or 0
        )

        gain = (
            balance_after
            - balance_before
        )

        state.last_balance = (
            balance_after
        )

        state.last_level = (
            level_after
        )

        state.cycles_run += 1

        state.last_run_ts = int(
            time.time()
        )

        state_mgr.save(
            state
        )

        await activity(
            account_id,
            "ACCOUNT",
            "READY",
            f"Bal={balance_after:.4f} ATF | Lvl={level_after}",
            row_key="account"
        )

        await activity(
            account_id,
            "BALANCE",
            "SUCCESS",
            f"{balance_before:.4f} -> {balance_after:.4f} ATF (+{gain:.4f})",
            row_key="activity"
        )

        return final_user

    except Exception as e:

        message = str(
            e
        ).strip()

        if not message:

            message = type(
                e
            ).__name__

        await activity(
            account_id,
            "ACCOUNT",
            "ERROR",
            message,
            row_key="account"
        )
        return None

    finally:

        state_mgr.save(
            state
        )

        await client.close()


# ==============================================================
# INDIVIDUAL ACCOUNT WORKER
# ==============================================================

async def run_account_worker(account_id, state_mgr):

    interval = int(CFG["cycle"].get("interval_seconds", 3600))

    while True:

        user_data = await run_account_cycle(account_id, state_mgr)

        pending = 0.0
        if user_data:
            pending = float(
                user_data.get("pending_reward") 
                or user_data.get("unclaimed_reward") 
                or user_data.get("mined_unclaimed") 
                or user_data.get("unclaimed") 
                or user_data.get("pending_balance") 
                or 0
            )

        await activity(
            account_id,
            "MINING",
            "SKIP",
            f"Mining aktif | Pend={pending:.4f} ATF",
            row_key="activity"
        )

        remaining = interval
        while remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60

            await activity(
                account_id,
                "NEXT CYCLE",
                "WAIT",
                f"Cycle berikutnya dalam {minutes:02d}:{seconds:02d}",
                row_key="next_cycle"
            )

            await asyncio.sleep(1)
            remaining -= 1


# ==============================================================
# ACCOUNT DISCOVERY
# ==============================================================

def get_existing_accounts():

    accounts = []

    for path in SESSIONS_DIR.glob(
        "acc_*.session"
    ):

        accounts.append(
            path.stem
        )

    return sorted(
        accounts
    )


# ==============================================================
# FIRST RUN
# ==============================================================

async def ensure_accounts():

    accounts = get_existing_accounts()

    if accounts:

        return accounts

    account_id = "acc_001"

    print()
    print("=" * 70)
    print("ATF BOT - LOGIN TELEGRAM PERTAMA")
    print("=" * 70)
    print()

    client = ATFClient(
        account_id
    )

    try:

        await client.connect(
            require_login=True
        )

    finally:

        await client.close()

    return get_existing_accounts()


# ==============================================================
# MAIN LOOP
# ==============================================================

async def run_loop():

    accounts = await ensure_accounts()

    if not accounts:
        print("Tidak ada account.")
        return

    DASHBOARD.accounts = accounts

    for account in accounts:
        DASHBOARD.register(account)

    DASHBOARD.start()
    DASHBOARD.render()

    state_mgr = StateManager(DATA_DIR)

    try:

        tasks = [
            run_account_worker(account_id, state_mgr)
            for account_id in accounts
        ]
        
        await asyncio.gather(*tasks)

    finally:
        DASHBOARD.stop()


# ==============================================================
# START
# ==============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            run_loop()
        )

    except KeyboardInterrupt:

        print()
        print("Bot dihentikan.")
