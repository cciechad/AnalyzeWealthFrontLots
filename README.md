# AnalyzeWealthFrontLots
Python script to analyze Wealthfront open tax lots CSV download and display long-term and short-term gains/losses.

usage: AnalyzeLots.py [-h] [-s] [-n] -f FILE [-d DAYS]

Analyze Wealthfront cost-basis data. Displays net short/long term gains/losses and total short/long term losses by default.

options:

  -h, --help            show this help message and exit
  
  -s, --symbol          Display net gain/loss by symbol and net short/long-term gain/loss per symbol

  -n, --no-summary      No summary
  
  -f FILE, --file FILE  File to process

  -d DAYS, --days DAYS  Show results for number of days in the future

  -v, --verbose         Display ETF descriptions

  -l, --live            Get live price from YF(experimental)

File required

Python 3, pandas and yfinance required. Tested on 3.11 and 3.12.
