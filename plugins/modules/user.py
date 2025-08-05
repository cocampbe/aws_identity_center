#!/usr/bin/env python
# Copyright: (c) 2025, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from botocore.exceptions import ClientError

def run_module(client, module: AnsibleAWSModule, current_count: int = 0):

    identifier_problem = validate_iam_identifiers(
        "user", name=module.params.get("user_name")
    )

    result = dict(
        changed=False,
        user_id='',
        message=''
    )

    identity_store_id = module.params['identity_store_id']
    user_name = module.params['user_name']
    given_name = module.params['given_name']
    family_name = module.params['family_name']
    display_name = module.params['display_name'] or f"{given_name} {family_name}"
    email = module.params['email']
    state = module.params['state']

    try:

        # Check if user exists
        response = client.list_users(
            IdentityStoreId=identity_store_id,
            Filters=[{'AttributePath': 'UserName', 'AttributeValue': user_name}]
        )
        existing_users = response.get('Users', [])

        if state == 'present':
            if existing_users:
                result['changed'] = False
                result['user_id'] = existing_users[0]['UserId']
                result['message'] = f"User {user_name} already exists"
            else:
                if not module.check_mode:
                    response = client.create_user(
                        IdentityStoreId=identity_store_id,
                        UserName=user_name,
                        Name={'GivenName': given_name, 'FamilyName': family_name},
                        DisplayName=display_name,
                        Emails=[{'Value': email, "Type": "work", 'Primary': True}]
                    )
                    result['user_id'] = response['UserId']
                    result['changed'] = True
                    result['message'] = f"User {user_name} created successfully"
                else:
                    result['changed'] = True
                    result['message'] = f"User {user_name} would be created (check mode)"

        elif state == 'absent':
            if existing_users:
                if not module.check_mode:
                    client.delete_user(
                        IdentityStoreId=identity_store_id,
                        UserId=existing_users[0]['UserId']
                    )
                    result['changed'] = True
                    result['message'] = f"User {user_name} deleted successfully"
                else:
                    result['changed'] = True
                    result['message'] = f"User {user_name} would be deleted (check mode)"
            else:
                result['message'] = f"User {user_name} does not exist"

    except ClientError as e:
        module.fail_json_aws(e, msg=f"AWS API error: {str(e)}")

    module.exit_json(**result)

def main():
    module_args = dict(
        identity_store_id=dict(type='str', required=True),
        user_name=dict(type='str', required=True),
        given_name=dict(type='str', required=True),
        family_name=dict(type='str', required=True),
        display_name=dict(type='str', required=False, default=''),
        email=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        region=dict(type='str', required=False, default=None)
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    region = module.params['region']

    # Initialize identitystore client using AnsibleAWSModule's boto3 client
    client = module.client('identitystore', region_name=region)
    run_module(client=client, module=AnsibleAWSModule())

if __name__ == '__main__':
    main()