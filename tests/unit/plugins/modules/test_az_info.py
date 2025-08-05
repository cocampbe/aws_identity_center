import pytest
from unittest.mock import MagicMock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.begoingto.aws_identity_center.plugins.modules import az_info

class MockAnsibleModule:
    def __init__(self, argument_spec):
        self.params = {}
        self.check_mode = False

    def fail_json(self, **kwargs):
        raise Exception(kwargs.get('msg', 'Failed'))

    def exit_json(self, **kwargs):
        return kwargs

@pytest.fixture
def mock_sso_client():
    client = MagicMock()
    client.list_permission_sets.return_value = {
        'PermissionSets': [
            {'Name': 'AdminAccess', 'PermissionSetArn': 'arn:aws:sso:::permissionSet/ssoins-1234567890/ps-123'}
        ]
    }
    return client

def test_az_info_get_sso_resources(mock_sso_client):
    module_args = {
        "region": "us-east-1",
        "instance_arn": "arn:aws:sso:::instance/ssoins-1234567890"
    }
    mock_module = MockAnsibleModule(argument_spec={})
    mock_module.params = module_args

    az_info.get_boto3_client = MagicMock(return_value=mock_sso_client)
    result = az_info.main()

    assert result['changed'] is False
    assert len(result['permission_sets']) == 1
    assert result['permission_sets'][0]['Name'] == 'AdminAccess'

def test_az_info_missing_required_params():
    mock_module = MockAnsibleModule(argument_spec={})
    mock_module.params = {}

    with pytest.raises(Exception, match="missing required arguments"):
        az_info.main()