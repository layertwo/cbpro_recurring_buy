# A simple Coinbase Pro API automation script
Couldn't sleep one night and threw this together. This is the initial upload, so please double check the code before putting any of your money on the line.  

Should all work and is very simple:
* Configure the script with your credentials by replacing relevant variables in config.py with your API keys
* Deposit: python3 cbpro_recurring_buy.py --amount=100 --deposit --funding_method='ach_bank_account'
* Buy: python3 cbpro_recurring_buy.py --amount=100 --buy --cryptocurrency='BTC-USD'

I set it up with a weekly deposit cron, and two weekly buy cron jobs, but do with it what you will!

Thanks.

# API library used:
https://github.com/danpaquin/coinbasepro-python