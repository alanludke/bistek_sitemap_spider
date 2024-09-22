
`$ tree
.
├── bistek_sitemap_spider/
│   ├── __init__
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scrapy.cfg
│   ├── data/
│   ├── logs/
│   ├── app.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── spider1.py
│   │   └── ...
│   └── ...
├── microservice2/
├── microservice3/
├── microservice4/
├── common/
│   ├── __init__.py
│   ├── items.py
│   ├── models.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── setup.py
│   ├── utils.py
│   └── ...
└── ...
`

virtualenv venv -p python3.9
avenv
pip install -r requirements.txt

from .
`
docker build -t bistek_sitemap_spider:v0.1 -f bistek_sitemap_spider/Dockerfile .
`

`
docker run -it bistek_sitemap_spider:v0.1 /bin/bash
`


`
docker run -it -e AZURE_ACCOUNT_NAME=$AZURE_ACCOUNT_NAME \
                -e AZURE_ACCOUNT_URL=$AZURE_ACCOUNT_URL \
                -e AZURE_ACCOUNT_KEY=$AZURE_ACCOUNT_KEY \
                -e AZURE_CONTAINER_NAME=$AZURE_CONTAINER_NAME \
                -e DB_HOST=$DB_HOST \
                -e DB_PORT=$DB_PORT \
                -e DB_USERNAME=$DB_USERNAME \
                -e DB_PASSWORD=$DB_PASSWORD \
                -e DB_NAME=$DB_NAME \
                bistek_sitemap_spider:v0.1 /bin/bash
`


# TODO talvez seria interessante colocar uma coluna com uma referência ao path do log
# TODO ou talvez uma identificação de início/fim da execução? (seria legal colocar em uma outra tabela)


