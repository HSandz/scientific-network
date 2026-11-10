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


@pytest.fixture
def hosted_recovery(tmp_path, monkeypatch):
    import importlib.util
    import json
    spec = importlib.util.spec_from_file_location('ci_recovery', ROOT/'ops/azure/scripts/rollback-ci-image.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'OPS', tmp_path)
    state = {'sha': 'a'*40, 'sequence': 5, 'operation': 'activated', 'rollback_snapshot': '.env.rollback-fixture'}
    (tmp_path/'.ci-deployment.json').write_text(json.dumps(state))
    (tmp_path/'.ci-rollback-state.json').write_text(json.dumps({'sha': 'b'*40, 'image_id': 'sha256:previous', 'sequence': 4}))
    return module, tmp_path, state


def test_hosted_failure_recovery_keeps_sequence_watermark(hosted_recovery, monkeypatch):
    import json
    module, ops, state = hosted_recovery
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    module.rollback('a'*40, 5)
    recovered = json.loads((ops/'.ci-deployment.json').read_text())
    assert recovered['sha'] == 'b'*40 and recovered['image_id'] == 'sha256:previous'
    assert recovered['sequence'] == 5 and recovered['operation'] == 'rolled_back'
    assert calls[0][0][0] == [str(ops/'scripts/rollback.sh'), '.env.rollback-fixture']


def test_hosted_recovery_refuses_superseding_deployment(hosted_recovery, monkeypatch):
    module, ops, state = hosted_recovery
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **kw: pytest.fail('Must not invoke rollback'))
    with pytest.raises(AssertionError, match='superseding'):
        module.rollback('c'*40, 4)


def test_hosted_recovery_failure_does_not_claim_restoration(hosted_recovery, monkeypatch):
    import json
    module, ops, state = hosted_recovery
    def fail(*a, **kw):
        raise subprocess.CalledProcessError(70, a)
    monkeypatch.setattr(module.subprocess, 'run', fail)
    with pytest.raises(subprocess.CalledProcessError):
        module.rollback('a'*40, 5)
    assert json.loads((ops/'.ci-deployment.json').read_text()) == state


def test_hosted_failure_after_noop_does_not_roll_back_unchanged_service(hosted_recovery, monkeypatch):
    import json
    module, ops, state = hosted_recovery
    state['operation'] = 'noop'
    (ops/'.ci-deployment.json').write_text(json.dumps(state))
    monkeypatch.setattr(module.subprocess, 'run', lambda *a, **kw: pytest.fail('Must retain unchanged service'))
    module.rollback('a'*40, 5)
    assert json.loads((ops/'.ci-deployment.json').read_text()) == state


def test_saved_config_identity_is_portable_and_validates_architecture(tmp_path):
    import hashlib
    import importlib.util
    import io
    import json
    import tarfile
    spec = importlib.util.spec_from_file_location('image_identity', ROOT/'ops/azure/scripts/image-identity.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sha = 'a'*40
    config = json.dumps({'architecture': 'amd64', 'os': 'linux', 'rootfs': {'diff_ids': ['sha256:layer']},
                         'config': {'Labels': {'org.opencontainers.image.revision': sha}}}).encode()
    path = tmp_path/'image.tar.gz'
    def save(data):
        with tarfile.open(path, 'w:gz') as t:
            for name, payload in [('manifest.json', json.dumps([{'RepoTags': ['scientific-network-api:sha-'+sha], 'Config': 'config.json'}]).encode()), ('config.json', data)]:
                item = tarfile.TarInfo(name)
                item.size = len(payload)
                t.addfile(item, io.BytesIO(payload))
    save(config)
    assert module.identity(path, sha) == 'sha256:'+hashlib.sha256(config).hexdigest()
    with pytest.raises(AssertionError):
        module.identity(path, 'b'*40)
    save(config.replace(b'amd64', b'arm64'))
    with pytest.raises(AssertionError):
        module.identity(path, sha)


def test_https_probe_has_reaper_without_relaxing_resource_or_health_limits():
    """TLS helper children must be reaped; retain the real trusted HTTPS probe."""
    import yaml
    config = yaml.safe_load((ROOT/'ops/azure/compose.yaml').read_text())
    proxy = config['services']['caddy']
    assert proxy['init'] is True
    assert proxy['pids_limit'] == 100
    assert 'https://$$API_HOSTNAME/api/live' in proxy['healthcheck']['test'][-1]
    assert '--no-check-certificate' not in proxy['healthcheck']['test'][-1]


def test_unhealthy_proxy_blocks_activation_before_download_or_update(monkeypatch, tmp_path):
    import importlib.util
    import json
    spec = importlib.util.spec_from_file_location('activate', ROOT/'ops/azure/scripts/activate-ci-image.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def inspect(*args):
        healthy = args[-1].endswith('neo4j-1')
        return json.dumps([{'Id': 'preserved', 'Image': 'same', 'Mounts': [], 'RestartCount': 0,
                            'State': {'Health': {'Status': 'healthy' if healthy else 'unhealthy'},
                                      'OOMKilled': False, 'StartedAt': 'unchanged'}}])
    monkeypatch.setattr(module, 'run', inspect)
    with pytest.raises(AssertionError, match='caddy unhealthy'):
        module.stable_services()
