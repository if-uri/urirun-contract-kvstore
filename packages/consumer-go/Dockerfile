FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY packages/consumer-go/go.mod .
COPY packages/consumer-go/service.go .
RUN go build -o service .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /build/service /app/service
COPY contracts.json /app/contracts.json
ENV CONTRACTS=/app/contracts.json PORT=8803
EXPOSE 8803
HEALTHCHECK --interval=3s --timeout=2s --retries=10 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8803/health')"
CMD ["/app/service"]
