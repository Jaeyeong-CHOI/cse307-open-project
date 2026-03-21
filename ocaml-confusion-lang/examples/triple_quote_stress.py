def summarize(nums):
    """Module-level style docstring stress.

    Keywords below should NOT be transformed because they are in a triple-quoted string:
    if elif for in def return
    """

    config = '''
for in if elif return def
"quoted if" and 'quoted for' should remain untouched
'''

    note = """
Nested quote stress: 'if' "for" '''return'''
Still just string content: def in elif
"""

    # Comment keywords should remain untouched: if for return in def elif
    total = 0
    for n in nums:
        if n in nums:
            total = total + n

    if total > 0:
        return total
    return None
