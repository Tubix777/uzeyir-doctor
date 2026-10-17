"""Release trust, package selection, downloads and installed-version checks."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from uzeyir_doctor import PACKAGE_NAME, UPDATE_REPOSITORY
from uzeyir_doctor.updates import (DownloadCancelled, UpdateError, check_for_update, checksum_for,
                                  download_update, installed_version, parse_updates, verify_download, version_key, promote_native_launcher)


def fixture(version="2.10.0", kind="deb", content=b"verified package bytes"):
    tag="v"+version
    name={"deb":f"{PACKAGE_NAME}_{version}-1_all.deb","rpm":f"{PACKAGE_NAME}-{version}-1.fc44.noarch.rpm",
          "arch":f"{PACKAGE_NAME}-{version}-1-any.pkg.tar.zst"}[kind]
    prefix=f"https://github.com/{UPDATE_REPOSITORY}/releases/download/{tag}/"
    sums=f"{hashlib.sha256(content).hexdigest()}  {name}\n".encode()
    def asset(filename,body):
        return {"name":filename,"size":len(body),"digest":"sha256:"+hashlib.sha256(body).hexdigest(),"browser_download_url":prefix+filename}
    data={"tag_name":tag,"html_url":f"https://github.com/{UPDATE_REPOSITORY}/releases/tag/{tag}",
          "draft":False,"prerelease":False,"body":"Release notes", "assets":[asset(name,content),asset("SHA256SUMS",sums)]}
    return data,{prefix+name:content,prefix+"SHA256SUMS":sums}


class UpdateCoreTests(unittest.TestCase):
    def test_versions_compare_numerically_and_skip_older_draft_and_preview_releases(self):
        data,_=fixture()
        old,_=fixture("2.9.9")
        self.assertGreater(version_key("2.10.0"),version_key("2.9.9"))
        offer=parse_updates([{**data,"draft":True},{**data,"prerelease":True},old,data],"deb","2.9.9")
        self.assertEqual(offer.version,"2.10.0")
        self.assertIsNone(parse_updates([data],"deb","2.10.0"))
        self.assertIsNone(parse_updates([data],"deb","3.0.0"))
        for value in ("../4.0.0","1.2","1.2.3;echo","1.2.3-beta",None,"01.2.3"):
            with self.assertRaises(UpdateError):version_key(value)

    def test_each_os_selects_only_the_correct_application_binary(self):
        for kind in ("deb","rpm","arch"):
            data,_=fixture(kind=kind)
            offer=parse_updates([data],kind,"1.0.0")
            self.assertEqual(offer.package_format,kind)
            self.assertTrue(offer.package.name.startswith(PACKAGE_NAME))
            self.assertEqual(offer.notes,"Release notes")
        with self.assertRaises(UpdateError):parse_updates([],"source","1.0.0")

    def test_wrong_repo_url_missing_digest_duplicates_and_unsafe_names_are_rejected(self):
        for mutation in ("wrong_repo","no_digest","duplicate","filename","too_large","wrong_tag","negative"):
            data,_=fixture()
            item=data["assets"][0]
            if mutation=="wrong_repo":item["browser_download_url"]=item["browser_download_url"].replace(UPDATE_REPOSITORY,"other/repo")
            elif mutation=="no_digest":del item["digest"]
            elif mutation=="duplicate":data["assets"].append(dict(item))
            elif mutation=="filename":item["name"]="unrelated_2.10.0-1_all.deb"
            elif mutation=="too_large":item["size"]=90_000_000
            elif mutation=="wrong_tag":item["browser_download_url"]=item["browser_download_url"].replace("/v2.10.0/","/v2.0.0/")
            elif mutation=="negative":item["size"]=-1
            with self.subTest(mutation=mutation),self.assertRaises(UpdateError):parse_updates([data],"deb","1.0.0")

    def test_source_rpm_is_never_selected_as_the_installable_package(self):
        data,_=fixture(kind="rpm")
        data["assets"][0]["name"]=data["assets"][0]["name"].replace("noarch.rpm","src.rpm")
        with self.assertRaises(UpdateError):parse_updates([data],"rpm","1.0.0")

    def test_http_failure_and_oversized_metadata_fail_without_new_requests(self):
        requests=[]
        def failed(request,timeout):
            requests.append(request.full_url)
            raise OSError("offline")
        with self.assertRaises(UpdateError) as caught:check_for_update("deb","1.0.0",failed)
        self.assertEqual(caught.exception.code,"network")
        self.assertEqual(requests,[f"https://api.github.com/repos/{UPDATE_REPOSITORY}/releases?per_page=20"])
        with self.assertRaises(UpdateError):check_for_update("deb","1.0.0",lambda *_a,**_k:io.BytesIO(b" "*2_000_001))

    def test_download_verifies_both_digests_and_reports_actual_received_bytes(self):
        data,bodies=fixture(content=b"a"*150_000)
        offer=parse_updates([data],"deb","1.0.0")
        samples=[]
        with tempfile.TemporaryDirectory() as directory:
            package=download_update(offer,progress=lambda a,b:samples.append((a,b)),cache=directory,
                                    opener=lambda request,**_kw:io.BytesIO(bodies[request.full_url]))
            self.assertEqual(verify_download(package).read_bytes(),b"a"*150_000)
            self.assertEqual(samples[0],(0,150_000))
            self.assertEqual(samples[-1],(150_000,150_000))
            self.assertTrue(all(a<=b for (a,_),(b,_) in zip(samples,samples[1:])))
            self.assertEqual(package.path.stat().st_mode & 0o777,0o600)
            package.path.write_bytes(b"tampered")
            with self.assertRaises(UpdateError):verify_download(package)

    def test_tampered_truncated_or_oversized_packages_leave_no_partial_directory(self):
        for content in (b"bad",b"verified package bytes"[:-1],b"verified package bytesEXTRA"):
            data,bodies=fixture();offer=parse_updates([data],"deb","1.0.0");bodies[offer.package.url]=content
            with self.subTest(content=content),tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(UpdateError):download_update(offer,cache=directory,opener=lambda req,**_k:io.BytesIO(bodies[req.full_url]))
                self.assertEqual(list(Path(directory).iterdir()),[])

    def test_checksum_mismatch_stops_before_package_request(self):
        data,bodies=fixture();offer=parse_updates([data],"deb","1.0.0");calls=[]
        def opener(request,**_kwargs):
            calls.append(request.full_url)
            return io.BytesIO(b"tampered checksum list")
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(UpdateError):download_update(offer,cache=directory,opener=opener)
        self.assertEqual(calls,[offer.checksums.url])
        with self.assertRaises(UpdateError):checksum_for(b"malformed line\n",offer.package.name)
        digest="a"*64
        with self.assertRaises(UpdateError):checksum_for(f"{digest}  file\n{digest}  file\n".encode(),"file")

    def test_cancel_during_download_cleans_up_and_never_returns_a_package(self):
        data,bodies=fixture(content=b"z"*140_000);offer=parse_updates([data],"deb","1.0.0");cancel=threading.Event()
        def progress(done,total):
            if done:cancel.set()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DownloadCancelled):download_update(offer,cancel,progress,cache=directory,opener=lambda req,**_k:io.BytesIO(bodies[req.full_url]))
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_cache_symlink_is_rejected(self):
        data,bodies=fixture();offer=parse_updates([data],"deb","1.0.0")
        with tempfile.TemporaryDirectory() as directory:
            link=Path(directory)/"link";link.symlink_to(directory)
            with self.assertRaises(UpdateError):download_update(offer,cache=link,opener=lambda req,**_k:io.BytesIO(bodies[req.full_url]))

    def test_installed_version_queries_do_not_execute_shell_text(self):
        calls=[]
        def runner(command,**kwargs):
            calls.append((command,kwargs));return subprocess.CompletedProcess(command,0,"2.10.0-1")
        self.assertEqual(installed_version("deb",runner),"2.10.0")
        self.assertEqual(calls[0][0],["dpkg-query","-W","-f=${Version}",PACKAGE_NAME])
        self.assertNotIn("shell",calls[0][1])
        self.assertIsNone(installed_version("deb",lambda *a,**k:subprocess.CompletedProcess([],1,"")))
        self.assertEqual(installed_version("arch",lambda *a,**k:subprocess.CompletedProcess([],0,PACKAGE_NAME+" 1.4.0-1")),"1.4.0")


class UserLauncherTests(unittest.TestCase):
    def test_only_a_marked_matching_versioned_launcher_is_migrated(self):
        from uzeyir_doctor import APPLICATION_ID
        with tempfile.TemporaryDirectory() as directory:
            data=Path(directory);base=data/PACKAGE_NAME;old=base/'versions/1.0.0';module=old/'src/app/updates.py'
            module.parent.mkdir(parents=True);module.write_text('')
            apps=data/'applications';apps.mkdir();native=data/'bin';native.mkdir();binary=native/PACKAGE_NAME
            binary.write_text('');binary.chmod(0o755)
            desktop=apps/(APPLICATION_ID+'.desktop')
            original='[Desktop Entry]\nExec="'+str(old/PACKAGE_NAME)+'"\nX-Linux-Control-UserInstall=true\n'
            desktop.write_text(original)
            self.assertTrue(promote_native_launcher(module,data,native))
            self.assertIn('Exec='+str(binary),desktop.read_text())
            self.assertEqual((base/'previous-launcher.desktop').read_text(),original)
            self.assertTrue(module.exists())
            desktop.write_text('[Desktop Entry]\nExec=/custom/launcher\n')
            self.assertFalse(promote_native_launcher(module,data,native))
            self.assertIn('Exec=/custom/launcher',desktop.read_text())

    def test_repository_checkout_does_not_modify_user_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(promote_native_launcher(Path(directory)/'checkout/module.py',directory))
