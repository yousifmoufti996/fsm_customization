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
        'product_expiration',
        'fieldservice_geoengine',
        'base_geoengine',
        'fieldservice_skill'
        # Field Service Management base module
    ],
    
    # # External dependencies
    # 'external_dependencies': {
    #     'python': [],
    #     'bin': [],
    # },
    
  
   
    'data': [
        # Security
        'security/fsm_security.xml',
        'security/ir.model.access.csv',
        'security/partner_security.xml', 
        'security/partner_access_override.xml',
        # 'security/emergency_partner_fix.xml',
        
        # Data
        'data/problem_data.xml',
        'data/ir_sequence.xml',
        'data/fsm_reply_action_data.xml',
        'data/fsm_order_dashboard_data.xml',
        'data/partner_category_data.xml',
        
        # 'data/deactivate_old_stages.xml',
        
        #views
        'views/FSM_Order/fsm_order.xml',
        'views/FSM_Order/fsm_stages.xml',
        'views/problem_management_views.xml',  
        'views/FSM_Order/fsm_order_contract_details_view.xml',  
        'views/FSM_Order/fsm_order_contact_details.xml',  
        'views/FSM_Order/fsm_order_assignment.xml',  
        'views/FSM_Order/fsm_order_replies_view.xml',
     
        'views/FSM_Order/fsm_reply_action_view.xml',
        'views/partner/res_partner_view.xml',  
        'views/FSM_Order/fsm_operation_type_view.xml',  
        'views/FSM_Order/fsm_order_stage_duration.xml',  
        'views/FSM_Order/fsm_order_dashboard_view.xml',
        'views/FSM_Order/fsm_order_products_view.xml',
        'views/area_views.xml',
        'views/partner/res_partner_contacts.xml',
        'views/partner/inherit_old_partner_view.xml',
        'views/partner/category_views.xml',
        'views/partner/category_res_partner_view.xml',
        'views/FSM_Order/navigationto_view.xml',
        'views/FSM_Order/fsm_person_views.xml',
        'views/fsm_order_callcenter_restrictions.xml',
        
        
        
        
        
        # 'views/fsm_dashboard_view.xml',
        # 'views/FSM_Order/fsm_order_geo.xml',
        # 'views/FSM_Order/fsm_order_map_view.xml',
     
        # # Reports
        # 'reports/fsm_reports.xml',
        # 'reports/fsm_report_templates.xml',
        
        # Wizards
        'wizards/AddProductWizard_view.xml',
        'wizards/current_location_wizard_view.xml',
        'wizards/customer_location_wizard_view.xml',
    ],
    
   
    
    # Static files and assets
    'assets': {
        'web.assets_backend': [
            'fsm_customization/static/src/js/simple_navigateto.js',
            'fsm_customization/static/src/js/get_current_location_action_second.js',
            'fsm_customization/static/src/js/navigateto.js',
            'fsm_customization/static/src/js/customer_location.js',
        ],
        # 'web.assets_frontend': [
        #     'fsm_customization/static/src/css/fsm_frontend.css',
        # ],
    },
    
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