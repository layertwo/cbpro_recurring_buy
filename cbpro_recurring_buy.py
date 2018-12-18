#!/usr/bin/env python
"""A short and sweet script to automate deposits and purchases using Coinbase Pro API,
getting around the massive Coinbase recurring purchase fees."""

import argparse
import binascii
import logging
from time import sleep
import cbpro
import config

PARSER = argparse.ArgumentParser(
    description="python3 cbpro_recurring_buy.py --amount=100 --buy --cryptocurrency='BTC-USD'")

ACTION = PARSER.add_mutually_exclusive_group(required=True)

PARSER.add_argument("--amount",
                    type=int,
                    help="Amount to deposit or buy (in fiat)",
                    required=True)

PARSER.add_argument("--fiat_currency", type=str,
                    help="Fiat base pair to use (default is USD)",
                    default='USD')

PARSER.add_argument("--cryptocurrency",
                    type=str,
                    help="Pair to buy (only supports fiat pairs)")

PARSER.add_argument("--funding_method",
                    type=str,
                    help="Payment method to use",
                    required=True,
                    choices=['ach_bank_account'])

ACTION.add_argument("--deposit",
                    action='store_true',
                    help="Deposit specified amount into wallet")

ACTION.add_argument("--buy",
                    action='store_true',
                    help="Buy specified amount of BTC (in USD)")

PARSER.add_argument("--debug",
                    action='store_true',
                    help="Output debug information to stdout")

ARGS = PARSER.parse_args()

API_KEY = config.api_key
API_SECRET = config.api_secret
API_PASSPHRASE = config.api_passphrase
FUNDING_METHOD = ARGS.funding_method
AMOUNT = ARGS.amount
FUNDING_CURRENCY = ARGS.fiat_currency
CRYPTOCURRENCY_PAIR = ARGS.cryptocurrency

# Setup logging
if ARGS.debug:
    logging.basicConfig(format='%(asctime)s %(message)s %(levelname)s:',
                        level=logging.DEBUG)
else:
    logging.basicConfig(
        filename='cbpro_recurring_buy.log',
        format='%(asctime)s %(message)s %(levelname)s:',
        level=logging.INFO)


def cbpro_auth(key, secret, passphrase):
    """Function to handle authentication with the Coinbase Pro API"""
    # Auth with CBPro
    try:
        auth_client = cbpro.AuthenticatedClient(key, secret, passphrase)
        print(auth_client)
    except binascii.Error:
        logging.critical("API secret key is not in proper Base64 format!")
        exit()

    return auth_client


def deposit_funds(client, account):
    """Function to handle depositing funds from a given payment method
    to the Coinbase Pro fiat wallet"""

    # Get Coinbase Pro funding accounts
    payment_methods = client.get_payment_methods()

    if 'Invalid API Key' in payment_methods:
        logging.critical("API key is invalid!")
        exit()

    # Search all payment methods for one matching the given type
    for method in payment_methods:
        if method['type'] == account:
            method_id = method['id']
            method_name = method['name']
            method_limit_remaining = float(
                method['limits']['deposit'][0]['remaining']['amount'])

            logging.debug("Payment method name: %s", method_name)
            logging.debug("Payment method ID: %s", method_id)
            logging.debug("Payment method remaining limit: %d", method_limit_remaining)

    # Check that we got a proper payment method
    try:
        method_id
    except NameError:
        logging.critical("Could not find a payment method matching the selected method")
        exit()

    # Deposit with above params
    deposit_response = client.deposit(amount=AMOUNT,
                                      currency=FUNDING_CURRENCY,
                                      payment_method_id=method_id)

    logging.info(
        "Deposited %d %s to Coinbase Pro from Coinbase account %s",
        AMOUNT, FUNDING_CURRENCY, method_name)
    logging.info("Deposit will be available at %s", deposit_response['payout_at'])

    return deposit_response


def buy_cryptocurrency(client, cryptocurrency):
    """Function to handle buying the given cryptocurrency pair
    with the payment method provided in deposit_funds"""

    # Place buy of BTC with above params
    buy_response = client.place_market_order(product_id=cryptocurrency,
                                             side='buy',
                                             funds=str(AMOUNT))

    if 'Invalid API Key' in buy_response:
        logging.critical("API key is invalid!")
        exit()

    trade_id = buy_response['id']

    # Sleep to allow time for trade to complete
    sleep(5)

    # Check status of trade
    executed_trade_response = client.get_order(trade_id)

    if executed_trade_response['settled'] is True:
        # If trade was successful, gather data and log it
        fees = executed_trade_response['fill_fees']
        btc_bought = executed_trade_response['filled_size']

        logging.info("Bought %d of BTC, resulting in %s BTC", ARGS.amount, btc_bought)
        logging.info("Fees: %s", fees)
    else:
        # Sleep for longer, should never need to do this unless CBPro is overloaded
        sleep(30)
        executed_trade_response = client.get_order(trade_id)
        fees = executed_trade_response['fill_fees']
        btc_bought = executed_trade_response['filled_size']

        logging.info("Bought %d of BTC, resulting in %s BTC", ARGS.amount, btc_bought)
        logging.info("Fees: %s", fees)

    return executed_trade_response


if __name__ == '__main__':
    # Authenticate with Coinbase Pro
    AUTH_CLIENT = cbpro_auth(API_KEY, API_SECRET, API_PASSPHRASE)

    if ARGS.deposit:
        deposit_funds(AUTH_CLIENT, FUNDING_METHOD)
    elif ARGS.buy:
        buy_cryptocurrency(AUTH_CLIENT, CRYPTOCURRENCY_PAIR)
    else:
        print("No action flags selected, doing nothing and exiting...")
