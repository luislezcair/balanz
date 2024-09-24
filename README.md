# Balanz

Define the following env vars:

```env
BALANZ_USER=<your balanz user name>
BALANZ_PASSWORD=<your balanz password>
BALANZ_ACCOUNT_ID=<your balanz account id>
```

To get your account ID you can check the DevTools from your browser and find a call to this endpoint

`https://clientes.balanz.com/api/v1/estadodecuenta/<account_id>?Fecha=20231115&ta=1&idMoneda=1`

The script will read the quotes from the `quotes.json` file and write to an output file in ODS format (OpenOffice spreadsheet) that you can link to or open in Excel. You should add/remove the stocks/bonds/CEDEARS or whatever you want the prices for in this file. Just the ticker, one per line in JSON format.


### Installation

Create and setup a new virtualenv:

```sh
python -m venv env
source env/bin/activate
pip install --upgrade pip setuptools
```

Install the project dependencies:

```sh
pip install -r requirements.txt
```

Run the script. You need to pass the path to this file as a parameter to the script:

```sh
python main.py output.ods
```