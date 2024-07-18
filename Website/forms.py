from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, IntegerField
from wtforms.validators import DataRequired, EqualTo
    
class AddItemsForm(FlaskForm):
    name = StringField("name", validators = [DataRequired()], render_kw={'autofocus': True})
    img_url = StringField("img_url", validators = [DataRequired()])
    description = StringField("Description", validators = [DataRequired()])
    price = DecimalField("price", validators=[DataRequired()])
    quantity = IntegerField("quantity", validators=[DataRequired()])
    submit = SubmitField()
    min_quantity = IntegerField("min_quantity", validators=[DataRequired()])
    order_quantity = IntegerField("order_quantity", validators=[DataRequired()])
    
class MakeAdminForm(FlaskForm):
    email = StringField("Email", validators = [DataRequired()], render_kw={'autofocus': True})
    submitadmin = SubmitField()