from treelib import Tree, Node
from sqlalchemy import create_engine, text
from dataclasses import dataclass

sql_engine = create_engine("sqlite+pysqlite:///:memory:")


def create_tables():
    with sql_engine.connect() as conn:
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS comments(
            id      INT PRIMARY KEY NOT NULL UNIQUE, 
            author  INT             NOT NULL, 
            content TEXT            NOT NULL, 
            replies INT             NOT NULL
            )"""
            )
        )
        conn.commit()
        conn.close()


@dataclass(frozen=True)
class Comment:
    id: int
    author: int
    content: str
    replies: int


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
        self.comment_tree.show()

    def save(self):
        for comment in self.comment_tree.all_nodes():
            with sql_engine.connect() as conn:
                comment_exists = conn.execute(
                    text("SELECT * FROM comments WHERE id = :id"),
                    {"id": comment.data.id},
                ).first()

                if comment_exists is None:
                    conn.execute(
                        text(
                            "INSERT INTO comments (id, author, content, replies) VALUES (:id, :author, :content, :replies)"
                        ),
                        vars(comment.data),
                    )
                    conn.commit()
                else:
                    conn.execute(
                        text(
                            "UPDATE comments SET id = :id, author = :author, content = :content, replies = :replies WHERE id = :id"
                        ),
                        vars(comment.data),
                    )
                    conn.commit()
                    pass
                pass
            pass
        pass

    pass


def load_tree():
    with sql_engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM comments ORDER BY id DESC"))
        print(res.all())


if __name__ == "__main__":
    create_tables()

    tree = CommentTree(Comment(1, 1, "Hello World", 1))

    tree.add_comment(comment=Comment(2, 1, "Hello World", 1))
    reply_node_test = tree.add_comment(comment=Comment(3, 1, "Hello World", 1))
    tree.add_comment(parent=reply_node_test, comment=Comment(4, 1, "Hello World", 3))

    tree.show_tree()

    tree.save()

    load_tree()
