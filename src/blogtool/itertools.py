def takeuntil(predicate, iterable, include_match=True):
    '''return items from an iterable until predicate is true'''
    for x in iterable:
        res = predicate(x)
        if res and not include_match:
            break

        yield x

        if res:
            break
