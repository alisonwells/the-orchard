import requests
import boto3
import csv
from datetime import datetime

URL = "https://data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD"
LOCAL_FILE = "../data/restaurants.csv"
DYNAMODB_TABLE = "restaurant"

def download_data_to_file(url, local_file):
    """Downloads a file from a url to a given local file"""

    r=requests.get(url)
    with open(local_file, 'wb') as f:
        f.write(r.content)

def convert_csv_to_json_list(local_file):
    """For each restaurant that matches the criteria, convert the CSV data into
    a dictionary of values that ensures only one entry per restaurant"""

    latest_restaurant_grade = {}
    with open(local_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if decide_if_latest_data(row, latest_restaurant_grade):
                data = get_data(row)
                latest_restaurant_grade[row['CAMIS']] = data
    items = [v for v in latest_restaurant_grade.values()]
    return items

def decide_if_latest_data(row, latest_restaurant_grade):
    """The criteria for adding the data for a restaurant is that the restaurant
    has been graded, and that if this is a duplicate row, then the date of the
    grading is more recent than the one we already have"""

    if "GRADE DATE" in row:
        if row['CAMIS'] not in latest_restaurant_grade:
            return True
        else:
            if row['GRADE DATE'] in [None, ""]:
                return False
            else:
                latest_so_far = datetime.strptime(latest_restaurant_grade[row['CAMIS']]['grade_date'], '%m/%d/%Y')
                date_to_compare = datetime.strptime(row['GRADE DATE'], '%m/%d/%Y')
                return date_to_compare > latest_so_far
    else:
        return False


def batch_write(items):
    """Write the items to DynamoDB in batches"""

    dynamodb = boto3.resource('dynamodb')
    db = dynamodb.Table(DYNAMODB_TABLE)

    with db.batch_writer() as batch:
        for item in items:
            response = batch.put_item(Item=item)


def get_data(row):
    """Pick out the relevant data from the CSV file for the DynamoDB table"""
    data = {}
    data['restaurant_id'] = row['CAMIS'] if row['CAMIS'] != "" else "?"
    data['name'] = row['DBA'] if row['DBA'] != "" else "?"
    building = row['BUILDING'] if row['BUILDING'] != "" else "?"
    street = row['STREET'] if row['STREET'] != "" else "?"
    boro = row['BORO'] if row['BORO'] != "" else "?"
    zip = row['ZIPCODE'] if row['ZIPCODE'] != "" else "?"
    data['address'] = "{}, {}, {} {}".format(building.strip(), street.strip(), boro.strip(), zip.strip())
    data['cuisine'] = row['CUISINE DESCRIPTION'] if row['CUISINE DESCRIPTION'] != "" else "?"
    data['rating'] = row['GRADE'] if row['GRADE'] != "" else "?"
    data['grade_date'] = row['GRADE DATE'] if row['GRADE DATE'] != "" else "01/01/1900"
    return data

# Tests below. They should be in a separate file, but I couldn't get the import to work properly
import pytest
@pytest.mark.parametrize("input, expected_result",
    [
        ({"CAMIS":"50069167", "DBA":"RICE THAI", "BUILDING":"3913 ", "STREET":" MAIN ST", "BORO":"Brooklyn", "ZIPCODE":"11215", "CUISINE DESCRIPTION":"Mexican", "GRADE": "A", "GRADE DATE":"06/11/2019"}, {"restaurant_id":"50069167", "name":"RICE THAI", "address":"3913, MAIN ST, Brooklyn 11215", "cuisine":"Mexican", "rating": "A", "grade_date":"06/11/2019"}),
        ({"CAMIS": "", "DBA":"", "BUILDING":"", "STREET":"", "BORO":"", "ZIPCODE":"", "CUISINE DESCRIPTION":"", "GRADE":"", "GRADE DATE":""}, {"restaurant_id":"?", "name":"?", "address":"?, ?, ? ?", "cuisine":"?", "rating":"?", "grade_date":"01/01/1900"})
    ])
def test_get_data(input, expected_result):
    # When
    result = get_data(input)
    # Then
    assert result == expected_result


@pytest.mark.parametrize("input1, input2, expected_result",
    [
        ({"CAMIS":"50069167", "DBA":"RICE THAI", "BUILDING":"3913 ", "STREET":" MAIN ST", "BORO":"Brooklyn", "ZIPCODE":"11215", "CUISINE DESCRIPTION":"Mexican", "GRADE": "A", "GRADE DATE":"06/11/2019"},
        {}, True),
        ({"CAMIS":"50069167", "DBA":"RICE THAI", "BUILDING":"3913 ", "STREET":" MAIN ST", "BORO":"Brooklyn", "ZIPCODE":"11215", "CUISINE DESCRIPTION":"Mexican", "GRADE": "A", "GRADE DATE":"06/11/2019"},
        {"50069167":{"grade_date":"05/11/2019"}}, True),
        ({"CAMIS":"50069167", "DBA":"RICE THAI", "BUILDING":"3913 ", "STREET":" MAIN ST", "BORO":"Brooklyn", "ZIPCODE":"11215", "CUISINE DESCRIPTION":"Mexican", "GRADE": "A", "GRADE DATE":"06/11/2019"},
        {"50069167":{"grade_date":"07/11/2019"}}, False),
        ({"CAMIS":"50069167", "DBA":"RICE THAI", "BUILDING":"3913 ", "STREET":" MAIN ST", "BORO":"Brooklyn", "ZIPCODE":"11215", "CUISINE DESCRIPTION":"Mexican"},
        {"50069167":{"grade_date":"07/11/2019"}}, False)
    ])
def test_decide_if_latest_data(input1, input2, expected_result):
    # When
    result = decide_if_latest_data(input1, input2)
    # Then
    assert result == expected_result

if __name__ == '__main__':
    # download_data_to_file(URL, LOCAL_FILE)
    json_data = convert_csv_to_json_list(LOCAL_FILE)
    batch_write(json_data)
