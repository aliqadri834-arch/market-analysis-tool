import json
from datetime import datetime, timezone
from pathlib import Path


def _signal_to_dict(ticker: str, signals: dict | None, error: Exception | None) -> dict:
    if error is not None:
        return {
            "ticker": ticker,
            "price": None,
            "volume_ratio": None,
            "volume_flagged": None,
            "move": None,
            "atr": None,
            "move_atr_ratio": None,
            "atr_flagged": None,
            "error": str(error),
        }

    return {
        "ticker": ticker,
        "price": round(float(signals["close"]), 2),
        "volume_ratio": round(float(signals["volume_ratio"]), 3),
        "volume_flagged": bool(signals["volume_flagged"]),
        "move": round(float(signals["move"]), 2),
        "atr": round(float(signals["atr"]), 2),
        "move_atr_ratio": round(float(signals["move_in_atr_units"]), 3),
        "atr_flagged": bool(signals["atr_flagged"]),
        "error": None,
    }


def write_json(results: list[tuple[str, dict | None, Exception | None]], path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "signals": [_signal_to_dict(ticker, signals, error) for ticker, signals, error in results],
    }

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
