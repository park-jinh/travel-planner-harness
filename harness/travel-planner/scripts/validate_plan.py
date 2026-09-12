"""Offline temporal/budget checks; does not verify external facts."""
import json
import math
import re
import sys
from datetime import datetime
from decimal import Decimal


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be a string')
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError('timestamps must include timezone')
    return result


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)) or not math.isfinite(value) or value < 0:
        raise ValueError('expected finite non-negative number')
    return value


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a nonempty string')


def record(value, required, field):
    if not isinstance(value, dict):
        raise ValueError(f'{field} must be an object')
    missing = set(required) - value.keys()
    if missing:
        raise ValueError(f'{field}: missing fields {sorted(missing)}')


def structure(plan):
    record(plan, ('version', 'budget_currency', 'budget_amount', 'items', 'costs', 'required_ids', 'unresolved'), 'plan')
    if type(plan['version']) is not int:
        raise ValueError('version must be an integer')
    for field in ('items', 'costs', 'required_ids', 'unresolved'):
        if not isinstance(plan[field], list):
            raise ValueError(f'{field} must be an array')
    for field in ('required_ids', 'unresolved'):
        for value in plan[field]:
            text(value, field)
    for item in plan['items']:
        record(item, ('id', 'candidate_id', 'kind', 'start', 'end', 'windows', 'incoming_minutes', 'evidence_status'), 'item')
        for field in ('id', 'kind', 'evidence_status'):
            text(item[field], field)
        if item['candidate_id'] is not None:
            text(item['candidate_id'], 'candidate_id')
        if item['windows'] is not None:
            if not isinstance(item['windows'], list):
                raise ValueError('windows must be an array or null')
            for window in item['windows']:
                if not isinstance(window, list) or len(window) != 2:
                    raise ValueError('window must be a two-element array')
    for cost in plan['costs']:
        record(cost, ('id', 'label', 'currency', 'low_amount', 'high_amount'), 'cost')
        for field in ('id', 'label', 'currency'):
            text(cost[field], field)


def money(value):
    number(value)
    return Decimal(str(value))


def json_amount(value):
    # Preserve the existing numeric JSON interface; comparisons use Decimal.
    return int(value) if value == value.to_integral_value() else float(value)


def validate(plan):
    structure(plan)
    errors, warnings = [], []
    if plan['version'] != 2:
        raise ValueError('unsupported version: migrate to version 2')
    currency = plan['budget_currency']
    if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
        raise ValueError('budget_currency must be a three-letter currency code')
    budget = plan['budget_amount']
    if budget is not None:
        budget = money(budget)
    seen, visited, previous_end = set(), set(), None
    if not plan['items']:
        errors.append('empty itinerary')
    for item in plan['items']:
        ident = item['id']
        if not isinstance(ident, str) or not ident:
            raise ValueError('item id must be nonempty string')
        if ident in seen:
            errors.append(f'{ident}: duplicate item id')
        seen.add(ident)
        kind = item['kind']
        if kind not in ('visit', 'meal', 'rest', 'lodging', 'transport'):
            raise ValueError('unknown item kind')
        status = item['evidence_status']
        if status not in ('verified', 'estimated', 'unknown', 'conflicting'):
            raise ValueError('unknown evidence status')
        start, end = timestamp(item['start']), timestamp(item['end'])
        if start >= end:
            errors.append(f'{ident}: end must follow start')
        incoming = item['incoming_minutes']
        if incoming is None:
            warnings.append(f'{ident}: unknown transfer duration')
        else:
            number(incoming)
        if previous_end is None and incoming != 0:
            errors.append(f'{ident}: first transfer must be zero')
        if item.get('latest_entry') is not None and start > timestamp(item['latest_entry']):
            errors.append(f'{ident}: after latest entry/order time')
        if previous_end is not None:
            gap = (start - previous_end).total_seconds() / 60
            if gap < 0:
                errors.append(f'{ident}: overlap or unsorted itinerary')
            elif incoming is not None and gap < incoming:
                errors.append(f'{ident}: insufficient transfer time')
        previous_end = max(previous_end, end) if previous_end else end
        windows = item['windows']
        if windows is None:
            if kind in ('visit', 'meal', 'lodging'):
                warnings.append(f'{ident}: unknown opening/check-in window')
        else:
            parsed = [(timestamp(a), timestamp(b)) for a, b in windows]
            if any(a >= b for a, b in parsed):
                raise ValueError('invalid opening window')
            if not any(a <= start and end <= b for a, b in parsed):
                errors.append(f'{ident}: outside available windows')
        if status != 'verified':
            warnings.append(f'{ident}: evidence {status}')
        if item['candidate_id'] is not None and kind in ('visit', 'meal', 'lodging'):
            visited.add(item['candidate_id'])
    for required in plan['required_ids']:
        if required not in visited:
            errors.append(f'{required}: required stop missing')
    low = high = Decimal(0)
    costs_complete = bool(plan['costs'])
    cost_ids = set()
    if not plan['costs']:
        warnings.append('no costs supplied')
    for cost in plan['costs']:
        if cost['currency'] != currency:
            raise ValueError('normalize costs to budget_currency before validation')
        if cost['id'] in cost_ids:
            errors.append(f"{cost['id']}: duplicate cost id")
        cost_ids.add(cost['id'])
        a, b = cost['low_amount'], cost['high_amount']
        if a is None and b is None:
            costs_complete = False
            warnings.append(f"{cost['id']}: unknown cost")
            continue
        a, b = money(a), money(b)
        if a > b:
            raise ValueError('cost lower bound exceeds upper bound')
        low += a
        high += b
    if budget is not None and high > budget:
        errors.append('estimated upper cost exceeds budget')
    if budget is None:
        warnings.append('budget unspecified')
    for issue in plan['unresolved']:
        if not isinstance(issue, str):
            raise ValueError('unresolved entries must be strings')
        warnings.append('unresolved: ' + issue)
    return dict(errors=errors, warnings=warnings,
                currency=currency,
                known_cost_subtotal=[json_amount(low), json_amount(high)],
                cost_range=[json_amount(low), json_amount(high)] if costs_complete else None,
                costs_complete=costs_complete)


if __name__ == '__main__':
    # Force UTF-8 output regardless of the console codepage (e.g. Windows cp949),
    # otherwise printing non-cp949 punctuation (em dash, curly quotes, ...) raises
    # a UnicodeEncodeError that the except clause below misreports as input_error.
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        with open(sys.argv[1], encoding='utf-8-sig') as stream:
            result = validate(json.load(stream, parse_float=Decimal))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1 if result['errors'] else 0)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(json.dumps({'input_error': str(exc)}, ensure_ascii=False))
        sys.exit(2)
