from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('download/', views.folder, name='folder'),
    path('download/href="main/exel/<str:filename>"', views.download, name='download'),
    path('report/', views.report, name='report'),
    path('report/report.pdf', views.download_report, name='download_report'),
    path('recover/recover_ajax/', views.recover_ajax, name='recover_ajax'),
    path('recover/', views.recover, name='recover'),
    path('recovered/', views.recovered, name='recovered'),
    path('reported/<str:city>/<int:start_day>/<int:start_month>/<int:start_year>/<int:end_day>/<int:end_month>/<int:end_year>', views.reported, name='reported'),
    path('<str:url>/error/<str:err_msg>', views.error, name='error')
]

urlpatterns += staticfiles_urlpatterns()
