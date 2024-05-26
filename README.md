# Django Social Network Project

This project is a simple social network built with Django and Django Rest Framework (DRF). It includes functionalities for user signup, login, posting content, and liking posts. Additionally, it includes an automated bot that demonstrates these functionalities according to defined rules.

## Features

- User Signup
- User Login
- Create Posts
- Like Posts
- Automated Bot to simulate user activity

## Requirements

- Python 3.12
- Django
- Django Rest Framework
- drf-yasg (for API documentation)
- requests
- Faker

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-repository.git
   cd your-repository
   ```

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

1. **Work with API:**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

### API Documentation

API documentation is available using Swagger. To access it, navigate to:

````
```bash
http://127.0.0.1:8000/swagger/
```
````

Sure! Here is the updated section in Markdown format:

### Configuration

The configuration for the automated bot is stored in `config.json`. It includes the following fields:

**automated_bot**

- `number_of_users`: Number of users to be created by the bot
- `max_posts_per_user`: Maximum number of posts each user can create

**starnavi**

- `number_of_users`: Number of users to be created by the bot
- `max_posts_per_user`: Maximum number of posts each user can create
- `max_likes_per_user`: Maximum number of posts each user can like

### Sample `config.json`

```json
{
    "automated_bot": {
        "number_of_users": 5,
        "max_posts_per_user": 10
    },
    "starnavi": {
        "number_of_users": 5,
        "max_posts_per_user": 10,
        "max_likes_per_user": 20
    }
}
```

### Running the Automated Bot

The automated bot reads the configuration from `config.json` and performs the following activities:

- Signs up users
- Each user creates a random number of posts
- Randomly likes posts

To run the automated bot, use the following command:

```bash
python bot.py
```
