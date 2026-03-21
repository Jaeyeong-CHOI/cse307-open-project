def add(nums):
    total = 0
    for n in nums:
        if n > 0:
            total = total + n
        elif n == 0:
            return total
    return total
