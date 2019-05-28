from sanic import Sanic

darksky_api_key = "4c51520b70b5ad96135ef89d52d829fb"

app = Sanic()
redis_client = None
