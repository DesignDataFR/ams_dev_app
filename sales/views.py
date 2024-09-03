from django.shortcuts import render, redirect
from django.db import connection
from datetime import datetime
from .forms import StatusUpdateForm, MessageForm, BulkStatusUpdateForm, BulkMessageForm
from django.http import HttpResponseBadRequest


def fetchall(query, params=None, query_name=""):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    if query_name:
        print(f"Results for '{query_name}':")
    for i, row in enumerate(results[:10]):
        print(f"Row {i+1}: {row}")
    
    return results

def call_procedure(proc_name, params=None):
    with connection.cursor() as cursor:
        if params:
            filtered_params = [f"'{param}'" if param is not None else "NULL" for param in params]
            param_str = ", ".join(filtered_params)
        else:
            param_str = ""
        
        query = f"EXEC {proc_name} {param_str}"
        print(f"Executing query: {query}") 

        cursor.execute(query)
        try:
            columns = [col[0] for col in cursor.description]
            print(columns)
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except TypeError:
            results = []
    
    return results

def Data(request):
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    alert_id_search = request.GET.get('alert_id_search')
    batch_id_search = request.GET.get('batch_id_search')
    user_id_search = request.GET.get('user_id_search')
    client_id_search = request.GET.get('client_id_search')
    serial_number_search = request.GET.get('serial_number_search')
    product_code_search = request.GET.get('product_code_search')
    status_filter = request.GET.get('status_filter')
    mah_name_search = request.GET.get('mah_name_search')

    params = [
        start_time if start_time else None,
        end_time if end_time else None,
        alert_id_search if alert_id_search else None,
        batch_id_search if batch_id_search else None,
        user_id_search if user_id_search else None,
        client_id_search if client_id_search else None,
        serial_number_search if serial_number_search else None,
        product_code_search if product_code_search else None,
        status_filter if status_filter else None,
        mah_name_search if mah_name_search else None
    ]

    distinct_codes = call_procedure('GetDistinctReturnCodes')
    distinct_statuses = call_procedure('GetDistinctStatusNames')
    total_count_result = call_procedure('GetAlertCount', params)
    total_count = total_count_result[0]['TotalCount'] if total_count_result else 0
    print (total_count)
    alerts = call_procedure('GetAlertData', params)

    for query in connection.queries:
        print(query)

    context = {
        'alerts': alerts,
        'total_count': total_count,
        'times': sorted(set(alert['TransactionTime'].strftime('%d/%m/%Y %H:%M') for alert in alerts)),
        'codes': sorted(set(alert.get('ReturnCode', 'N/A') for alert in alerts)),
        'distinct_codes': [code['ReturnCode'] for code in distinct_codes], 
        'distinct_statuses': [status['StatusName'] for status in distinct_statuses],
        'selected_times': [start_time, end_time],
        'alert_id_search': alert_id_search,
        'batch_id_search': batch_id_search,
        'user_id_search': user_id_search,
        'client_id_search': client_id_search,
        'serial_number_search': serial_number_search,
        'product_code_search': product_code_search,
        'mah_name_search': mah_name_search,
        'status_filter': status_filter,
    }
    return render(request, 'sales/Data.html', context)


def fetch_reasons():
    query = "SELECT ReasonCode, ReasonName FROM Ams_List_Reason"
    return fetchall(query, query_name="Reason List")

def alert_detail(request, alert_id):
    query = """
        SELECT a.AlertId, a.TransactionTime, a.ProductCode, a.ExceptionLevel, a.Serialnumber,
            a.ClientId, a.UserId, a.MAHId, a.MAHName, a.BatchIdReaded, a.ReturnCode, 
            s.StatusCode, sd.StatusName, s.ReasonCode, sl.ReasonName
        FROM Dwh_NMVS_Fct_Alerts_L5 a
        JOIN Ams_Alerts_Status s ON a.AlertId = s.AlertId
        JOIN Ams_List_Status sd ON sd.StatusCode = s.StatusCode
        LEFT JOIN Ams_List_Reason sl ON sl.ReasonCode = s.ReasonCode
        WHERE a.AlertId = %s
        ORDER BY s.CreationDatetime DESC
    """
    alert_details = fetchall(query, [alert_id], query_name="Alert Details")
    
    reasons = fetch_reasons()
    account_id = 1

    status_form = StatusUpdateForm(request.POST or None)
    message_form = MessageForm(request.POST or None)  

    if request.method == 'POST':
        if 'update_status' in request.POST:
            if status_form.is_valid():
                new_status = status_form.cleaned_data['status']
                comment = status_form.cleaned_data['comment']
                reason_code = request.POST.get('reason')
                call_procedure('InsertAmsAlertsStatus', [alert_id, account_id, new_status, reason_code, comment])
                return redirect('alert_detail', alert_id=alert_id)  

        elif 'message' in request.POST:
            if message_form.is_valid():
                new_message = message_form.cleaned_data['text']
                user_or_mah_choice = message_form.cleaned_data['user_or_mah_choice']
                mah_id = alert_details[0]['MAHId'] if user_or_mah_choice in ['mah', 'both'] else None
                user_id = alert_details[0]['UserId'] if user_or_mah_choice in ['user', 'both'] else None

                default_values = {
                    'AccountId': 1,
                    'Source': 'APP',  
                    'ContactType': 'U' if user_or_mah_choice == 'user' else 'M' if user_or_mah_choice == 'mah' else 'B', 
                    'Direction': 'S',  
                    'From': 'system',  
                    'ClientId': alert_details[0]['ClientId'],
                    'InteractionTypeCode': 'MAIL',
                    'EmailStatus': 'P'
                }
                
                call_procedure(
                    'InsertAmsAlertsInteraction',
                    [
                        alert_id, 
                        default_values['AccountId'], 
                        default_values['Source'], 
                        default_values['ContactType'], 
                        default_values['Direction'], 
                        default_values['From'], 
                        default_values['ClientId'], 
                        user_id, 
                        None, 
                        mah_id, 
                        default_values['InteractionTypeCode'], 
                        None, 
                        default_values['EmailStatus'], 
                        None, 
                        new_message
                    ]
                )
                return redirect('alert_detail', alert_id=alert_id)
    else:
        status_form = StatusUpdateForm()
        message_form = MessageForm()

    message_query = """
        SELECT * 
        FROM Ams_Alerts_Interactions_Temp
        WHERE AlertId = %s
        ORDER BY CreationDatetime DESC
    """
    
    messages = fetchall(message_query, [alert_id], query_name="Alert Messages")

    context = {
        'alert_details': alert_details,
        'status_form': status_form,
        'message_form': message_form,
        'messages': messages,
        'reasons': reasons,
    }
    return render(request, 'sales/alert_detail.html', context)


def Home(request):
    row_limit = 1000

    total_alerts = call_procedure('GetTotalAlerts')[0]['total']
    treated_alerts = call_procedure('GetTreatedAlerts')[0]['treated']
    non_treated_alerts = total_alerts - treated_alerts

    avg_treatment_time_result = call_procedure('GetAvgTreatmentTime', [row_limit])[0]
    avg_treatment_time = avg_treatment_time_result['avg_time'] / 3600 if avg_treatment_time_result['avg_time'] is not None else 0

    alerts_by_product_code = {row['ProductCode']: row['count'] for row in call_procedure('GetAlertsByProductCode', [row_limit])}
    alerts_by_return_code = {row['ReturnCode']: row['count'] for row in call_procedure('GetAlertsByReturnCode', [row_limit])}
    alerts_by_user = {row['UserId']: row['count'] for row in call_procedure('GetAlertsByUser', [row_limit])}
    alerts_by_mah = {row['MAHId']: row['count'] for row in call_procedure('GetAlertsByMAH', [row_limit])}

    percentage_non_treated_with_messages_result = call_procedure('GetPercentageNonTreatedWithMessages', [row_limit])[0]
    percentage_non_treated_with_messages = percentage_non_treated_with_messages_result['percentage'] if percentage_non_treated_with_messages_result['percentage'] is not None else 0

    alerts_by_time = {str(row['date']): row['count'] for row in call_procedure('GetAlertsByTime', [row_limit])}

    context = {
        'total_alerts': total_alerts,
        'treated_alerts': treated_alerts,
        'non_treated_alerts': non_treated_alerts,
        'avg_treatment_time': avg_treatment_time,
        'alerts_by_product_code': alerts_by_product_code,
        'alerts_by_return_code': alerts_by_return_code,
        'alerts_by_user': alerts_by_user,
        'alerts_by_mah': alerts_by_mah,
        'percentage_non_treated_with_messages': percentage_non_treated_with_messages,
        'alerts_by_time': alerts_by_time,
    }
    return render(request, 'sales/Home.html', context)



def bulk_update(request):
    message = None
    reasons = fetch_reasons()  

    if request.method == 'POST':
        selected_alerts = request.POST.get('selected_alerts_all', '').split(',')
        selected_alerts = [alert.strip() for alert in selected_alerts if alert.strip()]

        status_form = BulkStatusUpdateForm(request.POST)
        message_form = BulkMessageForm(request.POST)

        default_account_id = 1  
        default_values = {
            'AccountId': 1,
            'Source': 'APP',
            'Direction': 'S',
            'From': 'system',
            'ClientId': '',
            'InteractionDatetime': datetime.now(),
            'InteractionTypeCode': 'MAIL',
            'EmailStatus': 'P',
        }

        if 'update_status' in request.POST and status_form.is_valid():
            new_status = status_form.cleaned_data['status']

            if new_status == 'CLO':  
                reason_code = request.POST.get('reason')
                comment = request.POST.get('comment', '')

                if not reason_code:
                    return HttpResponseBadRequest("A reason must be selected when closing an alert.")

                with connection.cursor() as cursor:
                    cursor.execute("SELECT MAX(AlertIdBulkId) FROM Ams_Alerts_Status")
                    last_bulk_id = cursor.fetchone()[0] or 0
                new_bulk_id = int(last_bulk_id) + 1

                for alert_id in selected_alerts:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO Ams_Alerts_Status (AlertId, StatusCode, ReasonCode, CreationDatetime, AccountId, Comment, AlertIdBulkId)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, [alert_id, new_status, reason_code, datetime.now(), default_account_id, comment, new_bulk_id])
            else:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT MAX(AlertIdBulkId) FROM Ams_Alerts_Status")
                    last_bulk_id = cursor.fetchone()[0] or 0
                new_bulk_id = int(last_bulk_id) + 1

                for alert_id in selected_alerts:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO Ams_Alerts_Status (AlertId, StatusCode, CreationDatetime, AccountId, AlertIdBulkId)
                            VALUES (%s, %s, %s, %s, %s)
                        """, [alert_id, new_status, datetime.now(), default_account_id, new_bulk_id])

            message = "Status updated successfully."

        elif 'submit_message' in request.POST and message_form.is_valid():
            text = message_form.cleaned_data['text']
            user_or_mah_choice = message_form.cleaned_data['user_or_mah_choice']

            default_values['ContactType'] = 'U' if user_or_mah_choice == 'user' else 'M' if user_or_mah_choice == 'mah' else 'B'

            with connection.cursor() as cursor:
                cursor.execute("SELECT MAX(AlertIdBulkId) FROM Ams_Alerts_Interactions_Temp")
                last_bulk_id = cursor.fetchone()[0] or 0
            new_bulk_id = int(last_bulk_id) + 1

            for alert_id in selected_alerts:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT MAHId, UserId FROM Dwh_NMVS_Fct_Alerts_L5 WHERE AlertId = %s
                    """, [alert_id])
                    row = cursor.fetchone()
                    mah_id, user_id = row[0], row[1]

                mah_value = mah_id if user_or_mah_choice in ['mah', 'both'] else None
                user_value = user_id if user_or_mah_choice in ['user', 'both'] else None

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Ams_Alerts_Interactions_Temp (AlertId, AlertIdBulkId, AccountId, Source, ContactType, 
                        Direction, [From], ClientId, UserId, MAHId, InteractionDatetime, InteractionTypeCode, 
                        Message, CreationDatetime, EmailStatus)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [alert_id, new_bulk_id, default_account_id, default_values['Source'], 
                          default_values['ContactType'], default_values['Direction'], default_values['From'], 
                          default_values['ClientId'], user_value, mah_value, default_values['InteractionDatetime'], 
                          default_values['InteractionTypeCode'], text, datetime.now(), default_values['EmailStatus']])

            message = "Message submitted successfully."

    status_form = BulkStatusUpdateForm()
    message_form = BulkMessageForm()

    context = {
        'status_form': status_form,
        'message_form': message_form,
        'selected_alerts': selected_alerts,
        'reasons': reasons,
        'message': message,  
    }
    return render(request, 'sales/bulk_update.html', context)
