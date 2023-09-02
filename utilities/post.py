import datetime

import disnake

import config as config
from utilities import get_user


def site_log(user: str, action: str, content: str):
    usr = get_user.from_username(user)

    webhook = disnake.SyncWebhook.from_url(config.MOD_LOGS)
    emb = disnake.Embed(
        title=action,
        description=content,
        color=2829617,
        timestamp=datetime.datetime.now(),
    ).set_author(name=usr.username, icon_url=usr.profile_icon)
    webhook.send(embed=emb)


def error(title: str, message: str):
    webhook = disnake.SyncWebhook.from_url(config.MOD_LOGS)
    emb = disnake.Embed(
        title=title,
        description=message,
        color=disnake.Color.red(),
        timestamp=datetime.datetime.now(),
    )
    webhook.send(embed=emb)


def approval(
    approver: str, title: str, description: str, icon: str, author: int, url: str
):
    author_obj = get_user.from_id(author)

    webhook = disnake.SyncWebhook.from_url(config.PROJ_LOGS)
    emb = (
        disnake.Embed(
            title=title,
            description=description,
            color=2673743,
            timestamp=datetime.datetime.now(),
            url=f"https://datapackhub.net/project/{url}",
        )
        .set_author(
            name=f"Project approved by {approver}",
            icon_url="https://media.discordapp.net/attachments/1076912842269270037/1122514368979026021/utility12.png",
        )
        .set_footer(text=author_obj.username, icon_url=author_obj.profile_icon)
        .set_thumbnail(icon)
    )
    webhook.send(embed=emb)


def deletion(
    approver: str,
    title: str,
    description: str,
    icon: str,
    author: int,
    reason: str,
    url: str,
):
    author_obj = get_user.from_id(author)

    webhook = disnake.SyncWebhook.from_url(config.PROJ_LOGS)
    emb = (
        disnake.Embed(
            title=title,
            description=description,
            color=12597818,
            timestamp=datetime.datetime.now(),
            url=f"https://datapackhub.net/project/{url}",
        )
        .set_author(
            name=f"Project deleted by {approver}",
            icon_url="https://media.discordapp.net/attachments/1076912842269270037/1122514607572009040/utility8.png",
        )
        .set_footer(text=author_obj.username, icon_url=author_obj.profile_icon)
        .set_thumbnail(icon)
        .add_field("Reason", reason)
    )
    webhook.send(embed=emb)


def disabled(
    approver: str,
    title: str,
    description: str,
    icon: str,
    author: int,
    reason: str,
    url: str,
):
    author_obj = get_user.from_id(author)

    webhook = disnake.SyncWebhook.from_url(config.PROJ_LOGS)
    emb = (
        disnake.Embed(
            title=title,
            description=description,
            color=12597818,
            timestamp=datetime.datetime.now(),
            url=f"https://datapackhub.net/project/{url}",
        )
        .set_author(
            name=f"Project disabled by {approver}",
            icon_url="https://media.discordapp.net/attachments/1076912842269270037/1122514607572009040/utility8.png",
        )
        .set_footer(text=author_obj.username, icon_url=author_obj.profile_icon)
        .set_thumbnail(icon)
        .add_field("Reason", reason)
    )
    webhook.send(embed=emb)


def in_queue(title: str, description: str, icon: str, author: int, url: str):
    author_obj = get_user.from_id(author)

    webhook = disnake.SyncWebhook.from_url(config.PROJ_LOGS)
    emb = (
        disnake.Embed(
            title=title,
            description=description,
            color=12487214,
            timestamp=datetime.datetime.now(),
            url=f"https://datapackhub.net/project/{url}",
        )
        .set_author(
            name="Project awaiting approval",
            icon_url="https://media.discordapp.net/attachments/1076912842269270037/1122514541138432020/output-onlinepngtools.png",
        )
        .set_footer(text=author_obj.username, icon_url=author_obj.profile_icon)
        .set_thumbnail(icon)
    )
    webhook.send(embed=emb)
