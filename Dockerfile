FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git make latexmk texlive-latex-extra texlive-science texlive-fonts-recommended \
        texlive-bibtex-extra biber pandoc && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.12.5

WORKDIR /work
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --extra dev

COPY . .
ENV PATH="/work/.venv/bin:${PATH}"
CMD ["make", "quick"]
