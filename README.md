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
5. Place general dataset files into `shared/utils/datasets/`.
 - TODO: Specify dataset files and their sources.
6. Run the `docker-compose-infra.yml` file to start the necessary infrastructure services.
    ```sh
    docker compose -f docker-compose-infra.yml up -d --build
    ```
7. Run the `docker-compose-services.yml` file to start the essential services.
    ```sh
    docker compose -f docker-compose-apps.yml up -d --build
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