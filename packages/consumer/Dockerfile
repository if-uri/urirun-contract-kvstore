FROM python:3.12-slim
RUN pip install --no-deps "urirun-contract @ git+https://github.com/if-uri/urirun-contract.git"
WORKDIR /app
COPY toolkit/ /app/toolkit/
COPY contracts.json /app/contracts.json
COPY packages/consumer/ /app/packages/consumer/
ENV CONTRACTS=/app/contracts.json PORT=8802
EXPOSE 8802
HEALTHCHECK --interval=3s --timeout=2s --retries=10 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8802/health')"
CMD ["python", "packages/consumer/service.py"]
