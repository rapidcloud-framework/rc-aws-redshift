__author__ = "Igor Royzis"
__copyright__ = "Copyright 2022, Kinect Consulting"
__license__ = "Commercial"
__email__ = "iroyzis@kinect-consulting.com"

import datetime
import pprint
import json
import os

from boto3.dynamodb.conditions import Attr
from commands.kc_metadata_manager.aws_metadata import Metadata
from commands.kc_metadata_manager.aws_infra import AwsInfra
from commands.kc_metadata_manager.publishing import Publishing
from commands.modules import exec_module
from data_scripts.kc_publish_redshift_ddl import RedshiftDDL


class ModuleMetadata(Metadata):

    def __init__(self, args):
        super().__init__(args)
        self.args = args

    def pp(self, v):
        if 'RAPIDCLOUD_TEST_MODE_AWS_REDSHIFT' in os.environ and os.environ.get(
                'RAPIDCLOUD_TEST_MODE_AWS_REDSHIFT') == "true":
            print(pprint.pformat(v))

    def load_params(self, module, command, args):
        # we will populate this dict and pass it to the command functions
        params = {}
        try:
            # we're pulling all valus from the args object into a dict
            args_dict = vars(args)

            # we then load the actual args from the module's json
            json_args = self.get_module_json("redshift")[module][command]['args']

            # now we'll loop over them all
            for arg in json_args.keys():
                params[arg] = args_dict[f"{module}_{arg}"]
                if arg == 'tags' or arg == 'parameters':
                    # convert string to dict here
                    arg_json = json.loads(args_dict[f"{module}_{arg}"].replace("\\", ""))
                    try:
                        params[arg] = arg_json
                    except Exception as e:
                        print(e)

        except Exception as e:
            print(f"init.py error: {e}")

        # add values used originally in the init py code
        params['database_name'] = args_dict['name']
        if command == 'create':
            params['master_username'] = 'root'
            params['master_password'] = f"{args_dict['env']}/redshift_cluster/{args_dict['name']}"
        elif command == 'create_serverless':
            params['admin_username'] = 'root'
            params['admin_password'] = f"{args_dict['env']}/redshift_serverless/{args_dict['name']}"
        params['parameters'] = {"require_ssl": "true"}

        return params

    def add_datalake(self, metadata=None):
        if super().get_item("aws_infra", "fqn", f"{super().get_env()}_s3_bucket_ingestion"):
            self.logger.info("Current environment already has a datalake")
        else:
            exec_module(self.args, "datalake", "create")

        item = {
            'fqn': f"{super().get_env()}_{self.args.name}".replace('-', '').replace('_', ''),
            'name': self.args.name,
            'profile': super().get_env(),
            'type': "redshift_serverless",
            'timestamp': str(datetime.datetime.now()),
        }
        super().put_item("datawarehouse", item)

    def create(self, metadata=None):
        super().delete_infra_metadata(name=self.args.name)
        self.add_datalake()
        super().save_password(super().get_env(), 'redshift_cluster', self.args.name, '')

        params = self.load_params('redshift', 'create', self.args)
        resource_name = self.args.name
        resource_type = 'redshift_cluster'
        super().add_aws_resource(resource_type, resource_name, params)
        super().add_aws_resource('redshift_lambda', resource_name, params)

    def create_serverless(self, metadata=None):
        super().delete_infra_metadata(name=self.args.name)
        self.add_datalake()
        super().save_password(super().get_env(), 'redshift_serverless', self.args.name, '')

        params = self.load_params('redshift', 'create_serverless', self.args)
        resource_name = self.args.name
        resource_type = 'redshift_serverless'

        super().add_aws_resource(resource_type, resource_name, params)
        super().add_aws_resource('redshift_lambda', resource_name, params)

    def add_table(self, metadata=None):
        env = super().get_env()
        name = self.args.name
        db_name = self.args.redshift_db_name
        pk = self.args.redshift_primary_key
        sk = self.args.redshift_sort_key if self.args.redshift_sort_key else None
        dist_key = self.args.redshift_dist_key if self.args.redshift_dist_key else None
        dist_style = self.args.redshift_dist_style if self.args.redshift_dist_style else None
        target_db = f"{env}_{db_name}".replace('-', '').replace('_', '')
        connection_string = f"{env}/redshift_cluster/main/connection_string"

        fqn = f"{target_db}_{name}"
        item = {
            'fqn': fqn,
            'profile': env,
            'name': name,
            'dw': target_db,
            'connection_string': connection_string,
            'db_type': "redshift",
            'db_name': db_name,
            'schema': None,
            'primary_key': pk,
            'sort_key': sk,
            'enabled': False,
            'analysis_catalog': f"{env}_analysisdb",
            'analysis_bucket': f"{env}_analysis".replace('_', '-'),
            'iam_role': 'tbd',
            'dist_key': dist_key,
            'dist_style': dist_style,
            'timestamp': str(datetime.datetime.now()),
        }
        super().put_item("publishing", item)

        job_name = f"publish_redshift_{db_name}_{name}"
        db_connection = f"{super().get_env()}_{db_name}_redshift_cluster"
        params = super().get_glue_job_params(job_name, "pythonshell", dataset=name, db_connection=db_connection)
        super().add_aws_resource('glue_job', job_name, params)

    def generate_schema(self, metadata=None):
        # Generate schemas
        # do this after analysisdb has been crawled
        publishing = Publishing(super().get_args()).get_all_publishing()
        if len(publishing) > 0:
            step += 1
            if super().prompt(step, "Generate Redshift schemas (if applicable)") == 'yes':
                RedshiftDDL().main(super().get_args())


    def load_sql(self, metadata=None):
        pass