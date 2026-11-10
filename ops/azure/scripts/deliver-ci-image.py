#!/usr/bin/env python3
"""Deliver a hosted-runner artifact through Azure OIDC, without inbound SSH."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import urllib.error
import urllib.request


def api(path):
    request = urllib.request.Request('https://api.github.com/repos/HSandz/scientific-network/' + path,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(request, timeout=30))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def deliver():
    sha = os.environ['GITHUB_SHA']
    assert re.fullmatch('[0-9a-f]{40}', sha)
    assert os.environ['GITHUB_REF'] == 'refs/heads/main'
    assert os.environ['GITHUB_EVENT_NAME'] in ('push', 'workflow_dispatch')
    if api('git/ref/heads/main')['object']['sha'] != sha:
        print('Skipped stale run: main has advanced.')
        return
    artifact_id = os.environ['ARTIFACT_ID']
    assert artifact_id.isdigit()
    request = urllib.request.Request(
        f'https://api.github.com/repos/HSandz/scientific-network/actions/artifacts/{artifact_id}/zip',
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN']})
    try:
        urllib.request.build_opener(NoRedirect).open(request, timeout=30)
        raise RuntimeError('Expected private artifact redirect')
    except urllib.error.HTTPError as exc:
        assert exc.code == 302
        signed_url = exc.headers['Location']
    # Treat short-lived artifact URL as a secret. Never print az arguments.
    print('::add-mask::' + signed_url, flush=True)
    command = shlex.join([
        'python3', '/opt/scientific-network/ops/azure/scripts/activate-ci-image.py',
        '--sha', sha, '--sequence', os.environ['GITHUB_RUN_NUMBER'],
        '--checksum', Path('image.tar.gz.sha256').read_text().split()[0],
        '--image-id', Path('image-id.txt').read_text().strip(), '--url', signed_url,
    ])
    invoke(command, 'AZURE_API_DEPLOYMENT_VERIFIED', signed_url)
    try:
        subprocess.run(['python3', str(Path(__file__).with_name('smoke-api.py')),
                        '--base-url', 'https://scientific-network-api.eastasia.cloudapp.azure.com/api'],
                       check=True, timeout=180)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        rollback = shlex.join(['python3', '/opt/scientific-network/ops/azure/scripts/rollback-ci-image.py',
                              '--sha', sha, '--sequence', os.environ['GITHUB_RUN_NUMBER']])
        invoke(rollback, 'AZURE_API_ROLLBACK_VERIFIED', signed_url)
        raise RuntimeError('Hosted public smoke failed; recovery verified')


def invoke(command, marker, signed_url):
    with tempfile.TemporaryDirectory() as temp:
        script = Path(temp) / 'activate.sh'
        script.write_text('#!/bin/sh\nset -eu\n' + command + '\n')
        script.chmod(0o600)
        result = subprocess.run([
            'az', 'vm', 'run-command', 'invoke', '--ids', os.environ['AZURE_VM_ID'],
            '--command-id', 'RunShellScript', '--scripts', '@' + str(script),
            '--output', 'json', '--only-show-errors',
        ], capture_output=True, text=True, timeout=1200)
        if result.returncode:
            # Azure errors should not echo the submitted signed script.
            raise RuntimeError('Azure Run Command request failed; inspect Azure activity log (sensitive URL omitted)')
        values = json.loads(result.stdout)['value']
        for item in values:
            message = item.get('message', '').replace(signed_url, '[MASKED]')
            print(message)
            # API invocation success does NOT imply guest script success.
            if 'failed' in item.get('code', '').lower():
                raise RuntimeError('Azure guest command failed')
        assert any(marker in i.get('message', '') for i in values), 'Missing verified guest receipt'


if __name__ == '__main__':
    deliver()
