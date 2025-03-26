from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import UserProfile, OrderData, MasterInventory
from django.http import JsonResponse
from django.db.models import Q
import os
from dotenv import load_dotenv
from Portal.utils.logger import general_logger as logger
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

load_dotenv()

def home(request):
    """Home view displaying orders and system status"""
    try:
        # Get search parameters
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort_by', '-processed_at')
        page_size = int(request.GET.get('page_size', '100'))
        page = int(request.GET.get('page', '1'))
        
        logger.info(f"Home page accessed. Search: '{search_query}', Sort: '{sort_by}', Page: {page}, Page Size: {page_size}")
        
        # Base queryset
        orders = OrderData.objects.all()
        
        # Apply search if provided
        if search_query:
            orders = orders.filter(
                Q(order_number__icontains=search_query) |
                Q(item__icontains=search_query)
            )
            logger.info(f"Applied search filter. Found {orders.count()} matching orders")
        
        # Apply sorting
        orders = orders.order_by(sort_by)
        
        # Calculate pagination
        total_records = orders.count()
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        total_pages = (total_records + page_size - 1) // page_size
        
        # Get paginated orders
        paginated_orders = orders[start_idx:end_idx]
        
        # Get counts
        pending_count = OrderData.objects.filter(sent_status=0).count()
        sent_count = OrderData.objects.filter(sent_status=1).count()
        error_count = OrderData.objects.filter(sent_status=99).count()
        
        logger.info(f"Order counts - Total: {total_records}, Page: {page}/{total_pages}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.debug("AJAX request received, returning JSON response")
            return JsonResponse({
                'orders': list(paginated_orders.values('id', 'order_number', 'transaction_type',
                                           'item', 'quantity', 'actual_qty', 'sent_status', 
                                           'processed_at', 'api_error', 'user')),
                'pagination': {
                    'page': page,
                    'total_pages': total_pages,
                    'total_records': total_records,
                    'page_size': page_size
                }
            })
        
        # Format environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '1433')
        api_host = os.getenv('API_HOST', '').rstrip('/')
        import_frequency = os.getenv('IMPORT_FREQUENCY', '60')
        api_frequency = os.getenv('API_FREQUENCY', '10')
        pick_check_frequency = os.getenv('PICK_CHECK_FREQUENCY', '10')
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = os.getenv('REDIS_PORT', '6379')
        
        logger.debug(f"System configuration loaded - DB: {db_host}:{db_port}, API: {api_host}")
        
        context = {
            'orders': list(paginated_orders.values('id', 'order_number', 'transaction_type',
                                   'item', 'quantity', 'actual_qty', 'sent_status', 
                                   'processed_at', 'api_error')),
            'pending_count': pending_count,
            'sent_count': sent_count,
            'error_count': error_count,
            'WATCH_FOLDER': os.getenv('WATCH_FOLDER'),
            'COMPLETED_FOLDER': os.getenv('COMPLETED_FOLDER'),
            'ERROR_FOLDER': os.getenv('ERROR_FOLDER'),
            'search_query': search_query,
            'DB_HOST': db_host,
            'DB_PORT': db_port,
            'API_HOST': api_host,
            'IMPORT_FREQUENCY': import_frequency,
            'API_FREQUENCY': api_frequency,
            'PICK_CHECK_FREQUENCY': pick_check_frequency,
            'REDIS_HOST': redis_host,
            'REDIS_PORT': redis_port,
            'page': page,
            'total_pages': total_pages,
            'total_records': total_records,
            'page_size': page_size,
            'page_size_options': [100, 200, 500, 1000]
        }
        return render(request, 'portal/home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while loading the page. Please try again.')
        return render(request, 'portal/home.html', {})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'portal/register.html', {'form': form})

@login_required
def profile(request):
    user_profile = UserProfile.objects.get_or_create(user=request.user)[0]
    return render(request, 'portal/profile.html', {'profile': user_profile})

@login_required
def reset_order_status(request, order_id):
    """Reset order status to pending (0) and clear API error"""
    try:
        logger.info(f"Attempting to reset order with ID: {order_id}")
        order = OrderData.objects.get(id=order_id)
        logger.info(f"Found order: {order.order_number} (ID: {order.id}) with status: {order.sent_status}")
        
        # Reset the order status to pending
        order.sent_status = 0
        order.api_error = None
        order.save()
        logger.info(f"Successfully reset order {order.order_number} (ID: {order.id}) to pending status")
        messages.success(request, f'Order {order.order_number} has been reset to pending status and will be processed in the next API run.')
        
    except OrderData.DoesNotExist:
        logger.error(f"Order with ID {order_id} not found in database")
        messages.error(request, f'Order with ID {order_id} was not found in the database. Please refresh the page and try again.')
        
    except Exception as e:
        logger.error(f"Error resetting order {order_id}: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred while resetting the order: {str(e)}')
        
    return redirect('portal:home')

def inventory(request):
    # Get query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 50))
    sort_by = request.GET.get('sort_by', '-import_timestamp')
    search_query = request.GET.get('search', '')

    # Base queryset
    queryset = MasterInventory.objects.all()

    # Apply search if provided
    if search_query:
        queryset = queryset.filter(
            Q(item__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Apply sorting
    if sort_by.startswith('-'):
        queryset = queryset.order_by(sort_by, '-import_timestamp')
    else:
        queryset = queryset.order_by(sort_by, 'import_timestamp')

    # Create paginator
    paginator = Paginator(queryset, page_size)
    
    # Ensure page number is valid
    try:
        page_obj = paginator.page(page)
    except:
        page = 1
        page_obj = paginator.page(page)

    # Calculate statistics
    total_records = queryset.count()
    new_count = queryset.filter(status=0).count()
    updated_count = queryset.filter(status=1).count()
    error_count = queryset.filter(status=2).count()

    # Get configuration from environment variables
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    watch_folder = os.getenv('WATCH_FOLDER', '')
    inventory_import_frequency = os.getenv('INVENTORY_IMPORT_FREQUENCY', '300')  # Default to 5 minutes

    context = {
        'inventory_items': page_obj,
        'page': page,
        'page_size': page_size,
        'page_size_options': [25, 50, 100, 250],
        'total_pages': paginator.num_pages,
        'total_records': total_records,
        'new_count': new_count,
        'updated_count': updated_count,
        'error_count': error_count,
        'sort_by': sort_by,
        'search_query': search_query,
        'DB_HOST': db_host,
        'DB_PORT': db_port,
        'WATCH_FOLDER': watch_folder,
        'INVENTORY_IMPORT_FREQUENCY': inventory_import_frequency,
    }

    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'inventory_items': [{
                'id': item.id,
                'item': item.item,
                'description': item.description,
                'uom': item.uom,
                'cus1': item.cus1,
                'cus2': item.cus2,
                'cus3': item.cus3,
                'status': item.status,
                'import_timestamp': item.import_timestamp.isoformat(),
            } for item in page_obj],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_records': total_records,
            }
        }
        return JsonResponse(data)

    return render(request, 'portal/inventory.html', context)

@require_POST
def reset_inventory_status(request, item_id):
    inventory_item = get_object_or_404(MasterInventory, id=item_id)
    inventory_item.status = 0
    inventory_item.save()
    return redirect('portal:inventory')
