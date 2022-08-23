from django.db import connection, reset_queries
import time
import functools


def debug_query(func):
    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print('========================================')
        print('========================================')
        print(f"Class : {func.__qualname__}")
        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.2f}s")
        if end_queries - start_queries > 0:
            print('Queries:\n' + "\n".join([str(query) for query in connection.queries[-(end_queries - start_queries):]]))
        print('========================================')
        print('========================================')
        return result

    return inner_func