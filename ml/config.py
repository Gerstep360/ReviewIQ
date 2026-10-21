"""Configuración versionada, independiente de Django y de los notebooks."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "ml" / "data" / "raw"
PROCESSED_DIR = ROOT / "ml" / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class DatasetFile:
    name: str
    rows: int
    bytes: int
    sha256: str


@dataclass(frozen=True)
class ProjectConfig:
    seed: int
    n_jobs: int
    repository: str
    revision: str
    files: dict[str, DatasetFile]


def load_config(path: Path = ROOT / "config.json") -> ProjectConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    dataset = data["dataset"]
    if type(data["seed"]) is not int or data["seed"] < 0:
        raise ValueError("La semilla debe ser un entero no negativo.")
    if data["runtime"]["n_jobs"] != 1:
        raise ValueError("El presupuesto inicial de CPU requiere n_jobs=1.")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", dataset["repository"]):
        raise ValueError("Repositorio de Hugging Face inválido.")
    if not re.fullmatch(r"[0-9a-f]{40}", dataset["revision"]):
        raise ValueError("La revisión debe ser un SHA completo, no main.")
    if set(dataset["files"]) != set(SPLITS):
        raise ValueError("Se requieren las tres particiones originales.")
    files = {}
    for split in SPLITS:
        spec = DatasetFile(**dataset["files"][split])
        if spec.name != f"{split}.jsonl":
            raise ValueError("Nombre de archivo no permitido.")
        if spec.rows <= 0 or spec.bytes <= 0 or not re.fullmatch(r"[0-9a-f]{64}", spec.sha256):
            raise ValueError("Tamaño, filas o SHA-256 inválidos.")
        files[split] = spec
    return ProjectConfig(data["seed"], 1, dataset["repository"], dataset["revision"], files)
