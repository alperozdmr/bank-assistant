# logging_setup.py
import json, logging, os, sys
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_JSON = os.getenv("LOG_JSON", "1") in ("1", "true", "True")
os.makedirs(LOG_DIR, exist_ok=True)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "event": getattr(record, "event", record.msg if isinstance(record.msg, str) else "log"),
            "corr_id": getattr(record, "corr_id", None),
            "user_id": getattr(record, "user_id", None),
            "model": getattr(record, "model", None),
            "tool": getattr(record, "tool", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "ok": getattr(record, "ok", None),
            "error": getattr(record, "error", None),
            "meta": getattr(record, "meta", None),
        }
        # msg string ise ek meta olarak koy
        if isinstance(record.msg, str):
            payload.setdefault("message", record.msg)
        # extra dict geldiyse birleştir
        if isinstance(record.args, dict):
            payload.update(record.args)
        return json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False)

def get_logger(name: str, filename: str, service: str):
    logger = logging.getLogger(name)
    if logger.handlers:  # tekrar kurma
        return logger
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    fmt = JSONFormatter() if LOG_JSON else logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = RotatingFileHandler(os.path.join(LOG_DIR, filename), maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    # varsayılan extra
    logger = logging.LoggerAdapter(logger, extra={"service": service})
    return logger
