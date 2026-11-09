"""Check checked-in artifacts against their successful run manifest."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def verify():
    manifest = json.loads((ROOT/'outputs/run_manifest.json').read_text())
    failures = []
    for name, expected in manifest['artifact_sha256'].items():
        path = ROOT/'outputs'/name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name)
    for name, expected in manifest['code_sha256'].items():
        path = ROOT/name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(name)
    if failures:
        raise ValueError(f'Artifacts/code differ from successful run: {failures}. Rebuild the pipeline.')
    checks = json.loads((ROOT/'outputs/quality_report.json').read_text())
    if not checks or any(c['status'] == 'FAIL' for c in checks):
        raise ValueError('Quality checks did not pass')
    print(f"Verified {len(manifest['artifact_sha256'])} artifacts and {len(manifest['code_sha256'])} code files; all blocking quality gates pass (review warnings separately).")


if __name__ == '__main__':
    verify()
