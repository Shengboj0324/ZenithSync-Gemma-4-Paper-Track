"""Inventory replay observations without converting tool success into correctness."""
from collections import Counter
import hashlib

from .artifacts import canonical_json


def audit_observations(events):
    if not isinstance(events, list) or not events:
        raise ValueError('Nonempty replay events required')
    records = []
    previous = -1
    tools = Counter()
    statuses = Counter()
    for event in events:
        index = event['source_index']
        if type(index) is not int or index <= previous:
            raise ValueError('Unique increasing source indices required')
        previous = index
        calls = event['native_calls']
        if not isinstance(calls, list):
            raise ValueError('Native calls must be a list')
        for position, call in enumerate(calls):
            if not isinstance(call, dict) or set(call) != {'name','arguments','result'}:
                raise ValueError('Exact recorded native call required')
            name, arguments, result = call['name'], call['arguments'], call['result']
            if (not isinstance(name, str) or not name or not isinstance(arguments, dict)
                    or not isinstance(result, dict) or result.get('status') not in ('ok','error')):
                raise ValueError('Invalid native observation')
            details = result.get('details', {})
            if not isinstance(details, dict):
                raise ValueError('Observation details must be an object')
            codes = [obj['exit_code'] for obj in (result, details) if 'exit_code' in obj]
            if any(type(code) is not int for code in codes) or len(set(codes)) > 1:
                raise ValueError('Ambiguous or invalid command exit code')
            flags = [obj[key] for obj in (result, details)
                     for key in ('is_truncated','truncated') if key in obj]
            if any(type(flag) is not bool for flag in flags):
                raise ValueError('Invalid truncation flag')
            # A missing flag is unknown, never a claim that output was complete.
            truncation = any(flags) if flags else None
            code = codes[0] if codes else None
            texts = {}
            for owner, obj in (('result',result), ('details',details)):
                for key in ('stdout','stderr','content','diff','error_message'):
                    if key in obj:
                        if not isinstance(obj[key], str):
                            raise ValueError('Expected textual observation field')
                        raw = obj[key].encode('utf-8')
                        texts[owner+'.'+key] = {'utf8_bytes':len(raw),
                            'sha256':hashlib.sha256(raw).hexdigest()}
            tools[name] += 1
            statuses[result['status']] += 1
            records.append({'source_index':index,'call_position':position,'tool':name,
                'status':result['status'],'exit_code':code,'reported_truncation':truncation,
                'arguments_sha256':hashlib.sha256(canonical_json(arguments)).hexdigest(),
                'result_sha256':hashlib.sha256(canonical_json(result)).hexdigest(),
                'text_fields':texts})
    if not records:
        raise ValueError('No native observations')
    return {'calls':records,'tool_counts':dict(sorted(tools.items())),
            'status_counts':dict(sorted(statuses.items())),
            'explicitly_truncated_calls':sum(r['reported_truncation'] is True for r in records),
            'truncation_unspecified_calls':sum(r['reported_truncation'] is None for r in records),
            'nonzero_exit_calls':sum(r['exit_code'] is not None and r['exit_code'] != 0 for r in records),
            'training_approved':False,
            'scope':'Recorded root/details flags and text identities only; no inference of semantic success, completeness of unflagged output, or teacher conditioning fidelity.'}
