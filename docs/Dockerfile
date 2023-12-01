FROM python:3.9-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
 && apt-get install --no-install-recommends -y \
      curl \
 && apt-get autoremove \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV PM_PACKAGES_ROOT=/var/tmp/packman
COPY . /work

RUN /work/repo docs || true
RUN /work/tools/packman/python.sh -m pip install --no-cache-dir --no-deps -U \
   -t /tmp/extension \
   sphinx-copybutton
RUN (cd /tmp/extension; tar cf - . ) | (cd /var/tmp/packman/chk/sphinx/4.5.0.2-py3.7-linux-x86_64/; tar xf -)
RUN rm -rf /work /tmp/extension
