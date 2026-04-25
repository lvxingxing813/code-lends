FROM python:3.11-slim

WORKDIR /app

COPY codelens/pyproject.toml codelens/README.md ./codelens/
COPY codelens/src ./codelens/src
COPY demo-project ./demo-project

WORKDIR /app/codelens
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sh", "-c", "codelens scan /app/demo-project && codelens analyze '修改用户登录验证码规则' --project /app/demo-project && codelens serve --project /app/demo-project --host 0.0.0.0 --port 8000"]
