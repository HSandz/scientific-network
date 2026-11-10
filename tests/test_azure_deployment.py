"""Fault injection against the real shell transaction, without production access."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def deployment(tmp_path):
    ops = tmp_path / 'ops'
    scripts = ops / 'scripts'
    scripts.mkdir(parents=True)
    for name in ('common.sh', 'update.sh', 'rollback.sh'):
        shutil.copy2(ROOT / 'ops/azure/scripts' / name, scripts / name)
    artifacts = tmp_path / 'artifacts'
    artifacts.mkdir()
    (artifacts / 'manifest.json').write_text('{}')
    original = f'API_IMAGE=scientific-network-api:old\nARTIFACT_DIR={artifacts}\nNEO4J_PASSWORD=fixture-only\nNEO4J_DATA_VOLUME=preserved-volume\n'
    (ops / '.env').write_text(original)
    (ops / '.env').chmod(0o600)
    executable = tmp_path / 'docker'
    executable.write_text('''#!/usr/bin/env python3
import os,sys
from pathlib import Path
ops=Path(os.environ['TEST_OPS'])
with (ops/'commands').open('a') as f: f.write(' '.join(sys.argv[1:])+'\\n')
if 'up' in sys.argv:
 assert '--no-deps' in sys.argv and '--pull' in sys.argv and sys.argv[-1]=='api'
 text=(ops/'.env').read_text()
 if os.environ.get('FAIL_START')=='1' and 'api:new' in text: sys.exit(1)
''')
    executable.chmod(0o755)
    verifier = scripts / 'verify.sh'
    verifier.write_text('''#!/usr/bin/env bash
set -euo pipefail
cat .env >> verified-envs
if [[ ${FAIL_ROLLBACK:-0} == 1 ]]; then exit 1; fi
if [[ ${FAIL_VERIFY:-0} == 1 ]] && grep -q 'api:new' .env; then exit 1; fi
''')
    verifier.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path)+os.pathsep+os.environ['PATH'], TEST_OPS=str(ops))
    return ops, artifacts, original, env


@pytest.mark.parametrize('fault', ['FAIL_START', 'FAIL_VERIFY'])
def test_failed_update_restores_exact_config_and_verifies_without_nested_lock(deployment, fault):
    ops, artifacts, original, env = deployment
    result = subprocess.run(['bash', str(ops/'scripts/update.sh'), 'scientific-network-api:new', str(artifacts)],
                            env=dict(env, **{fault: '1'}), capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert (ops/'.env').read_text() == original
    assert (ops/'.env').stat().st_mode & 0o777 == 0o600
    assert original in (ops/'verified-envs').read_text()
    assert 'Previous API restored and verified' in result.stderr
    assert 'neo4j' not in (ops/'commands').read_text()
    assert 'caddy' not in (ops/'commands').read_text()
    assert 'down' not in (ops/'commands').read_text()
    assert len(list(ops.glob('.env.rollback-*'))) == 1


def test_rollback_failure_is_critical(deployment):
    ops, artifacts, original, env = deployment
    result = subprocess.run(['bash', str(ops/'scripts/update.sh'), 'scientific-network-api:new', str(artifacts)],
                            env=dict(env, FAIL_VERIFY='1', FAIL_ROLLBACK='1'), capture_output=True, text=True, timeout=10)
    assert result.returncode == 70
    assert 'CRITICAL' in result.stderr
    assert (ops/'.env').read_text() == original


def test_success_and_manual_rollback_touch_only_api(deployment):
    ops, artifacts, original, env = deployment
    result = subprocess.run(['bash', str(ops/'scripts/update.sh'), 'scientific-network-api:new', str(artifacts)],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert 'API_IMAGE=scientific-network-api:new' in (ops/'.env').read_text()
    snapshot = next(ops.glob('.env.rollback-*'))
    result = subprocess.run(['bash', str(ops/'scripts/rollback.sh'), snapshot.name], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert (ops/'.env').read_text() == original


@pytest.mark.parametrize(('paths', 'deploy'), [
    (['apps/research-explorer/backend/api/routes.py'], True),
    (['ops/azure/Dockerfile.api'], True),
    (['uv.lock'], True),
    (['apps/research-explorer/frontend/src/lib/api.ts'], False),
    (['ops/azure/README.md', 'docs/status.md'], False),
    (['reports/release-v4/analysis.json', 'data/processed/new-graph.json'], False),
    (['ops/azure/compose.yaml', 'ops/azure/scripts/prepare-artifacts.py'], False),
])
def test_actual_workflow_path_policy(paths, deploy):
    import fnmatch
    import yaml
    workflow = yaml.load((ROOT/'.github/workflows/deploy-azure-api.yml').read_text(), Loader=yaml.BaseLoader)
    push = workflow['on']['push']
    assert push['branches'] == ['main']
    assert any(fnmatch.fnmatchcase(path, pattern) for path in paths for pattern in push['paths']) == deploy
    assert 'pull_request' not in workflow['on'] and 'pull_request_target' not in workflow['on']
    for job in workflow['jobs'].values():
        assert "github.ref == 'refs/heads/main'" in job['if']
        assert "github.event_name == 'push' || github.event_name == 'workflow_dispatch'" in job['if']
    assert workflow['concurrency']['cancel-in-progress'] == 'false'
