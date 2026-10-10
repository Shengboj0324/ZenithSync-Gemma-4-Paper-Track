"""Experimental causal next-action supervision, separate from corpus admission."""

import hashlib

from .artifacts import canonical_json
from .conversation import normalize_history
from .training_masks import assistant_training_tokens


def action_prefix(messages, *, target_index, allowed_tools):
    """Select one action with its entire preceding history, never its outcome.

    The source must be a complete, valid history. A partial example is explicit:
    it ends with a pending tool call, not a fabricated completion or response.
    """
    normalized = normalize_history(messages, allowed_tools=allowed_tools)
    if (type(target_index) is not int or not 0 < target_index < len(normalized)):
        raise ValueError('Target must be a noninitial message index')
    target = normalized[target_index]
    calls = target.get('tool_calls', [])
    if target['role'] != 'assistant' or len(calls) != 1:
        raise ValueError('Exactly one assistant tool call must be selected')
    context = normalized[:target_index]
    normalize_history(context, allowed_tools=allowed_tools)
    return normalized[:target_index + 1]


def action_training_tokens(tokenizer, messages, *, target_index,
                           template_sha256, allowed_tools, tools):
    """Preserve native prefix tokens and mask every earlier assistant action.

    Refuse a tokenizer/template whose context tokenization changes when the
    action is appended. This explicit boundary check prevents labels from
    accidentally crossing into prior observations or prior assistant messages.
    """
    prefix = action_prefix(messages, target_index=target_index,
                           allowed_tools=allowed_tools)
    call = prefix[-1]['tool_calls'][0]
    encoded = assistant_training_tokens(
        tokenizer, prefix, template_sha256=template_sha256,
        allowed_tools=allowed_tools, tools=tools,
        terminal_call_tools={call['function']['name']})
    context_ids = tokenizer.apply_chat_template(
        prefix[:-1], tools=tools, tokenize=True, add_generation_prompt=False,
        return_dict=False)
    boundary = len(context_ids)
    if not boundary or encoded['input_ids'][:boundary] != context_ids:
        raise ValueError('Context tokenization is not an exact prefix')
    labels = [-100] * boundary + encoded['labels'][boundary:]
    targets = sum(label != -100 for label in labels[1:])
    if targets == 0:
        raise ValueError('Selected action has no supervised next-token targets')
    if any(label != -100 and label != token
           for label, token in zip(labels, encoded['input_ids'], strict=True)):
        raise ValueError('Labels must equal their original native token IDs')
    return {
        'input_ids': encoded['input_ids'], 'labels': labels,
        'context_tokens': boundary, 'supervised_tokens': targets,
        'target_index': target_index, 'target_call_id': call['id'],
        'prefix_sha256': hashlib.sha256(canonical_json(prefix)).hexdigest(),
        'target_sha256': hashlib.sha256(canonical_json(prefix[-1])).hexdigest(),
        'training_approved': False,
    }
