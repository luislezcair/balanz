import os
import sys
import json
import re
from datetime import datetime
import dotenv
import pyexcel
from brokers.balanz import Balanz
dotenv.load_dotenv()


BALANZ_USER = os.environ["BALANZ_USER"]
BALANZ_PASSWORD = os.environ["BALANZ_PASSWORD"]
BALANZ_ACCOUNT_ID = os.environ["BALANZ_ACCOUNT_ID"]

QUOTES_FILE = "quotes.json"
ACCOUNT_OUTPUT_FILE = "my_account.json"


def parse_date(quote_date):
    if not quote_date:
        return ""

    if re.match(r"\d{1,2}:\d{1,2}", quote_date):
        return datetime.now().date()

    if re.match(r"\d{1,2}/\d{1,2}/\d{4}", quote_date):
        return datetime.strptime(quote_date, "%d/%m/%Y").date()

    if re.match(r"\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}.\d+", quote_date):
        return datetime.strptime(quote_date, "%Y-%m-%d %H:%M:%S.%f").date()


def get_quotes(balanz: Balanz, quotes: list):
    account = balanz.account_status()

    # print(f"Saving account status to file {ACCOUNT_OUTPUT_FILE}")
    # with open(ACCOUNT_OUTPUT_FILE, "w") as account_file:
    #     account_file.write(json.dumps(account, indent=4))

    account_tickers = account.keys()

    data = [
        ["Ticker", "Fecha", "Valor", "Compra", "Venta"]
    ]

    for ticker in quotes:
        if ticker in account_tickers:
            quote = account[ticker]
            ticker_date = parse_date(quote["FechaUltimoOperado"])
            price = buy_price = sell_price = quote["Precio"]
            print(f"Found ticker {ticker} in account with current price {price}")
        else:
            print(f"Ticker {ticker} not found in account. I will have to search in Balanz")
            quote = balanz.get_ticker_data(ticker)["Cotizacion"]
            ticker_date = parse_date(quote["UltimaOperacion"])

            # The ticker may not be found due to it not listed in BYMA
            if quote["SecurityID"] is None:
                price = buy_price = sell_price = 1.0
            else:
                price = quote["UltimoPrecio"]
                buy_price = quote["PrecioCompra"]
                sell_price = quote["PrecioVenta"]

            print(f"Found ticker {ticker} in Balanz with current price {price}")

        data.append([ticker, ticker_date, price, buy_price, sell_price])

    return data


def get_cash_flow(balanz: Balanz):
    data = [
        ["Especie", "Fecha", "Residual", "Renta", "Amortizacion", "Renta/Amortizacion", "Total", "Moneda"]
    ]

    cash_flow = balanz.get_future_cash_flow()

    for flow in cash_flow:
        data.append([
            flow['codigoespeciebono'],
            flow['fecha'],
            flow['vr'],
            flow['renta'],
            flow['amort'],
            flow['rentaamort'],
            flow['total'],
            flow['tipo_moneda']
        ])

    return data


def main(excel_file: str):
    print(f"Reading quotes from file {QUOTES_FILE}")
    with open(QUOTES_FILE) as quotes_file:
        quotes = json.loads(quotes_file.read())

    balanz = Balanz(BALANZ_USER, BALANZ_PASSWORD, BALANZ_ACCOUNT_ID)

    book_dict = {
        "Titulos": get_quotes(balanz, quotes),
        "Flujos": get_cash_flow(balanz)
    }

    pyexcel.save_book_as(
        dest_file_name=excel_file,
        bookdict=book_dict
    )



if __name__ == "__main__":
    main(sys.argv[1])
