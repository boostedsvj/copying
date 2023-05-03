import os, os.path as osp, argparse, json
import seutils
import tqdm
from time import strftime

stageout = (
        'root://cmseos.fnal.gov/'
        '/store/user/lpcdarkqcd/boosted/signal_madpt300_2023/'
        )


class Cache:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.reread()

    def reread(self):
        if not osp.isfile(self.cache_file):
            self.cache = {}
        else:
            with open(self.cache_file) as f:
                self.cache = json.load(f)
    
    def write(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)


src_cache = Cache(osp.join(osp.dirname(osp.abspath(__file__)), 'src.cache'))
dst_cache = Cache(osp.join(osp.dirname(osp.abspath(__file__)), 'dst.cache'))
dst_cache.cache.setdefault('existing', [])
dst_cache.cache.setdefault('missing', [])


def get_dst(rootfile):
    base = osp.basename(rootfile)
    dir = osp.basename(osp.dirname(rootfile))
    if 'TREEMAKER/HADD' in rootfile:
        return osp.join(stageout, 'HADD', base)
    elif 'TREEMAKER' in rootfile:
        return osp.join(stageout, 'TREEMAKER', dir, base)
    elif 'MINIAOD' in rootfile:
        return osp.join(stageout, 'MINIAOD', dir, base)
    raise Exception('Can\'t determine stageout for ' + rootfile)



def get_rootfiles(filename):
    filename = osp.abspath(filename)

    if filename not in src_cache.cache:
        print('No cached entry for %s, reading' % filename)

        with open(filename) as f:
            lines = list(f.readlines())

        rootfiles = []

        for line in tqdm.tqdm(lines):
            if '#' in line: line = line.split('#',1)[0]
            line = line.strip()
            if not line: continue

            if line.startswith('root:'):
                pass
            elif line.startswith('/eos/user/s/snabili/'):
                line = 'root://eosuser.cern.ch/' + line
            else:
                raise Exception('Cannot process line %s' % line)

            if not seutils.exists(line):
                print(f'{line} does not exist!')
                continue

            if line.endswith('.root'):
                rootfiles.append(line)
            else:
                rootfiles.extend(seutils.ls_wildcard(line + '/*.root'))

        rootfiles = [r for r in rootfiles if not(r.startswith('.sys.a')) and r.endswith('.root')]
        src_cache.cache[filename] = rootfiles
        src_cache.write()

    return src_cache.cache[filename]


def get_missing(rootfiles):
    existing = set(dst_cache.cache['existing'])
    missing = set(dst_cache.cache['missing'])

    did_update = False
    for rootfile in set(rootfiles) - existing - missing:
        did_update = True
        if seutils.isfile(rootfile):
            existing.add(rootfile)
        else:
            missing.add(rootfile)

    if did_update:
        dst_cache.cache['existing'] = list(existing)
        dst_cache.cache['missing'] = list(missing)
        dst_cache.write()
    
    return missing


def update_dst(rootfiles):
    existing = set(dst_cache.cache['existing'])
    missing = set(dst_cache.cache['missing'])

    print('Updating %s' % dst_cache.cache_file)
    n_missing = 0
    for rootfile in tqdm.tqdm(rootfiles):
        if seutils.isfile(rootfile):
            existing.add(rootfile)
            missing.discard(rootfile)
        else:
            n_missing += 1
            missing.add(rootfile)
            existing.discard(rootfile)

    print(f'Missing {n_missing} out of {len(rootfiles)} rootfiles')
    dst_cache.cache['existing'] = list(existing)
    dst_cache.cache['missing'] = list(missing)
    dst_cache.write()




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', type=str, choices=['copy', 'check', 'update', 'copylocal', 'check_existing'])
    parser.add_argument('copyfile', type=str)
    parser.add_argument('--testlocal', action='store_true')
    args = parser.parse_args()

    rootfiles = get_rootfiles(args.copyfile)
    dsts = [get_dst(r) for r in rootfiles]

    if args.action == 'update':
        print('Checking which files are missing on %s' % stageout)
        update_dst(dsts)

    elif args.action == 'check':
        missing = get_missing(dsts)
        print(f'There are {len(missing)} files missing:')
        for f in sorted(missing): print(f)

    elif args.action == 'check_existing':
        missing = get_missing(dsts)
        existing = set(dsts) - missing
        print(f'There are {len(existing)} files already existing:')
        for f in sorted(existing): print(f)

    elif args.action == 'copylocal':
        missing = get_missing(dsts)
        print(f'Copying {len(missing)} files LOCALLY')

        for rootfile, dst in zip(rootfiles, dsts):
            if dst not in missing: continue
            print(f'{rootfile} -> {dst}')
            seutils.cp(rootfile, dst)

    elif args.action == 'copy':
        missing = get_missing(dsts)
        print('Copying %s files' % len(missing))

        import jdlfactory
        group = jdlfactory.Group.from_file('job.py')
        group.venv()
        group.sh([
            'pip install --ignore-installed https://github.com/tklijnsma/jdlfactory/archive/main.zip',
            'pip install seutils'
            ])
        group.htcondor['on_exit_hold'] = '(ExitBySignal == true) || (ExitCode != 0)'
        # group.htcondor['request_memory'] = '4000'
        group.group_data['stageout'] = stageout

        jobs = [[r,d] for r, d in list(zip(rootfiles, dsts)) if d in missing]
        for i in range(0, len(jobs), 100):
            group.add_job({'jobs' : jobs[i:i+100]})

        if args.testlocal:
            group.run_locally()
        else:
            jobdir = strftime('copyjob_{}_%b%d_%H%M%S'.format(len(group.jobs)))
            group.prepare_for_jobs(jobdir)
            os.system('cd {}; condor_submit submit.jdl'.format(jobdir))

main()



# for dir in [
#     'root://cmseos.fnal.gov//store/user/lpcdarkqcd/boosted/signal_madpt0_2023/MINIAOD/',
#     'root://cmseos.fnal.gov//store/user/lpcdarkqcd/boosted/signal_madpt300_2023/MINIAOD/',
#     ]:
#     for subdir in seutils.ls_wildcard(dir+'/*'):
#         print(subdir)
#         rootfiles = seutils.ls_wildcard(subdir+'/*.root')[:1000]
#         group.add_job({'rootfiles' : rootfiles})

# print('Submitting', len(group.jobs), 'jobs')

# # group.run_locally()
# jobdir = strftime('jobs_genxsec_{}_%b%d_%H%M%S'.format(len(group.jobs)))
# group.prepare_for_jobs(jobdir)
# os.system('cd {}; condor_submit submit.jdl'.format(jobdir))