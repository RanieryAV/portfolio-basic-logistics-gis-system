# portfolio-basic-logistics-gis-system

# Prerequisites:
1. Operating System (OS): **Linux** (such as, but not limited to, [Ubuntu](https://ubuntu.com/download/desktop))
2. A global Python install and the `pyenv` library installed
3. Docker Engine installed and running [(Reference link)](https://docs.docker.com/engine/install/)
4. Node.js installed [(Reference link)](https://nodejs.org/en/download/)

# Setup instructions
1. Clone this repository
    ```sh
    git clone https://github.com/RanieryAV/portfolio-basic-logistics-gis-system.git
    cd portfolio-basic-logistics-gis-system
    ```
2. Run the `install_dependencies.sh` script to install the required dependencies.
    ```sh
    chmod +x scripts/install_dependencies.sh
    ./scripts/install_dependencies.sh
    ```
3. Run the `set_up_folder_permissions.sh` script to start the Data Processing API and configure crucial directories.
    ```sh
    chmod +x scripts/set_up_folder_permissions.sh
    ./scripts/set_up_folder_permissions.sh
    ```
4. Run the `create_nextjs_app.sh` script to create the Next.js application for the frontend demo.
    ```sh
    chmod +x scripts/create_nextjs_app.sh
    ./scripts/create_nextjs_app.sh
    ```
5. Place general dataset files into `shared/utils/datasets/`:
 - Access the following websites:
    - [Portal de Dados Abertos - Agências dos Correios nos municípios alagoanos (click here)](https://dados.gov.br/dados/conjuntos-dados/agencias-dos-correios-nos-municipios-alagoanos) , click the **`Recursos`** dropdown menu to reveal the available resource sections and download the **`correios_al.geojson.json`** file by clicking on the button named **`Acessar o recurso`** right under the section **`[GeoJSON]  gências dos Correios`**.
    - [Portal de Dados Abertos - Bairros de Alagoas (click here)](https://dados.gov.br/dados/conjuntos-dados/bairros-de-alagoas1) , click the **`Recursos`** dropdown menu to reveal the available resource sections and download the **`bairros.geojson.json`** file by clicking on the button named **`Acessar o recurso`** right under the section **`[GeoJSON]  Bairros de Alagoas Censo IBGE 2022`**.
    - [Portal de Dados Abertos - Malha de Ruas e Avenidas 🌎 (click here)](https://dados.gov.br/dados/conjuntos-dados/malha-de-ruas-e-avenidas1) , click the **`Recursos`** dropdown menu to reveal the available resource sections and download the **`arruamento-al-osm.geojson.json`** file by clicking on the button named **`Acessar o recurso`** right under the section **`[GeoJSON]  Malha de arruamento`**.
    - Then, place the **`correios_al.geojson.json`**, **`bairros.geojson.json`** and **`arruamento-al-osm.geojson.json`** files in the **`shared/utils/datasets/`** directory.
6. Run the `docker-compose-infra.yml` file to start the necessary infrastructure services.
    ```sh
    docker compose -f docker-compose-infra.yml up -d --build
    ```
7. Run the `docker-compose-services.yml` file to start the essential services.
    ```sh
    docker compose -f docker-compose-apps.yml up -d --build
    ```

8. **[OPTIONAL]** If you prefer to run the apps locally (outside of Docker containers), you can do so by following the instructions below:
    - For the Data Processing API, run the commands below from the repository root directory:
    ```sh
    chmod +x scripts/launch_data_processing_api.sh
    ./launch_data_processing_api.sh
    ```
    - For the Model Training API, run the commands below from the repository root directory:
    ```sh
    chmod +x scripts/launch_model_training_api.sh
    ./launch_model_training_api.sh
    ```
    - For the Model Deployment API, run the commands below from the repository root directory:
    ```sh
    chmod +x scripts/launch_model_deployment_api.sh
    ./launch_model_deployment_api.sh
    ```
    - For the Frontend Demo, run the commands below from the repository root directory:
    ```sh
    chmod +x scripts/launch_frontend_demo.sh
    ./launch_frontend_demo.sh
    ``` 

# Troubleshooting:
- Every now and then, or when you run out of disk space, run the command below to clean up unused Docker resources.
    ```sh
    docker system prune -af
    ```
- If you suspect that the Docker build cache is causing issues (or you suspect that something is wrong while downloading images during a build operation) you can clear it with the command below (and restart Docker after that).
    ```sh
    docker builder prune -a -f
    sudo systemctl restart docker
    ```
- If you are using a Linux OS, you may need to add your user to the Docker group in order to run Docker commands without `sudo`. You can do this with the command below (and restart your computer after that).
    ```sh
    sudo usermod -aG docker $USER
    ```

# NOTES:
- It was discovered that in order for the local data processing API to be able to send Spark jobs to the Spark containers, the Driver host must also be a container. Insisting on using the local API would require additional configurations that are not worth the effort at this moment (such as using extra softwares, like Lily, which would increase function verbosity and add an extra failure point).
    - Consequence: Only the containerized data processing API can send Spark jobs to the Spark containers.
    - That leaves the local APIs for debugging purposes only.

---

# Pants Build System Integration

## Setup
1. **Install the Pants Launcher**:
    ```sh
    curl --proto '=https' --tlsv1.2 -fsSL [https://static.pantsbuild.org/setup/get-pants.sh](https://static.pantsbuild.org/setup/get-pants.sh) | bash
    ```
2. **Add to PATH & Reload** *(Bash default)*:
    ```sh
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```
    *(If using Zsh, replace `~/.bashrc` with `~/.zshrc`)*
3. **Verify Installation**:
    ```sh
    pants --version
    ```
4. **Configure `pants.toml`**: 
    Create a `pants.toml` file in the root directory and add the following configuration:
    ```toml
    [GLOBAL]
    pants_version = "2.20.0"
    backend_packages = [
    "pants.backend.python",
    "pants.backend.experimental.python.lint.ruff.check",   # Ruff Linter
    "pants.backend.experimental.python.lint.ruff.format",  # Ruff Formatter
    "pants.backend.python.typecheck.mypy",
    ]

    [python]
    # Matches your repository's .python-version (3.11)
    interpreter_constraints = ["==3.11.*"]

    [source]
    # Tell Pants where your Python import paths begin
    root_patterns = [
        "/",                                  # For your shared domain/ folder
        "/applications/api_data_processing",  # So 'import src...' works here
        "/applications/api_model_deployment", # So 'import src...' works here
        "/applications/api_model_training"    # So 'import src...' works here
    ]

    [python-infer]
    # Tell Pants to resolve overlapping dependencies (like FastAPI)
    # by picking the requirements target in the same source root as the code.
    ambiguity_resolution = "by_source_root"
    ```
5. **Generate `BUILD` Files**: 
    Automatically map boundaries and establish internal dependencies.
    ```sh
    pants tailor ::
    ```

## Day-to-Day Workflow
Run these commands from the repository root to maintain formatting, code quality, and testing standards. Move down the list to progress from automatic cleanups to strict validations:

*   **Auto-Fix**: `pants fix ::` *(Safely resolves unused imports and variables)*
    * *Note: There is also an option for automatically applying unsafe fixes. **These fixes can change the runtime behavior or semantics of your code.** Always ensure your code is committed to version control before executing these commands so you can carefully review the diff generated by the unsafe rules.*
        * *The command is:* `pants --ruff-args=--unsafe-fixes fix ::`
*   **Format**: `pants fmt ::` *(Corrects indentation, quotes, line lengths, and spacing)*
*   **Lint**: `pants lint ::` *(Catches undefined variables and code errors Ruff cannot fix)*
*   **Type Check**: `pants check ::` *(Validates type hints via MyPy)*
*   **Test**: `pants test ::` *(Executes unit tests for changed code only)*
*   **Maintenance (`pants tailor ::`)**: Run only when adding new folders or generating `BUILD` files for new microservices.