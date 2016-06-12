#!/usr/bin/env python
import os, sys, requests, json, base64, time, random, collections, argparse
from multiprocessing import Process, Pipe

# TODO: use conf
ARRIVAL_INTERVAL_MEAN = 1
ARRIVAL_INTERVAL_DEV = 0.5

def conf():
    if conf.val == None:
        with open('static/config.json') as f:
            conf.val = json.loads(f.read())
    return conf.val
conf.val = None

def db_b64():
    with open('examples/tyler.db') as f:
        return base64.b64encode(f.read())

class User():
    def __init__(self, fbid, endtime):
        self.url = conf()['url']
        self.fbid = fbid
        self.endtime = endtime
        self.db = db_b64()
        self.ops = [
            {'fn': self.OP_fetch_words, 'freq': 1},
            {'fn': self.OP_upload, 'freq': 1},
            {'fn': self.OP_stats, 'freq': 10},
            {'fn': self.OP_practice, 'freq': 50},
        ]
        self.freq_tot = sum(map(lambda op: op['freq'], self.ops))
        self.stats = {'ops': 0, 
                      'latency-sum': 0.0}

    def post(self, op, data):
        print op
        data['op'] = op
        data['fbid'] = self.fbid

        t0 = time.time()
        # TODO: support skip mode to make sure client isn't overwhelmed
        r = requests.post(self.url, data=json.dumps(data))
        t1 = time.time()

        self.stats['ops'] += 1
        self.stats['latency-sum'] += (t1-t0)

        return r.text

    # TODO: verify results
    def OP_fetch_words(self):
        self.post('fetch_words', {})

    def OP_upload(self):
        self.post('upload', {'db': self.db})

    def OP_stats(self):
        self.post('stats', {})

    def OP_practice(self):
        self.post('practice', {}) # TODO: use actual values

    def do_op(self, op):
        fn = op['fn']
        fn()

    def rand_op(self):
        r = random.randrange(0, self.freq_tot)
        for op in self.ops:
            if r <= op['freq']:
                self.do_op(op)
                break
            r -= op['freq']

    def run(self):
        while True:
            delay = max(random.normalvariate(ARRIVAL_INTERVAL_MEAN,
                                             ARRIVAL_INTERVAL_DEV), 0)
            if time.time() + delay >= self.endtime:
                break
            # TODO: subtract out time spent on last req
            time.sleep(delay)
            self.rand_op()
        return self.stats

class UserProcess:
    def __init__(self, fbid, endtime):
        self.fbid = fbid
        self.parent_conn = None
        self.child = None
        self.endtime = endtime

    def run(self, conn):
        u = User(self.fbid, self.endtime)
        results = u.run()
        conn.send(results)
        conn.close()

    def start(self):
        self.parent_conn, child_conn = Pipe()
        self.child = Process(target=self.run, args=(child_conn,))
        self.child.start()

    def wait(self):
        result = self.parent_conn.recv()
        self.child.join()
        return result

# child
def run(conn):
    u = User()
    results = u.run()
    conn.send(results)
    conn.close()

# parent
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', '-u', metavar='u', default=1, type=int)
    parser.add_argument('--seconds', '-s', metavar='s', default=10, type=int)
    args = parser.parse_args()

    endtime = time.time() + args.seconds

    procs = []
    for i in range(args.users):
        procs.append(UserProcess(i+1, endtime))

    for proc in procs:
        proc.start()

    totals = {'latency-sum': 0.0, 'ops': 0.0}
    for proc in procs:
        results = proc.wait()
        for k in totals.keys():
            totals[k] += results[k]
    print 'Average latency: %.3f seconds' % (totals['latency-sum'] / totals['ops'])

if __name__ == '__main__':
    main()
