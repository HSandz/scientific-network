#!/usr/bin/env bash
# Operator-only installation. CI cannot replace its VM activation scripts/policy.
set -euo pipefail
cd "$(dirname "$0")/../../.."
host=${1:-azure_scientific-network}
contract=$(python3 ops/azure/scripts/runtime-contract.py)
remote=$(ssh "$host" 'mktemp -d /tmp/azure-api-ci-install-XXXXXX')
trap 'ssh "$host" "rm -rf -- $remote"' EXIT
scp ops/azure/scripts/{activate-ci-image.py,rollback-ci-image.py,common.sh,update.sh,rollback.sh,verify.sh,smoke-api.py} "$host:$remote/" >/dev/null
ssh "$host" sudo -n python3 - "$remote" "$contract" <<'PY'
import fcntl,hashlib,json,pathlib,subprocess,sys
source=pathlib.Path(sys.argv[1])
ops=pathlib.Path('/opt/scientific-network/ops/azure')
with (ops/'.runtime.lock').open('w') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    env=dict(l.split('=',1) for l in (ops/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
    manifest=pathlib.Path(env['ARTIFACT_DIR'])/'manifest.json'
    approval={'runtime_contract':sys.argv[2],'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
    path=ops/'.ci-approval.json'
    if path.exists():
        assert json.loads(path.read_text())==approval, 'Approval differs: explicit coordinated operator review required'
    else:
        path.write_text(json.dumps(approval,indent=2)+'\n')
        path.chmod(0o600)
    for file in source.iterdir():
        target=ops/'scripts'/file.name
        assert not target.is_symlink()
        subprocess.run(['install','-o','root','-g','root','-m','0755',str(file),str(target)],check=True)
print('Installed root-owned activation scripts; protected compatibility approval pinned.')
PY
