#!/usr/bin/env python3
import argparse, subprocess, pathlib, sys, os

# --- colores ---
GREEN  = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; RESET = "\033[0m"

# --- localizar raíz del repo (sube hasta encontrar program/Compiscript.g4) ---
def find_repo_root(start: pathlib.Path) -> pathlib.Path:
    p = start.resolve()
    for d in [p] + list(p.parents):
        if (d / "program" / "Compiscript.g4").exists():
            return d
    return start

ROOT = find_repo_root(pathlib.Path(__file__).parent)
TESTS_DIR = ROOT / "tests"

def activate_venv():
    """Activa venv si hay .venv/ o venv/ en la raíz."""
    for name in (".venv", "venv"):
        v = ROOT / name
        if (v / "bin" / "activate").exists():  # Linux/macOS
            os.environ["VIRTUAL_ENV"] = str(v)
            os.environ["PATH"] = f"{v}/bin:{os.environ['PATH']}"
            return
        if (v / "Scripts" / "activate.bat").exists():  # Windows
            os.environ["VIRTUAL_ENV"] = str(v)
            os.environ["PATH"] = f"{v}/Scripts;{os.environ['PATH']}"
            return

def run_case(path, expect_fail, show_invalid=False):
    proc = subprocess.run(
        [sys.executable, "-m", "program.Driver", str(path)],
        capture_output=True, text=True, cwd=ROOT
    )
    has_err = proc.returncode != 0
    ok = (has_err == expect_fail)
    mark = GREEN + "✅" if ok else RED + "❌"
    print(f"{mark} {path.relative_to(TESTS_DIR)} {RESET}")

    # mostrar errores si falló cuando no debía, o si pedimos ver invalid
    if not ok or (show_invalid and expect_fail):
        out = (proc.stdout + "\n" + proc.stderr).strip()
        if out:
            print(YELLOW + out + RESET)
    return ok

def main():
    activate_venv()
    ap = argparse.ArgumentParser(description="Suite de tests Compiscript")
    ap.add_argument("--only", choices=["valid", "invalid"],
                    help="Ejecutar solo una carpeta")
    ap.add_argument("--show-invalid", action="store_true",
                    help="Imprimir errores también para los casos invalid que fallan como se espera")
    args = ap.parse_args()

    groups = [("valid", False), ("invalid", True)]
    if args.only:
        groups = [(args.only, args.only == "invalid")]

    all_ok = True  # <-- inicializar

    for folder, must_fail in groups:
        print(f"\n📂 {folder.upper()}")
        for path in sorted((TESTS_DIR / folder).rglob("*.cps")):
            all_ok &= run_case(path, must_fail, show_invalid=args.show_invalid)

    print((GREEN if all_ok else RED) +
          ("\n🏁 Todos los tests pasan\n" if all_ok else "\n💥 Algunos tests fallaron\n") +
          RESET)
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()

