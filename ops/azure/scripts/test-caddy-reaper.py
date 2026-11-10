#!/usr/bin/env python3
"""Local isolated reproduction of BusyBox TLS helper zombies; no graph or host ports.

Uses the production Caddy image, HTTPS target and PID cap. Both disposable
containers are removed, including anonymous volumes, even on failure.
"""
import json
import subprocess
import time
import uuid


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def zombies(name):
    output = run('docker', 'exec', name, 'ps', '-o', 'pid,ppid,stat,comm')
    return sum('Z' in line.split()[2] and 'ssl_client' in line for line in output.splitlines()[1:])


def main():
    results = {}
    for reaper in (False, True):
        name = 'explorer-caddy-reaper-' + uuid.uuid4().hex[:10]
        try:
            run('docker', 'run', '-d', '--name', name,
                *(['--init'] if reaper else []), '--pids-limit', '100',
                '--memory', '128m', '--read-only',
                '--tmpfs', '/data', '--tmpfs', '/config', '--tmpfs', '/tmp',
                '-e', 'GOMAXPROCS=2',
                '--health-cmd', 'wget -q --spider --timeout=10 https://scientific-network-api.eastasia.cloudapp.azure.com/api/live',
                '--health-interval', '1s', '--health-timeout', '15s', '--health-retries', '3',
                'caddy:2.10.2-alpine')
            time.sleep(20)
            health = json.loads(run('docker', 'inspect', name))[0]['State']['Health']
            assert health['Status'] == 'healthy', health
            count = zombies(name)
            if reaper:
                assert count == 0, f'Init failed to reap TLS children: {count}'
                run('docker', 'restart', name)
                run('docker', 'exec', name, 'wget', '-q', '--spider', '--timeout=10',
                    'https://scientific-network-api.eastasia.cloudapp.azure.com/api/live')
                assert zombies(name) == 0
            else:
                assert count >= 10, f'Expected TLS helper leak reproduction, got {count}'
            results['with_init' if reaper else 'without_init'] = {'health_interval_seconds': 1, 'observation_seconds': 20, 'ssl_client_zombies': count, 'restart_verified': reaper}
        finally:
            subprocess.run(['docker', 'rm', '-fv', name], check=False, capture_output=True)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
