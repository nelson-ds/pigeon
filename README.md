# pigeon
Trip planning service utilizing AI recommendation as well as travelling expertise of other users

## How does this service work?
- Onboard to the service using text messages
    - You will be asked to share information about cities you have previoulsy visited or lived in (voluntary)
    - You will be made aware of service restrictions and rate limiting (if any)
- Using AI for trip planning
    - Ask questions realted to planning a visit to a city and recive AI recommendations
    - Converse with the AI as you would with any other human
    - There will be limits on the interaction with the AI - these are determined by your past usage of the service
- Using/Providing other users' travelling expertise
    - Using help - For more specific questions that AI cannot answer, get matched up with another user (anonymously) who has visited the same place
    - Providing help - Answer questsions other users might have (after being matched anonymously) about visiting the places you have been to
    - Every match will be valid for a limited amount of time and have text count/size limits - these are determined by your past interactions with others
    - Once a match expires, both users will be asked to rate the conversation and this will help determine quality of future matches


## Development

### Dependencies
1. [Docker](https://www.docker.com/) needs to be installed
2. [Make](https://www.gnu.org/software/make/) needs to be installed

### Working in development environment
1. Start the application: `make start`
    - App can be accessed via `http://localhost:5000/`
2. Stop the application: `make stop`
3. Access Twilio cli (optional): `make twilio-cli`
