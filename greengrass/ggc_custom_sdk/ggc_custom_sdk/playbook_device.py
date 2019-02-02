import os
import sys
import shutil

from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase

import ansible.constants as C


Options = namedtuple(
    'Options',
    [
        'connection',
        'module_path',
        'forks',
        'remote_user',
        'private_key_file',
        'ssh_common_args',
        'ssh_extra_args',
        'sftp_extra_args',
        'scp_extra_args',
        'become',
        'become_method',
        'become_user',
        'verbosity',
        'check',
        'diff'
    ]
)

options = Options(
    connection='ssh',
    module_path=['/to/mymodules'],
    forks=10,
    remote_user='pi',
    private_key_file=None,
    ssh_common_args=None,
    ssh_extra_args=None,
    sftp_extra_args=None,
    scp_extra_args=None,
    become=None,
    become_method='sudo',
    become_user='root',
    verbosity=None,
    check=False,
    diff=False
)


def exec_playbook(host_list, username, password, device_name, device_source, group_source):

    loader = DataLoader()
    passwords = dict()

    inventory_manager = InventoryManager(loader=loader, sources=','.join(host_list))
    variable_manager  = VariableManager(loader=loader, inventory=inventory_manager)

    variable_manager.extra_vars = {
        'ansible_ssh_user': username,
        'ansible_ssh_pass': password
    }

    play_source =  dict(
        name = "Greengrass Device Playbook",
        hosts = 'all',
        remote_user=username,
        gather_facts = 'yes',
        tasks = [
            dict(
                name='Set Playbook Facts',
                action=dict(
                    module='set_fact',
                    args=dict(
                        device_name=device_name,
                        device_source=device_source,
                        group_source=group_source
                    )
                )
            ),
            dict(
                name='Stop Greengrass Device (if exists)',
                become=True,
                action=dict(
                    module='systemd',
                    args=dict(
                        name=device_name,
                        state='stopped'
                    )
                ),
                ignore_errors=True
            ),
            dict(
                name='Remove Greengrass Device groupCA (if exists)',
                become=True,
                action=dict(
                    module='file',
                    args=dict(
                        path='/gg_devices/{{ device_name }}/groupCA',
                        state='absent'
                    )
                ),
                ignore_errors=True
            ),
            dict(
                name='Create Greengrass Device Directory',
                become=True,
                action=dict(
                    module='file',
                    args=dict(
                        path='/gg_devices/{{ device_name }}',
                        state='directory'
                    )
                )
            ),
            dict(
                name='Create Greengrass Certs Directory',
                become=True,
                action=dict(
                    module='file',
                    args=dict(
                        path='/greengrass/certs',
                        state='directory'
                    )
                )
            ),
            dict(
                name='Copy Greengrass Device Source',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='{{ device_source }}',
                        dest='/gg_devices/{{ device_name }}'
                    )
                )
            ),
            dict(
                name='Copy Greengrass Root Certs',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='{{ item }}',
                        dest='/greengrass/certs/'
                    )
                ),
                with_fileglob=[
                    '{{ group_source }}/.gg/certs/root.*'
                ]
            ),
            dict(
                name='Copy Greengrass Device Certs',
                become=True,
                action=dict(
                    module='copy',
                    args=dict(
                        src='{{ item }}',
                        dest='/greengrass/certs/'
                    )
                ),
                with_fileglob=[
                    '{{ group_source }}/.gg/certs/{{ device_name }}.*'
                ]
            ),
            dict(
                name='Install Base System Packages',
                become=True,
                action=dict(
                    module='apt',
                    args=dict(
                        pkg='{{ item }}',
                        update_cache=True,
                        state='present'
                    )
                ),
                with_items=[
                    'python-setuptools',
                    'python-dev',
                    'python-rpi.gpio'
                ]
            ),
            dict(
                name='Install Pip',
                become=True,
                action=dict(
                    module='easy_install',
                    args=dict(
                        name='pip'
                    )
                )
            ),
            dict(
                name='Upgrade Pip',
                become=True,
                action=dict(
                    module='command',
                    args='pip install --upgrade pip'
                )
            ),
            dict(
                name='Install Base Pip Packages',
                become=True,
                action=dict(
                    module='pip',
                    args=dict(
                        name='{{ item }}'
                    )
                ),
                with_items=[
                    'virtualenv'
                ]

            ),
            dict(
                name='Create Virtualenv',
                become=True,
                action=dict(
                    module='command',
                    args='virtualenv /gg_devices/{{ device_name }}/venv --no-site-packages'
                )
            ),
            dict(
                name='Install Virtualenv Dependencies',
                become=True,
                action=dict(
                    module='pip',
                    args=dict(
                        requirements='/gg_devices/{{ device_name }}/requirements.txt',
                        virtualenv='/gg_devices/{{ device_name }}/venv'
                    )
                )
            ),
            dict(
                name='Create Systemd Device Service',
                become=True,
                action=dict(
                    module='template',
                    args=dict(
                        src='systemd.service.j2',
                        dest='/etc/systemd/system/{{ device_name }}.service',
                        mode='0664'
                    )
                )
            ),
            dict(
                name='Start Greengrass Device',
                become=True,
                action=dict(
                    module='systemd',
                    args=dict(
                        name=device_name,
                        enabled=True,
                        state='started'
                    )
                )
            )
        ]
    )


    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = None
    try:
        tqm = TaskQueueManager(
            inventory=inventory_manager,
            variable_manager=variable_manager,
            loader=loader,
            options=options,
            passwords=passwords,
        )
        result = tqm.run(play)

    finally:

        if tqm is not None:
            tqm.cleanup()

        shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
