# Copying files from CERN eos to FNAL efficiently

## Setup

One time:
```
git clone git@github.com:boostedsvj/copying.git
cd copying
mkdir -p env/bin
mkdir -p env/lib/python3.6/site-packages
pip install tqdm seutils
pip install -U https://github.com/tklijnsma/jdlfactory/archive/main.zip
```

Every time:
```
cd copying # whereever you put it
source activate.sh
```

## How to use

Create a file like with the following contents, and call it e.g. `copylist_May3.txt`:

```
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz300_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz400_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz500_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz300_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz400_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/madpt300_mz500_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz300_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz400_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz500_mdark10_rinv0.1
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz300_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz400_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/MINIAOD/madpt300_mz500_mdark10_rinv0.7
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz300_mdark10_rinv0.1.root
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz400_mdark10_rinv0.1.root
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz500_mdark10_rinv0.1.root
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz300_mdark10_rinv0.7.root
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz400_mdark10_rinv0.7.root
/eos/user/s/snabili/SIG/mDark10/TREEMAKER/HADD/madpt300_mz500_mdark10_rinv0.7.root
```

To determine which files need to be copied, run the following:

```
python submit.py update copylist_May3.txt
```

This should print something like this:

```
No cached entry for /uscms_data/d3/klijnsma/semivis/copying/copylist_May3.txt, reading
100%|████████████████████████████████████████████████| 18/18 [01:23<00:00,  4.61s/it]
Checking which files are missing on root://cmseos.fnal.gov//store/user/lpcdarkqcd/boosted/signal_madpt300_2023/
Updating /uscms_data/d3/klijnsma/semivis/copying/dst.cache
100%|██████████████████████████████████████████| 23942/23942 [07:00<00:00, 56.94it/s]
Missing 11993 out of 23942 rootfiles
```

First the code loops through the list of directories/files in the .txt file, and caches all found rootfiles in `src.cache`.
It then loops through all found source files (23942 in this example), and checks per file if it already exists in the at the copy destination.
Whether a file is missing or already existing is cached in `dst.cache`.
If something goes wrong during `update`, delete the `src.cache` and `dst.cache` files.

Once the update is done, run:

`python submit.py copy copylist_May3.txt`

This should submit a bunch of jobs that start the copying process.
You can close your terminal safely at this point.
Typically copying takes a few hours.

Once all jobs are done, run `update` again:

`python submit.py update copylist_May3.txt`

After the jobs are done, you should see `Missing 0 out of 23942 rootfiles`; if not, run the `copy` command again to submit new jobs (or, if there are only a few files missing, run `python submit.py copylocal copylist_May3.txt` to run the copying interactively).
