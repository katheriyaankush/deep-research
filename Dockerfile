FROM python:3.11-slim

# HF Spaces runs as non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Install dependencies
COPY --chown=user requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy source code
COPY --chown=user app.py .
COPY --chown=user core/ ./core/
COPY --chown=user ai_agents/ ./ai_agents/

# HF Spaces requires port 7860
EXPOSE 7860

# Run the app on port 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
