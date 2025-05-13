FROM quay.io/jupyter/minimal-notebook:latest
LABEL author="Soros Liu"
# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/recipes.html#using-mamba-install-recommended-or-pip-install-in-a-child-docker-image
RUN mamba install --yes python-graphviz nbconvert requests jinja2 ipython && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
