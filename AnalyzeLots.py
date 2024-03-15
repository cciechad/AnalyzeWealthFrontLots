#!/usr/bin/env python
import argparse
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path

import pandas as pd


def main() -> None:
    args: argparse.Namespace = parse_args()
    if args.file.is_file():
        data: pd.DataFrame = pd.read_csv(args.file, header=1, low_memory=False, memory_map=True,
                                         names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value', 'gain'])
        data['date'] = pd.to_datetime(data['date'])
        one_year_prior: datetime = datetime.now() - timedelta(days=(365 - args.days))
        is_short: bool = data['date'] >= one_year_prior
        is_long: bool = data['date'] < one_year_prior
        if args.live:
            data = data.assign(value=lambda x: update_value(x['symbol'], x['quantity']))
            data['gain'] = data['value'] - data['cost']
        if not args.no_summary:
            is_loss: bool = data['gain'] < 0
            print(f"Net gain/loss {format_dollar(data['gain'].sum())}")
            print(f"Net short term gain/loss {format_dollar(data.loc[is_short, 'gain'].sum())}")
            print(f"Net long term gain/loss {format_dollar(data.loc[is_long, 'gain'].sum())}")
            print(f"Total value {format_dollar(data['value'].sum())}")
            print(f"Short term total value {format_dollar(data.loc[is_short, 'value'].sum())}")
            print(f"Long term total value {format_dollar(data.loc[is_long, 'value'].sum())}")
            print(f"Total short term losses {format_dollar(data.loc[is_short & is_loss, 'gain'].sum())}")
            print(f"Total long term losses {format_dollar(data.loc[is_long & is_loss, 'gain'].sum())}")
        if args.symbol | args.no_summary:
            symbols: list[str] = data['symbol'].explode().unique().tolist()
            symbols_name: list[str] = data['display_name'].explode().unique().tolist()
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
            symbols_net_print(symbols, symbols_name, symbols_net, symbols_range, args.verbose)
            print('Net short term gain/loss per symbol')
            symbols_net_print(symbols, symbols_name, symbols_net_short, symbols_range, args.verbose)
            print('Net long term gain/loss per symbol')
            symbols_net_print(symbols, symbols_name, symbols_net_long, symbols_range, args.verbose)
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
    parser.add_argument('-d', '--days', help='Show results for number of days in the future', type=int, default=0)
    parser.add_argument('-v', '--verbose', help='Display ETF descriptions', action='store_true')
    parser.add_argument('-l', '--live', help='Get live price from YF(experimental)', action='store_true')
    return parser.parse_args()


def symbols_net_print(symbols: list[str], names: list[str], net: list[float], symbols_range: range,
                      verbose: bool) -> None:
    symbols_dict: dict = {symbols[i]: (names[i], net[i]) for i in symbols_range}
    if verbose:
        print("\n".join(f"{k:8s}{v[0]:42.42s}{format_dollar(v[1]):>21s}" for k, v in symbols_dict.items()))
    else:
        print("\n".join(f"{k}\t{format_dollar(v[1])}" for k, v in symbols_dict.items()))
    return


def format_dollar(amount: float) -> str:
    formatted_absolute_amount: str = '${:,.2f}'.format(abs(amount))
    return f'-{formatted_absolute_amount}' if round(amount, 2) < 0 else formatted_absolute_amount


def update_value(symbols: pd.Series, quantities: pd.Series) -> pd.Series:
    value_list: list[float] = []
    for symbol, quantity in zip(symbols, quantities):
        value_list.append(quantity * get_price(symbol))
    return pd.Series(value_list)


@cache
def get_price(symbol: str) -> float:
    from yfinance import Ticker
    ticker: Ticker.fast_info = Ticker(str.upper(symbol)).fast_info
    return ticker['lastPrice']


if __name__ == '__main__':
    main()
