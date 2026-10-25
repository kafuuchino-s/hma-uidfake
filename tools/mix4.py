#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
"""Normal external Kbuild, Android tools, exact approved payload checks and ZIPs."""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APPROVED = json.loads((ROOT / 'config/approved.json').read_text())
TUS = ['abx', 'text_xml', 'packages_xml', 'main', 'sync', 'watcher', 'netlink',
       'status', 'rules', 'preset_rules', 'packages', 'paths', 'paging']
JSON_SHA = '9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def output_dir(path):
    path = Path(path).resolve()
    if path == ROOT or ROOT in path.parents:
        raise RuntimeError('Generated output must be outside the source checkout')
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(argv, *, cwd=None, env=None, log=None):
    result = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace', check=False)
    if log:
        Path(log).write_text(result.stdout, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Command failed ({}): {}\n{}'.format(
            result.returncode, ' '.join(map(str, argv)), result.stdout[-6000:]))
    return result.stdout.strip()


def source_inputs_ok():
    expected = json.loads((ROOT / 'config/source-inputs.json').read_text())
    for name, sha in expected.items():
        if digest(ROOT / name) != sha:
            raise RuntimeError('Source differs from approved inputs: ' + name)
    return len(expected)


def verify(directory):
    directory = Path(directory).resolve()
    source_inputs_ok()
    for name, expected in APPROVED['payloads'].items():
        path = directory / name
        data = path.read_bytes()
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise RuntimeError('Unapproved payload: ' + name + '; obtain new ABI/CFI/runtime evidence first')
        if data[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', data, 18)[0] != 183:
            raise RuntimeError('Not an ELF64 little-endian AArch64 payload: ' + name)
        expected_type = 1 if name.endswith('.ko') else 3
        if struct.unpack_from('<H', data, 16)[0] != expected_type:
            raise RuntimeError('Unexpected ELF type: ' + name)
    return {'approved_payloads': 4, 'source_inputs_verified': source_inputs_ok()}


def build_tools(args):
    out = output_dir(args.out)
    ndk = Path(args.ndk).resolve()
    props = (ndk / 'source.properties').read_text()
    if '27.3.13750724' not in props:
        raise RuntimeError('The approved userspace toolchain is NDK r27d')
    tag = 'windows-x86_64' if os.name == 'nt' else ('darwin-x86_64' if sys.platform == 'darwin' else 'linux-x86_64')
    tc = ndk / 'toolchains/llvm/prebuilt' / tag
    suffix = '.exe' if os.name == 'nt' else ''
    cxx, cc = tc / ('bin/clang++' + suffix), tc / ('bin/clang' + suffix)
    header = Path(args.json_header).resolve()
    if digest(header) != JSON_SHA:
        raise RuntimeError('JSON single-header hash mismatch')
    dep = out / 'deps/include/nlohmann/json.hpp'
    dep.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(header, dep)
    objects = out / 'objects'
    objects.mkdir(exist_ok=True)
    flags = ['--target=aarch64-linux-android33', '--sysroot=' + str(tc / 'sysroot'),
             '-std=c++23', '-O2', '-Wall', '-Wextra', '-fPIE', '-fstack-protector-strong',
             '-I' + str(ROOT / 'src/tools'), '-I' + str(ROOT / 'src/include'),
             '-I' + str(out / 'deps/include')]
    ledger = []

    def compile_one(name):
        src = ROOT / ('tools/kauxctl.cpp' if name == 'kauxctl' else 'src/tools/' + name + '.cpp')
        argv = [str(cxx), *flags, '-c', str(src), '-o', str(objects / (name + '.o'))]
        run(argv, log=objects / (name + '.log'))
        return argv

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        ledger.extend(pool.map(compile_one, [*TUS, 'kauxctl']))
    for name, tus in [('sync-tool', TUS), ('kauxctl', ['kauxctl', 'netlink', 'paging'])]:
        argv = [str(cxx), *flags, '-static-libstdc++', '-pie', '-Wl,-z,relro,-z,now',
                '-Wl,-z,max-page-size=16384', '-s',
                *[str(objects / (n + '.o')) for n in tus], '-ldl', '-lz', '-o', str(out / name)]
        run(argv, log=out / (name + '.link.log')); ledger.append(argv)
    argv = [str(cc), '--target=aarch64-linux-android33', '--sysroot=' + str(tc / 'sysroot'),
            '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-fPIE', '-fstack-protector-strong',
            '-pie', '-Wl,-z,relro,-z,now', '-Wl,-z,max-page-size=16384', '-s',
            str(ROOT / 'tools/load-ko.c'), '-o', str(out / 'load-ko')]
    run(argv, log=out / 'load-ko.log'); ledger.append(argv)
    (out / 'tools-build.json').write_text(json.dumps({'commands': ledger, 'max_compilers': 2}, indent=2) + '\n')
    return {name: digest(out / name) for name in ['load-ko', 'kauxctl', 'sync-tool']}


def build_module(args):
    out = output_dir(args.out)
    kernel, prepared = Path(args.kernel).resolve(), Path(args.kernel_out).resolve()
    if out == kernel or kernel in out.parents or out == prepared or prepared in out.parents:
        raise RuntimeError('Use a separate output outside the supplied kernel and its output')
    if digest(prepared / '.config') != APPROVED['kernel']['config_sha256']:
        raise RuntimeError('Kernel config mismatch')
    if digest(prepared / 'Module.symvers') != APPROVED['kernel']['symvers_sha256']:
        raise RuntimeError('Kernel symbol/CRC table mismatch')
    watched = ['.config', 'Module.symvers', 'include/config/auto.conf',
               'include/generated/autoconf.h', 'include/generated/utsrelease.h']
    before = {name: digest(prepared / name) for name in watched}
    k_out, module = out / 'kernel-out', out / 'module-src'
    k_out.mkdir(exist_ok=True); module.mkdir(exist_ok=True)
    names = ['.config', 'Module.symvers', 'include/config/auto.conf', 'include/config/auto.conf.cmd',
             'include/config/tristate.conf', 'include/config/kernel.release',
             'scripts/basic/fixdep', 'scripts/basic/cc-wrapper', 'scripts/mod/modpost', 'scripts/genksyms/genksyms']
    for rel in ['include/generated', 'arch/arm64/include/generated']:
        names.extend(str(p.relative_to(prepared)) for p in (prepared / rel).rglob('*') if p.is_file())
    for name in names:
        src = prepared / name
        if src.is_file():
            dest = k_out / name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dest)
    for src in (ROOT / 'src').iterdir():
        if src.is_file() and (src.suffix in ['.c', '.h'] or src.name == 'Makefile'):
            shutil.copy2(src, module / src.name)
    shutil.copytree(ROOT / 'src/include', module / 'include', dirs_exist_ok=True)
    recipe = json.loads(Path(args.recipe).read_text())
    clang = Path(args.clang_bin).resolve()
    if '11.0.2' not in run([clang / 'clang', '--version']):
        raise RuntimeError('The target module requires AOSP Clang 11.0.2')
    maps = ' '.join('-' + kind + '=' + str(src) + '=' + dest
                    for src, dest in [(k_out, '/build/out'), (kernel, '/build/src')]
                    for kind in ['fdebug-prefix-map', 'ffile-prefix-map'])
    argv = ['make', '-C', str(kernel), 'O=' + str(k_out), *recipe['make_args'], 'M=' + str(module),
            'KCFLAGS=-Wno-error -Werror=incompatible-pointer-types ' + maps, 'KAFLAGS=' + maps,
            '-j2', 'V=1', 'modules']
    env = os.environ.copy(); env.update(recipe['build_env']); env['PATH'] = str(clang) + os.pathsep + env.get('PATH', '')
    env['LOCALVERSION'] = ''
    for key in ['KCPPFLAGS', 'CFLAGS_KERNEL', 'CFLAGS_MODULE']:
        env.pop(key, None)
    try:
        run(argv, env=env, log=out / 'module-build.log')
    finally:
        if before != {name: digest(prepared / name) for name in watched}:
            raise RuntimeError('Supplied kernel inputs changed')
    shutil.copy2(module / 'hma_uidfake.ko', out / 'hma_uidfake.ko')
    (out / 'module-build.json').write_text(json.dumps({'argv': argv, 'input_hashes_unchanged': before,
            'sha256': digest(out / 'hma_uidfake.ko'), 'requires_approval_if_hash_differs': True}, indent=2) + '\n')
    return {'candidate_module_sha256': digest(out / 'hma_uidfake.ko'), 'normal_kbuild': True,
            'kernel_inputs_unchanged': True}


def package(args):
    artifacts = Path(args.artifacts).resolve()
    checked = verify(artifacts)
    if run(['git', 'status', '--porcelain'], cwd=ROOT):
        raise RuntimeError('Commit the complete source before packaging')
    commit = run(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
    tree = run(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT)
    out = Path(args.out).resolve(); output_dir(out.parent)
    contents = {p.name: p.read_bytes() for p in (ROOT / 'module').iterdir() if p.is_file()}
    for name in APPROVED['payloads']:
        contents['ko/' + name if name.endswith('.ko') else name] = (artifacts / name).read_bytes()
    contents['LICENSE'] = (ROOT / 'LICENSE').read_bytes()
    contents['NOTICE'] = (ROOT / 'NOTICE').read_bytes()
    hashes = []
    for name, info in APPROVED['payloads'].items():
        hashes.append(info['sha256'] + '  ' + ('ko/' + name if name.endswith('.ko') else name))
    contents['payload.sha256'] = ('\n'.join(hashes) + '\n').encode()
    contents['package.json'] = (json.dumps({'repository': 'https://github.com/kafuuchino-s/hma-uidfake',
            'branch': 'mix4-5.4', 'source_commit': commit, 'source_tree': tree,
            'upstream_commit': APPROVED['upstream_commit'], 'kernel': APPROVED['kernel'],
            'payloads': APPROVED['payloads'], 'module_id': 'hma_uidfake_mix4'}, indent=2) + '\n').encode()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0)); info.create_system = 3
            mode = 0o755 if name.endswith('.sh') or name in ['load-ko', 'kauxctl', 'sync-tool'] else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16; info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return {**checked, 'source_commit': commit, 'source_tree': tree, 'zip': str(out),
            'zip_sha256': digest(out), 'entries': len(contents)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['verify', 'package']:
        p = sub.add_parser(name); p.add_argument('--artifacts', required=True)
        if name == 'package': p.add_argument('--out', required=True)
    p = sub.add_parser('tools'); p.add_argument('--ndk', required=True); p.add_argument('--json-header', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('module')
    for name in ['kernel', 'kernel-out', 'recipe', 'clang-bin', 'out']: p.add_argument('--' + name, required=True)
    args = parser.parse_args()
    result = {'verify': lambda x: verify(x.artifacts), 'tools': build_tools,
              'module': build_module, 'package': package}[args.command](args)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
