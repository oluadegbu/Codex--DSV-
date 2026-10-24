"""Offline snapshot admission/redaction only: no SDK, account login or order API."""
from dataclasses import dataclass, field
import hashlib
import json
import re

from phase4.collector import unique
from phase6_2.readiness import decimal, positive, nonnegative

SERVER = 'VantageMarkets-Demo'  # explicitly designated by the user; not proof of DEMO
ALIASES = ('EURUSD','GBPUSD','XAUUSD','BTCUSD')
SCHEMA = 'DAT_MT5_READONLY_PREFLIGHT_V1'
HELPERS = {'J','B','Label','Pinned','DI','II','SI','SymbolSnapshot','OnStart'}
READ_API = {'StringReplace','StringLen','StringFind','StringSubstr','TimeGMT','GetMicrosecondCount',
    'AccountInfoInteger','AccountInfoString','TerminalInfoInteger','TerminalInfoString','MQLInfoInteger',
    'PositionsTotal','OrdersTotal','SymbolInfoDouble','SymbolInfoInteger','SymbolInfoString',
    'MathIsValidNumber','DoubleToString','IntegerToString','SymbolInfoTick','TimeTradeServer',
    'OrderCalcMargin','SymbolsTotal','FileIsExist','FileOpen','FileWriteString','FileClose',
    'Print','StringToCharArray','FileSize','ResetLastError','GetLastError','IsStopped'}


class NoGo(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise NoGo(code)


def collector_source_audit(source):
    """Closed source call surface, not a substitute for native compilation/review."""
    require(type(source) is str and 0 < len(source) <= 32768, 'COLLECTOR_SOURCE_BOUNDS')
    clean=re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',lambda m:'""' if m[0].startswith('"') else '',source,flags=re.S)
    for line in clean.splitlines():
        if line.lstrip().startswith('#'):
            require(bool(re.fullmatch(r'\s*#property\s+(?:strict|script_show_inputs|version\s+"")\s*',line)), 'COLLECTOR_PREPROCESSOR')
    require(not re.search(r'\b(?:class|struct|typedef|template|union)\b|::|->',clean),'COLLECTOR_DYNAMIC_SURFACE')
    definitions=set(re.findall(r'\b(?:bool|void|string|double|long)\s+(\w+)\s*\(',clean))
    require(definitions == HELPERS,'COLLECTOR_FUNCTION_SET')
    calls=set(re.findall(r'\b([A-Za-z_]\w*)\s*\(',clean))
    require(calls <= READ_API|HELPERS|{'if','for'},'COLLECTOR_UNKNOWN_CALL')
    require('OrderCalcMargin' in calls and 'FileWriteString' in calls,'COLLECTOR_REQUIRED_READS')
    return {'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'call_surface':'CLOSED_READS_PLUS_BOUNDED_LOCAL_OUTPUT',
            'native_compilation_verified':False}


@dataclass(frozen=True)
class Target:
    login: int = 0  # private operator metadata; never returned in report
    server: str = SERVER
    company: str = ''
    currency: str = ''
    terminal_name: str = ''
    terminal_path: str = ''
    data_path: str = ''
    terminal_build: int = 0
    symbols: dict = field(default_factory=dict)  # exact alias -> broker symbol, no suffix fallback


@dataclass(frozen=True)
class GateAPlan:
    approval_received: bool = False
    approval_reference: str = ''
    session_nonce: str = ''
    valid_from_ms: int = 0
    valid_until_ms: int = 0
    investor_access_evidence: str = ''
    isolated_terminal_evidence: str = ''
    independent_review_evidence: str = ''
    collector_source_sha256: str = ''
    compiled_collector_sha256: str = ''
    terminal_binary_sha256: str = ''
    compilation_evidence: str = ''
    targets: tuple = ()  # exactly one explicitly approved account; empty default


def plan_checks(plan, source):
    require(type(plan) is GateAPlan,'PLAN_TYPE')
    require(plan.approval_received is True,'GATE_A_APPROVAL_REQUIRED')
    require(len(plan.targets)==1 and type(plan.targets[0]) is Target,'ONE_ACCOUNT_ALLOWLIST_REQUIRED')
    for label in (plan.approval_reference,plan.session_nonce):
        require(type(label) is str and bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}',label)),'BOUNDED_APPROVAL_LABELS')
    require(type(plan.valid_from_ms) is int and type(plan.valid_until_ms) is int and
            0 < plan.valid_from_ms < plan.valid_until_ms <= plan.valid_from_ms+600000,'BOUNDED_APPROVAL_WINDOW')
    require(all(type(x) is str and 0 < len(x) <= 128 for x in
                (plan.investor_access_evidence,plan.isolated_terminal_evidence,
                 plan.independent_review_evidence,plan.compilation_evidence)), 'INDEPENDENT_EVIDENCE_REQUIRED')
    audit=collector_source_audit(source)
    require(plan.collector_source_sha256==audit['source_sha256'],'COLLECTOR_HASH_MISMATCH')
    for digest in (plan.compiled_collector_sha256,plan.terminal_binary_sha256):
        require(type(digest) is str and bool(re.fullmatch('[a-f0-9]{64}',digest)),'COMPILED_AND_TERMINAL_HASHES_REQUIRED')
    t=plan.targets[0]
    require(type(t.login) is int and t.login > 0 and t.server==SERVER,'EXACT_DESIGNATED_ACCOUNT_SERVER_REQUIRED')
    require(all(type(x) is str and 0 < len(x) <= 512 for x in
                (t.company,t.currency,t.terminal_name,t.terminal_path,t.data_path)),'EXACT_TARGET_METADATA_REQUIRED')
    require(t.terminal_path!=t.data_path,'ISOLATED_BINARY_DATA_PATHS_REQUIRED')
    require(type(t.terminal_build) is int and t.terminal_build > 0,'EXACT_BUILD_REQUIRED')
    require(type(t.symbols) is dict and set(t.symbols)==set(ALIASES),'ALL_FOUR_SYMBOL_MAPPINGS_REQUIRED')
    require(all(type(x) is str and bool(re.fullmatch(r'[A-Za-z0-9_.#-]{1,96}',x)) for x in t.symbols.values()),'EXACT_SYMBOL_NAMES_REQUIRED')
    require(len(set(t.symbols.values()))==4,'SYMBOL_MAPPING_COLLISION')
    return t


def keys(obj, expected, code):
    require(type(obj) is dict and set(obj)==set(expected.split()),code)


def integer(value, minimum=0, maximum=2**63-1):
    return type(value) is int and minimum <= value <= maximum


def validate_snapshot(raw, plan, source):
    """Input may be private. Return fixed codes/aliases only, never input values/errors.

    Evidence references are operator attestations, not cryptographic authentication.
    Matching a supplied snapshot never grants a connection or Gate B permission.
    """
    base={'gate_b_authorized':False,'broker_order_authority':False,
          'snapshot_authenticated':False,'independent_operational_review_required':True,
          'private_input_echoed':False}
    try:
        t=plan_checks(plan,source)
        require(type(raw) is bytes and 0 < len(raw) <= 65536,'SNAPSHOT_SIZE')
        q=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(NoGo('NONFINITE_JSON')))
        keys(q,'schema approval_reference session_nonce captured_utc_ms private_identity terminal available_symbol_count symbols duration_us final_fence_ok','SNAPSHOT_SCHEMA')
        require(q['schema']==SCHEMA,'SNAPSHOT_VERSION')
        require(q['approval_reference']==plan.approval_reference and q['session_nonce']==plan.session_nonce,'SESSION_BINDING')
        require(integer(q['captured_utc_ms']) and plan.valid_from_ms <= q['captured_utc_ms'] < plan.valid_until_ms,'CAPTURE_OUTSIDE_APPROVAL')
        require(integer(q['duration_us'],0,5000000),'CAPTURE_DURATION')
        require(q['captured_utc_ms']+(q['duration_us']+999)//1000 < plan.valid_until_ms,'CAPTURE_END_OUTSIDE_APPROVAL')
        require(q['final_fence_ok'] is True,'FINAL_IDENTITY_FENCE')
        a=q['private_identity']
        keys(a,'login server company currency trade_mode trade_allowed expert_trade_allowed leverage margin_mode positions orders','ACCOUNT_SCHEMA')
        require(type(a['login']) is int and a['login']==t.login and a['server']==t.server,'ACCOUNT_SERVER_MISMATCH')
        require(a['company']==t.company and a['currency']==t.currency,'COMPANY_CURRENCY_MISMATCH')
        require(type(a['trade_mode']) is int and a['trade_mode']==0,'REAL_CONTEST_UNKNOWN_ACCOUNT_REJECTED')
        require(a['trade_allowed'] is False and type(a['expert_trade_allowed']) is bool,'READ_ONLY_ACCOUNT_REQUIRED')
        require(integer(a['positions'],0,0) and integer(a['orders'],0,0),'ACCOUNT_NOT_FLAT')
        require(integer(a['leverage'],1,10000) and integer(a['margin_mode'],0,2),'ACCOUNT_MARGIN_METADATA')
        term=q['terminal']
        keys(term,'name build path data_path connected trade_allowed dlls_allowed script_trade_allowed script_dlls_allowed ping_us','TERMINAL_SCHEMA')
        require(term['name']==t.terminal_name and type(term['build']) is int and term['build']==t.terminal_build and
                term['path']==t.terminal_path and term['data_path']==t.data_path,'TERMINAL_BUILD_PATH_MISMATCH')
        require(term['connected'] is True,'DISCONNECTED')
        require(all(term[k] is False for k in ('trade_allowed','dlls_allowed','script_trade_allowed','script_dlls_allowed')),'TERMINAL_SCRIPT_TRADING_OR_DLL_ENABLED')
        require(integer(term['ping_us'],1,1000000),'LATENCY_MISSING_OR_HIGH')
        require(integer(q['available_symbol_count'],4),'AVAILABLE_SYMBOL_COUNT')
        require(type(q['symbols']) is list and len(q['symbols'])==4,'SYMBOL_COUNT')
        aliases=[]
        for s in q['symbols']:
            keys(s,'alias broker_symbol exists selected custom calc_mode trade_mode execution_mode filling_mode digits stops_level_points freeze_level_points point contract_size tick_size tick_value tick_value_profit tick_value_loss volume_min volume_max volume_step volume_limit margin_initial margin_maintenance currency_profit currency_margin margin_buy_minlot margin_sell_minlot quote','SYMBOL_SCHEMA')
            alias=s['alias'];require(type(alias) is str and alias in ALIASES and alias not in aliases,'SYMBOL_ALIAS')
            require(s['broker_symbol']==t.symbols[alias],'SYMBOL_MAPPING_MISMATCH')
            require(s['exists'] is True and s['selected'] is True and s['custom'] is False,'BROKER_SYMBOL_UNAVAILABLE_OR_CUSTOM')
            require(integer(s['digits'],0,10) and type(s['calc_mode']) is int and s['calc_mode'] in (0,2,3,4,5) and integer(s['trade_mode'],0,4)
                    and integer(s['execution_mode'],0,3) and integer(s['filling_mode'],0,15),'SYMBOL_ENUM_METADATA')
            require(integer(s['stops_level_points']) and integer(s['freeze_level_points']),'STOP_FREEZE_METADATA')
            for k in ('point','contract_size','tick_size','tick_value','tick_value_profit','tick_value_loss',
                      'volume_min','volume_max','volume_step','margin_buy_minlot','margin_sell_minlot'):
                positive(s[k])
            for k in ('volume_limit','margin_initial','margin_maintenance'):nonnegative(s[k])
            require(decimal(s['volume_max'])>=decimal(s['volume_min']) and
                    decimal(s['volume_min'])%decimal(s['volume_step'])==0,'VOLUME_RULES')
            require(decimal(s['point'])==decimal('1').scaleb(-s['digits']),'DIGITS_POINT_MISMATCH')
            require(decimal(s['tick_size'])%decimal(s['point'])==0,'TICK_POINT_MISMATCH')
            require(all(type(s[k]) is str and 0<len(s[k])<=16 for k in ('currency_profit','currency_margin')),'SYMBOL_CURRENCY_METADATA')
            quote=s['quote'];keys(quote,'bid ask time_msc age_ms age_basis','QUOTE_SCHEMA')
            bid=positive(quote['bid']);ask=positive(quote['ask'])
            require(bid<=ask and bid%decimal(s['tick_size'])==0 and ask%decimal(s['tick_size'])==0,'QUOTE_CROSSED_OR_OFF_GRID')
            require(integer(quote['time_msc'],1) and integer(quote['age_ms'],0,5000) and
                    quote['age_basis']=='SERVER_RELATIVE_ESTIMATE','QUOTE_AGE_OR_CLOCK_METADATA')
            aliases.append(alias)
        return {**base,'status':'PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY','failure_codes':[],
                'checked_aliases':sorted(aliases),'account_expert_permission_observed':a['expert_trade_allowed'],
                'quote_clock_certified_for_execution':False,
                'margin_estimates_certify_order_acceptance':False}
    except NoGo as exc:
        return {**base,'status':'NO_GO','failure_codes':[str(exc)],'checked_aliases':[]}
    except (ValueError,TypeError,KeyError,ArithmeticError,RecursionError):
        return {**base,'status':'NO_GO','failure_codes':['INVALID_OR_UNTRUSTED_INPUT'],'checked_aliases':[]}


def main():
    """Offline explicit-file CLI. Never pass credential files as input."""
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def read_bounded(path,limit=65536):
        with path.open('rb') as stream:
            data=stream.read(limit+1)
        require(len(data)<=limit,'FILE_SIZE')
        return data
    try:
        private=json.loads(read_bounded(args.plan),object_pairs_hook=unique)
        require(type(private) is dict,'PLAN_SCHEMA')
        targets=private.pop('targets',[])
        require(type(targets) is list and len(targets)<=1,'ONE_ACCOUNT_ALLOWLIST_REQUIRED')
        plan=GateAPlan(**private,targets=tuple(Target(**t) for t in targets))
        source=read_bounded(Path(__file__).with_name('ReadOnlyDemoPreflight.mq5'),32768).decode('utf-8')
        out=validate_snapshot(read_bounded(args.snapshot),plan,source)
    except (OSError,ValueError,TypeError,KeyError,RecursionError):
        out={'status':'NO_GO','failure_codes':['INVALID_PRIVATE_PLAN_OR_ARTIFACT'],
             'gate_b_authorized':False,'broker_order_authority':False,'private_input_echoed':False}
    # Output is an explicitly selected isolated research destination; no overwrite.
    if args.output.resolve() in (args.plan.resolve(),args.snapshot.resolve()):
        raise SystemExit('NO_GO: output/input overlap')
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(out,stream,sort_keys=True,indent=2)
    print(out['status'])
    return 0 if out['status']=='PASS_READ_ONLY_SNAPSHOT_CHECKS_ONLY' else 2


if __name__=='__main__':
    raise SystemExit(main())
