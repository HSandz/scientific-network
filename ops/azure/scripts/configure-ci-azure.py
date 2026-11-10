#!/usr/bin/env python3
"""Operator setup: free managed identity, main-only OIDC, VM-scoped Run Command.

Requires an authenticated Azure operator with identity/custom-role/role-assignment
rights and GitHub repository administration. No credential is created or copied.
"""
import json
import subprocess
import tempfile
from pathlib import Path

SUBSCRIPTION = '22962704-ad29-4ef3-9245-844a8cbf3a1a'
GROUP = 'social-network'
VM = f'/subscriptions/{SUBSCRIPTION}/resourceGroups/{GROUP}/providers/Microsoft.Compute/virtualMachines/scientific-network'
REPO = 'HSandz/scientific-network'
IDENTITY = 'scientific-network-api-github'
ROLE = 'Scientific Network API Deployment'


def az(*args):
    return json.loads(subprocess.check_output(['az', *args, '--subscription', SUBSCRIPTION, '-o', 'json']))


def gh(path, payload):
    subprocess.run(['gh', 'api', '--method', 'PUT', f'repos/{REPO}/' + path, '--input', '-'],
                   input=json.dumps(payload), text=True, check=True)


def configure():
    vm = az('vm', 'show', '--ids', VM)
    # Identity has no billable compute, registry or network component.
    identities = az('identity', 'list', '--resource-group', GROUP)
    identity = next((i for i in identities if i['name'] == IDENTITY), None)
    if identity is None:
        identity = az('identity', 'create', '--resource-group', GROUP, '--name', IDENTITY, '--location', vm['location'])
    # Environment restricts deployment to main, with no per-push approval gate.
    gh('environments/production-api', {'deployment_branch_policy': {'protected_branches': False, 'custom_branch_policies': True}})
    policies = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPO}/environments/production-api/deployment-branch-policies']))
    if not any(p['name'] == 'main' and p['type'] == 'branch' for p in policies['branch_policies']):
        subprocess.run(['gh', 'api', '--method', 'POST', f'repos/{REPO}/environments/production-api/deployment-branch-policies',
                        '-f', 'name=main', '-f', 'type=branch'], check=True)
    # Bind identity to this exact workflow, not every job that can name the env.
    gh('actions/oidc/customization/sub', {'use_default': False, 'include_claim_keys': ['repo', 'context', 'job_workflow_ref']})
    oidc = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPO}/actions/oidc/customization/sub']))
    prefix = oidc.get('sub_claim_prefix', f'repo:{REPO}')
    subject = f'{prefix}:environment:production-api:job_workflow_ref:{REPO}/.github/workflows/deploy-azure-api.yml@refs/heads/main'
    credentials = az('identity', 'federated-credential', 'list', '--resource-group', GROUP, '--identity-name', IDENTITY)
    if not any(c['name'] == 'github-main-api' for c in credentials):
        az('identity', 'federated-credential', 'create', '--resource-group', GROUP, '--identity-name', IDENTITY,
           '--name', 'github-main-api', '--issuer', 'https://token.actions.githubusercontent.com',
           '--subject', subject, '--audiences', 'api://AzureADTokenExchange')
    else:
        if next(c for c in credentials if c['name'] == 'github-main-api')['subject'] != subject:
            az('identity', 'federated-credential', 'update', '--resource-group', GROUP, '--identity-name', IDENTITY,
               '--name', 'github-main-api', '--subject', subject)
    roles = az('role', 'definition', 'list', '--name', ROLE)
    if not roles:
        role = {'Name': ROLE, 'IsCustom': True,
                'Description': 'Read one VM and invoke guest Run Command for trusted API releases. Root-equivalent inside that VM.',
                'Actions': ['Microsoft.Compute/virtualMachines/read',
                            'Microsoft.Compute/virtualMachines/instanceView/read',
                            'Microsoft.Compute/virtualMachines/runCommand/action'],
                'NotActions': [], 'DataActions': [], 'NotDataActions': [],
                'AssignableScopes': [f'/subscriptions/{SUBSCRIPTION}/resourceGroups/{GROUP}']}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'role.json'
            path.write_text(json.dumps(role))
            az('role', 'definition', 'create', '--role-definition', str(path))
    assignments = az('role', 'assignment', 'list', '--scope', VM)
    if not any(a['principalId'] == identity['principalId'] and a['roleDefinitionName'] == ROLE for a in assignments):
        az('role', 'assignment', 'create', '--assignee-object-id', identity['principalId'],
           '--assignee-principal-type', 'ServicePrincipal', '--role', ROLE, '--scope', VM)
    values = {'AZURE_API_CLIENT_ID': identity['clientId'], 'AZURE_API_TENANT_ID': identity['tenantId'],
              'AZURE_API_SUBSCRIPTION_ID': SUBSCRIPTION, 'AZURE_API_VM_ID': VM}
    for key, value in values.items():
        subprocess.run(['gh', 'variable', 'set', key, '--repo', REPO, '--env', 'production-api', '--body', value], check=True)
    print('Configured passwordless identity and production-api variables. No secrets created.')


if __name__ == '__main__':
    configure()
