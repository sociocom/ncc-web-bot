FROM python:3.9-slim

ENV RYE_NO_AUTO_INSTALL=1
ENV RYE_INSTALL_OPTION="--yes"

ENV PATH=/bot/.venv/bin:$PATH

RUN apt-get update && apt-get install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN curl -Lf https://rye.astral.sh/get | bash && \
    echo 'source "/root/.rye/env"' >> ~/.bashrc

SHELL ["/bin/bash", "-lc"]

WORKDIR /bot

COPY .python-version pyproject.toml requirements.lock requirements-dev.lock /bot/
RUN source ~/.bashrc && rye sync --no-lock && \
    rm -rf /root/.cache

COPY src/ /bot/src
COPY .env /bot/

CMD ["/bin/bash", "-c", "source ~/.bashrc && ~/.rye/shims/streamlit run /bot/src/login.py --server.port=3030 --server.baseUrlPath=/brecobot-counselor-chat"]