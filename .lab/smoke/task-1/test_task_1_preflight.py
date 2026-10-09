"""Task-1-only acceptance checks; no installation, execution of tools, or broad rehash."""
import ast
import base64
import datetime
import getpass
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import unittest
import xml.etree.ElementTree as ET
import zipfile

WORKSPACE = Path('.lab/private/sdd/2026-10-09-01-instalacion-verificacion-herramientas')
OLD = Path('.lab/private/sources/task-1')
NEW = Path('.lab/private/sources/task-1-recovery')

def load(p):
    data=p.read_bytes()
    return json.loads(gzip.decompress(data) if data[:2]==b'\x1f\x8b' else data)

class Task1Preflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock=load(Path('.lab/toolchain.lock.json'))
        cls.tools={e['name']:e for e in cls.lock['tools']}
        cls.baseline=load(Path('.lab/private/input-baseline.json'))

    def test_task_1_required_deliverables_and_closed_selection(self):
        for p in ['.lab/toolchain.lock.json','.lab/env.sh','docs/lab/estado-herramientas.md']:
            self.assertTrue(Path(p).is_file(),p)
        self.assertTrue(self.lock['selection_complete'])
        required={'Python','dotnet-sdk','ILSpyCmd','Temurin-JDK','JADX','Apktool','AssetRipper','UnityPy','Android-command-line-tools','Android-platform-tools-ADB','Android-emulator','Android-system-image'}
        self.assertTrue(required<=self.tools.keys())
        self.assertEqual(len(self.tools),len(self.lock['tools']))
        for e in self.tools.values():
            for k in ['name','version','platform','source_url','install_path','runtime','artifact_sha256','verification_source','status','checked_at']:
                self.assertIn(k,e)
            self.assertTrue(e['version'])
            self.assertNotEqual(e['version'],'latest')
            self.assertTrue(e['source_url'].startswith('https://'))
            self.assertTrue(e['runtime'])
            self.assertIn(e['status'],['DEFERRED','BLOCKED'])
            if e['name']!='Python':
                self.assertTrue(e['install_path'].startswith('.lab/'))
                self.assertTrue(e['published_checksum']['value'])
            for source in e['verification_source']:
                if source.startswith('.lab/'):
                    self.assertTrue(Path(source).is_file(),source)

    def test_task_1_recovered_baseline_preserved_and_input_stats(self):
        recovery=load(WORKSPACE/'recovery-1.json')
        expected=next(f for f in recovery['partial_files'] if f['path']=='.lab/private/input-baseline.json')
        self.assertEqual(hashlib.sha256(Path(expected['path']).read_bytes()).hexdigest(),expected['sha256'])
        self.assertEqual(self.baseline['file_count'],10393)
        self.assertEqual(len(self.baseline['files']),10393)
        actual={str(p) for root in ['apk+obb-original','unpacked'] for p in Path(root).rglob('*') if p.is_file()}
        self.assertEqual(actual,{f['path'] for f in self.baseline['files']})
        self.assertEqual(sum(f['size'] for f in self.baseline['files']),self.baseline['total_file_bytes'])
        for f in self.baseline['files']:
            p=Path(f['path']);s=p.stat()
            self.assertEqual(s.st_size,f['size'],str(p))
            self.assertEqual(datetime.datetime.fromtimestamp(s.st_mtime,datetime.timezone.utc).isoformat(),f['mtime_utc'],str(p))
            self.assertEqual(sum(b['size'] for b in f['blocks']),f['size'])
            self.assertEqual(f['block_size'],67108864)
        # Full input hashes were already verified at recovery; do not duplicate mass I/O.
        self.assertEqual(recovery['baseline_changes'],[])
        self.assertEqual(recovery['baseline_files_verified'],10393)

    def test_task_1_independent_samples_match_originals_and_manifest(self):
        samples=list(Path('.lab/samples/Managed').glob('*.dll'))+[Path('.lab/samples/Data/globalgamemanagers')]
        self.assertEqual(len(samples),28)
        manifest={f['path']:f for f in self.baseline['files']}
        sources=Path('unpacked/apk/assets/bin/Data')
        for sample in samples:
            original=sources/('Managed/'+sample.name if sample.suffix=='.dll' else sample.name)
            self.assertFalse(sample.is_symlink())
            self.assertEqual(sample.stat().st_nlink,1)
            self.assertNotEqual((sample.stat().st_dev,sample.stat().st_ino),(original.stat().st_dev,original.stat().st_ino))
            expected=manifest[str(original)]
            self.assertEqual(sample.stat().st_size,expected['size'])
            self.assertEqual(hashlib.sha256(sample.read_bytes()).hexdigest(),expected['sha256'])
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),expected['sha256'])
            with sample.open('rb') as stream:
                header=stream.read(256)
            if sample.suffix=='.dll':
                self.assertEqual(header[:2],b'MZ')
            else:
                self.assertIn(b'5.3.7p1',header)

    def test_task_1_no_installation_or_false_readiness(self):
        self.assertFalse(self.lock['installation_performed'])
        self.assertEqual(list(Path('.lab/tools').iterdir()),[])
        self.assertEqual(list(Path('.lab/venvs').iterdir()),[])
        self.assertEqual(self.lock['capabilities'],{'STATIC_READY':'DEFERRED','RUNTIME_READY':'BLOCKED'})
        for name in ['dotnet','java','javac','ilspycmd','jadx','apktool','adb','sdkmanager','emulator']:
            self.assertIsNone(shutil.which(name),name)

    def test_task_1_private_permissions(self):
        for p in [Path('.lab'),*Path('.lab').rglob('*')]:
            if p.is_symlink():
                self.fail('Unexpected symlink in private lab: '+str(p))
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o700 if p.is_dir() else 0o600,str(p))

    def test_task_1_env_shell_clean_explicit_source(self):
        r=subprocess.run(['bash','-n','.lab/env.sh'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        # Only an explicitly sourced child Bash receives local settings.
        script='source .lab/env.sh; test "$DOTNET_CLI_TELEMETRY_OPTOUT" = 1 && test "$DOTNET_SKIP_FIRST_TIME_EXPERIENCE" = 1 && test "$LAB_MIN_FREE_GIB" = 10 && test "$JAVA_HOME" = "$LAB_ROOT/tools/java" && test "$ANDROID_HOME" = "$LAB_ROOT/tools/android-sdk" && test "$PIP_REQUIRE_VIRTUALENV" = true && test "$(umask)" = 0077 && test "$LAB_ROOT" = "$PWD/.lab" && test "$LAB_UNITYPY_PYTHON" = "$LAB_ROOT/venvs/unitypy/bin/python" && case "$PATH" in *"$ANDROID_HOME/cmdline-tools/17.0/bin"*) true;; *) false;; esac'
        r=subprocess.run(['env','-i','PATH=/usr/bin:/bin','bash','--noprofile','--norc','-c',script],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        text=Path('.lab/env.sh').read_text()
        for forbidden in ['sudo ','curl ','sdkmanager --licenses','export LD_LIBRARY_PATH=','source ~/.bashrc']:
            self.assertNotIn(forbidden,text)

    def test_task_1_dotnet_and_published_metadata_checksums(self):
        ilspy=self.tools['ILSpyCmd']
        blob=OLD/'ilspycmd_11_1_0_nupkg.body'
        self.assertEqual(hashlib.sha256(blob.read_bytes()).hexdigest(),ilspy['artifact_sha256'])
        self.assertEqual(base64.b64encode(hashlib.sha512(blob.read_bytes()).digest()).decode(),ilspy['published_checksum']['value'])
        with zipfile.ZipFile(blob) as z:
            cfg=json.loads(z.read('tools/net10.0/any/ilspycmd.runtimeconfig.json'))
        self.assertEqual(cfg['runtimeOptions']['framework']['version'],'10.0.0')
        self.assertEqual(self.tools['dotnet-sdk']['version'],'10.0.401')
        self.assertIn('10.0.12',self.tools['dotnet-sdk']['runtime'])
        self.assertIn('NativeAOT',self.tools['AssetRipper']['runtime'])
        self.assertIn('<PublishAot>true</PublishAot>',(NEW/'assetripper_csproj.body').read_text())
        tpk=self.tools['tpk_ar']
        self.assertEqual(hashlib.sha256((NEW/'tpk_ar_sdist_metadata.body').read_bytes()).hexdigest(),tpk['published_checksum']['value'])

    def test_task_1_dotnet_native_packages_cover_official_ubuntu_2604_list(self):
        source=(NEW/'dotnet_ubuntu.body').read_text()
        ubuntu=source.split('data-pivot="os-linux-ubuntu-2604"',1)[1].split('data-pivot="os-linux-ubuntu-2510"',1)[0]
        dependencies=re.search(r'<h2 id="dependencies">Dependencies</h2>.*?<ul>(.*?)</ul>',ubuntu,re.S)
        self.assertIsNotNone(dependencies,'Ubuntu 26.04 manual-install dependency list missing')
        official=set(re.findall(r'<li>([^<]+)</li>',dependencies.group(1)))
        self.assertEqual(len(official),10,'Unexpected source structure; inspect the official list')
        self.assertEqual(set(self.tools['dotnet-sdk']['native_packages']),official)
        selector=ast.parse(Path('.lab/smoke/task-1/select_toolchain.py').read_text())
        native=next(n.value for n in selector.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='native' for t in n.targets))
        self.assertEqual(set(ast.literal_eval(native)),official)
        inventory=load(Path(self.tools['dotnet-sdk']['native_packages_inventory']))
        self.assertEqual(set(p['name'] for p in inventory['packages']),official)
        self.assertEqual(len(inventory['packages']),len(official))
        self.assertEqual(inventory['missing_packages'],self.lock['native_packages_pending'])
        self.assertEqual(inventory['missing_packages'],[])
        self.assertFalse(inventory['system_changes_performed'])
        self.assertEqual(hashlib.sha256((NEW/'dotnet_ubuntu.body').read_bytes()).hexdigest(),inventory['source_sha256_local_identifier'])
        versions={}
        for line in Path(self.lock['native_packages_evidence']).read_text().splitlines():
            name,version,status=line.split('\t')
            versions[name.split(':',1)[0]]=(version,status)
        self.assertEqual(set(versions),official)
        for package in inventory['packages']:
            self.assertEqual(versions[package['name']],(package['version'],'installed'))
            self.assertEqual(package['status'],'installed')
            self.assertTrue(package['version'])
            self.assertIn(package['version'],package['origin_policy'])
            self.assertIn('http://',package['origin_policy'])
            self.assertIn('ubuntu',package['origin_policy'])
            self.assertIn(package['origin_policy'],Path(package['origin_evidence']).read_text())
        self.assertTrue(all(c['returncode']==0 for c in inventory['commands']))

    def test_task_1_python_dependency_closure_and_wheel_tags(self):
        names=['UnityPy','lz4','brotli','Pillow','texture2ddecoder','etcpak','astc-encoder-py','fmod_toolkit','fsspec','attrs','tpk_ar','archspec','pyfmodex','pip','setuptools','wheel','packaging']
        for name in names:
            e=self.tools[name];p=Path(e['verification_source'][-1]);j=load(p)
            self.assertEqual(e['version'],j['info']['version'])
            a=next(a for a in j['urls'] if a['filename']==e['artifact_filename'])
            self.assertEqual(e['source_url'],a['url'])
            self.assertEqual(e['published_checksum']['value'],a['digests']['sha256'])
            if name=='tpk_ar':
                self.assertTrue(e['artifact_filename'].endswith('.tar.gz'))
            else:
                n=e['artifact_filename']
                self.assertTrue(n.endswith(('py3-none-any.whl','py2.py3-none-any.whl')) or ('manylinux' in n and 'x86_64' in n and ('cp314-cp314' in n or 'abi3' in n)),n)
        # Dependency metadata adds only archspec and pyfmodex without extras on 3.14.
        self.assertIn('archspec>=0.2',self.tools['etcpak']['requires_dist'])
        self.assertIn('pyfmodex>=0.7.2',self.tools['fmod_toolkit']['requires_dist'])
        self.assertIn('packaging>=24.0',self.tools['wheel']['requires_dist'])

    def test_task_1_sdk_stable_exact_artifacts_and_runtime_gate(self):
        sources=[ET.parse(OLD/'android_repository.body').getroot(),ET.parse(NEW/'android_sysimg.body').getroot()]
        for name in ['Android-command-line-tools','Android-platform-tools-ADB','Android-emulator','Android-system-image']:
            e=self.tools[name]
            p=next(p for root in sources for p in root if p.tag.endswith('remotePackage') and p.get('path')==e['sdk_package'] and p.find('channelRef').get('ref')=='channel-0')
            self.assertIsNone(p.find('revision/preview'))
            archives=p.findall('archives/archive');a=next((a for a in archives if a.findtext('host-os')=='linux'),archives[0])
            self.assertTrue(e['source_url'].endswith(a.findtext('complete/url')))
            self.assertEqual(e['published_checksum'],{'algorithm':'sha1','value':a.findtext('complete/checksum')})
            self.assertEqual(e['status'],'BLOCKED')
            self.assertIsNone(e['artifact_sha256'])
        self.assertEqual(self.tools['Android-command-line-tools']['sdk_package'],'cmdline-tools;17.0')
        for n in ['sdkmanager','avdmanager']:
            self.assertIn('This tool requires JDK 17 or later.',(NEW/(n+'_17_launcher.txt')).read_text())
        self.assertTrue(self.lock['selection_rulings'])
        self.assertEqual(len(self.lock['administrative_gates']),3)
        self.assertTrue(all(g['status']=='BLOCKED' for g in self.lock['administrative_gates']))

    def test_task_1_budget_and_sanitized_document(self):
        budget=self.lock['budget']
        self.assertEqual(budget['minimum_free_bytes'],10*1024**3)
        self.assertGreaterEqual(shutil.disk_usage('.').free-budget['static_peak_reserve_bytes']-budget['runtime_peak_reserve_bytes'],budget['minimum_free_bytes'])
        text=Path('docs/lab/estado-herramientas.md').read_text()
        self.assertNotIn(getpass.getuser(),text)
        self.assertNotIn('/home/',text)
        self.assertNotIn('uid=',text)
        self.assertIn('RUNTIME_READY',text)
        self.assertIn('10 GiB',text)

if __name__=='__main__':
    unittest.main(verbosity=2)
