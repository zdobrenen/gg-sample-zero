ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))


# Project Installation
install: install-virtualenv install-requirements install-custom-sdk


install-virtualenv:
	sudo pip install virtualenv && virtualenv $(ROOT_DIR)/venv


install-requirements:
	$(ROOT_DIR)/venv/bin/pip install -r $(ROOT_DIR)/requirements.txt


install-custom-sdk:
	cd $(ROOT_DIR)/ggc_custom_sdk && $(ROOT_DIR)/venv/bin/pip install .



# Project Commands
create-group:
	$(ROOT_DIR)/venv/bin/python ggc_groups_ste/groups/$(GROUP)/commands.py create_group


delete-group:
	$(ROOT_DIR)/venv/bin/python ggc_groups_ste/groups/$(GROUP)/commands.py delete_group


update-group:
	$(ROOT_DIR)/venv/bin/python ggc_groups_ste/groups/$(GROUP)/commands.py update_group


config-group:
	$(ROOT_DIR)/venv/bin/ansible-playbook -i $(pi_host), ggc_groups_ste/groups/$(GROUP)/playbook.yml -e "ansible_user=$(pi_user) ansible_ssh_pass=$(pi_pass) ansible_sudo_pass=$(pi_pass)"


deploy-group:
	$(ROOT_DIR)/venv/bin/python ggc_groups_ste/groups/$(GROUP)/commands.py deploy_group


deploy-device:
	$(ROOT_DIR)/venv/bin/ansible-playbook -i $(pi_host), ggc_groups_ste/device/$(GROUP)/$(DEVICE)/playbook.yml -e "ansible_user=$(pi_user) ansible_ssh_pass=$(pi_pass) ansible_sudo_pass=$(pi_pass)"
