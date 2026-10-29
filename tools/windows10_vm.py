#!/usr/bin/env python3
"""Create an external Windows 10 evaluation VM; never accept guest licenses."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MEDIA_SHA256 = 'E4AB2E3535BE5748252A8D5D57539A6E59BE8D6726345EE10E7AFD2CB89FEFB5'


def external_directory(value):
    directory = Path(value).expanduser().resolve()
    if directory == Path(directory.anchor) or directory.is_relative_to(ROOT):
        raise ValueError('VM files must be in a dedicated directory outside the repository')
    return directory


def digest(path):
    with path.open('rb') as stream:
        value = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
        return value.hexdigest().upper()


def executable(name):
    found = shutil.which(name)
    if not found:
        raise RuntimeError('Install the official QEMU package first: ' + name)
    return found


def create(directory, iso, memory, cpus):
    directory = external_directory(directory)
    iso = Path(iso).expanduser().resolve(strict=True)
    if not iso.is_file() or iso.suffix.lower() != '.iso':
        raise ValueError('Expected a regular ISO file')
    if not 2048 <= memory <= 16384 or not 1 <= cpus <= 8:
        raise ValueError('Memory must be 2048-16384 MiB; CPUs must be 1-8')
    disk = directory / 'windows10.qcow2'
    manifest = directory / 'vm.json'
    if disk.exists() or manifest.exists():
        raise FileExistsError('Existing VM files will not be replaced')
    if digest(iso) != MEDIA_SHA256:
        raise ValueError('ISO does not match Microsoft Windows 10 LTSC 2021 x64 en-us evaluation hash')
    qemu = executable('qemu-system-x86_64')
    image = executable('qemu-img')
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation protects existing images, including a concurrent creator.
    with disk.open('xb'):
        pass
    subprocess.run([image, 'create', '-f', 'qcow2', str(disk), '64G'], check=True)
    record = {'created_at': datetime.now(timezone.utc).isoformat(),
              'qemu_version': subprocess.check_output([qemu, '--version'], text=True).splitlines()[0],
              'media': str(iso), 'media_sha256': MEDIA_SHA256, 'disk': str(disk),
              'memory_mib': memory, 'cpus': cpus, 'accelerator': 'tcg',
              'guest': 'Windows 10 Enterprise LTSC 2021 Evaluation x64',
              'installation': 'not_completed', 'license_acceptance': 'user_required',
              'browser_validation': 'not_run', 'host_shares': [], 'network': 'user-mode NAT, no host forwarding'}
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    return record


def command(directory, display, tools_iso=None):
    directory = external_directory(directory)
    record = json.loads((directory / 'vm.json').read_text(encoding='utf-8'))
    disk = directory / 'windows10.qcow2'
    iso = Path(record['media']).resolve(strict=True)
    if not disk.is_file() or digest(iso) != MEDIA_SHA256:
        raise ValueError('Missing VM disk or changed installation media')
    memory, cpus = record['memory_mib'], record['cpus']
    if not isinstance(memory, int) or not 2048 <= memory <= 16384 or not isinstance(cpus, int) or not 1 <= cpus <= 8:
        raise ValueError('Invalid VM resource configuration')
    args = [executable('qemu-system-x86_64'), '-name', 'Plaintrace Windows 10 Evaluation',
            '-machine', 'q35', '-accel', 'tcg,thread=multi', '-cpu', 'max',
            '-m', str(memory), '-smp', str(cpus),
            '-drive', 'file='+str(disk).replace(',', ',,')+',format=qcow2,if=ide,index=0',
            '-drive', 'file='+str(iso).replace(',', ',,')+',media=cdrom,readonly=on,if=ide,index=2',
            '-boot', 'order=c,once=d,menu=on', '-vga', 'std',
            '-nic', 'user,model=e1000', '-rtc', 'base=localtime',
            '-monitor', 'none']
    if tools_iso is not None:
        tools = Path(tools_iso).expanduser().resolve(strict=True)
        if not tools.is_file() or tools.suffix.lower() != '.iso':
            raise ValueError('Expected a regular tools ISO')
        args += ['-drive', 'file='+str(tools).replace(',', ',,')+',media=cdrom,readonly=on,if=ide,index=4']
    if display == 'vnc':
        args += ['-display', 'none', '-vnc', '127.0.0.1:7']
    elif display == 'cocoa':
        args += ['-display', 'cocoa']
    else:
        raise ValueError('Unsupported display')
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'command', 'run'])
    parser.add_argument('--directory', required=True)
    parser.add_argument('--iso')
    parser.add_argument('--tools-iso')
    parser.add_argument('--memory', type=int, default=8192)
    parser.add_argument('--cpus', type=int, default=4)
    parser.add_argument('--display', choices=['vnc', 'cocoa'], default='vnc')
    args = parser.parse_args()
    if args.action == 'create':
        if not args.iso:
            parser.error('--iso is required for create')
        print(json.dumps(create(args.directory, args.iso, args.memory, args.cpus), indent=2))
        return 0
    launch = command(args.directory, args.display, args.tools_iso)
    if args.action == 'command':
        print(json.dumps(launch, indent=2))
        return 0
    print('Booting real x64 guest via TCG. Guest license acceptance must be performed by the user.', flush=True)
    return subprocess.run(launch).returncode


if __name__ == '__main__':
    raise SystemExit(main())
