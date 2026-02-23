"""
JeyaRamaDesk — Ticket Views (Template-based)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from tickets.models import Ticket, TicketComment, Category, Tag
from tickets.services.ticket_service import TicketService
from accounts.models import User


@login_required
def ticket_list_view(request):
    """List tickets with filtering and search."""
    user = request.user

    # Base queryset based on role
    if user.is_customer:
        tickets = Ticket.objects.filter(customer=user)
    elif user.is_agent:
        tickets = Ticket.objects.filter(
            Q(assigned_agent=user) | Q(assigned_agent__isnull=True)
        )
    else:
        tickets = Ticket.objects.all()

    tickets = tickets.select_related('customer', 'assigned_agent', 'category')

    # Filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search = request.GET.get('search', '')
    assigned_filter = request.GET.get('assigned', '')

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    if category_filter:
        tickets = tickets.filter(category_id=category_filter)
    if assigned_filter == 'me':
        tickets = tickets.filter(assigned_agent=user)
    elif assigned_filter == 'unassigned':
        tickets = tickets.filter(assigned_agent__isnull=True)
    if search:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search)
            | Q(title__icontains=search)
            | Q(description__icontains=search)
        )

    paginator = Paginator(tickets, 25)
    page = request.GET.get('page')
    tickets_page = paginator.get_page(page)

    # Get stats for the current user context
    stats = TicketService.get_ticket_stats(user)

    context = {
        'tickets': tickets_page,
        'stats': stats,
        'categories': Category.objects.filter(is_active=True),
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search': search,
        'assigned_filter': assigned_filter,
    }
    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_create_view(request):
    """Create a new ticket."""
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'category': request.POST.get('category', ''),
            'priority': request.POST.get('priority', 'medium'),
            'due_date': request.POST.get('due_date') or None,
        }

        if not data['title'] or not data['description']:
            messages.error(request, 'Title and description are required.')
        else:
            files = request.FILES.getlist('attachments')
            ticket = TicketService.create_ticket(data, request.user, files)
            messages.success(request, f'Ticket {ticket.ticket_id} created successfully.')
            return redirect('tickets:detail', ticket_id=ticket.ticket_id)

    context = {
        'categories': Category.objects.filter(is_active=True),
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'tickets/ticket_create.html', context)


@login_required
def ticket_detail_view(request, ticket_id):
    """View ticket details with conversation thread."""
    ticket = get_object_or_404(
        Ticket.objects.select_related('customer', 'assigned_agent', 'category', 'sla_policy'),
        ticket_id=ticket_id,
    )

    # Access check
    if request.user.is_customer and ticket.customer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tickets:list')

    # Get comments (filter internal notes for customers)
    comments = ticket.comments.select_related('author').all()
    if request.user.is_customer:
        comments = comments.exclude(comment_type='internal_note')

    # Get activities
    activities = ticket.activities.select_related('actor').all()[:50]

    # Get attachments
    attachments = ticket.attachments.select_related('uploaded_by').all()

    # Available agents for assignment
    agents = User.objects.filter(
        role__in=['agent', 'manager', 'superadmin'],
        is_active=True,
    ).order_by('first_name') if request.user.is_staff_member else []

    context = {
        'ticket': ticket,
        'comments': comments,
        'activities': activities,
        'attachments': attachments,
        'agents': agents,
        'categories': Category.objects.filter(is_active=True),
        'tags': Tag.objects.all(),
        'status_choices': Ticket.Status.choices,
        'priority_choices': Ticket.Priority.choices,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update_view(request, ticket_id):
    """Update ticket properties (status, priority, assignment, etc.)."""
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    if request.user.is_customer and ticket.customer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tickets:list')

    if request.method == 'POST':
        data = {}

        # Staff can update all fields
        if request.user.is_staff_member:
            if 'status' in request.POST:
                data['status'] = request.POST['status']
            if 'priority' in request.POST:
                data['priority'] = request.POST['priority']
            if 'assigned_agent' in request.POST:
                data['assigned_agent'] = request.POST['assigned_agent']
            if 'category' in request.POST:
                data['category'] = request.POST['category']

        # Both can update title/description
        if 'title' in request.POST:
            data['title'] = request.POST['title'].strip()
        if 'description' in request.POST:
            data['description'] = request.POST['description'].strip()

        TicketService.update_ticket(ticket, data, request.user)
        messages.success(request, 'Ticket updated.')
        return redirect('tickets:detail', ticket_id=ticket.ticket_id)

    return redirect('tickets:detail', ticket_id=ticket.ticket_id)


@login_required
def ticket_comment_view(request, ticket_id):
    """Add a comment to a ticket."""
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    if request.user.is_customer and ticket.customer != request.user:
        messages.error(request, 'Access denied.')
        return redirect('tickets:list')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        comment_type = request.POST.get('comment_type', 'reply')

        # Customers can only add replies
        if request.user.is_customer:
            comment_type = 'reply'

        if not content:
            messages.error(request, 'Comment cannot be empty.')
        else:
            files = request.FILES.getlist('attachments')
            TicketService.add_comment(ticket, request.user, content, comment_type, files)
            messages.success(request, 'Comment added.')

    return redirect('tickets:detail', ticket_id=ticket.ticket_id)


@login_required
def ticket_assign_view(request, ticket_id):
    """Quick assign a ticket to self or another agent."""
    if not request.user.is_staff_member:
        messages.error(request, 'Permission denied.')
        return redirect('tickets:list')

    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '')
        if agent_id == 'self':
            agent = request.user
        elif agent_id:
            agent = get_object_or_404(User, pk=agent_id)
        else:
            agent = None

        TicketService.assign_ticket(ticket, agent, request.user)
        messages.success(request, f'Ticket assigned to {agent.full_name if agent else "unassigned"}.')

    return redirect('tickets:detail', ticket_id=ticket.ticket_id)
