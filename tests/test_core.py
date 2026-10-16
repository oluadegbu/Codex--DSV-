import json
import unittest
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

from dci.adapters import PublicSolanaRpc, RpcError
from dci.confluence import converge
from dci.models import Buy, RiskEvidence, WalletProfile
from dci.pipeline import run_fixture
from dci.research import FixtureDiscovery, WalletRegistry
from dci.scoring import ScoreConfig, assess
from dci.shadow import ShadowBook

FIXTURE = Path(__file__).parent / 'fixtures/synthetic.json'


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.registry = WalletRegistry()
        self.buys = []
        for i in range(3):
            self.registry.register(WalletProfile(str(i), str(i), D('.9'), 10, 1000))
            self.buys.append(Buy(str(i), 0, str(i), 'T', 1050+i, 100+i, D(1)))
        self.risk = RiskEvidence('T', 1090, True, True, True, D('.95'), D('.85'))

    def opportunity(self, risk=None, buys=None):
        return assess('T', 1100, converge(self.buys if buys is None else buys, self.registry, 'T', 1100),
                      self.risk if risk is None else risk, D('.9'), D('.8'))

    def test_e2e_deterministic_paper_outcome(self):
        result = run_fixture(FIXTURE)
        self.assertEqual(result, run_fixture(FIXTURE))
        self.assertEqual(D(result['score']), D('0.915'))
        self.assertTrue(result['eligible'])
        self.assertEqual([a['type'] for a in result['audit']], ['paper_entry', 'paper_mark', 'paper_exit'])
        self.assertEqual(D(result['cash']), D(900) + D(100) / D('1.003') * D('1.6') * D('.997'))

    def test_duplicate_events_do_not_inflate(self):
        a = converge(self.buys, self.registry, 'T', 1100)
        self.assertEqual(a, converge(self.buys * 3, self.registry, 'T', 1100))
        self.assertEqual(len(FixtureDiscovery(self.buys * 3).early_buyers('T', 1000, 1100)), 3)

    def test_conflicting_buy_events_rejected(self):
        conflict = replace(self.buys[0], price=D(2))
        with self.assertRaises(ValueError):
            converge(self.buys + [conflict], self.registry, 'T', 1100)
        with self.assertRaises(ValueError):
            FixtureDiscovery(self.buys + [conflict]).early_buyers('T', 1000, 1100)

    def test_finality_type_and_policy_validation(self):
        with self.assertRaises(ValueError):
            replace(self.buys[0], finalized='false')
        with self.assertRaises(ValueError):
            converge(self.buys, self.registry, 'T', 1100, window=-1)

    def test_linked_wallets_count_once(self):
        self.registry.register(WalletProfile('1', '0', D('.8'), 10, 1001))
        self.registry.register(WalletProfile('2', '0', D('.8'), 10, 1001))
        opportunity = self.opportunity()
        self.assertFalse(opportunity.eligible)
        self.assertIn('insufficient_independent_wallets', opportunity.reasons)

    def test_unknown_cluster_excluded(self):
        self.registry.register(WalletProfile('0', None, D(1), 10, 1001))
        self.assertEqual(len(converge(self.buys, self.registry, 'T', 1100).clusters), 2)

    def test_future_and_unfinalized_and_wrong_token_excluded(self):
        invalid = [replace(self.buys[0], timestamp=1101), replace(self.buys[1], finalized=False), replace(self.buys[2], token='OTHER')]
        self.assertEqual(converge(invalid, self.registry, 'T', 1100).clusters, ())

    def test_profile_point_in_time_and_samples(self):
        self.registry.register(WalletProfile('0', 'future', D(1), 10, 1200))
        self.assertEqual(self.registry.at('0', 1100).cluster, '0')
        self.registry.register(WalletProfile('1', '1', D(1), 1, 1001))
        self.assertEqual(len(converge(self.buys, self.registry, 'T', 1100).clusters), 2)
        self.assertIsNone(self.registry.at('missing', 1100))

    def test_stale_profiles_excluded(self):
        self.assertEqual(converge(self.buys, self.registry, 'T', 1100, profile_max_age=10).clusters, ())

    def test_recalibration_is_time_indexed(self):
        profile = self.registry.recalibrate('0', [D(1), D(0)], 1200)
        self.assertEqual(profile.quality, D('.5'))
        self.assertEqual(self.registry.at('0', 1100).quality, D('.9'))
        with self.assertRaises(ValueError):
            self.registry.register(profile)

    def test_risk_missing_stale_future_mismatched(self):
        c = converge(self.buys, self.registry, 'T', 1100)
        for risk in [None, replace(self.risk, as_of=1000), replace(self.risk, as_of=1101), replace(self.risk, token='OTHER')]:
            with self.subTest(risk=risk):
                result = assess('T', 1100, c, risk, D(1), D(1))
                self.assertFalse(result.eligible)
                self.assertIn('missing_or_stale_risk', result.reasons)

    def test_unknown_and_active_authorities_fail_closed(self):
        for field in ['mint_authority_revoked', 'freeze_authority_revoked', 'liquidity_verified']:
            for value in [False, None]:
                result = self.opportunity(replace(self.risk, **{field: value}))
                self.assertFalse(result.eligible)
                self.assertIn('unsafe_or_unknown_token', result.reasons)

    def test_invalid_features_and_weight_config(self):
        for value in [D('NaN'), D('Infinity'), D('-1'), D('1.1')]:
            with self.assertRaises(ValueError):
                WalletProfile('W', 'C', value, 1, 1)
        with self.assertRaises(ValueError):
            ScoreConfig(weights=(D('.1'),) * 6)
        with self.assertRaises(ValueError):
            ScoreConfig(min_clusters=1)

    def test_paper_stop_and_no_reentry(self):
        book = ShadowBook()
        book.enter(self.opportunity(), D(1))
        p = book.mark('T', D('.7'), 1200)
        self.assertEqual(p.closed_at, 1200)
        self.assertLess(p.pnl, 0)
        with self.assertRaises(ValueError):
            book.enter(self.opportunity(), D(1))
        with self.assertRaises(ValueError):
            book.mark('T', D(1), 1300)

    def test_paper_timeout_and_order(self):
        book = ShadowBook()
        book.enter(self.opportunity(), D(1))
        book.mark('T', D(1), 1200)
        with self.assertRaises(ValueError):
            book.mark('T', D(1), 1199)
        self.assertEqual(book.mark('T', D(1), 4700).closed_at, 4700)

    def test_paper_exposure_and_ineligible(self):
        book = ShadowBook(max_positions=1)
        with self.assertRaises(ValueError):
            book.enter(replace(self.opportunity(), eligible=False), D(1))
        book.enter(self.opportunity(), D(1))
        with self.assertRaises(ValueError):
            book.enter(replace(self.opportunity(), token='SECOND'), D(1))
        self.assertEqual(book.cash, D(900))
        with self.assertRaises(ValueError):
            ShadowBook(friction=D(1))

    def test_rpc_read_only_and_finalized(self):
        requests = []
        def transport(payload):
            requests.append(payload)
            return {'jsonrpc': '2.0', 'id': 1, 'result': [] if payload['method'] == 'getSignaturesForAddress' else None}
        rpc = PublicSolanaRpc(transport)
        self.assertEqual(rpc.signatures('public-address', 'cursor'), [])
        self.assertIsNone(rpc.transaction('public-signature'))
        self.assertEqual(requests[0]['params'][1]['commitment'], 'finalized')
        self.assertEqual(requests[0]['params'][1]['before'], 'cursor')
        for method in ['sendTransaction', 'requestAirdrop', 'simulateTransaction']:
            with self.assertRaises(RpcError):
                rpc.call(method, [])
        self.assertEqual(len(requests), 2)

    def test_rpc_errors_fail_closed(self):
        for response in [{'error': 'unavailable'}, {'id': 1, 'jsonrpc': '2.0'}, {'id': 2, 'jsonrpc': '2.0', 'result': []}]:
            with self.assertRaises(RpcError):
                PublicSolanaRpc(lambda _: response).signatures('W')
        with self.assertRaises(RpcError):
            PublicSolanaRpc(lambda _: {'id': 1, 'jsonrpc': '2.0', 'result': {}}).signatures('W')

    def test_repository_policy_and_state(self):
        root = Path(__file__).parents[1]
        state = json.loads((root / 'BUILD_STATE.json').read_text())
        self.assertEqual(state['mode'], 'SHADOW')
        self.assertFalse(any(state['hard_gates'].values()))
        for request in state['open_decisions']:
            text = (root / request).read_text()
            for field in ['CONTEXT', 'EVIDENCE', 'OPTIONS', 'RECOMMENDATION', 'IMPACT', 'BLOCKING:', 'HARD_GATE:']:
                self.assertIn(field, text)


if __name__ == '__main__':
    unittest.main()
