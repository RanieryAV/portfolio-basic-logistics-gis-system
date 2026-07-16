# portfolio-basic-logistics-gis-system

# Setup instructions
1. Clone this repository
    ```sh
    git clone https://github.com/RanieryAV/portfolio-basic-logistics-gis-system.git
    cd masters-project-PPGEEC
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
4. Place general dataset files into `shared/utils/datasets/`.
 - TODO: Specify dataset files and their sources.
5. Run the `docker-compose-infra.yml` file to start the necessary infrastructure services.
    ```sh
    docker compose -f docker-compose-infra.yml up -d --build
    ```
6. Run the `docker-compose-services.yml` file to start the essential services.
    ```sh
    docker compose -f docker-compose-apps.yml up -d --build
    ```

NOTES:
- It was discovered that in order for the local data processing API to be able to send Spark jobs to the Spark containers, the Driver host must also be a container. Insisting on using the local API would require additional configurations that are not worth the effort at this moment (such as using extra softwares, like Lily, which would increase function verbosity and add an extra failure point).
    - Consequence: Only the containerized data processing API can send Spark jobs to the Spark containers.
    - That leaves the local APIs for debugging purposes only.
- Every now and then, run the command below to clean up unused Docker resources.
    ```sh
    docker system prune -af
    ```
