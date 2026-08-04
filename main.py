from config import WATCHLIST
from data_fetch import fetch_history
from report import print_report
from signals import calculate_signals


def main() -> None:
    results = []
    for ticker in WATCHLIST:
        try:
            df = fetch_history(ticker)
            signals = calculate_signals(df)
            results.append((ticker, signals, None))
        except Exception as e:
            results.append((ticker, None, e))

    print_report(results)


if __name__ == "__main__":
    main()
