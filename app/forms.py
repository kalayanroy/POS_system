from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField # Import QuerySelectField
from app.models import User, Product # Import Product

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    purchase_price = FloatField('Purchase Price', validators=[DataRequired(), NumberRange(min=0)])
    sale_price = FloatField('Sale Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Product')

def get_products(): # Function to provide choices for QuerySelectField
    return Product.query.all()

class PurchaseForm(FlaskForm):
    product = QuerySelectField('Product', query_factory=get_products, allow_blank=False, get_label='name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    purchase_price = FloatField('Purchase Price (per unit)', validators=[DataRequired(), NumberRange(min=0)]) # Price at which it's being bought now
    submit = SubmitField('Record Purchase')

class SaleForm(FlaskForm):
    product = QuerySelectField('Product', query_factory=get_products, allow_blank=False, get_label='name', validators=[DataRequired()])
    quantity = IntegerField('Quantity Sold', validators=[DataRequired(), NumberRange(min=1)])
    # Sale price can be pre-filled from product.sale_price but confirmable/editable at time of sale
    sale_price = FloatField('Sale Price (per unit)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Record Sale')

    def validate_quantity(self, quantity_field):
        # Check if there's enough product quantity
        product_selected = self.product.data
        if product_selected and quantity_field.data > product_selected.quantity:
            raise ValidationError(f"Not enough stock for {product_selected.name}. Only {product_selected.quantity} available.")
