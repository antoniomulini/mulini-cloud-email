# Define DynamoDB table to store NACL details for blocking IPs that are scanning us

resource "aws_dynamodb_table" "gd_block_table" {
    name           = "gdBlockNACLs"
    read_capacity  = 5
    write_capacity = 5
    hash_key       = "nacl_id"      # Text ID of the NACL that is blocking the scanners
    range_key      = "nacl_entry"   # NACL entry in format nacl-rule-n, or 'nacl-state' for NACL state info

  attribute {
    name = "nacl_id"
    type = "S"
  }

  attribute {
    name = "nacl_entry"
    type = "S"
  }
}

# Set up nacl state entry

resource "aws_dynamodb_table_item" "nacl_state" {
  table_name = "${aws_dynamodb_table.gd_block_table.name}"
  hash_key   = "${aws_dynamodb_table.gd_block_table.hash_key}"
  range_key  = "${aws_dynamodb_table.gd_block_table.range_key}"

  item = <<ITEM
{
  "nacl_id": {"S": "${aws_network_acl.mailhub_acl.id}"},
  "nacl_entry": {"S": "nacl_state"},
  "gdBlockCounter": {"N": "1"},
  "gdBlockStartAt": {"N": "1"},
  "gdBlockEndAt": {"N": "900"},
  "gdBlockAgeInDays": {"N": "30"}
}
ITEM

    lifecycle {
        ignore_changes = ["item"] # Don't reset the values every time this project is run
    }

}

