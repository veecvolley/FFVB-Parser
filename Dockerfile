FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USER=veecvolley

WORKDIR /app
COPY . /app
    
RUN addgroup --system ${USER} && adduser --system --ingroup ${USER} ${USER} \
 && chown -R ${USER}:${USER} /app

USER ${USER}

RUN pip install --upgrade --no-warn-script-location pip \
 && if [ -f requirements.txt ]; then pip install --no-warn-script-location --no-cache-dir -r requirements.txt; fi

CMD ["python", "main.py"]
