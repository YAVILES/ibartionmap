from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group
from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from django.utils.translation import ugettext_lazy as _

from apps.security.models import User


class UserResource(ModelResource):
    class Meta:
        model = User
        exclude = ('id', 'created', 'updated',)
        export_order = ('id', 'email', 'name')


class UserResourceAdmin(ImportExportModelAdmin):
    resource_class = UserResource


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class CustomUserAdmin(UserAdmin, ImportExportModelAdmin):
    form = CustomUserChangeForm
    list_display = ['email', 'name', 'last_name', 'is_staff', 'is_superuser', 'status']
    list_filter = ['email', 'status', 'is_staff', 'is_superuser']
    filter_horizontal = ['groups']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)


admin.site.register(User, CustomUserAdmin)


class RoleResource(ModelResource):
    class Meta:
        model = Group
        exclude = ('id', 'created', 'updated',)

