"""Conservative review hints for Python test snippets, never admission decisions.

Only supplied Python text is parsed. No code executes and no correctness claim
is inferred from missing findings. Locations refer to the original snippet.
"""
import ast


def review_python_test_source(source: str) -> dict:
    """Locate unconditional module-level success claims and broad handlers."""
    if not isinstance(source, str):
        raise ValueError('Python source must be text')
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return {'parsed': False, 'findings': [{
            'kind': 'syntax_error', 'line': error.lineno,
            'detail': error.msg}], 'admission_decision': None}
    findings = []
    success_words = ('passed', 'success', 'verified')
    for statement in tree.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Name) or call.func.id != 'print':
            continue
        literals = [arg.value for arg in call.args
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
        if any(word in text.casefold() for text in literals for word in success_words):
            findings.append({'kind': 'unconditional_module_success_message',
                             'line': statement.lineno,
                             'detail': 'Earlier checks may justify this message; review required.'})
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        types = node.type.elts if isinstance(node.type, ast.Tuple) else [node.type]
        broad = any(value is None or isinstance(value, ast.Name)
                    and value.id in ('Exception', 'BaseException') for value in types)
        if broad:
            findings.append({'kind': 'broad_exception_handler', 'line': node.lineno,
                             'detail': 'May be legitimate error handling; inspect the acceptance path.'})
    return {'parsed': True, 'findings': sorted(findings, key=lambda row: (row['line'], row['kind'])),
            'admission_decision': None}
