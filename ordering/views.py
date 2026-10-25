from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from .models import Supplier, Restaurant, Food, Agents, Customer, OrderDetails, Feedback, OrderItem
from .forms import (
    SupplierForm, RestaurantForm, FoodForm, AgentsForm,
    CustomerForm, OrderDetailsForm, FeedbackForm
)


# ==========================================
# 1. DASHBOARD VIEW
# ==========================================
def dashboard(request):
    """
    Renders the Dashboard with table record counts, aggregate statistics,
    and recent activity.
    """
    counts = {
        'restaurants': Restaurant.objects.count(),
        'food': Food.objects.count(),
        'suppliers': Supplier.objects.count(),
        'agents': Agents.objects.count(),
        'customers': Customer.objects.count(),
        'orders': OrderDetails.objects.count(),
        'feedback': Feedback.objects.count(),
    }

    # Aggregate DBMS calculations
    aggregates = {
        'total_revenue': OrderDetails.objects.aggregate(total=Sum('price'))['total'] or Decimal('0.00'),
        'total_items_sold': OrderDetails.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'avg_order_value': OrderDetails.objects.aggregate(avg=Avg('price'))['avg'] or Decimal('0.00'),
        'avg_restaurant_rating': Restaurant.objects.aggregate(avg=Avg('rating'))['avg'] or 0.0,
        'avg_customer_rating': Feedback.objects.aggregate(avg=Avg('rating'))['avg'] or 0.0,
    }

    recent_orders = OrderDetails.objects.select_related('customer', 'supplier').order_by('-order_id')[:5]
    recent_feedbacks = Feedback.objects.select_related('customer').order_by('-feedback_id')[:5]
    top_restaurants = Restaurant.objects.select_related('supplier').order_by('-rating')[:4]

    context = {
        'counts': counts,
        'aggregates': aggregates,
        'recent_orders': recent_orders,
        'recent_feedbacks': recent_feedbacks,
        'top_restaurants': top_restaurants,
    }
    return render(request, 'ordering/dashboard.html', context)


# ==========================================
# 2. RESTAURANTS CRUD
# ==========================================
def restaurant_list(request):
    search_query = request.GET.get('q', '').strip()
    restaurants = Restaurant.objects.select_related('supplier').annotate(
        food_count=Count('food_items')
    )
    if search_query:
        restaurants = restaurants.filter(restaurant_name__icontains=search_query)

    return render(request, 'ordering/restaurant_list.html', {
        'restaurants': restaurants,
        'search_query': search_query,
    })


def restaurant_create(request):
    if request.method == 'POST':
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save()
            messages.success(request, f"Restaurant '{restaurant.restaurant_name}' added successfully!")
            return redirect('restaurant_list')
    else:
        form = RestaurantForm()
    return render(request, 'ordering/restaurant_form.html', {'form': form, 'title': 'Add New Restaurant'})


def restaurant_update(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Restaurant '{restaurant.restaurant_name}' updated successfully!")
            return redirect('restaurant_list')
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'ordering/restaurant_form.html', {
        'form': form, 
        'restaurant': restaurant,
        'title': f'Edit Restaurant #{restaurant.restaurant_id}'
    })


def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        name = restaurant.restaurant_name
        restaurant.delete()
        messages.success(request, f"Restaurant '{name}' was deleted.")
        return redirect('restaurant_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Restaurant: {restaurant.restaurant_name}",
        'cancel_url': 'restaurant_list'
    })


# ==========================================
# 3. FOOD MENU CRUD
# ==========================================
def food_list(request):
    restaurant_id = request.GET.get('restaurant')
    search_query = request.GET.get('q', '').strip()

    foods = Food.objects.select_related('restaurant')
    if restaurant_id:
        foods = foods.filter(restaurant_id=restaurant_id)
    if search_query:
        foods = foods.filter(food_name__icontains=search_query)

    restaurants = Restaurant.objects.all()
    return render(request, 'ordering/food_list.html', {
        'foods': foods,
        'restaurants': restaurants,
        'selected_restaurant': int(restaurant_id) if restaurant_id and restaurant_id.isdigit() else None,
        'search_query': search_query,
    })


def food_create(request):
    if request.method == 'POST':
        form = FoodForm(request.POST)
        if form.is_valid():
            food = form.save()
            messages.success(request, f"Food item '{food.food_name}' added to menu!")
            return redirect('food_list')
    else:
        form = FoodForm()
    return render(request, 'ordering/food_form.html', {'form': form, 'title': 'Add New Food Item'})


def food_update(request, pk):
    food = get_object_or_404(Food, pk=pk)
    if request.method == 'POST':
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            messages.success(request, f"Food item '{food.food_name}' updated successfully!")
            return redirect('food_list')
    else:
        form = FoodForm(instance=food)
    return render(request, 'ordering/food_form.html', {
        'form': form,
        'food': food,
        'title': f'Edit Food Item #{food.food_id}'
    })


def food_delete(request, pk):
    food = get_object_or_404(Food, pk=pk)
    if request.method == 'POST':
        name = food.food_name
        food.delete()
        messages.success(request, f"Food item '{name}' was removed from the menu.")
        return redirect('food_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Food Item: {food.food_name} (₹{food.food_price})",
        'cancel_url': 'food_list'
    })


# ==========================================
# 4. SUPPLIERS CRUD
# ==========================================
def supplier_list(request):
    suppliers = Supplier.objects.annotate(
        restaurant_count=Count('restaurants', distinct=True),
        agent_count=Count('agents', distinct=True)
    )
    return render(request, 'ordering/supplier_list.html', {'suppliers': suppliers})


def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' registered successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'ordering/supplier_form.html', {'form': form, 'title': 'Add New Supplier'})


def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' updated successfully!")
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'ordering/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'title': f'Edit Supplier #{supplier.supplier_id}'
    })


def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        name = supplier.supplier_name
        supplier.delete()
        messages.success(request, f"Supplier '{name}' was deleted.")
        return redirect('supplier_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Supplier: {supplier.supplier_name}",
        'cancel_url': 'supplier_list'
    })


# ==========================================
# 5. AGENTS CRUD
# ==========================================
def agent_list(request):
    agents = Agents.objects.select_related('supplier')
    return render(request, 'ordering/agent_list.html', {'agents': agents})


def agent_create(request):
    if request.method == 'POST':
        form = AgentsForm(request.POST)
        if form.is_valid():
            agent = form.save()
            messages.success(request, f"Agent '{agent.agent_name}' added successfully!")
            return redirect('agent_list')
    else:
        form = AgentsForm()
    return render(request, 'ordering/agent_form.html', {'form': form, 'title': 'Add New Delivery Agent'})


def agent_update(request, pk):
    agent = get_object_or_404(Agents, pk=pk)
    if request.method == 'POST':
        form = AgentsForm(request.POST, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, f"Agent '{agent.agent_name}' updated successfully!")
            return redirect('agent_list')
    else:
        form = AgentsForm(instance=agent)
    return render(request, 'ordering/agent_form.html', {
        'form': form,
        'agent': agent,
        'title': f'Edit Agent #{agent.agent_id}'
    })


def agent_delete(request, pk):
    agent = get_object_or_404(Agents, pk=pk)
    if request.method == 'POST':
        name = agent.agent_name
        agent.delete()
        messages.success(request, f"Agent '{name}' was deleted.")
        return redirect('agent_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Agent: {agent.agent_name}",
        'cancel_url': 'agent_list'
    })


# ==========================================
# 6. CUSTOMERS CRUD
# ==========================================
def customer_list(request):
    customers = Customer.objects.annotate(
        order_count=Count('orders', distinct=True),
        feedback_count=Count('feedbacks', distinct=True)
    )
    return render(request, 'ordering/customer_list.html', {'customers': customers})


def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.cust_name}' registered successfully!")
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'ordering/customer_form.html', {'form': form, 'title': 'Add New Customer'})


def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer '{customer.cust_name}' updated successfully!")
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'ordering/customer_form.html', {
        'form': form,
        'customer': customer,
        'title': f'Edit Customer #{customer.cust_id}'
    })


def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = customer.cust_name
        customer.delete()
        messages.success(request, f"Customer '{name}' was deleted.")
        return redirect('customer_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Customer: {customer.cust_name}",
        'cancel_url': 'customer_list'
    })


# ==========================================
# 7. ORDERS CRUD & ORDER_ITEMS
# ==========================================
def order_list(request):
    orders = OrderDetails.objects.select_related('customer', 'supplier').prefetch_related('items__food')
    return render(request, 'ordering/order_list.html', {'orders': orders})


def order_detail(request, pk):
    order = get_object_or_404(OrderDetails.objects.select_related('customer', 'supplier').prefetch_related('items__food'), pk=pk)
    return render(request, 'ordering/order_detail.html', {'order': order})


def order_create(request):
    """
    Creates an order in ORDER_DETAILS.
    Also handles optional food items selection to populate ORDER_ITEMS table.
    """
    if request.method == 'POST':
        form = OrderDetailsForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save()

                # Process optional selected food items for ORDER_ITEMS table
                food_ids = request.POST.getlist('item_food_id[]')
                quantities = request.POST.getlist('item_quantity[]')
                prices = request.POST.getlist('item_price[]')

                if food_ids and len(food_ids) > 0:
                    for fid, q, p in zip(food_ids, quantities, prices):
                        if fid and q and p:
                            try:
                                food_obj = Food.objects.get(pk=int(fid))
                                OrderItem.objects.create(
                                    order=order,
                                    food=food_obj,
                                    quantity=int(q),
                                    item_price=Decimal(p)
                                )
                            except (Food.DoesNotExist, ValueError):
                                pass

            messages.success(request, f"Order #{order.order_id} created successfully!")
            return redirect('order_detail', pk=order.order_id)
    else:
        initial_data = {'order_date': timezone.now().date(), 'quantity': 1, 'price': Decimal('0.00')}
        form = OrderDetailsForm(initial=initial_data)

    available_foods = Food.objects.select_related('restaurant').all()
    return render(request, 'ordering/order_form.html', {
        'form': form,
        'available_foods': available_foods,
        'title': 'Place New Order'
    })


def order_update(request, pk):
    order = get_object_or_404(OrderDetails, pk=pk)
    if request.method == 'POST':
        form = OrderDetailsForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{order.order_id} updated successfully!")
            return redirect('order_list')
    else:
        form = OrderDetailsForm(instance=order)
    return render(request, 'ordering/order_edit_form.html', {
        'form': form,
        'order': order,
        'title': f'Edit Order #{order.order_id}'
    })


def order_delete(request, pk):
    order = get_object_or_404(OrderDetails, pk=pk)
    if request.method == 'POST':
        oid = order.order_id
        order.delete()
        messages.success(request, f"Order #{oid} was deleted.")
        return redirect('order_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Order #{order.order_id} for {order.customer.cust_name} (₹{order.price})",
        'cancel_url': 'order_list'
    })


# ==========================================
# 8. FEEDBACK CRUD
# ==========================================
def feedback_list(request):
    feedbacks = Feedback.objects.select_related('customer')
    return render(request, 'ordering/feedback_list.html', {'feedbacks': feedbacks})


def feedback_create(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save()
            messages.success(request, f"Feedback #{fb.feedback_id} recorded successfully!")
            return redirect('feedback_list')
    else:
        form = FeedbackForm(initial={'feedback_date': timezone.now().date(), 'rating': 5})
    return render(request, 'ordering/feedback_form.html', {'form': form, 'title': 'Submit Customer Feedback'})


def feedback_update(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            messages.success(request, f"Feedback #{feedback.feedback_id} updated successfully!")
            return redirect('feedback_list')
    else:
        form = FeedbackForm(instance=feedback)
    return render(request, 'ordering/feedback_form.html', {
        'form': form,
        'feedback': feedback,
        'title': f'Edit Feedback #{feedback.feedback_id}'
    })


def feedback_delete(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if request.method == 'POST':
        fid = feedback.feedback_id
        feedback.delete()
        messages.success(request, f"Feedback #{fid} was deleted.")
        return redirect('feedback_list')
    return render(request, 'ordering/confirm_delete.html', {
        'object_name': f"Feedback #{feedback.feedback_id} from {feedback.customer.cust_name}",
        'cancel_url': 'feedback_list'
    })


# ==========================================
# 9. DBMS QUERIES DEMO VIEW (For College Viva)
# ==========================================
def dbms_queries_demo(request):
    """
    Runs demonstration SQL queries live on MySQL and displays results
    to help during college project evaluations and presentations.
    """
    demo_queries = [
        {
            'title': '1. Simple SELECT Query with WHERE Filter',
            'description': 'Retrieve restaurants having rating greater than or equal to 4.5',
            'sql': "SELECT restaurant_id, restaurant_name, restaurant_ph_no, rating FROM restaurant WHERE rating >= 4.5 ORDER BY rating DESC;"
        },
        {
            'title': '2. INNER JOIN: Food Items with their Restaurant Names and Suppliers',
            'description': 'Demonstrates joining FOOD, RESTAURANT, and SUPPLIER tables.',
            'sql': """SELECT f.food_name, f.food_price, f.food_rating, r.restaurant_name, s.supplier_name 
FROM food f
JOIN restaurant r ON f.restaurant_id = r.restaurant_id
JOIN supplier s ON r.supplier_id = s.supplier_id
LIMIT 6;"""
        },
        {
            'title': '3. JOIN & Aggregates: Orders with Customer Name, Supplier, and Total Price',
            'description': 'Demonstrates relational joins between ORDER_DETAILS, CUSTOMER, and SUPPLIER.',
            'sql': """SELECT o.order_id, c.cust_name, s.supplier_name, o.order_date, o.quantity, o.price
FROM order_details o
JOIN customer c ON o.cust_id = c.cust_id
JOIN supplier s ON o.supplier_id = s.supplier_id
ORDER BY o.order_id DESC;"""
        },
        {
            'title': '4. Aggregate Functions: COUNT, SUM, AVG across Orders',
            'description': 'Computes total orders count, total revenue, average order value, and total items sold.',
            'sql': """SELECT 
    COUNT(order_id) AS total_orders, 
    SUM(price) AS total_revenue, 
    AVG(price) AS average_order_value,
    SUM(quantity) AS total_items_sold
FROM order_details;"""
        },
        {
            'title': '5. GROUP BY and HAVING: Restaurant-wise Food Count & Average Food Price',
            'description': 'Groups food items by restaurant and filters groups using HAVING count >= 1.',
            'sql': """SELECT r.restaurant_name, COUNT(f.food_id) AS total_items, ROUND(AVG(f.food_price), 2) AS avg_item_price
FROM restaurant r
LEFT JOIN food f ON r.restaurant_id = f.restaurant_id
GROUP BY r.restaurant_id, r.restaurant_name
HAVING total_items >= 1;"""
        },
        {
            'title': '6. Customer Feedback with Ratings (INNER JOIN)',
            'description': 'Retrieves customer names with their feedback rating and review messages.',
            'sql': """SELECT fb.feedback_id, c.cust_name, fb.rating, fb.message, fb.feedback_date
FROM feedback fb
JOIN customer c ON fb.cust_id = c.cust_id
ORDER BY fb.rating DESC;"""
        }
    ]

    results = []
    with connection.cursor() as cursor:
        for q in demo_queries:
            try:
                cursor.execute(q['sql'])
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                results.append({
                    'title': q['title'],
                    'description': q['description'],
                    'sql': q['sql'],
                    'columns': columns,
                    'rows': rows,
                    'count': len(rows),
                    'error': None
                })
            except Exception as e:
                results.append({
                    'title': q['title'],
                    'description': q['description'],
                    'sql': q['sql'],
                    'columns': [],
                    'rows': [],
                    'count': 0,
                    'error': str(e)
                })

    return render(request, 'ordering/dbms_queries.html', {'results': results})



# ==========================================
# 10. STORED PROCEDURE DEMONSTRATION
# ==========================================
def customer_orders_procedure(request):
    orders = []
    customer_id = None
    error = None

    if request.method == 'POST':
        customer_id = request.POST.get('customer_id', '').strip()

        if not customer_id.isdigit():
            error = "Please enter a valid customer ID."
        else:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "CALL restaurant_food_ordering.GetCustomerOrders(%s)",
                        [int(customer_id)]
                    )
                    columns = [column[0] for column in cursor.description]
                    orders = [
                        dict(zip(columns, row))
                        for row in cursor.fetchall()
                    ]

                    # Consume any remaining result sets before reusing
                    # the MySQL connection.
                    while cursor.nextset():
                        pass

            except Exception as e:
                error = str(e)

    return render(request, 'ordering/customer_orders_procedure.html', {
        'orders': orders,
        'customer_id': customer_id,
        'error': error,
    })


def cursor_revenue_procedure(request):
    total_revenue = None
    error = None

    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL restaurant_food_ordering.CalculateRevenueUsingCursor()"
                )

                row = cursor.fetchone()
                if row:
                    total_revenue = row[0]

                # Consume any remaining result sets.
                while cursor.nextset():
                    pass

        except Exception as e:
            error = str(e)

    return render(request, 'ordering/cursor_revenue_procedure.html', {
        'total_revenue': total_revenue,
        'error': error,
    })


def trigger_audit_demo(request):
    audit_records = []
    error = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT audit_id, order_id, action_type, action_time
                FROM order_audit
                ORDER BY audit_id DESC
            """)

            columns = [column[0] for column in cursor.description]
            audit_records = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    except Exception as e:
        error = str(e)

    return render(request, 'ordering/trigger_audit_demo.html', {
        'audit_records': audit_records,
        'error': error,
    })


