import praw
import prawcore
import sys
from app.cache.list import List
from praw.models.util import stream_generator


class Reddit:
    not_included_keywords = ''

    @staticmethod
    def is_comment_deleted(comment):
        if comment.author:
            return False
        return True

    @classmethod
    def get_not_deleted_comments(cls, submission):
        return [comment for comment in Reddit.get_comments(submission) if not cls.is_comment_deleted(comment)]

    @staticmethod
    def get_comments(submission):
        try:
            submission.comments.replace_more(limit=None)
            comments = submission.comments
        except prawcore.exceptions.NotFound:
            sys.exit(1)
        return comments

    @classmethod
    def get_regular_users_comments(cls, comments):
        return [comment for comment in cls.get_not_deleted_comments(comments) if
                not cls.is_user_special(cls.get_author(comment))]

    @staticmethod
    def get_author(comment):
        if comment.author:
            return comment.author.name
        return None

    @staticmethod
    def get_api(settings):
        api = praw.Reddit(client_id=settings.CLIENT_ID,
                          client_secret=settings.CLIENT_SECRET,
                          user_agent=settings.USER_AGENT,
                          username=settings.USERNAME,
                          password=settings.PASSWORD)
        return api

    def get_comment_karma(self, user):
        return self.api.redditor(str(user)).comment_karma

    def get_submission(self, url):
        return self.api.submission(url=url)

    def is_karma_valid(self, karma):
        return karma >= self.min_karma

    def has_required_keywords(self, title):
        keywords = self.required_keywords
        if not keywords:
            return True
        not_included_keywords = List.get_not_included_keywords(title, keywords)
        if not_included_keywords:
            self.not_included_keywords = not_included_keywords
            return False
        return True

    def get_regular_comments_stream(self):
        return self.subreddit.stream.comments()

    def get_regular_comment(self):
        for comment in self.get_regular_comments_stream():
            if Reddit.is_top_level_comment(comment) and self.has_required_keywords(comment.submission.title):
                yield comment

    def get_edited_comments_stream(self):
        return stream_generator(self.subreddit.mod.edited, pause_after=-1)

    def get_edited_comment(self):
        for comment in self.get_edited_comments_stream():
            if Reddit.is_top_level_comment(comment) and self.has_required_keywords(comment.submission.title):
                yield comment

    def get_usernames(self, usernames, prefixed=False):
        if prefixed:
            return [self.profile_prefix + winner for winner in usernames]
        return usernames

    @staticmethod
    def is_user_special(username):
        return username.find('_bot') != -1 or username == 'AutoModerator'

    def get_subreddit(self):
        return self.subreddit.display_name

    def is_entering(self, comment):
        return self.not_entering not in comment.body.lower()

    def get_redditor(self, username):
        return self.api.redditor(username)

    @staticmethod
    def is_top_level_comment(comment):
        return 't3' in comment.parent_id

    def send_message(self, username, subject, message):
        self.get_redditor(username).message(subject, message)

    def __init__(self, steam, settings):
        self.steam_api = steam
        self.min_karma = settings.MIN_KARMA
        self.api = self.get_api(settings)
        self.subreddit = self.api.subreddit(settings.SUBREDDIT)
        self.not_entering = settings.NOT_ENTERING
        self.required_keywords = settings.REQUIRED_KEYWORDS
