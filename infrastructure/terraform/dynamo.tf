resource "aws_dynamodb_table" "restaurant" {
  name           = "restaurant"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "restaurant_id"

  attribute {
    name = "restaurant_id"
    type = "S"

  }

  attribute {
    name = "cuisine"
    type = "S"
  }

  attribute {
    name = "rating"
    type = "S"
  }

  global_secondary_index {
    name               = "cuisine_index"
    hash_key           = "cuisine"
    range_key          = "rating"
    projection_type    = "ALL"
  }

}
