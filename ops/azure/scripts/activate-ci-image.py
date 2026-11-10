#!/usr/bin/env python3
"""Root-owned VM entrypoint. Accept an image, never code/scripts or scientific data.

Installed by an operator, not replaced by CI. Azure Run Command is the privileged
transport. No GitHub token or SSH key is stored on the VM.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile

OPS = Path('/opt/scientific-network/ops/azure')
STATE = OPS / '.ci-deployment.json'
APPROVAL = OPS / '.ci-approval.json'


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def portable_id(image, sha):
    return run('python3', str(OPS / 'scripts/image-identity.py'), '--docker-image', image, '--sha', sha)


def env_values():
    return dict(line.split('=', 1) for line in (OPS / '.env').read_text().splitlines()
                if '=' in line and not line.startswith('#'))


def stable_services():
    result = {}
    for name in ('neo4j', 'caddy'):
        d = json.loads(run('docker', 'inspect', f'scientific-network-production-{name}-1'))[0]
        assert d['State']['Health']['Status'] == 'healthy', f'{name} unhealthy'
        assert not d['State']['OOMKilled'], f'{name} OOM'
        result[name] = {k: d[k] for k in ('Id', 'Image', 'Mounts', 'RestartCount')}
        result[name]['StartedAt'] = d['State']['StartedAt']
    return result


def activate(args):
    assert re.fullmatch('[0-9a-f]{40}', args.sha)
    assert re.fullmatch('[0-9a-f]{64}', args.checksum)
    assert re.fullmatch('sha256:[0-9a-f]{64}', args.image_id)
    assert args.sequence > 0
    url = urllib.parse.urlsplit(args.url)
    # GitHub's short-lived private artifact storage URL; no arbitrary URL/file.
    assert url.scheme == 'https' and url.hostname and (
        url.hostname.endswith('.blob.core.windows.net') or
        url.hostname.endswith('.actions.githubusercontent.com')
    ) and not url.username
    approval = json.loads(APPROVAL.read_text())
    current = env_values()
    artifacts = Path(current['ARTIFACT_DIR'])
    assert hashlib.sha256((artifacts / 'manifest.json').read_bytes()).hexdigest() == approval['manifest_sha256']
    previous = json.loads(STATE.read_text()) if STATE.exists() else {}
    assert args.sequence >= previous.get('sequence', 0), 'Stale deployment rejected'
    if args.sequence == previous.get('sequence'):
        assert args.sha == previous.get('sha'), 'Conflicting sequence rejected'
    image = 'scientific-network-api:sha-' + args.sha
    before = stable_services()
    assert os.statvfs(OPS).f_bavail * os.statvfs(OPS).f_frsize > 8 * 1024**3, 'Need 8 GiB free'
    if previous.get('sha') == args.sha:
        api = json.loads(run('docker', 'inspect', 'scientific-network-production-api-1'))[0]
        if (current['API_IMAGE'] == image and api['Image'] == json.loads(run('docker', 'image', 'inspect', image))[0]['Id']
                and portable_id(image, args.sha) == previous.get('image_id')):
            subprocess.run([str(OPS / 'scripts/verify.sh')], cwd=OPS, check=True)
            assert before == stable_services()
            previous['operation'] = 'noop'
            # An operator may coordinate a new immutable artifact directory with
            # this same image. Record the verified active inputs, not stale pins.
            previous['artifact_dir'] = str(artifacts)
            previous['preserved_services'] = before
            previous['sequence'] = args.sequence
            previous['verified_at'] = datetime.now(timezone.utc).isoformat()
            STATE.write_text(json.dumps(previous, indent=2) + '\n')
            print('Verified idempotent no-op: existing immutable image retained; redundant build discarded')
            print(json.dumps(previous))
            return
    with tempfile.TemporaryDirectory(prefix='api-delivery-', dir=OPS) as temp:
        package = Path(temp) / 'delivery.zip'
        # Never log the signed bearer URL. Bound transfer time and disk use.
        with urllib.request.urlopen(args.url, timeout=60) as response, package.open('wb') as f:
            size = 0
            while block := response.read(1024 * 1024):
                size += len(block)
                assert size <= 512 * 1024**2, 'Package too large'
                f.write(block)
        with zipfile.ZipFile(package) as z:
            assert z.namelist() == ['image.tar.gz'], 'Unexpected artifact contents'
            member = z.getinfo('image.tar.gz')
            assert member.file_size <= 512 * 1024**2
            h = hashlib.sha256()
            tar = Path(temp) / 'image.tar.gz'
            with z.open(member) as source, tar.open('wb') as target:
                while block := source.read(1024 * 1024):
                    h.update(block)
                    target.write(block)
            assert h.hexdigest() == args.checksum, 'Image package checksum mismatch'
        # Refuse rebinding an existing commit tag to a different image.
        existing = subprocess.run(['docker', 'image', 'inspect', image], capture_output=True, text=True)
        if existing.returncode == 0:
            assert portable_id(image, args.sha) == args.image_id, 'Immutable tag conflict'
        subprocess.run(['docker', 'load', '-i', str(tar)], check=True, timeout=180)
    d = json.loads(run('docker', 'image', 'inspect', image))[0]
    assert portable_id(image, args.sha) == args.image_id and d['Architecture'] == 'amd64'
    labels = d['Config']['Labels']
    assert labels['org.opencontainers.image.revision'] == args.sha
    assert labels['org.scientific-network.runtime-contract'] == approval['runtime_contract'], 'Artifact contract changed: coordinated release required'
    try:
        updated = subprocess.run([str(OPS / 'scripts/update.sh'), image, str(artifacts)], cwd=OPS, capture_output=True, text=True)
        print(updated.stdout, flush=True)
        print(updated.stderr, flush=True)
        updated.check_returncode()
    finally:
        assert before == stable_services(), 'CRITICAL: database/proxy identity or mounts changed'
    assert env_values()['ARTIFACT_DIR'] == str(artifacts)
    active = json.loads(run('docker', 'inspect', 'scientific-network-production-api-1'))[0]
    assert active['Image'] == d['Id'] and active['State']['Health']['Status'] == 'healthy'
    assert not active['State']['OOMKilled'] and active['RestartCount'] == 0
    snapshot = next(line.split(': ', 1)[1] for line in updated.stdout.splitlines() if line.startswith('Deployment verified; rollback snapshot: '))
    prior = OPS / '.ci-rollback-state.json'
    prior.write_text(json.dumps(previous) + '\n')
    prior.chmod(0o600)
    receipt = dict(operation='activated', rollback_snapshot=snapshot, sha=args.sha, image=image, image_id=args.image_id, image_store_id=d['Id'], sequence=args.sequence,
                   artifact_dir=str(artifacts), verified_at=datetime.now(timezone.utc).isoformat(),
                   preserved_services=before)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(receipt, indent=2) + '\n')
    tmp.chmod(0o600)
    tmp.replace(STATE)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--sequence', required=True, type=int)
    parser.add_argument('--checksum', required=True)
    parser.add_argument('--image-id', required=True)
    parser.add_argument('--url', required=True)
    args = parser.parse_args()
    # Separate delivery lock serializes download/load as well as activation.
    import fcntl
    with (OPS / '.ci-delivery.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate(args)
        print("AZURE_API_DEPLOYMENT_VERIFIED", flush=True)
