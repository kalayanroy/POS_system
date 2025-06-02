from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ProductForm, PurchaseForm, SaleForm, get_products as get_products_for_form # Add SaleForm and get_products
from app.models import User, Product, Purchase, Sale # Add Sale
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from sqlalchemy import func # For SUM operations

@app.route('/')
@app.route('/index')
@login_required # Protect this route
def index():
    # Now current_user is available
    return render_template('base.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data,
                          description=form.description.data,
                          purchase_price=form.purchase_price.data,
                          sale_price=form.sale_price.data,
                          quantity=form.quantity.data)
        db.session.add(product)
        db.session.commit()
        flash('Product "{}" has been added successfully!'.format(product.name))
        return redirect(url_for('list_products'))
    return render_template('add_product.html', title='Add Product', form=form)

@app.route('/products')
@login_required
def list_products():
    products = Product.query.all()
    return render_template('list_products.html', title='Products', products=products)

@app.route('/record_purchase', methods=['GET', 'POST'])
@login_required
def record_purchase():
    form = PurchaseForm()
    if form.validate_on_submit():
        product = form.product.data # This is a Product object
        quantity_purchased = form.quantity.data
        price_at_time = form.purchase_price.data

        # Create the purchase record
        purchase = Purchase(product_id=product.id,
                            quantity=quantity_purchased,
                            purchase_price_at_time=price_at_time)
        db.session.add(purchase)

        # Update product quantity
        product.quantity += quantity_purchased
        db.session.add(product) # Add product to session to save quantity update

        db.session.commit()
        flash('Purchase of {} {} recorded successfully!'.format(quantity_purchased, product.name))
        return redirect(url_for('list_purchases'))
    return render_template('record_purchase.html', title='Record Purchase', form=form)

@app.route('/purchases')
@login_required
def list_purchases():
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()
    return render_template('list_purchases.html', title='Purchase History', purchases=purchases)

@app.route('/record_sale', methods=['GET', 'POST'])
@login_required
def record_sale():
    form = SaleForm()

    if form.validate_on_submit():
        product_sold = form.product.data
        quantity_sold = form.quantity.data
        price_at_sale_time = form.sale_price.data

        # This check is technically redundant due to form.validate_quantity,
        # but kept as a safeguard or if form validation is somehow bypassed.
        if quantity_sold > product_sold.quantity:
            flash(f"Error: Not enough stock for {product_sold.name}. Only {product_sold.quantity} available.", 'error')
            return render_template('record_sale.html', title='Record Sale', form=form, get_products=get_products_for_form)

        cost_for_this_sale_unit = product_sold.purchase_price
        sale = Sale(product_id=product_sold.id,
                    quantity_sold=quantity_sold,
                    sale_price_at_time=price_at_sale_time,
                    cost_price_at_time_of_sale=cost_for_this_sale_unit)
        db.session.add(sale)

        product_sold.quantity -= quantity_sold
        db.session.add(product_sold)

        db.session.commit()
        flash('Sale of {} {} recorded successfully!'.format(quantity_sold, product_sold.name))
        return redirect(url_for('list_sales'))
    elif request.method == 'GET':
        # Pre-fill sale_price based on selected product (if any) or first product
        # This logic runs when the form is initially loaded or reloaded after a non-POST request (e.g. validation error from GET?)
        # QuerySelectField usually has a value after form creation if there are items.
        selected_product_in_form = form.product.data # This is the actual Product object selected by QuerySelectField

        if selected_product_in_form:
            if not form.sale_price.data: # Only set if not already populated (e.g. by user or previous error)
                form.sale_price.data = selected_product_in_form.sale_price
        else:
            # If form.product.data is None (e.g. no products in DB or allow_blank=True and nothing selected)
            # You might want to set a default price or leave it blank.
            # If QuerySelectField is not allowing blank and there's at least one product,
            # form.product.data should be the first product by default.
            # Let's ensure it handles the case where Product.query.first() might be None.
            first_product = Product.query.first()
            if first_product and not form.sale_price.data : # and not form.product.data (already checked)
                 form.sale_price.data = first_product.sale_price

    return render_template('record_sale.html', title='Record Sale', form=form, get_products=get_products_for_form)

@app.route('/sales')
@login_required
def list_sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('list_sales.html', title='Sales History', sales=sales)

@app.route('/report/summary')
@login_required
def report_summary():
    # Calculate Total Revenue
    total_revenue_query = db.session.query(func.sum(Sale.quantity_sold * Sale.sale_price_at_time)).scalar()
    total_revenue = total_revenue_query if total_revenue_query is not None else 0.0

    # Calculate Total Cost of Goods Sold (COGS)
    total_cogs_query = db.session.query(func.sum(Sale.quantity_sold * Sale.cost_price_at_time_of_sale)).scalar()
    total_cogs = total_cogs_query if total_cogs_query is not None else 0.0

    # Calculate Gross Profit
    gross_profit = total_revenue - total_cogs

    # Get total items sold
    total_items_sold_query = db.session.query(func.sum(Sale.quantity_sold)).scalar()
    total_items_sold = total_items_sold_query if total_items_sold_query is not None else 0

    return render_template('report_summary.html',
                           title='Overall Profit Report',
                           total_revenue=total_revenue,
                           total_cogs=total_cogs,
                           gross_profit=gross_profit,
                           total_items_sold=total_items_sold)
