{
    'name': 'Contact Creation Restriction',
    'version': '15.0.1.0.0',
    'category': 'Account',
    'summary': 'Change a Sequence of Invoice Account Number',
    'author': 'INKERP',
    'website': "https://www.INKERP.com",
    'depends': ['account'],
    
    'data': [
        'security/account_move_security.xml',
        'views/res_partner.xml',
    ],
   
    'images': ['static/description/banner.png'],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
