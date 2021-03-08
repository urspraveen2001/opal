from fastapi import APIRouter, Depends, WebSocket

from fastapi_websocket_pubsub import PubSubEndpoint
from opal.common.logger import get_logger
from opal.server.config import BROADCAST_URI
from opal.server.deps.authentication import logged_in

logger = get_logger("opal.server.pubsub")


class PubSub:
    """
    Warpper for the Pub/Sub channel used for both policy and data updates
    """

    def __init__(self,broadcaster_uri:str=BROADCAST_URI):
        """
        Args:
            broadcaster_uri (str, optional): Which server/medium should the PubSub use for broadcasting. Defaults to BROADCAST_URI.
            None means no broadcasting.
        """
        self.router = APIRouter()
        self.endpoint = PubSubEndpoint(broadcaster=broadcaster_uri)

        @self.router.websocket("/ws")
        async def websocket_rpc_endpoint(websocket: WebSocket, logged_in: bool = Depends(logged_in)):
            """
            this is the main websocket endpoint the sidecar uses to register on policy updates.
            as you can see, this endpoint is protected by an HTTP Authorization Bearer token.
            """
            if not logged_in:
                logger.info("Closing connection", remote_address=websocket.client, reason="Authentication failed")
                await websocket.close()
                return
            # Init PubSub main-loop with or without broadcasting
            if broadcaster_uri is not None:
                async with self.endpoint.broadcaster:
                    await self.endpoint.main_loop(websocket)
            else:
                await self.endpoint.main_loop(websocket)
