#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, alex (@akamsoft)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: yc_instance

short_description: Manage Yandex Cloud compute instances via yc CLI

version_added: "1.1.0"

description:
  - Creates or deletes Yandex Cloud VM instances using the C(yc) CLI.
  - Idempotent by instance name.
  - Supports check mode.

options:
    name:
        description: Name of the instance.
        required: true
        type: str
    state:
        description: Desired state of the instance.
        required: false
        type: str
        default: present
        choices: [present, absent]
    zone:
        description: Availability zone.
        required: false
        type: str
        default: ru-central1-a
    folder_id:
        description: Folder ID. If omitted, the current yc config folder is used.
        required: false
        type: str
    cores:
        description: Number of vCPUs.
        required: false
        type: int
        default: 2
    memory:
        description: RAM size in GB.
        required: false
        type: int
        default: 2
    image_family:
        description: Image family for the boot disk.
        required: false
        type: str
        default: ubuntu-2204-lts
    disk_size:
        description: Boot disk size in GB (minimum 8).
        required: false
        type: int
        default: 10
    public_ip:
        description: Assign a public IP address.
        required: false
        type: bool
        default: false
    ssh_key:
        description: Path to a public SSH key file to authorise for user yc-user.
        required: false
        type: str
    platform_id:
        description: Platform ID.
        required: false
        type: str
        default: standard-v3

author:
    - alex (@akamsoft)
'''

EXAMPLES = r'''
- name: Create a VM with public IP
  akamsoft.yandex_cloud_elk.yc_instance:
    name: clickhouse-01
    zone: ru-central1-a
    cores: 2
    memory: 4
    disk_size: 20
    public_ip: true
    ssh_key: ~/.ssh/id_ed25519.pub

- name: Delete a VM
  akamsoft.yandex_cloud_elk.yc_instance:
    name: clickhouse-01
    state: absent
'''

RETURN = r'''
name:
    description: Instance name.
    type: str
    returned: always
    sample: clickhouse-01
id:
    description: Instance ID (when present).
    type: str
    returned: when state=present and instance exists
    sample: fhm1234567890abcdef
ip:
    description: Public IP address of the instance (when present).
    type: str
    returned: when state=present and instance has public IP
    sample: 51.250.1.2
changed:
    description: Whether the instance was created or deleted.
    type: bool
    returned: always
    sample: true
message:
    description: Human-readable status message.
    type: str
    returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule


def _yc_cmd(module, args, check_rc=False):
    """Run a yc command and return (rc, stdout, stderr)."""
    cmd = ['yc'] + args
    rc, out, err = module.run_command(cmd, check_rc=check_rc)
    return rc, out.strip(), err.strip()


def _instance_exists(module, name, folder_id):
    """Return (exists, instance_dict_or_None)."""
    args = ['compute', 'instance', 'get', name, '--format', 'json']
    if folder_id:
        args += ['--folder-id', folder_id]
    rc, out, err = _yc_cmd(module, args)
    if rc != 0:
        return False, None
    try:
        data = json.loads(out)
    except Exception:
        return False, None
    return True, data


def _instance_id(module, name, folder_id):
    exists, data = _instance_exists(module, name, folder_id)
    if not exists or not data:
        return None
    return data.get('id')


def _extract_ip(instance):
    """Extract public IP from a yc instance dict."""
    if not instance:
        return None
    nis = instance.get('network_interfaces') or []
    if not nis:
        return None
    primary = nis[0].get('primary_v4_address') or {}
    nat = primary.get('one_to_one_nat') or {}
    return nat.get('address')


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        zone=dict(type='str', default='ru-central1-a'),
        folder_id=dict(type='str', required=False, default=None),
        cores=dict(type='int', default=2),
        memory=dict(type='int', default=2),
        image_family=dict(type='str', default='ubuntu-2204-lts'),
        disk_size=dict(type='int', default=10),
        public_ip=dict(type='bool', default=False),
        ssh_key=dict(type='str', required=False, default=None),
        platform_id=dict(type='str', default='standard-v3'),
    )

    result = dict(
        changed=False,
        name='',
        id=None,
        ip=None,
        message='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    zone = module.params['zone']
    folder_id = module.params['folder_id']
    cores = module.params['cores']
    memory = module.params['memory']
    image_family = module.params['image_family']
    disk_size = module.params['disk_size']
    public_ip = module.params['public_ip']
    ssh_key = module.params['ssh_key']
    platform_id = module.params['platform_id']

    result['name'] = name

    exists, instance = _instance_exists(module, name, folder_id)

    # ---- state=absent ----
    if state == 'absent':
        if not exists:
            result['message'] = 'Instance {0} already absent'.format(name)
            module.exit_json(**result)

        result['changed'] = True
        result['message'] = 'Instance {0} would be deleted'.format(name)
        if module.check_mode:
            module.exit_json(**result)

        args = ['compute', 'instance', 'delete', name]
        if folder_id:
            args += ['--folder-id', folder_id]
        rc, out, err = _yc_cmd(module, args, check_rc=True)
        result['message'] = 'Instance {0} deleted'.format(name)
        module.exit_json(**result)

    # ---- state=present ----
    if exists:
        result['id'] = instance.get('id') if instance else None
        result['ip'] = _extract_ip(instance)
        result['message'] = 'Instance {0} already exists'.format(name)
        module.exit_json(**result)

    # need to create
    result['changed'] = True
    result['message'] = 'Instance {0} would be created'.format(name)
    if module.check_mode:
        module.exit_json(**result)

    args = [
        'compute', 'instance', 'create',
        '--name', name,
        '--zone', zone,
        '--platform-id', platform_id,
        '--cores', str(cores),
        '--memory', '{0}G'.format(memory),
        '--create-boot-disk',
        'image-folder-id=standard-images,image-family={0},size={1}G'.format(image_family, disk_size),
    ]

    if public_ip:
        args += ['--public-ip']

    if ssh_key:
        args += ['--ssh-key', ssh_key]

    if folder_id:
        args += ['--folder-id', folder_id]

    rc, out, err = _yc_cmd(module, args, check_rc=True)

    # after creation, try to fetch ID and IP
    _, new_instance = _instance_exists(module, name, folder_id)
    result['id'] = new_instance.get('id') if new_instance else None
    result['ip'] = _extract_ip(new_instance)
    result['message'] = 'Instance {0} created'.format(name)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()