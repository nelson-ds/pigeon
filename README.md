# pigeon
Trip planning service which leverages AI recommendations as well as human traveling experience

## How does this service work?
- Onboarding to the service
    - You will be asked to share information about cities you have previoulsy visited or lived in (voluntary)
    - You will be made aware of service restrictions and rate limiting (if any)
    - All interactions with this service will be via text message
    - At any point, if you want to communicate with the service, start your message with the word `pigeon`
- Using AI for trip planning
    - Ask questions realted to planning a visit to a city and recive AI recommendations
    - Converse with the AI as you would with any other human
    - There will be limits on the interaction with the AI - these are determined by your past usage of the service
- Asking/Answering other users' travel questions
    - Utilizing help - for more specific questions that AI cannot answer, get connected up with another user (anonymously) who has visited the same place
    - Providing help - answer questsions other users might have (after being connected anonymously) about visiting the places you have been to
    - Every connection will be valid for a limited amount of time and have text count/size limits - these are determined by your past interactions
    - A user can only be connected with one other user at any given time -  there are limits on the total number of connections per week
    - A users can chose to end their connection with another user at any time
    - Once a connection has ended, both users will be asked to rate their conversation and this will help determine quality of future connections


## Development

### Dependencies
1. [Docker](https://www.docker.com/): needs to be installed
2. [Make](https://www.gnu.org/software/make/): needs to be installed
3. Secrets: should be placed in `pigeon/secrets/` (refer `pigeon/secrets_template/` for format)
4. Env: variables in `.env` should be updated basedon on user preference

### Working in development environment
1. Start the application: `make start`
    - App can be accessed via `http://localhost:8000/`
2. Stop the application: `make stop`


### Helper commands
- Access MongoDB cli: 
  ```
  docker exec -it mongodb bash
  eval $MONGOSH
  ```

- Twilio
  - Access Twilio cli: 
    ```
    make twilio-cli
    twilio phone-numbers:list
    ```

  - Simulate Twilio webhook to receive sms:
    ```
    curl -X POST -d "To=%2B1234567890" -d "From=%2B0987654321" -d "Body=Hello, pigeon" http://localhost:8000/sms
    ```

### Work in progress
- TODO: deploy app on server (pull fresh code & setup secrets for prod)
- TODO: recieve sms from Twilio in server from webhook (non 80 port)
- TODO: configure only Twilio IPs in Firewall rules (deny other IPs)
- TODO: configure rate limiting for webhook
- TODO: create flow for on-boarding user
- TODO: sanitize input to avoid injection attacks
- TODO: add unit tests
- TODO: encrypt mongodb data at rest
- TODO: peruse drive use-cases
