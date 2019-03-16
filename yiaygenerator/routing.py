"""Basic Django Channels routing."""

from channels import routing
import django.urls

from . import consumers

application = routing.ProtocolTypeRouter({
	'websocket': routing.URLRouter([
		django.urls.path('request/', consumers.YiayConsumer),
	]),
})
