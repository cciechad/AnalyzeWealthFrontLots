# AnalyzeWealthFrontLots
Python script to analyze Wealthfront open tax lots CSV download and display long-term and short-term gains/losses.

usage: AnalyzeLots.py [-h] [-s] [-n] -f FILE

Analyze Wealthfront cost-basis data. Displays net short/long term gains/losses and total short/long term losses by default.

options:

  -h, --help            show this help message and exit
  
  -s, --symbol          Display net gain/loss by symbol and net short/long-term gain/loss per symbol

  -n, --no-summary      No summary
  
  -f FILE, --file FILE  File to process

File required
