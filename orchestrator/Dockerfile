FROM python:3.12-slim
WORKDIR /app
COPY toolkit/ /app/toolkit/
COPY contracts.json /app/contracts.json
COPY orchestrator/ /app/orchestrator/
ENV CONTRACTS=/app/contracts.json
CMD ["python", "orchestrator/drive.py"]
