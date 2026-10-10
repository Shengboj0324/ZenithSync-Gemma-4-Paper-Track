"""Deterministic whole-example updates with exact supervised-token accounting.

Hash ordering is a reproducible shuffle rule, not a claim of statistical
independence. Repeated epochs are repeated exposures, not new training data.
"""
import hashlib
from .artifacts import canonical_json
from .contracts import digest


def _positive(value):
    if type(value) is not int or value <= 0:
        raise ValueError('Positive integer required')
    return value


def _hash(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def make_schedule(examples, *, corpus_content_sha256, seed, target_supervised_tokens,
                  max_epochs, max_update_supervised_tokens):
    digest(corpus_content_sha256)
    if type(seed) is not int or seed < 0:
        raise ValueError('Nonnegative integer seed required')
    for value in (target_supervised_tokens, max_epochs, max_update_supervised_tokens):
        _positive(value)
    if not isinstance(examples,list) or not examples:
        raise ValueError('Nonempty example metadata required')
    copied=[];seen=set()
    for row in examples:
        if not isinstance(row,dict) or set(row)!={'example_id','input_tokens','supervised_tokens'}:
            raise ValueError('Exact example metadata fields required')
        name=row['example_id']
        if not isinstance(name,str) or not name or name in seen:
            raise ValueError('Unique nonempty example identity required')
        seen.add(name)
        count=_positive(row['supervised_tokens']);length=_positive(row['input_tokens'])
        if count>=length or count>max_update_supervised_tokens:
            raise ValueError('Example cannot fit the update budget without truncation')
        copied.append(dict(row))
    if sum(r['supervised_tokens'] for r in copied)*max_epochs<target_supervised_tokens:
        raise ValueError('Token target exceeds explicit epoch allowance')
    body={'schema_version':1,'corpus_content_sha256':corpus_content_sha256,'seed':seed,
          'target_supervised_tokens':target_supervised_tokens,'max_epochs':max_epochs,
          'max_update_supervised_tokens':max_update_supervised_tokens,
          'examples':sorted(copied,key=lambda r:r['example_id'])}
    return {**body,'schedule_sha256':_hash(body)}


def initial_cursor(schedule):
    return {'schedule_sha256':schedule['schedule_sha256'],'completed_updates':0,
            'consumed_input_tokens':0,'consumed_supervised_tokens':0,
            'prefix_sha256':_hash(['training-schedule-prefix-v1',schedule['schedule_sha256']])}


def iter_updates(schedule, *, resume=None):
    """Resume only at an exactly reproduced completed-update boundary."""
    keys={'schema_version','corpus_content_sha256','seed','target_supervised_tokens',
          'max_epochs','max_update_supervised_tokens','examples','schedule_sha256'}
    if not isinstance(schedule,dict) or set(schedule)!=keys or type(schedule['schema_version']) is not int or schedule['schema_version']!=1:
        raise ValueError('Invalid schedule schema')
    rebuilt=make_schedule(schedule['examples'],**{k:schedule[k] for k in
        ['corpus_content_sha256','seed','target_supervised_tokens','max_epochs','max_update_supervised_tokens']})
    if rebuilt!=schedule:raise ValueError('Schedule identity changed')
    cursor=initial_cursor(schedule)
    if resume is None:resume=dict(cursor)
    if not isinstance(resume,dict) or set(resume)!=set(cursor):raise ValueError('Invalid resume cursor')
    for key in ('completed_updates','consumed_input_tokens','consumed_supervised_tokens'):
        if type(resume[key]) is not int or resume[key]<0:raise ValueError('Invalid resume counter')
    digest(resume['prefix_sha256'])
    if resume['schedule_sha256']!=schedule['schedule_sha256']:raise ValueError('Resume schedule mismatch')
    matched=resume==cursor
    if resume['completed_updates']==0 and not matched:raise ValueError('Initial resume cursor mismatch')
    done=False
    for epoch in range(schedule['max_epochs']):
        ordered=sorted(schedule['examples'],key=lambda r:(_hash(
            ['training-order-v1',schedule['seed'],epoch,r['example_id']]),r['example_id']))
        index=0
        while index<len(ordered):
            rows=[];targets=inputs=0
            while index<len(ordered):
                row=ordered[index]
                if rows and targets+row['supervised_tokens']>schedule['max_update_supervised_tokens']:break
                rows.append(dict(row));targets+=row['supervised_tokens'];inputs+=row['input_tokens'];index+=1
                if cursor['consumed_supervised_tokens']+targets>=schedule['target_supervised_tokens']:
                    done=True;break
            update={'step':cursor['completed_updates']+1,'epoch':epoch,'examples':rows,
                    'input_tokens':inputs,'supervised_tokens':targets}
            cursor={'schedule_sha256':schedule['schedule_sha256'],'completed_updates':update['step'],
                    'consumed_input_tokens':cursor['consumed_input_tokens']+inputs,
                    'consumed_supervised_tokens':cursor['consumed_supervised_tokens']+targets,
                    'prefix_sha256':_hash([cursor['prefix_sha256'],update])}
            if update['step']<=resume['completed_updates']:
                if update['step']==resume['completed_updates']:
                    if cursor!=resume:raise ValueError('Resume prefix or counters mismatch')
                    matched=True
            else:
                if not matched:raise ValueError('Resume boundary not reached')
                yield {**update,'next_cursor':dict(cursor)}
            if done:break
        if done:break
    if not matched:raise ValueError('Resume cursor is beyond terminal schedule')
