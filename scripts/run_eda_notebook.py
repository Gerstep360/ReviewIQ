"""Ejecuta el notebook de EDA con el mismo Python que invoca este script."""

import json
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "notebooks" / "01_EDA.ipynb"


def main() -> None:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    # Kernel temporal: no registrar kernels globales ni depender de otro Python.
    with tempfile.TemporaryDirectory() as directory:
        kernel_dir = Path(directory) / "reviewiq"
        kernel_dir.mkdir()
        (kernel_dir / "kernel.json").write_text(json.dumps({
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "ReviewIQ", "language": "python",
        }), encoding="utf-8")
        manager = KernelManager(
            kernel_name="reviewiq",
            kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]),
        )
        try:
            NotebookClient(
                notebook, km=manager, timeout=180,
                resources={"metadata": {"path": str(ROOT)}},
            ).execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    nbformat.write(notebook, NOTEBOOK)
    print("Notebook ejecutado: notebooks/01_EDA.ipynb")


if __name__ == "__main__":
    main()
