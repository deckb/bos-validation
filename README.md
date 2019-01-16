
# Environment setup
```
# install virtualenv if not installed
sudo apt install virtualenv
virtualenv ~/envs/eospy/
source ~/envs/eospy/bin/activate
pip install libeospy

# pull down this github
git clone https://github.com/deckb/bos_validation.git
cd bos_validation
time python ./bos_validation.py -u http://10.132.0.3:9999 --snapshot-csv ./accounts_info_bos_snapshot.airdrop.normal.csv --snapshot-json ./accounts_info_bos_snapshot.airdrop.msig.json --out-file bos_validation.log

```