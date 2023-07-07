"""
** Comments API endpoints**
"""

import sqlite3

from flask import Blueprint

import config

from treelib import Tree

from usefuls.commons import Comment

comments = Blueprint("comments", __name__, url_prefix="/comments")


class CommentTree:
    """A comment tree representation"""

    comment_tree = Tree()
    root = None

    def __init__(self, root: Comment) -> None:
        self.root = root
        self.comment_tree.create_node(tag=root.id, identifier=root.id, data=root)
        pass

    def add_comment(self, parent: Comment = None, comment: Comment = None) -> Comment:
        """Adds a comment"""
        actual_parent = parent or self.root

        if comment is not None:
            self.comment_tree.create_node(
                tag=f"Comment {comment.id} (Replies to {comment.replies})",
                identifier=comment.id,
                parent=actual_parent.id,
                data=comment,
            )
            return comment
        pass

    def delete_comment(self, comment: Comment) -> None:
        """Removes a comment"""
        self.comment_tree.remove_node(comment.id)
        pass

    def show_tree(self) -> None:
        """Prints tree for debugging"""
        print(self.comment_tree.nodes)
        
    def to_json(self) -> str:
        for n in self.comment_tree.all_nodes():
            print(n.data)

def get_comment_chain(parent: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    parent = conn.execute(
        f"select rowid, message, author, replies, sent from comments where rowid = {parent}"
    ).fetchone()

    if not parent[3]:
        return {
            "id": parent[0],
            "message": parent[1],
            "author": parent[2],
            "sent": parent[4],
        }

    parent = {
        "id": parent[0],
        "message": parent[1],
        "author": parent[2],
        "sent": parent[4],
        "replies": [],
    }

    replies = str(parent[3]).split(" ")
    for i in replies:
        # something
        pass


@comments.route("/thread/<int:thread>")
def messages_from_thread(thread: int):
    conn = sqlite3.connect(config.DATA + "data.db")
    cmts = conn.execute(
        f"select rowid, message, author, replies, sent from comments where thread = {thread} and replied_to = null"
    ).fetchall()

    out = []
    for cmt in cmts:
        if cmt[3]:
            conn.execute(
                f"select rowid, message, author, replies, sent from comments where thread = {thread} and replied_to = null"
            )
        out.append({"id": cmt[0], "message": cmt[1], "author": cmt[2], "sent": cmt[4]})
