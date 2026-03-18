# Sim agent image. Ubuntu 24.04, venv, OPM Flow.
# License: Application Apache-2.0; OPM Flow GPL-3.0-or-later (see NOTICE.txt in image).

FROM ubuntu:24.04
LABEL org.opencontainers.image.licenses="Apache-2.0 AND GPL-3.0-or-later"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_PREFER_BINARY=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common gnupg git wget curl ca-certificates \
    build-essential poppler-utils python3 python3-venv python3-dev python3-pip \
    && add-apt-repository ppa:opm/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends libopm-simulators-bin libopm-simulators \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/share/licenses/opm \
    && printf 'OPM Flow Simulator -- GPL-3.0-or-later Notice\n\nPackages: libopm-simulators, libopm-simulators-bin\nSource:   https://github.com/OPM/opm-simulators\nLicense:  GNU General Public License v3.0 or later (SPDX: GPL-3.0-or-later)\n\nCopyright (C) 2011-2024 SINTEF Digital, Mathematics & Cybernetics\nCopyright (C) 2011-2024 Equinor ASA\n\nFull license text: https://www.gnu.org/licenses/gpl-3.0.html\n\nSource (GPL-3.0 s.6d written offer, valid 3 years from image build):\n  https://github.com/OPM/opm-simulators\n  https://github.com/OPM/opm-common\n  https://github.com/OPM/opm-grid\n  https://github.com/OPM/opm-models\n' > /usr/share/licenses/opm/NOTICE.txt

COPY sim_agent /workspace/sim_agent
WORKDIR /workspace/sim_agent

RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --only-binary=:all: grpcio && \
    /opt/venv/bin/pip install -e ".[rag,analysis,flow_diagnostics]" && \
    /opt/venv/bin/pip install openai

ENV PATH="/opt/venv/bin:$PATH"

RUN echo '' >> /root/.bashrc && \
    echo 'flow() { command flow "$@" $OPM_FLOW_EXTRA_ARGS; }' >> /root/.bashrc

CMD ["/bin/bash"]
