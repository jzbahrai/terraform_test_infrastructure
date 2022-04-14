import base64
import boto3
import json
from os import environ

ecs = boto3.client("ecs")
ssm = boto3.client("ssm")
servicediscovery = boto3.client('servicediscovery')

account_list = ssm.get_parameter(Name='asset_inventory_account_list', WithDecryption=True)['Parameter']['Value'].split("\n")

def handler(event, context): 
  instance_list = []
  response = servicediscovery.list_services()
  for service in response['Services']:
    if service['Name'] == "neo4j":
      li_response = servicediscovery.list_instances(ServiceId=service['Id'])
      for instance in li_response['Instances']:
        if instance['Attributes']['AWS_INIT_HEALTH_STATUS'] == 'HEALTHY':
          instance_list.append(instance['Attributes']['AWS_INSTANCE_IPV4'])

  aws_profile_template = "[profile {account_id}]\nrole_arn = arn:aws:iam::{account_id}:role/AssetInventorySecurityAuditRole\nsource_profile = default\nregion = ca-central-1\noutput = json\n\n"
  for account_id in account_list:
    response = ecs.run_task(
        taskDefinition='cartography',
        launchType='FARGATE',
        cluster='cartography',
        platformVersion='LATEST',
        count=1,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': environ.get("CARTOGRAPHY_ECS_NETWORKING").split(","),
                'securityGroups': [environ.get("CARTOGRAPHY_ECS_SECURITY_GROUPS")]
            }
        },
        overrides={
          'containerOverrides': [
            {
              "name" : "cartography",
              'environment': [
                  {
                    'name': 'AWS_ACCOUNT',
                    'value': account_id
                  },
                  {
                    'name': 'AWS_CONFIG_FILE',
                    'value': '/config/role_config'
                  },
                  {
                    "name" : "NEO4J_URI",
                    "value" : f"bolt://{instance_list.pop()}:7687"
                  },
                  {
                    "name" : "NEO4J_USER",
                    "value" : "neo4j"
                  },
                  {
                    "name" : "AWS_PROFILE_DATA",
                    "value" : base64.b64encode(aws_profile_template.format(account_id=account_id).encode('ascii')).decode('ascii')
                  },
              ],
            }
          ]
        }
    )