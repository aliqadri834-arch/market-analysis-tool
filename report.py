COLUMNS = [
    ("Ticker", 8),
    ("Price", 10),
    ("Vol Ratio", 10),
    ("Vol Flag", 9),
    ("Move", 9),
    ("ATR", 8),
    ("Move/ATR", 9),
    ("ATR Flag", 9),
]


def _header() -> str:
    return "  ".join(name.ljust(width) for name, width in COLUMNS)


def _separator() -> str:
    return "  ".join("-" * width for _, width in COLUMNS)


def _format_row(ticker: str, signals: dict) -> str:
    values = [
        ticker,
        f"{signals['close']:.2f}",
        f"{signals['volume_ratio']:.2f}x",
        "FLAG" if signals["volume_flagged"] else "",
        f"{signals['move']:+.2f}",
        f"{signals['atr']:.2f}",
        f"{signals['move_in_atr_units']:+.2f}x",
        "FLAG" if signals["atr_flagged"] else "",
    ]
    return "  ".join(str(v).ljust(width) for v, (_, width) in zip(values, COLUMNS))


def _format_error_row(ticker: str, error: Exception) -> str:
    return f"{ticker.ljust(8)}  ERROR: {error}"


def print_report(results: list[tuple[str, dict, Exception | None]]) -> None:
    print(_header())
    print(_separator())
    for ticker, signals, error in results:
        if error is not None:
            print(_format_error_row(ticker, error))
        else:
            print(_format_row(ticker, signals))
