#!/usr/bin/env python3

__author__ = "Igor Royzis"
__copyright__ = "Copyright 2023, Kinect Consulting"
__license__ = "Commercial"
__email__ = "iroyzis@kinect-consulting.com"

import logging
import os
import pprint

from boto3.dynamodb.conditions import Attr

logger = logging.getLogger("server")
logger.setLevel(logging.INFO)


def example_data():
    return [{"name": "example"}]


def example_vpc_2():
    return [{
        "type": "Theia::Option",
        "label": "Yes",
        "value": "true"
    }, {
        "type": "Theia::Option",
        "label": "No",
        "value": "false"
    }]


def pp(d):
    if 'RAPIDCLOUD_TEST_MODE_AWS_REDSHIFT' in os.environ and os.environ.get(
            'RAPIDCLOUD_TEST_MODE_AWS_REDSHIFT') == "true":
        print(pprint.pformat(d))


def module_redshift_subnets(boto3_session, user_session, params):
    metadata_dict = module_redshift_metadata(boto3_session, user_session, 'create_subnet', 'net')
    aws_dict = {}
    output_list = []
    ec2_client = boto3_session.client('ec2')

    try:
        f = [{'Name': 'tag:profile', 'Values': [user_session['env']]}]
        r = ec2_client.describe_subnets(Filters=f)
        for subnet in r['Subnets']:
            for tag in subnet['Tags']:
                if tag['Key'] == 'fqn':
                    aws_dict[tag['Value']] = subnet['SubnetId']
    except Exception as e:
        print(e)

    for fqn, subnet_name in metadata_dict.items():
        output_dict = {}
        label = f"{subnet_name} (not deployed yet)"
        if fqn in aws_dict.keys():
            label = f"{subnet_name} ({aws_dict[fqn]})"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = subnet_name
        output_dict['value']['disableControls'] = ["vpc_id"]
        output_list.append(output_dict)
    return output_list


def module_redshift_metadata(boto3_session, user_session, cmd, phase):
    # this is a generic function, it queries the aws_infra tables and filters results
    # based on "cmd"
    # when we create subnets, we give the user the option to create a route table
    # with the subnet OR use an existing subnet.
    # when we list route tables from our metadata we pass the `create_subnet` cmd
    # which means that some subnets will end up listed in the route table drop down
    # when `route_tables`is set to True we only include subnets if the `create_route_table`
    # is set to true
    metadata_dict = {}
    d = boto3_session.resource('dynamodb')
    try:
        cmdfilter = Attr('profile').eq(user_session["env"]) & Attr('command').eq(cmd) & Attr('phase').eq(phase)
        t = d.Table('aws_infra')
        r = t.scan(FilterExpression=cmdfilter)
        for i in r['Items']:
            metadata_dict[i['fqn']] = i['resource_name']

        while 'LastEvaluatedKey' in r:
            r = t.scan(FilterExpression=cmdfilter, ExclusiveStartKey=r['LastEvaluatedKey'])
            for i in r['Items']:
                metadata_dict[i['fqn']] = i['resource_name']
    except Exception as e:
        print(e)
    sorted_metadata_tuple = sorted(metadata_dict.items(), key=lambda x: x[1])
    sorted_metadata_dict = {k: v for k, v in sorted_metadata_tuple}
    return sorted_metadata_dict


def module_redshift_vpcs(boto3_session, user_session, params):
    metadata_dict = module_redshift_metadata(boto3_session, user_session, 'create_vpc', 'net')
    aws_dict = {}
    output_list = []
    ec2_client = boto3_session.client('ec2')

    try:
        f = [{'Name': 'tag:profile', 'Values': [user_session['env']]}]
        r = ec2_client.describe_vpcs(Filters=f)
        for vpc in r['Vpcs']:
            for tag in vpc['Tags']:
                if tag['Key'] == 'fqn':
                    aws_dict[tag['Value']] = vpc['VpcId']
    except Exception as e:
        print(e)

    for fqn, vpc_name in metadata_dict.items():
        output_dict = {}
        label = f"{vpc_name} (not deployed yet)"
        if fqn in aws_dict.keys():
            label = f"{vpc_name} ({aws_dict[fqn]})"
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = label
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = vpc_name
        output_list.append(output_dict)
    return output_list


def module_redshift_rpus(boto3_session, user_session, params):
    output_list = []
    output_dict = {}
    output_dict['value'] = {}
    output_dict['type'] = "Theia::Option"
    output_dict['label'] = params['capacity']
    output_dict['value']['type'] = "Theia::DataOption"
    output_dict['value']['value'] = params['capacity']
    output_list.append(output_dict)

    rpus_list = [8 * i for i in range(1, 65)]
    for rpu in rpus_list:
        output_dict = {}
        output_dict['value'] = {}
        output_dict['type'] = "Theia::Option"
        output_dict['label'] = rpu
        output_dict['value']['type'] = "Theia::DataOption"
        output_dict['value']['value'] = rpu
        output_list.append(output_dict)
    return output_list


def module_redshift_buckets(boto3_session, user_session, params):
    metadata_dict = module_redshift_metadata(boto3_session, user_session, 'create', 'redshift')
    metadata_dict.update(module_redshift_metadata(boto3_session, user_session, 'create_serverless', 'redshift'))
    output_list = []
    output_dict = {}

    for k, v in metadata_dict.items():
        if 'redshift_serverless' in k:
            output_dict = {}
            output_dict['value'] = {}
            output_dict['type'] = "Theia::Option"
            output_dict['label'] = f"Serverless: {v}"
            output_dict['value']['type'] = "Theia::DataOption"
            output_dict['value']['value'] = f"redshift-serverless-{v}-mgmt-lambda"
            output_list.append(output_dict)
        elif 'redshift_cluster' in k:
            output_dict = {}
            output_dict['value'] = {}
            output_dict['type'] = "Theia::Option"
            output_dict['label'] = f"Cluster: {v}"
            output_dict['value']['type'] = "Theia::DataOption"
            output_dict['value']['value'] = f"redshift-cluster-{v}-mgmt-lambda"
            output_list.append(output_dict)
    return output_list


def custom_endpoint(action, params, boto3_session, user_session):
    if action == "example":
        return example_data()
    elif action == "module_redshift_subnets":
        return module_redshift_subnets(boto3_session, user_session, params)
    elif action == "module_redshift_vpcs":
        return module_redshift_vpcs(boto3_session, user_session, params)
    elif action == "module_redshift_rpus":
        return module_redshift_rpus(boto3_session, user_session, params)
    elif action == "module_redshift_buckets":
        return module_redshift_buckets(boto3_session, user_session, params)
    else:
        return ["no such endpoint"]

    return []
