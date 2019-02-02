import boto3
import fire
import logging
import json
import os
import sys
import pprint
import shutil
import datetime
import time
import requests

from botocore.exceptions import ClientError

from policy import (gen_group_role_doc, gen_group_policy_doc, gen_core_policy_doc,
                    gen_device_policy_doc, gen_lambda_role_doc, gen_lambda_policy_doc)


logging.basicConfig(
    format='%(asctime)s|%(name).10s|%(levelname).5s: %(message)s',
    level=logging.WARNING
)

log = logging.getLogger('ggc_custom_sdk')
log.setLevel(logging.DEBUG)



def boto_scrub(resp):

    resp = resp.copy()

    resp.pop('ResponseMetadata', None)
    resp.pop('certificatePem', None)
    resp.pop('keyPair', None)

    for k, v in resp.iteritems():
        if type(v) == datetime.datetime:
            resp[k] = unicode(v.replace(microsecond=0))

    return resp


def state_scrub(state_obj={}):

    for k, v in state_obj.iteritems():
        if type(v) == dict:
            state_obj[k] = state_scrub(v)
        else:
            if type(v) == list:
                state_obj[k] = []
            else:
                state_obj[k] = ''

    return state_obj



class GroupCommands(object):


    def __init__(self, group={}):
        super(GroupCommands, self).__init__()

        s = boto3.session.Session()
        if not s.region_name:
            log.error(
                "AWS credentials and region must be setup."
            )
            sys.exit(-1)
        else:
            log.info(
                "AWS credentials found for region '{}'".format(
                s.region_name
            ))

        self.__init_magic()

        self._region       = s.region_name
        self._gg           = s.client('greengrass')
        self._iot          = s.client('iot')
        self._iot_endpoint = self._iot.describe_endpoint()['endpointAddress']
        self._lambda       = s.client('lambda')
        self._iam          = s.client('iam')
        self._s3           = s.client('s3')

        self.group         = self.__load_defin()
        self.state         = self.__load_state()


    #*************************
    # Begin Public Methods
    #*************************

    def create_group(self):

        if not self.state.get('Group'):
            self.state['Group'] = {}

        try:
            group_defs = [g for g in self._gg.list_groups()['Groups']
                if g.get('Name') == self.group['Group']['Name']]

            if not len(group_defs) == 0:
                log.warn('GG Group already exist')

                self.state['Group'] = boto_scrub(group_defs[0])
                log.info('Retrieved GG Group')

                role_name   = '{}-role'.format(self.state['Group']['Name'])
                policy_name = '{}-policy'.format(role_name)

                group_role = self._iam.get_role(
                    RoleName=role_name
                )

                if not self.state.get('Roles'):
                    self.state['Roles'] = {}

                log.info('Retrieved GG Group role')
                self.state['Roles']['Group'] = boto_scrub(group_role['Role'])

            else:
                log.info('GG Group does not exist')

                role_name   = '{}-role'.format(self.group['Group']['Name'])
                policy_name = '{}-policy'.format(role_name)

                try:
                    group_role = self._iam.create_role(
                        RoleName=role_name,
                        AssumeRolePolicyDocument=gen_group_role_doc()
                    )
                    log.info('Created GG Group role')

                    if not self.state.get('Roles'):
                        self.state['Roles'] = {}

                    self.state['Roles']['Group'] = boto_scrub(group_role['Role'])

                    self._iam.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=gen_group_policy_doc(self._region)
                    )
                    log.info('Created GG Group role policy')
                except Exception as e:
                    log.error('Create GG Group role unexpected error', exc_info=True)

                group = self._gg.create_group(
                    Name=self.group['Group']['Name']
                )
                log.info('Created GG Group')
                self.state['Group'].update(boto_scrub(group))

                self._gg.associate_role_to_group(
                    GroupId=self.state['Group']['Id'],
                    RoleArn=self.state['Roles']['Group']['Arn']
                )
                log.info('Associated Role to GG Group')

        except ClientError as e:
            log.error('Create GG Group unexpected client error', exc_info=True)

        else:
            self.__create_cores()
            self.__create_resources()
            self.__create_lambdas()
            self.__attach_lambdas()
            self.__create_devices()
            self.__create_subscriptions()
            self.__create_version()

        finally:
            self.__save_state()


    def delete_group(self):

        try:
            group_defs = [g for g in self._gg.list_groups()['Groups']
                if g.get('Name') == self.state['Group']['Name']]

            if not len(group_defs) == 1:
                log.error('GG Group does not exist')

            else:
                log.info('GG Group found')

                self.state['Group'] = boto_scrub(group_defs[0])
                log.info('Retrieved GG Group')

                self._gg.reset_deployments(
                    GroupId=self.state['Group']['Id'],
                    Force=True
                )
                log.info('Reset GG Group deployment')

                if self.state['Roles'].get('Group', {}).get('RoleName'):
                    role_name   = self.state['Roles']['Group']['RoleName']
                    policy_name = '{}-policy'.format(role_name)

                    self._iam.delete_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                    log.info('Deleted GG Group role policy')

                    self._iam.delete_role(
                        RoleName=role_name
                    )
                    log.info('Deleted GG Group role')
                    self.state['Roles']['Group'] = state_scrub(self.state['Roles']['Group'])

                self._gg.delete_group(
                    GroupId=self.state['Group']['Id']
                )
                log.info('Deleted GG Group')
                self.state['Group']        = state_scrub(self.state['Group'])

                if self.state.get('GroupVersion'):
                    self.state['GroupVersion'] = state_scrub(self.state['GroupVersion'])

                if self.state.get('Deployment'):
                    self.state['Deployment']   = state_scrub(self.state['Deployment'])
        except ClientError as e:
            log.error('Delete GG Group unexpected client error', exc_info=True)

        else:
            self.__delete_cores()
            self.__delete_resources()
            self.__detach_lambdas()
            self.__delete_lambdas()
            self.__delete_devices()
            self.__delete_subscriptions()

        finally:
            self.__save_state()


    def update_group(self):
        raise NotImplementedError()


    def deploy_group(self):

        if not self.state.get('Deployment'):
            self.state['Deployment'] = {}

        try:
            deploy = self._gg.create_deployment(
                GroupId=self.state['Group']['Id'],
                GroupVersionId=self.state['GroupVersion']['Version'],
                DeploymentType='NewDeployment'
            )
            log.info('Deploying GG Group')
            self.state['Deployment'].update(boto_scrub(deploy))

        except ClientError as e:
            log.error('Deploy GG Group unexpected client error', exc_info=True)

        finally:
            self.__save_state()


    #*************************
    # Begin Private Methods
    #*************************

    def __create_version(self):

        try:
            args = {
                'GroupId': \
                    self.state.get('Group', {}).get('Id', ''),
                'CoreDefinitionVersionArn': \
                    self.state.get('CoreDefinition', {}).get('LatestVersionArn', ''),
                'FunctionDefinitionVersionArn': \
                    self.state.get('FunctionDefinition', {}).get('LatestVersionArn', ''),
                'ResourceDefinitionVersionArn': \
                    self.state.get('ResourceDefinition', {}).get('LatestVersionArn', ''),
                'SubscriptionDefinitionVersionArn': \
                    self.state.get('SubscriptionDefinition', {}).get('LatestVersionArn', ''),
                'DeviceDefinitionVersionArn': \
                    self.state.get('DeviceDefinition', {}).get('LatestVersionArn', '')
            }
            args = {k: v for k, v in args.iteritems() if v}

            version = self._gg.create_group_version(**args)
            log.info('Creating GG Group version')
            self.state['GroupVersion'] = boto_scrub(version)

        except ClientError as e:
            log.error('Create GG Group version unexpected error', exc_info=True)

        finally:
            self.__save_state()


    def __create_cores(self):

        if not self.state.get('Cores'):
            self.state['Cores'] = {}

        try:
            core_defs = [c for c in self._gg.list_core_definitions()['Definitions']
                if c.get('Name') == self.group['Cores']['Name']]

            if not len(core_defs) == 0:
                log.error('GG Core Definition already exists')

                self.state['Cores']['Name'] = self.group['Cores']['Name']
                log.info('Set GG Core name')

                self.state['CoreDefinition'] = boto_scrub(core_defs[0])
                log.info('Retrieved GG Core Definition')

                core_version = self._gg.get_core_definition_version(
                    CoreDefinitionId=self.state['CoreDefinition']['Id'],
                    CoreDefinitionVersionId=self.state['CoreDefinition']['LatestVersion']
                )
                log.info('Retrieved GG Core Definition version')
                self.state['CoreDefinition']['LatestVersionDetails'] = boto_scrub(core_version)

                self.__gather_core_certs()
                self.__gather_core_thing()
                self.__gather_core_policy()
                self.__create_core_config()

            else:
                self.state['Cores']['Name'] = self.group['Cores']['Name']
                log.info('Set GG Core name')

                self.__create_core_certs()
                self.__create_core_thing()
                self.__create_core_policy()
                self.__create_core_config()

                cores = [{
                    'CertificateArn': self.state['Cores']['Certs']['certificateArn'],
                    'Id': self.state['Cores']['Name'],
                    'SyncShadow': self.group['Cores']['SyncShadow'],
                    'ThingArn': self.state['Cores']['Thing']['thingArn']
                }]

                core_defin  = self._gg.create_core_definition(
                    InitialVersion={
                        'Cores': cores
                    },
                    Name=self.state['Cores']['Name']
                )
                log.info('Created GG Core Definition')
                self.state['CoreDefinition'] = boto_scrub(core_defin)

                core_version = self._gg.create_core_definition_version(
                    CoreDefinitionId=self.state['CoreDefinition']['Id'],
                    Cores=cores
                )
                log.info('Created GG Core Definition version')
                self.state['CoreDefinition']['LatestVersionDetails'] = boto_scrub(core_version)

        except ClientError as e:
            log.error('Create GG Core unexpected client error', exc_info=True)

        else:
            return self.state['CoreDefinition']['Arn']

        finally:
            self.__save_state()


    def __delete_cores(self):

        try:
            if self.state.get('CoreDefinition', {}) \
                and self.state['CoreDefinition']['Name']:

                self.__delete_core_certs()
                self.__delete_core_thing()
                self.__delete_core_policy()

                core_defs = [c for c in self._gg.list_core_definitions()['Definitions']
                    if c.get('Name') == self.state['CoreDefinition']['Name']]

                if not len(core_defs) == 1:
                    log.error('GG Core Definition does not exist')

                else:
                    self.state['CoreDefinition'] = boto_scrub(core_defs[0])
                    log.info('Retrieved GG Core Definition')

                    self._gg.delete_core_definition(
                        CoreDefinitionId=self.state['CoreDefinition']['Id']
                    )
                    log.info('Deleted GG Core definition')
                    self.state['CoreDefinition'] = state_scrub(self.state['CoreDefinition'])

            self.state['Cores'] = state_scrub(self.state['Cores'])

        except ClientError as e:
            log.error('Delete GG Core definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __create_core_certs(self):

        try:
            keys_certs = self._iot.create_keys_and_certificate(
                setAsActive=True
            )
            log.info('Created core keys/certs')
            self.state['Cores']['Certs'] = boto_scrub(keys_certs)

            root_certs = requests.get('http://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem')
            log.info('Retrieved root keys/certs')

        except ClientError as e:
            log.error('Create core keys/certs unexpected client error', exc_info=True)

        else:
            self.__save_keys_certs(self.CERTS_PATH, self.state['Cores']['Name'], keys_certs)
            self.__save_keys_certs(self.CERTS_PATH, 'root.ca.pem', root_certs.text)

            return self.state['Cores']['Certs']['certificateArn']

        finally:
            self.__save_state()


    def __delete_core_certs(self):

        try:
            if self.state.get('Cores', {}).get('Policy') \
                and self.state['Cores']['Certs']['certificateArn'] \
                and self.state['Cores']['Policy']['policyName']:

                self._iot.detach_policy(
                    policyName=self.state['Cores']['Policy']['policyName'],
                    target=self.state['Cores']['Certs']['certificateArn']
                )
                log.info('Detached core policy')


            if self.state.get('Cores', {}).get('Thing') \
                and self.state['Cores']['Certs']['certificateArn'] \
                and self.state['Cores']['Thing']['thingName']:

                self._iot.detach_thing_principal(
                    thingName=self.state['Cores']['Thing']['thingName'],
                    principal=self.state['Cores']['Certs']['certificateArn']
                )
                log.info('Detached core thing principal')

            if self.state.get('Cores', {}).get('Certs') \
                and self.state['Cores']['Certs']['certificateId']:

                self._iot.update_certificate(
                    certificateId=self.state['Cores']['Certs']['certificateId'],
                    newStatus='INACTIVE'
                )
                log.info('Deactivated core certs')

                self._iot.delete_certificate(
                    certificateId=self.state['Cores']['Certs']['certificateId'],
                    forceDelete=True
                )
                log.info('Deleted core key/certs')
                self.state['Cores']['Certs'] = state_scrub(self.state['Cores']['Certs'])

        except ClientError as e:
            log.error('Deleting core key/certs unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_core_certs(self):

        try:
            core_certs = [c for c in self._iot.list_certificates()['certificates']
                if c.get('certificateArn') == \
                self.state['CoreDefinition']['LatestVersionDetails']['Definition']['Cores'][0]['CertificateArn']]

            log.info('Retrieved GG Core certs')
            self.state['Cores']['Certs'] = boto_scrub(core_certs[0])

        except ClientError as e:
            log.error('Retrieve GG Core certs unexpected client error', exc_info=True)

        finally:
            self.__save_state()


    def __create_core_thing(self):

        try:
            core_thing = self._iot.create_thing(
                thingName=self.group['Cores']['Name']
            )
            log.info('Created core thing')
            self.state['Cores']['Thing'] = boto_scrub(core_thing)

            self._iot.attach_thing_principal(
                thingName=self.group['Cores']['Name'],
                principal=self.state['Cores']['Certs']['certificateArn']
            )
            log.info('Attached core thing principal')

        except ClientError as e:
            log.error('Creating core thing unexpected client error', exc_info=True)

        else:
            return self.state['Cores']['Thing']['thingArn']

        finally:
            self.__save_state()


    def __delete_core_thing(self):

        try:
            if self.state.get('Cores', {}).get('Thing') \
                and self.state['Cores']['Thing']['thingName']:

                self._iot.delete_thing(
                    thingName=self.state['Cores']['Thing']['thingName']
                )
                log.info('Deleted core thing')
                self.state['Cores']['Thing'] = state_scrub(self.state['Cores']['Thing'])

        except ClientError as e:
            log.error('Deleting core thing unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_core_thing(self):

        try:
            core_thing = [t for t in self._iot.list_things()['things']
                if t.get('thingArn') == \
                self.state['CoreDefinition']['LatestVersionDetails']['Definition']['Cores'][0]['ThingArn']]

            log.info('Retrieved GG Core thing')
            self.state['Cores']['Thing'] = boto_scrub(core_thing[0])

        except ClientError as e:
            log.error('Retrieve GG Core thing unexpected error', exc_info=True)

        finally:
            self.__save_state()


    def __create_core_policy(self):

        try:
            core_policy = self._iot.create_policy(
                policyName='{}-policy'.format(self.group['Cores']['Name']),
                policyDocument=gen_core_policy_doc(self._region)
            )
            log.info('Creating core policy')
            self.state['Cores']['Policy'] = boto_scrub(core_policy)

            self._iot.attach_principal_policy(
                policyName='{}-policy'.format(self.group['Cores']['Name']),
                principal=self.state['Cores']['Certs']['certificateArn']
            )

        except ClientError as e:
            log.error('Create core policy unexpected client error', exc_info=True)

        else:
            return self.state['Cores']['Policy']['policyArn']

        finally:
            self.__save_state()


    def __delete_core_policy(self):

        try:
            if self.state.get('Cores', {}).get('Policy') \
                and self.state['Cores']['Policy']['policyName']:

                self._iot.delete_policy(
                    policyName=self.state['Cores']['Policy']['policyName']
                )
                log.info('Deleted core policy')
                self.state['Cores']['Policy'] = state_scrub(self.state['Cores']['Policy'])

        except ClientError as e:
            log.error('Deleting core policy unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_core_policy(self):

        try:
            core_policy = self._iot.get_policy(
                policyName='{}-policy'.format(self.state['Cores']['Name'])
            )
            log.info('Retrieved GG Core policy')
            self.state['Cores']['Policy'] = boto_scrub(core_policy)

        except ClientError as e:
            log.error('Retrieve GG Core policy unexpected client error', exc_info=True)

        finally:
            self.__save_state()


    def __create_core_config(self):
		config = {
			"coreThing": {
				"caPath": "root.ca.pem",
				"certPath": "{}.cert.pem".format(self.state['Cores']['Name']),
				"keyPath": "{}.private.key".format(self.state['Cores']['Name']),
				"thingArn": self.state['Cores']['Thing']['thingArn'],
				"iotHost": self._iot_endpoint,
				"ggHost": "greengrass.iot." + self._region + ".amazonaws.com",
				"keepAlive": 600
			},
			"runtime": {
				"cgroup": {
					"useSystemd": "yes"
				}
			},
			"managedRespawn": False
		}
		with open('{}/config.json'.format(self.CONFG_PATH), 'w') as f:
			json.dump(config, f, indent=4, separators=(',', ' : '))


    def __create_lambdas(self):

        if not self.state.get('Lambdas'):
            self.state['Lambdas'] = {}

        if not self.state.get('Roles'):
            self.state['Roles'] = {}

        if not self.state['Roles'].get('Lambdas'):
            self.state['Roles']['Lambdas'] = {}


        for key, core_lambda in self.group['Lambdas'].iteritems():

            try:
                self._lambda.get_function(
                    FunctionName=core_lambda['FunctionName']
                )

            except self._lambda.exceptions.ResourceNotFoundException as e:
                log.info('Lambda Function does not exist')

                role_name   = '{}-role'.format(core_lambda['FunctionName'])
                policy_name = '{}-policy'.format(role_name)

                lambda_role = self._iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=gen_lambda_role_doc()
                )
                log.info('Created Lambda Function role')
                self.state['Roles']['Lambdas'][core_lambda['FunctionName']] = boto_scrub(lambda_role['Role'])

                self._iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=gen_lambda_policy_doc(self._region)
                )
                log.info('Created Lambda Function role policy')

                log.info('Packaging Lambda Function for upload')
                zip_file = shutil.make_archive(
                    os.path.join(self.ARCHS_PATH, core_lambda['FunctionName']),
                    'zip',
                    os.path.join(self.LAMBD_PATH, core_lambda['Package'])
                )
                log.info('Created Lambda Function zip package')

                RETRIES = 5
                while RETRIES > 0:
                    try:
                        with open(zip_file, 'rb') as f:
                            lambda_func = self._lambda.create_function(
                                FunctionName=core_lambda['FunctionName'],
                                Runtime=core_lambda['Runtime'],
                                Role=self.state['Roles']['Lambdas'][core_lambda['FunctionName']]['Arn'],
                                Handler=core_lambda['Handler'],
                                Code=dict(ZipFile=f.read()),
                                Publish=True
                            )
                            break

                    except ClientError as e:
                        log.warn('Lamdba Function role has not propagated. retrying')
                        if RETRIES > 0:
                            RETRIES = RETRIES - 1
                            time.sleep(10)
                        else:
                            raise

                log.info('Uploaded Lambda Function zip package')
                self.state['Lambdas'][core_lambda['FunctionName']] = boto_scrub(lambda_func)

                lambda_alias = self._lambda.create_alias(
                    FunctionName=core_lambda['FunctionName'],
                    Name=core_lambda['Alias'],
                    FunctionVersion=self.state['Lambdas'][core_lambda['FunctionName']]['Version']
                )
                log.info('Create Lambda Function alias')
                self.state['Lambdas'][core_lambda['FunctionName']]['Alias'] = boto_scrub(lambda_alias)

            else:
                log.info('Lambda Function already exists')

                lambda_func = self._lambda.get_function(
                    FunctionName=core_lambda['FunctionName']
                )
                log.info('Retrieved GG Core Lambda Function')
                self.state['Lambdas'][core_lambda['FunctionName']] = boto_scrub(lambda_func['Configuration'])

                lambda_alias = self._lambda.get_alias(
                    FunctionName=core_lambda['FunctionName'],
                    Name=core_lambda['Alias']
                )
                log.info('Retrieved GG Core Lambda Function alias retrieved')
                self.state['Lambdas'][core_lambda['FunctionName']]['Alias'] = boto_scrub(lambda_alias)

                lambda_role = self._iam.get_role(
                    RoleName='{}-role'.format(core_lambda['FunctionName'])
                )
                log.info('Retrieved GG Core Lambda Function role')
                self.state['Roles']['Lambdas'][core_lambda['FunctionName']] = boto_scrub(lambda_role['Role'])

            finally:
                self.__save_state()


    def __delete_lambdas(self):

        for key, core_lambda in self.state.get('Lambdas', {}).copy().iteritems():

            try:
                self._lambda.delete_function(
                    FunctionName=core_lambda['FunctionName']
                )
                log.info('Deleted Lambda Function')
                self.state['Lambdas'].pop(core_lambda['FunctionName'])

                self._iam.delete_role_policy(
                    RoleName='{}-role'.format(core_lambda['FunctionName']),
                    PolicyName='{}-role-policy'.format(core_lambda['FunctionName'])
                )
                log.info('Deleted Lambda Function role policy')

                self._iam.delete_role(
                    RoleName='{}-role'.format(core_lambda['FunctionName'])
                )
                log.info('Deleted Lambda Function role')
                self.state['Roles']['Lambdas'].pop(core_lambda['FunctionName'])

            except ClientError as e:
                log.error('Delete Lambda Function unexpected client error', exc_info=True)

            finally:
                self.__save_state()


    def __attach_lambdas(self):

        def functions():
            funcs = []
            for key, core_lambda in self.state['Lambdas'].iteritems():
                func_tmp = {}

                func_tmp.update({
                    'FunctionArn': core_lambda['Alias']['AliasArn'],
                    'Id': core_lambda['FunctionName']
                })

                func_tmp.update({
                    'FunctionConfiguration': self.group['Lambdas'][key]['Configuration']
                })

                funcs.append(func_tmp)
            return funcs

        try:
            func_defs = [f for f in self._gg.list_function_definitions()['Definitions']
                if f.get('Name') == self.state['Group']['Name']]

            if not len(func_defs) == 0:
                log.info('GG Function Definition already exists')

                self.state['FunctionDefinition'] = boto_scrub(func_defs[0])
                log.info('Retrieved GG Function Definition')

                func_version = self._gg.get_function_definition_version(
                    FunctionDefinitionId=self.state['FunctionDefinition']['Id'],
                    FunctionDefinitionVersionId=self.state['FunctionDefinition']['LatestVersion']
                )
                log.info('Retrieved GG Function Definition version')
                self.state['FunctionDefinition']['LatestVersionDetails'] = boto_scrub(func_version)

            else:
                func_def = self._gg.create_function_definition(
                    InitialVersion={
                        'Functions': functions()
                    },
                    Name=self.state['Group']['Name']
                )
                log.info('Created GG Function Definition', exc_info=True)
                self.state['FunctionDefinition'] = boto_scrub(func_def)

                func_version = self._gg.create_function_definition_version(
                    FunctionDefinitionId=self.state['FunctionDefinition']['Id'],
                    Functions=functions()
                )
                log.info('Created GG Function Definition version')
                self.state['FunctionDefinition']['LatestVersionDetails'] = boto_scrub(func_version)

        except ClientError as e:
            log.error('Create GG Function Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __detach_lambdas(self):

        try:
            if self.state.get('FunctionDefinition', {}) \
                and self.state['FunctionDefinition']['Name']:

                func_defs = [f for f in self._gg.list_function_definitions()['Definitions']
                    if f.get('Name') == self.state['FunctionDefinition']['Name']]

                if not len(func_defs) == 1:
                    log.error('GG Function Definition does not exist')

                else:
                    self.state['FunctionDefinition'] = boto_scrub(func_defs[0])
                    log.info('Retrieved GG Function Definition')

                    self._gg.delete_function_definition(
                        FunctionDefinitionId=self.state['FunctionDefinition']['Id']
                    )
                    log.info('Deleted GG Function Definition')
                    self.state['FunctionDefinition'] = state_scrub(self.state['FunctionDefinition'])

        except ClientError as e:
            log.error('Delete GG Function Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __create_resources(self):

        def resources():
            return [rsrc for k, rsrc in self.group['Resources'].iteritems()]

        try:
            rsrc_defs = [r for r in self._gg.list_resource_definitions()['Definitions']
                if r.get('Name') == self.state['Group']['Name']]

            if not len(rsrc_defs) == 0:
                log.info('GG Core Resource Definition already exists')

                self.state['ResourceDefinition'] = boto_scrub(rsrc_defs[0])
                log.info('Retrieved GG Resource Definition')

                rsrc_version = self._gg.get_resource_definition_version(
                    ResourceDefinitionId=self.state['ResourceDefinition']['Id'],
                    ResourceDefinitionVersionId=self.state['ResourceDefinition']['LatestVersion']
                )
                log.info('Retrieved GG Resource Definition version')
                self.state['ResourceDefinition']['LatestVersionDetails'] = boto_scrub(rsrc_version)

            else:

                rsrc_def = self._gg.create_resource_definition(
                    InitialVersion={
                        'Resources': resources()
                    },
                    Name=self.state['Group']['Name']
                )
                log.info('Created GG Core resource definition')
                self.state['ResourceDefinition'] = boto_scrub(rsrc_def)

                rsrc_version = self._gg.create_resource_definition_version(
                    ResourceDefinitionId=self.state['ResourceDefinition']['Id'],
                    Resources=resources()
                )
                log.info('Created GG Core resource definition version')
                self.state['ResourceDefinition']['LatestVersionDetails'] = boto_scrub(rsrc_version)

        except ClientError as e:
            log.error('Creating GG Core resource definition unexpected error', exc_info=True)

        finally:
            self.__save_state()


    def __delete_resources(self):

        try:
            if self.state.get('ResourceDefinition', {}) \
                and self.state['ResourceDefinition']['Name']:

                rsrc_defs = [r for r in self._gg.list_resource_definitions()['Definitions']
                    if r.get('Name') == self.state['ResourceDefinition']['Name']]

                if not len(rsrc_defs) == 1:
                    log.error('GG Resource Definition does not exist')

                else:
                    self.state['ResourceDefinition'] = boto_scrub(rsrc_defs[0])
                    log.info('Retrieved GG Resource Definition')

                    self._gg.delete_resource_definition(
                        ResourceDefinitionId=self.state['ResourceDefinition']['Id']
                    )
                    log.info('Deleted GG Resource Definition')
                    self.state['ResourceDefinition'] = state_scrub(self.state['ResourceDefinition'])

        except ClientError as e:
            log.error('Delete GG Resource Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __create_subscriptions(self):

        def subscriptions():
            subs = []
            for key, core_subscripts in self.group['Subscriptions'].iteritems():
                subs_tmp = {}

                subs_tmp.update({
                    'Id': core_subscripts['Id'],
                    'Subject': core_subscripts['Subject']
                })

                if core_subscripts['Source'] == 'cloud' \
                    or core_subscripts['Source'] == 'GGShadowService':

                    subs_tmp.update({
                        'Source': core_subscripts['Source']
                    })

                elif 'Lambda::' in core_subscripts['Source']:
                    function_name = core_subscripts['Source'].split('::')[-1]
                    subs_tmp.update({
                        'Source': self.state['Lambdas'][function_name]['Alias']['AliasArn']
                    })

                elif 'Device::' in core_subscripts['Source']:
                    device_name = core_subscripts['Source'].split('::')[-1]
                    subs_tmp.update({
                        'Source': self.state['Devices'][device_name]['Thing']['thingArn']
                    })


                if core_subscripts['Target'] == 'cloud' \
                    or core_subscripts['Target'] == 'GGShadowService':

                    subs_tmp.update({
                        'Target': core_subscripts['Target']
                    })

                elif 'Lambda::' in core_subscripts['Target']:
                    function_name = core_subscripts['Target'].split('::')[-1]
                    subs_tmp.update({
                        'Target': self.state['Lambdas'][function_name]['Alias']['AliasArn']
                    })

                elif 'Device::' in core_subscripts['Target']:
                    device_name = core_subscripts['Target'].split('::')[-1]
                    subs_tmp.update({
                        'Target': self.state['Devices'][device_name]['Thing']['thingArn']
                    })

                subs.append(subs_tmp)
            return subs

        try:
            subs_defs = [s for s in self._gg.list_subscription_definitions()['Definitions']
                if s.get('Name') == self.state['Group']['Name']]

            if not len(subs_defs) == 0:
                log.info('GG Subscription Definition already exist')

                self.state['SubscriptionDefinition'] = boto_scrub(subs_defs[0])
                log.info('Retrieved GG Subscription Definition')

                subs_version = self._gg.get_subscription_definition_version(
                    SubscriptionDefinitionId=self.state['SubscriptionDefinition']['Id'],
                    SubscriptionDefinitionVersionId=self.state['SubscriptionDefinition']['LatestVersion']
                )
                log.info('Retrieved GG Subscription Definition version')
                self.state['SubscriptionDefinition']['LatestVersionDetails'] = boto_scrub(subs_version)

            else:
                subs_def = self._gg.create_subscription_definition(
                    InitialVersion={
                        'Subscriptions': subscriptions()
                    },
                    Name=self.state['Group']['Name']
                )
                log.info('Created GG Subscription Definition', exc_info=True)
                self.state['SubscriptionDefinition'] = boto_scrub(subs_def)

                subs_version = self._gg.create_subscription_definition_version(
                    SubscriptionDefinitionId=self.state['SubscriptionDefinition']['Id'],
                    Subscriptions=subscriptions()
                )
                log.info('Created GG Subscription Definition version')
                self.state['SubscriptionDefinition']['LatestVersionDetails'] = boto_scrub(subs_version)

        except ClientError as e:
            log.error('Attaching GG Subscription Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __delete_subscriptions(self):

        try:
            if self.state.get('SubscriptionDefinition', {}) \
                and self.state['SubscriptionDefinition']['Name']:

                subs_defs = [s for s in self._gg.list_subscription_definitions()['Definitions']
                    if s.get('Name') == self.state['SubscriptionDefinition']['Name']]

                if not len(subs_defs) == 1:
                    log.error('GG Subscription Definition does not exist')

                else:
                    self.state['SubscriptionDefinition'] = boto_scrub(subs_defs[0])
                    log.info('Retrieved GG Subscription Definition')

                    self._gg.delete_subscription_definition(
                        SubscriptionDefinitionId=self.state['SubscriptionDefinition']['Id']
                    )
                    log.info('Deleted GG Subscription Definition')
                    self.state['SubscriptionDefinition'] = state_scrub(self.state['SubscriptionDefinition'])

        except ClientError as e:
            log.error('Delete GG Subscription Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __create_devices(self):

        if not self.state.get('Devices'):
            self.state['Devices'] = {}

        def create_devices():
            devices = []

            for k, device in self.group['Devices'].iteritems():
                self.state['Devices'][device['Id']] = {}
                self.state['Devices'][device['Id']]['Id'] = device['Id']

                certs_arn  = self.__create_device_certs(device)
                thing_arn  = self.__create_device_thing(device)
                policy_arn = self.__create_device_policy(device)

                devices.append({
                    'CertificateArn': certs_arn,
                    'Id': device['Id'],
                    'SyncShadow': device['SyncShadow'],
                    'ThingArn': thing_arn
                })

            return devices

        try:
            dvce_defs = [d for d in self._gg.list_device_definitions()['Definitions']
                if d.get('Name') == self.state['Group']['Name']]

            if not len(dvce_defs) == 0:
                log.error('GG Device Definition already exists')

                self.state['DeviceDefinition'] = boto_scrub(dvce_defs[0])
                log.info('Retrieved GG Device Definition')

                dvce_version = self._gg.get_device_definition_version(
                    DeviceDefinitionId=self.state['DeviceDefinition']['Id'],
                    DeviceDefinitionVersionId=self.state['DeviceDefinition']['LatestVersion']
                )
                log.info('Retrieved GG Device Definition version')
                self.state['DeviceDefinition']['LatestVersionDetails'] = boto_scrub(dvce_version)

                for device in self.state['DeviceDefinition']['LatestVersionDetails']['Definition']['Devices']:

                    if not self.state['Devices'].get(device['Id']):
                        self.state['Devices'][device['Id']] = {}

                    self.__gather_device_certs(device)
                    self.__gather_device_thing(device)
                    self.__gather_device_policy(device)

            else:
                devices = create_devices()

                dvce_defin  = self._gg.create_device_definition(
                    InitialVersion={
                        'Devices': devices
                    },
                    Name=self.state['Group']['Name']
                )
                log.info('Created GG Device Definition')
                self.state['DeviceDefinition'] = boto_scrub(dvce_defin)

                dvce_version = self._gg.create_device_definition_version(
                    DeviceDefinitionId=self.state['DeviceDefinition']['Id'],
                    Devices=devices
                )
                log.info('Created GG Device Definition version')
                self.state['DeviceDefinition']['LatestVersionDetails'] = boto_scrub(dvce_version)

        except ClientError as e:
            log.error('Create GG Device unexpected client error', exc_info=True)

        else:
            return self.state['DeviceDefinition']['Arn']

        finally:
            self.__save_state()


    def __delete_devices(self):

        try:
            if self.state.get('DeviceDefinition', {}) \
                and self.state['DeviceDefinition']['Name']:

                devices = self.state['DeviceDefinition']['LatestVersionDetails'].get('Definition', {}).get('Devices', [])

                if not devices:
                    devices = self.state['Devices']

                for device in devices:

                    if type(device) == basestring or type(device) == unicode:
                        device = self.state['Devices'].get(device)

                    self.__delete_device_certs(device)
                    self.__delete_device_thing(device)
                    self.__delete_device_policy(device)

                dvce_defs = [d for d in self._gg.list_device_definitions()['Definitions']
                    if d.get('Name') == self.state['DeviceDefinition']['Name']]

                if not len(dvce_defs) == 1:
                    log.error('GG Device Definition does not exist')

                else:
                    self.state['DeviceDefinition'] = boto_scrub(dvce_defs[0])
                    log.info('Retrieved GG Device Definition')

                    self._gg.delete_device_definition(
                        DeviceDefinitionId=self.state['DeviceDefinition']['Id']
                    )
                    log.info('Deleted GG Device Definition')
                    self.state['DeviceDefinition'] = state_scrub(self.state['DeviceDefinition'])

            if self.state.get('Devices'):
                self.state['Devices'] = state_scrub(self.state['Devices'])

        except ClientError as e:
            log.error('Delete GG Device Definition unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __create_device_certs(self, device):

        try:
            keys_certs = self._iot.create_keys_and_certificate(
                setAsActive=True
            )
            log.info('Created GG Device keys/certs')
            self.state['Devices'][device['Id']]['Certs'] = boto_scrub(keys_certs)

        except ClientError as e:
            log.error('Create GG Device keys/certs unexpected client error', exc_info=True)

        else:
            self.__save_keys_certs(self.CERTS_PATH, device['Id'], keys_certs)
            return keys_certs['certificateArn']

        finally:
            self.__save_state()


    def __delete_device_certs(self, device):

        try:
            if self.state.get('Devices', {}).get(device['Id'], {}).get('Policy') \
                and self.state['Devices'][device['Id']]['Certs']['certificateArn'] \
                and self.state['Devices'][device['Id']]['Policy']['policyName']:

                self._iot.detach_policy(
                    policyName=self.state['Devices'][device['Id']]['Policy']['policyName'],
                    target=self.state['Devices'][device['Id']]['Certs']['certificateArn']
                )
                log.info('Detached GG Device Certs policy')


            if self.state.get('Devices', {}).get(device['Id'], {}).get('Thing') \
                and self.state['Devices'][device['Id']]['Certs']['certificateArn'] \
                and self.state['Devices'][device['Id']]['Thing']['thingName']:

                self._iot.detach_thing_principal(
                    thingName=self.state['Devices'][device['Id']]['Thing']['thingName'],
                    principal=self.state['Devices'][device['Id']]['Certs']['certificateArn']
                )
                log.info('Detached GG Device Thing principal')

            if self.state.get('Devices', {}).get(device['Id'], {}).get('Certs') \
                and self.state['Devices'][device['Id']]['Certs']['certificateId']:

                self._iot.update_certificate(
                    certificateId=self.state['Devices'][device['Id']]['Certs']['certificateId'],
                    newStatus='INACTIVE'
                )
                log.info('Deactivated GG Device Certs')

                self._iot.delete_certificate(
                    certificateId=self.state['Devices'][device['Id']]['Certs']['certificateId'],
                    forceDelete=True
                )
                log.info('Deleted GG Device Certs')
                self.state['Devices'][device['Id']]['Certs'] = state_scrub(
                    self.state['Devices'][device['Id']]['Certs']
                )

        except ClientError as e:
            log.error('Deleting GG Device Certs unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_device_certs(self, device):

        try:
            dvce_certs = [c for c in self._iot.list_certificates()['certificates']
                if c.get('certificateArn') in device['CertificateArn']]

            log.info('Retrieved GG Device Certs')
            self.state['Devices'][device['Id']]['Certs'] = boto_scrub(dvce_certs[0])

        except ClientError as e:
            log.error('Retrieve GG Device Certs unexpected client error', exc_info=True)

        finally:
            self.__save_state()


    def __create_device_thing(self, device):

        try:
            dvce_thing = self._iot.create_thing(
                thingName=device['Id']
            )
            log.info('Created GG Device Thing')
            self.state['Devices'][device['Id']]['Thing'] = boto_scrub(dvce_thing)

            self._iot.attach_thing_principal(
                thingName=device['Id'],
                principal=self.state['Devices'][device['Id']]['Certs']['certificateArn']
            )
            log.info('Attached GG Device Thing principal')

        except ClientError as e:
            log.error('Create GG Device Thing unexpected client error', exc_info=True)

        else:
            return dvce_thing['thingArn']

        finally:
            self.__save_state()


    def __delete_device_thing(self, device):

        try:
            if self.state.get('Devices', {}).get(device['Id'], {}).get('Thing') \
                and self.state['Devices'][device['Id']]['Thing']['thingName']:

                self._iot.delete_thing(
                    thingName=self.state['Devices'][device['Id']]['Thing']['thingName']
                )
                log.info('Deleted GG Device Thing')
                self.state['Devices'][device['Id']]['Thing'] = state_scrub(
                    self.state['Devices'][device['Id']]['Thing'])

        except ClientError as e:
            log.error('Deleting GG Device Thing unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_device_thing(self, device):

        try:
            dvce_thing = [t for t in self._iot.list_things()['things']
                if t.get('thingArn') == device['ThingArn']]

            log.info('Retrieved GG Device Thing')
            self.state['Devices'][device['Id']]['Thing'] = boto_scrub(dvce_thing[0])

        except ClientError as e:
            log.error('Retrieve GG Device Thing unexpected error', exc_info=True)

        finally:
            self.__save_state()


    def __create_device_policy(self, device):

        try:
            dvce_policy = self._iot.create_policy(
                policyName='{}-policy'.format(device['Id']),
                policyDocument=gen_device_policy_doc(self._region)
            )
            log.info('Created GG Device Policy')
            self.state['Devices'][device['Id']]['Policy'] = boto_scrub(dvce_policy)

            self._iot.attach_principal_policy(
                policyName='{}-policy'.format(device['Id']),
                principal=self.state['Devices'][device['Id']]['Certs']['certificateArn']
            )
            log.info('Attached GG Device Policy to Certs')

        except ClientError as e:
            log.error('Create GG Device Policy unexpected client error', exc_info=True)

        else:
            return dvce_policy['policyArn']

        finally:
            self.__save_state()


    def __delete_device_policy(self, device):

        try:
            if self.state.get('Devices', {}).get(device['Id'], {}).get('Policy') \
                and self.state['Devices'][device['Id']]['Policy']['policyName']:

                self._iot.delete_policy(
                    policyName=self.state['Devices'][device['Id']]['Policy']['policyName']
                )
                log.info('Deleted GG Device policy')
                self.state['Devices'][device['Id']]['Policy'] = state_scrub(
                    self.state['Devices'][device['Id']]['Policy'])

        except ClientError as e:
            log.error('Deleting GG Device Policy unexpected client error', exc_info=True)
            sys.exit(-1)

        finally:
            self.__save_state()


    def __gather_device_policy(self, device):

        try:
            dvce_policy = self._iot.get_policy(
                policyName='{}-policy'.format(device['Id'])
            )
            log.info('Retrieved GG Device Policy')
            self.state['Devices'][device['Id']]['Policy'] = boto_scrub(dvce_policy)

        except ClientError as e:
            log.error('Retrieve GG Device Policy unexpected client error', exc_info=True)

        finally:
            self.__save_state()


    #*************************
    # Begin Utility Methods
    #*************************

    def __init_magic(self):
        self.DEFIN_FILE = '{}/{}'.format(self.GROUP_PATH, 'config.json')
        self.LAMBD_PATH = '{}/{}'.format(self.GROUP_PATH, '../..')

        self.MAGIC_PATH = '{}/{}'.format(self.GROUP_PATH, '.gg')
        self.CERTS_PATH = '{}/{}'.format(self.MAGIC_PATH, 'certs')
        self.CONFG_PATH = '{}/{}'.format(self.MAGIC_PATH, 'config')
        self.ARCHS_PATH = '{}/{}'.format(self.MAGIC_PATH, 'archives')
        self.STATE_FILE = '{}/{}'.format(self.MAGIC_PATH, 'state.json')


        if not os.path.isfile(self.DEFIN_FILE):
            log.error('GG Group config.json file not found')
            sys.exit(-1)

        if not os.path.isdir(os.path.join(self.LAMBD_PATH, 'lambda')):
            log.error('Lambda source dir not found')
            sys.exit(-1)

        if not os.path.isdir(self.MAGIC_PATH):
            log.info('Created GG Group magic dir')
            os.makedirs(self.MAGIC_PATH)

        if not os.path.isdir(self.CERTS_PATH):
            log.info('Created GG Group certs dir')
            os.makedirs(self.CERTS_PATH)

        if not os.path.isdir(self.CONFG_PATH):
            log.info('Created GG Group config dir')
            os.makedirs(self.CONFG_PATH)

        if not os.path.isdir(self.ARCHS_PATH):
            log.info('Created GG Group archives dir')
            os.makedirs(self.ARCHS_PATH)


    def __load_defin(self):

        try:
            with open(self.DEFIN_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            log.error('Failed to load definition file')
        else:
            log.info('Loaded definition file')


    def __load_state(self):

        if not os.path.exists(self.STATE_FILE):
            log.warn('State file not found. Assume new group')
            return {}

        try:
            with open(self.STATE_FILE, 'r') as f:
                log.info('State file loaded')
                return json.load(f)
        except Exception as e:
            log.error('State file failed to load', exc_info=True)


    def __save_state(self):

        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=4, sort_keys=True)
        except Exception as e:
            log.error('State file failed to save', exc_info=True)
        else:
            log.info('State file saved')


    def __save_keys_certs(self, dest_path, name, keys_certs):

        try:
            if type(keys_certs) == unicode:
                with open('{}/{}'.format(dest_path, name), 'w') as f:
                    f.write(keys_certs)

            if keys_certs.get('certificatePem'):
                with open('{}/{}.cert.pem'.format(dest_path, name), 'w') as f:
                    f.write(keys_certs['certificatePem'])

            if keys_certs.get('keyPair', {}).get('PublicKey'):
                with open('{}/{}.public.key'.format(dest_path, name), 'w') as f:
                    f.write(keys_certs['keyPair']['PublicKey'])

            if keys_certs.get('keyPair', {}).get('PrivateKey'):
                with open('{}/{}.private.key'.format(dest_path, name), 'w') as f:
                    f.write(keys_certs['keyPair']['PrivateKey'])

            if keys_certs.get('PemEncodedCertificate'):
                with open('{}/{}'.format(dest_path, name), 'w') as f:
                    f.write(keys_certs['PemEncodedCertificate'])

            log.info('AWS IoT Keys and Certs saved')

        except Exception as e:
            log.error('AWS IoT keys/certs unexpected error saving')
