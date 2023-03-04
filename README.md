# pigeon
Serendipitious intermittent message delivery service

## Setting up development environment
1. Create python virtual environment: `pyenv virtualenv 3.9.10 py39_pigeon`
2. Install python libraries in the newly created environment: `pip install -r requirements.txt`
3. Build Docker container: `docker build . -t pigeon`
4. Run Docker container: `docker run -p 5000:5000 -d --name pigeon pigeon`