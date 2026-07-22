import random
from pathlib import Path
import os
import pickle
import io

import requests
import json

import uvicorn
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from loguru import logger

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from settings import Settings
from city_bounds import check_town as _check_town
from dijkstra_inference import DijkstraPath
from eta_inference import ETAInf
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import(
    FastAPI,
    Header,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile
    )

# CORS: restrict to the GitHub Pages origin(s) that host the UI.
# Override in prod via ALLOWED_ORIGINS (comma-separated) — see AZURE_DEPLOYMENT_PLAN.md C2.
origins = os.getenv("ALLOWED_ORIGINS", "https://vlzm.github.io").split(",")
BASE = Path(os.path.realpath(__file__)).parent

# Rate limit keyed by client IP — main barrier against flooding the CPU-bound
# /get_path endpoint (CORS does not protect against curl). See plan C1.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount('/js', StaticFiles(directory=BASE / 'js'))
app.mount('/css', StaticFiles(directory=BASE / 'css'))

logger.debug('loading abakan dijkstra graph and ETA model')
dijkstra_abakan = DijkstraPath(BASE / 'data/dijkstra.pickle', BASE / 'data/clear_nodes.pkl')
etainf_abakan = ETAInf(BASE / 'data/SimpleTTE.pth', BASE / 'data/meteoData.csv', BASE / 'data/dgi_sage_abakan_5_5_5_relu_relu_relu_200e_mean_pool_0.0114.csv')
weights_dict_abakan = {}

logger.debug('loading omsk dijkstra graph')
# Omsk computes ETA via get_shortest_path_grph (weighted-sum), not the FFNet ETA model,
# so etainf_omsk is never used — its .forward() call in return_path is commented out.
# Dropping it avoids loading the 50M dgi_sage embeddings CSV a second time (~40-80 MB RAM).
dijkstra_omsk = DijkstraPath(BASE / 'data/graph_omsk.pkl', BASE / 'data/clear_nodes_omsk.pkl')
weights_dict_omsk = {}

logger.debug('loading abakan weight variants')
for weight in sorted((BASE / 'data/weights_abakan').iterdir()):
    if '.pkl' in weight.name:
        with open(weight, 'rb') as fd:
            weights_dict_abakan[weight.name.split('.')[0]] = pickle.load(fd)

logger.debug('loading omsk weight variants')
for weight in sorted((BASE / 'data/weights_omsk').iterdir()):
    if '.pkl' in weight.name:
        with open(weight, 'rb') as fd:
            weights_dict_omsk[weight.name.split('.')[0]] = pickle.load(fd)
    

class Points(BaseModel):
    start_lat: float = 55.7809453
    start_lon: float = 37.6373427
    end_lat: float = 55.6217188
    end_lon: float = 37.49859


class PointsTyped(BaseModel):
    start_lat: float = 55.7809453
    start_lon: float = 37.6373427
    end_lat: float = 55.6217188
    end_lon: float = 37.49859
    type_: str = "beauty_dist_weights"

def check_town(points):
    return _check_town(points.start_lat, points.start_lon, points.end_lat, points.end_lon)
    
preloaded_weights = True
logger.debug('loading graphormer weights')
if preloaded_weights:
    weights_abakan_link = str(BASE) + '/data/graphormer_weights/' + 'weights_abakan.pickle'
    weights_omsk_link = str(BASE) + '/data/graphormer_weights/' + 'weights_omsk.pickle'
    weights_abakan = pd.read_pickle(weights_abakan_link)
    weights_abakan = [float(x) for x in weights_abakan]
    weights_omsk = pd.read_pickle(weights_omsk_link)
    weights_omsk = [float(x) for x in weights_omsk]
    # weights_dict_abakan['graphormer_weights'] = weights_abakan
    # weights_dict_omsk['graphormer_weights'] = weights_omsk
else:
    a = Points()
    body = {"start_lat": a.start_lat,
                        "start_lon": a.start_lon,
                        "end_lat": a.end_lat,
                        "end_lon": a.end_lon,
                       "type": 'lolo'}

    r = requests.post('http://127.0.0.1:3006/get_path', headers = {'Content-Type': 'application/json'}, json = body)
    weights_abakan = r.json()['abakan']
    weights_omsk = r.json()['omsk']
logger.debug('graphormer weights loaded')

    

@app.get('/')
def ping():
    html_file = BASE / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.get('/health')
def health():
    # All heavy assets load at module import (before uvicorn accepts requests),
    # so any 200 here means the container is fully warm. Used by the UI warmup
    # spinner to poll the cold-started container. Intentionally not rate-limited.
    return {"status": "ok"}


@app.post('/get_path')
@limiter.limit("20/minute")
def return_path(request: Request, points: Points):

    logger.debug('start get_path')
    logger.info(points)
    if not all(map(lambda x: 0 <= x[1] <= 180, points)):
        raise HTTPException(status_code=400, detail="Every coordinate should be in 0..180")
    cur_data_name = check_town(points)
    response = []
    paths = []
    if cur_data_name == 'abakan':
        logger.debug('routing in abakan')
        for name, weights in weights_dict_abakan.items():
            p, path = dijkstra_abakan.get_shortest_path((points.start_lat, points.start_lon), (points.end_lat, points.end_lon), weights)
            etapred = etainf_abakan.forward(p, points, path[1][:2], path[1][-2:])
            dict_ = {'path': path[1][:-1], 'eta': etapred, 'type': name}
            paths.append(dict_['path'])
            response.append(dict_)
        name = 'graphormer_weights'
        weights = weights_abakan
        p, path, time = dijkstra_abakan.get_shortest_path_grph((points.start_lat, points.start_lon), (points.end_lat, points.end_lon), weights)
        dict_ = {'path': path[1][:-1], 'eta': int(time), 'type': name}
        response.append(dict_)
        logger.debug('len response {}', len(response))
    elif cur_data_name == 'omsk':
        logger.debug('routing in omsk')
        for name, weights in weights_dict_omsk.items():
            p, path, time = dijkstra_omsk.get_shortest_path_grph((points.start_lat, points.start_lon), (points.end_lat, points.end_lon), weights)
            time = time / 10
            # time = etainf_omsk.forward(p, points, path[1][:2], path[1][-2:])
            dict_ = {'path': path[1][:-1], 'eta': int(time), 'type': name}
            # paths.append(dict_['path'])
            response.append(dict_)
        name = 'graphormer_weights'
        weights = weights_omsk
        p, path, time = dijkstra_omsk.get_shortest_path_grph((points.start_lat, points.start_lon), (points.end_lat, points.end_lon), weights)
        dict_ = {'path': path[1][:-1], 'eta': int(time), 'type': name}
        response.append(dict_)
        logger.debug('len response {}', len(response))
    else:
        logger.debug('coordinates outside supported cities')
        raise HTTPException(status_code=400, detail="Coordinates should be in Omsk or Abakan")
    
            
    return response


if __name__ == "__main__":
    app_name = "app:app"
    # uvicorn.run(app_name, host=Settings().hostname, port=Settings().port, log_level="info", ssl_certfile=Settings().ssl_certfile, ssl_keyfile=Settings().ssl_keyfile)
    uvicorn.run(app, host='0.0.0.0', port=80)