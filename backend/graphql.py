import json
from django.core.cache import cache
from django.http import HttpResponse
from graphene_django.views import GraphQLView


class CachedGraphQLView(GraphQLView):
    """GraphQL view that caches introspection query responses."""

    introspection_cache_timeout = 60 * 60  # one hour

    def dispatch(self, request, *args, **kwargs):
        query = ""
        if request.method.lower() == "get":
            query = request.GET.get("query", "")
        else:
            try:
                body = json.loads(request.body.decode() or "{}")
            except Exception:
                body = {}
            query = body.get("query", "")

        is_introspection = self._is_introspection_query(query)
        cache_key = "graphql-introspection"
        if is_introspection:
            cached = cache.get(cache_key)
            if cached:
                return HttpResponse(cached, content_type="application/json")

        response = super().dispatch(request, *args, **kwargs)
        if is_introspection:
            cache.set(cache_key, response.content, self.introspection_cache_timeout)
        return response

    @staticmethod
    def _is_introspection_query(query: str) -> bool:
        return "__schema" in query or "IntrospectionQuery" in query
