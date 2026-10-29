from pydantic_schemaforms import Field, FormModel, Layout, render_form_html


class LoginForm(FormModel):
    email: str = Field(title='Email', ui_element='email')
    password: str = Field(title='Password', ui_element='password')


class NewsletterForm(FormModel):
    email: str = Field(title='Email', ui_element='email')


login_html = render_form_html(LoginForm, submit_url='/login')
newsletter_html = render_form_html(NewsletterForm, submit_url='/newsletter')

page_section = Layout.create_grid(
    Layout.create_card('Sign in', login_html).render(),
    Layout.create_card('Get the newsletter', newsletter_html).render(),
    columns='2fr 1fr',
    gap='2rem',
).render()
