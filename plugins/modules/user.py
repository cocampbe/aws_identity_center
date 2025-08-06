from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from botocore.exceptions import ClientError

def find_user(client, module: AnsibleAWSModule):
    """
    Find a user in the identity store.
    """
    response = client.list_users(
        IdentityStoreId=module.params['identity_store_id'],
        Filters=[{'AttributePath': 'UserName', 'AttributeValue': module.params['user_name']}]
    )
    users = response.get('Users', [])
    if not users:
        return None

    return users[0]  # Return the first matching user


def create_or_update_user(client, module: AnsibleAWSModule):
    """
    Create a user in the identity store.
    """
    user_name = module.params.get("name")

    changed = False
    new_user = False
    user = find_user(client, module)

    if user is None:
        client.create_user(
            IdentityStoreId=module.params['identity_store_id'],
            UserName=module.params['user_name'],
            Name={
                'GivenName': module.params['given_name'],
                'FamilyName': module.params['family_name']
            },
            DisplayName=module.params['display_name'],
            Emails=[
                {
                    'Value': module.params['email'],
                    "Type": "work",
                    'Primary': True
                }
            ]
        )
        new_user = True

    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the user again
    user = find_user(client, module)

    module.exit_json(changed=changed, user=user)

def delete_user(client, module: AnsibleAWSModule):
    """
    Delete a user from the identity store.
    """
    client.delete_user(
        IdentityStoreId=module.params['identity_store_id'],
        UserId=module.params['user_id']
    )

    module.exit_json(changed=True, msg="User deleted successfully.")

def main():
    argument_spec = dict(
        identity_store_id=dict(type='str', required=True),
        user_name=dict(type='str', required=True),
        given_name=dict(type='str', required=True),
        family_name=dict(type='str', required=True),
        display_name=dict(type='str', required=False, default=''),
        email=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    identifier_problem = validate_iam_identifiers(
        "user", name=module.params.get("user_name")
    )

    if identifier_problem:
        module.fail_json_aws(message=identifier_problem)

    # Initialize identitystore client using AnsibleAWSModule's boto3 client
    connection = module.client('identitystore')
    try:
        if module.params['state'] == 'present':
            create_or_update_user(connection, module)
        else:
            delete_user(connection, module)
    except ClientError as e:
        module.fail_json_aws(e, msg=f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()