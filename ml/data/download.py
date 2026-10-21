"""Descarga JSONL fijado a un commit y verifica tamaño y SHA-256."""

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from ml.config import RAW_DIR, REPORTS_DIR, DatasetFile, ProjectConfig, load_config

LICENSE_URL = "https://github.com/awslabs/open-data-docs/blob/main/docs/amazon-reviews-ml/README.md#license"


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_file(path: Path, spec: DatasetFile) -> str:
    if path.stat().st_size != spec.bytes:
        raise ValueError(f"Tamaño inesperado: {path.name}.")
    digest = sha256_file(path)
    if digest != spec.sha256:
        raise ValueError(f"SHA-256 inesperado: {path.name}; no se usará este archivo.")
    return digest


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def download_file(url: str, target: Path, spec: DatasetFile) -> None:
    """Un fallo no reemplaza un archivo anterior ni deja un JSONL incompleto."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".part", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        request = Request(url, headers={"User-Agent": "ReviewIQ/0.1 academic-project"})
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            size = 0
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > spec.bytes:
                    raise ValueError(f"Descarga mayor al tamaño fijado: {target.name}.")
                output.write(block)
        verify_file(temporary, spec)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def download_dataset(
    raw_dir: Path = RAW_DIR,
    reports_dir: Path = REPORTS_DIR,
    *,
    force: bool = False,
    config: ProjectConfig | None = None,
) -> dict:
    config = config or load_config()
    files = {}
    for split, spec in config.files.items():
        url = f"https://huggingface.co/datasets/{config.repository}/resolve/{config.revision}/{spec.name}"
        target = raw_dir / spec.name
        if force or not target.exists():
            download_file(url, target, spec)
        digest = verify_file(target, spec)
        files[split] = {
            "file": spec.name,
            "url": url,
            "bytes": target.stat().st_size,
            "sha256": digest,
            "local_file_mtime_utc": datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat(),
        }
    manifest = {
        "repository": config.repository,
        "revision": config.revision,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "license_url": LICENSE_URL,
        "usage": "academic research only; do not redistribute corpus or reidentify authors",
        "reader": "Python standard library JSONL; no remote dataset scripts executed",
        "files": files,
    }
    write_json(reports_dir / "dataset_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--force", action="store_true", help="Volver a descargar y verificar.")
    args = parser.parse_args()
    manifest = download_dataset(args.raw_dir, force=args.force)
    print(json.dumps({"revision": manifest["revision"], "verified_files": list(manifest["files"])}, indent=2))


if __name__ == "__main__":
    main()
