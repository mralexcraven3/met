def noop_decorator(name=None):
    def real_noop_decorator(function):
        return function
    return real_noop_decorator
