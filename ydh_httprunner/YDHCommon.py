import redis, json
from config import Config

rdp = redis.ConnectionPool(host=Config.redis_host, port=Config.redis_port, db=Config.redis_db)


def check_case_result(case_name):
    rdc = redis.StrictRedis(connection_pool=rdp)
    if rdc.get(case_name) == b"fail":
        return True
    else:
        return False


def clean_redis():
    rdc = redis.StrictRedis(connection_pool=rdp)
    rdc.flushdb()


def set_case_result(case_name,result):
    rdc = redis.StrictRedis(connection_pool=rdp)
    if not rdc.get(case_name):
        result = result if result else "idempotency"
        rdc.set(case_name, json.dumps(result))


def get_case_result(case_name):
    rdc = redis.StrictRedis(connection_pool=rdp)
    last_result = rdc.get(case_name)
    if last_result == json.dumps("idempotency").encode("utf8"):
        return dict()
    elif last_result:
        return json.loads(last_result.decode("utf8"))
    else:
        return False
