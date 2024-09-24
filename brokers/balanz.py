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


class Balanz:
    def __init__(self, username, password, account_id, token_file="balanz_token.json"):
        self.username = username
        self.password = password
        self.account_id = account_id
        self.token_file = token_file

    def get_token(self):
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

    def do_login(self):
        token = self.get_token()

        if token:
            return token

        print("Getting a new authentication token...")

        params = {
            "avoidAuthRedirect": True
        }

        init_payload = {
            "user": self.username,
            "source": "WebV2"
        }

        r = requests.post(f"{BALANZ_BASE_URL}/auth/init", json=init_payload, headers=DEFAULT_HEADERS, params=params)

        if r.status_code != 200:
            raise BalanzLoginError(f"Login error: {r.text}")
        
        r = r.json()

        login_payload = {
            "user": self.username,
            "pass": self.password,
            "nonce": r['nonce'],
            "NombreDispositivo": "Firefox 121.0",
            "idDispositivo": "c54662d6-b273-48d2-9a94-1a85a9adb69f",
            "SistemaOperativo": "Windows",
            "VersionSO": "10",
            "source": "WebV2",
            "TipoDispositivo": "Web",
            "VersionAPP": "2.10.0"
        }

        r = requests.post(f"{BALANZ_BASE_URL}/auth/login", json=login_payload, headers=DEFAULT_HEADERS, params=params)

        if r.status_code == 200:
            response = r.json()
            token = response["AccessToken"]

            with open(self.token_file, "w") as f:
                f.write(json.dumps(
                    {
                        "token": token,
                        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    },
                    indent=4
                ))

            return token
        else:
            print(f"Login error: {r.text}")
            raise BalanzLoginError(r.text)

    def _balanz_request(self, endpoint):
        token = self.do_login()
        if not token:
            return None

        DEFAULT_HEADERS.update({
            "Authorization": token
        })

        url = f"{BALANZ_BASE_URL}/{endpoint}"
        print(f"Making request to URL {url}")

        r = requests.get(url, headers=DEFAULT_HEADERS)

        if r.status_code == 200:
            return r.json()

        print(f"Error: {r.text}")
        return None

    def account_status(self):
        today = datetime.now().strftime("%Y%m%d")
        url = f"estadodecuenta/{self.account_id}?Fecha={today}"
        account_status = self._balanz_request(url)

        return {
            item["Ticker"]:item
            for item in account_status["tenencia"]
        }

    def get_ticker_data(self, ticker):
        url = f'cotizacioninstrumento?ticker={ticker}&plazo=0'
        data = self._balanz_request(url)
        return data

    def get_future_cash_flow(self):
        url = f"bonos/flujoproyectado/{self.account_id}"
        cash_flow = self._balanz_request(url)
        return cash_flow['flujo']
