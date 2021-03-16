<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<UxAS FormatVersion="1.0" EntityID="{{element.mainEntityID}}" EntityType="{{element.mainEntityType}}">

{% for bridge in element.bridges %}
<Bridge Ty0pe="{{bridge.type}}"{% for bridgeOpt in bridge.options
    %} {{bridgeOpt.key}}="{{bridgeOpt.val}}"{% endfor %}>
    {% for subsc in bridge.subscriptions %}
    <SubscribeToMessage MessageType="{{subsc.messageType}}" />
    {% endfor %}
</Bridge>
{% endfor %}

{% for service in element.services %}
<Service Type="{{service.type}}"{% for serviceOpt in service.options
    %} {{serviceOpt.key}}="{{serviceOpt.val}}"{% endfor %}>

</Service>
</UxAS>