Date: 13/07/2023
Version: 15.0.0.1

Improvements:
    - Fix the improvement in fields product wise and lot/serial number shows in drop down.
    - Fix the improvement in Report "Expire Within" field name change into "Expire Within (days)".
    - Fix the improvement in report add Lot/serial number field.

Issues:
    - Fix the issue of when we disable the expiry field from setting and select report By Lot/Serial Wise or By Product Wise at that time traceback raised.
    - Fix the issue of Product --> Expiry date of the product is next month and when we create report expiry within 10 days still we can see this product.
    - Fix the issue of when the report is printed but in the Expire Within field it shows only "0" days if the product is expired with in 3 days still it shows "0".

Date: 03/08/2023
Version: 15.0.0.2

Issues:
    - Fix the issue of when we disable the expiration date selection and select report By Lot/Serial Wise or By Product Wise at that time traceback raised.