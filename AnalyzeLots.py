#!/usr/bin/env python
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas


def main() -> None:
    args: argparse.Namespace = parse_args()
    if args.file.is_file():
        data: pandas.DataFrame = pandas.read_csv(args.file, header=1,
                                                 names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value',
                                                        'gain'])
        data['date'] = pandas.to_datetime(data['date'])
        one_year_prior: datetime = datetime.now() - timedelta(days=365)
        is_short: bool = data['date'] >= one_year_prior
        is_long: bool = data['date'] < one_year_prior
        if not args.no_summary:
            is_loss: bool = data['gain'] < 0
            print(f"Net gain/loss {format_dollar(data['gain'].sum())}")
            print(f"Net short term gain/loss {format_dollar(data.loc[is_short, 'gain'].sum())}")
            print(f"Net long term gain/loss {format_dollar(data.loc[is_long, 'gain'].sum())}")
            print(f"Short term total value {format_dollar(data.loc[is_short, 'value'].sum())}")
            print(f"Long term total value {format_dollar(data.loc[is_long, 'value'].sum())}")
            print(f"Total short term losses {format_dollar(data.loc[is_short & is_loss, 'gain'].sum())}")
            print(f"Total long term losses {format_dollar(data.loc[is_long & is_loss, 'gain'].sum())}")
        if args.symbol | args.no_summary:
            symbols: list[str] = data['symbol'].explode().unique().tolist()
            symbols_net: list[float] = []
            symbols_net_short: list[float] = []
            symbols_net_long: list[float] = []
            for iter_symbol in symbols:
                is_iter_symbol: bool = data['symbol'] == iter_symbol
                symbols_net.append(data.loc[is_iter_symbol, 'gain'].sum())
                symbols_net_long.append(data.loc[is_iter_symbol & is_long, 'gain'].sum(0))
                symbols_net_short.append(data.loc[is_iter_symbol & is_short, 'gain'].sum(0))
            symbols_range: range = range(len(symbols))
            print('Net gain/loss per symbol')
            symbols_net_print(symbols, symbols_net, symbols_range)
            print('Net short term per symbol')
            symbols_net_print(symbols, symbols_net_short, symbols_range)
            print('Net long term per symbol')
            symbols_net_print(symbols, symbols_net_long, symbols_range)
    else:
        print(f'{args.file} is not a readable file.')
    return


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


def symbols_net_print(symbols: list[str], net: list[float], symbols_range: range) -> None:
    symbols_dict: dict = {symbols[i]: net[i] for i in symbols_range}
    print("\n".join(f"{k}\t{format_dollar(v)}" for k, v in symbols_dict.items()))
    return


def format_dollar(amount: float) -> str:
    formatted_absolute_amount: str = '${:,.2f}'.format(abs(amount))
    return f'-{formatted_absolute_amount}' if round(amount, 2) < 0 else formatted_absolute_amount


if __name__ == '__main__':
    main()
