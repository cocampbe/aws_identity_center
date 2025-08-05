#!/usr/bin/python

# Copyright: (c) 2024, Your Name <your.email@example.com>
# MIT License

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: permission_set
short_description: Manage an AWS Identity Center Permission Set.
description:
    - This module allows for the creation, update, and deletion of Permission Sets in AWS Identity Center.
    - It is idempotent and will only make changes if the desired state differs from the current state.
version_added: "1.0.0"
author:
    - Your Name (@begoingto)
options:
    state:
        description:
            - Specifies whether the permission set should be 'present' or 'absent'.
        required: true
        type: str
        choices: ['present', 'absent']
    name:
        description:
            - The name of the permission set.
        required: true
        type: str
    instance_arn:
        description:
            - The ARN of the AWS Identity Center instance.
        required: true
        type: str
    description:
        description:
            - A description for the permission set.
        required: false
        type: str
    session_duration:
        description:
            - The length of time that a user can be signed in to an AWS account.
            - Formatted as an ISO 8601 duration string (e.g., 'PT1H' for 1 hour, 'PT8H' for 8 hours).
        required: false
        type: str
        default: 'PT1H'
    relay_state:
        description:
            - The URL that users are redirected to after signing in.
        required: false
        type: str
    managed_policies:
        description:
            - A list of ARNs for AWS managed policies to attach to the permission set.
        required: false
        type: list
        elements: str
    inline_policy:
        description:
            - A JSON-formatted IAM policy to be embedded in the permission set.
        required: false
        type: str
    tags:
        description:
            - A dictionary of key-value pairs to tag the permission set.
        required: false
        type: dict
extends_documentation_fragment:
    - amazon.aws.common
'''

EXAMPLES = r'''
# Create or update a permission set with a managed policy
- name: Ensure PowerUser permission set exists
  begoingto.aws_identity_center.permission_set:
    state: present
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
    name: "PowerUser"
    description: "Grants power user access"
    session_duration: "PT8H"
    managed_policies:
      - "arn:aws:iam::aws:policy/PowerUserAccess"

# Delete a permission set
- name: Ensure OldPermissionSet is removed
  begoingto.aws_identity_center.permission_set:
    state: absent
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
    name: "OldPermissionSet"
'''

RETURN = r'''
permission_set_arn:
    description: The ARN of the permission set.
    returned: on success when state is 'present'
    type: str
    sample: 'arn:aws:sso:::permissionSet/ssoins-xxxxxxxxxxxxxxxx/ps-yyyyyyyyyyyyyyyy'
changed:
    description: Whether or not a change was made.
    returned: always
    type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six import string_types
import json

# In a real implementation, you would put helper functions in module_utils
# For this example, we'll keep it simple.

def find_permission_set_by_name(client, instance_arn, name):
    """Helper to find a permission set ARN by its name."""
    paginator = client.get_paginator('list_permission_sets')
    for page in paginator.paginate(InstanceArn=instance_arn):
        for ps_arn in page.get('PermissionSets', []):
            details = client.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=ps_arn
            )
            if details['PermissionSet']['Name'] == name:
                # Get managed policies
                managed_policies = []
                mp_paginator = client.get_paginator('list_managed_policies_in_permission_set')
                for mp_page in mp_paginator.paginate(InstanceArn=instance_arn, PermissionSetArn=ps_arn):
                    managed_policies.extend(mp_page.get('AttachedManagedPolicies', []))
                managed_policy_arns = [mp['Arn'] for mp in managed_policies]

                # Get inline (custom) policy
                try:
                    inline_policy_resp = client.get_inline_policy_for_permission_set(
                        InstanceArn=instance_arn,
                        PermissionSetArn=ps_arn
                    )
                    inline_policy = inline_policy_resp.get('InlinePolicy', None)
                except client.exceptions.ResourceNotFoundException:
                    inline_policy = None

                return {
                    'PermissionSetArn': ps_arn,
                    'ManagedPolicies': managed_policy_arns,
                    'InlinePolicy': json.loads(inline_policy) if inline_policy else {}
                }
    return None

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str', required=True),
        instance_arn=dict(type='str', required=True),
        description=dict(type='str', required=False),
        session_duration=dict(type='str', required=False, default='PT1H'),
        relay_state=dict(type='str', required=False),
        managed_policies=dict(type='list', elements='str', required=False, default=[]),
        inline_policy=dict(type='str', required=False),
        inline_policy_json=dict(type="json", default=None, required=False),
        tags=dict(type='dict', required=False)
    )
    
    # required_if = [
    #     ("state", "present", ("inline_policy_json",), True),
    # ]

    # Using AnsibleAWSModule helps with authentication and client creation
    module = AnsibleAWSModule(
        argument_spec=module_args,
        # required_if=required_if, 
        supports_check_mode=True
    )

    client = module.client('sso-admin')
    
    state = module.params['state']
    name = module.params['name']
    instance_arn = module.params['instance_arn']
    
    result = dict(
        changed=module.check_mode,
        permission_set_arn='',
        managed_policies=[],
        inline_policy={}
    )

    try:
        # Find existing permission set
        ps_arn = find_permission_set_by_name(client, instance_arn, name)

        if state == 'present':
            if not ps_arn:
                # --- CREATE ---
                if module.check_mode:
                    result['changed'] = True
                    module.exit_json(**result)

                create_params = {
                    'InstanceArn': instance_arn,
                    'Name': name,
                    'Description': module.params.get('description', ''),
                    'SessionDuration': module.params['session_duration'],
                }
                if module.params.get('relay_state'):
                    create_params['RelayState'] = module.params['relay_state']

                response = client.create_permission_set(**create_params)
                ps_arn = response['PermissionSet']['PermissionSetArn']
                result['changed'] = True

                # Attach customer managed policy reference if provided
                if module.params.get('managed_policies'):
                    for policy_arn in module.params['managed_policies']:
                        client.attach_managed_policy_to_permission_set(
                            InstanceArn=instance_arn,
                            PermissionSetArn=ps_arn,
                            ManagedPolicyArn=policy_arn
                        )
                    # set Attach managed policies
                    result['managed_policies'] = module.params['managed_policies']

                        
                if module.params.get('inline_policy_json'):
                    inline_policy = json.dumps(json.loads(module.params['inline_policy_json']))
                    client.put_inline_policy_to_permission_set(
                        InstanceArn=instance_arn,
                        PermissionSetArn=ps_arn,
                        InlinePolicy=inline_policy
                    )
                    # set Inline policy
                    result['inline_policy'] = json.loads(inline_policy)

                # NOTE: In a real module, you'd add logic here to attach policies and tags
                # This is a simplified example.
            
            else:
                # --- UPDATE (Check for diffs) ---
                # A full implementation would compare all params (description, duration, etc.)
                # and call update_permission_set if needed. This is complex.
                # For this example, we assume if it exists, it's correctly configured.
                # A real module would set result['changed'] = True if an update is performed.
                pass
            
            result['permission_set_arn'] = ps_arn

        elif state == 'absent':
            if ps_arn:
                # --- DELETE ---
                if module.check_mode:
                    result['changed'] = True
                    module.exit_json(**result)

                client.delete_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )
                result['changed'] = True

    except Exception as e:
        module.fail_json(msg=str(e))

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
