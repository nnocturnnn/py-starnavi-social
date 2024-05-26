from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class ApiUser(AbstractUser):
    public_id = models.AutoField(unique=True, primary_key=True)
    last_login = models.DateTimeField(
        null=True, blank=True, default=timezone.now)
    last_request = models.DateTimeField(
        null=True, blank=True, default=timezone.now)
    password_hash = models.CharField(max_length=128)

    def hash_password(self, password):
        """
        Hashes the given password and stores it in the password_hash field.
        :param password: str
        """
        self.password_hash = make_password(password)

    def verify_password(self, password):
        """
        Verifies the given password against the stored password hash.
        :param password: str
        :return: bool
        """
        return check_password(password, self.password_hash)

    def __str__(self):
        return self.username


class Post(models.Model):
    user = models.ForeignKey(
        ApiUser, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=80)
    body = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Like(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(
        ApiUser, on_delete=models.CASCADE, related_name='likes')
    state = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    public_id = models.AutoField(unique=True, primary_key=True)

    def __repr__(self):
        return f'<Like {self.public_id}, {self.state}>'
