#!/usr/bin/env python
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas


def parse_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Analyze Wealthfront cost-basis data. Displays net short/long term gains/losses and total "
                    "short/long term losses by default.", epilog="File required")
    parser.add_argument('-s', '--symbol',
                        help='Display net gain/loss by symbol and net short/long-term gain/loss per symbol',
                        action='store_true')
    parser.add_argument('-n', '--no-summary', help='No summary', action='store_true')
    parser.add_argument('-f', '--file', help='File to process', type=lambda p: Path(p).absolute(), required=True)
    return parser.parse_args()


def fmt_dollar(amount: float) -> str:
    formatted_absolute_amount: str = '${:,.2f}'.format(abs(amount))
    if round(amount, 2) < 0:
        return f'-{formatted_absolute_amount}'
    return formatted_absolute_amount


def main() -> None:
    args: argparse.Namespace = parse_args()
    if args.file.is_file():
        data: pandas.DataFrame = pandas.read_csv(args.file, header=1,
                                                 names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value',
                                                        'gain'])
        data['date'] = pandas.to_datetime(data['date'])
        one_year_prior: datetime = datetime.now() - timedelta(days=365)
        date_short: bool = data['date'] >= one_year_prior
        date_long: bool = data['date'] < one_year_prior
        if not args.no_summary:
            is_loss: bool = data['gain'] < 0
            print(f"Net gain/loss {fmt_dollar(data['gain'].sum())}")
            print(f"Net short term gain/loss {fmt_dollar(data.loc[date_short, 'gain'].sum())}")
            print(f"Net long term gain/loss {fmt_dollar(data.loc[date_long, 'gain'].sum())}")
            print(f"Total short term losses {fmt_dollar(data.loc[date_short & is_loss, 'gain'].sum())}")
            print(f"Total long term losses {fmt_dollar(data.loc[date_long & is_loss, 'gain'].sum())}")
        if args.symbol | args.no_summary:
            symbols: list[str] = data['symbol'].explode().unique().tolist()
            symbols_gain: list[float] = []
            symbols_gain_short: list[float] = []
            symbols_gain_long: list[float] = []
            for iter_symbol in symbols:
                is_iter_symbol: bool = data['symbol'] == iter_symbol
                symbols_gain.append(data.loc[is_iter_symbol, 'gain'].sum())
                symbols_gain_long.append(data.loc[is_iter_symbol & date_long, 'gain'].sum(0))
                symbols_gain_short.append(data.loc[is_iter_symbol & date_short, 'gain'].sum(0))
            symbols_range: range = range(len(symbols))
            symbols_dict: dict = {symbols[i]: symbols_gain[i] for i in symbols_range}
            print('Net gain/loss per symbol')
            print("\n".join(f"{k}\t{fmt_dollar(v)}" for k, v in symbols_dict.items()))
            symbols_short_dict: dict = {symbols[i]: symbols_gain_short[i] for i in symbols_range}
            print('Net short term per symbol')
            print("\n".join(f"{k}\t{fmt_dollar(v)}" for k, v in symbols_short_dict.items()))
            symbols_long_dict: dict = {symbols[i]: symbols_gain_long[i] for i in symbols_range}
            print('Net long term per symbol')
            print("\n".join(f"{k}\t{fmt_dollar(v)}" for k, v in symbols_long_dict.items()))


if __name__ == '__main__':
    main()
