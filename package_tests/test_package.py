"""Meaningful package boundary rejection; native runtime smoke belongs to Windows CI."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from windows_package_runtime import verify_package
from build_windows_package import unpack


class PackageTests(unittest.TestCase):
    def make(self, root):
        app=root/'app';app.mkdir()
        git=root/'runtime/git/cmd/git.exe';git.parent.mkdir(parents=True);git.write_bytes(b'synthetic not executable')
        source=app/'CODEX.md';source.write_bytes(b'SHADOW')
        manifest={'schema_version':1,'mode':'SHADOW','package_version':'0.1.3','architecture':'windows-amd64','source_commit':'a'*40,
                  'files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (git,source)}}
        (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
        return app,manifest

    def test_tampered_package_source_rejected_before_path_change(self):
        with tempfile.TemporaryDirectory() as d:
            app,manifest=self.make(Path(d));(app/'CODEX.md').write_bytes(b'CHANGED')
            prior=os.environ.get('PATH')
            with self.assertRaises(PermissionError):verify_package(app)
            self.assertEqual(os.environ.get('PATH'),prior)

    def test_missing_runtime_and_wrong_version_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);app,manifest=self.make(root)
            (root/'runtime/git/cmd/git.exe').unlink()
            with self.assertRaises(PermissionError):verify_package(app)
            manifest['package_version']='unknown';(root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            with self.assertRaises(PermissionError):verify_package(app)

    def test_path_traversal_in_manifest_and_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);app,manifest=self.make(root)
            manifest['files']['../outside']='0'*64;(root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
            with self.assertRaises(PermissionError):verify_package(app)
            archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('../outside','forbidden')
            with self.assertRaises(PermissionError):unpack(archive,root/'unpack')
            self.assertFalse((root/'unpack').exists())

    def test_redirected_package_file_cannot_escape_boundary(self):
        if os.name=='nt':self.skipTest('No symlink privilege requested; native boundary remains gated')
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            root=Path(d);app,manifest=self.make(root);(app/'CODEX.md').unlink()
            external=Path(outside)/'CODEX.md';external.write_bytes(b'SHADOW');(app/'CODEX.md').symlink_to(external)
            with self.assertRaises(PermissionError):verify_package(app)

    def test_success_uses_only_process_path_and_no_installer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);app,manifest=self.make(root);prior=os.environ.get('PATH','')
            try:
                self.assertEqual(verify_package(app),manifest)
                self.assertEqual(os.environ['PATH'].split(os.pathsep)[0],str(root/'runtime/git/cmd'))
            finally:os.environ['PATH']=prior


if __name__=='__main__':unittest.main()
