from django.contrib import admin
from django.contrib import admin
from core.models import BloodRequest,Donation,BloodEvent

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'blood_type', 'status', 'urgency', 'needed_by', 'created_at')
    list_filter = ('status', 'urgency', 'blood_type')
    search_fields = ('requester__email', 'hospital')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
     list_display = ('donor', 'request', 'units_donated', 'donation_date', 'is_verified')
     list_filter = ('is_verified', 'donation_date')
     search_fields = ('donor__email', 'request__hospital')
     date_hierarchy = 'donation_date'
     ordering = ('-donation_date',)

@admin.register(BloodEvent)
class BloodEventAdmin(admin.ModelAdmin):
    list_display = ('creator', 'blood_type', 'required_date', 'created_at')
    list_filter = ('blood_type', 'required_date')
    search_fields = ('creator__email', 'message')
    filter_horizontal = ('accepted_by',)  # For ManyToMany field in admin
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

