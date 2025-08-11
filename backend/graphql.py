import json

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from graphene_django.views import GraphQLView
from graphql import GraphQLError
from graphql.language.ast import (
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
)
from graphql.validation import ValidationRule


class MaxQueryComplexityRule(ValidationRule):
    """Validation rule that rejects overly complex GraphQL queries."""

    def __init__(self, context):
        super().__init__(context)
        self.max_complexity = getattr(settings, "GRAPHQL_MAX_COMPLEXITY", 100)

    def leave_operation_definition(self, node: OperationDefinitionNode, *_args):
        complexity = sum(
            self._calculate_complexity(selection)
            for selection in node.selection_set.selections
        )
        if complexity > self.max_complexity:
            self.context.report_error(
                GraphQLError(
                    f"Query is too complex: {complexity}. Max complexity: {self.max_complexity}"
                )
            )

    def _calculate_complexity(self, node) -> int:
        if not getattr(node, "selection_set", None):
            return 1
        total = 1
        for selection in node.selection_set.selections:
            if isinstance(selection, FieldNode):
                total += self._calculate_complexity(selection)
            elif isinstance(selection, FragmentSpreadNode):
                fragment = self.context.get_fragment(selection.name.value)
                total += self._calculate_complexity(fragment)
            elif isinstance(selection, InlineFragmentNode):
                total += self._calculate_complexity(selection)
        return total


class CachedGraphQLView(GraphQLView):
    """GraphQL view that caches introspection query responses and enforces complexity limits."""

    introspection_cache_timeout = 60 * 60  # one hour

    def __init__(self, *args, **kwargs):
        rules = kwargs.pop("validation_rules", []) or []
        rules.append(MaxQueryComplexityRule)
        super().__init__(*args, validation_rules=rules, **kwargs)

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
