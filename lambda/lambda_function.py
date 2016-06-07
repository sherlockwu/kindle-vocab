import sqlite3, base64, tempfile, os, traceback, urllib2, json

class DatabaseIF:
    def __init__(self):
        raise NotImplementedError()

    def append(self, rowkey, colkey, value):
        raise NotImplementedError()

    def get(self, rowkey):
        raise NotImplementedError()

    def put(self, row):
        raise NotImplementedError()

class DynamoDB(DatabaseIF):
    def __init__(self, tablename, rowkey):
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = dynamodb.Table(tablename)
        self.rowkey = rowkey

    def append(self, rowkey, colkey, value):
        result = self.table.update_item(
            Key={
                self.rowkey: rowkey,
            },
            UpdateExpression='SET practice = list_append(%s, :i)' % colkey,
            ExpressionAttributeValues={
                ':i': [value],
            },
            ReturnValues='UPDATED_NEW'
        )

    def get(self, rowkey):
        # self.rowkey: field name
        # rowkey:      field value
        response = self.table.get_item(Key={self.rowkey: rowkey})
        if not 'Item' in response:
            return None
        return response['Item']

    def put(self, row):
        return self.table.put_item(Item=row)

class RethinkDB(DatabaseIF):
    def __init__(self, conn, dbname, tablename):
        import rethinkdb as r
        self.conn = conn
        self.table = r.db(dbname).table(tablename)

    def append(self, rowkey, colkey, value):
        table = self.table
        # not atomic!
        lst = table.get(rowkey)[colkey].run(self.conn)
        lst.append(value)
        return table.get(rowkey).update({colkey: lst}).run(self.conn)

    def get(self, rowkey):
        return self.table.get(rowkey).run(self.conn)

    def put(self, row):
        return self.table.insert(row, conflict='replace').run(self.conn)

def update_user(event, words):
    # insert words in dynamodb
    table = event['table']
    user = {'fbid': event['fbid'],
            'words': words,
            'practice': []}
    return table.put(user)

def practice(event):
    table = event['table']
    assert(len(event['cur_words']) <= 10)
    for w in event['cur_words']:
        assert(isinstance(w, basestring))
        assert(len(w) < 255)
    assert(event['guess'] in event['cur_words'])
    assert(event['actual'] in event['cur_words'])
    row = {'cur_words': event['cur_words'],
	   'guess':     event['guess'],
	   'actual':    event['actual']};
    return table.append(event['fbid'], 'practice', row)

def fetch_words(event):
    table = event['table']
    row = table.get(event['fbid'])
    if row == None:
        update_user(event, [])
    row = table.get(event['fbid'])
    return row['words']

def upload(event):
    fd, path = tempfile.mkstemp(suffix='.db')
    f = os.fdopen(fd, 'wb')
    f.write(base64.b64decode(event['db']))
    f.close()
    conn = sqlite3.connect(path)
    words = [row[0] for row in conn.execute('SELECT word FROM words')]
    return update_user(event, words);

def stats(event):
    table = event['table']
    user = table.get(event['fbid'])

    correct = 0
    wrong = 0
    for row in user['practice']:
        if row['actual'] == row['guess']:
            correct += 1
        else:
            wrong += 1
    rv = [
        {'name': 'correct', 'val': correct},
        {'name': 'wrong', 'val': wrong}
    ]
    return rv

def handler_generic(event):
    fn = {
        'upload': upload,
        'fetch_words': fetch_words,
        'practice': practice,
        'stats': stats,
    }[event['op']]
    return fn(event)    

# aws entry
def lambda_handler(event, context):
    # authenticate with FB
    if not 'fbid' in event:
        event['fbid'] = '0'
    if event['fbid'] != '0':
        url = 'https://graph.facebook.com/me?access_token='+event['fbid'];
        response = urllib2.urlopen(url)
        info = json.loads(response.read())
        event['fbid'] = info['id'];

    # use dynamoDB
    event['table'] = DynamoDB('kindle-users', 'fbid')

    return handler_generic(event)

# ol entry
def handler(conn, event):
    # TODO: add FB support

    # use rethinkDB
    event['table'] = RethinkDB(conn, 'vocab', 'kindle_users')

    return handler_generic(event)
