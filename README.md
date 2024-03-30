# [PigeonMsg](http://pigeonmsg.com)
Trip planning service which leverages AI recommendations as well as human traveling experience

## How does this service work?
- Onboarding to the service
    - You will be asked to share information about cities you have previoulsy visited or lived in (voluntary)
    - You will be made aware of service restrictions and rate limiting (if any)
    - All interactions with this service will be via text message
    - At any point, if you want to communicate with the service, start your message with the word `pigeon`
- Leveraging AI for trip planning
    - Ask basic questions realted to planning a visit to a city and recive AI recommendations
    - Converse with the AI as you would with any other human
    - There will be limits on the interaction with the AI - these are determined by your past usage of the service
- Leveraging human help for trip planning
    - Requesting help - for more specific questions that AI cannot answer, get connected up with another user (anonymously) who has visited the same place
    - Providing help - answer questsions other users might have (after being connected anonymously) about visiting the places you have been to
    - Every connection to another human will be valid for a limited amount of time and have text count/size limits - these are determined by your past interactions with the service
    - A user can only be connected with one other user at any given time -  there are limits on the total number of connections per week
    - A users can chose to end their connection with another user at any time
    - Once a connection has ended, both users will be asked to rate their conversation and this will help determine quality of future connections


## Development

### Mandatory Dependencies
1. [Docker](https://www.docker.com/): needs to be installed for containerizing the app
2. [Make](https://www.gnu.org/software/make/): needs to be installed for running app specific cli commands
3. Environment variables: shoule be placed in `.env` (refer `pigeon/templates/.env_template/` for format)
4. Secret variables: should be placed in `pigeon/secrets/` (refer `pigeon/templates/secrets_template/` for format)
5. Twilio configurations:
    - Access your Twilio console, navigate to 'Phone Numbers -> Manage -> Active Numbers'
    - In the option for 'A message comes in', add the url for this app
    - URL format: `https://APP_USERNAME_CONFIGURED_IN_SECRETS:APP_PASSWORD_CONFIGURED_IN_SECRETS@YOUR_DOMAIN_URL/sms` (example https://test:test@pigeonmsg.com/sms)
    - If you do not have a domain URL, you can also configure the IP address (exposed to the internet) of the remote server that the app is running on
6. Langchain configurations:
    - Place your custom knowledge documents (if any) in `/pigeon/app/back_end/langchain/retrieval_docs/` - these will be used to provide additional context for the AI chatbot

### Optional Dependencies
1. [Nginx](https://nginx.org/en/download.html): install this if you want to implement reverse proxy to serve app's web page
2. Nginx configurations: should be placed in `/usr/local/etc/nginx/` (refer `pigeon/templates/nginx_template/` for format)

### Working in development environment
1. Start the application: `make start`
2. Stop the application: `make stop`

### Helper commands
- Access app landing page:
  ```
  http://localhost:8001/ (if not configured Nginx reverse proxy)
  https://localhost (if configured Nginx reverse proxy)
  ```

- Access MongoDB cli: 
  ```
  docker exec -it mongodb bash
  eval $MONGOSH
    Example DB commands:
        use pigeon
        show collections
        db.users.insertOne({name: "John Doe", phone_number: '+19999999999'})
        db.users.find()
        db.users.deleteOne({name: "John Doe", phone_number: '+19999999999'})
        db.users.deleteMany({})
  ```

- Twilio
  - Access Twilio cli: 
    ```
    make twilio-cli
    twilio phone-numbers:list
    ```

  - Simulate Twilio webhook to receive sms:
    - Obtain digest token for web server credentials:
      ```
      python -c 'import base64; h = base64.urlsafe_b64encode (b"test:test"); print(h)'
      ```
    - Obtain twilio signature by following documentation in `app/back_end/routes.py/validate_twilio_signature` (not needed for dev testing)
    - Send a curl request using token and twilio signature; example -
    ```
      curl -i -X POST \
      -H "Authorization: Basic dGVzdDp0ZXN0" \
      -H "X-Twilio-Signature: 5rVrhMTIJCCg0FOvzCbH809pehE=" \
      -d "To=%2B1234567890" -d "From=%2B0987654321" -d "Body=Hello, pigeon" \
      https://localhost/sms
    ```

### Work in progress
- TODO: create feature for user to user communication
- TODO: create feature for user data updates via 'pidge' command
- TODO: create feature for landing page with [basic usage guide, git project in about, feedback, faqs]
- TODO: experiment with user to AI communication by building LLM [from scratch](youtube.com/watch?v=kCc8FmEb1nY)
- TODO: experiment with deploying llm locally using [llama](github.com/ggerganov/llama.cpp)
- TODO: experiment with interacting with ai models in sandbox via [streamlit](github.com/craigsdennis/llm-trip-saver)
- TODO: experiment with vectorization replacement from Chroma to [Mongo](mongodb.com/developer/products/atlas/advanced-rag-langchain-mongodb/)
- TODO: add functionality (testing) for unit tests
- TODO: add functionality (security) to configure rate limiting for webhook at application level
- TODO: add functionality (security) to sanitize input to avoid injection attacks
- TODO: add functionality (security) to encrypt mongodb data at rest
- TODO: peruse and document [auth, logging, middleware, jinja, ai web pages, langchain]
