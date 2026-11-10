#!/usr/bin/env python3
"""Roll back only the just-activated CI transaction after hosted public smoke fails."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess

OPS = Path('/opt/scientific-network/ops/azure')


def rollback(sha, sequence):
    with (OPS / '.ci-delivery.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = OPS / '.ci-deployment.json'
        state = json.loads(path.read_text())
        assert state['sha'] == sha and state['sequence'] == sequence, 'Refuse rollback of a superseding release'
        if state['operation'] == 'activated':
            subprocess.run([str(OPS / 'scripts/rollback.sh'), state['rollback_snapshot']], cwd=OPS, check=True)
            previous = json.loads((OPS / '.ci-rollback-state.json').read_text())
            previous.update(sequence=sequence, operation='rolled_back')
            path.write_text(json.dumps(previous, indent=2) + '\n')
            print('Hosted smoke failed: previous configuration restored and verified')
        else:
            print('No activation occurred; verified existing image retained')
        print('AZURE_API_ROLLBACK_VERIFIED', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--sequence', required=True, type=int)
    args = parser.parse_args()
    rollback(args.sha, args.sequence)
