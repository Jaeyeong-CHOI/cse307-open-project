# L2 Language Specification: Syntax Inversion

**Design goal:** Invert Python structural patterns so NTP-predicted continuations are consistently wrong.
**Underlying principle:** LLMs predict P(next_token | prefix). If we design syntax so that Python-likely tokens are grammatically *invalid*, model fails structurally.

## L2 Grammar Inverisons

### 1. Function definition (reversed argument syntax)
```
# Python
def fib(n):

# L2
:define fib [n] ->
```

### 2. Return statement (value-first)
```
# Python
return n

# L2
<= n
```

### 3. If condition (postfix condition)
```
# Python
if n <= 1:

# L2
n <= 1 ?cond:
```

### 4. For loop (range last)
```
# Python
for i in range(7):

# L2
loop i over range(7) {
```

### 5. Block delimiters (explicit, not indent)
```
# Python (indent-based)
def fib(n):
    if n <= 1:
        return n

# L2 (explicit delimiters)
:define fib [n] ->
  n <= 1 ?cond: <= n ;else: <= fib[n-1] + fib[n-2] ;end
```

## Expected LLM failure mode
- NTP will predict `def`, `return`, `if`, `for` at natural positions
- L2 syntax places tokens in positions where Python priors are maximally wrong
- Confusion: Python prior fires → wrong token → AST-level failure

## Measurement additions (beyond L1)
- **SIR** (Structural Inversion Rate): fraction of structural positions where model uses Python syntax instead of L2
- **TRP** (Token Position Reversal Performance): accuracy at inverted-position token slots specifically
