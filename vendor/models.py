from django.db import models
from accounts.models import User,UserProfile
from accounts.utils import send_notification


# Create your models here.
class Vendor(models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_license = models.ImageField(upload_to='vendor/license')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.vendor_name

    def save(self,*args,**kwargs):
        if self.pk is None:  # new vendor
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:  # is_approved value changed?
                if self.is_approved:
                    # send notification email
                    mail_subject = "Congratulations! Your restaurant has been approved."
                    mail_template = "accounts/emails/admin_approval_email.html"
                    context = {
                        'user': self.user,
                        'is_approved': self.is_approved
                    }
                    send_notification(mail_subject,mail_template,context)
                else:
                    mail_subject = "We're sorry! You're not eligible for publishing your food menu on our marketplace."
                    mail_template = "accounts/emails/admin_approval_email.html"
                    context = {
                        'user': self.user,
                        'is_approved': self.is_approved
                    }
                    send_notification(mail_subject, mail_template, context)
                    pass
        return super(Vendor,self).save(*args,**kwargs)