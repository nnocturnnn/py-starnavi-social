import json
import random

import requests
from faker import Faker


def load_config(file_path):
    with open(file_path) as config_file:
        return json.load(config_file)


fake = Faker()

SIGNUP_URL = 'http://127.0.0.1:8000/api/users/signup/'
LOGIN_URL = 'http://127.0.0.1:8000/api/users/login/'
POST_URL = 'http://127.0.0.1:8000/api/posts/'
LIKE_URL_TEMPLATE = 'http://127.0.0.1:8000/api/posts/{post_id}/like/'


def signup_users(number_of_users):
    users = []
    for _ in range(number_of_users):
        username = fake.user_name()
        email = fake.email()
        password = fake.password()
        response = requests.post(
            SIGNUP_URL, data={'username': username, 'email': email, 'password': password})
        if response.status_code == 201:
            print(f"User {username} created successfully.")
            users.append({'username': username, 'password': password})
        else:
            print(f"Failed to create user {username}: {response.json()}")
    return users


def login_users(users):
    for user in users:
        response = requests.post(
            LOGIN_URL, data={'username': user['username'], 'password': user['password']})
        if response.status_code == 200:
            user['token'] = response.json()['access']
            print(f"User {user['username']} logged in successfully.")
        else:
            print(f"Failed to login user {user['username']}: {response.json()}")
    return users


def create_posts(users, max_posts_per_user):
    post_ids = []
    for user in users:
        token = user['token']
        headers = {'Authorization': f'Bearer {token}'}
        number_of_posts = random.randint(1, max_posts_per_user)
        for _ in range(number_of_posts):
            title = fake.sentence()
            body = fake.text()
            response = requests.post(POST_URL, headers=headers, data={
                                     'title': title, 'body': body})
            if response.status_code == 201:
                try:
                    post_id = response.json()['id']
                    post_ids.append(post_id)
                    print(f"Post {post_id} created by user {user['username']}.")
                except KeyError:
                    print(f"Unexpected response format: {response.json()}")
            else:
                print(f"Failed to create post by user {
                      user['username']}: {response.json()}")
    return post_ids


def like_posts(users, post_ids, max_likes_per_user):
    if not post_ids:
        print("No posts available to like.")
        return

    for user in users:
        token = user['token']
        headers = {'Authorization': f'Bearer {token}'}
        number_of_likes = random.randint(1, max_likes_per_user)
        for _ in range(number_of_likes):
            post_id = random.choice(post_ids)
            response = requests.post(LIKE_URL_TEMPLATE.format(
                post_id=post_id), headers=headers)
            if response.status_code == 200:
                print(f"Post {post_id} liked by user {user['username']}.")
            else:
                print(f"Failed to like post {post_id} by user {
                      user['username']}: {response.json()}")


def main():
    config = load_config('config.json')
    automated_bot_config = config['automated_bot']
    starnavi_config = config['starnavi']

    number_of_users = automated_bot_config['number_of_users']
    max_posts_per_user = automated_bot_config['max_posts_per_user']
    max_likes_per_user = starnavi_config['max_likes_per_user']

    users = signup_users(number_of_users)
    users = login_users(users)
    post_ids = create_posts(users, max_posts_per_user)
    like_posts(users, post_ids, max_likes_per_user)


if __name__ == '__main__':
    main()
