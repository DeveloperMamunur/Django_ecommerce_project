from django.shortcuts import render, get_object_or_404
from products.models import Product, ProductMainCategory, ProductSubCategory, Wishlist
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

# Create your views here.
def home(request):
    search = request.GET.get('search', '').strip()
    main_category_id = request.GET.get('main_category')

    # Base queryset
    products_qs = Product.objects.filter(is_active=True)

    # Search filter
    if search:
        products_qs = products_qs.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(main_category__name__icontains=search) |
            Q(sub_category__name__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(sku__icontains=search)
        )

    # Filter by category if selected
    if main_category_id:
        products_qs = products_qs.filter(main_category_id=main_category_id)

    # Order by creation date
    products_qs = products_qs.order_by('-created_at')

    # Pagination for "All Products"
    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categories
    categories = (
        ProductMainCategory.objects.annotate(product_count=Count('products'))
        .filter(is_active=True, product_count__gt=0)
        .order_by('name')
    )
    for cat in categories:
        cat.top_products = [(p, p.display_badge) for p in cat.products.filter(is_active=True)[:8]]

    # Section-specific lists with badges
    new_arrivals = [(p, ("🆕 New Arrival", "bg-success")) for p in products_qs[:8]]
    featured_products = [(p, ("⭐ Featured", "bg-primary")) for p in Product.objects.filter(is_active=True, is_featured=True)[:8]]
    top_selling = [(p, ("🏆 Best Seller", "bg-warning text-dark")) for p in Product.objects.filter(is_active=True).order_by('-total_views')[:8]]
    all_products = [(p, p.display_badge) for p in page_obj.object_list]

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

    context = {
        'categories': categories,
        'new_arrivals': new_arrivals,
        'featured_products': featured_products,
        'top_selling': top_selling,
        'products': all_products,
        'page_obj': page_obj,
        'search': search,
        'main_category_id': main_category_id,
        'user_wishlist_ids': wishlist_ids
    }

    return render(request, 'frontend/home.html', context)

def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('main_category')

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(main_category__name__icontains=search_query) |
            Q(sub_category__name__icontains=search_query)
        )

    # Category filter
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(main_category_id__in=category_ids)

    # Price filter
    try:
        min_price = float(request.GET.get('min_price', 0))
        max_price = float(request.GET.get('max_price', 0))
        if min_price and max_price:
            products = products.filter(price__gte=min_price, price__lte=max_price)
    except ValueError:
        pass

    # Rating filter
    ratings = request.GET.getlist('rating')
    if ratings:
        try:
            products = products.filter(average_rating__gte=min(map(int, ratings)))
        except ValueError:
            pass

    # 🏷 Availability
    if request.GET.get('stock') == 'in-stock':
        products = products.filter(quantity__gt=0)
    if request.GET.get('sale') == 'on-sale':
        products = products.filter(sale_price__isnull=False)
    if request.GET.get('new') == 'new':
        cutoff = timezone.now() - timedelta(days=30)
        products = products.filter(created_at__gte=cutoff)

    # Sorting
    sort_option = request.GET.get('sort', 'featured')
    sort_map = {
        'price-low': 'price',
        'price-high': '-price',
        'rating': '-average_rating',
        'newest': '-created_at',
        'name': 'name',
        'featured': '-id',
    }
    products = products.order_by(sort_map.get(sort_option, '-id'))

    # Pagination
    per_page = int(request.GET.get('show', 12))
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Category counts
    categories = (
        ProductMainCategory.objects.annotate(product_count=Count('products'))
        .filter(is_active=True, product_count__gt=0)
        .order_by('name')
    )

    # Convert selected categories to integers for comparison
    selected_categories = [int(cat_id) for cat_id in category_ids if cat_id.isdigit()]
    selected_ratings = ratings

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

    context = {
        'products': page_obj,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_ratings': selected_ratings,
        'request': request,
        'user_wishlist_ids': wishlist_ids
    }
    return render(request, 'frontend/products.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    product.add_view(request)
    related_products = Product.objects.filter(
        main_category=product.main_category
    ).exclude(id=product.id)[:4]

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True)

    return render(request, 'frontend/product_details.html', {
        'product': product,
        'related_products': related_products,
        'user_wishlist_ids': wishlist_ids
    })