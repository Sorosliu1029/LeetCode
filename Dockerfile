FROM jupyter/base-notebook:python-3.8.6
LABEL author="Soros Liu"
RUN conda install --yes 'python-graphviz=0.17' && \
    conda clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
