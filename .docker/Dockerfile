FROM python:3.11-slim

WORKDIR /workspace

# Install Jupyter and common data science libraries
RUN pip install --no-cache-dir \
    jupyter \
    notebook \
    jupyterlab \
    numpy \
    pandas \
    matplotlib \
    scikit-learn

# Expose port for Jupyter
EXPOSE 8888

# Run Jupyter Lab by default
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--no-browser"]
