"""\nJeyaRamaDesk — Knowledge Base Models\nArticles, categories, and search for self-service support.\nDesigned for millions of records with proper indexing.\n"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


class KBCategory(models.Model):
    """Category for knowledge base articles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Category Name', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    description = models.TextField('Description', blank=True, default='')
    icon = models.CharField(
        'Icon CSS Class', max_length=50, blank=True, default='',
        help_text='Tailwind/Heroicon class name',
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
    )
    order = models.PositiveIntegerField('Display Order', default=0)
    is_active = models.BooleanField('Active', default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jrd_kb_categories'
        verbose_name = 'KB Category'
        verbose_name_plural = 'KB Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug'], name='idx_kbcat_slug'),
            models.Index(fields=['parent', 'is_active'], name='idx_kbcat_parent'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def article_count(self):
        return self.articles.filter(status='published').count()


class Article(models.Model):
    """Knowledge base article with rich content and versioning."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Title', max_length=255)
    slug = models.SlugField('Slug', max_length=255, unique=True)
    category = models.ForeignKey(
        KBCategory, on_delete=models.SET_NULL,
        null=True, related_name='articles',
    )
    body = models.TextField('Content', help_text='Supports HTML/Markdown')
    excerpt = models.CharField(
        'Excerpt', max_length=255, blank=True, default='',
        help_text='Short summary shown in search results',
    )
    status = models.CharField(
        'Status', max_length=15,
        choices=Status.choices, default=Status.DRAFT,
        db_index=True,
    )

    # ── SEO ───────────────────────────────────────────────
    meta_title = models.CharField('Meta Title', max_length=200, blank=True, default='')
    meta_description = models.CharField('Meta Description', max_length=255, blank=True, default='')

    # ── Engagement ────────────────────────────────────────
    views_count = models.PositiveIntegerField('Views', default=0)
    helpful_yes = models.PositiveIntegerField('Helpful: Yes', default=0)
    helpful_no = models.PositiveIntegerField('Helpful: No', default=0)

    # ── Visibility ────────────────────────────────────────
    is_internal = models.BooleanField(
        'Internal Only', default=False,
        help_text='Only visible to staff members',
    )
    is_featured = models.BooleanField('Featured', default=False)

    # ── Authoring ─────────────────────────────────────────
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='kb_articles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField('Published At', null=True, blank=True)

    class Meta:
        db_table = 'jrd_kb_articles'
        verbose_name = 'KB Article'
        verbose_name_plural = 'KB Articles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug'], name='idx_kbart_slug'),
            models.Index(fields=['status', 'is_internal'], name='idx_kbart_status'),
            models.Index(fields=['category', 'status'], name='idx_kbart_cat_status'),
            models.Index(fields=['-views_count'], name='idx_kbart_views'),
            models.Index(fields=['-published_at'], name='idx_kbart_published'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.body:
            self.excerpt = self.body[:200]
        super().save(*args, **kwargs)

    @property
    def helpfulness_rate(self):
        total = self.helpful_yes + self.helpful_no
        if total == 0:
            return 0
        return round((self.helpful_yes / total) * 100)

    @property
    def reading_time(self):
        """Estimated reading time in minutes."""
        word_count = len(self.body.split())
        return max(1, round(word_count / 200))


class ArticleAttachment(models.Model):
    """File attachments for KB articles."""

    id = models.BigAutoField(primary_key=True)
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField('File', upload_to='kb_attachments/%Y/%m/')
    filename = models.CharField('Original Filename', max_length=255)
    file_size = models.PositiveIntegerField('Size (bytes)', default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'jrd_kb_attachments'
        verbose_name = 'KB Attachment'
        verbose_name_plural = 'KB Attachments'

    def __str__(self):
        return self.filename
