FROM langchain/langgraph-api:3.13

# System dependencies for geospatial stack + rclone for R2 data sync
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    rclone \
    && rm -rf /var/lib/apt/lists/*

# -- Adding local package . --
ADD . /deps/agents

# -- Installing all local dependencies --
RUN for dep in /deps/*; do \
        echo "Installing $dep"; \
        if [ -d "$dep" ]; then \
            (cd "$dep" && PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e .); \
        fi; \
    done

ENV LANGGRAPH_HTTP='{"app": "/deps/agents/src/api/main.py:app"}'
ENV LANGSERVE_GRAPHS='{"orchestrator_agent": "/deps/agents/src/agents/orchestrator_agent/agent.py:agent", "geospatial_intelligence_agent": "/deps/agents/src/agents/geospatial_intelligence_agent/agent.py:agent", "opportunity_identification_agent": "/deps/agents/src/agents/opportunity_identification_agent/agent.py:agent", "infrastructure_optimization_agent": "/deps/agents/src/agents/infrastructure_optimization_agent/agent.py:agent", "economic_impact_modeling_agent": "/deps/agents/src/agents/economic_impact_modeling_agent/agent.py:agent", "financing_optimization_agent": "/deps/agents/src/agents/financing_optimization_agent/agent.py:agent", "stakeholder_intelligence_agent": "/deps/agents/src/agents/stakeholder_intelligence_agent/agent.py:agent"}'

# Ensure user deps didn't overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && \
    touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api

# Remove build deps from final image
RUN pip uninstall -y pip setuptools wheel || true
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && find /usr/local/bin -name "pip*" -delete || true
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm -f /usr/bin/uv /usr/bin/uvx || true

# Bake data from R2 into the image at BUILD time — no runtime download needed.
# Railway passes build args from env vars automatically.
ARG R2_ACCESS_KEY
ARG R2_SECRET_KEY
ARG R2_ENDPOINT
RUN mkdir -p /data && \
    if [ -n "$R2_ACCESS_KEY" ] && [ -n "$R2_SECRET_KEY" ] && [ -n "$R2_ENDPOINT" ]; then \
        echo "Syncing data from R2 into image..." && \
        rclone sync \
            ":s3,provider=Cloudflare,access_key_id=$R2_ACCESS_KEY,secret_access_key=$R2_SECRET_KEY,endpoint=$R2_ENDPOINT:corridor-data/v1/data" \
            /data \
            --transfers=8 --fast-list && \
        echo "Data baked: $(du -sh /data | cut -f1)" ; \
    else \
        echo "WARNING: R2 credentials not provided as build args — /data will be empty." ; \
    fi

ENV CORRIDOR_DATA_ROOT=/data

WORKDIR /deps/agents

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/healthz/live')" || exit 1
