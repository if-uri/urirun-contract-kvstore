FROM python:3.12-slim
RUN pip install --no-deps "urirun-contract @ git+https://github.com/if-uri/urirun-contract.git"
WORKDIR /app
COPY toolkit/ /app/toolkit/
COPY contracts.json /app/contracts.json
COPY orchestrator/ /app/orchestrator/
ENV CONTRACTS=/app/contracts.json
CMD ["python", "orchestrator/drive.py"]
