
data "aws_iam_policy_document" "serverless" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}


resource "aws_iam_role" "serverless" {
  name               = var.namespace_name
  assume_role_policy = data.aws_iam_policy_document.serverless.json
  tags = merge({
    Name = var.namespace_name
    },
    var.tags
  )
}



data "aws_iam_policy" "commands" {
  name = "AmazonRedshiftAllCommandsFullAccess"
}

resource "aws_iam_role_policy_attachment" "commands" {
  role       = aws_iam_role.serverless.name
  policy_arn = data.aws_iam_policy.commands.arn
}
