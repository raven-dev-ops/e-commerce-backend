import os

"""Optional OpenTelemetry tracing integration."""

if os.getenv("OTEL_TRACE_ENABLED", "true").lower() in {"true", "1"}:
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )  # type: ignore
        from opentelemetry.instrumentation.django import (  # type: ignore
            DjangoInstrumentor,
        )
        from opentelemetry.instrumentation.requests import (  # type: ignore
            RequestsInstrumentor,
        )
        from opentelemetry.sdk.resources import (  # type: ignore
            SERVICE_NAME,
            Resource,
        )
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import (  # type: ignore
            BatchSpanProcessor,
        )
    except ModuleNotFoundError:
        pass
    else:
        resource = Resource.create(
            {SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "ecommerce-backend")}
        )
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=os.getenv(
                    "OTEL_EXPORTER_OTLP_ENDPOINT",
                    "http://localhost:4318/v1/traces",
                )
            )
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        DjangoInstrumentor().instrument()
        RequestsInstrumentor().instrument()
