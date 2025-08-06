from ansible_collections.amazon.aws.plugins.module_utils.iam import validate_iam_identifiers, IAMErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from botocore.exceptions import ClientError

from ansible_collections.begoingto.aws_identity_center.plugins.module_utils.dict_converter import \
    convert_dict_keys_to_pascal, remove_keys_from_dict, \
    remove_keys_empty_value


@IAMErrorHandler.common_error_handler("wait for IAM user creation")
def _wait_user_exists(connection, **params):
    waiter = connection.get_waiter("user_exists")
    waiter.wait(**params)


def wait_iam_exists(connection, module):
    if not module.params.get("wait"):
        return

    user_name = module.params.get("user_name")
    wait_timeout = module.params.get("wait_timeout")

    delay = min(wait_timeout, 5)
    max_attempts = wait_timeout // delay
    waiter_config = {"Delay": delay, "MaxAttempts": max_attempts}

    _wait_user_exists(connection, WaiterConfig=waiter_config, UserName=user_name)


def find_user(client, identity_store_id, user_name):
    """
    Find a user in the identity store.
    """
    response = client.list_users(
        IdentityStoreId=identity_store_id,
        Filters=[{'AttributePath': 'UserName', 'AttributeValue': user_name}]
    )
    users = response.get('Users', [])
    if not users:
        return None

    return users[0]  # Return the first matching user


def create_or_update_user(client, module: AnsibleAWSModule):
    """
    Create a user in the identity store.
    """
    # user_name = module.params.get("user_name")
    user_params = convert_dict_keys_to_pascal(module.params)
    remove_key = {"State", "Region", "Wait", "WaitTimeout"}
    user_params = remove_keys_from_dict(user_params, remove_key)
    user_params = remove_keys_empty_value(user_params)

    changed = False
    user = find_user(client, identity_store_id=user_params['IdentityStoreId'], user_name=user_params['UserName'])

    if user is None:
        if not module.check_mode:
            # Create user from model parameters
            params_create = {
                'IdentityStoreId': user_params['IdentityStoreId'],
                'UserName': user_params['UserName'],
                'Name': {
                    'Formatted': user_params['Name']['Formatted'],
                    'FamilyName': user_params['Name']['FamilyName'],
                    'GivenName': user_params['Name']['GivenName']
                },
                'DisplayName': user_params['DisplayName'],
                'Emails': user_params['Emails']
            }
            if 'Addresses' in user_params:
                params_create['Addresses'] = user_params['Addresses']

            if 'PhoneNumbers' in user_params:
                params_create['PhoneNumbers'] = user_params['PhoneNumbers']

            if 'Title' in user_params:
                params_create['Title'] = user_params['Title']

            if 'Locale' in user_params:
                params_create['Locale'] = user_params['Locale']

            if 'Timezone' in user_params:
                params_create['Timezone'] = user_params['Timezone']

            if 'PreferredLanguage' in user_params:
                params_create['PreferredLanguage'] = user_params['PreferredLanguage']

            if 'UserType' in user_params:
                params_create['UserType'] = user_params['UserType']

            if 'NickName' in user_params:
                params_create['NickName'] = user_params['NickName']

            if 'Enterprise' in user_params:
                params_create['Enterprise'] = convert_dict_keys_to_pascal(remove_keys_empty_value(user_params['Enterprise']))

            res = client.create_user(**params_create)
            changed = True
            # Wait for user to be fully available before continuing
            wait_iam_exists(client, module)
            user_params['UserId'] = res['UserId']
            user = user_params
    else:
        # update user from model parameters
        user_params['UserId'] = user['UserId']
        on_update_user(user_params, client, module)
        user = find_user(client, identity_store_id=user_params['IdentityStoreId'], user_name=user_params['UserName'])

    module.exit_json(changed=changed, message=f"User {user['UserName']} created", user=user)


def on_update_user(user, client, module: AnsibleAWSModule):
    # Check for changes in attributes
    if not module.check_mode:
        try:
            # Update user attributes
            user_operation = [
                {
                    'AttributePath': 'userName',
                    'AttributeValue': user['UserName'],
                },
                {
                    'AttributePath': 'name.formatted',
                    'AttributeValue': user['Name']['Formatted'],
                },
                {
                    'AttributePath': 'name.familyName',
                    'AttributeValue': user['Name']['FamilyName'],
                },
                {
                    'AttributePath': 'name.givenName',
                    'AttributeValue': user['Name']['GivenName'],
                },
                {
                    'AttributePath': 'emails',
                    'AttributeValue': user['Emails'],
                },
                {
                    'AttributePath': 'displayName',
                    'AttributeValue': user['DisplayName'],
                }
            ]

            if 'Addresses' in user:
                user_operation.append({
                    'AttributePath': 'addresses',
                    'AttributeValue': user['Addresses'],
                })

            if 'PhoneNumbers' in user:
                user_operation.append({
                    'AttributePath': 'phoneNumbers',
                    'AttributeValue': user['PhoneNumbers'],
                })

            if 'Title' in user:
                user_operation.append({
                    'AttributePath': 'title',
                    'AttributeValue': user['Title'],
                })

            if 'Locale' in user:
                user_operation.append({
                    'AttributePath': 'locale',
                    'AttributeValue': user['Locale'],
                })

            if 'Timezone' in user:
                user_operation.append({
                    'AttributePath': 'timezone',
                    'AttributeValue': user['Timezone'],
                })

            if 'PreferredLanguage' in user:
                user_operation.append({
                    'AttributePath': 'preferredLanguage',
                    'AttributeValue': user['PreferredLanguage'],
                })

            if 'UserType' in user:
                user_operation.append({
                    'AttributePath': 'userType',
                    'AttributeValue': user['UserType'],
                })

            if 'NickName' in user:
                user_operation.append({
                    'AttributePath': 'nickName',
                    'AttributeValue': user['NickName'],
                })

            if 'Enterprise' in user:
                enterprise = user['Enterprise']
                if enterprise:
                    if 'EmployeeNumber' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.employeeNumber',
                            'AttributeValue': enterprise['EmployeeNumber'],
                        })
                    if 'CostCenter' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.costCenter',
                            'AttributeValue': enterprise['CostCenter'],
                        })
                    if 'Organization' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.organization',
                            'AttributeValue': enterprise['Organization'],
                        })
                    if 'Division' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.division',
                            'AttributeValue': enterprise['Division'],
                        })
                    if 'Department' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.department',
                            'AttributeValue': enterprise['Department'],
                        })
                    if 'Manager' in enterprise:
                        user_operation.append({
                            'AttributePath': 'enterprise.manager',
                            'AttributeValue': enterprise['Manager'],
                        })

            client.update_user(
                IdentityStoreId=module.params['identity_store_id'],
                UserId=user['UserId'],
                Operations=user_operation
            )
        except ClientError as e:
            module.fail_json_aws(e, msg="Failed to update user")


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
    argument_spec = {
        "identity_store_id": {"type": "str", "required": True},
        "user_name": {"type": "str", "required": True},
        "name": {
            "type": "dict",
            "required": True,
            "options": {
                "formatted": {"type": "str", "required": True},
                "family_name": {"type": "str", "required": True},
                "given_name": {"type": "str", "required": True},
            }
        },
        "display_name": {"type": "str", "required": True},
        "emails": {
            "type": "list",
            "required": True,
            "elements": "dict",
            "options": {
                "value": {"type": "str", "required": True},
                "type": {"type": "str", "required": True},
                "primary": {"type": "bool", "required": True},
            }
        },
        "nick_name": {"type": "str", "required": False},
        "enterprise": {
            "type": "dict",
            "required": False,
            "options": {
                "employee_number": { "type": "str", "required": False},
                "cost_center": { "type": "str", "required": False},
                "organization": { "type": "str", "required": False},
                "division": { "type": "str", "required": False},
                "department": { "type": "str", "required": False},
                "manager": { "type": "str", "required": False}
            }
        },
        "user_type": {
            "type": "str",
            "default": "DEVELOPER",
            "choices": ["DEVELOPER", "SUPPORT", "OPERATIONS", "SYSTEM_ADMINISTRATOR", "CEO", "CFO", "CTO",
                        "TEAM_LEAD", "SALES", "MARKETING", "PRODUCT_MANAGER",
                        "ENGINEERING_MANAGER", "DATA_ANALYST"],
            "required": False
        },
        "addresses": {
            "type": "list",
            "required": False,
            "elements": "dict",
            "options": {
                "street_address": {"type": "str", "required": False},
                "locality": {"type": "str", "required": False},
                "region": {"type": "str", "required": False},
                "postal_code": {"type": "str", "required": False},
                "country": {"type": "str", "required": False},
                "formatted": {"type": "str", "required": False},
                "type": {"type": "str", "required": False},
                "primary": {"type": "bool", "required": False},
            }
        },
        "phone_numbers": {
            "type": "list",
            "required": False,
            "elements": "dict",
            "options": {
                "value": {"type": "str", "required": False},
                "type": {"type": "str", "required": False},
                "primary": {"type": "bool", "required": False},
            }
        },
        "title": {"type": "str", "required": False},
        "locale": {"type": "str", "required": False},
        "timezone": {"type": "str", "required": False},
        "preferred_language": {"type": "str", "required": False},
        "state": {
            "type": "str",
            "default": "present",
            "choices": ["present", "absent"]
        },
        "wait": {"type": "bool", "default": False, "required": False},
        "wait_timeout": {"type": "int", "default": 300, "required": False}
    }

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    identifier_problem = validate_iam_identifiers(
        "user", name=module.params.get("user_name")
    )

    if identifier_problem:
        module.fail_json(message=identifier_problem)

    # Initialize identitystore client using AnsibleAWSModule's boto3 client
    try:
        connection = module.client('identitystore')

        if module.params['state'] == 'present':
            create_or_update_user(connection, module)
        else:
            delete_user(connection, module)
    except ClientError as e:
        module.fail_json_aws(e, msg=f"An error occurred: {str(e)}")


if __name__ == '__main__':
    main()
