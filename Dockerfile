FROM debian:stable
SHELL ["/bin/bash", "-lc"]
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl build-essential

RUN curl -Lf https://rye.astral.sh/get | RYE_NO_AUTO_INSTALL=1 RYE_INSTALL_OPTION="--yes" bash && \
    echo 'source "/root/.rye/env"' >> ~/.bashrc

WORKDIR /bot
COPY .python-version pyproject.toml requirements.lock requirements-dev.lock /bot/

RUN rye sync --no-lock

COPY src/ .env /bot/

CMD ["/bin/bash", "-c", "source ~/.bashrc && rye run streamlit run login.py --server.port=3030 --server.baseUrlPath=/brecobot-counselor-chat"]
