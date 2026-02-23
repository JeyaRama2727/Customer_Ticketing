"""
JeyaRamaDesk — Live Chat Views
Handles chat room creation, listing, and rendering.
"""

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ChatRoom, ChatMessage


@login_required
def chat_room_list(request):
    """List chat rooms for the current user (agent or customer)."""
    user = request.user
    if user.role in ('superadmin', 'manager', 'agent'):
        # Staff sees: their active rooms + unassigned waiting rooms
        rooms = ChatRoom.objects.filter(
            models_q_agent(user)
        ).select_related('customer', 'agent')
    else:
        rooms = ChatRoom.objects.filter(
            customer=user
        ).select_related('customer', 'agent')

    waiting_rooms = ChatRoom.objects.filter(status='waiting').select_related('customer') if user.role != 'customer' else None

    return render(request, 'livechat/room_list.html', {
        'rooms': rooms,
        'waiting_rooms': waiting_rooms,
    })


def models_q_agent(user):
    """Return Q filter for agent's rooms."""
    from django.db.models import Q
    return Q(agent=user) | Q(status='waiting')


@login_required
def chat_room(request, room_id):
    """Render a single chat room with message history."""
    room = get_object_or_404(ChatRoom, pk=room_id)

    # Security: only the customer, assigned agent, or staff can view
    user = request.user
    if user.role == 'customer' and room.customer != user:
        return redirect('livechat:room_list')

    # If agent opens a waiting room, assign themselves
    if room.status == 'waiting' and user.role in ('superadmin', 'manager', 'agent'):
        room.agent = user
        room.status = 'active'
        room.save(update_fields=['agent', 'status', 'updated_at'])
        # System message
        ChatMessage.objects.create(
            room=room,
            sender=None,
            content=f'{user.full_name or user.email} joined the chat.',
            message_type='system',
        )

    chat_messages = room.messages.select_related('sender').order_by('created_at')

    # Mark unread messages as read
    room.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    return render(request, 'livechat/chat_room.html', {
        'room': room,
        'chat_messages': chat_messages,
    })


@login_required
@require_POST
def start_chat(request):
    """Customer starts a new chat session."""
    subject = request.POST.get('subject', 'Live Chat').strip() or 'Live Chat'
    room = ChatRoom.objects.create(
        customer=request.user,
        subject=subject,
    )
    # System message
    ChatMessage.objects.create(
        room=room,
        sender=None,
        content=f'{request.user.full_name or request.user.email} started a chat.',
        message_type='system',
    )
    return redirect('livechat:room', room_id=room.pk)


@login_required
@require_POST
def close_chat(request, room_id):
    """Close a chat room."""
    room = get_object_or_404(ChatRoom, pk=room_id)
    room.status = 'closed'
    room.closed_at = timezone.now()
    room.save(update_fields=['status', 'closed_at', 'updated_at'])
    ChatMessage.objects.create(
        room=room,
        sender=None,
        content='Chat closed.',
        message_type='system',
    )
    return redirect('livechat:room_list')


@login_required
def unread_chat_count(request):
    """JSON endpoint for unread chat message count."""
    from django.db.models import Q
    user = request.user
    if user.role == 'customer':
        count = ChatMessage.objects.filter(
            room__customer=user, is_read=False
        ).exclude(sender=user).count()
    else:
        count = ChatMessage.objects.filter(
            Q(room__agent=user) | Q(room__status='waiting'),
            is_read=False,
        ).exclude(sender=user).count()
    return JsonResponse({'unread_count': count})


@login_required
@require_POST
def send_message(request, room_id):
    """
    HTTP fallback for sending a chat message.
    Used when WebSocket is unavailable (e.g. WSGI server).
    Returns the saved message as JSON.
    """
    room = get_object_or_404(ChatRoom, pk=room_id)

    # Security: only participants may send
    user = request.user
    if user.role == 'customer' and room.customer != user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    content = request.POST.get('message', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    msg = ChatMessage.objects.create(
        room=room,
        sender=user,
        content=content,
        message_type='text',
    )
    room.save(update_fields=['updated_at'])

    return JsonResponse({
        'id': str(msg.id),
        'content': msg.content,
        'message_type': msg.message_type,
        'sender_id': str(user.id),
        'sender_name': user.full_name or user.email,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def fetch_messages(request, room_id):
    """
    Poll endpoint: return messages created after the given timestamp.
    Query param: ?after=<ISO-timestamp>
    """
    room = get_object_or_404(ChatRoom, pk=room_id)
    user = request.user

    if user.role == 'customer' and room.customer != user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    after = request.GET.get('after')
    qs = room.messages.select_related('sender').order_by('created_at')
    if after:
        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(after)
        if dt:
            qs = qs.filter(created_at__gt=dt)

    # Mark incoming messages as read
    qs.filter(is_read=False).exclude(sender=user).update(is_read=True)

    msgs = []
    for m in qs[:50]:
        msgs.append({
            'id': str(m.id),
            'content': m.content,
            'message_type': m.message_type,
            'sender_id': str(m.sender_id) if m.sender_id else '',
            'sender_name': (m.sender.full_name or m.sender.email) if m.sender else 'System',
            'created_at': m.created_at.isoformat(),
        })

    return JsonResponse({'messages': msgs})
