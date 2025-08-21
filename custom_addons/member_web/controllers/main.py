from odoo import http
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)


class MemberWebsite(http.Controller):
    @http.route(["/member/register"], type="http", auth="public", website=True)
    def member_register_form(self, **kwargs):
        return request.render("member_web.member_template", {})

    @http.route(
        ["/member/submit"], type="http", auth="public", website=True, csrf=False
    )
    def member_register_submit(self, **post):

        uploaded_file = request.httprequest.files.get("member_document")

        if uploaded_file:
            _logger.info("Uploaded file received: %s", uploaded_file.filename)
            print("Uploaded file:", uploaded_file.filename)
        else:
            _logger.warning("No file uploaded!")
            print("No file uploaded.")

        file_content = base64.b64encode(uploaded_file.read()) if uploaded_file else None
        file_name = uploaded_file.filename if uploaded_file else None
        dob = post.get("dob") or None

        # Create partner
        partner = (
            request.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": post.get("name"),
                    "email": post.get("email"),
                }
            )
        )

        user = (
            request.env["res.users"]
            .sudo()
            .create(
                {
                    "name": post.get("name"),
                    "login": post.get("email"),
                    "email": post.get("email"),
                    "partner_id": partner.id,
                    "password": "default123",
                    "groups_id": [(6, 0, [request.env.ref("base.group_portal").id])],
                    "active": True,
                }
            )
        )

        request.env["website.member"].sudo().create(
            {
                "name": post.get("name"),
                "height": post.get("height"),
                "weight": post.get("weight"),
                "dob": dob,
                "email": post.get("email"),
                "member_document": file_content,
                "member_document_filename": file_name,
                "partner_id": partner.id,
                "medical_info": post.get("medical_info"),
                "user_id": user.id,
            }
        )
        return request.render("member_web.website_member_thanks")

    @http.route(["/member/list"], type="http", auth="user", website=True)
    def member_list(self, **kwargs):
        user = request.env.user
        if user.has_group("base.group_system") or user.login == "mitchell.admin":
            members = request.env["website.member"].search([])
        else:
            members = request.env["website.member"].search(
                [("create_uid", "=", user.id)]
            )
        return request.render("member_web.template_member_list", {"members": members})

    @http.route(["/member/register"], type="http", auth="public", website=True)
    def member_register_form(self, **kwargs):
        return request.render("member_web.member_template", {})

    @http.route(["/membership/list"], type="http", auth="user", website=True)
    def membership_list(self, **kwargs):
        user = request.env.user
        Membership = request.env["membership.membership"]

        if user.has_group("base.group_system") or user.login == "mitchell.admin":
            memberships = Membership.sudo().search([])
        else:
            member = (
                request.env["website.member"]
                .sudo()
                .search([("user_id", "=", user.id)], limit=1)
            )
            memberships = (
                Membership.sudo().search([("member_id", "=", member.id)])
                if member
                else []
            )

        return request.render(
            "member_web.template_membership_list", {"memberships": memberships}
        )
