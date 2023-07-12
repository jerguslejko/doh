from re import I
from typing import Optional
from pydantic import BaseModel
import typer
import docker

import subprocess

from docker.models.images import Image


from pyfzf.pyfzf import FzfPrompt

from doh.resources.resource import Resource
from doh.resources.image import ImageResource
from doh.search import tags_similarity

app = typer.Typer(no_args_is_help=True)
client = docker.from_env()


def search_images(needle: str) -> list[ImageResource]:
    matching = []

    for image in client.images.list(all=True):
        for tag in image.attrs["RepoTags"]:
            if tags_similarity(needle, tag) > 50:
                matching.append(ImageResource(image=image))

    return matching


def get_images() -> list[ImageResource]:
    matching = []

    for image in client.images.list(all=True):
        matching.append(ImageResource(image=image))

    return matching


def get_all() -> list[Resource]:
    return get_images()


def search(needle: str) -> list[Resource]:
    matching = []

    for resource in get_all():
        if isinstance(resource, ImageResource):
            matching.extend(search_images(needle))

    return matching


class DohCommand(BaseModel):
    command: str
    tags: list


def fzf_prompt(
    options: list[Resource],
    label: str,
    height: int,
    tags: list[str] = [],
    print_command: bool = False,
):
    fzf = FzfPrompt()

    str_results = fzf.prompt(
        options,
        f"-i --header='{label}' --height={height+3} "
        # + ("--bind 'ctrl-r:become(echo doh-command {})'" if print_command else ""),
    )

    if not str_results:
        return None
    str_result = str_results[0]

    if print_command:
        if str_result.startswith("doh-command"):
            return DohCommand(command=str_result, tags=tags)

    return [m for m in options if str(m) == str_result][0]


def get_actions(resource: Resource):
    if isinstance(resource, ImageResource):
        return ["run", "dive"]

    return []


def execute_image_action(image: Image, action: str):
    match action:
        case "dive":
            subprocess.run(["dive", image.id])
        case "run":
            subprocess.run(["docker", "run", "-it", "--rm", image.id, "bash"])
        case _:
            raise NotImplementedError(f"Unknown action [{action}]")


def execute(resource: Resource, action: str):
    if isinstance(resource, ImageResource):
        execute_image_action(resource.image, action)
    else:
        raise NotImplementedError(f"Unknown resource [{resource}]")


@app.command()
def main(tag: Optional[str] = None, height: int = 5):
    matching = search(tag) if tag else get_all()
    resource = fzf_prompt(
        matching,
        label="select image",
        height=height,
        tags=[],
    )

    if not resource:
        typer.echo("no image selected. exiting.")
        return

    action = fzf_prompt(
        get_actions(resource),
        label="select action to run",
        height=height,
        tags=[("resource", resource)],
    )

    if not action:
        typer.echo("no action selected. exiting.")
        return

    if isinstance(action, DohCommand):
        print(action.command, action.tags)
        return

    execute(resource, action)


import distutils


def ensure_executable_exists(executable: str, suggestion: str = ""):
    if not distutils.spawn.find_executable(executable):
        typer.echo(
            f"error: could not find executable [{executable}]."
            + (f" suggestion: {suggestion}" if suggestion else "")
        )
        return True


if __name__ == "__main__":
    checks = [
        ensure_executable_exists("fzf", suggestion="brew install fzf"),
        ensure_executable_exists("dive", suggestion="brew install dive"),
    ]

    if not any(checks):
        app()
