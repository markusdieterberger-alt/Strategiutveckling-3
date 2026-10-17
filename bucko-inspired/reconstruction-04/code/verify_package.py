"""Verify the delivered package before replay overwrites outputs."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'MANIFEST_SHA256.json').read_text());failed=[]
for row in manifest['files']:
 p=ROOT/row['path']
 if not p.is_file():failed.append(row['path']+': missing');continue
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 if h!=row['sha256'] or p.stat().st_size!=row['bytes']:failed.append(row['path']+': mismatch')
print(json.dumps({'verified_files':len(manifest['files']),'failed':failed},indent=2))
sys.exit(bool(failed))
