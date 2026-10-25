"""Independent offline signed-protocol/receipt fixtures. No real keys or GitHub.

Uses existing reviewed tests against memory transport and disposable SQLite.
Synthetic ephemeral fixture keys are not trust enrollment or credentials.
"""
import argparse
from pathlib import Path
import sys
import unittest

CASES={
 'signed-receipts':['test_windows_adapter.ReceiptContractTests.test_signed_fixture_cycle_and_duplicate',
                    'test_windows_adapter.ReceiptContractTests.test_signature_tampering_before_worker'],
 'recovery':['test_windows_adapter.ReceiptContractTests.test_sealed_recovery_no_second_effect',
             'test_windows_adapter.ReceiptContractTests.test_uncertain_intent_never_reruns',
             'test_document_bridge.DDBTests.test_corrupt_audit_prevents_publication_and_execution'],
 'policy':['test_document_bridge.DDBTests.test_stale_report_and_expired_directive_cannot_execute',
           'test_document_bridge.DDBTests.test_wrong_signature_and_worker_cannot_sign_directive',
           'test_document_bridge.DDBTests.test_stream_gap_mirror_tamper_and_rollback_are_rejected',
           'test_windows_adapter.WindowsAdapterTests.test_workspace_rejection',
           'test_windows_adapter.WindowsAdapterTests.test_tools_rejected'],
}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=CASES);a=p.parse_args()
 sys.path.insert(0,str(Path(__file__).resolve().parent/'tests'))
 suite=unittest.defaultTestLoader.loadTestsFromNames(CASES[a.case])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
