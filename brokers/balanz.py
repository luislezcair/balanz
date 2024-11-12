from typing import Literal
from datetime import datetime, timedelta
import json
import requests
import dotenv
dotenv.load_dotenv()

BALANZ_BASE_URL = "https://clientes.balanz.com/api/v1"

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"
}

TOKEN_VALID_TIME = timedelta(seconds=900)


class BalanzLoginError(Exception):
    pass

class BalanzError(Exception):
    pass


class Balanz:
    def __init__(self, username: str, password: str, account_id: str, token_file: str ="balanz_token.json"):
        self.username = username
        self.password = password
        self.account_id = account_id
        self.token_file = token_file
        self.token: str | None = ""

    def _get_token(self) -> str | None:
        try:
            with open(self.token_file) as f:
                print("Reading token from cache file")
                token_file = json.loads(f.read())

            expiration = datetime.strptime(token_file["timestamp"], "%d-%m-%Y %H:%M:%S")
            if expiration + TOKEN_VALID_TIME > datetime.now():
                print("Token from file is still valid")
                return token_file["token"]
        except Exception:
            print("Token file does not exist")

        return None

    def _balanz_request(self, endpoint) -> dict:
        if not self.token:
            raise BalanzError("No token found, call login() first")

        DEFAULT_HEADERS.update({
            "Authorization": self.token
        })

        url = f"{BALANZ_BASE_URL}/{endpoint}"
        print(f"Making request to URL {url}")

        r = requests.get(url, headers=DEFAULT_HEADERS)

        if r.status_code == 200:
            return r.json()

        raise BalanzError(r.text)

    def _get_login_nonce(self) -> str:
        """Returns the nonce code"""

        params = {
            "avoidAuthRedirect": True
        }

        payload = {
            "user": self.username,
            "source": "WebV2"
        }

        r = requests.post(f"{BALANZ_BASE_URL}/auth/init", json=payload, headers=DEFAULT_HEADERS, params=params)

        if r.status_code != 200:
            raise BalanzLoginError(f"Login error: {r.text}")

        r = r.json()
        return r["nonce"]

    def login(self):
        self.token = self._get_token()

        if self.token:
            return

        print("Getting a new authentication token...")

        nonce = self._get_login_nonce()

        payload = {
            "user": self.username,
            "pass": self.password,
            "nonce": nonce,
            "NombreDispositivo": "Firefox 121.0",
            "idDispositivo": "c54662d6-b273-48d2-9a94-1a85a9adb69f",
            "SistemaOperativo": "Windows",
            "VersionSO": "10",
            "source": "WebV2",
            "TipoDispositivo": "Web",
            "VersionAPP": "2.10.0"
        }

        params = {
            "avoidAuthRedirect": True
        }

        r = requests.post(f"{BALANZ_BASE_URL}/auth/login", json=payload, headers=DEFAULT_HEADERS, params=params)

        if r.status_code == 200:
            response = r.json()
            self.token = response["AccessToken"]

            with open(self.token_file, "w") as f:
                f.write(json.dumps(
                    {
                        "token": self.token,
                        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    },
                    indent=4
                ))
        else:
            print(f"Login error: {r.text}")
            raise BalanzLoginError(r.text)

    def account_status(self) -> dict:
        today = datetime.now().strftime("%Y%m%d")
        url = f"estadodecuenta/{self.account_id}?Fecha={today}"
        account_status = self._balanz_request(url)

        return {
            item["Ticker"]:item
            for item in account_status["tenencia"]
        }

    def get_ticker_data(self, ticker: str, settlement: Literal[0, 1] = 1) -> dict:
        """Returns the data for stock `ticker`. Settlement period can be 0 for Contado Inmediato and 1 for 24 hours"""

        url = f'cotizacioninstrumento?ticker={ticker}&plazo={settlement}'
        data = self._balanz_request(url)
        return data["Cotizacion"]

    def get_future_cash_flow(self) -> dict:
        url = f"bonos/flujoproyectado/{self.account_id}"
        cash_flow = self._balanz_request(url)
        return cash_flow['flujo']
