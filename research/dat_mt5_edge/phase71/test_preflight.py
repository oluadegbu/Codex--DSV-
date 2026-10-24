"""Synthetic, offline admission/capability tests; no actual broker evidence."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from phase71.preflight import (GateAPlan, Target, SERVER, ALIASES, SCHEMA,
                              collector_source_audit, validate_snapshot, NoGo)

SOURCE=Path(__file__).with_name('ReadOnlyDemoPreflight.mq5').read_text()
T=1735776000000


def fixture():
    target=Target(login=7,company='OFFLINE_FIXTURE_COMPANY',currency='USD',
                  terminal_name='OFFLINE_FIXTURE_TERMINAL',terminal_path='FIXTURE_BINARY_PATH',
                  data_path='FIXTURE_ISOLATED_DATA_PATH',terminal_build=5000,
                  symbols={a:'FIXTURE_'+a for a in ALIASES})
    plan=GateAPlan(True,'FIXTURE_APPROVAL','FIXTURE_NONCE',T,T+600000,
                  'FIXTURE_INVESTOR_EVIDENCE','FIXTURE_ISOLATION_EVIDENCE','FIXTURE_REVIEW_EVIDENCE',
                  collector_source_audit(SOURCE)['source_sha256'],'a'*64,'b'*64,
                  'FIXTURE_COMPILATION_EVIDENCE_NOT_REAL',(target,))
    symbols=[]
    for alias in ALIASES:
        symbols.append(dict(alias=alias,broker_symbol=target.symbols[alias],exists=True,selected=True,custom=False,
            calc_mode=0,trade_mode=4,execution_mode=2,filling_mode=3,digits=2,
            stops_level_points=5,freeze_level_points=0,point='0.01',contract_size='100',
            tick_size='0.01',tick_value='1',tick_value_profit='1',tick_value_loss='1',
            volume_min='0.01',volume_max='1',volume_step='0.01',volume_limit='0',
            margin_initial='0',margin_maintenance='0',currency_profit='USD',currency_margin='USD',
            margin_buy_minlot='1',margin_sell_minlot='1',
            quote=dict(bid='100.00',ask='100.02',time_msc=T+990,age_ms=10,age_basis='SERVER_RELATIVE_ESTIMATE')))
    snapshot=dict(schema=SCHEMA,approval_reference='FIXTURE_APPROVAL',session_nonce='FIXTURE_NONCE',
        captured_utc_ms=T+1000,private_identity=dict(login=7,server=SERVER,company=target.company,currency='USD',
        trade_mode=0,trade_allowed=False,expert_trade_allowed=False,leverage=100,margin_mode=2,positions=0,orders=0),
        terminal=dict(name=target.terminal_name,build=5000,path=target.terminal_path,data_path=target.data_path,
        connected=True,trade_allowed=False,dlls_allowed=False,script_trade_allowed=False,script_dlls_allowed=False,ping_us=50000),
        available_symbol_count=100,symbols=symbols,duration_us=100000,final_fence_ok=True)
    return plan,snapshot


class Preflight(unittest.TestCase):
    def setUp(self):self.plan,self.snapshot=fixture()

    def check(self,snapshot=None,plan=None,source=SOURCE):
        raw=json.dumps(snapshot if snapshot is not None else self.snapshot,allow_nan=False).encode()
        return validate_snapshot(raw,plan or self.plan,source)

    def reject(self,snapshot=None,plan=None,source=SOURCE):
        out=self.check(snapshot,plan,source)
        self.assertEqual(out['status'],'NO_GO')
        self.assertFalse(out['gate_b_authorized']);self.assertFalse(out['broker_order_authority'])
        return out

    def test_valid_fixture_snapshot_only_not_connected_certificate(self):
        out=self.check();self.assertEqual(out['status'],'PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY')
        self.assertEqual(out['checked_aliases'],sorted(ALIASES))
        self.assertFalse(out['snapshot_authenticated']);self.assertFalse(out['gate_b_authorized'])

    def test_disabled_empty_default(self):self.reject(plan=GateAPlan())

    def test_exactly_one_allowlisted_account_required(self):
        for targets in ((),self.plan.targets*2):
            with self.subTest(targets=targets):self.reject(plan=replace(self.plan,targets=targets))

    def test_real_contest_unknown_and_bool_account_type_rejected(self):
        for kind in (1,2,3,None,False,'DEMO'):
            with self.subTest(kind=kind):
                self.snapshot['private_identity']['trade_mode']=kind;self.reject()

    def test_login_server_mismatch_and_bool_login_rejected(self):
        for key,value in (('login',8),('login',True),('server','OTHER_DEMO_SERVER')):
            with self.subTest(key=key,value=value):
                _,s=fixture();s['private_identity'][key]=value;self.reject(s)

    def test_no_fallback_server_in_plan(self):
        t=replace(self.plan.targets[0],server='OTHER_DEMO_SERVER')
        self.reject(plan=replace(self.plan,targets=(t,)))

    def test_company_currency_identity_mismatch(self):
        for key,value in (('company','OTHER'),('currency','EUR')):
            with self.subTest(key=key):
                _,s=fixture();s['private_identity'][key]=value;self.reject(s)

    def test_trading_account_permission_denies_read_only_admission(self):
        for value in (True,0,None,'false'):
            with self.subTest(value=value):
                self.snapshot['private_identity']['trade_allowed']=value;self.reject()

    def test_expert_permission_is_diagnostic_not_an_order_grant(self):
        self.snapshot['private_identity']['expert_trade_allowed']=True
        out=self.check();self.assertTrue(out['account_expert_permission_observed'])
        self.assertFalse(out['broker_order_authority'])

    def test_terminal_and_script_mutation_flags_must_be_false(self):
        for key in ('trade_allowed','dlls_allowed','script_trade_allowed','script_dlls_allowed'):
            with self.subTest(key=key):
                _,s=fixture();s['terminal'][key]=True;self.reject(s)

    def test_terminal_path_name_build_mismatch(self):
        for key,value in (('path','UNAPPROVED_PATH'),('data_path','SHARED_PATH'),('name','OTHER'),('build',5001),('build',True)):
            with self.subTest(key=key):
                _,s=fixture();s['terminal'][key]=value;self.reject(s)

    def test_disconnected_or_missing_latency_rejected(self):
        self.snapshot['terminal']['connected']=False;self.reject()
        for ping in (0,-1,1000001,True):
            with self.subTest(ping=ping):
                _,s=fixture();s['terminal']['ping_us']=ping;self.reject(s)

    def test_existing_exposure_never_closed_or_adopted(self):
        for field in ('positions','orders'):
            with self.subTest(field=field):
                _,s=fixture();s['private_identity'][field]=1;self.reject(s)

    def test_missing_or_overlong_approval_window(self):
        for start,end in ((0,1),(T,T),(T,T+600001),(True,T+1)):
            with self.subTest(start=start,end=end):self.reject(plan=replace(self.plan,valid_from_ms=start,valid_until_ms=end))

    def test_expired_and_pre_window_captures_rejected(self):
        for capture in (T-1,T+600000):
            with self.subTest(capture=capture):self.snapshot['captured_utc_ms']=capture;self.reject()

    def test_capture_must_finish_before_approval_expiry(self):
        self.snapshot['captured_utc_ms']=T+599999;self.reject()

    def test_runtime_bound_and_final_fence(self):
        for duration in (-1,5000001,True):
            with self.subTest(duration=duration):
                _,s=fixture();s['duration_us']=duration;self.reject(s)
        _,s=fixture();s['final_fence_ok']=False;self.reject(s)

    def test_nonce_approval_reference_binding(self):
        for key in ('session_nonce','approval_reference'):
            with self.subTest(key=key):
                _,s=fixture();s[key]='OTHER_SESSION';self.reject(s)

    def test_operator_evidence_is_required_but_not_authenticated_by_snapshot(self):
        for key in ('investor_access_evidence','isolated_terminal_evidence','independent_review_evidence','compilation_evidence'):
            with self.subTest(key=key):self.reject(plan=replace(self.plan,**{key:''}))

    def test_source_and_binary_manifest_hashes_required(self):
        for key in ('collector_source_sha256','compiled_collector_sha256','terminal_binary_sha256'):
            with self.subTest(key=key):self.reject(plan=replace(self.plan,**{key:'invalid'}))

    def test_all_four_exact_symbols_no_suffix_fallback(self):
        self.snapshot['symbols'][2]['broker_symbol']='UNAPPROVED_GOLD_SUFFIX';self.reject()
        _,s=fixture();s['symbols'].pop();self.reject(s)

    def test_duplicate_alias_or_symbol_mapping_denied(self):
        self.snapshot['symbols'][1]['alias']='EURUSD';self.reject()
        t=self.plan.targets[0];mapping=dict(t.symbols);mapping['GBPUSD']=mapping['EURUSD']
        self.reject(plan=replace(self.plan,targets=(replace(t,symbols=mapping),)))

    def test_symbol_must_exist_selected_not_custom(self):
        for key,value in (('exists',False),('selected',False),('custom',True)):
            with self.subTest(key=key):
                _,s=fixture();s['symbols'][0][key]=value;self.reject(s)

    def test_unknown_calc_mode_and_invalid_contract_values(self):
        for key,value in (('calc_mode',999),('digits',-1),('tick_size','0'),('contract_size','NaN'),('tick_value_loss','0'),('stops_level_points',-1),('freeze_level_points',True)):
            with self.subTest(key=key):
                _,s=fixture();s['symbols'][0][key]=value;self.reject(s)

    def test_volume_rules(self):
        for key,value in (('volume_min','2'),('volume_step','0'),('volume_min','0.015')):
            with self.subTest(key=key,value=value):
                _,s=fixture();s['symbols'][0][key]=value;self.reject(s)

    def test_price_precision_grid_and_quote_integrity(self):
        for key,value in (('bid','100.03'),('bid','100.001'),('ask','0')):
            with self.subTest(key=key,value=value):
                _,s=fixture();s['symbols'][0]['quote'][key]=value;self.reject(s)
        _,s=fixture();s['symbols'][0]['point']='0.001';self.reject(s)

    def test_stale_negative_unknown_quote_age(self):
        for key,value in (('age_ms',5001),('age_ms',-1),('age_basis','UNVERIFIED_UTC'),('time_msc',0)):
            with self.subTest(key=key):
                _,s=fixture();s['symbols'][0]['quote'][key]=value;self.reject(s)

    def test_missing_margin_estimates_rejected(self):
        self.snapshot['symbols'][0]['margin_buy_minlot']='0';self.reject()

    def test_zero_initial_margin_and_stop_level_are_data_not_guarantees(self):
        self.snapshot['symbols'][0]['stops_level_points']=0
        out=self.check();self.assertEqual(out['status'],'PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY')
        self.assertFalse(out['margin_estimates_certify_order_acceptance'])

    def test_missing_unknown_fields_secrets_never_echoed(self):
        secret='DO_NOT_ECHO_FIXTURE_SECRET'
        self.snapshot['password']=secret
        out=self.reject();text=json.dumps(out)
        self.assertNotIn(secret,text);self.assertNotIn('FIXTURE_BINARY_PATH',text)
        self.assertNotIn('OFFLINE_FIXTURE_COMPANY',text)

    def test_invalid_json_duplicates_and_size_fail_closed(self):
        for raw in (b'{',b'{"x":1,"x":2}',b'{}'*40000,b'NaN',b'[]'):
            with self.subTest(length=len(raw)):
                self.assertEqual(validate_snapshot(raw,self.plan,SOURCE)['status'],'NO_GO')

    def test_unknown_target_schema_does_not_accept_secret_fields(self):
        with self.assertRaises(TypeError):Target(password='DO_NOT_ACCEPT')

    def test_collector_source_closed_call_surface(self):
        out=collector_source_audit(SOURCE)
        self.assertFalse(out['native_compilation_verified'])

    def test_order_sdk_network_import_and_symbol_selection_calls_denied(self):
        for bad in ('OrderSend','OrderSendAsync','OrderCheck','PositionClose','SymbolSelect','WebRequest','AccountLogin','TerminalClose','FileDelete'):
            with self.subTest(call=bad),self.assertRaises(NoGo):collector_source_audit(SOURCE+'\nvoid Hack(){'+bad+'();}\n')

    def test_forbidden_preprocessor_or_dynamic_surface(self):
        for added in ('\n#include <Trade/Trade.mqh>','\n#import "unsafe.dll"','\n#define Submit OrderSend','\ntypedef int CALLBACK;'):
            with self.subTest(added=added),self.assertRaises(NoGo):collector_source_audit(SOURCE+added)

    def test_harmless_mutation_still_breaks_approved_source_hash(self):
        self.reject(source=SOURCE+'\n// different reviewed artifact\n')

    def test_read_only_margin_calculation_is_explicit_not_order_sending(self):
        self.assertIn('OrderCalcMargin',SOURCE)
        self.assertNotIn('OrderSend(',SOURCE)
        self.assertNotIn('SymbolSelect(',SOURCE)

    def test_validator_needs_no_network_or_process(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')),patch('subprocess.Popen',side_effect=AssertionError('process forbidden')):
            self.assertEqual(self.check()['status'],'PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY')

    def test_repeated_offline_validation_is_deterministic(self):
        self.assertEqual(self.check(),self.check())


if __name__=='__main__':unittest.main()
