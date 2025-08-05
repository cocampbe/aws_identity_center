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
        "user_id": "test-user-id",
        "user_name": "test-user",
        "given_name": "Test",
        "family_name": "User",
        "display_name": "",
        "email": "test.user@example.com",
        "state": "present",
        "region": "us-east-1"
    }
    module.check_mode = False
    module.fail_json_aws = MagicMock()
    module.exit_json = MagicMock()
    return module


@pytest.fixture(name="aws_identity_center_user_module")
def fixture_user(monkeypatch):
    return user_module

def _assert_defaults(user_obj, to_skip=None):
    if not to_skip:
        to_skip = []

    assert isinstance(user_obj, dict)

    assert user_obj["IdentityStoreId"] == "test-identity-store-id"
    if "UserName" in user_obj:
        assert user_obj["UserName"] == "test-user"
    if "Name" in user_obj:
        if "Formatted" in user_obj["Name"]:
            assert user_obj["Name"]["Formatted"] == "Test User"
        if "FamilyName" in user_obj["Name"]:
            assert user_obj["Name"]["FamilyName"] == "User"
        if "GivenName" in user_obj["Name"]:
            assert user_obj["Name"]["GivenName"] == "Test"
        if "MiddleName" in user_obj["Name"]:
            assert user_obj["Name"]["MiddleName"] == "Middle"
        if "HonorificPrefix" in user_obj["Name"]:
            assert user_obj["Name"]["HonorificPrefix"] == "Mr."
        if "HonorificSuffix" in user_obj["Name"]:
            assert user_obj["Name"]["HonorificSuffix"] == "Jr."

    if "DisplayName" in user_obj:
        assert user_obj["DisplayName"] == "Test User"
    if "NickName" in user_obj:
       assert user_obj["NickName"] == "Tester"
    if "ProfileUrl" in user_obj:
        assert user_obj["ProfileUrl"] == "https://example.com/profile/test-user"

    assert user_obj["Emails"] == [{
        "Value": "test.user@example.com",
        "Type": "work",
        "Primary": True
    }]
    if "Addresses" in user_obj:
        assert user_obj["Addresses"] == [{
            "StreetAddress": "123 Main St",
            "Locality": "Anytown",
            "Region": "Anystate",
            "PostalCode": "12345",
            "Country": "USA",
            "Formatted": "123 Main St, Anytown, Anystate, 12345, USA",
            "Type": "work",
            "Primary": True
        }]

    if "PhoneNumbers" in user_obj:
        assert user_obj["PhoneNumbers"] == [{
            "Value": "+1234567890",
            "Type": "mobile",
            "Primary": True
        }]
    if "UserId" in user_obj:
       assert user_obj["UserType"] == "employee"
    if "Title" in user_obj:
       assert user_obj["Title"] == "Engineer"
    if "PreferredLanguage" in user_obj:
       assert user_obj["PreferredLanguage"] == "en-US"
    if "Locale" in user_obj:
       assert user_obj["Locale"] == "en-US"
    if "Timezone" in user_obj:
       assert user_obj["Timezone"] == "America/New_York"

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

    aws_identity_center_user_module.run_module(client, ansible_begoingto_module)

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
    _assert_defaults(user_spec)

def test_create_user(ansible_begoingto_module, aws_identity_center_user_module):
    """Test creating a new user (state=present, user does not exist)."""
    client = MagicMock()
    client.list_users.return_value = {"Users": []}
    client.create_user.return_value = {"UserId": "test-user-id"}

    aws_identity_center_user_module.run_module(client, ansible_begoingto_module)

    result = ansible_begoingto_module.exit_json.call_args[1]

    assert result == {
        "changed": True,
        "user_id": "test-user-id",
        "message": "User test-user created successfully"
    }

    client.list_users.assert_called_once_with(
        IdentityStoreId="test-identity-store-id",
        Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
    )
    client.create_user.assert_called_once_with(
        IdentityStoreId="test-identity-store-id",
        UserName="test-user",
        Name={"GivenName": "Test", "FamilyName": "User"},
        DisplayName="Test User",
        Emails=[{"Value": "test.user@example.com", "Type": "work", "Primary": True}]
    )

    # Verify the user specification passed to create_user
    user_spec = client.create_user.call_args[1]
    user_spec["GivenName"] = user_spec["Name"]["GivenName"]
    user_spec["FamilyName"] = user_spec["Name"]["FamilyName"]
    user_spec["Emails"] = [{"Value": email["Value"], "Type": email["Type"], "Primary": True} for email in user_spec["Emails"]]
    _assert_defaults(user_spec)

def test_update_user(ansible_begoingto_module, aws_identity_center_user_module):
    ansible_begoingto_module.params["given_name"] = "UpdatedTest"  # Simulate a change
    ansible_begoingto_module.params["email"] = "updated.user@example.com"
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
    aws_identity_center_user_module.run_module(client, ansible_begoingto_module)
    result = ansible_begoingto_module.exit_json.call_args[1]
    assert result == {
        "changed": False,
        "user_id": "test-user-id",
        "message": "User test-user already exists"
    }

#     client.list_users.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
#     )
#     client.update_user.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         UserId="test-user-id",
#         Operations=[
#             {
#                 "AttributePath": "Name.GivenName",
#                 "AttributeValue": "UpdatedTest"
#             },
#             {
#                 "AttributePath": "Emails",
#                 "AttributeValue": [{"Value": "updated.user@example.com", "Primary": True}]
#             }
#         ]
#     )
#     client.create_user.assert_not_called()
#     client.delete_user.assert_not_called()
#
#     # Verify the user specification passed to update_user
#     user_spec = {
#         "UserName": "test-user",
#         "GivenName": "UpdatedTest",
#         "FamilyName": "User",
#         "DisplayName": "UpdatedTest User",
#         "Emails": [{"Value": "updated.user@example.com", "Primary": True}],
#         "IdentityStoreId": "test-identity-store-id"
#     }
#     _assert_defaults(user_spec, to_skip=["GivenName", "DisplayName", "Emails"])
#
#
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