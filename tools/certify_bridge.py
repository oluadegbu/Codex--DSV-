"""Repeatable local synthetic certification; live gates are observed, not inferred."""
import argparse
import hashlib
import io
import json
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dci.bridge.identity import require_non_admin


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def main():
    parser = argparse.ArgumentParser(description='Certify local BHB+HEG synthetic scope; no external activation')
    parser.add_argument('--output', default=str(ROOT / 'docs' / 'evidence'))
    args = parser.parse_args()
    require_non_admin(ROOT)
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT):
        raise PermissionError('certification evidence must stay in DCI workspace')
    output.mkdir(parents=True, exist_ok=True)
    baseline = json.loads((ROOT / 'docs/evidence/BHB_BASELINE.json').read_text())
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult).run(suite)
    passed = set(result.passed_ids)
    def gate(name, tests):
        return {'name': name, 'result': 'PASS' if all('test_bridge.BridgeTests.'+t in passed for t in tests) else 'FAIL',
                'scope': 'local synthetic shadow', 'test_evidence': tests}
    gates = [
        gate('100 cycles: zero lost/duplicate committed synthetic executions', ['test_100_cycles_zero_lost_or_duplicate_executions']),
        gate('schemas, writer/route/scope/replay rejection', ['test_all_six_schemas_are_versioned_and_match_runtime_envelope','test_wrong_route_writer_and_operation_rejected','test_replay_conflict_out_of_order_and_task_reuse']),
        gate('atomicity, single execution and Brain response-loss retry', ['test_mailbox_atomicity_and_single_execution_across_connections','test_brain_response_loss_retry_preserves_task_and_correlation']),
        gate('pause, timeout and bounded proven-prestart retry', ['test_pause_resume_and_task_timeout','test_prestart_retry_is_bounded_and_audited','test_expired_execution_fails_closed']),
        gate('crash/restart, fencing and ambiguous outcome fail-closed', ['test_real_process_crash_after_claim_is_not_reexecuted','test_crash_restart_recovery_and_stale_completion_fence','test_ambiguous_external_outcome_not_retried','test_codex_runtime_fault_is_control_degradation_not_routine_failure']),
        gate('standalone operation without ChatGPT/OpenClaw/DSV', ['test_standalone_runner_without_conversational_control_plane']),
        gate('Brain tool delivery/result return (local MCP only)', ['test_mcp_brain_task_and_result_roundtrip','test_standalone_mcp_protocol_roundtrip']),
        gate('HEG simulated approve/reject/timeout and identity/scope binding', ['test_human_approval_exact_identity_scope_expiry_and_replay','test_human_rejection_and_timeout','test_control_degradation_cannot_be_blindly_approved']),
        gate('WhatsApp simulation failure and independent email fallback', ['test_whatsapp_failure_independent_email_ack_is_not_approval','test_simulated_provider_ack_dedup_survives_restart']),
        gate('failed notification keeps task blocked; unrelated work proceeds', ['test_both_notifications_fail_keep_task_blocked_unrelated_proceeds']),
        gate('fixed Hands verification, no arbitrary shell or provider activation', ['test_hands_fixed_fixture_task_and_no_arbitrary_commands','test_external_provider_activation_rejected','test_non_admin_and_workspace_guard'])
    ]
    live = [
        {'name':'non-admin DirectiveCodex Windows identity/workspace','result':'FAIL','state':'BLOCKED','evidence':baseline['windows']},
        {'name':'actual Codex execution','result':'FAIL','state':'BLOCKED','evidence':baseline['codex'], 'bridge_gate_evidence':'docs/evidence/BHB_CODEX_GATE.json'},
        {'name':'GitHub write certification','result':'FAIL','state':'BLOCKED','evidence':baseline['github']},
        {'name':'actual ChatGPT bidirectional bridge','result':'FAIL','state':'BLOCKED','evidence':baseline['live_chatgpt']},
        {'name':'live HEG identity and WhatsApp/Pulse/email providers','result':'FAIL','state':'BLOCKED','evidence':baseline['live_notifications']}
    ]
    files = sorted([*ROOT.glob('src/dci/bridge/*.py'), *ROOT.glob('schemas/bridge/*.json'), ROOT/'tests/test_bridge.py', Path(__file__)])
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report = {'schema_version':1,'mode':'SHADOW','generated_at':datetime.now(timezone.utc).isoformat(),
              'overall':'BLOCKED' if any(g['result']=='FAIL' for g in live) else 'PASS',
              'synthetic_certification':'PASS' if result.wasSuccessful() and all(g['result']=='PASS' for g in gates) else 'FAIL',
              'target_fully_certified':False,'tests_run':result.testsRun,'test_failures':len(result.failures),'test_errors':len(result.errors),
              'git_head_at_test':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
              'tested_source_sha256':source_hashes,'synthetic_gates':gates,'live_gates':live,
              'limits':['No Windows implementation performed','No live ChatGPT task delivery claimed','No services or scheduled tasks installed','No live providers, credentials, trading or account/risk changes','External process exactly-once execution is not claimed']}
    (output/'BHB_CERTIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'BHB_TESTS.log').write_text(stream.getvalue())
    print(json.dumps({'synthetic_certification':report['synthetic_certification'],'overall':report['overall'],'tests_run':report['tests_run'],'evidence':str(output)},indent=2))
    return 0 if report['synthetic_certification']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
