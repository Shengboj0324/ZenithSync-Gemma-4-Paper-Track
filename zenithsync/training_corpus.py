"""Hash-bound corpus loading; integrity checks are separate from training admission.

Receipts are local reviewed evidence, not cryptographic proof of their truth.
Operate on a quiescent, owned directory, not an adversarial concurrent filesystem.
"""
import hashlib
from copy import deepcopy
from pathlib import Path

from .artifacts import canonical_json, file_record, load_json, relative_path
from .contracts import digest
from .splits import validate_splits
from .training_batch import collate_training_examples

SCHEMA_VERSION = 2
LEGACY_GATES = ('rights_and_attribution', 'split_isolation', 'runtime_qualification')
GATES = (*LEGACY_GATES, 'task_alignment')


def _positive(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(name + ' must be a positive integer')
    return value


def _identity(value):
    if not isinstance(value, dict) or set(value) != {'sha256', 'size_bytes'}:
        raise ValueError('Exact file identity required')
    digest(value['sha256'])
    if type(value['size_bytes']) is not int or value['size_bytes'] < 0:
        raise ValueError('Invalid file size')
    return value


def _bound_file(root, reference, max_bytes):
    if not isinstance(reference, dict) or set(reference) != {'path', 'identity'}:
        raise ValueError('Exact relative file reference required')
    name = relative_path(reference['path'])
    expected = _identity(reference['identity'])
    if expected['size_bytes'] > max_bytes:
        raise ValueError('Referenced file exceeds byte ceiling')
    path = root / name
    if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
        raise ValueError('Symlinked corpus paths rejected')
    if not path.resolve(strict=True).is_relative_to(root):
        raise ValueError('Corpus path escapes root')
    if file_record(path) != expected:
        raise ValueError('Corpus file hash mismatch')
    value = load_json(path)
    if file_record(path) != expected:
        raise ValueError('Corpus file changed during loading')
    return value


def corpus_content_identity(manifest):
    """Admission is bound to content; adding receipts cannot change this identity."""
    content = {key: manifest[key] for key in ('schema_version', 'tokenizer_assets', 'max_length', 'examples')}
    return hashlib.sha256(canonical_json(content)).hexdigest()


def validate_task_alignment(evidence_documents, records):
    """Require exact task/repository coverage; this does not prove review truth.

    Multiple traces of one task share its issue-level review. Identity spelling
    must match the manifest exactly; reviewers must resolve aliases upstream.
    """
    expected = {(r['task_id'], r['repository_group']) for r in records}
    seen = set()
    for document in evidence_documents:
        if (not isinstance(document, dict)
                or type(document.get('schema_version')) is not int
                or document['schema_version'] != 1
                or not isinstance(document.get('task_reviews'), list)
                or not document['task_reviews']):
            raise ValueError('Task alignment evidence requires versioned task reviews')
        for review in document['task_reviews']:
            if (not isinstance(review, dict) or set(review) != {
                    'task_id', 'repository_group', 'decision', 'rationale'}
                    or any(not isinstance(review[key], str) or not review[key].strip()
                           for key in review)):
                raise ValueError('Invalid task alignment review fields')
            key = (review['task_id'], review['repository_group'])
            if key not in expected:
                raise ValueError('Task alignment review names a foreign task or repository')
            if key in seen:
                raise ValueError('Duplicate task alignment review')
            if review['decision'] != 'accepted':
                raise ValueError('Task alignment review is not accepted')
            seen.add(key)
    if seen != expected:
        raise ValueError('Task alignment review coverage is incomplete')


def load_corpus(root: Path, manifest_path: Path, *, expected_manifest_sha256: str,
                purpose='inspection', max_examples=100000, max_total_bytes=1024**3):
    """Validate every example before returning any, with no truncation or packing."""
    return _load_corpus(root, manifest_path, expected_manifest_sha256=expected_manifest_sha256,
                        purpose=purpose, max_examples=max_examples,
                        max_total_bytes=max_total_bytes, materialize=True,
                        max_example_bytes=max_total_bytes)


def _load_corpus(root, manifest_path, *, expected_manifest_sha256, purpose,
                 max_examples, max_total_bytes, materialize, max_example_bytes):
    digest(expected_manifest_sha256)
    _positive(max_examples, 'max_examples')
    _positive(max_total_bytes, 'max_total_bytes')
    _positive(max_example_bytes, 'max_example_bytes')
    if purpose not in ('inspection', 'training'):
        raise ValueError('Unknown corpus purpose')
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Corpus root must be an ordinary directory')
    root = root.resolve(strict=True)
    manifest_identity = file_record(manifest_path)
    if manifest_identity['sha256'] != expected_manifest_sha256 or manifest_identity['size_bytes'] > 16*1024**2:
        raise ValueError('Untrusted or oversized corpus manifest')
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or set(manifest) != {
            'schema_version', 'status', 'tokenizer_assets', 'max_length', 'examples', 'admission'}:
        raise ValueError('Invalid corpus manifest fields')
    if type(manifest['schema_version']) is not int or manifest['schema_version'] not in (1, SCHEMA_VERSION):
        raise ValueError('Unsupported corpus schema')
    legacy = manifest['schema_version'] == 1
    if legacy and purpose == 'training':
        raise ValueError('Legacy corpus lacks explicit task alignment; rebuild and review before training')
    if manifest['status'] not in ('quarantine', 'admitted'):
        raise ValueError('Invalid corpus status')
    max_length = _positive(manifest['max_length'], 'max_length')
    assets = manifest['tokenizer_assets']
    if not isinstance(assets, dict) or set(assets) != {'chat_template.jinja','tokenizer.json','tokenizer_config.json'}:
        raise ValueError('Exact tokenizer asset identities required')
    for value in assets.values():
        _identity(value)
    records = manifest['examples']
    if not isinstance(records, list) or not 0 < len(records) <= max_examples:
        raise ValueError('Corpus example count out of bounds')
    required = {'example_id','task_id','repository_group','leakage_group','split','tokens','audit'}
    total = 0
    seen_files, seen_ids = set(), set()
    for record in records:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError('Invalid corpus example fields')
        for key in ('example_id','task_id','repository_group','leakage_group'):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError('Missing example grouping identity')
        if record['example_id'] in seen_ids:
            raise ValueError('Duplicate example identity')
        seen_ids.add(record['example_id'])
        for key in ('tokens','audit'):
            ref = record[key]
            if not isinstance(ref, dict) or set(ref) != {'path','identity'}:
                raise ValueError('Invalid example file reference')
            name = relative_path(ref['path'])
            if name in seen_files:
                raise ValueError('Example files must not alias')
            seen_files.add(name)
            total += _identity(ref['identity'])['size_bytes']
    if total > max_total_bytes:
        raise ValueError('Corpus exceeds explicit aggregate byte ceiling')
    content_identity = corpus_content_identity(manifest)
    admission = manifest['admission']
    if not isinstance(admission, dict) or set(admission) != set(LEGACY_GATES if legacy else GATES):
        raise ValueError('Explicit admission gate map required')
    if purpose == 'training' and manifest['status'] != 'admitted':
        raise ValueError('Quarantine corpus cannot train')
    for gate, reference in admission.items():
        if reference is None:
            if manifest['status'] == 'admitted':
                raise ValueError('Admitted corpus has an unresolved gate')
            continue
        total += _identity(reference['identity'])['size_bytes']
        if total > max_total_bytes:
            raise ValueError('Admission files exceed aggregate byte ceiling')
        receipt = _bound_file(root, reference, 1024**2)
        if (not isinstance(receipt, dict) or receipt.get('gate') != gate
                or receipt.get('status') != 'passed'
                or receipt.get('corpus_content_sha256') != content_identity
                or not isinstance(receipt.get('evidence'), list) or not receipt['evidence']):
            raise ValueError('Admission receipt does not bind this corpus')
        alignment_documents = []
        for evidence in receipt['evidence']:
            total += _identity(evidence['identity'])['size_bytes']
            if total > max_total_bytes:
                raise ValueError('Admission evidence exceeds aggregate byte ceiling')
            document = _bound_file(root, evidence, 16*1024**2)
            if gate == 'task_alignment':
                alignment_documents.append(document)
        if gate == 'task_alignment':
            validate_task_alignment(alignment_documents, records)
    examples, tasks, input_hashes = [], [], set()
    vocab, pad = None, None
    input_total = supervised_total = 0
    for record in records:
        candidate = _bound_file(root, record['tokens'], min(max_total_bytes, max_example_bytes))
        audit = _bound_file(root, record['audit'], min(max_total_bytes, max_example_bytes))
        if (not isinstance(candidate, dict) or type(candidate.get('schema_version')) is not int
                or candidate['schema_version'] != 1 or candidate.get('training_approved') is not False):
            raise ValueError('Expected immutable unapproved token candidate')
        if (audit.get('token_candidate') != record['tokens']['identity']
                or audit.get('assets') != assets or audit.get('truncated') is not False
                or candidate.get('history') != audit.get('history')
                or candidate.get('tools') != audit.get('tools')):
            raise ValueError('Token, audit or tokenizer lineage mismatch')
        _identity(candidate['history']); _identity(candidate['tools'])
        current_vocab, current_pad = candidate.get('vocab_size'), candidate.get('pad_token_id')
        if vocab is not None and (current_vocab != vocab or current_pad != pad):
            raise ValueError('Mixed token vocabularies or padding IDs')
        batch = collate_training_examples([candidate], pad_token_id=current_pad,
            vocab_size=current_vocab, max_length=max_length)
        vocab, pad = current_vocab, current_pad
        ids, labels = candidate['input_ids'], candidate['labels']
        hashes = {name:hashlib.sha256(canonical_json(values)).hexdigest()
                  for name,values in [('input_sha256',ids),('labels_sha256',labels)]}
        if any(audit.get(name) != value for name,value in hashes.items()):
            raise ValueError('Token arrays differ from tokenizer audit')
        if (type(audit.get('input_tokens')) is not int or audit['input_tokens'] != len(ids)
                or type(audit.get('supervised_tokens')) is not int
                or audit['supervised_tokens'] != batch['supervised_tokens']):
            raise ValueError('Token accounting differs from audit')
        if hashes['input_sha256'] in input_hashes:
            raise ValueError('Duplicate token sequence')
        input_hashes.add(hashes['input_sha256'])
        tasks.append({'task_id':record['example_id'],'repository_group':record['repository_group'].casefold(),
                      'leakage_group':record['leakage_group'],'split':record['split'],
                      'input_sha256':hashes['input_sha256']})
        example = {'example_id':record['example_id'],'task_id':record['task_id'],
                   'split':record['split']}
        if materialize:
            example.update(input_ids=ids, labels=labels)
        else:
            example.update(input_tokens=len(ids), supervised_tokens=batch['supervised_tokens'],
                           tokens=deepcopy(record['tokens']))
        examples.append(example)
        input_total += len(ids); supervised_total += batch['supervised_tokens']
    validate_splits({'schema_version':1,'status':'frozen' if manifest['status']=='admitted' else 'draft','tasks':tasks})
    # A repeated issue cannot cross splits even if a caller supplies distinct family labels.
    issue_splits = {}
    for record in records:
        key = record['task_id'].casefold()
        if key in issue_splits and issue_splits[key] != record['split']:
            raise ValueError('Task crosses corpus splits')
        issue_splits[key] = record['split']
    if file_record(manifest_path) != manifest_identity:
        raise ValueError('Manifest changed during corpus load')
    if purpose == 'training':
        examples = [example for example in examples if example['split'] == 'train']
        if not examples:
            raise ValueError('No training examples in admitted corpus')
    return {'examples':examples,'vocab_size':vocab,'pad_token_id':pad,
            'summary':{'examples':len(records),'returned_examples':len(examples),'unique_tasks':len(issue_splits),
                       'input_tokens':input_total,'supervised_tokens':supervised_total,
                       'content_sha256':content_identity,'manifest':manifest_identity,
                       'status':manifest['status'],'purpose':purpose,
                       'training_admitted':manifest['status']=='admitted' and not legacy}}


class IndexedCorpus:
    """Validate all splits once; rehash individual examples on demand.

    Host storage scales with manifest metadata plus the largest example, rather
    than all token arrays. Callers must also bound their own fetched batches.
    This is a snapshot over a quiescent owned directory, not a live filesystem
    authorization service. Receipt validity is established at construction.
    """

    def __init__(self, root: Path, manifest_path: Path, *, expected_manifest_sha256,
                 purpose='training', max_examples=100000, max_total_bytes=1024**3,
                 max_example_bytes=16*1024**2):
        result = _load_corpus(
            root, manifest_path, expected_manifest_sha256=expected_manifest_sha256,
            purpose=purpose, max_examples=max_examples, max_total_bytes=max_total_bytes,
            materialize=False, max_example_bytes=max_example_bytes)
        self._root = root.resolve(strict=True)
        self._manifest_path = manifest_path.resolve(strict=True)
        self._summary = result['summary']
        self._records = {row['example_id']: row for row in result['examples']}
        self._max_example_bytes = min(max_total_bytes, max_example_bytes)
        self.vocab_size = result['vocab_size']
        self.pad_token_id = result['pad_token_id']

    @property
    def summary(self):
        return deepcopy(self._summary)

    def metadata(self):
        return [{key: value for key, value in row.items() if key != 'tokens'}
                for row in self._records.values()]

    def example_metadata(self, example_id):
        return {key: value for key, value in self._records[example_id].items()
                if key != 'tokens'}

    def fetch(self, example_id):
        if file_record(self._manifest_path) != self._summary['manifest']:
            raise ValueError('Manifest changed after corpus indexing')
        row = self._records[example_id]
        candidate = _bound_file(self._root, row['tokens'], self._max_example_bytes)
        # Exact bytes were already validated against the tokenizer audit and all
        # corpus-wide invariants during construction. Rehashing prevents stale
        # validation from admitting subsequently replaced token arrays.
        return {'example_id': row['example_id'], 'task_id': row['task_id'],
                'split': row['split'], 'input_ids': candidate['input_ids'],
                'labels': candidate['labels']}
