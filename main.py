from sanic_jwt import Initialize
from aredis import StrictRedis
from jogging.Routes.auth import (
    authenticate,
)
from jogging.Routes.users import register
from jogging import config


def config_app():
    #
    # REDIS (refresh_token cache)
    #
    config.redis_client = StrictRedis(host="127.0.0.1", port=6379, db=0)

    #
    # sanic_jwt configuration & setup
    #
    Initialize(
        config.app,
        authenticate=authenticate,
        #       refresh_token_enabled=True,
        #       store_refresh_token=store_refresh_token,
        #       retrieve_refresh_token=retrieve_refresh_token,
        debug=True,
        claim_iat=True,
        #        scopes_enabled=True,
        expiration_delta=60 * 10,
    )

    #
    # user routes
    #
    config.app.add_route(register, "/users", methods=["POST"])
    # jogging routes
    #
    # register Idea routes
    #
    # config.app.add_route(update_idea, "/ideas/<id>", methods=["PUT"])
    # config.app.add_route(delete_idea, "/ideas/<id>", methods=["DELETE"])
    # config.app.add_route(create_idea, "/ideas", methods=["POST"])
    # config.app.add_route(get_ideas, "/ideas", methods=["GET"])
    # config.app.add_route(me_me_me, "/me", methods=["GET"])


if __name__ == "__main__":

    #
    # Get Ready!
    #
    config_app()

    #
    # Run Lola, Run!
    #
    config.app.run(host="0.0.0.0", port=8000)
