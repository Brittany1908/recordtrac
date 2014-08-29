# RecordTrac's Admin Features

## Description 

RecordTrac’s administrative controls allows the users to:

* [Edit or remove request text](#how-to-remove-or-edit-a-request)
* [Remove a record](#how-to-remove-a-record)
* [Edit or remove the text of a note](#how-to-remove-or-edit-a-note)
* [Edit or remove a question or answer](#how-to-remove-or-edit-a-question-and-answer-exchange)
* [Update your RecordTrac website text](#updating-website-text)

The administrative controls allows the user to permanently delete records, requests, and notes from the database. Because of this, administrative access should be restricted to a small number of users. 


## Best Practices

Content should only be removed or edited if sensitive or confidential information is revealed. If this happens, you should:

* Save a copy of the original message. (This will have to be done outside of RecordTrac. There is no way to hide a message from public view.) 
* Edit the message to indicate why it needs to be removed. 
* Notify the requester why their post or answer was removed.
* Provide guidance to the requester on how they can get the record they need. 

If a staff member enters information incorrectly, simply add a note explaining the mistake. 

If a member of the public enters incorrect information,  the requester (or a staff member) can add a note correcting the mistake. 

Sometimes it’s necessary to create a new request. If a new request must be created, we suggest you do the following:

* Create a new request with the proper information.
* In the old request, include a note explaining what is wrong with it and a link to the new request.
* Close out the old request.
* In the new request, reference and/or provide a link to the old request. 

Although RecordTrac has a spam filter, every once in a while it may receive spam. When confronted with spam, close the request with a note indicating why it is not a public records request.  If there is a large amount of spam requests, it is appropriate to simply remove the spam. 

If a record needs to be removed. It not only has to be deleted on RecordTrac, it has to be removed from Scribd as well. 

## How to Remove or Edit a Request

To remove or edit a request, visit records.oaklandnet.com/admin/requestview. 

image::admin_request.png[]

A description of the fields in the table displayed can be found below:

* Id: Unique ID assigned to each request.
* Text: Entire text of public records request.
* Date Created: The date the request was entered in RecordTrac.
* Status: Status of the records request, namely whether it’s open, closed, due soon, or overdue.

Clicking on the trashcan icon permanently deletes an entire request.

image::admin_delete_request.png[]

Clicking on the pencil icon will allow you to edit a request. 

image::admin_edit_request.png[]

## How to Remove a Record

To remove a record, visit records.oaklandnet.com/admin/recordreview.

image::admin_record.png[]

You can only remove a record, not "edit" any of the fields.  Records include web links, uploaded electronic documents, and instructions on how to view or pick up copies of a record. 

A description of the fields in the table displayed can be found below:

* ID: Unique ID assigned to each request.
* Filename: Name of electronic record uploaded to RecordTrac. 
* URL: Web address provided to requester.
* Download URL: Web address where you can automatically download the record. 
* Access: Instructions on how to view or pick up copies of a record

Click on the trashcan icon to permanently delete the record from RecordTrac. You must also delete the record from the hosted location.  For example, if you are using Scribd, it must be deleted from the Scribd account.  

image::admin_delete_record.png[]

## How to Remove or Edit a Note

To edit or remove a note, visit records.oaklandnet.com/admin/noteview.

image::admin_note.png[]

A description of the fields in the table displayed can be found below:

* ID: Unique ID assigned to each request.
* Text: Entire text of the note.
* Date Created: The date the note was created. 

Click on the trashcan icon to permanently delete the note from RecordTrac. 

image::admin_delete_note.png[]

Clicking on the pencil icon will allow you to edit the text of a note.

image::admin_edit_note.png[]

## How to Remove or Edit a Question and Answer Exchange

To remove posted questions and/or answers, navigate to the "Q A" tab.

image::admin_qa.png[]

A description of the fields in the table displayed can be found below:

* ID: Unique ID assigned to each request.
* Question: Entire text of the question asked by agency staff.
* Answer: Entire response of question provided by member of the public. 
* Date Created: The date the exchange was created

Clicking on the trashcan icon permanently deletes the entire question and answer exchange.

image::admin_delete_qa.png[]

Clicking on the pencil icon will allow you to edit the text of the question and answer exchange. 

image::admin_edit_qa.png[]


## Updating Website Text

The web copy is not managed through the admin interface. To update the copy on the website, the .json files or HTML templates must be modified.  See the [technical documentation](/readme/redeploy.md) for more detailed instructions.


## Changing Passwords

Passwords are not managed through the admin section. Agency employees are required to manage their own passwords directly through the Mozilla Persona sign-in.

image::reset_password.png[]


## Checking Status of RecordTrac

![status](/readme/images/status.png "status")

There is a quick way for adminstrators to check on the status of the application. Visit `[records.youragency.gov]/.well-known/status` to get a quick confirmation of whether the app is working.

If the status is 'ok,' it means the app is working properly and users should not encounter any problems.

The number next to SendGrid is the percentage of its email quota the application has used this month. If it is close to 100, then the agency is close to hitting its email quotas for the month and may be charged for each additional email. 

The dependencies section lists additional web applications used by RecordTrac. Askismet is the spam filter. Scribd is where all uploaded documents are hosted. SendGrid sends out the email notifications and Postgres is where all of the data is stored. 

