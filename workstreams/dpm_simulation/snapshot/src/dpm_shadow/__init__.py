"""Independent synthetic SHADOW research; no DPM production integration."""
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from collections.abc import Mapping

MAX_SCENARIOS = 32
MAX_ASSETS = 16
MAX_PERIODS = 512
MAX_TOTAL_SAMPLES = 65536


class InvalidResearchInput(ValueError):
    pass


def _fields(value, expected, label):
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise InvalidResearchInput(f"{label}: exact fields required")


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise InvalidResearchInput(f"{label}: use bounded decimal strings or integers")
    text = str(value)
    if len(text) > 64:
        raise InvalidResearchInput(f"{label}: decimal input too long")
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise InvalidResearchInput(f"{label}: invalid decimal") from exc
    if not number.is_finite():
        raise InvalidResearchInput(f"{label}: nonfinite decimal")
    if abs(number.as_tuple().exponent) > 40:
        raise InvalidResearchInput(f"{label}: decimal exponent outside resource bound")
    return number


def _identifier(value):
    if not isinstance(value, str) or not value or len(value) > 64:
        raise InvalidResearchInput("identifier must be a nonempty bounded string")
    if any(not (c.isascii() and (c.isalnum() or c in '_-')) for c in value):
        raise InvalidResearchInput("identifier contains disallowed characters")
    return value


def _prepare(request):
    _fields(request, ('version', 'mode', 'intent', 'scenarios'), 'request')
    if type(request['version']) is not int or request['version'] != 1:
        raise InvalidResearchInput('unsupported version')
    if request['mode'] != 'SHADOW' or request['intent'] != 'RESEARCH':
        raise InvalidResearchInput('only SHADOW RESEARCH is authorized')
    scenarios = request['scenarios']
    if type(scenarios) is not list or not 1 <= len(scenarios) <= MAX_SCENARIOS:
        raise InvalidResearchInput('scenario resource bound exceeded')
    prepared, names, samples = [], set(), 0
    for scenario in scenarios:
        _fields(scenario, ('name', 'periods', 'weights', 'returns'), 'scenario')
        name = _identifier(scenario['name'])
        if name in names:
            raise InvalidResearchInput('duplicate scenario')
        names.add(name)
        periods = scenario['periods']
        if type(periods) is not list or not 1 <= len(periods) <= MAX_PERIODS:
            raise InvalidResearchInput('period resource bound exceeded')
        if any(type(p) is not int or p != i for i, p in enumerate(periods)):
            raise InvalidResearchInput('periods must be ordered consecutive indices from zero')
        weights, returns = scenario['weights'], scenario['returns']
        if not isinstance(weights, Mapping) or not 1 <= len(weights) <= MAX_ASSETS:
            raise InvalidResearchInput('asset resource bound exceeded')
        if not isinstance(returns, Mapping) or set(weights) != set(returns):
            raise InvalidResearchInput('return assets must exactly match weights')
        samples += len(weights) * len(periods)
        if samples > MAX_TOTAL_SAMPLES:
            raise InvalidResearchInput('total sample resource bound exceeded')
        parsed_weights, parsed_returns = {}, {}
        for asset in weights:
            _identifier(asset)
        for asset in sorted(weights):
            weight = _number(weights[asset], 'weight')
            if not 0 <= weight <= 1:
                raise InvalidResearchInput('weight outside [0, 1]')
            parsed_weights[asset] = weight
            series = returns[asset]
            if type(series) is not list or len(series) != len(periods):
                raise InvalidResearchInput('series length must match periods')
            parsed = [_number(value, 'return') for value in series]
            if any(not -1 <= value <= 1 for value in parsed):
                raise InvalidResearchInput('synthetic return outside [-1, 1]')
            parsed_returns[asset] = parsed
        if sum(parsed_weights.values(), Decimal(0)) != 1:
            raise InvalidResearchInput('weights must sum exactly to one')
        prepared.append((name, periods, parsed_weights, parsed_returns))
    return prepared


def evaluate(request):
    """Analyze supplied synthetic paths using fixed initial exposures.

    No prices, accounts, orders, trading signals, allocations, or mutable runtime
    state are produced. A zero asset index stays zero after total synthetic loss.
    """
    with localcontext(Context(prec=128, rounding=ROUND_HALF_EVEN)):
        prepared = _prepare(request)
        results = []
        for name, periods, weights, returns in prepared:
            indices = dict.fromkeys(weights, Decimal(1))
            peak, drawdown = Decimal(1), Decimal(0)
            portfolio = Decimal(1)
            for i in periods:
                for asset in weights:
                    indices[asset] *= 1 + returns[asset][i]
                portfolio = sum((weights[asset] * indices[asset] for asset in weights), Decimal(0))
                peak = max(peak, portfolio)
                drawdown = max(drawdown, (peak - portfolio) / peak)
            results.append({'name': name, 'period_count': len(periods),
                            'asset_count': len(weights),
                            'cumulative_return': str(portfolio - 1),
                            'max_drawdown': str(drawdown)})
        return {'version': 1, 'mode': 'SHADOW', 'source': 'synthetic_only',
                'method': 'fixed_initial_exposure_index', 'results': results}
