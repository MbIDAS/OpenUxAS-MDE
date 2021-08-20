
def check_message_send_receive(config, schema, external_services_schema, excludes):
    messages_sent = set()
    messages_received = set()

    configured_services = config["services"]

# The excluded messages are intended to exclude messages from the
# report, so -exclude_sent gives the messages to exclude from the
# "Messages sent with no subscriber" report. This means that we
# actually want to add the excluded sent messages from the
# messages received in order to exclde them. The reverse is true
# for the -exclude_received
    for send in excludes["sent"]:
        messages_received.add(send)

    for receive in excludes["received"]:
        messages_sent.add(receive)

    for service in configured_services:
        if service["type"] in schema["service"]:
            service_config = schema["service"][service["type"]]
            if "messages" in service_config:
                messages = service_config["messages"]
                for send in messages["sends"]:
                    messages_sent.add(send)
                for receive in messages["receives"]:
                    messages_received.add(receive)
        else:
            print("No schema available for service "+service["type"])

    if "service" in external_services_schema:
        for (_, service_config) in external_services_schema["service"].items():
            if "messages" in service_config:
                messages = service_config["messages"]
                for send in messages["sends"]:
                    messages_sent.add(send)
                for receive in messages["receives"]:
                    messages_received.add(receive)

    messages_sent_not_received = messages_sent.difference(messages_received)
    messages_received_not_sent = messages_received.difference(messages_sent)

    if len(messages_received_not_sent) > 0:
        print("Messages subscribed to with no sender:")
        for message in messages_received_not_sent:
            print(message)
        print()

    if len(messages_sent_not_received) > 0:
        print("Messages sent with no subscriber:")
        for message in messages_sent_not_received:
            print(message)
        print()
