def get_uniques(l: list):
    return list(set(l) - set([""]))


def uniq_preserve_order(l: list):
    return sorted(set(l), key=lambda x: l.index(x))

def truncate_middle(s, n):
    if len(s) <= n:
        return s
    n_2 = int(n / 2 - 3)
    n_1 = int(n - n_2 - 3)
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])
