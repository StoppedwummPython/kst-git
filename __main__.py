from webdav3.client import Client
from os import path
import os
import configReader
import getpass
import click
import json
import directory_diff
import shutil

os.makedirs(path.expanduser("~/.kst-git"), exist_ok=True)

config = configReader.ConfigReader()

if config.getConfig()["firstConfig"] == False:
    server = input("Server URL: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    config.updateConfig({"username": username, "password": password, "server": server, "firstConfig": True})
    config.saveConfig()

options = {
 'webdav_hostname': config.getConfig()["server"],
 'webdav_login': config.getConfig()["username"],
 'webdav_password': config.getConfig()["password"]
}
client = Client(options)

@click.group()
def cli():
    pass

@cli.command()
def init():
    cwd = os.getcwd()
    print(cwd)
    os.makedirs(path.join(cwd, ".kst-git"), exist_ok=True)
    p = input("Webdav Path: ")
    c = True if input("Create new Path (y/n): ") == "y" else False
    if c:
        project_name = input("Project Name: ")
        if not client.is_dir(path.join(p, project_name)):
            client.mkdir(path.join(p, project_name))
        p = path.join(p, project_name)
    with open(path.join(cwd, ".kst-git/config.json"), "w") as f:
        standard = {
            "changes" : [],
            "path" : p,
        }
        json.dump(standard, f)
    click.echo("Created empty repo")
@cli.command()
def push():
    cwd = os.getcwd()
    click.echo("Push command not implemented yet.")

@cli.command()
def diff():
    cwd = os.getcwd()
    with open(path.join(cwd, ".kst-git/config.json"), "r") as f:
        config = json.load(f)
    if path.exists(path.join(cwd, ".kst-git", "copy")):
        shutil.rmtree(path.join(cwd, ".kst-git", "copy"), ignore_errors=True)
    # pull from server
    click.echo("Downloading remote state...")
    client.download_directory(config["path"], path.join(cwd, ".kst-git", "copy"))
    click.echo("Comparing directories...")
    # Example using basic comparison:
    basic_diff = directory_diff.compare_directories_basic(cwd, path.join(cwd, ".kst-git", "copy"), [".kst-git", ".kst-git/copy"])
    if basic_diff:
        only_in_dir1, only_in_dir2, common = basic_diff
        if only_in_dir1:
            click.echo("\nFiles only in local directory (New files):")
            for item in only_in_dir1:
                click.echo(f"  + {item}")
        if only_in_dir2:
            click.echo("\nFiles only in remote directory (Potentially deleted locally or new remote files):")
            for item in only_in_dir2:
                click.echo(f"  - {item}")
        if common:
            click.echo("\nCommon files:")
            # For a basic diff, we are not checking content differences in common files.
            # If you want to check content differences, you would need a more detailed comparison.
            click.echo("  (Content comparison for common files is not implemented in this basic diff.)")
    else:
        click.echo("No differences found between local and remote directories.")
    click.echo("Diff complete.")


if __name__ == '__main__':
    cli()