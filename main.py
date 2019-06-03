from sanic_jwt import Initialize
from aredis import StrictRedis
from jogging.Routes.auth import (
    authenticate,
    store_refresh_token,
    retrieve_refresh_token,
    retrieve_user,
    EmailClaim,
    NameClaim,
    scope_extender,
)
from jogging.Routes.users import (
    register,
    get_users,
    update_user,
    update_user_scope,
    delete_user
)
from jogging.Routes.jogging_results import (
    add_jogging_result,
    update_jogging_result,
    get_jogging_results,
    get_jogging_result,
    delete_jogging_result,
    get_jogging_weekly_report,
)
from jogging import config


def config_app():
    #
    # REDIS (refresh_token cache)
    #
    config.redis_client = StrictRedis(host="127.0.0.1", port=6379, db=0)

    #
    # sanic_jwt configuration & setup
    #
    custom_claims = [NameClaim, EmailClaim]
    Initialize(
        config.app,
        authenticate=authenticate,
        custom_claims=custom_claims,
        store_refresh_token=store_refresh_token,
        retrieve_refresh_token=retrieve_refresh_token,
        retrieve_user=retrieve_user,
        add_scopes_to_payload=scope_extender,
        debug=True,
        claim_iat=True,
        refresh_token_enabled=True,
    )

    #
    # user routes
    #
    config.app.add_route(register, "/users", methods=["POST"])
    config.app.add_route(get_users, "/users", methods=["GET"])
    config.app.add_route(
        update_user_scope, "/users/<userId>/scopes", methods=["PATCH"]
    )
    config.app.add_route(update_user, "/users/<userId>", methods=["PATCH"])
    config.app.add_route(delete_user, "/users/<userId>", methods=["DELETE"])
    #
    # jogging routes
    #
    config.app.add_route(add_jogging_result, "/results", methods=["POST"])
    config.app.add_route(
        update_jogging_result, "/results/<resultId>", methods=["PATCH"]
    )
    config.app.add_route(
        get_jogging_result, "/results/<resultId>", methods=["GET"]
    )
    config.app.add_route(
        delete_jogging_result, "/results/<resultId>", methods=["DELETE"]
    )
    config.app.add_route(get_jogging_results, "/results", methods=["GET"])
    config.app.add_route(
        get_jogging_weekly_report, "/results/reports/weekly", methods=["GET"]
    )


if __name__ == "__main__":

    #
    # Get Ready!
    #
    config_app()

    #
    # Run Lola, Run!
    #
    config.app.run(host="0.0.0.0", port=8000)
