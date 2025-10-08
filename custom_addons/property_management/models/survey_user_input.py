from odoo import models, fields, api
from odoo.http import request

class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def _get_line_answer_values(self, question, answer, answer_type):
        vals = super(SurveyUserInput, self)._get_line_answer_values(question, answer, answer_type)
        sale_order_id = request.session.get('current_sale_order_id')
        if sale_order_id:
            vals['sale_order_id'] = sale_order_id
        if answer_type == 'numerical_box':
            try:
                vals['value_numerical_box'] = float(answer) if answer not in (None, "", "Skipped") else 0.0
            except Exception:
                vals['value_numerical_box'] = 0.0
        return vals

    def _mark_done(self):
        res = super(SurveyUserInput, self)._mark_done()
        if request and request.session.get('current_sale_order_id'):
            request.session.pop('current_sale_order_id', None)
        return res
    
    def _save_line_choice(self, question, old_answers, answers, comment):
        """
        Override: For multiple_choice, save only ONE line 
        with all answers merged (comma-separated).
        """
        if not isinstance(answers, list):
            answers = [answers]

        if not answers:
            answers = [False] 

        vals_list = []

        if question.question_type == 'simple_choice':
            if not (question.comment_count_as_answer and question.comments_allowed and comment):
                vals_list = [self._get_line_answer_values(question, answers[0], 'suggestion')]

        elif question.question_type == 'multiple_choice':
            answer_records = self.env['survey.question.answer'].browse([int(ans) for ans in answers if ans])
            merged_answers = ", ".join(answer_records.mapped("value"))

            vals = self._get_line_answer_values(question, merged_answers, 'char_box')
            vals_list = [vals]

        if comment:
            vals_list.append(self._get_line_comment_values(question, comment))

        old_answers.sudo().unlink()
        return self.env['survey.user_input.line'].create(vals_list)

class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input.line"

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        ondelete="cascade"
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        readonly=False
    )
    question_type = fields.Selection(
        related="question_id.question_type",
        store=True,
        readonly=True
    )
    char_answer = fields.Char(
        string="Text / Number / Date Answer",
        compute="_compute_char_answer",
        store=True    
    )

    choice_options = fields.Char(
        string="Available Options",
        compute="_compute_choice_options",
        store=False
    )

    answer_id = fields.Many2one(
        'survey.question.answer',
        string="Answer (Single Choice)",
        domain="[('question_id', '=', question_id)]",
        compute="_compute_char_answer",store=True
    )

    answer_ids = fields.Many2many(
        'survey.question.answer',
        'survey_user_input_line_answer_rel',
        'line_id', 'answer_id',
        string="Answer (Multiple)",
        domain="[('question_id', '=', question_id)]",
        compute="_compute_char_answer",store=True
    )
    
    @api.depends('question_id', 'question_type')
    def _compute_choice_options(self):
        for rec in self:
            if rec.question_type in ['simple_choice', 'multiple_choice'] and rec.question_id:
                rec.choice_options = ", ".join(rec.question_id.suggested_answer_ids.mapped('value'))
            else:
                rec.choice_options = ""

    @api.depends('question_type', 'display_name')
    def _compute_char_answer(self):
        for rec in self:
            if rec.question_type == 'simple_choice' and rec.display_name:
                rec.answer_id = rec.question_id.suggested_answer_ids.filtered(
                    lambda a: a.value == rec.display_name
                )[:1]
                rec.answer_ids = [(5, 0, 0)]
                rec.char_answer = ""
            elif rec.question_type == 'multiple_choice' and rec.display_name:
                values = [val.strip() for val in rec.display_name.split(',')]
                rec.answer_ids = rec.question_id.suggested_answer_ids.filtered(
                    lambda a: a.value in values
                )
                rec.answer_id = False
                rec.char_answer = ""
            else:
                rec.char_answer = rec.display_name
                rec.answer_id = False
                rec.answer_ids = [(5, 0, 0)]
    @api.model
    def _get_answer_score_values(self, vals, compute_speed_score=True):
        question_id = vals.get('question_id')
        answer_type = vals.get('answer_type')

        if question_id and answer_type == 'numerical_box':
            answer_val = vals.get('value_numerical_box')
            try:
                answer_val = float(answer_val)
            except (ValueError, TypeError):
                answer_val = 0.0

            question = self.env['survey.question'].browse(int(question_id))
            if answer_val == question.answer_numerical_box:
                return {
                    'answer_is_correct': True,
                    'answer_score': question.answer_score
                }
            else:
                return {
                    'answer_is_correct': False,
                    'answer_score': 0.0
                }

        res = super(SurveyUserInputLine, self)._get_answer_score_values(vals, compute_speed_score=compute_speed_score) or {}
        return res

class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    def _compute_display_name(self):
        """Override: only show the answer label (value_label)."""
        for answer in self:
            answer.display_name = answer.value or ""