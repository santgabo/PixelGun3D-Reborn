"""Disposable task-1 metadata-to-lock transcription; installs nothing."""
import base64
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

old = Path('.lab/private/sources/task-1')
new = Path('.lab/private/sources/task-1-recovery')
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

def load(path):
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    return json.loads(data)

tools = []
def entry(name, version, url, path, runtime, source, checksum=None, size=None, status='DEFERRED', notes=None):
    result = dict(name=name, version=version, platform='linux-x86_64', source_url=url,
                  install_path=path, runtime=runtime, artifact_sha256=None,
                  verification_source=source, published_checksum=checksum,
                  checksum_comparison='NOT_DOWNLOADED', artifact_size_bytes=size,
                  status=status, checked_at=now, notes=notes or [])
    tools.append(result)
    return result

native = ['ca-certificates', 'libbrotli1', 'libc6', 'libgcc-s1', 'libgssapi-krb5-2', 'libicu78', 'libssl3t64', 'libstdc++6', 'tzdata', 'zlib1g']
python = entry('Python', '3.14.4', 'https://packages.ubuntu.com/resolute/python3.14',
               '/usr/bin/python3.14', 'Existing Ubuntu interpreter; isolated venv .lab/venvs/unitypy only',
               ['.lab/private/logs/task-1-recovery/inventory.stdout', '.lab/private/logs/task-1-recovery/package_origins.stdout'],
               notes=['No system replacement or global pip.', 'venv is present; ensurepip and python3.14-venv are absent.',
                      'Use venv --without-pip and the pinned pip wheel through PYTHONPATH for local bootstrap in task 3. No get-pip script or system package installation.'])
python['existing_package'] = {'name': 'python3.14', 'version': '3.14.4-1ubuntu0.2', 'origin': 'Ubuntu resolute-updates/main amd64; see package_origins.stdout'}
python['checksum_comparison'] = 'EXISTING_SYSTEM_PACKAGE; no installer hash invented'

dotnet = load(old/'dotnet_10_releases.body')
release = next(r for r in dotnet['releases'] if r['release-version'] == dotnet['latest-release'])
sdk = release['sdk']
artifact = next(f for f in sdk['files'] if f['rid']=='linux-x64' and f['name'].endswith('.tar.gz'))
e = entry('dotnet-sdk', sdk['version'], artifact['url'], '.lab/tools/dotnet',
          'Bundled Microsoft.NETCore.App '+release['runtime']['version']+'; native Ubuntu libraries',
          ['https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json', str(old/'dotnet_10_releases.body'), str(new/'dotnet_ubuntu.body')],
          {'algorithm':'sha512', 'value':artifact['hash']}, notes=['SDK chosen for dotnet tool install; not a source-build requirement of ILSpyCmd.'])
e['native_packages'] = native
e['native_packages_inventory'] = '.lab/private/logs/task-1-fix-1/dotnet-native-packages.json'

catalog = load(new/'ilspy_catalog.body')
registration = load(new/'ilspy_registration.body')
e = entry('ILSpyCmd', '11.1.0.9782', registration['packageContent'], '.lab/tools/ilspy',
          'Microsoft.NETCore.App >=10.0.0, major 10; selected SDK 10.0.401 bundles runtime 10.0.12',
          [catalog['@id'], str(new/'ilspy_catalog.body'), str(old/'ilspycmd_11_1_0_nupkg.body')],
          {'algorithm':'sha512-base64', 'value':catalog['packageHash']}, size=(old/'ilspycmd_11_1_0_nupkg.body').stat().st_size)
blob = (old/'ilspycmd_11_1_0_nupkg.body').read_bytes()
assert base64.b64encode(hashlib.sha512(blob).digest()).decode() == catalog['packageHash']
e['artifact_sha256'] = hashlib.sha256(blob).hexdigest()
e['checksum_comparison'] = 'MATCH; official NuGet catalog SHA512; NuGet signature NOT_VERIFIED'
e['metadata_archive_path'] = str(old/'ilspycmd_11_1_0_nupkg.body')
with zipfile.ZipFile(old/'ilspycmd_11_1_0_nupkg.body') as z:
    runtime_config = json.loads(z.read('tools/net10.0/any/ilspycmd.runtimeconfig.json'))
    assert runtime_config['runtimeOptions']['framework']['version'] == '10.0.0'
e['runtime_config'] = runtime_config

jdk = load(new/'jdk21_assets_latest.body')[0]
a = jdk['binary']['package']
e = entry('Temurin-JDK', jdk['version']['openjdk_version'], a['link'], '.lab/tools/java',
          'OpenJDK HotSpot 21 LTS, Linux glibc x64; CLI usage headless',
          [jdk['release_link'] if 'release_link' in jdk else 'https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.12.1%2B1', str(new/'jdk21_assets_latest.body'), str(new/'temurin_install.body')],
          {'algorithm':'sha256','value':a['checksum']}, a['size'], notes=['Selected instead of previously discovered JRE to supply JAVA_HOME consistently for Android CLI too. No Gradle installation.'])
e['published_signature_url'] = a['signature_link']
e['published_checksum_url'] = a['checksum_link']
e['native_packages'] = ['libc6', 'libgcc-s1', 'libstdc++6', 'zlib1g', 'ca-certificates']
e['optional_gui_packages'] = ['libx11-6','libxext6','libxi6','libxrender1','libxtst6','libfreetype6','fontconfig','libasound2t64']

for name, filename, artifact_name, path, runtime, runtime_source in [
    ('JADX', 'jadx_latest.body', 'jadx-1.5.6.zip', '.lab/tools/jadx', 'Java >=11 64-bit; selected Temurin 21.0.12.1+1-LTS', new/'jadx_readme.body'),
    ('Apktool', 'apktool_latest.body', 'apktool_3.0.3.jar', '.lab/tools/apktool', 'Java >=8; selected Temurin 21.0.12.1+1-LTS; invoke java -jar', new/'apktool_install.body')]:
    r = load(old/filename)
    assert not r['prerelease'] and not r['draft']
    a = next(a for a in r['assets'] if a['name']==artifact_name)
    entry(name,r['tag_name'].removeprefix('v'),a['browser_download_url'],path,runtime,
          [r['html_url'], str(old/filename),str(runtime_source)],
          {'algorithm':'sha256','value':a['digest'].removeprefix('sha256:')},a['size'],
          notes=['Release binary only. JADX build JDK >=17 is distinct from its Java >=11 runtime.' if name=='JADX' else 'Decode only; aapt/aapt2 source-build dependencies are not required for the planned decode.'])

r = next(r for r in load(old/'assetripper_releases.body') if not r['prerelease'] and not r['draft'])
a = next(a for a in r['assets'] if a['name']=='AssetRipper_linux_x64.tar.xz')
e = entry('AssetRipper',r['tag_name'],a['browser_download_url'],'.lab/tools/assetripper',
          'Published NativeAOT self-contained Linux x64 executable AssetRipper.GUI.Free; no external .NET runtime',
          [r['html_url'],str(old/'assetripper_releases.body'),str(new/'assetripper_publish_actual.body'),str(new/'assetripper_csproj.body'),str(new/'dotnet_nativeaot.body')],
          {'algorithm':'sha256','value':a['digest'].removeprefix('sha256:')},a['size'],
          notes=['Published on Ubuntu 22.04; .NET 10 SDK/clang are build-time only.', 'Invariant globalization; inspect executable/shared-library NEEDED entries before execution in task 3.', 'Use Free edition only and UI on loopback; do not export full OBB.'])
e['native_packages'] = ['libc6','libgcc-s1','libstdc++6','zlib1g','libssl3t64']

# Pick exactly one cp314/abi3 x64 manylinux wheel or pure-Python wheel.
# tpk_ar has only a pure-Python sdist; its setuptools build tooling is pinned too.
def python_artifact(j):
    candidates = []
    for a in j['urls']:
        n=a['filename']
        if a['yanked'] or not n.endswith('.whl'):
            continue
        if n.endswith(('py3-none-any.whl','py2.py3-none-any.whl')):
            candidates.append(a)
        elif 'manylinux' in n and 'x86_64' in n and ('-cp314-cp314-' in n or '-abi3-' in n or '-abi3.abi3t-' in n):
            candidates.append(a)
    if not candidates:
        assert j['info']['name'].lower().replace('-','_') == 'tpk_ar'
        return next(a for a in j['urls'] if a['packagetype']=='sdist' and not a['yanked'])
    return sorted(candidates, key=lambda a: ('abi3.abi3t' in a['filename'], a['filename']))[0]

unity = load(old/'unitypy_pypi.body')
python_names = ['UnityPy','lz4','brotli','Pillow','texture2ddecoder','etcpak','astc-encoder-py','fmod_toolkit','fsspec','attrs','tpk_ar','archspec','pyfmodex','pip','setuptools','wheel','packaging']
python_versions = {}
for name in python_names:
    metadata = old/'unitypy_pypi.body' if name=='UnityPy' else new/('pip_pypi.body' if name=='pip' else 'pypi_'+name.lower()+'.body')
    j = load(metadata); a = python_artifact(j); version=j['info']['version']
    python_versions[name]=version
    e = entry(name,version,a['url'],'.lab/venvs/unitypy',
              'CPython 3.14.4 normal GIL ABI; glibc 2.43; '+str(j['info']['requires_python'] or 'no Requires-Python constraint in metadata'),
              ['https://pypi.org/pypi/'+name+'/'+version+'/json',str(metadata)],
              {'algorithm':'sha256','value':a['digests']['sha256']},a['size'])
    e['artifact_filename'] = a['filename'];e['requires_dist'] = j['info']['requires_dist'] or []
    e['role'] = 'tool' if name=='UnityPy' else ('local-bootstrap/build' if name in ['pip','setuptools','wheel','packaging'] else 'UnityPy runtime dependency')
    if name=='tpk_ar':
        data=(new/'tpk_ar_sdist_metadata.body').read_bytes()
        assert hashlib.sha256(data).hexdigest()==a['digests']['sha256']
        e['artifact_sha256']=hashlib.sha256(data).hexdigest();e['checksum_comparison']='MATCH; PyPI published SHA256; metadata inspected only, not built'
        e['notes']=['Pure-Python sdist, no native compiler needed. Build offline using pinned setuptools/wheel/packaging in isolated venv with --no-build-isolation; no unpinned build resolver.']
    if name=='UnityPy':
        e['notes']=['Default extras only; no ttgen/full/tests/dev.', 'All default direct/transitive dependencies pinned in this lock; compatible wheel tags found for Python 3.14, except pure-Python tpk_ar sdist. Actual imports and object parsing deferred to task 3.']
    if name=='fmod_toolkit':
        e['notes']=['Wheel bundles FMOD Engine 2.00.10. No vendor account/login/download or audio playback needed for the selected sample. Audit bundled notices before installation; stop if an explicit license-acceptance step is required. Audio compatibility not certified.']

# Exact Android artefacts: stable channel only, no preview or floating package alias.
def android(path, filename, base, name, install_path, runtime):
    root=ET.parse(filename).getroot()
    package=next(p for p in root if p.tag.endswith('remotePackage') and p.get('path')==path and p.find('channelRef').get('ref')=='channel-0')
    assert package.find('revision/preview') is None
    rev='.'.join(c.text for c in package.find('revision'))
    archives=package.findall('archives/archive')
    a=next((a for a in archives if a.findtext('host-os')=='linux'),archives[0])
    checksum=a.find('complete/checksum')
    e=entry(name,rev,base+a.findtext('complete/url'),install_path,runtime,
            [str(filename),'https://developer.android.com/tools/sdkmanager'],
            {'algorithm':checksum.get('type','sha1'),'value':checksum.text},int(a.findtext('complete/size')),status='BLOCKED',
            notes=['Official android-sdk-license acceptance is NOT authorized; do not download/install/accept with sdkmanager.', 'Published SHA1 only in repository XML; SHA256 unknown until approved download, not invented.'])
    e['sdk_package']=path;e['license_ref']=package.find('uses-license').get('ref')
    return e

android_repo=old/'android_repository.body'
e=android('cmdline-tools;17.0',android_repo,'https://dl.google.com/android/repository/','Android-command-line-tools','.lab/tools/android-sdk/cmdline-tools/17.0', 'JDK >=17 per both published launchers; selected Temurin JDK 21.0.12.1+1-LTS; actual startup deferred behind license gate')
e['verification_source'] += [str(new/'sdkmanager_17_launcher.txt'),str(new/'avdmanager_17_launcher.txt')]
e['notes'] += ['Supervisor-approved stable 17.0 instead of 23.0: 23.0 replaces sdkmanager with a new native Android CLI wrapper, outside this laboratory scope.', 'HTTP Range bounded to <=131072 bytes per request inspected official launcher metadata only, not installed or executed.']
android('platform-tools',android_repo,'https://dl.google.com/android/repository/','Android-platform-tools-ADB','.lab/tools/android-sdk/platform-tools','Linux x64 native executable; no Java runtime for adb')
android('emulator',android_repo,'https://dl.google.com/android/repository/','Android-emulator','.lab/tools/android-sdk/emulator','Linux x64, KVM read/write and CPU virtualization, isolated lab only; 16 GB RAM vendor recommendation')
e=android('system-images;android-25;default;x86',new/'android_sysimg.body','https://dl.google.com/android/repository/sys-img/android/','Android-system-image','.lab/tools/android-sdk/system-images/android-25/default/x86','Android 7.1 API 25 x86 32-bit guest; selected emulator 37.2.12; actual ro.product.cpu.abilist validation deferred')
e['notes']+=['No Google-account requirement for default AOSP image. No claim of boot, ABI effectiveness, or game compatibility.']

free=shutil.disk_usage('.').free
assert free>=10*1024**3
lock={'schema':'lab-toolchain-lock-v1','checked_at':now,'selection_complete':True,
      'installation_performed':False,'tools':tools,
      'budget':{'minimum_free_bytes':10*1024**3,'minimum_free_gib':10,'policy_owner':'laboratory, not vendor requirement',
                'free_bytes_at_selection':free,'static_peak_reserve_bytes':5*1024**3,'runtime_peak_reserve_bytes':12*1024**3,
                'reserve_note':'Conservative working allowances including archives, extracted distributions, cache, bounded smoke output and one AVD; not measured expansion sizes. Recheck df before each download/extraction/export and stop if free minus planned peak <10 GiB.',
                'known_download_bytes':sum(e['artifact_size_bytes'] or 0 for e in tools)},
      'capabilities':{'STATIC_READY':'DEFERRED','RUNTIME_READY':'BLOCKED'},
      'administrative_gates':[
          {'status':'BLOCKED','action':'Authorize acceptance of android-sdk-license for command-line tools/platform-tools/emulator/API25 image. No licenses accepted.'},
          {'status':'BLOCKED','action':'Authorize administrator-managed read/write access to /dev/kvm (e.g. membership of kvm followed by session renewal). No group/perms changed.'},
          {'status':'BLOCKED','action':'Authorize and verify APK network isolation/rollback before any emulator boot or game execution. No firewall/network changes.'}],
      'native_packages_evidence':'.lab/private/logs/task-1-fix-1/native_packages.stdout',
      'native_packages_pending':[],
      'selection_rulings':['Supervisor-approved: select stable cmdline-tools 17.0 instead of 23.0 to preserve sdkmanager/avdmanager and avoid the new native Android CLI outside scope; risk: future repositories/commands may require a separately selected and tested CLI update.'],
      'host_resource_concerns':['Host has about 11 GiB RAM versus 16 GB emulator documentation recommendation; no emulator boot or compatibility claimed.'],
      'notes':['No source-build toolchain, Unity Editor, Gradle, Ghidra or Frida required.',
               'Android filename commandlinetools-linux-12700392_latest.zip is the vendor build-number-pinned filename, NOT a latest alias; replay the exact URL and checksum and cmdline-tools;17.0 only.',
               'Task 1 status concerns selection only: no tool marked PASS before version AND functional validation.',
               'Existing baseline and independent sample copies reused per recovery instruction; no initial massive rehash.']}
Path('.lab/toolchain.lock.json').write_text(json.dumps(lock,indent=2,ensure_ascii=False)+'\n')
Path('.lab/toolchain.lock.json').chmod(0o600)
print('Selected',len(tools),'entries; published NuGet and tpk_ar hashes match; no installation.')
print('Versions:',json.dumps({e['name']:e['version'] for e in tools},ensure_ascii=False))
print('Free GiB:',round(free/1024**3,2),'known download MiB:',round(lock['budget']['known_download_bytes']/1024**2,2))
