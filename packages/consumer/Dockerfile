FROM python:3.12-slim
COPY --from=urirun_contract_src / /tmp/urirun-contract
RUN pip install --no-deps /tmp/urirun-contract && rm -rf /tmp/urirun-contract
WORKDIR /app
COPY toolkit/ /app/toolkit/
COPY contracts.json /app/contracts.json
COPY packages/consumer/ /app/packages/consumer/
ENV CONTRACTS=/app/contracts.json PORT=8802
EXPOSE 8802
HEALTHCHECK --interval=3s --timeout=2s --retries=10 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8802/health')"
CMD ["python", "packages/consumer/service.py"]
