from django.conf.urls import url
from django.views.generic.base import RedirectView

from danceschool.core.classreg import StudentInfoView

from .forms import NCSContactForm
from danceschool.core.views import StudentInfoView

urlpatterns = [
    # This should override the existing student info view to use our custom form.
    url(r'^register/getinfo/$', StudentInfoView.as_view(form_class=NCSContactForm), name='getStudentInfo'),
]
