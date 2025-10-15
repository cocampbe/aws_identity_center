# Ansible Collection - begoingto.aws_identity_center

The Ansible AWS collection has modules focused on managing items in IAM Identity Center.

## Description

The primary purpose of this collection is add modules that can manage items in AWS IAM Identity Center. Currently there are not any officials modules for creating user, group, permissions sets, etc in IAM Identity Center.

## Requirements

- Ansible version >= 2.19.0 (This is the only version I have tested on)
- AWS SWK (boto3 and botocore). This has been tested with python 3.12

## Installation

The first step is to clone the repo. After that, you can install it into your project directory using the following command.

```sh
ansible-galaxy collection install /path/to/clone/aws_identity_center/ -p ./collections
```
