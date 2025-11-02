FROM jupyter/scipy-notebook:python-3.11.6

WORKDIR /home/jovyan/work

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["start-notebook.sh", "--NotebookApp.token=''", "--NotebookApp.password=''", "--NotebookApp.notebook_dir=/home/jovyan/work"]
