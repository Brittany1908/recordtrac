from public_records_portal.notifications import notify_due
from public_records_portal.departments import populate_users_with_departments
from public_records_portal.prr import set_directory_fields

# Notify city staff via e-mail if they belong to a request that is due soon or overdue:
notify_due()

# Set directory fields from information in the directory.json file
set_directory_fields()

# Update user info with information in the departments.json file
populate_users_with_departments()

