#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Neuy Mich <begoingto.me@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: idc_group
version_added_collection: community.aws
short_description: Manage AWS Identity Center groups
description:
  - Manage AWS Identity Center groups.
author:
  - Neuy Mich (@begoingto)
  - Courtney Campbell (@cocampbe)
options:
  name:
    description:
      - The name of the group.
    required: true
    type: str
  description:
    description:
      - A description of the group.
    required: false
    type: str
  identity_store_id:
    description:
      - AWS identity store ID
    required: true
    type: str
  state:
    description:
      - Create or remove the IDC group.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a group
  community.aws.idc_group:
    name: testgroup1
    state: present

- name: Delete the group
  community.aws.idc_group:
    name: testgroup1
    state: absent
"""


from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule
from botocore.exceptions import ClientError

def create_group(connection, module):
    display_name = module.params['name']
    description = module.params['description']
    identity_store_id = module.params['identity_store_id']

    existing_groups = get_idc_group(connection, module)

    if existing_groups:
        module.exit_json(changed=False, idc_group=display_name)
    else:
        if description == None:
            response = connection.create_group(
                IdentityStoreId=identity_store_id,
                DisplayName=display_name
            )
        else:
            response = connection.create_group(
                IdentityStoreId=identity_store_id,
                DisplayName=display_name,
                Description=description
            )

        module.exit_json(changed=True, idc_group=display_name)

    if module.check_mode:
        module.exit_json(changed=True, idc_group=display_name)


def destroy_group(connection, module):
    display_name = module.params['name']
    identity_store_id = module.params['identity_store_id']

    existing_groups = get_idc_group(connection, module)

    if existing_groups:
        connection.delete_group(
            IdentityStoreId=identity_store_id,
            GroupId=existing_groups[0]['GroupId']
        )

        module.exit_json(changed=True, idc_group=display_name)
    else:
        module.exit_json(changed=False, idc_group=display_name)

    if module.check_mode:
        module.exit_json(changed=True, idc_group=display_name)

def get_idc_group(connection, module):
    display_name = module.params['name']
    identity_store_id = module.params['identity_store_id']

    response = connection.list_groups(
        IdentityStoreId=identity_store_id,
        Filters=[{'AttributePath': 'DisplayName', 'AttributeValue': display_name}]
    )

    return response.get('Groups', [])


def main():
    argument_spec = dict(
        identity_store_id=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=None),
        region=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params['state']

    connection = module.client("identitystore")

    try:
        if state == 'present':
            create_group(connection, module)
        else:
            destroy_group(connection, module)
    except ClientError as e:
        module.fail_json_aws(e)


if __name__ == '__main__':
    main()
