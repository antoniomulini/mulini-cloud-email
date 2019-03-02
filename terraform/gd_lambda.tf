# Creates processGDAlert lambda function to act on Guard Duty alerts

data "archive_file" "zipit" {
  type        = "zip"
  source_file = "../lambda/gd_alerts/processGDAlert.py"
  output_path = "../lambda/gd_alerts/processGDAlert.zip"
}

data "aws_caller_identity" "current" {}

resource "aws_lambda_function" "processGDAlert" {
    filename = "../lambda/gd_alerts/processGDAlert.zip"
    source_code_hash = "${data.archive_file.zipit.output_base64sha256}"
    function_name = "processGDAlert"
    publish = true
    handler = "processGDAlert.lambda_handler"
    role = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/lambda_GDAlert"
    runtime = "python2.7"
}

resource "aws_lambda_permission" "processGDAlert_allowCWE" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.processGDAlert.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "arn:aws:events:eu-west-1:${data.aws_caller_identity.current.account_id}:rule/GuardDutyEvent"
}

resource "aws_lambda_alias" "latest_alias" {
  name             = "latest_processGDAlert"
  description      = "Process Guard Duty Alert"
  function_name    = "${aws_lambda_function.processGDAlert.arn}"
  function_version = "$LATEST"
}