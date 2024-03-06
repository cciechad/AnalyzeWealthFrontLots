#!/usr/bin/env python
import pandas
import argparse
from pathlib import Path
from datetime import datetime, timedelta


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Analyze Wealthfront cost-basis data. Displays total short/long-term gains/losses by default.",
        epilog="File required")
    parser.add_argument(
        '-s', '--symbol', help='Display gain/loss by symbol and short/long-term gain/loss per symbol',
        action='store_true')
    parser.add_argument('-n', '--nosummary', help='No summary', action='store_true')
    parser.add_argument('-f', '--file', help='File to process', type=lambda p: Path(p).absolute(), required=True)
    return parser.parse_args()


def main() -> None:
    args: argparse.Namespace = parse_args()
    one_year_prior: datetime = datetime.now() - timedelta(days=365)
    if args.file.is_file():
        data: pandas.DataFrame = pandas.read_csv(
                args.file, header=1, names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value', 'gain'])
        data['date'] = pandas.to_datetime(data['date'])
        if not args.nosummary:
            print(f"Total gain/loss ${round(data['gain'].sum(), 2)}")
            print(f"Short term gain/loss ${round(data.loc[data['date'] >= one_year_prior, 'gain'].sum(), 2)}")
            print(f"Long term gain/loss ${round(data.loc[data['date'] < one_year_prior, 'gain'].sum(), 2)}")
        if args.symbol | args.nosummary:
            symbols: list[str] = data['symbol'].str.split(',\s*').explode().unique().tolist()
            symbols_gain: list[float] = []
            symbols_gain_short: list[float] = []
            symbols_gain_long: list[float] = []
            for iter_symbol in symbols:
                symbols_gain.append(round(data.loc[data['symbol'] == iter_symbol, 'gain'].sum(), 2))
                symbols_gain_long.append(
                    round(
                        data.loc[(data['symbol'] == iter_symbol) & (data['date'] < one_year_prior), 'gain'].sum(0), 2))
                symbols_gain_short.append(
                    round(
                        data.loc[(data['symbol'] == iter_symbol) & (data['date'] >= one_year_prior), 'gain'].sum(0), 2))
            symbols_dict: dict = {symbols[i]: symbols_gain[i] for i in range(len(symbols))}
            print('Total gain/loss per symbol')
            print("\n".join(f"{k}\t${v}" for k, v in symbols_dict.items()))
            symbols_short_dict: dict = {symbols[i]: symbols_gain_short[i] for i in range(len(symbols))}
            print('Short term per symbol')
            print("\n".join(f"{k}\t${v}" for k, v in symbols_short_dict.items()))
            symbols_long_dict: dict = {symbols[i]: symbols_gain_long[i] for i in range(len(symbols))}
            print('Long term per symbol')
            print("\n".join(f"{k}\t${v}" for k, v in symbols_long_dict.items()))


if __name__ == '__main__':
    main()
