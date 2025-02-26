from webdav3.client import Client
from os import path
import os
import configReader
import getpass
import click
import json
import shutil
import filecmp
import datetime

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
            "changes": [],
            "path": p,
        }
        json.dump(standard, f)
    click.echo("Created empty repo")

@cli.command()
def push():
    cwd = os.getcwd()
    config_path = path.join(cwd, ".kst-git/config.json")
    with open(config_path, "r") as f:
        repo_config = json.load(f)
    copy_dir = path.join(cwd, ".kst-git", "copy")
    repo_config_copy_path = path.join(copy_dir, ".kst-git")
    os.makedirs(repo_config_copy_path, exist_ok=True)
    shutil.copy2(config_path, path.join(repo_config_copy_path, "config.json"))
    click.echo("Uploading changes to server...")

    remote_path = repo_config["path"]

    def ensure_remote_directory(remote_dir):
        try:
            client.mkdir(remote_dir)
        except Exception as e:
            pass


    for root, _, files in os.walk(copy_dir):
        for file in files:
            local_file_path = path.join(root, file)
            relative_path = path.relpath(local_file_path, copy_dir)
            remote_file_path = path.join(remote_path, relative_path).replace("\\", "/")
            remote_dir_path = path.dirname(remote_file_path)
            try:
                # Ensure all parent directories exist on the server
                ensure_remote_directory(remote_dir_path)
                client.upload_file(remote_file_path, local_file_path)
                click.echo(f"Uploaded: {relative_path}")
            except Exception as e:
                click.echo(click.style(f"Error uploading {relative_path}: {e}", fg="red"))

    click.echo(click.style("Push complete.", fg="green"))

@cli.command()
def pull():
    cwd = os.getcwd()
    config_path = path.join(cwd, ".kst-git/config.json")
    with open(config_path, "r") as f:
        repo_config = json.load(f)
    remote_path = repo_config["path"]
    click.echo("Downloading latest version from server...")
    try:
        # Remove all local files except .kst-git directory
        for item in os.listdir(cwd):
            item_path = path.join(cwd, item)
            if item != ".kst-git":
                if path.isfile(item_path) or path.islink(item_path):
                    os.unlink(item_path)
                elif path.isdir(item_path):
                    shutil.rmtree(item_path)

        client.download_directory(remote_path, cwd)
        click.echo(click.style("Pull complete. Local repository updated to latest version.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Pull failed: {e}", fg="red"))

@cli.command()
def diff():
    cwd = os.getcwd()
    config_path = path.join(cwd, ".kst-git/config.json")
    with open(config_path, "r") as f:
        repo_config = json.load(f)
    if path.exists(path.join(cwd, ".kst-git", "copy")):
        shutil.rmtree(path.join(cwd, ".kst-git", "copy"), ignore_errors=True)
    # pull from server
    click.echo("Downloading server version...", color="yellow")
    client.download_directory(repo_config["path"], path.join(cwd, ".kst-git", "copy"))
    click.echo("Comparing local changes...")

    local_dir = cwd
    remote_copy_dir = path.join(cwd, ".kst-git", "copy")

    def generate_file_list(dir_path):
        file_list = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                relative_path = path.relpath(path.join(root, file), dir_path)
                if ".kst-git" not in relative_path and ".kst-git" != relative_path and relative_path != "":
                    file_list.append(relative_path)
        return file_list

    local_files = generate_file_list(local_dir)
    remote_files = generate_file_list(remote_copy_dir)

    added_files = list(set(local_files) - set(remote_files))
    deleted_files = list(set(remote_files) - set(local_files))
    modified_files = []
    common_files = set(local_files) & set(remote_files)

    for file in common_files:
        local_file_path = path.join(local_dir, file)
        remote_file_path = path.join(remote_copy_dir, file)
        if not filecmp.cmp(local_file_path, remote_file_path, shallow=False):
            modified_files.append(file)
    modified_files = list(modified_files)

    if added_files:
        click.echo(click.style("\nAdded files:", fg="green"))
        for file in added_files:
            click.echo(f"  + {file}")
            local_file_path = path.join(local_dir, file)
            remote_file_path = path.join(remote_copy_dir, file)
            os.makedirs(path.dirname(remote_file_path), exist_ok=True)
            shutil.copy2(local_file_path, remote_file_path)

    if deleted_files:
        click.echo(click.style("\nDeleted files:", fg="red"))
        for file in deleted_files:
            click.echo(f"  - {file}")
            remote_file_path = path.join(remote_copy_dir, file)
            os.remove(remote_file_path)

    if modified_files:
        click.echo(click.style("\nModified files:", fg="yellow"))
        for file in modified_files:
            click.echo(f"  ~ {file}")
            local_file_path = path.join(local_dir, file)
            remote_file_path = path.join(remote_copy_dir, file)
            shutil.copy2(local_file_path, remote_file_path)

    if not added_files and not deleted_files and not modified_files:
        click.echo(click.style("\nNo changes detected.", fg="cyan"))
    else:
        click.echo(click.style("\nChanges staged to copy.", fg="cyan"))
        commit_message = click.prompt("Enter commit message")
        now = datetime.datetime.now()
        commit_data = {
            "message": commit_message,
            "added": added_files,
            "deleted": deleted_files,
            "modified": modified_files,
            "timestamp": now.isoformat()
        }
        repo_config["changes"].append(commit_data)
        with open(config_path, "w") as f:
            json.dump(repo_config, f, indent=4)
        click.echo(click.style("\nCommit message and changes added to repo config.", fg="cyan"))

if __name__ == '__main__':
    cli()
