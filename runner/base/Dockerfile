FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends iptables curl build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir streamlit==1.32.2

COPY entrypoint.sh /usr/local/bin/sheetify-entrypoint
RUN chmod +x /usr/local/bin/sheetify-entrypoint

WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/sheetify-entrypoint"]
CMD ["streamlit", "hello"]
