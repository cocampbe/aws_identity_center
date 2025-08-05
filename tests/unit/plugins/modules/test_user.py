from unittest.mock import MagicMock
import pytest
import ansible_collections.begoingto.aws_identity_center.plugins.modules.user as user_module
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)


@pytest.fixture(name="ansible_begoingto_module")
def fixture_ansible_begoingto_module():
    module = MagicMock()
    module.params = {
        "identity_store_id": "test-identity-store-id",
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

    if "UserName" not in to_skip:
        assert "UserName" in user_obj
        assert user_obj["UserName"] == "test-user"

    if "GivenName" not in to_skip:
        assert "GivenName" in user_obj
        assert user_obj["GivenName"] == "Test"

    if "FamilyName" not in to_skip:
        assert "FamilyName" in user_obj
        assert user_obj["FamilyName"] == "User"

    if "DisplayName" not in to_skip:
        assert "DisplayName" in user_obj
        assert user_obj["DisplayName"] == "Test User"  # Module sets this to "given_name family_name" if empty

    if "Emails" not in to_skip:
        assert "Emails" in user_obj
        assert user_obj["Emails"] == [{"Value": "test.user@example.com", "Primary": True}]

    if "IdentityStoreId" not in to_skip:
        assert "IdentityStoreId" in user_obj
        assert user_obj["IdentityStoreId"] == "test-identity-store-id"


def test_get_user(ansible_begoingto_module, aws_identity_center_user_module):
    """Test retrieving an existing user (state=present, user exists)."""
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

    aws_identity_center_user_module.run_module(client, ansible_begoingto_module)

    result = ansible_begoingto_module.exit_json.call_args[1]

    print("\n")
    print(result)

    assert result == {
        "changed": False,
        "user_id": "test-user-id",
        "message": "User test-user already exists"
    }

    # client.list_users.assert_called_once_with(
    #     IdentityStoreId="test-identity-store-id",
    #     Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
    # )
    # client.create_user.assert_not_called()
    # client.update_user.assert_not_called()
    # client.delete_user.assert_not_called()
    #
    # # Verify the user specification
    # user_spec = client.list_users.return_value["Users"][0]
    # _assert_defaults(user_spec)

def test_create_user(ansible_begoingto_module, aws_identity_center_user_module):
    """Test creating a new user (state=present, user does not exist)."""
    client = MagicMock()
    client.list_users.return_value = {"Users": []}
    client.create_user.return_value = {"UserId": "test-user-id"}

    aws_identity_center_user_module.run_module(client, ansible_begoingto_module)

    result = ansible_begoingto_module.exit_json.call_args[1]

    print("\n")
    print(result)

    assert result == {
        "changed": True,
        "user_id": "test-user-id",
        "message": "User test-user created successfully"
    }
#     client.list_users.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         Filters=[{"AttributePath": "UserName", "AttributeValue": "test-user"}]
#     )
#     client.create_user.assert_called_once_with(
#         IdentityStoreId="test-identity-store-id",
#         UserName="test-user",
#         Name={"GivenName": "Test", "FamilyName": "User"},
#         DisplayName="Test User",
#         Emails=[{"Value": "test.user@example.com", "Primary": True}]
#     )
#     client.update_user.assert_not_called()
#     client.delete_user.assert_not_called()
#
#     # Verify the user specification passed to create_user
#     user_spec = client.create_user.call_args[1]
#     user_spec["GivenName"] = user_spec["Name"]["GivenName"]
#     user_spec["FamilyName"] = user_spec["Name"]["FamilyName"]
#     user_spec["Emails"] = [{"Value": email["Value"], "Primary": True} for email in user_spec["Emails"]]
#     _assert_defaults(user_spec)
#
#
# def test_update_user(ansible_begoingto_module, aws_identity_center_user_module):
#     """Test updating an existing user (state=present, user exists, different attributes)."""
#     ansible_begoingto_module.params["given_name"] = "UpdatedTest"  # Simulate a change
#     ansible_begoingto_module.params["email"] = "updated.user@example.com"
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
#     client.update_user.return_value = {}
#
#     result = aws_identity_center_user_module.run_module(client, ansible_begoingto_module)
#
#     assert result == {
#         "changed": True,
#         "user_id": "test-user-id",
#         "message": "User test-user updated successfully"
#     }
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