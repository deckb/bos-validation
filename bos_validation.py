from eospy import cleos
import argparse
import datetime as dt
from threading import Thread

try:
    # if python 3
    from math import isclose
except :
    # running in python 2
    def isclose(a, b, rel_tol=1e-09, abs_tol=0.0) :
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

# 
# 
parser = argparse.ArgumentParser(description='Create a snapshot')
parser.add_argument('--url', '-u', type=str, action='store', default='http://localhost:8888', dest='url')
parser.add_argument('--snapshot', type=str, action='store', required=True, dest='snapshot')
parser.add_argument('--out-file', type=str, help='output log', action='store', required=True, dest='out_file')
parser.add_argument('--num-threads', help='number of threads to run', type=int, default=16, action='store', dest='num_thds')
args = parser.parse_args()

ce = cleos.Cleos(args.url)
global log_queue
total_bos = 0.0
log_queue = []

# whack the file
with open(args.out_file,'w') :
    print('Resetting file {}'.format(args.out_file))

def flush_output() :
    with open(args.out_file,'a') as wb :
        try: 
            line = log_queue.pop()
            while line :
                wb.write(str(line))
                line = log_queue.pop()
        except IndexError:
            pass

def calc_bos(eos_amt):
    eos_to_bos = eos_amt / 20.0
    staked=0.2
    if(eos_to_bos < 0.5) :
        return 0.5 + staked
    else:
        return eos_to_bos + staked 

def check_account(eos_account, owner_key, active_key, eos_amt, name, bos_total):
    global total_bos
    account_errors = 0
    try:
        acct_info = ce.get_account(name)
    except:
        log_queue.append("ERROR!!! It appears {} was not added\n".format(name))
        account_errors += 1
    if account_errors == 0 and name == acct_info['account_name']:
        try:
            liquid = liquid = float(acct_info['core_liquid_balance'].split()[0])
            acct_info['total_resources']['cpu_weight'].split()[0]
            staked_cpu = float(acct_info['total_resources']['cpu_weight'].split()[0])
            staked_net = float(acct_info['total_resources']['net_weight'].split()[0])
            total = liquid + staked_cpu + staked_net
            calculated = calc_bos(float(eos_amt.split()[0]))
            total_bos += total
            # check if the numbers are super close or if they equal
            if isclose(total, calculated):
                log_queue.append("ERROR!!!: {} has the wrong balance information {} != {}.\n".format(name, total, calculated))    
                account_errors += 1
        except Exception as ex:
            print(ex)
            log_queue.append("ERROR!!!: {} Failed to get balance information.\n".format(name))
            account_errors += 1

        for perm in acct_info['permissions']:
            if perm['perm_name'] == active_key and perm['required_auth']['keys'][0]['key'] != active_key:
                log_queue.append('ERROR!!! {0} has mismatched active key expected {1} and got {2}'.format(name, active_key, perm['required_auth']['keys'][0]['key']))
                account_errors += 1
            if perm['perm_name'] == owner_key and perm['required_auth']['keys'][0]['key'] != owner_key:
                log_queue.append('ERROR!!! {0} has mismatched owner key expected {1} and got {2}'.format(name, active_key, perm['required_auth']['keys'][0]['key']))
                account_errors += 1

        # check code
        if u'1970-01-01T00:00:00.000' != acct_info['last_code_update'] :
            log_queue.append('ERROR!!! this {0}\'s code has been updated'.format(name))
            account_errors += 1
        # check priv
        if acct_info['privileged'] :
            log_queue.append('ERROR!!! this {0} has been set to privileged\n'.format(name))
            account_errors += 1    

    if account_errors == 0: 
        log_queue.append('SUCCESS!!! account {} appears valid with {} BOS, no contract set, and not privileged\n'.format(name, calculated))
    

num_thds = args.num_thds

with open(args.snapshot) as fo:
    import csv
    cnt = 0
    snap = list(csv.reader(fo, delimiter=','))
    log_queue.append('Checking {0} accounts\n'.format(len(snap)))
    flush_output()
    while cnt < len(snap):
        threads = []
        cnt_thds = 0
        if cnt + num_thds > len(snap):
            num_thds = len(snap) - cnt
        proc_list = snap[cnt:cnt+num_thds]
        for p in proc_list:
            t = Thread(target=check_account, args=(p))
            t.start()
            threads.append(t)
        for thd in threads:
            thd.join()
        flush_output()
        cnt += len(proc_list)
        # TODO remove
    log_queue.append('Total accounts: {} worth {} BOS\n'.format(cnt, total_bos))
    flush_output()