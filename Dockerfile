FROM langchain/langgraph-api:3.13



# -- Adding local package . --
ADD . /deps/agents
# -- End of local package . --

# -- Installing all local dependencies --
RUN for dep in /deps/*; do             echo "Installing $dep";             if [ -d "$dep" ]; then                 echo "Installing $dep";                 (cd "$dep" && PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e .);             fi;         done
# -- End of local dependencies install --
ENV LANGGRAPH_HTTP='{"app": "/deps/agents/src/api/main.py:app"}'
ENV LANGSERVE_GRAPHS='{"orchestrator_agent": "/deps/agents/src/agents/orchestrator_agent/agent.py:agent", "geospatial_intelligence_agent": "/deps/agents/src/agents/geospatial_intelligence_agent/agent.py:agent", "opportunity_identification_agent": "/deps/agents/src/agents/opportunity_identification_agent/agent.py:agent", "infrastructure_optimization_agent": "/deps/agents/src/agents/infrastructure_optimization_agent/agent.py:agent", "economic_impact_modeling_agent": "/deps/agents/src/agents/economic_impact_modeling_agent/agent.py:agent", "financing_optimization_agent": "/deps/agents/src/agents/financing_optimization_agent/agent.py:agent", "stakeholder_intelligence_agent": "/deps/agents/src/agents/stakeholder_intelligence_agent/agent.py:agent"}'



# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license && touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing build deps from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel
RUN rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* && find /usr/local/bin -name "pip*" -delete || true
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* && find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx

WORKDIR /deps/agents