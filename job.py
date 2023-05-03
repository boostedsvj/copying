from jdlfactory_server import data, group_data # type: ignore
import os.path as osp
import seutils

failures = []

for rootfile, dst in data.jobs:
    try:
        if seutils.isfile(dst):
            print('Skipping {}; already exists'.format(rootfile))
            continue
        print(rootfile + ' -> ' + dst)
        seutils.cp(rootfile, dst)
    except Exception:
        print('Failed for {}; skipping'.format(rootfile))
        failures.append(rootfile)

if failures:
    print('Failed to copy:')
    print('\n'.join(failures))
    if len(failures) == len(data.rootfiles):
        print('ALL FAILED')
