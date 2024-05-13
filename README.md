# Streamlit Dashboard Application

This is a Streamlit-based web application structured to provide various financial and utility tools. The app is containerized using Docker, making it easy to deploy and run.

## Configuration

The application uses several configuration files. Copy and rename each files without the ".example" suffix:
- `.streamlit/config.toml.example`: A sample streamlit configuration for reference.
- `.streamlit/secrets.toml.example`: A sample secrets configuration file used by streamlit. This is where the database connection information is stored, among other useful configuration items.
- `nginx/nginx.conf.example`: A sample NGINX configuration for reference. Can be used as a starting point if you decide to place a nginx reverse proxy/load balancer in front of the app.


## Getting Started

### Clone the Repository

```bash
git clone https://github.com/magoulet/personal-website-streamlit.git
cd personal-website-streamlit
```

### Setting Up the Virtual Environment

1. **Create a Virtual Environment**

   Open a terminal (or command prompt) and navigate to the project directory. Then, create a virtual environment by running:

   ```sh
   python3 -m venv .venv
   ```

   This will create a new directory named `.venv` in your project directory containing the virtual environment.

2. **Activate the Virtual Environment**

   - On **Windows**, run:

     ```sh
     .\.venv\Scripts\activate
     ```

   - On **macOS/Linux**, run:

     ```sh
     source .venv/bin/activate
     ```

   After activating the virtual environment, you should see `(.venv)` prefixed in your terminal prompt.

### Installing Dependencies

With the virtual environment activated, install the required dependencies using `pip`:

```sh
pip install -r requirements.txt
```


### Running the Streamlit App

Start the Streamlit app by running the following command in the terminal:

```sh
streamlit run app.py
```

This will launch the app and provide a local URL (usually `http://localhost:8501`) that you can open in your web browser to view the application.

### Deactivating the Virtual Environment

Once you are done with running the app, you can deactivate the virtual environment by running:

```sh
deactivate
```

Adding this section to your README file will provide your users with a clear, step-by-step guide on how to set up their environment and run the Streamlit application.

### Build and Run the Docker Containers
Alternately, this app can be run as a Docker container.

#### Build the Docker Image
```bash
docker-compose build
```

#### Run the Docker Container
```bash
docker-compose up
```

This will start your Streamlit application and expose it on port 8501.

#### Running the Application

After running `docker-compose up`, you can access the application in your web browser at:

```
http://localhost:8501
```

## Using a Load Balancer or Reverse Proxy

We recommend placing a load balancer or reverse proxy in front of this application to handle SSL termination and improve performance. In this project, we provide a sample NGINX configuration that uses a self-signed certificate for SSL.

### NGINX Configuration

The `nginx` directory contains the following file:
- `nginx.conf.example`: Sample NGINX configuration file to use as a reference.

We also created a useful script:
- `scripts/generate-self-signed-cert.sh`: Script to generate a self-signed SSL certificate.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.