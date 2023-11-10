from datetime import datetime
import random
from faker import Faker

from utilities import util
from utilities.commons import Project

import config


fake = Faker()


# Function to generate random project data
def generate_fake_project():
    return Project(
        type="datapack",
        id=random.randint(0, 9e9),
        author=fake.random_int(
            min=1, max=100
        ),  # Adjust max based on your actual author IDs
        title=fake.sentence(),
        description=fake.paragraph(),
        body=fake.text(),
        icon_url=fake.image_url(),
        slug=fake.url(),
        status="live",
        category=[random.choice(config.valid_tags) for _ in range(0, 3)],
        uploaded=int(datetime.timestamp(fake.date_time_this_decade())),
        updated=int(datetime.timestamp(fake.date_time_this_decade())),
        mod_message=fake.sentence() if random.choice([True, False]) else None,
        downloads=fake.random_int(min=0, max=1000),
        featured_until=int(datetime.timestamp(fake.future_datetime())),
        licence=fake.word(),
        dependencies=fake.word() if random.choice([True, False]) else None,
    )


def commit_fake_project(count: int = 50):
    for _ in range(0, count):
        project = generate_fake_project()
        util.commit_query(
            """insert into projects(
                type, 
                author, 
                title, 
                description, 
                body,
                category, 
                url, 
                status,
                uploaded,
                updated,
                icon) values (
                    :type, 
                    :id, 
                    :title, 
                    :desc, 
                    :body,
                    :categories, 
                    :url, 
                    :status,
                    :uploaded,
                    :updated,
                    :icon)""",
            type=project.type,
            id=project.author,
            title=project.title,
            desc=project.description,
            body=project.body,
            categories=",".join(project.category),
            url=project.slug,
            uploaded=project.uploaded,
            updated=project.updated,
            icon=project.icon_url,
            status=project.status
        )
