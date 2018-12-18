import cbpro
import config
import logging
from time import sleep
import argparse

parser = argparse.ArgumentParser(description="python3 cbpro_recurring_buy.py --amount=100 --buy --cryptocurrency='BTC-USD'")
action = parser.add_mutually_exclusive_group(required=True)
parser.add_argument("--amount", type=int, help="Amount to deposit or buy (in fiat)", required=True)
parser.add_argument("--fiat_currency", type=str, help="Fiat base pair to use (default is USD)", default='USD')
parser.add_argument("--cryptocurrency", type=str, help="Pair to buy (only supports fiat pairs)")
parser.add_argument("--funding_method", type=str, help="Payment method to use", required=True,
                    choices=['ach_bank_account'])
action.add_argument("--deposit", action='store_true', help="Deposit specified amount into wallet")
action.add_argument("--buy", action='store_true', help="Buy specified amount of BTC (in USD)")
parser.add_argument("--debug", action='store_true', help="Output debug information to stdout")
args = parser.parse_args()

cbpro_api_key = config.api_key
cbpro_api_secret = config.api_secret
cbpro_api_passphrase = config.api_passphrase
funding_method = args.funding_method
amount = args.amount
funding_currency = args.fiat_currency
cryptocurrency_pair = args.cryptocurrency

# Setup logging
if args.debug:
    logging.basicConfig(format='%(asctime)s %(message)s %(levelname)s:', level=logging.DEBUG)
else:
    logging.basicConfig(filename='cbpro_recurring_buy.log', format='%(asctime)s %(message)s %(levelname)s:', level=logging.INFO)


def cbpro_auth(key, secret, passphrase):
    # Deposit funds from Coinbase wallet to Coinbase Pro wallet
    # Auth with CBPro
    try:
        auth_client = cbpro.AuthenticatedClient(key, secret, passphrase)
    except Exception as e:
        logging.critical(e)
        exit()

    return auth_client


def deposit_funds(client, account):
    # Get Coinbase Pro funding accounts
    payment_methods = client.get_payment_methods()

    # Search all payment methods for one matching the given type
    for method in payment_methods:
        if method['type'] == account:
            method_id = method['id']
            method_name = method['name']
            method_limit_remaining = float(method['limits']['deposit'][0]['remaining']['amount'])

            logging.debug("Payment method name: " + method_name)
            logging.debug("Payment method ID: " + method_id)
            logging.debug("Payment method remaining limit: " + str(method_limit_remaining))

    # Check that we got a proper payment method
    try:
        method_id
    except NameError:
        logging.critical("Could not find a payment method matching the selected method")
        exit()

    # Deposit with above params
    deposit_response = client.deposit(amount=amount,
                                      currency=funding_currency,
                                      payment_method_id=method_id)

    logging.info(
        "Deposited " + str(amount) + funding_currency + " to Coinbase Pro from Coinbase account " + method_name)
    logging.info("Deposit will be available at " + deposit_response['payout_at'])

    return deposit_response


def buy_cryptocurrency(client, cryptocurrency):
    # Place buy of BTC with above params
    buy_response = client.place_market_order(product_id=cryptocurrency,
                                             side='buy',
                                             funds=str(amount))

    trade_id = buy_response['id']

    # Sleep to allow time for trade to complete
    sleep(5)

    # Check status of trade
    executed_trade_response = client.get_order(trade_id)

    if executed_trade_response['settled'] is True:
        # If trade was successful, gather data and log it
        fees = executed_trade_response['fill_fees']
        btc_bought = executed_trade_response['filled_size']

        logging.info("Bought " + str(args.amount) + " of BTC, resulting in " + btc_bought + " BTC")
        logging.info("Fees: " + fees)
    else:
        # Sleep for longer, should never need to do this unless CBPro is overloaded
        sleep(30)
        executed_trade_response = client.get_order(trade_id)
        fees = executed_trade_response['fill_fees']
        btc_bought = executed_trade_response['filled_size']

        logging.info("Bought " + str(args.amount) + " of BTC, resulting in " + btc_bought + " BTC")
        logging.info("Fees: " + fees)

    return executed_trade_response


if __name__ == '__main__':
    auth_client = cbpro_auth(cbpro_api_key, cbpro_api_secret, cbpro_api_passphrase)
    if args.deposit:
        deposit_funds(auth_client, funding_method)
    elif args.buy:
        buy_cryptocurrency(auth_client, cryptocurrency_pair)
    else:
        print("No action flags selected, doing nothing and exiting...")
