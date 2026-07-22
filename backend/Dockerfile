FROM python:3.9
USER root
RUN pip install -U pip
RUN pip install --upgrade setuptools
RUN pip install --upgrade pip
RUN pip install fastapi
RUN pip install pydantic
RUN pip install pydantic-settings
RUN pip install uvicorn
RUN pip install numpy
RUN pip install pandas
RUN pip install scikit-learn
RUN pip install python-igraph
RUN pip install loguru

RUN pip install requests
# CPU-only build — ACA has no GPU, so the full CUDA wheel (~6GB of nvidia-*-cu12
# packages) is dead weight that bloats the image and slows scale-from-zero cold start.
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install slowapi

COPY . .
EXPOSE 80
CMD ["python", "app/app.py"]
