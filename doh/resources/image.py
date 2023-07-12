from docker.models.images import Image
from doh.resources.resource import Resource


class ImageResource(Resource):
    image: Image

    def __str__(self) -> str:
        tags = ", ".join(self.image.tags)
        return f"image: {tags} ({self.image.short_id})"


def get_images(client) -> list[ImageResource]:
    matching = []

    for image in client.images.list(all=True):
        matching.append(ImageResource(image=image))

    return matching
