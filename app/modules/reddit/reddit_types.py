from pydantic import Field
from app.common.responses import OkResponse
from app.common.types import BaseEntity, PkBaseModel


class RedditConfigSet(PkBaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    subs: list[str]
    usernames: list[str]


class RedditConfig(OkResponse, BaseEntity):
    sets: list[RedditConfigSet]
    blocked_users: list[str]


class RedditConfigRequest(PkBaseModel):
    sets: list[RedditConfigSet] = Field(default_factory=list)
    blocked_users: list[str] = Field(default_factory=list)


class RedditSubsRequest(PkBaseModel):
    subs: list[str]
    limit: int = 10


class RedditUsersRequest(PkBaseModel):
    usernames: list[str]
    limit: int = 10


class RedditPost(PkBaseModel):
    url: str
    title: str
    author: str
    subreddit: str

    def __repr__(self):
        return f"Post(author={self.author}, title={self.title}, url={self.url}, subreddit={self.subreddit})"
