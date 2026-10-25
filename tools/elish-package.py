#!/usr/bin/env python3
"""Build the separately approved elish KSU package from a clean source tree."""
import argparse,hashlib,json,os,re,stat,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if git('status','--porcelain','--untracked-files=all'): raise SystemExit('Source must be clean and committed')
    approved=json.loads((ROOT/'config/elish-approved.json').read_text())
    assert approved['schema']=='elish-uidfake-approved-v1'
    assert approved['module']['id']=='hma_uidfake_elish'
    for name,expected in approved['module_source_inputs'].items():
        assert sha(ROOT/name)==expected,name
    for name,value in approved['payloads'].items():
        assert (a.artifacts/name).is_file() and (a.artifacts/name).stat().st_size==value['bytes'],name
        assert sha(a.artifacts/name)==value['sha256'],name
    prop=(ROOT/'module/module.prop').read_text()
    for key,value in [('id',approved['module']['id']),('version',approved['module']['version']),('versionCode',str(approved['module']['version_code']))]:
        assert re.search(r'^'+key+'='+re.escape(value)+r'$',prop,re.M),key
    common=(ROOT/'module/common.sh').read_text()
    for key in ['notes_sha256','source_config_sha256','visible_config_sha256']:
        assert re.fullmatch('[0-9a-f]{64}',approved['kernel'][key]),key
        assert approved['kernel'][key] in common,key
    assert '__ELISH_' not in common
    files={}
    for name in ['module.prop','customize.sh','post-fs-data.sh','service.sh','action.sh','uninstall.sh','common.sh','README.md','skip_mount']:
        path=ROOT/'module'/name; files[name]=(path.read_bytes(),0o755 if name.endswith('.sh') else 0o644)
    for name in ['LICENSE','NOTICE','ELISH.md']:
        files[name]=((ROOT/name).read_bytes(),0o644)
    for name in approved['payloads']:
        files[name]=((a.artifacts/name).read_bytes(),0o644 if name.endswith('.ko') else 0o755)
    files['payload.sha256']=(''.join(v['sha256']+'  '+n+'\n' for n,v in approved['payloads'].items()).encode(),0o644)
    package={'schema':'elish-uidfake-package-v1','module':approved['module'],
             'source':{'base_commit':approved['base_commit'],'commit':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'branch':git('branch','--show-current'),'local_source_bundle_supplied':True},
             'kernel':approved['kernel'],'payloads':approved['payloads'],
             'status':{'protocol':3,'bytes':104,'native_required':4,'compat_required':4,'lsm_required':'cap_task_fix_setuid'},
             'runtime_verified':False,'device_commands':0}
    files['package.json']=(json.dumps(package,ensure_ascii=False,indent=2).encode()+b'\n',0o644)
    a.out.mkdir(parents=True,exist_ok=True)
    name='hma_uidfake_elish-'+approved['module']['version']+'.zip';target=a.out/name
    if target.exists(): raise SystemExit('Refusing to overwrite '+str(target))
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,(data,mode) in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));info.create_system=3
            info.external_attr=(stat.S_IFREG|mode)<<16;info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and set(z.namelist())==set(files)
        for name,(data,mode) in files.items():
            assert z.read(name)==data and stat.S_IMODE(z.getinfo(name).external_attr>>16)==mode,name
    receipt={'zip':str(target),'bytes':target.stat().st_size,'sha256':sha(target),'entries':len(files),'source':package['source'],'payloads':approved['payloads'],'kernel':approved['kernel'],'runtime_verified':False,'all_checks_pass':True}
    (a.out/'package-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
