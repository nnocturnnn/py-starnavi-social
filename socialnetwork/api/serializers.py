from django.utils import timezone
from rest_framework import serializers

from .models import ApiUser, Like, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiUser
        fields = ['public_id', 'username',
                  'password', 'last_login', 'last_request']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = ApiUser(
            username=validated_data['username'],
            last_login=timezone.now(),
            last_request=timezone.now()
        )
        # Use custom hash_password method
        user.hash_password(validated_data['password'])
        user.save()
        return user

    def validate_password(self, value):
        """
        Add validation for the password field if necessary.
        """
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one letter.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter.")
        return value


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'body', 'pub_date']
        read_only_fields = ['user', 'pub_date']


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'date', 'state']


class AnalyticsSerializer(serializers.Serializer):
    date = serializers.DateField(source='date__date')
    count = serializers.IntegerField()
