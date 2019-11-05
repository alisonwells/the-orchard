resource "aws_appsync_graphql_api" "restaurant" {
  authentication_type = "API_KEY"
  name                = "restaurant-api"

  schema = <<EOF
type Restaurant {
  name: String
  cuisine: String
  address: String
  rating: String
}

type Query {
    getCuisine(cuisine: String!, rating:String): [Restaurant]
}

schema {
    query: Query
}
EOF
}

resource "aws_appsync_datasource" "dynamodb" {
  api_id           = "${aws_appsync_graphql_api.restaurant.id}"
  name             = "dynamodb"
  service_role_arn = "${aws_iam_role.appsync.arn}"
  type             = "AMAZON_DYNAMODB"

  dynamodb_config {
    table_name = "${aws_dynamodb_table.restaurant.name}"
  }
}


resource "aws_appsync_resolver" "getcuisine" {
  api_id      = "${aws_appsync_graphql_api.restaurant.id}"
  field       = "getCuisine"
  type        = "Query"
  data_source = "${aws_appsync_datasource.dynamodb.name}"

  request_template = <<EOF
  {
    "version": "2017-02-28",
    "operation" : "Query",
    "index" : "cuisine_index",
    #if($ctx.args.rating)
    "query" : {
        "expression" : "cuisine = :cuisine and rating between :highest and :rating",
        "expressionValues" : {
            ":cuisine" : $util.dynamodb.toDynamoDBJson($ctx.args.cuisine),
            ":rating" : $util.dynamodb.toDynamoDBJson($ctx.args.rating),
            ":highest" : $util.dynamodb.toDynamoDBJson("A")
        }
      },
    #else
    "query" : {
        "expression" : "cuisine = :cuisine",
        "expressionValues" : {
            ":cuisine" : $util.dynamodb.toDynamoDBJson($ctx.args.cuisine)
        }
      },
    #end
  }
EOF

  response_template = <<EOF
  $utils.toJson($context.result.items)
EOF
}

resource "aws_iam_role" "appsync" {
  name = "appsync"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "appsync.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

}

resource "aws_iam_role_policy" "dynamodb_policy" {
  name = "dynamodb_policy"
  role = "${aws_iam_role.appsync.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "dynamodb:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}
