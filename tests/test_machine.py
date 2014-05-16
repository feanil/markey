from markey.rules import ruleset, include, rule, bygroups
from markey.machine import iter_rules, tokenize, parse_arguments
from markey.tools import Token, TokenStream


# Full functioning handlebars parser for testing.
keywords = frozenset((
    'pluralidx', 'gettext', 'ngettext', 'gettext_noop', 'pgettext',
    'npgettext', 'interpolate', '_'
))


rules = {
    'everything': ruleset(
        include('inline'),
        include('function'),
    ),
    'inline': ruleset(
        rule(r'<%=', enter='interpolate'),
        rule(r'<%-', enter='escape'),
        rule(r'<%', enter='evaluate'),
    ),
    'inline_with_func': ruleset(
        include('inline'),
        include('function')
    ),
    'function': ruleset(
        rule(r'({keywords})\('.format(keywords='|'.join(keywords)),
             bygroups('func_name'), enter='gettext')
    ),
    'gettext': ruleset(
        rule(r'([\"\'])?\)', leave=1),
        include('function_call')
    ),
    'evaluate': ruleset(
        rule(r'%>', leave=1),
        include('inline_with_func'),
    ),
    'interpolate': ruleset(
        rule(r'%>', leave=1),
        include('inline_with_func'),
    ),
    'escape': ruleset(
        rule(r'%>', leave=1),
        include('inline_with_func'),
    ),
    # function calls (parse string arguments and implicit strings)
    'function_call': ruleset(
        rule(',', 'func_argument_delimiter'),
        rule('\s+', None),
        rule(r"('([^'\\]*(?:\\.[^'\\]*)*)'|"
             r'"([^"\\]*(?:\\.[^"\\]*)*)")(?s)', 'func_string_arg'),
        rule(r'([\w_]+)\s*=', bygroups('func_kwarg'))
    )
}


def test_parse_arguments():
    line = '<% gettext("some string", str="foo")'
    stream = TokenStream.from_tuple_iter(tokenize(line, rules))
    stream.next()
    stream.next()
    stream.expect('gettext_begin')
    funcname = stream.expect('func_name').value
    args, kwargs = parse_arguments(stream, 'gettext_end')
    assert args == ('some string',)
    assert kwargs == {'str': 'foo'}
