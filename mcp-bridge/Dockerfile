FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime deps
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic

# Copy code
COPY bridge.py /app/bridge.py
COPY cli.py /app/cli.py

# CLI shim (fix: pass argv correctly; no escaping that collapses args)
RUN cat > /usr/local/bin/mcp-bridge << "SH" \
 && chmod +x /usr/local/bin/mcp-bridge
#!/usr/bin/env bash
exec python /app/cli.py "$@"
SH

EXPOSE 8787
CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "8787"]