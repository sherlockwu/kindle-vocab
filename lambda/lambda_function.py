import sqlite3, base64, tempfile, os, boto3, traceback, urllib2, json

def update_user(event, words):
    # insert words in dynamodb
    user = {'fbid': event['fbid'], 'words': words}
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('kindle-users')
    response = table.put_item(Item=user)
    return response

def fetch(event):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('kindle-users')
    response = table.get_item(Key={'fbid': event['fbid']})
    if not "Item" in response:
        update_user(event, [])
    response = table.get_item(Key={'fbid': event['fbid']})
    return response["Item"]

def upload(event):
    fd, path = tempfile.mkstemp(suffix='.db')
    f = os.fdopen(fd, 'wb')
    f.write(base64.b64decode(event['db']))
    f.close()
    conn = sqlite3.connect(path)
    words = [row[0] for row in conn.execute('SELECT word FROM words')]
    return update_user(event, words);

def lambda_handler(event, context):
    fn = {
        'upload': upload,
        'fetch': fetch,
    }[event['op']]

    # authenticate with FB
    if not 'fbid' in event:
        event['fbid'] = "0"
    if event['fbid'] != "0":
        url = 'https://graph.facebook.com/me?access_token='+event['fbid'];
        response = urllib2.urlopen(url)
        info = json.loads(response.read())
        event['fbid'] = info['id'];

    # run specific handler
    return fn(event)
