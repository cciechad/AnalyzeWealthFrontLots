#!/usr/bin/env python
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Analyze Wealthfront cost-basis data. Displays net short/long-term gains/losses and total short/long term losses by default.",
        epilog="File required")
    parser.add_argument(
        '-s', '--symbol', help='Display net gain/loss by symbol and net short/long-term gain/loss per symbol',
        action='store_true')
    parser.add_argument('-n', '--no-summary', help='No summary', action='store_true')
    parser.add_argument('-f', '--file', help='File to process', type=lambda p: Path(p).absolute(), required=True)
    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_args()
    one_year_prior: datetime = datetime.now() - timedelta(days=365)
    if args.file.is_file():
        data: pandas.DataFrame = pandas.read_csv(
            args.file, header=1, names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value', 'gain'])
        data['date'] = pandas.to_datetime(data['date'])
        if not args.no_summary:
            print(f"Net gain/loss ${round(data['gain'].sum(), 2):,.2f}")
            print(f"Net short term gain/loss ${round(data.loc[data['date'] >= one_year_prior, 'gain'].sum(), 2):,.2f}")
            print(f"Net long term gain/loss ${round(data.loc[data['date'] < one_year_prior, 'gain'].sum(), 2):,.2f}")
            print(
                f"Total short term losses ${round(data.loc[(data['date'] >= one_year_prior) & (data['gain'] < 0), 'gain'].sum(), 2):,.2f}")
            print(
                f"Total long term losses ${round(data.loc[(data['date'] < one_year_prior) & (data['gain'] < 0), 'gain'].sum(), 2):,.2f}")
        if args.symbol | args.no_summary:
            symbols: list[str] = data['symbol'].explode().unique().tolist()
            symbols_gain: list[float] = []
            symbols_gain_short: list[float] = []
            symbols_gain_long: list[float] = []
            for iter_symbol in symbols:
                symbols_gain.append(data.loc[data['symbol'] == iter_symbol, 'gain'].sum())
                symbols_gain_long.append(
                    data.loc[(data['symbol'] == iter_symbol) & (data['date'] < one_year_prior), 'gain'].sum(0))
                symbols_gain_short.append(
                    data.loc[(data['symbol'] == iter_symbol) & (data['date'] >= one_year_prior), 'gain'].sum(0))
            symbols_dict: dict = {symbols[i]: symbols_gain[i] for i in range(len(symbols))}
            print('Net gain/loss per symbol')
            print("\n".join(f"{k}\t${v:,.2f}" for k, v in symbols_dict.items()))
            symbols_short_dict: dict = {symbols[i]: symbols_gain_short[i] for i in range(len(symbols))}
            print('Net short term per symbol')
            print("\n".join(f"{k}\t${v:,.2f}" for k, v in symbols_short_dict.items()))
            symbols_long_dict: dict = {symbols[i]: symbols_gain_long[i] for i in range(len(symbols))}
            print('Net long term per symbol')
            print("\n".join(f"{k}\t${v:,.2f}" for k, v in symbols_long_dict.items()))


if __name__ == '__main__':
    main()
