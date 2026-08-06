COLUMNS = [
    ("Ticker", 8),
    ("Price", 10),
    ("Vol Ratio", 10),
    ("Vol Flag", 9),
    ("Move", 9),
    ("ATR", 8),
    ("Move/ATR", 9),
    ("ATR Flag", 9),
    ("IV", 8),
    ("HV", 8),
    ("IV/HV", 8),
    ("IV Flag", 8),
]


def _header() -> str:
    return "  ".join(name.ljust(width) for name, width in COLUMNS)


def _separator() -> str:
    return "  ".join("-" * width for _, width in COLUMNS)


def _iv_hv_cells(record: dict) -> list[str]:
    iv_hv = record["iv_hv"]
    if iv_hv is not None:
        return [
            f"{iv_hv['iv']:.1%}",
            f"{iv_hv['hv']:.1%}",
            f"{iv_hv['iv_hv_ratio']:.2f}x",
            "FLAG" if iv_hv["iv_hv_flagged"] else "",
        ]
    if record["iv_hv_error"] is not None:
        return ["—", "—", "—", "ERR"]
    return ["", "", "", ""]


def _format_row(record: dict) -> str:
    signals = record["signals"]
    values = [
        record["ticker"],
        f"{signals['close']:.2f}",
        f"{signals['volume_ratio']:.2f}x",
        "FLAG" if signals["volume_flagged"] else "",
        f"{signals['move']:+.2f}",
        f"{signals['atr']:.2f}",
        f"{signals['move_in_atr_units']:+.2f}x",
        "FLAG" if signals["atr_flagged"] else "",
        *_iv_hv_cells(record),
    ]
    return "  ".join(str(v).ljust(width) for v, (_, width) in zip(values, COLUMNS))


def _format_error_row(record: dict) -> str:
    return f"{record['ticker'].ljust(8)}  ERROR: {record['error']}"


def print_report(results: list[dict]) -> None:
    print(_header())
    print(_separator())

    iv_hv_errors = []
    catalysts = []
    for record in results:
        if record["error"] is not None:
            print(_format_error_row(record))
        else:
            print(_format_row(record))

        if record["iv_hv_error"] is not None:
            iv_hv_errors.append(record)
        if record["catalyst_status"] in ("found", "unclear", "error"):
            catalysts.append(record)

    if iv_hv_errors:
        print()
        print("IV/HV data unavailable:")
        for record in iv_hv_errors:
            print(f"  {record['ticker']}: {record['iv_hv_error']}")

    if catalysts:
        print()
        print("Possible catalysts (flagged tickers):")
        for record in catalysts:
            if record["catalyst_status"] == "found":
                c = record["catalyst"]
                print(f"  {record['ticker']}: {c['headline']} ({c['source']}) — {c['url']}")
            elif record["catalyst_status"] == "unclear":
                print(f"  {record['ticker']}: No clear catalyst identified")
            else:
                print(f"  {record['ticker']}: catalyst lookup failed — {record['catalyst_error']}")
