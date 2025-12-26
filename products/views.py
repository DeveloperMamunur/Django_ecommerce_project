from django.shortcuts import render, get_object_or_404, redirect
from .models import Brand, ProductMainCategory, ProductSubCategory, Product, ProductImage, ProductVariant, InventoryLog, Wishlist
from django.utils.text import slugify
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from .forms import ProductImageForm, ProductVariantForm, InventoryLogForm
from django.contrib.auth.decorators import login_required
from core.permissions import CheckUserPermission

# Create your views here.
@login_required(login_url='accounts:login')
def brand_list_view(request):
    if not CheckUserPermission(request, 'can_view', 'products:brand_list'):
        return render(request, '403.html')
    search = request.GET.get('search', '').strip()
    brands = Brand.objects.all()

    if search:
        brands = brands.filter(name__icontains=search)

    if request.method == 'POST':
        brand_id = request.POST.get('brand_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if brand_id:
            brand = get_object_or_404(Brand, id=brand_id)
            brand.name = name
            brand.description = description
            if image:
                brand.image = image
            brand.save()
            messages.success(request, 'Brand updated successfully.')
        else:
            if name and image:
                Brand.objects.create(
                    name=name,
                    description=description,
                    image=image
                )
                messages.success(request, 'Brand created successfully.')

        return redirect('products:brand_list')

    context = {
        'brands': brands,
    }
    return render(request, 'products/brand/index.html', context)

@login_required(login_url='accounts:login')
def toggle_brand_status(request, brand_id):
    if not CheckUserPermission(request, 'can_update', 'products:toggle_brand_status'):
        return render(request, '403.html')
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_active = not brand.is_active
    brand.save()
    messages.success(request, f"Brand '{brand.name}' status updated.")
    return redirect('products:brand_list')

@login_required(login_url='accounts:login')
def delete_brand(request, brand_id):
    if not CheckUserPermission(request, 'can_delete', 'products:delete_brand'):
        return render(request, '403.html')
    brand = get_object_or_404(Brand, id=brand_id)
    brand.delete()
    messages.success(request, f"Brand '{brand.name}' deleted successfully.")
    return redirect('products:brand_list')

@login_required(login_url='accounts:login')
def product_main_category_view(request):
    if not CheckUserPermission(request, 'can_view', 'products:product_main_category'):
        return render(request, '403.html')
    search = request.GET.get('search', '').strip()
    categories = ProductMainCategory.objects.all()

    if search:
        categories = categories.filter(name__icontains=search)

    # CREATE or UPDATE
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')

        if category_id:
            category = get_object_or_404(ProductMainCategory, id=category_id)
            category.name = name
            category.description = description
            if image:
                category.image = image
            category.save()
            messages.success(request, 'Category updated successfully.')
        else:
            if name and image:
                ProductMainCategory.objects.create(
                    name=name,
                    description=description,
                    image=image
                )
                messages.success(request, 'Category created successfully.')

        return redirect('products:product_main_category')

    context = {
        'categories': categories
    }
    return render(request, 'products/category/index.html', context)

@login_required(login_url='accounts:login')
def toggle_category_status(request, category_id):
    if not CheckUserPermission(request, 'can_update', 'products:toggle_category_status'):
        return render(request, '403.html')
    category = get_object_or_404(ProductMainCategory, id=category_id)
    category.is_active = not category.is_active
    category.save()
    messages.success(request, f"Category '{category.name}' status updated.")
    return redirect('products:product_main_category')

@login_required(login_url='accounts:login')
def delete_category(request, category_id):
    if not CheckUserPermission(request, 'can_delete', 'products:delete_category'):
        return render(request, '403.html')
    category = get_object_or_404(ProductMainCategory, id=category_id)
    category.delete()
    messages.success(request, f"Category '{category.name}' deleted successfully.")
    return redirect('products:product_main_category')

@login_required(login_url='accounts:login')
def product_sub_category_view(request):
    if not CheckUserPermission(request, 'can_view', 'products:product_sub_category'):
        return render(request, '403.html')
    search = request.GET.get('search', '').strip()
    subcategories = ProductSubCategory.objects.select_related('main_category').all()
    main_categories = ProductMainCategory.objects.filter(is_active=True)

    if search:
        subcategories = subcategories.filter(name__icontains=search)

    # CREATE or UPDATE
    if request.method == 'POST':
        subcat_id = request.POST.get('subcategory_id')
        main_category_id = request.POST.get('main_category')
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if main_category_id:
            main_category = get_object_or_404(ProductMainCategory, id=main_category_id)
        else:
            main_category = None

        if subcat_id:
            subcategory = get_object_or_404(ProductSubCategory, id=subcat_id)
            subcategory.main_category = main_category
            subcategory.name = name
            if image:
                subcategory.image = image
            subcategory.save()
            messages.success(request, 'Subcategory updated successfully.')
        else:
            if main_category and name:
                ProductSubCategory.objects.create(
                    main_category=main_category,
                    name=name,
                    image=image
                )
                messages.success(request, 'Subcategory created successfully.')

        return redirect('products:product_sub_category')

    context = {
        'subcategories': subcategories,
        'main_categories': main_categories,
    }
    return render(request, 'products/sub_category/index.html', context)

@login_required(login_url='accounts:login')
def toggle_sub_category_status(request, sub_category_id):
    if not CheckUserPermission(request, 'can_update', 'products:toggle_sub_category_status'):
        return render(request, '403.html')
    subcategory = get_object_or_404(ProductSubCategory, id=sub_category_id)
    subcategory.is_active = not subcategory.is_active
    subcategory.save()
    messages.success(request, f"Subcategory '{subcategory.name}' status updated.")
    return redirect('products:product_sub_category')

@login_required(login_url='accounts:login')
def delete_sub_category(request, sub_category_id):
    if not CheckUserPermission(request, 'can_delete', 'products:delete_sub_category'):
        return render(request, '403.html')
    sub_category = get_object_or_404(ProductSubCategory, id=sub_category_id)
    sub_category.delete()
    messages.success(request, f"Subcategory '{sub_category.name}' deleted successfully.")
    return redirect('products:product_sub_category')


@login_required(login_url='accounts:login')
def product_list_view(request):
    if not CheckUserPermission(request, 'can_view', 'products:product_list'):
        return render(request, '403.html')
    
    # Handle Product Creation
    if request.method == 'POST':
        if not CheckUserPermission(request, 'can_create', 'products:product_list'):
            messages.error(request, 'Permission denied')
            return redirect('products:product_list')
        
        try:
            product = Product()
            product.name = request.POST.get('name')
            product.main_category_id = request.POST.get('main_category')
            product.sub_category_id = request.POST.get('sub_category') or None
            product.brand_id = request.POST.get('brand') or None
            product.price = request.POST.get('price') or 0
            product.sale_price = request.POST.get('sale_price') or None
            product.quantity = request.POST.get('quantity') or 0
            product.stock = request.POST.get('quantity') or 0
            product.description = request.POST.get('description', '')
            product.save()
            
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('products:product_list')
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
            return redirect('products:product_list')
    
    # Handle GET requests (list/filter)
    search = request.GET.get('search', '').strip()
    main_category_id = request.GET.get('main_category')
    sub_category_id = request.GET.get('sub_category')
    brand_id = request.GET.get('brand')

    products = Product.objects.all().order_by('-created_at')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(main_category__name__icontains=search) |
            Q(sub_category__name__icontains=search) |
            Q(brand__name__icontains=search) |
            Q(sku__icontains=search)
        )
    if main_category_id and main_category_id not in ['None', '', 'null']:
        products = products.filter(main_category_id=main_category_id)
    if sub_category_id and sub_category_id not in ['None', '', 'null']:
        products = products.filter(sub_category_id=sub_category_id)
    if brand_id and brand_id not in ['None', '', 'null']:
        products = products.filter(brand_id=brand_id)

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'main_categories': ProductMainCategory.objects.filter(is_active=True),
        'sub_categories': ProductSubCategory.objects.filter(is_active=True),
        'brands': Brand.objects.filter(is_active=True),
        'selected_main_category': main_category_id,
        'selected_sub_category': sub_category_id,
        'selected_brand': brand_id,
    }

    # If AJAX request, return only table HTML
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('products/product/_product_table.html', context, request=request)
        return JsonResponse({'html': html})
    
    return render(request, 'products/product/index.html', context)


@login_required(login_url='accounts:login')
def edit_product_view(request, product_id):
    if not CheckUserPermission(request, 'can_update', 'products:edit_product'):
        return render(request, '403.html')

    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.main_category_id = request.POST.get('main_category')
            product.sub_category_id = request.POST.get('sub_category') or None
            product.brand_id = request.POST.get('brand') or None
            product.price = request.POST.get('price') or 0
            product.sale_price = request.POST.get('sale_price') or None
            product.quantity = request.POST.get('quantity') or 0
            product.stock = request.POST.get('quantity') or 0
            product.description = request.POST.get('description', '')
            product.save()
            
            messages.success(request, f"Product '{product.name}' updated successfully!")
            refer_page = request.META.get('HTTP_REFERER')
            if refer_page:
                return HttpResponseRedirect(refer_page)
            return redirect('products:product_list')
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
            return redirect('products:product_list')

    context = {
        'product': product,
        'main_categories': ProductMainCategory.objects.filter(is_active=True),
        'sub_categories': ProductSubCategory.objects.filter(
            main_category=product.main_category, is_active=True
        ),
        'brands': Brand.objects.filter(is_active=True),
    }
    return render(request, 'products/product/edit_product_modal.html', context)


@login_required(login_url='accounts:login')
def product_detail_view(request, product_id):
    if not CheckUserPermission(request, 'can_view', 'products:product_detail'):
        return render(request, '403.html')
    
    product = get_object_or_404(Product, id=product_id)
    images = ProductImage.objects.filter(product=product, is_active=True)
    variants = ProductVariant.objects.filter(product=product)

    context = {
        'product': product,
        'images': images,
        'variants': variants,
    }

    # AJAX modal support
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('products/product/_product_detail_modal.html', context, request=request)
        return JsonResponse({'html': html})

    return render(request, 'products/product/detail.html', context)


@login_required(login_url='accounts:login')
def get_subcategories_ajax(request):
    if not CheckUserPermission(request, 'can_view', 'products:get_subcategories_ajax'):
        return render(request, '403.html')
    
    main_category_id = request.GET.get('main_category_id')
    subcategories = ProductSubCategory.objects.filter(
        main_category_id=main_category_id,
        is_active=True
    ).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

@login_required(login_url='accounts:login')
def delete_product(request, product_id):
    if not CheckUserPermission(request, 'can_delete', 'products:delete_product'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, f"Product '{product.name}' deleted successfully.")
    refer_page = request.META.get('HTTP_REFERER')
    if refer_page:
        return HttpResponseRedirect(refer_page)
    return redirect('products:product_list')

@login_required(login_url='accounts:login')
def toggle_product_status(request, product_id):
    if not CheckUserPermission(request, 'can_update', 'products:toggle_product_status'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f"Product '{product.name}' status updated.")
    refer_page = request.META.get('HTTP_REFERER')
    if refer_page:
        return HttpResponseRedirect(refer_page)
    return redirect('products:product_list')

@login_required(login_url='accounts:login')
def toggle_product_feature(request, product_id):
    if not CheckUserPermission(request, 'can_update', 'products:toggle_product_feature'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    product.is_featured = not product.is_featured
    product.save()
    messages.success(request, f"Product '{product.name}' feature status updated.")
    refer_page = request.META.get('HTTP_REFERER')
    if refer_page:
        return HttpResponseRedirect(refer_page)
    return redirect('products:product_list')

@login_required(login_url='accounts:login')
def product_image_list_view(request, product_id):
    if not CheckUserPermission(request, 'can_view', 'products:product_image_list'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    images = product.product_images.all()
    return render(request, 'products/product_images/product_image_list.html', {
        'product': product,
        'images': images,
    })

@login_required(login_url='accounts:login')
def product_image_upload_view(request, product_id):
    if not CheckUserPermission(request, 'can_edit', 'products:product_image_upload'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        files = request.FILES.getlist('image')

        if files:
            for i, f in enumerate(files):
                ProductImage.objects.create(
                    product=product,
                    image=f,
                    is_primary=(i == 0 and not ProductImage.objects.filter(product=product, is_primary=True).exists())
                )

            messages.success(request, "Images uploaded successfully.")
            return redirect('products:product_image_list', product_id=product.id)
        else:
            messages.warning(request, "Please select at least one image.")
    else:
        form = ProductImageForm()

    return render(request, 'products/product_images/product_image_upload.html', {
        'form': form,
        'product': product,
    })

@login_required(login_url='accounts:login')
def set_primary_image(request, image_id):
    if not CheckUserPermission(request, 'can_update', 'products:set_primary_image'):
        return render(request, '403.html')
    image = get_object_or_404(ProductImage, id=image_id)
    image.is_primary = True
    image.save()
    messages.success(request, "Primary image updated successfully.")
    return redirect('products:product_image_list', product_id=image.product.id)

# Delete Product Image
@login_required(login_url='accounts:login')
def delete_product_image(request, image_id):
    if not CheckUserPermission(request, 'can_delete', 'products:delete_product_image'):
        return render(request, '403.html')
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    image.delete()
    messages.success(request, "Image deleted successfully.")
    return redirect('products:product_image_list', product_id=product_id)


# List Variants
@login_required(login_url='accounts:login')
def variant_list_view(request, product_id):
    if not CheckUserPermission(request, 'can_view', 'products:variant_list'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all()
    return render(request, 'products/product/variant_list.html', {
        'product': product,
        'variants': variants
    })


# Create Variant
@login_required(login_url='accounts:login')
def variant_create_view(request, product_id):
    if not CheckUserPermission(request, 'can_create', 'products:variant_create'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.created_by = request.user
            variant.save()
            messages.success(request, "Variant created successfully.")
            return redirect('products:variant_list', product_id=product.id)
    else:
        form = ProductVariantForm()
    return render(request, 'products/product/variant_form.html', {'form': form, 'product': product})


# Update Variant
@login_required(login_url='accounts:login')
def variant_update_view(request, pk):
    if not CheckUserPermission(request, 'can_update', 'products:variant_update'):
        return render(request, '403.html')
    variant = get_object_or_404(ProductVariant, pk=pk)
    form = ProductVariantForm(request.POST or None, instance=variant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Variant updated successfully.")
        return redirect('products:variant_list', product_id=variant.product.id)
    return render(request, 'products/product/variant_form.html', {'form': form, 'product': variant.product})


# Delete Variant
@login_required(login_url='accounts:login')
def variant_delete_view(request, pk):
    if not CheckUserPermission(request, 'can_delete', 'products:variant_delete'):
        return render(request, '403.html')
    variant = get_object_or_404(ProductVariant, pk=pk)
    product_id = variant.product.id
    variant.delete()
    messages.success(request, "Variant deleted successfully.")
    return redirect('products:variant_list', product_id=product_id)

# List inventory logs
@login_required(login_url='accounts:login')
def inventory_log_list_view(request, product_id):
    if not CheckUserPermission(request, 'can_view', 'products:inventory_log_list'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    logs = product.inventory_logs.all().order_by('-created_at')
    return render(request, 'products/product/inventory_log_list.html', {
        'product': product,
        'logs': logs
    })


# Add inventory log
@login_required(login_url='accounts:login')
def inventory_log_create_view(request, product_id):
    if not CheckUserPermission(request, 'can_create', 'products:inventory_log_create'):
        return render(request, '403.html')
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = InventoryLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.product = product
            log.created_by = request.user
            log.save()
            messages.success(request, "Inventory updated successfully.")
            return redirect('products:inventory_log_list', product_id=product.id)
    else:
        form = InventoryLogForm()
    return render(request, 'products/product/inventory_log_form.html', {'form': form, 'product': product})


# Update inventory log
@login_required(login_url='accounts:login')
def inventory_log_update_view(request, pk):
    if not CheckUserPermission(request, 'can_update', 'products:inventory_log_update'):
        return render(request, '403.html')
    log = get_object_or_404(InventoryLog, pk=pk)
    form = InventoryLogForm(request.POST or None, instance=log)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Inventory updated successfully.")
        return redirect('products:inventory_log_list', product_id=log.product.id)
    return render(request, 'products/product/inventory_log_form.html', {'form': form, 'product': log.product})


# Delete inventory log
@login_required(login_url='accounts:login')
def inventory_log_delete_view(request, pk):
    if not CheckUserPermission(request, 'can_delete', 'products:inventory_log_delete'):
        return render(request, '403.html')
    log = get_object_or_404(InventoryLog, pk=pk)
    product_id = log.product.id
    log.delete()
    messages.success(request, "Inventory deleted successfully.")
    return redirect('products:inventory_log_list', product_id=product_id)

@login_required(login_url='accounts:login')
def toggle_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            return JsonResponse({
                "success": True,
                "action": "removed"
            })
        else:
            Wishlist.objects.create(
                user=request.user,
                product=product
            )
            return JsonResponse({
                "success": True,
                "action": "added"
            })

    return JsonResponse({"success": False}, status=400)

@login_required(login_url='accounts:login')
def wishlist_view(request):
    wishlist_qs = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related('product')
    )

    products = [w.product for w in wishlist_qs]

    user_wishlist_ids = set(w.product_id for w in wishlist_qs)

    return render(request, 'products/wishlist/index.html', {
        'products': products,
        'user_wishlist_ids': user_wishlist_ids,
    })

@login_required(login_url='accounts:login')
def frontend_wishlist_view(request):
    wishlist_qs = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related('product')
    )

    products = [w.product for w in wishlist_qs]

    user_wishlist_ids = set(w.product_id for w in wishlist_qs)

    return render(request, 'frontend/wishlist.html', {
        'products': products,
        'user_wishlist_ids': user_wishlist_ids,
    })