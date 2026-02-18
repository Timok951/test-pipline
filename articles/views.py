from django.shortcuts import render, get_object_or_404
from shop.models import Good
from .models import Article


def article_list(request):
    articles = Article.objects.all()
    context = {
        "Articles": articles,
    }
    return render(request, "articles/article_list.html", context)


def article_detail(request, pk):
    article = get_object_or_404(Article, id=pk)
    related_goods = Good.objects.filter(article=article)
    context = {
        "Article": article,
        "Goods": related_goods,
    }
    return render(request, "articles/article_detail.html", context)
