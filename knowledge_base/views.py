"""\nJeyaRamaDesk — Knowledge Base Views\nPublic and internal views for the knowledge base.\n"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.utils import timezone
from django.http import JsonResponse

from .models import KBCategory, Article


def kb_home_view(request):
    """Public knowledge base home page with categories and featured articles."""
    categories = KBCategory.objects.filter(
        is_active=True, parent__isnull=True
    ).prefetch_related('children')

    featured = Article.objects.filter(
        status='published', is_featured=True, is_internal=False,
    ).select_related('category', 'author')[:6]

    popular = Article.objects.filter(
        status='published', is_internal=False,
    ).order_by('-views_count')[:5]

    return render(request, 'knowledge_base/kb_home.html', {
        'categories': categories,
        'featured_articles': featured,
        'popular_articles': popular,
    })


def kb_category_view(request, slug):
    """View articles in a specific category."""
    category = get_object_or_404(KBCategory, slug=slug, is_active=True)

    articles = Article.objects.filter(
        category=category, status='published',
    )
    # Hide internal articles from customers
    if not request.user.is_authenticated or request.user.is_customer:
        articles = articles.filter(is_internal=False)

    articles = articles.select_related('author').order_by('-published_at')

    paginator = Paginator(articles, 12)
    page = request.GET.get('page')
    articles_page = paginator.get_page(page)

    return render(request, 'knowledge_base/kb_category.html', {
        'category': category,
        'articles': articles_page,
    })


def kb_article_view(request, slug):
    """View a single knowledge base article."""
    article = get_object_or_404(Article, slug=slug)

    # Access control: drafts only visible to staff
    if article.status == 'draft' and (
        not request.user.is_authenticated or request.user.is_customer
    ):
        from django.http import Http404
        raise Http404

    # Internal articles only visible to staff
    if article.is_internal and (
        not request.user.is_authenticated or request.user.is_customer
    ):
        from django.http import Http404
        raise Http404

    # Increment view count (using F() to avoid race conditions)
    Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)

    # Related articles in the same category
    related = Article.objects.filter(
        category=article.category,
        status='published',
    ).exclude(pk=article.pk)[:4]

    return render(request, 'knowledge_base/kb_article.html', {
        'article': article,
        'related_articles': related,
    })


def kb_article_feedback(request, slug):
    """Handle article helpfulness feedback (AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    article = get_object_or_404(Article, slug=slug)
    feedback = request.POST.get('feedback')

    if feedback == 'yes':
        Article.objects.filter(pk=article.pk).update(helpful_yes=F('helpful_yes') + 1)
    elif feedback == 'no':
        Article.objects.filter(pk=article.pk).update(helpful_no=F('helpful_no') + 1)

    return JsonResponse({'success': True})


def kb_search_view(request):
    """Search knowledge base articles."""
    query = request.GET.get('q', '').strip()
    results = Article.objects.none()

    if query:
        results = Article.objects.filter(
            Q(title__icontains=query) |
            Q(body__icontains=query) |
            Q(excerpt__icontains=query),
            status='published',
        )
        if not request.user.is_authenticated or request.user.is_customer:
            results = results.filter(is_internal=False)

        results = results.select_related('category', 'author').order_by('-views_count')

    paginator = Paginator(results, 10)
    page = request.GET.get('page')
    results_page = paginator.get_page(page)

    return render(request, 'knowledge_base/kb_search.html', {
        'query': query,
        'results': results_page,
    })


# ── Staff-only Article Management ─────────────────────────────

@login_required
def kb_manage_list_view(request):
    """Staff view: manage all KB articles."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('knowledge_base:home')

    articles = Article.objects.select_related(
        'category', 'author'
    ).order_by('-updated_at')

    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        articles = articles.filter(status=status_filter)

    category_filter = request.GET.get('category')
    if category_filter:
        articles = articles.filter(category__slug=category_filter)

    search = request.GET.get('q', '').strip()
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | Q(body__icontains=search)
        )

    paginator = Paginator(articles, 20)
    page = request.GET.get('page')
    articles_page = paginator.get_page(page)

    categories = KBCategory.objects.filter(is_active=True)

    return render(request, 'knowledge_base/kb_manage_list.html', {
        'articles': articles_page,
        'categories': categories,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search': search,
    })


@login_required
def kb_article_create_view(request):
    """Staff view: create a new KB article."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('knowledge_base:home')

    if request.method == 'POST':
        try:
            status = request.POST.get('status', 'draft')
            article = Article.objects.create(
                title=request.POST.get('title'),
                category_id=request.POST.get('category') or None,
                body=request.POST.get('body', ''),
                excerpt=request.POST.get('excerpt', ''),
                status=status,
                is_internal=request.POST.get('is_internal') == 'on',
                is_featured=request.POST.get('is_featured') == 'on',
                meta_title=request.POST.get('meta_title', ''),
                meta_description=request.POST.get('meta_description', ''),
                author=request.user,
                published_at=timezone.now() if status == 'published' else None,
            )
            messages.success(request, f'Article "{article.title}" created.')
            return redirect('knowledge_base:manage')
        except Exception as e:
            messages.error(request, f'Error creating article: {e}')

    categories = KBCategory.objects.filter(is_active=True)
    return render(request, 'knowledge_base/kb_article_form.html', {
        'categories': categories,
    })


@login_required
def kb_article_edit_view(request, slug):
    """Staff view: edit an existing KB article."""
    if request.user.is_customer:
        messages.error(request, 'Access denied.')
        return redirect('knowledge_base:home')

    article = get_object_or_404(Article, slug=slug)

    if request.method == 'POST':
        try:
            article.title = request.POST.get('title')
            article.category_id = request.POST.get('category') or None
            article.body = request.POST.get('body', '')
            article.excerpt = request.POST.get('excerpt', '')
            new_status = request.POST.get('status', 'draft')
            if new_status == 'published' and article.status != 'published':
                article.published_at = timezone.now()
            article.status = new_status
            article.is_internal = request.POST.get('is_internal') == 'on'
            article.is_featured = request.POST.get('is_featured') == 'on'
            article.meta_title = request.POST.get('meta_title', '')
            article.meta_description = request.POST.get('meta_description', '')
            article.save()
            messages.success(request, f'Article "{article.title}" updated.')
            return redirect('knowledge_base:manage')
        except Exception as e:
            messages.error(request, f'Error updating article: {e}')

    categories = KBCategory.objects.filter(is_active=True)
    return render(request, 'knowledge_base/kb_article_form.html', {
        'article': article,
        'categories': categories,
    })
