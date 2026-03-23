# Unified simulation-agent image: orchestration, ressim, and workflow agents.
# Build from repo root: docker build -f Dockerfile -t simulation-agent:latest .
#
# Reuses the same base and patterns as sim_agent/Dockerfile and workflow_agent/Dockerfile.

FROM ubuntu:24.04

# License notes:
#   Application code: Apache-2.0
#   OPM Flow binaries (libopm-simulators*): GPL-3.0-or-later — bundled as a
#   standalone external executable invoked via subprocess; not linked into the
#   application. GPL does not propagate across the process boundary.
#   See /usr/share/licenses/opm/NOTICE.txt (in image) for source offer.
LABEL org.opencontainers.image.licenses="Apache-2.0 AND GPL-3.0-or-later"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_PREFER_BINARY=1

WORKDIR /workspace

# System deps: PDF parsing, OPM Flow (shared by ressim and workflow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    gnupg \
    git \
    wget \
    curl \
    ca-certificates \
    build-essential \
    poppler-utils \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    && add-apt-repository ppa:opm/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libopm-simulators-bin \
        libopm-simulators \
    && rm -rf /var/lib/apt/lists/*

# GPL-3.0 compliance: embed notice and source pointer for OPM binaries
COPY LICENSES/OPM-GPL3-NOTICE.txt /usr/share/licenses/opm/NOTICE.txt

# Copy all agent components (order for layer caching: least-changed first)
COPY config /workspace/config
COPY llm_provider /workspace/llm_provider
COPY orchestration_agent /workspace/orchestration_agent
COPY sim_agent /workspace/sim_agent
COPY workflow_agent /workspace/workflow_agent

# Install sim_agent (provides LangChain, LangGraph, openai, OPM tools)
WORKDIR /workspace/sim_agent
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --only-binary=:all: grpcio && \
    /opt/venv/bin/pip install -e ".[rag,analysis,flow_diagnostics]" && \
    /opt/venv/bin/pip install openai

# Install workflow_agent (optimization deps + agentic)
WORKDIR /workspace/workflow_agent
RUN /opt/venv/bin/pip install -r workflow/optimization/requirements.txt && \
    /opt/venv/bin/pip install -e .

ENV PATH="/opt/venv/bin:$PATH"

# OPM_FLOW_EXTRA_ARGS wrapper (e.g. --CheckSatfuncConsistency=0)
RUN echo '' >> /root/.bashrc && \
    echo 'flow() { command flow "$@" $OPM_FLOW_EXTRA_ARGS; }' >> /root/.bashrc

WORKDIR /workspace

# Default: run orchestration (interactive ressim chat)
CMD ["python", "-m", "orchestration_agent", "--interactive"]
