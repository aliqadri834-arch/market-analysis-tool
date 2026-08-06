import json
from datetime import datetime, timezone
from pathlib import Path


def _signals_fields(record: dict) -> dict:
    signals = record["signals"]
    error = record["error"]

    if error is not None:
        return {
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
        "price": round(float(signals["close"]), 2),
        "volume_ratio": round(float(signals["volume_ratio"]), 3),
        "volume_flagged": bool(signals["volume_flagged"]),
        "move": round(float(signals["move"]), 2),
        "atr": round(float(signals["atr"]), 2),
        "move_atr_ratio": round(float(signals["move_in_atr_units"]), 3),
        "atr_flagged": bool(signals["atr_flagged"]),
        "error": None,
    }


def _iv_hv_fields(record: dict) -> dict:
    iv_hv = record["iv_hv"]
    iv_hv_error = record["iv_hv_error"]

    if iv_hv is not None:
        return {
            "iv": round(float(iv_hv["iv"]), 4),
            "hv": round(float(iv_hv["hv"]), 4),
            "iv_hv_ratio": round(float(iv_hv["iv_hv_ratio"]), 3),
            "iv_hv_flagged": bool(iv_hv["iv_hv_flagged"]),
            "iv_hv_expiry": iv_hv["expiry"],
            "iv_hv_error": None,
        }

    return {
        "iv": None,
        "hv": None,
        "iv_hv_ratio": None,
        "iv_hv_flagged": None,
        "iv_hv_expiry": None,
        "iv_hv_error": str(iv_hv_error) if iv_hv_error is not None else None,
    }


def _catalyst_fields(record: dict) -> dict:
    return {
        "catalyst_status": record["catalyst_status"],
        "catalyst": record["catalyst"],
        "catalyst_error": record["catalyst_error"],
    }


def _record_to_dict(record: dict) -> dict:
    return {
        "ticker": record["ticker"],
        **_signals_fields(record),
        **_iv_hv_fields(record),
        **_catalyst_fields(record),
    }


def write_json(results: list[dict], path: str) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "signals": [_record_to_dict(record) for record in results],
    }

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
