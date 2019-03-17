

async def check_list(checks=None, maxseed=1000):
    if checks is None:
        checks = maxseed
    assert checks <= maxseed
