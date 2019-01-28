# A simple Coinbase Pro API automation script

## Overview
Couldn't sleep one night and threw this together. This is the initial upload, so please double check the code before putting any of your money on the line.

I set it up with a weekly deposit cron, and two weekly buy cron jobs, but do with it what you will!

Thanks.

## Setup
### Installation
* Install the script requirements
	* `pip3 install -r requirements.txt`
* Set your credentials in config with your API keys or set the appropriate environment variables in your .bashrc
* Source config with the set environment variables

## Example usage

### Deposit
`python3 cbpro_recurring_buy.py --amount=100 --deposit --funding_method='ach_bank_account'`

### Buy
`python3 cbpro_recurring_buy.py --amount=100 --buy --cryptocurrency='BTC-USD'`

## API library used:
https://github.com/danpaquin/coinbasepro-python

