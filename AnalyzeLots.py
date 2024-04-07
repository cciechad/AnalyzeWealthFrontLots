#!/usr/bin/env python
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from multiprocessing import Pool
from pathlib import Path

from numpy import uint16, float32
from pandas import DataFrame, Series, read_csv, options as pdopt


def main() -> None:
    args: Namespace = parse_args()
    pdopt.mode.copy_on_write = True
    if args.file.is_file():
        data: DataFrame = read_csv(args.file, header=1, low_memory=False, memory_map=True, parse_dates=['date'],
                                   names=['symbol', 'display_name', 'date', 'cost', 'quantity', 'value', 'gain'],
                                   dtype={'quantity': uint16, 'cost': float32, 'value': float32, 'gain': float32,
                                          'symbol': 'category', 'display_name': 'category'})
        is_short: Series[bool] = data['date'] > (datetime.now() - timedelta(days=(365 - args.days)))
        is_long: Series[bool] = ~is_short
        symbols: list[str] = data['symbol'].unique().tolist()
        if args.live:
            data: DataFrame = live_update(data, symbols)
        if args.summary:
            summary(data, is_long, is_short)
        if args.symbol | (not args.summary):
            by_symbol(data, symbols, is_long, is_short, args.verbose)
    else:
        print(f'{args.file} is not a readable file.')
    return


def by_symbol(data: DataFrame, symbols: list[str], is_long: Series, is_short: Series, verbose: bool) -> None:
    symbols_name: list[str] = data['display_name'].unique().tolist()
    symbols_net: list[float] = []
    symbols_net_short: list[float] = []
    symbols_net_long: list[float] = []
    for iter_symbol in symbols:
        is_iter_symbol: Series[bool] = data['symbol'] == iter_symbol
        symbols_net.append(data.loc[is_iter_symbol, 'gain'].sum())
        symbols_net_long.append(data.loc[is_iter_symbol & is_long, 'gain'].sum(0))
        symbols_net_short.append(data.loc[is_iter_symbol & is_short, 'gain'].sum(0))
    symbols_range: range = range(len(symbols))
    print('Net gain/loss per symbol')
    symbols_net_print(symbols, symbols_name, symbols_net, symbols_range, verbose)
    print('Net short term gain/loss per symbol')
    symbols_net_print(symbols, symbols_name, symbols_net_short, symbols_range, verbose)
    print('Net long term gain/loss per symbol')
    symbols_net_print(symbols, symbols_name, symbols_net_long, symbols_range, verbose)
    return


def summary(data: DataFrame, is_long: Series, is_short: Series) -> None:
    is_loss: Series[bool] = data['gain'] < 0
    print(f"Total cost {format_dollar(data['cost'].sum())}")
    print(f"Total value {format_dollar(data['value'].sum())}")
    print(f"Short term total value {format_dollar(data.loc[is_short, 'value'].sum())}")
    print(f"Long term total value {format_dollar(data.loc[is_long, 'value'].sum())}")
    print(f"Net gain/loss {format_dollar(data['gain'].sum())}")
    print(f"Net short term gain/loss {format_dollar(data.loc[is_short, 'gain'].sum())}")
    print(f"Net long term gain/loss {format_dollar(data.loc[is_long, 'gain'].sum())}")
    print(f"Total short term losses "
          f"{format_dollar(total_short_losses := data.loc[is_short & is_loss, 'gain'].sum())}")
    if total_short_losses != 0:
        print(f"{','.join(data.loc[is_short & is_loss, 'symbol'].unique().tolist())}")
    print(f"Total long term losses "
          f"{format_dollar(total_long_losses := data.loc[is_long & is_loss, 'gain'].sum())}")
    if total_long_losses != 0:
        print(f"{','.join(data.loc[is_long & is_loss, 'symbol'].unique().tolist())}")
    return


def live_update(data: DataFrame, symbols: list[str]) -> DataFrame:
    with Pool() as p:
        data['price'] = data['symbol'].map(dict(p.imap_unordered(get_price, symbols, chunksize=2))).astype(float32)
    data['value'] = data['quantity'] * data['price']
    data['gain'] = data['value'] - data['cost']
    return data.drop(columns=['price'])


def parse_args() -> Namespace:
    parser: ArgumentParser = ArgumentParser(description="Analyze Wealthfront cost-basis data. Displays net short/long "
                                                        "term gains/losses & total short/long term losses by default.",
                                            epilog="File required")
    parser.add_argument('-s', '--symbol', action='store_true',
                        help='Display net gain/loss by symbol and net short/long-term gain/loss per symbol')
    parser.add_argument('-n', '--no-summary', help='No summary', action='store_false', dest='summary')
    parser.add_argument('-f', '--file', help='File to process', type=lambda p: Path(p).absolute(), required=True)
    parser.add_argument('-d', '--days', help='Show results for number of days in the future', type=int, default=0)
    parser.add_argument('-v', '--verbose', help='Display ETF descriptions', action='store_true')
    parser.add_argument('-l', '--live', help='Get live price from YF(experimental)', action='store_true')
    return parser.parse_args()


def symbols_net_print(symbols: list[str], names: list[str], nets: list[float], symbols_range: range,
                      verbose: bool) -> None:
    net_pairs: dict[str, tuple[str, float]] = {symbols[i]: (names[i], nets[i]) for i in symbols_range}
    if verbose:
        print("\n".join(f"{k:8s}{v[0]:42.42s}{format_dollar(v[1]):>21s}" for k, v in net_pairs.items()))
    else:
        print("\n".join(f"{k}\t{format_dollar(v[1])}" for k, v in net_pairs.items()))
    return


def format_dollar(amount: float) -> str:
    formatted_absolute_amount: str = f'${abs(amount):,.2f}'
    return f'-{formatted_absolute_amount}' if round(amount, 2) < 0 else formatted_absolute_amount


def get_price(symbol: str) -> tuple[str, float]:
    from yfinance import Ticker
    ticker: Ticker.fast_info = Ticker(symbol).fast_info
    return symbol, ticker['lastPrice']


if __name__ == '__main__':
    main()
