from twilio.rest import Client


def send_sms(twilio_client: Client, to: str, from_: str):

    message = twilio_client.messages.create(
        body="Coo Coo",
        to=to,
        from_=from_
    )

    print(f"message: {message.body}")
    print(f"sent from: {message.from_}")
    print(f"sent to: {message.to}")
