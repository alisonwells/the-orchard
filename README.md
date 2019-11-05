## Restaurant chooser

This API allows you to request a list of restaurants which provide a certain cuisine with a certain minimum standard. Restaurants are graded A-C with A as the best rating.

To use the API you need a provided `API_KEY` from which you can construct a CURL command such as below:

```
curl --request POST \
  --url https://wjbd7a5qmvbmvjo6t46kribx6q.appsync-api.eu-west-1.amazonaws.com/graphql \
  --header 'content-type: application/json' \
  --header 'x-api-key: API_KEY' \
  --data '{"query":"    query GetCuisine {\n      getCuisine(cuisine: \"Thai\", rating: \"B\") {\n        name\n        address\n        cuisine\n        rating\n      }\n    }"}'
  ```

  Other cuisines are available, e.g. you could try with `American` or `Chinese`.
  In return you will receive a list of restaurant names and their locations as well as the latest rating. The minimum rating is optional - if you leave it out you will get all restaurants for a specific cuisine that have been inspected and given a rating.

  ### Design
  This system downloads restaurant rating data from <https://data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD>, picks out restaurants that have been rated and ensures that the rating from the most recent inspection is used. It then uploads the data to DynamoDB. The DynamoDB table has a Global Secondary Index on cuisine type and rating which allows you to look up records by cuisine and query the rating. There is then an AppSync endpoint which uses API keys as authentication which provides a single GraphQL endpoint `GetCuisine`.

  ### Infrastructure
  The infrastructure for the DynamoDB table and the AppSync endpoint have been specified using Terraform. To install into another AWS account, make sure that you set up your credentials via `aws configure` using the aws cli. Then navigate to the terraform folder and run `terraform apply`

  ### Testing
  Tests have been written for the Python ETL code using pytest. To run them use `py.test`

  ### Improvements
  This system has been set up purely to answer the question "Which Thai restaurants have a rating B or above?". If other questions were to be asked the DynamoDB table might need to be redesigned and new AppSync end points added.
