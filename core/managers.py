from django.db import models

class BloodRequestManager(models.Manager):
    def get_emergency_requests(self):
        return self.filter(urgency__iexact='emergency')  
    def get_by_blood_group(self, blood_group):
        return self.filter(blood_group__iexact=blood_group)
    def get_pending_requests(self):
        return self.filter(status__iexact='pending')
    def urgent_and_pending(self):
        return self.filter(urgency__iexact='emergency', status__iexact='pending')

