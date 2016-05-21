import sqlite3, base64, tempfile, os, boto3, traceback

fbid = "0"

def fetch(event):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('kindle-users')
    response = table.get_item(Key={'fbid': fbid})
    return response["Item"]

def upload(event):
    fd, path = tempfile.mkstemp(suffix='.db')
    f = os.fdopen(fd, 'wb')
    f.write(base64.b64decode(event['db']))
    f.close()
    conn = sqlite3.connect(path)
    words = [row[0] for row in conn.execute('SELECT word FROM words')]

    # insert words in dynamodb
    user = {'fbid': fbid, 'words': words}
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('kindle-users')
    response = table.put_item(Item=user)
    return response

def lambda_handler(event, context):
    fn = {
        'upload': upload,
        'fetch': fetch,
    }[event['op']]
    return fn(event)
