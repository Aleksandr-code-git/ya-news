import pytest
from datetime import datetime

from django.test.client import Client
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm

pytestmark = pytest.mark.django_db

HOME_URL = reverse('news:home')

today = datetime.today()

now = timezone.now()


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news(db):
    news = News.objects.create(
        title='Title',
        text='text'
    )
    return news


@pytest.fixture
def all_news(db):
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timezone.timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    return all_news


@pytest.fixture
def comments(author, news):
    for index in range(10):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timezone.timedelta(days=index)
        comment.save()
    return comment


def test_news_count(client, all_news):
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client, all_news):
    response = client.get(HOME_URL)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(client, comments, news):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert ('news' in response.context)
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.parametrize(
    'parametrized_client, form_expected, form_type',
    [
        ('client', False, None),
        ('author_client', True, CommentForm),
    ]
)
def test_comment_form_availability(
    request, parametrized_client, form_expected, form_type, news
):
    client = request.getfixturevalue(parametrized_client)
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert ('form' in response.context) == form_expected
    if form_expected:
        assert isinstance(response.context['form'], form_type)
