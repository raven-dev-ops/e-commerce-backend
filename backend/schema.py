import graphene


class Query(graphene.ObjectType):
    """GraphQL API is disabled for product data now that the
    catalog is managed on the frontend. This placeholder schema
    remains so the /graphql/ endpoint stays valid but empty.
    """

    ping = graphene.String(description="Simple liveness field")

    def resolve_ping(root, info):
        return "ok"


schema = graphene.Schema(query=Query)
