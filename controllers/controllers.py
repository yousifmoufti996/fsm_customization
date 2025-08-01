# -*- coding: utf-8 -*-
# from odoo import http


# class FsmCustomization(http.Controller):
#     @http.route('/fsm_customization/fsm_customization', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fsm_customization/fsm_customization/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fsm_customization.listing', {
#             'root': '/fsm_customization/fsm_customization',
#             'objects': http.request.env['fsm_customization.fsm_customization'].search([]),
#         })

#     @http.route('/fsm_customization/fsm_customization/objects/<model("fsm_customization.fsm_customization"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fsm_customization.object', {
#             'object': obj
#         })

