# -*- coding: utf-8 -*-
{
    'name': "FSM Customization",
    
    'summary': "Field Service Management customizations and enhancements",
    
    'description': """
FSM Customization Module
========================

This module provides customizations and enhancements for Field Service Management operations.

Features:
---------
* Custom field service workflows
* Enhanced task management
* Additional reporting capabilities
* Custom views and forms for FSM operations
* Integration with existing Odoo modules

Technical Features:
------------------
* Custom models for FSM operations
* Enhanced security rules
* Custom reports and dashboards
* Automated workflows and actions
    """,
    
    'author': "yousif basil almufti",
    'website': "https://www.yourcompany.com",
    'maintainer': "yousif basil almufti",
    'support': "yousif.b.almufti@gmail.com",
    
    # Categories can be used to filter modules in modules listing
 
    # for the full list
    'category': 'Services/Field Service',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    
    # Odoo version compatibility
    'odoo_version': '17',
    
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'fieldservice',
        'fieldservice_account_analytic',
        'helpdesk_mgmt',
        # Field Service Management base module
    ],
    
    # # External dependencies
    # 'external_dependencies': {
    #     'python': [],
    #     'bin': [],
    # },
    
  
   
    'data': [
        # Security
        # 'security/fsm_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/problem_data.xml',
        'data/ir_sequence.xml',
        # 'data/deactivate_old_stages.xml',
        
        #views
        'views/fsm_stages.xml',
        'views/fsm_order.xml',
        'views/problem_management_views.xml',  
        'views/fsm_order_contract_details_view.xml',  
        'views/fsm_order_contact_details.xml',  
        'views/fsm_order_assignment.xml',  
     
        # # Reports
        # 'reports/fsm_reports.xml',
        # 'reports/fsm_report_templates.xml',
        
        # # Wizards
        # 'wizards/fsm_wizard_views.xml',
    ],
    
   
    
    # # Static files and assets
    # 'assets': {
    #     'web.assets_backend': [
    #         'fsm_customization/static/src/css/fsm_style.css',
    #         'fsm_customization/static/src/js/fsm_widget.js',
    #     ],
    #     'web.assets_frontend': [
    #         'fsm_customization/static/src/css/fsm_frontend.css',
    #     ],
    # },
    
    # Module installation and configuration
    'installable': True,
    'auto_install': False,
    'application': False,  
    'sequence': 100,
    
    # Post-installation configuration
    # 'post_init_hook': 'post_init_hook',
    # 'pre_init_hook': 'pre_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
    
    # Module images
    # 'images': [
    #     'static/description/banner.png',
    #     'static/description/icon.png',
    # ],
    
    # Development and testing
    # 'test': [
    #     'tests/test_fsm_functionality.py',
    # ],
    
    # Translation
    # 'qweb': [
    #     'static/src/xml/fsm_templates.xml',
    # ],
}