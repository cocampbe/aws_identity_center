from unittest.mock import MagicMock
import pytest
import plugins.modules.user as user_module
import logging

logging.basicConfig(level=logging.INFO)


@pytest.fixture(name="ansible_begoingto_module")
def fixture_ansible_begoingto_module():
    module = MagicMock()
    module.params = {
        "identity_store_id": "test-identity-store-id",
        "user_name": "begoingtNewoUx",
        "name": {
            "given_name": "BegoingNew",
            "family_name": "ToxyNew",
            "formatted": "BegoingNew ToxyNew"
        },
        "display_name": "begoingtNewoUx",
        "emails": [
            {
                "value": "begoingtoxuxxnew.me@gmail.com",
                "type": "work",
                "primary": True
            }
        ],
        "state": "present",
        "region": "us-east-1"
    }
    # module.params = {
    #     "identity_store_id": "test-identity-store-id",
    #     "user_name": "begoingto.ux",
    #     "name": {
    #         "formatted": "Begoingto UX",
    #         "family_name": "Begoingto",
    #         "given_name": "UX"
    #     },
    #     "display_name": "Begoingto UX",
    #     "emails": [
    #         {
    #             "value": "begoingto.ux@gmail.com",
    #             "type": "work",
    #             "primary": True
    #         }
    #     ],
    #     "addresses": [
    #         {
    #             "street_address": "Phnom Penh",
    #             "locality": "Anytown",
    #             "region": "KH",
    #             "postal_code": "12001",
    #             "country": "Cambodia",
    #             "formatted": "123 Main St\nAnytown, PP 12345\nCambodia",
    #             "type": "work",
    #             "primary": True
    #         }
    #     ],
    #     "phone_numbers": [],
    #     "title": "DevOps Engineer",
    #     "locale": "",
    #     "timezone": "Asia/Phnom_Penh",
    #     "state": "present",
    #     "region": "us-east-1"
    # }
    module.check_mode = False
    module.fail_json_aws = MagicMock()
    module.exit_json = MagicMock()
    return module


@pytest.fixture(name="aws_identity_center_user_module")
def fixture_user(monkeypatch):
    return user_module

def test_get_user(ansible_begoingto_module, aws_identity_center_user_module):
    """Test retrieving an existing user (state=present, user exists)."""
    client = MagicMock()
    client.list_users.return_value = {
        "Users": [
            {
                "IdentityStoreId": "test-identity-store-id",
                "UserId": "test-user-id",
                "UserName": "test-user",
                "Name": {
                    "Formatted": "Test User",
                    "FamilyName": "User",
                    "GivenName": "Test",
                    "MiddleName": "Middle",
                    "HonorificPrefix": "Mr.",
                    "HonorificSuffix": "Jr."
                },
                "DisplayName": "Test User",
                "NickName": "Tester",
                "ProfileUrl": "https://example.com/profile/test-user",
                "Emails": [
                    {
                        "Value": "test.user@example.com",
                        "Type": "work",
                        "Primary": True
                    }
                ],
                "Addresses": [
                    {
                        "StreetAddress": "123 Main St",
                        "Locality": "Anytown",
                        "Region": "Anystate",
                        "PostalCode": "12345",
                        "Country": "USA",
                        "Formatted": "123 Main St, Anytown, Anystate, 12345, USA",
                        "Type": "work",
                        "Primary": True
                    }
                ],
                "PhoneNumbers": [
                    {
                        "Value": "+1234567890",
                        "Type": "mobile",
                        "Primary": True
                    }
                ],
                "UserType": "employee",
                "Title": "Engineer",
                "PreferredLanguage": "en-US",
                "Locale": "en-US",
                "Timezone": "America/New_York"
            }
        ]
    }

    aws_identity_center_user_module.create_or_update_user(client, ansible_begoingto_module)

    result = ansible_begoingto_module.exit_json.call_args[1]

    assert result == {
        "changed": False,
        "user_id": "test-user-id",
        "message": "User test-user already exists"
    }

    client.list_users.assert_called_once_with(
        IdentityStoreId="test-identity-store-id",
        Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
    )

    # Verify the user specification
    user_spec = client.list_users.return_value["Users"][0]

def test_create_user(ansible_begoingto_module, aws_identity_center_user_module):
    """Test creating a new user (state=present, user does not exist)."""
    client = MagicMock()
    client.list_users.return_value = {"Users": []}

    # Mock describe_user to simulate user not existing
    client.describe_user.side_effect = client.exceptions.ResourceNotFoundException(
        operation_name="DescribeUser", error_response={"Message": "User not found"}
    )

    # Mock create_user to return success
    client.create_user.return_value = {"UserId": "user-123", "IdentityStoreId": "test-identity-store-id"}

    aws_identity_center_user_module.create_or_update_user(client, ansible_begoingto_module)
    result = ansible_begoingto_module.exit_json.call_args[1]
    user = result["user"]
    assert result["changed"] is True
    assert result["message"] == f"User {user['UserName']} created"
    # client.create_user.assert_called_with(
    #     IdentityStoreId="test-identity-store-id",
    #     UserName="begoingto.ux",
    #     Name={
    #         "Formatted": "Begoingto UX",
    #         "FamilyName": "Begoingto",
    #         "GivenName": "UX"
    #     },
    #     DisplayName="Begoingto UX",
    #     Emails=[{
    #         "Value": "begoingto.ux@gmail.com",
    #         "Type": "work",
    #         "Primary": True
    #     }]
    # )

def test_update_user(ansible_begoingto_module, aws_identity_center_user_module):
    ansible_begoingto_module.params["display_name"] = "TestUserUpdated"  # Simulate a change
    client = MagicMock()
    client.list_users.return_value = {
        "Users": [
            {
                "UserId": "test-user-id",
                "UserName": "test-user",
                "Name": {"GivenName": "Test", "FamilyName": "User"},
                "DisplayName": "Test User",
                "Emails": [{"Value": "test.user@example.com", "Primary": True}],
                "IdentityStoreId": "test-identity-store-id"
            }
        ]
    }
    client.update_user.return_value = {}
    aws_identity_center_user_module.create_or_update_user(client, ansible_begoingto_module)
    result = ansible_begoingto_module.exit_json.call_args[1]

    assert result["changed"] is False

# def test_delete_user(ansible_begoingto_module, aws_identity_center_user_module):
#     """Test deleting an existing user (state=absent)."""
#     ansible_begoingto_module.params["state"] = "absent"
#     client = MagicMock()
#     client.list_users.return_value = {
#         "Users": [
#             {
#                 "UserId": "test-user-id",
#                 "UserName": "test-user",
#                 "Name": {"GivenName": "Test", "FamilyName": "User"},
#                 "DisplayName": "Test User",
#                 "Emails": [{"Value": "test.user@example.com", "Primary": True}],
#                 "IdentityStoreId": "test-identity-store-id"
#             }
#         ]
#     }
#     client.delete_user.return_value = {}
#
#     result = aws_identity_center_user_module.run_module(client, ansible_begoingto_module)
#
#     assert result == {
#         "changed": True,
#         "user_id": "",
#         "message": "User test-user deleted successfully"
#     }
#     client.list_users.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
#     )
#     client.delete_user.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         UserId="test-user-id"
#     )
#     client.create_user.assert_not_called()
#     client.update_user.assert_not_called()
#
#
# def test_delete_nonexistent_user(ansible_begoingto_module, aws_identity_center_user_module):
#     """Test deleting a nonexistent user (state=absent)."""
#     ansible_begoingto_module.params["state"] = "absent"
#     client = MagicMock()
#     client.list_users.return_value = {"Users": []}
#
#     result = aws_identity_center_user_module.run_module(client, ansible_begoingto_module)
#
#     assert result == {
#         "changed": False,
#         "user_id": "",
#         "message": "User test-user does not exist"
#     }
#     client.list_users.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
#     )
#     client.delete_user.assert_not_called()
#     client.create_user.assert_not_called()
#     client.update_user.assert_not_called()