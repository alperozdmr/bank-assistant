#!/usr/bin/env python3
import os
import sys
import signal
import shutil
import threading
import subprocess
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent

# Olası klasör isimleri
BACKEND = ROOT / "backend"
FRONTEND_CANDIDATES = [ROOT / "frontend", ROOT / "fronted"]  # fronted yazımı da destekle

def ensure_dir(p: Path, name: str):
    if not p.exists():
        raise SystemExit(f"[HATA] {name} dizini bulunamadı: {p}")
    if not p.is_dir():
        raise SystemExit(f"[HATA] {name} bir dizin değil: {p}")

def find_frontend_dir() -> Path:
    for p in FRONTEND_CANDIDATES:
        if p.exists() and p.is_dir():
            return p
    raise SystemExit("[HATA] frontend/fronted dizini bulunamadı. 'frontend' veya 'fronted' oluşturun.")

def detect_backend_python() -> str:
    """
    backend/.venv varsa onu kullan; yoksa mevcut interpreter'ı (sys.executable) kullan.
    """
    # Unix
    py_unix = BACKEND / ".venv" / "bin" / "python"
    # Windows
    py_win = BACKEND / ".venv" / "Scripts" / "python.exe"
    if py_unix.exists():
        return str(py_unix)
    if py_win.exists():
        return str(py_win)
    return sys.executable

def which_or_module(cmd: str, module: str) -> List[str]:
    """
    'uvicorn' gibi bir komutu bul; yoksa 'python -m uvicorn' kullan.
    """
    if shutil.which(cmd):
        return [cmd]
    return [detect_backend_python(), "-m", module]

def npm_command() -> str:
    if os.name == "nt":
        return "npm.cmd" if shutil.which("npm.cmd") else "npm"
    return "npm"

def pipe_output(proc: subprocess.Popen, tag: str):
    try:
        with proc.stdout:
            for line in iter(proc.stdout.readline, b""):
                try:
                    text = line.decode(errors="replace")
                except Exception:
                    text = str(line)
                print(f"[{tag}] {text}", end="")
    except Exception as e:
        print(f"[{tag}] Çıkış akışı kapandı: {e}")

def spawn(name: str, cmd: List[str], cwd: Path) -> Tuple[subprocess.Popen, threading.Thread]:
    env = os.environ.copy()
    # Windows'ta UTF-8 konsol
    if os.name == "nt":
        env.setdefault("PYTHONUTF8", "1")
    print(f"[INFO] {name} başlıyor: {' '.join(cmd)}  (cwd={cwd})")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    t = threading.Thread(target=pipe_output, args=(proc, name), daemon=True)
    t.start()
    return proc, t

def terminate(proc: subprocess.Popen, name: str):
    if proc.poll() is not None:
        return
    print(f"\n[INFO] {name} kapatılıyor...")
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGINT)
    except Exception:
        pass

def kill(proc: subprocess.Popen, name: str):
    if proc.poll() is not None:
        return
    print(f"[WARN] {name} zorla sonlandırılıyor...")
    try:
        proc.kill()
    except Exception:
        pass

def main():
    ensure_dir(BACKEND, "backend")
    FRONTEND = find_frontend_dir()

    backend_python = detect_backend_python()

    # 1) MCP server
    mcp_cmd = [backend_python, "-m", "mcp_server.server"]

    # 2) Uvicorn (komut veya python -m)
    uvicorn_base = which_or_module("uvicorn", "uvicorn")
    uvicorn_cmd = uvicorn_base + ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

    # 3) Frontend npm dev
    npm = npm_command()
    if not shutil.which(npm):
        raise SystemExit("[HATA] 'npm' bulunamadı. Node.js / npm kurulu mu ve PATH'e eklendi mi?")
    npm_cmd = [npm, "run", "dev"]

    procs = []
    threads = []

    try:
        p1, t1 = spawn("MCP", mcp_cmd, BACKEND)
        p2, t2 = spawn("API", uvicorn_cmd, BACKEND)
        p3, t3 = spawn("WEB", npm_cmd, FRONTEND)

        procs.extend([("MCP", p1), ("API", p2), ("WEB", p3)])
        threads.extend([t1, t2, t3])

        # Çalışır halde bekle
        while True:
            exited = [(name, p.poll()) for name, p in procs if p.poll() is not None]
            if exited:
                # Birisi beklenmedik şekilde kapandıysa diğerlerini kapat
                for name, code in exited:
                    print(f"\n[ERROR] {name} süreç sonlandı (exit={code}). Diğer süreçler kapatılıyor...")
                break
            threading.Event().wait(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] CTRL+C alındı, kapatılıyor...")
    finally:
        # Önce nazikçe sonlandır
        for name, p in procs:
            terminate(p, name)
        # Biraz bekle
        for _ in range(20):
            if all(p.poll() is not None for _, p in procs):
                break
            threading.Event().wait(0.1)
        # Canlı kalanları öldür
        for name, p in procs:
            if p.poll() is None:
                kill(p, name)

        # Çıktı thread'lerini kapat
        for t in threads:
            try:
                t.join(timeout=0.5)
            except Exception:
                pass

        # Çıkış kodu: herhangi biri başarısızsa 1
        exit_codes = [p.poll() for _, p in procs]
        if any(code not in (0, None) for code in exit_codes):
            sys.exit(1)

if __name__ == "__main__":
    main()
