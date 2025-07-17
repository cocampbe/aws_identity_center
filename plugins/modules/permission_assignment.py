#!/usr/bin/python

# Copyright: (c) 2024, Your Name <your.email@example.com>
# MIT License

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_identity_center_assignment
short_description: Manage an AWS Identity Center Account Assignment.
description:
    - This module creates or deletes account assignments in AWS Identity Center.
    - An assignment connects a principal (User or Group) to a target (AWS Account) using a Permission Set.
version_added: "1.0.0"
author:
    - Your Name (@your_github_handle)
options:
    state:
        description:
            - Specifies whether the assignment should be 'present' or 'absent'.
        required: true
        type: str
        choices: ['present', 'absent']
    instance_arn:
        description:
            - The ARN of the AWS Identity Center instance.
        required: true
        type: str
    permission_set_arn:
        description:
            - The ARN of the Permission Set to assign.
        required: true
        type: str
    principal_type:
        description:
            - The type of the principal to assign.
        required: true
        type: str
        choices: ['USER', 'GROUP']
    principal_id:
        description:
            - The ID of the User or Group in Identity Center.
        required: true
        type: str
    target_id:
        description:
            - The ID of the target. Currently, this is the AWS Account ID.
        required: true
        type: str
    target_type:
        description:
            - The type of target.
        required: false
        type: str
        default: 'AWS_ACCOUNT'
        choices: ['AWS_ACCOUNT']
extends_documentation_fragment:
    - amazon.aws.common
'''

EXAMPLES = r'''
# Assign a group to an AWS account with a specific permission set
- name: Assign Developers group to the Sandbox account
  my_org.aws_identity_center.aws_identity_center_assignment:
    state: present
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
    permission_set_arn: "arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-yyyyyyyyyyyyyyyy"
    principal_type: "GROUP"
    principal_id: "a1b2c3d4-e5f6-7890-1234-567890abcdef" # Group ID from Identity Center
    target_id: "123456789012" # AWS Account ID

# Remove an assignment
- name: Remove an assignment
  my_org.aws_identity_center.aws_identity_center_assignment:
    state: absent
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
    permission_set_arn: "arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-zzzzzzzzzzzzzzzz"
    principal_type: "USER"
    principal_id: "f1e2d3c4-b5a6-7890-1234-567890abcdef" # User ID from Identity Center
    target_id: "987654321098" # AWS Account ID
'''

RETURN = r'''
changed:
    description: Whether or not a change was made.
    returned: always
    type: bool
assignment_status:
    description: The status of the assignment request (e.g., IN_PROGRESS, SUCCEEDED, FAILED).
    returned: on create or delete
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

def check_assignment_exists(client, instance_arn, account_id, ps_arn, principal_type, principal_id):
    """Helper to check if a specific assignment already exists."""
    paginator = client.get_paginator('list_account_assignments')
    for page in paginator.paginate(InstanceArn=instance_arn, AccountId=account_id, PermissionSetArn=ps_arn):
        for assignment in page.get('AccountAssignments', []):
            if assignment['PrincipalType'] == principal_type and assignment['PrincipalId'] == principal_id:
                return True
    return False

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        instance_arn=dict(type='str', required=True),
        permission_set_arn=dict(type='str', required=True),
        principal_type=dict(type='str', required=True, choices=['USER', 'GROUP']),
        principal_id=dict(type='str', required=True),
        target_id=dict(type='str', required=True),
        target_type=dict(type='str', default='AWS_ACCOUNT', choices=['AWS_ACCOUNT'])
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    client = module.client('sso-admin')
    
    state = module.params['state']
    instance_arn = module.params['instance_arn']
    ps_arn = module.params['permission_set_arn']
    principal_type = module.params['principal_type']
    principal_id = module.params['principal_id']
    target_id = module.params['target_id']
    target_type = module.params['target_type']

    result = dict(
        changed=False,
        assignment_status=None
    )

    try:
        assignment_exists = check_assignment_exists(client, instance_arn, target_id, ps_arn, principal_type, principal_id)

        if state == 'present':
            if not assignment_exists:
                if module.check_mode:
                    result['changed'] = True
                    module.exit_json(**result)

                response = client.create_account_assignment(
                    InstanceArn=instance_arn,
                    TargetId=target_id,
                    TargetType=target_type,
                    PermissionSetArn=ps_arn,
                    PrincipalType=principal_type,
                    PrincipalId=principal_id
                )
                result['changed'] = True
                result['assignment_status'] = response.get('AccountAssignmentCreationStatus', {}).get('Status')

        elif state == 'absent':
            if assignment_exists:
                if module.check_mode:
                    result['changed'] = True
                    module.exit_json(**result)

                response = client.delete_account_assignment(
                    InstanceArn=instance_arn,
                    TargetId=target_id,
                    TargetType=target_type,
                    PermissionSetArn=ps_arn,
                    PrincipalType=principal_type,
                    PrincipalId=principal_id
                )
                result['changed'] = True
                result['assignment_status'] = response.get('AccountAssignmentDeletionStatus', {}).get('Status')

    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
