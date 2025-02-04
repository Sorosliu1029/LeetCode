# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/recipes.html#using-mamba-install-recommended-or-pip-install-in-a-child-docker-image
FROM quay.io/jupyter/base-notebook:latest
LABEL author="Soros Liu"
RUN mamba install --yes 'python-graphviz' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
