ARG BUILD_FROM
FROM $BUILD_FROM

COPY . .
WORKDIR /app

RUN apk --update add --no-cache \
    jq \
    python3 \
    py3-pip
RUN python3 -m venv /venv && \
    . /venv/bin/activate && \
    pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
