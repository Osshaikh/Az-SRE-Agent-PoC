import os
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import AlwaysOnSampler
import logging

from app import app

# Application Insights connection string from env
APPINSIGHTS_CS = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

if APPINSIGHTS_CS:
    # Enable distributed tracing
    FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string=APPINSIGHTS_CS),
        sampler=AlwaysOnSampler()
    )

    # Enable log export to App Insights
    handler = AzureLogHandler(connection_string=APPINSIGHTS_CS)
    handler.setLevel(logging.WARNING)
    app.logger.addHandler(handler)

    # Also capture root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    app.logger.info("Application Insights telemetry enabled")
