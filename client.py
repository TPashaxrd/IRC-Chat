import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import threading
import time
import sys
from datetime import datetime
from colorama import init, Fore, Style

USE_PROMPT_TOOLKIT = False
try:
    from prompt_toolkit import PromptSession, print_formatted_text, HTML
    from prompt_toolkit.patch_stdout import patch_stdout
    # USE_PROMPT_TOOLKIT = True
except Exception:
    USE_PROMPT_TOOLKIT = True

init(autoreset=True)

if len(sys.argv) < 3:
    print(Fore.RED + "Using: py client.py https://irc.r3tosint.xyz <username>" + Style.RESET_ALL)
    sys.exit(1)

SERVER = sys.argv[1].rstrip("/")
USERNAME = sys.argv[2]
stop_flag = False
VERIFY = False if SERVER.startswith("https://") else True
TIMEOUT = 5

def now():
    return datetime.now().strftime("%H:%M:%S")

BANNER_COLOR = Fore.CYAN
HANDSHAKE_COLOR = Fore.MAGENTA
INFO_COLOR = Fore.BLUE
ERROR_COLOR = Fore.RED
JOIN_COLOR = Fore.YELLOW
MESSAGE_COLOR = Fore.GREEN
ME_COLOR = Fore.LIGHTMAGENTA_EX
PROMPT_COLOR = Fore.LIGHTWHITE_EX

def hacker_banner():
    banner = r"""
 _______  ______ _________            _______  _______  ______   _______    ______             _________ _______  _______  _______  _______  _       
(  ____ )/ ___  \\__   __/           (       )(  ___  )(  __  \ (  ____ \  (  ___ \ |\     /|  \__   __/(  ___  )(  ____ )(  ____ )(  ___  )| \    /\
| (    )|\/   \  \  ) (              | () () || (   ) || (  \  )| (    \/  | (   ) )( \   / )     ) (   | (   ) || (    )|| (    )|| (   ) ||  \  / /
| (____)|   ___) /  | |      _____   | || || || (___) || |   ) || (__      | (__/ /  \ (_) /      | |   | |   | || (____)|| (____)|| (___) ||  (_/ / 
|     __)  (___ (   | |     (_____)  | |(_)| ||  ___  || |   | ||  __)     |  __ (    \   /       | |   | |   | ||  _____)|     __)|  ___  ||   _ (  
| (\ (         ) \  | |              | |   | || (   ) || |   ) || (        | (  \ \    ) (        | |   | |   | || (      | (\ (   | (   ) ||  ( \ \ 
| ) \ \__/\___/  /  | |              | )   ( || )   ( || (__/  )| (____/\  | )___) )   | |        | |   | (___) || )      | ) \ \__| )   ( ||  /  \ \
|/   \__/\______/   )_(              |/     \||/     \|(______/ (_______/  |/ \___/    \_/        )_(   (_______)|/       |/   \__/|/     \||_/    \/
"""
    print(BANNER_COLOR + banner + Style.RESET_ALL)
    print(JOIN_COLOR + f"[{now()}] initializing client... welcome, {USERNAME}" + Style.RESET_ALL)
def faux_handshake():
    steps = [
        "opening secure socket (simulated)",
        "negotiating cipher suite",
        "exchanging keys",
        "Sometimes I Dreaming saving the world. - Mr Robot",
        "authenticating identity",
        "handshake complete"
    ]
    for s in steps:
        print(HANDSHAKE_COLOR + f"[{now()}] · {s}..." + Style.RESET_ALL)
        time.sleep(0.25)

def safe_post(path, json):
    url = f"{SERVER}{path}"
    try:
        return requests.post(url, json=json, timeout=TIMEOUT, verify=VERIFY)
    except Exception as e:
        print(ERROR_COLOR + f"[{now()}] ! POST {url} hata: {e}" + Style.RESET_ALL)
        return None

def safe_get(path, params=None):
    url = f"{SERVER}{path}"
    try:
        return requests.get(url, params=params, timeout=TIMEOUT, verify=VERIFY)
    except Exception as e:
        print(ERROR_COLOR + f"[{now()}] ! GET {url} hata: {e}" + Style.RESET_ALL)
        return None

def print_message(text, kind="msg"):
    if kind == "join":
        color = JOIN_COLOR
    elif kind == "me":
        color = ME_COLOR
    else:
        color = MESSAGE_COLOR

    sys.stdout.write("\r")
    sys.stdout.write(" " * 200 + "\r")
    sys.stdout.flush()
    sys.stdout.write(color + f"[{now()}] {text}" + Style.RESET_ALL + "\n")
    sys.stdout.write(PROMPT_COLOR + ">>> " + Style.RESET_ALL)
    sys.stdout.flush()


def poll_messages():
    while not stop_flag:
        try:
            resp = safe_get("/messages", params={"username": USERNAME})
            if resp and resp.status_code == 200:
                msgs = resp.json().get("messages", [])
                for m in msgs:
                    if "connected to chat" in m or "joined" in m:
                        print_message(m, kind="join")
                    elif m.startswith("*"):
                        print_message(m, kind="me")
                    else:
                        print_message(m, kind="msg")
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)

hacker_banner()
faux_handshake()

print(INFO_COLOR + f"[{now()}] trying to register as {USERNAME} -> {SERVER}/connect" + Style.RESET_ALL)
resp = safe_post("/connect", json={"username": USERNAME})
if not resp or resp.status_code != 200:
    print(ERROR_COLOR + f"[{now()}] bağlantı başarısız. Server çalışıyor mu? URL doğru mu?" + Style.RESET_ALL)
else:
    print(INFO_COLOR + f"[{now()}] registered: {resp.json().get('message')}" + Style.RESET_ALL)
    safe_post("/send", json={"username": USERNAME, "message": f"{USERNAME} connected to chat."})
    print_message(f"*** {USERNAME} connected to chat ***", kind="join")

threading.Thread(target=poll_messages, daemon=True).start()

if USE_PROMPT_TOOLKIT:
    session = PromptSession()
    try:
        with patch_stdout():
            while True:
                text = session.prompt(PROMPT_COLOR + ">>> " + Style.RESET_ALL)
                if text.lower() == "/quit":
                    stop_flag = True
                    safe_post("/disconnect", json={"username": USERNAME})
                    print(JOIN_COLOR + f"[{now()}] çıkış yapılıyor..." + Style.RESET_ALL)
                    break
                if text.strip() == "":
                    continue
                payload = text
                if text.startswith("/me "):
                    payload = text[4:]
                    payload = f"* {USERNAME} {payload}"
                safe_post("/send", json={"username": USERNAME, "message": payload})
    except (KeyboardInterrupt, EOFError):
        stop_flag = True
        safe_post("/disconnect", json={"username": USERNAME})
        print(JOIN_COLOR + f"\n[{now()}] Ctrl-C ile çıkış yapıldı." + Style.RESET_ALL)
else:
    try:
        while True:
            sys.stdout.write(PROMPT_COLOR + f">>> " + Style.RESET_ALL)
            sys.stdout.flush()
            text = sys.stdin.readline()
            if not text:
                break
            text = text.rstrip("\n")
            if text.lower() == "/quit":
                stop_flag = True
                safe_post("/disconnect", json={"username": USERNAME})
                print(JOIN_COLOR + f"[{now()}] çıkış yapılıyor..." + Style.RESET_ALL)
                break
            if text.strip() == "":
                continue
            payload = text
            if text.startswith("/me "):
                payload = text[4:]
                payload = f"* {USERNAME} {payload}"
            safe_post("/send", json={"username": USERNAME, "message": payload})
    except KeyboardInterrupt:
        stop_flag = True
        safe_post("/disconnect", json={"username": USERNAME})
        print(JOIN_COLOR + f"\n[{now()}] Ctrl-C ile çıkış yapıldı." + Style.RESET_ALL)