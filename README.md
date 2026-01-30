# [PigeonMsg](http://pigeonmsg.com)
Trip planning service which leverages AI recommendations as well as human traveling experience

## What does this service do?
- Helps with planning your trip to a new city by combining the ease of texting, the power of AI and the bond of human connection :)
- Have generic questions? Ask the helpful `AI` - Pidge who'll gladly scour the internet and help answer your question!
- Have a more specific question AIs struggle to answer? No problem - we'll connect you to another `human` who can help!

## How does this service work?
1. Text the service and start the on-boarding process:
    - All interactions with this service will be via text message
    - This service utilizes an AI under the hood so you can chat with it about trip planning as you would with any chat-bot
    - This service exposes admin commands via keyword `pidge` if you want to bypass the AI, for example `pidge help`
    - Since this is a free service, it has rate limits for users and is currently restricted to planning trips only to cities in California
    
2. Leveraging AI for trip planning
    - Ask questions realted to planning a visit to a city and recive help from our friendly AI - pidge!

3. Leveraging human help for trip planning
    - Providing help: 
        - During on-boarding, you will be asked if you want to help other users on this platform in planning trips to cities you are familiar with (voluntary)
        - Answer questsions other users might have (after being connected anonymously) about visiting the places you are familiar with
    - Requesting help: 
        - For specific questions that AI cannot answer, get connected up with another user (anonymously) who is familar with that place and get help from them
    - A user can only be connected with one other user at any time
    - A users can chose to end their connection with another user at any time

## Architecture
![Architecture](diagrams/architecture.png)

## Development

### Mandatory Dependencies
1. [Docker](https://www.docker.com/): needs to be installed for containerizing the app
2. Environment variables: 
    - shoule be placed in `.env` (refer `pigeon/templates/.env_template/` for format)
3. Secret variables: 
    - should be placed in `pigeon/secrets/` (refer `pigeon/templates/secrets_template/` for format)
4. Twilio configurations:
    - Access your Twilio console, navigate to 'Phone Numbers -> Manage -> Active Numbers'
    - In the option for 'A message comes in', add the url for this app
    - URL format: `https://APP_USERNAME_CONFIGURED_IN_SECRETS:APP_PASSWORD_CONFIGURED_IN_SECRETS@YOUR_DOMAIN_URL/sms` (example https://test:test@pigeonmsg.com/sms)
    - If you do not have a domain URL, you can also configure the IP address (exposed to the internet) of the remote server that the app is running on
5. Langchain configurations:
    - Place your custom knowledge documents (if any) in `/pigeon/app/backend/langchain/retrieval_docs/` - these will be used to provide additional context for the AI chatbot

### Optional Dependencies
1. [Make](https://www.gnu.org/software/make/): 
    - needs to be installed for running app specific cli commands
2. [Nginx](https://nginx.org/en/download.html): 
    - install this if you want to implement reverse proxy to serve app's web page / api
    - configurations should be placed in `/usr/local/etc/nginx/` (refer `pigeon/templates/nginx_template/` for format)
3. [Mingrammer](https://github.com/mingrammer/diagrams):
    - install this to update service diagrams

### Working in development environment
1. Build service: `docker-compose up --build -d`
2. Start the application: `make start`
3. Stop the application: `make stop`

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
        - Obtain twilio signature by following documentation in `app/backend/routes.py/validate_twilio_signature` (not needed for dev testing)
        - Send a curl request using token and twilio signature; example -
        ```
            curl -i -X POST \
            -H "Authorization: Basic dGVzdDp0ZXN0" \
            -H "X-Twilio-Signature: 5rVrhMTIJCCg0FOvzCbH809pehE=" \
            -d "To=%2B1234567890" -d "From=%2B0987654321" -d "Body=Hello, pigeon" \
            http://localhost:8001/sms
        ```

