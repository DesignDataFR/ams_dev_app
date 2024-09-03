from django.db import models

class AmsAlertsInteractions(models.Model):
    ID = models.AutoField(primary_key=True, db_column='ID')
    AlertId = models.CharField(max_length=300, db_column='AlertId')
    messages_user_mah = models.TextField(null=True, db_column='Message')
    CreationDatetime = models.DateTimeField(auto_now_add=True, db_column='CreationDatetime')
    MAHId = models.CharField(max_length=200, null=True, db_column='MAHId')
    UserId = models.CharField(max_length=100, null=True, db_column='UserId')
    AlertIdBulkId = models.IntegerField(db_column='AlertIdBulkId')

    class Meta:
        db_table = 'Ams_Alerts_Interactions'
        managed = False

class AmsAlertsStatus(models.Model):
    AlertId = models.CharField(max_length=300, db_column='AlertId')
    StatusCode = models.CharField(max_length=10, db_column='StatusCode')
    CreationDatetime = models.DateTimeField(auto_now_add=True, db_column='CreationDatetime')
    AlertIdBulkId = models.IntegerField(db_column='AlertIdBulkId')

    class Meta:
        db_table = 'Ams_Alerts_Status'
        managed = False

class AmsListStatus(models.Model):
    StatusCode = models.CharField(max_length=10, primary_key=True, db_column='StatusCode')
    StatusName = models.CharField(max_length=100, db_column='StatusName')

    class Meta:
        db_table = 'Ams_List_Status'
        managed = False
