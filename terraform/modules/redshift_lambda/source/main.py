#!/usr/bin/env python3
import boto3
import psycopg2
import os
import sys
import re
import json
import urllib


def sep(pattern="=", count=80):
    print(pattern * count)


def get_secret_value(secret_arn):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_arn)
    secret_data = response['SecretString']
    return json.loads(secret_data)


def list_tables(cfg):
    print("Listing current tables")
    try:
        conn = psycopg2.connect(dbname=cfg['redshift_database'],
                                host=cfg['redshift_cluster_endpoint'],
                                port=cfg['redshift_port'],
                                user=cfg['redshift_user'],
                                password=cfg['redshift_password'])
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)

        table_names = cursor.fetchall()
        for table_name in table_names:
            print(table_name[0])
    except Exception as e:
        print(f"Error creating table: {e}")
        raise


def approved_sql_commands(sql_statements):
    print("Making sure statement contain only approved patterns")
    approved_statments = []
    unapproved_statments = []
    not_allowed_commands = ["DROP"]
    for sql in sql_statements:
        for command in not_allowed_commands:
            if re.match(command, sql.upper()):
                unapproved_statments.append(sql)
            else:
                approved_statments.append(sql)

    if len(unapproved_statments) > 0:
        print(
            f"{len(unapproved_statments)} statements out of {len(sql_statements)} are prohibited ({'.'.join(not_allowed_commands)}) and will be ignored."
        )
        for sql in unapproved_statments:
            print(sql.strip())

    return approved_statments


def validate_sql(cfg, sql_statements):
    print("Validating statements")
    valid_statments = []
    invalid_statments = []
    try:
        conn = psycopg2.connect(dbname=cfg['redshift_database'],
                                host=cfg['redshift_cluster_endpoint'],
                                port=cfg['redshift_port'],
                                user=cfg['redshift_user'],
                                password=cfg['redshift_password'])
        cursor = conn.cursor()
        conn.autocommit = False

        for sql in sql_statements:
            try:
                cursor.execute(sql)
                valid_statments.append(sql)
            except Exception as e:
                print(f"Statements {sql.strip()}")
                print(f"Ignored due to: {e}")
                invalid_statments.append(sql)
            conn.rollback()

    except Exception as e:
        print(f"Connection Error {e}")

    if cursor:
        cursor.close()
    if conn:
        conn.close()

    if len(invalid_statments) > 0:
        print(f"{len(invalid_statments)} statements out of {len(sql_statements)} are invalid and will be ignored")
    return valid_statments


def exec_sql(cfg, sql_statements):
    if len(sql_statements) > 0:
        print("Executing valid statements")

        try:
            conn = psycopg2.connect(dbname=cfg['redshift_database'],
                                    host=cfg['redshift_cluster_endpoint'],
                                    port=cfg['redshift_port'],
                                    user=cfg['redshift_user'],
                                    password=cfg['redshift_password'])
            cursor = conn.cursor()
            for sql in sql_statements:
                cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error executing statements: {e}")
            raise
    else:
        print("No valid statements found")


def s3_get(cfg, event):
    if event['Records'][0]['eventSource'] == "aws:s3":
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        file = key.split('/')[-1]
        local_file = f"/tmp/{file}"

    print('downloading {} from {}/{}'.format(file, bucket, key))
    try:
        cfg['s3_client'].download_file(bucket, key, local_file)
        return local_file
    except Exception as e:
        print('download failed')
        print(e)
        return False


def lambda_handler(event, context):
    print(event)

    secret_value = get_secret_value(os.environ.get('SECRET_ARN'))
    cfg = {
        'redshift_client': boto3.client('redshift'),
        's3_client': boto3.client('s3'),
        's3_resource': boto3.resource('s3'),
        'redshift_user': secret_value.get('user'),
        'redshift_cluster_endpoint': secret_value.get('host'),
        'redshift_port': secret_value.get('port'),
        'redshift_database': secret_value.get('dbname'),
        'redshift_password': secret_value.get('password'),
        's3_bucket': 'S3_BUCKET_NAME',
    }
    print(f"Deploing SQL code to {cfg['redshift_database']}")
    sql_s3_obj = s3_get(cfg, event)
    with open(sql_s3_obj, 'r') as sql_file:
        sql_content = sql_file.read()
    sql_statements = sql_content.split(';')
    sql_statements = [sql.strip() for sql in sql_statements if sql.strip()]
    approved_statements = approved_sql_commands(sql_statements)
    valid_statements = validate_sql(cfg, approved_statements)
    exec_sql(cfg, valid_statements)
    list_tables(cfg)


# lambda_handler(None, None)
