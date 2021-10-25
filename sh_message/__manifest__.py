# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Popup Message",
    'author': "SIT & think digital",
    "website": "https://www.softhealer.com",
    'website': "http://sitco.odoo.com/",        
    "category": "Custom",
    "summary": "Custom Success, warnings, alert message box wizard",
    "description": """
        This module is useful to crate custom message/pop up wizard.
        You can create Success, warnings, alert message box wizard by the few line of code.
        
                    """,    
    "version":"12.0.1",
    "depends" : ["base","web"],
    "application" : True,
    "data" : ['wizard/sh_message_wizard.xml',        
            ],            
    "images": ["static/description/background.png",],              
    "auto_install":False,
    "installable" : True,      
}
