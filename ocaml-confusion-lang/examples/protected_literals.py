def demo(items):
    text = "if return for in def elif should stay inside string"
    triple = '''
for if def return elif in
'''
    # if for return inside comment should stay
    for x in items:
        if x in items:
            return x
    return None
