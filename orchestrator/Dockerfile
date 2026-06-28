FROM python:3.12-slim
COPY --from=urirun_contract_src / /tmp/urirun-contract
RUN pip install --no-deps /tmp/urirun-contract && rm -rf /tmp/urirun-contract
WORKDIR /app
COPY toolkit/ /app/toolkit/
COPY contracts.json /app/contracts.json
COPY orchestrator/ /app/orchestrator/
ENV CONTRACTS=/app/contracts.json
CMD ["python", "orchestrator/drive.py"]
