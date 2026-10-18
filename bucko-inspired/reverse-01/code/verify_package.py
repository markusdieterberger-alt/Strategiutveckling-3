"""Verify delivered bytes, inherited sources, protocol, and pre-economic code lock."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checked={}
    for base,name in [(ROOT,'MANIFEST_SHA256.json'),(ROOT/'baseline','MANIFEST_SHA256.json')]:
        manifest=json.loads((base/name).read_text());n=0
        for row in manifest['files']:
            p=base/row['path'];assert p.is_file(),p
            assert p.stat().st_size==row['bytes'],p
            assert sha(p)==row['sha256'],p
            n+=1
        checked[str(base.relative_to(ROOT))]=n
    assert sha(ROOT/'PROTOCOL_PRE_RESULTS.md')==json.loads((ROOT/'protocol_lock.json').read_text())['sha256']
    for path,digest in json.loads((ROOT/'code_lock_pre_economic.json').read_text())['sha256'].items():assert sha(ROOT/path)==digest,path
    assert sha(ROOT/'code/analyze_experiment.py')==json.loads((ROOT/'analysis_lock.json').read_text())['sha256']
    print(json.dumps(dict(all_pass=True,verified_files=checked),indent=2))
if __name__=='__main__':main()
