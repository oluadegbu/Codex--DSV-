"""Deterministic archive construction and unsafe-base refusal; no network/runtime."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
import io

spec=importlib.util.spec_from_file_location('ddb_build',Path(__file__).resolve().parents[1]/'tools/build_windows_ddb_package.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)


class DDBPackageTests(unittest.TestCase):
    def test_bytes_reproducible_and_order_independent(self):
        a=build.archive({'b':b'two','a':b'one'});b=build.archive({'a':b'one','b':b'two'})
        self.assertEqual(a,b)
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertEqual(z.namelist(),['a','b']);self.assertEqual(z.getinfo('a').date_time,(1980,1,1,0,0,0))
    def test_base_hash_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.zip';p.write_bytes(b'not approved')
            with self.assertRaises(PermissionError):build.collect(False,p)
        with self.assertRaises(PermissionError):build.collect(False,None)
