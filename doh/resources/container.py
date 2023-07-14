from docker.models.containers import Container
from doh.resources.resource import Resource


class ContainerResource(Resource):
    container: Container

    def __str__(self) -> str:
        return f"container: {self.container.name}"
