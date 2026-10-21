"""Copia limpia de los archivos versionables, entorno nuevo y reproducción full."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    destination = Path(tempfile.mkdtemp(prefix="repro-", dir=ROOT / "ml" / "artifacts"))
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    for name in names:
        if not name:
            continue
        relative = Path(name)
        source, target = ROOT / relative, destination / relative
        if not source.resolve().is_relative_to(ROOT) or not target.resolve().is_relative_to(destination):
            raise ValueError("Ruta fuera de la copia aislada.")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for forbidden in (destination / "ml" / "data" / "raw", destination / "ml" / "data" / "processed", destination / "ml" / "artifacts" / "reviewiq_pipeline.joblib", destination / "venv"):
        if forbidden.exists():
            raise ValueError("La copia contiene datos, checkpoint o entorno previo.")
    print("Copia aislada creada sin corpus, artefactos ni entorno previo.", flush=True)
    environment = os.environ.copy()
    environment.update({name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    environment["PYTHONHASHSEED"] = "42"
    subprocess.run([sys.executable, "-m", "venv", str(destination / ".venv")], check=True, env=environment)
    python = destination / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements.txt"], cwd=destination, env=environment, check=True)
    subprocess.run([str(python), "-m", "pip", "check"], cwd=destination, env=environment, check=True)
    subprocess.run([str(python), "-m", "ml.training.train", "--mode", "full", "--seed", "42"], cwd=destination, env=environment, check=True)
    manifest = json.loads((destination / "ml/artifacts/full/manifest.json").read_text(encoding="utf-8"))
    build = json.loads((destination / "ml/artifacts/full/build_report.json").read_text(encoding="utf-8"))
    performance = json.loads((destination / "ml/artifacts/full/performance.json").read_text(encoding="utf-8"))
    evidence = {
        "scope": "Fresh copy of Git-listed files (including current phase changes), fresh venv, pinned install, no prior corpus or artifact. Not an HTTP/frontend check.",
        "model_id": manifest["model_id"], "model_state_sha256": manifest["model_state_sha256"],
        "historical_test": manifest["historical_test"], "build": build, "performance": performance,
        "workspace_relative_copy": destination.relative_to(ROOT).as_posix(),
    }
    # Los resultados históricos deben conservarse byte por byte en la copia.
    for name in ("model_selection.json", "test_metrics.json", "final_test_ledger.json"):
        if (ROOT / "reports" / name).read_bytes() != (destination / "reports" / name).read_bytes():
            raise ValueError("Se modificó un resultado histórico durante reproducción.")
    (ROOT / "reports" / "reproducibility.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Reproducción limpia verificada; reports/reproducibility.json", flush=True)


if __name__ == "__main__":
    main()
