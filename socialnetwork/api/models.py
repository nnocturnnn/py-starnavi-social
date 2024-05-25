from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    last_activity = models.DateTimeField(null=True, blank=True)


class Post(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
