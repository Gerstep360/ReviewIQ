"""Smoke HTTP reproducible en loopback: proceso propio, modelo real y cierre final."""

import json
import math
import os
import platform
import re
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

import psutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ml.inference.probes import PROBE_TEXTS


def percentile(values, percent):
    values = sorted(values)
    position = (len(values) - 1) * percent / 100
    lower, upper = math.floor(position), math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def main():
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    opener = build_opener(ProxyHandler({}))
    environment = os.environ.copy()
    environment.update({name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')})
    # Puerto efímero, un proceso y sin autoreload; no deja un servidor en ejecución.
    command = [sys.executable, 'manage.py', 'runapi', f'127.0.0.1:{port}', '--noreload', '--nothreading']
    rss_samples = []

    def call(path, payload=None, expected=200):
        content = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
        request = Request(base + path, data=content, headers={'Content-Type': 'application/json'} if content is not None else {})
        try:
            response = opener.open(request, timeout=15)
        except HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            if response.status != expected:
                raise AssertionError(f'{path}: HTTP {response.status}, esperado {expected}')
            content_type = response.headers.get('Content-Type', '')
            if 'json' in content_type:
                return json.loads(body)
            return body.decode('utf-8') if content_type.startswith('text/') else body

    def sample_rss(process):
        candidates = [process, *process.children(recursive=True)]
        # El ejecutable del venv de Windows puede ser un launcher de otro Python.
        rss = max(candidate.memory_info().rss for candidate in candidates if candidate.is_running()) / 1024**2
        rss_samples.append(rss)
        return rss

    started = time.perf_counter()
    with tempfile.TemporaryFile() as log:
        server = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log, stderr=log)
        try:
            process = psutil.Process(server.pid)
            deadline = time.perf_counter() + 30
            while True:
                if server.poll() is not None or time.perf_counter() > deadline:
                    log.seek(0)
                    raise RuntimeError('No se pudo iniciar la API: ' + log.read().decode('utf-8', errors='replace')[-2000:])
                try:
                    health = call('/api/v1/health/')
                    break
                except URLError:
                    time.sleep(0.1)
            startup_sec = time.perf_counter() - started
            idle_rss = sample_rss(process)
            prediction = call('/api/v1/predict/', {'text': PROBE_TEXTS[1]})
            trace = call('/api/v1/nlp/trace/', {'text': PROBE_TEXTS[0]})
            metrics = call('/api/v1/metrics/')
            assert prediction['model_id'] == trace['model_id'] == metrics['model_id'] == health['model_id']
            assert set(prediction['probabilities']) == set('12345')
            assert math.isclose(sum(prediction['probabilities'].values()), 1, abs_tol=1e-5)
            assert len(metrics['metrics']['confusion_matrix']) == 5
            assert metrics['split'] == ('test' if health['mode'] == 'full' else 'validation')
            invalid = call('/api/v1/predict/', {'text': '   '}, expected=400)
            assert invalid['error']['code'] == 'invalid_input'
            schema = call('/api/schema/')
            assert '/api/v1/nlp/trace/' in schema['paths']
            docs = call('/docs/')
            assets = sorted(set(re.findall(r'(?:src|href)="(/static/[^"?]+)', docs)))
            assert assets, 'Swagger debe usar sus recursos locales.'
            for asset in assets:
                call(asset)
            for _ in range(3):
                call('/api/v1/predict/', {'text': PROBE_TEXTS[1]})
            durations, inference_times = [], []
            for text in PROBE_TEXTS * 3:
                started_request = time.perf_counter()
                result = call('/api/v1/predict/', {'text': text})
                durations.append((time.perf_counter() - started_request) * 1000)
                inference_times.append(result['inference_ms'])
                sample_rss(process)
            report = {
                'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                'scope': 'Actual loopback HTTP, Django runapi development server, one process and no request threading; no frontend or production load test.',
                'model_id': health['model_id'], 'mode': health['mode'],
                'health_status': 'ok', 'endpoints_checked': ['health', 'predict', 'metrics', 'nlp/trace', 'schema', 'docs'],
                'invalid_input_status': 400, 'swagger_local_assets_checked': len(assets),
                'metric_split': metrics['split'], 'metric_model_matches_predictor': True,
                'synthetic_example': {'text': PROBE_TEXTS[1], 'response': prediction},
                'test_evaluation_repeated': False, 'startup_until_ready_sec': startup_sec,
                'warmup_calls': 3, 'measured_calls': len(durations),
                'http_roundtrip': {'p50_ms': percentile(durations, 50), 'p95_ms': percentile(durations, 95)},
                'reported_inference': {'p50_ms': percentile(inference_times, 50), 'p95_ms': percentile(inference_times, 95)},
                'idle_ready_rss_mib': idle_rss, 'max_server_rss_mib_sampled_after_requests': max(rss_samples),
                'machine': {'os': platform.platform(), 'python': platform.python_version(), 'cpu': platform.processor(), 'logical_cpus': psutil.cpu_count(), 'ram_total_gib': psutil.virtual_memory().total / 1024**3},
                'limitations': 'Thirty synthetic single-review calls. RSS sampled at request boundaries, largest server process excluding launcher; not a continuous peak measurement. Startup includes imports and model warm-up. No database or migrations used.',
            }
        finally:
            children = process.children(recursive=True) if process.is_running() else []
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            # Windows puede mantener el Python hijo del launcher: cerrar solo este árbol.
            for child in children:
                if child.is_running():
                    child.terminate()
            _, alive = psutil.wait_procs(children, timeout=5)
            for child in alive:
                child.kill()
    (ROOT / 'reports/api_smoke.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'model_id': report['model_id'], 'endpoints': 'OK', 'http_roundtrip': report['http_roundtrip']}, indent=2))


if __name__ == '__main__':
    main()
