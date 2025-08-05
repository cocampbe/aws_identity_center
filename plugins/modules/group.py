#!/usr/bin/env python
# Copyright: (c) 2025, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from botocore.exceptions import ClientError

def run_module():
    module_args = dict(
        identity_store_id=dict(type='str', required=True),
        display_name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=''),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        region=dict(type='str', required=False, default=None)
    )

    result = dict(
        changed=False,
        group_id='',
        message=''
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    identity_store_id = module.params['identity_store_id']
    display_name = module.params['display_name']
    description = module.params['description']
    state = module.params['state']
    region = module.params['region']

    try:
        # Initialize identitystore client using AnsibleAWSModule's boto3 client
        client = module.client('identitystore', region_name=region)

        # Check if group exists
        response = client.list_groups(
            IdentityStoreId=identity_store_id,
            Filters=[{'AttributePath': 'DisplayName', 'AttributeValue': display_name}]
        )
        existing_groups = response.get('Groups', [])

        if state == 'present':
            if existing_groups:
                result['group_id'] = existing_groups[0]['GroupId']
                result['message'] = f"Group {display_name} already exists"
            else:
                if not module.check_mode:
                    response = client.create_group(
                        IdentityStoreId=identity_store_id,
                        DisplayName=display_name,
                        Description=description
                    )
                    result['group_id'] = response['GroupId']
                    result['changed'] = True
                    result['message'] = f"Group {display_name} created successfully"
                else:
                    result['changed'] = True
                    result['message'] = f"Group {display_name} would be created (check mode)"

        elif state == 'absent':
            if existing_groups:
                if not module.check_mode:
                    client.delete_group(
                        IdentityStoreId=identity_store_id,
                        GroupId=existing_groups[0]['GroupId']
                    )
                    result['changed'] = True
                    result['message'] = f"Group {display_name} deleted successfully"
                else:
                    result['changed'] = True
                    result['message'] = f"Group {display_name} would be deleted (check mode)"
            else:
                result['message'] = f"Group {display_name} does not exist"

    except ClientError as e:
        module.fail_json_aws(e, msg=f"AWS API error: {str(e)}")

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()