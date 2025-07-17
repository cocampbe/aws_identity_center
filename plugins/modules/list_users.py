#!/usr/bin/python

# Copyright: (c) 2024, Your Name <your.email@example.com>
# MIT License

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: aws_identity_center_users_info
short_description: List users from AWS Identity Center.
description:
    - This module retrieves a list of users from the AWS Identity Center identity store.
    - It can retrieve all users or filter for a specific user by their username.
    - This is an information-gathering module and does not make any changes.
version_added: "1.0.1"
author:
    - Your Name (@your_github_handle)
options:
    instance_arn:
        description:
            - The ARN of the AWS Identity Center instance. This is used to find the correct Identity Store.
        required: true
        type: str
    user_name:
        description:
            - The username of a specific user to retrieve. If not provided, all users will be returned.
        required: false
        type: str
extends_documentation_fragment:
    - amazon.aws.common
'''

EXAMPLES = r'''
# List all users in the Identity Center instance
- name: Get all users
  begoingto.aws_identity_center.list_users:
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
  register: all_users_result

- name: Print all users
  ansible.builtin.debug:
    var: all_users_result.users

# Find a specific user by username
- name: Get a specific user's details
  begoingto.aws_identity_center.list_users:
    instance_arn: "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx"
    user_name: "jane.doe"
  register: specific_user_result

- name: Print specific user's ID
  ansible.builtin.debug:
    msg: "User ID for jane.doe is {{ specific_user_result.users[0].user_id }}"
  when: specific_user_result.users | length > 0
'''

RETURN = r'''
users:
    description: A list of dictionaries, where each dictionary represents a user.
    returned: always
    type: list
    sample:
      - user_id: "a1b2c3d4-e5f6-7890-1234-567890abcdef"
        user_name: "jane.doe"
        display_name: "Jane Doe"
        emails:
          - primary: true
            type: "work"
            value: "jane.doe@example.com"
        name:
          formatted: "Jane Doe"
          given_name: "Jane"
          family_name: "Doe"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from botocore.exceptions import ClientError

def get_identity_store_id(sso_admin_client, instance_arn):
    """Find the Identity Store ID associated with an SSO instance ARN."""
    try:
        paginator = sso_admin_client.get_paginator('list_instances')
        for page in paginator.paginate():
            for instance in page.get('Instances', []):
                if instance.get('InstanceArn') == instance_arn:
                    return instance.get('IdentityStoreId')
    except ClientError as e:
        # Handle cases where the instance might not be found or other API errors
        return None
    return None

def run_module():
    module_args = dict(
        instance_arn=dict(type='str', required=True),
        user_name=dict(type='str', required=False)
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True # Info modules are safe for check mode
    )

    sso_admin_client = module.client('sso-admin')
    identity_store_client = module.client('identitystore')

    instance_arn = module.params['instance_arn']
    user_name_filter = module.params.get('user_name')

    result = dict(
        changed=False,
        users=[]
    )

    try:
        identity_store_id = get_identity_store_id(sso_admin_client, instance_arn)
        if not identity_store_id:
            module.fail_json(msg=f"Could not find Identity Store ID for instance ARN: {instance_arn}")

        users_list = []
        
        # If a specific username is provided, use a filter
        if user_name_filter:
            response = identity_store_client.list_users(
                IdentityStoreId=identity_store_id,
                Filters=[
                    {
                        'AttributePath': 'UserName',
                        'AttributeValue': user_name_filter
                    },
                ]
            )
            users_list.extend(response.get('Users', []))
        else:
            # Otherwise, paginate through all users
            paginator = identity_store_client.get_paginator('list_users')
            pages = paginator.paginate(IdentityStoreId=identity_store_id)
            for page in pages:
                users_list.extend(page.get('Users', []))

        # Convert the AWS camelCase keys to Ansible snake_case
        for user in users_list:
            result['users'].append(camel_dict_to_snake_dict(user))

    except ClientError as e:
        module.fail_json(msg=f"AWS API Error: {e}")
    except Exception as e:
        module.fail_json(msg=f"An unexpected error occurred: {e}")

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
