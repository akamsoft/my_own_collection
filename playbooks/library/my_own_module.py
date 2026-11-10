#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, alex
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_own_module

short_description: Create a file with the specified content

version_added: "1.0.0"

description:
  - Creates a text file at the given path with the given content.
  - Idempotent - if the file already exists with the same content, no change is made.

options:
    path:
        description: Absolute path to the file to create.
        required: true
        type: str
    content:
        description: Content to write into the file.
        required: false
        type: str
        default: ''

author:
    - alex (@akamsoft)
'''

EXAMPLES = r'''
- name: Create file with content
  akamsoft.my_own_collection.my_own_module:
    path: /tmp/example.txt
    content: |
      Hello, World!

- name: Create an empty file
  akamsoft.my_own_collection.my_own_module:
    path: /tmp/empty.txt
'''

RETURN = r'''
path:
    description: Path of the managed file.
    type: str
    returned: always
    sample: /tmp/example.txt
changed:
    description: Whether the file was created or modified.
    type: bool
    returned: always
    sample: true
message:
    description: Human-readable status message.
    type: str
    returned: always
    sample: File /tmp/example.txt created
'''

import os

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        path=dict(type='str', required=True),
        content=dict(type='str', required=False, default=''),
    )

    result = dict(
        changed=False,
        path='',
        message='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    path = module.params['path']
    content = module.params['content']
    result['path'] = path

    file_exists = os.path.exists(path)
    current_content = None
    if file_exists:
        with open(path, 'r', encoding='utf-8') as f:
            current_content = f.read()

    if file_exists and current_content == content:
        result['message'] = 'File {0} already exists with the same content'.format(path)
        module.exit_json(**result)

    result['changed'] = True
    result['message'] = (
        'File {0} updated'.format(path) if file_exists
        else 'File {0} created'.format(path)
    )

    # In check mode we report what would happen, but don't touch the disk
    if module.check_mode:
        module.exit_json(**result)

    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()