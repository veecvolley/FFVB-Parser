## FFVB-Parser  

FFVB-Parser is a tool for parsing scores and data provided by the FFVB website (https://www.ffvb.org / https://www.ffvbbeach.org/ffvbapp/).
The aim is to be able to dynamically generate regular graphical tables of the scores of the selected club.

---
## Note

---

## Documentation

---

## Installation - Deployment

### Docker

Build & Run

```
docker build -t veec-comm-generator:dev -f Dockerfile.dev .

docker run -it --rm -v $PWD:/app -p 8000:8000 veec-comm-generator:dev
```

--> http://localhost:8000


