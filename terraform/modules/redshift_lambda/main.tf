resource "aws_s3_bucket_notification" "redshift_lambda" {
  bucket = "${var.name}-mgmt-lambda"
  lambda_function {
    lambda_function_arn = aws_lambda_function.redshift_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_s3_bucket" "redshift_lambda" {
  bucket = "${var.name}-mgmt-lambda"
  tags = merge(
    {
      Name = "${var.name}-mgmt-lambda"
    }, var.tags
  )
}

resource "aws_s3_bucket_server_side_encryption_configuration" "redshift_lambda" {
  bucket = aws_s3_bucket.redshift_lambda.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_ownership_controls" "redshift_lambda" {
  bucket = aws_s3_bucket.redshift_lambda.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "redshift_lambda" {
  bucket                  = aws_s3_bucket.redshift_lambda.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# create the code
data "archive_file" "redshift_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/source/"
  output_path = "${path.module}/zip/main.zip"
}

resource "aws_lambda_function" "redshift_lambda" {
  function_name    = "${var.name}-mgmt"
  role             = aws_iam_role.redshift_lambda.arn
  handler          = "main.lambda_handler"
  description      = "Manage Redshift Objects"
  runtime          = "python3.9"
  filename         = "${path.module}/zip/main.zip"
  source_code_hash = data.archive_file.redshift_lambda.output_base64sha256
  memory_size      = 128
  timeout          = 900
  tags             = var.tags

  environment {
    variables = {
      SECRET_ARN = var.redshift_secret
    }
  }

  vpc_config {
    subnet_ids         = var.subnets
    security_group_ids = [var.redshift_sg]
  }

  lifecycle {
    ignore_changes = [
    ]
  }
}

resource "aws_lambda_permission" "redshift_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.redshift_lambda.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.redshift_lambda.arn
}

resource "aws_cloudwatch_log_group" "redshift_lambda" {
  name              = "/aws/lambda/${var.name}-mgmt-lambda"
  retention_in_days = 30
}

resource "aws_iam_role" "redshift_lambda" {
  name               = "${var.name}-mgmt-lambda"
  description        = "send sns events to slack"
  assume_role_policy = data.aws_iam_policy_document.redshift_lambda-sts.json
}

data "aws_iam_policy_document" "redshift_lambda-sts" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "redshift_lambda" {
  role       = aws_iam_role.redshift_lambda.name
  policy_arn = aws_iam_policy.redshift_lambda.arn
}

resource "aws_iam_policy" "redshift_lambda" {
  name        = "${var.name}-mgmt-lambda"
  description = "redshift_lambda"
  policy      = data.aws_iam_policy_document.redshift_lambda.json
}

data "aws_iam_policy_document" "redshift_lambda" {
  statement {
    sid = "AllowSecrets"

    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:ListSecretVersionIds",
      "secretsmanager:PutSecretValue",
      "secretsmanager:UpdateSecret",
      "secretsmanager:TagResource",
      "secretsmanager:UntagResource"
    ]

    resources = [var.redshift_secret]
  }

  statement {
    sid = "AllowKms"

    actions = [
      "kms:Decrypt"
    ]

    resources = ["*"]
  }

  statement {
    sid = "AllowLogsandEc2"
    actions = [
      "logs:PutLogEvents",
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeInstances",
      "ec2:DeleteNetworkInterface",
      "ec2:CreateNetworkInterface",
      "ec2:AttachNetworkInterface",
    ]

    resources = ["*"]
  }

  statement {
    sid = "s3"

    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:GetObject",
      "s3:PutObject",
      "s3:CopyObject",
      "s3:PutObjectAcl",
      "s3:DeleteObject",
      "s3:GetBucketLocation",
      "s3:ListAllMyBuckets",
      "s3:HeadObject"
    ]

    resources = [
      aws_s3_bucket.redshift_lambda.arn,
      "${aws_s3_bucket.redshift_lambda.arn}/*"
    ]
  }
}

